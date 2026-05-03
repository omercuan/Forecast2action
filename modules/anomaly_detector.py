"""Anomali Tespiti — Z-score + IsolationForest"""
import numpy as np
from collections import deque

try:
    from sklearn.ensemble import IsolationForest
    HAS_ISO = True
except ImportError:
    HAS_ISO = False


class AnomalyDetector:
    def __init__(self, window_size=7):
        self.window_size = window_size
        self.history = deque(maxlen=window_size)
        self.iso_model = None

    def detect(self, actual, expected, historical=None):
        """Çoklu anomali tespiti"""
        if historical:
            self.history = deque(historical[-self.window_size:], maxlen=self.window_size)
        self.history.append(expected)

        if len(self.history) < 3 or expected <= 0:
            return {"alert": False, "z_score": 0.0, "performance_ratio": 1.0}

        # Z-Skoru Hesaplama
        avg = np.mean(self.history)
        std = np.std(self.history)
        z = (actual - avg) / std if std > 0 else 0

        # Performans Oranı Hesaplaması
        pr = actual / expected if expected > 0 else 1.0

        # Anomali karar kriterleri uygulanır
        is_anomaly = z < -2 or pr < 0.6

        # IsolationForest ile ek anomali doğrulaması (kütüphane mevcut ise)
        if HAS_ISO and len(self.history) >= 5:
            try:
                if self.iso_model is None:
                    self.iso_model = IsolationForest(contamination=0.1, random_state=42)
                    hist_arr = np.array(list(self.history)).reshape(-1, 1)
                    self.iso_model.fit(hist_arr)
                iso_pred = self.iso_model.predict([[actual]])[0]
                if iso_pred == -1:
                    is_anomaly = True
            except Exception:
                pass

        if is_anomaly and actual < expected:
            perf_drop = ((expected - actual) / expected * 100)
            severity = "KRİTİK" if perf_drop > 40 or z < -3 else "UYARI"

            causes = []
            if perf_drop > 40:
                causes.append("Panel kirliliği (ağır düzeyde)")
            elif perf_drop > 20:
                causes.append("Panel kirliliği veya gölgelenme")
            causes.extend([
                "Yeni engel/gölgelenme",
                "İnverter arızası",
                "Kablo bağlantı sorunu",
            ])

            return {
                "alert": True,
                "severity": severity,
                "z_score": float(z),
                "performance_ratio": float(pr),
                "message": f"Beklenenin %{perf_drop:.0f} altında üretim",
                "possible_causes": causes[:3],
            }

        return {"alert": False, "z_score": float(z), "performance_ratio": float(pr)}
