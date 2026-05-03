"""Open-Meteo ve PVGIS veri entegrasyonu"""
import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


@st.cache_data(ttl=3600, show_spinner="🌤️ Hava verileri çekiliyor...")
def get_weather_forecast(lat: float, lon: float, hours: int = 48) -> pd.DataFrame:
    """Open-Meteo'dan saatlik hava tahmini çek"""
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": ",".join([
                "temperature_2m",
                "relative_humidity_2m",
                "cloud_cover",
                "wind_speed_10m",
                "wind_speed_100m",
                "shortwave_radiation",
                "direct_radiation",
                "diffuse_radiation",
            ]),
            "forecast_days": max(2, (hours // 24) + 1),
            "timezone": "Europe/Istanbul",
        }
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params=params,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data["hourly"])
        df["time"] = pd.to_datetime(df["time"])
        df = df.head(hours)
        return df
    except Exception as e:
        st.warning(f"⚠️ API hatası: {e} — Mock veri kullanılıyor.")
        return _generate_mock_forecast(lat, lon, hours)


@st.cache_data(ttl=86400, show_spinner="📊 PVGIS tarihsel verisi çekiliyor...")
def get_pvgis_hourly(lat: float, lon: float, peakpower: float = 5,
                     loss: float = 14, angle: int = 30, aspect: int = 0):
    """PVGIS'ten saatlik tarihsel üretim verisi (ML eğitimi için)"""
    try:
        params = {
            "lat": lat, "lon": lon,
            "startyear": 2020, "endyear": 2020,
            "pvcalculation": 1,
            "peakpower": peakpower, "loss": loss,
            "angle": angle, "aspect": aspect,
            "outputformat": "json",
        }
        response = requests.get(
            "https://re.jrc.ec.europa.eu/api/v5_2/seriescalc",
            params=params, timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        records = data.get("outputs", {}).get("hourly", [])
        if not records:
            return None
        df = pd.DataFrame(records)
        df["time"] = pd.to_datetime(df["time"], format="%Y%m%d:%H%M")
        return df
    except Exception as e:
        st.warning(f"⚠️ PVGIS hatası: {e}")
        return None


def _generate_mock_forecast(lat: float, lon: float, hours: int) -> pd.DataFrame:
    """Gerçekçi mock hava verisi (fallback)"""
    rng = np.random.RandomState(42)
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    times = [now + timedelta(hours=i) for i in range(hours)]

    hourly_solar = []
    for t in times:
        h = t.hour
        if 6 <= h <= 19:
            angle = np.sin((h - 6) * np.pi / 13)
            rad = max(0, 800 * angle * (0.7 + 0.3 * rng.random()))
        else:
            rad = 0
        hourly_solar.append(rad)

    df = pd.DataFrame({
        "time": times,
        "temperature_2m": [15 + 10 * (hourly_solar[i] / 800) + rng.randn() * 2
                           for i in range(hours)],
        "relative_humidity_2m": [max(10, min(100, 60 + rng.randint(-20, 20)))
                                 for _ in range(hours)],
        "cloud_cover": [max(0, min(100, 30 + rng.randint(-30, 40)))
                        for _ in range(hours)],
        "wind_speed_10m": [max(0, 5 + rng.randn() * 3) for _ in range(hours)],
        "wind_speed_100m": [max(0, 8 + rng.randn() * 4) for _ in range(hours)],
        "shortwave_radiation": hourly_solar,
        "direct_radiation": [s * 0.75 for s in hourly_solar],
        "diffuse_radiation": [s * 0.25 for s in hourly_solar],
    })
    return df
