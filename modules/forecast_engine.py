"""Hibrit Tahmin Motoru: Fizik Baseline + LightGBM Quantile Regression

ML Eğitim Veri Kaynağı (öncelik sırası):
1. PVGIS saatlik gerçek üretim verisi (2020, AB JRC API)
2. Sentetik fizik bazlı 3000 senaryo (fallback)
"""
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
import joblib
import os
import requests


class ForecastEngine:
    def __init__(self):
        self.model_dir = "./data/models/"
        os.makedirs(self.model_dir, exist_ok=True)
        self.models = {}

    # ------------------------------------------------------------------ #
    #                        PUBLIC: Solar Tahmin                         #
    # ------------------------------------------------------------------ #
    def predict_solar(self, weather_df, installed_kw, tilt, azimuth, loss_pct):
        baselines = np.array([
            self._solar_physics(
                row.get("shortwave_radiation", 0),
                row.get("direct_radiation", 0),
                row.get("diffuse_radiation", 0),
                row.get("temperature_2m", 25),
                row.get("cloud_cover", 0),
                installed_kw, loss_pct,
            )
            for _, row in weather_df.iterrows()
        ])

        features = self._build_features(weather_df, baselines)

        if not self._has_models("solar"):
            self._train_quantile_models("solar", installed_kw, loss_pct)

        if self._has_models("solar"):
            p10 = np.maximum(0, self.models["solar_p10"].predict(features))
            p50 = np.maximum(0, self.models["solar_p50"].predict(features))
            p90 = np.maximum(0, self.models["solar_p90"].predict(features))
            p10 = np.minimum(p10, p50)
            p90 = np.maximum(p90, p50)
        else:
            p50 = baselines
            cloud = weather_df["cloud_cover"].values / 100
            unc = 0.15 + 0.25 * cloud
            p10 = np.maximum(0, p50 * (1 - unc))
            p90 = p50 * (1 + unc)

        confidence = self._confidence(weather_df)
        ts = weather_df["time"].tolist()
        return self._pack_result(ts, p10, p50, p90, confidence)

    # ------------------------------------------------------------------ #
    #                        PUBLIC: Wind Tahmin                          #
    # ------------------------------------------------------------------ #
    def predict_wind(self, weather_df, rated_kw, hub_height):
        results = []
        for _, row in weather_df.iterrows():
            ws = row.get("wind_speed_10m", 0) * (hub_height / 10) ** 0.2
            results.append(self._wind_curve(ws, rated_kw))

        p50 = np.array(results)
        wind_std = weather_df["wind_speed_10m"].rolling(3, min_periods=1).std().fillna(1).values
        unc = np.clip(0.2 + 0.1 * wind_std, 0.15, 0.5)
        p10 = np.maximum(0, p50 * (1 - unc))
        p90 = p50 * (1 + unc)

        confidence = self._confidence(weather_df)
        ts = weather_df["time"].tolist()
        return self._pack_result(ts, p10, p50, p90, confidence)

    # ------------------------------------------------------------------ #
    #                        PHYSICS MODELS                               #
    # ------------------------------------------------------------------ #
    def _solar_physics(self, irr, direct, diffuse, temp, cloud, kw, loss):
        if irr <= 0:
            return 0.0
        cell_temp = temp + 0.03 * irr
        temp_coeff = 1 - 0.004 * (cell_temp - 25)
        return max(0.0, (irr / 1000) * kw * temp_coeff * (1 - loss / 100))

    def _wind_curve(self, ws, rated):
        if ws < 3 or ws > 25:
            return 0.0
        if ws >= 12:
            return rated
        return rated * ((ws - 3) / 9) ** 3

    # ------------------------------------------------------------------ #
    #                        ML TRAINING                                  #
    # ------------------------------------------------------------------ #
    def _train_quantile_models(self, etype, kw, loss, lat=39.0, lon=35.0,
                               angle=30, aspect=0):
        """
        Quantile regression modellerini eğit.
        Önce PVGIS gerçek verisi (2020) denenir.
        Başarısız olursa sentetik 3000-senaryo fallback kullanılır.
        """
        try:
            pvgis_df = self._fetch_pvgis_training_data(
                lat, lon, kw, loss, angle, aspect)
            if pvgis_df is not None and len(pvgis_df) >= 500:
                feats, actual = self._pvgis_to_features(pvgis_df, kw, loss)
                data_source = "pvgis_real"
            else:
                feats, actual = self._synthetic_features(kw, loss)
                data_source = "synthetic"

            for q_name, alpha in [("p10", 0.1), ("p50", 0.5), ("p90", 0.9)]:
                mdl = LGBMRegressor(
                    objective="quantile", alpha=alpha,
                    n_estimators=300, max_depth=6,
                    learning_rate=0.04, verbose=-1,
                )
                mdl.fit(feats, actual)
                key = f"{etype}_{q_name}"
                self.models[key] = mdl
                joblib.dump(mdl, os.path.join(self.model_dir, f"{key}.pkl"))

            # Model eğitim kaynağı meta veri dosyasına kaydedilir (arayüz gösterimi için)
            meta_path = os.path.join(self.model_dir, f"{etype}_meta.txt")
            with open(meta_path, "w") as f:
                f.write(data_source)
            print(f"[ForecastEngine] Model eğitildi: {data_source} ({len(actual)} nokta)")
        except Exception as e:
            print(f"Model eğitim hatası: {e}")

    # ------------------------------------------------------------------ #
    #                    PVGIS REAL DATA TRAINING                         #
    # ------------------------------------------------------------------ #
    def _fetch_pvgis_training_data(self, lat, lon, kw, loss, angle, aspect):
        """PVGIS API'den 2020 yılı saatlik üretim verisi çek (ML eğitimi)."""
        try:
            params = {
                "lat": lat, "lon": lon,
                "startyear": 2020, "endyear": 2020,
                "pvcalculation": 1,
                "peakpower": kw, "loss": loss,
                "angle": angle, "aspect": aspect,
                "outputformat": "json",
            }
            resp = requests.get(
                "https://re.jrc.ec.europa.eu/api/v5_2/seriescalc",
                params=params, timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            records = data.get("outputs", {}).get("hourly", [])
            if not records:
                return None
            df = pd.DataFrame(records)
            df["time"] = pd.to_datetime(df["time"], format="%Y%m%d:%H%M")
            return df
        except Exception:
            return None

    def _pvgis_to_features(self, df, kw, loss):
        """PVGIS DataFrame'ini ML feature matrisine dönüştür."""
        hours = df["time"].dt.hour.values
        doy   = df["time"].dt.dayofyear.values

        # PVGIS çıktı sütunları: P (W) = üretim gücü, G(i) = eğim açısına göre ışınım, T2m = sıcaklık
        rad       = df.get("G(i)",  pd.Series(np.zeros(len(df)))).values
        temp      = df.get("T2m",   pd.Series(np.full(len(df), 25.0))).values
        wind      = df.get("WS10m", pd.Series(np.full(len(df), 5.0))).values
        actual_w  = df.get("P",     pd.Series(np.zeros(len(df)))).values
        actual_kw = actual_w / 1000.0   # W cinsinden güç değeri kW'ye dönüştürülür

        baselines = np.array([
            self._solar_physics(r, r * 0.75, r * 0.25, t, 0, kw, loss)
            for r, t in zip(rad, temp)
        ])
        cloud  = np.clip((1 - rad / (np.maximum(rad.max(), 1))) * 100, 0, 100)
        hum    = np.full(len(df), 60.0)

        feats = np.column_stack([
            hours, doy,
            np.sin(2 * np.pi * hours / 24), np.cos(2 * np.pi * hours / 24),
            np.sin(2 * np.pi * doy  / 365), np.cos(2 * np.pi * doy  / 365),
            temp, cloud, hum, wind, rad, baselines,
        ])
        return feats, actual_kw

    def _synthetic_features(self, kw, loss):
        """Fallback: sentetik 3000 senaryo."""
        rng   = np.random.RandomState(42)
        N     = 3000
        hours = rng.randint(0, 24, N)
        doy   = rng.randint(1, 366, N)
        temp  = rng.uniform(-5, 40, N)
        cloud = rng.uniform(0, 100, N)
        hum   = rng.uniform(20, 95, N)
        wind  = rng.uniform(0, 20, N)
        rad   = np.array([
            max(0, 1000 * np.sin(max(0, (h - 6) * np.pi / 13)) * (1 - c / 133))
            for h, c in zip(hours, cloud)
        ])
        baselines = np.array([
            self._solar_physics(r, r * 0.75, r * 0.25, t, c, kw, loss)
            for r, t, c in zip(rad, temp, cloud)
        ])
        noise  = 0.1 + 0.2 * (cloud / 100)
        actual = np.maximum(0, baselines * (1 + rng.randn(N) * noise))
        feats  = np.column_stack([
            hours, doy,
            np.sin(2 * np.pi * hours / 24), np.cos(2 * np.pi * hours / 24),
            np.sin(2 * np.pi * doy  / 365), np.cos(2 * np.pi * doy  / 365),
            temp, cloud, hum, wind, rad, baselines,
        ])
        return feats, actual

    def get_training_source(self, etype="solar") -> str:
        """Son eğitimde kullanılan veri kaynağını döndür."""
        meta_path = os.path.join(self.model_dir, f"{etype}_meta.txt")
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                return f.read().strip()
        return "unknown"

    def _has_models(self, etype):
        needed = [f"{etype}_{q}" for q in ("p10", "p50", "p90")]
        for k in needed:
            if k not in self.models:
                path = os.path.join(self.model_dir, f"{k}.pkl")
                if os.path.exists(path):
                    self.models[k] = joblib.load(path)
                else:
                    return False
        return True

    # ------------------------------------------------------------------ #
    #                        HELPERS                                      #
    # ------------------------------------------------------------------ #
    def _build_features(self, df, baselines):
        hours = pd.to_datetime(df["time"]).dt.hour.values
        doy = pd.to_datetime(df["time"]).dt.dayofyear.values
        return np.column_stack([
            hours, doy,
            np.sin(2 * np.pi * hours / 24), np.cos(2 * np.pi * hours / 24),
            np.sin(2 * np.pi * doy / 365), np.cos(2 * np.pi * doy / 365),
            df["temperature_2m"].values,
            df["cloud_cover"].values,
            df["relative_humidity_2m"].values,
            df["wind_speed_10m"].values,
            df.get("shortwave_radiation", pd.Series([0] * len(df))).values,
            baselines,
        ])

    def _confidence(self, df):
        return (100 - df["cloud_cover"] * 0.5).clip(20, 95).values

    def _pack_result(self, ts, p10, p50, p90, confidence):
        return {
            "timestamps": ts,
            "p50": p50.tolist(),
            "p10": p10.tolist(),
            "p90": p90.tolist(),
            "confidence": confidence.tolist(),
            "total_production": float(p50.sum()),
            "max_production": float(p50.max()),
            "max_hour": str(ts[int(p50.argmax())]) if p50.max() > 0 else "N/A",
            "avg_confidence": float(confidence.mean()),
            "low_production_hours": int((p50 < 0.5).sum()),
        }
