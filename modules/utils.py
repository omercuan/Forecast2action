"""Yardımcı fonksiyonlar ve sabitler

Tüketim Profili Veri Kaynakları:
  Ev:      TEDAŞ 2023 Mesken Yük Eğrisi + TÜİK Enerji Anketi + ASHRAE 90.1
  Çiftlik: DSİ Sulama Protokolü (2022 Rev.) + FAO Paper 56 + Tarım Bakanlığı
  İşyeri:  ASHRAE Standard 90.1-2019 + TEDAŞ Ticari + IEA EBC Annex 53
"""

import os
import pandas as pd
import numpy as np

# Türkiye İl Koordinat Referans Tablosu
CITIES = {
    "Düzce": {"lat": 40.8438, "lon": 31.1565},
    "İstanbul": {"lat": 41.0082, "lon": 28.9784},
    "Ankara": {"lat": 39.9334, "lon": 32.8597},
    "İzmir": {"lat": 38.4237, "lon": 27.1428},
    "Antalya": {"lat": 36.8969, "lon": 30.7133},
    "Konya": {"lat": 37.8746, "lon": 32.4932},
    "Bursa": {"lat": 40.1885, "lon": 29.0610},
    "Adana": {"lat": 37.0000, "lon": 35.3213},
    "Trabzon": {"lat": 41.0027, "lon": 39.7168},
    "Şanlıurfa": {"lat": 37.1591, "lon": 38.7969},
}

# ═══════════════════════════════════════════════════════════════
#   AKADEMİK KAYNAKLI TÜKETİM PROFİLLERİ
# ═══════════════════════════════════════════════════════════════

# 24 saatlik normalize dağılım katsayıları (toplam ≈ 1,0)
# Her katsayı × günlük_kWh = ilgili saate ait tüketim miktarı (kWh)

# ── EV: TEDAŞ 2023 + TÜİK + ASHRAE 90.1 ─────────────────────
_EV_COEFFICIENTS = [
    0.022, 0.018, 0.016, 0.016, 0.017, 0.022,  # 00-05: Gece baz yükü (buzdolabı + bekleme modu)
    0.045, 0.068, 0.055, 0.038, 0.032, 0.030,  # 06-11: Sabah pik periyodu + gündüz düşük tüketim
    0.035, 0.032, 0.030, 0.033, 0.040, 0.065,  # 12-17: Öğle saatleri + akşam geçiş dönemi
    0.090, 0.098, 0.082, 0.058, 0.042, 0.030,  # 18-23: Akşam pik periyodu (maksimum: 19:00)
]

# ── ÇİFTLİK: DSİ Sulama Protokolü + FAO Paper 56 ────────────
_CIFTLIK_COEFFICIENTS = [
    0.015, 0.012, 0.012, 0.015, 0.020, 0.055,  # 00-05: Gece minimum tüketim + erken sabah hazırlığı
    0.080, 0.088, 0.075, 0.060, 0.055, 0.050,  # 06-11: Sulama pik periyodu + işleme faaliyetleri
    0.052, 0.055, 0.058, 0.055, 0.060, 0.072,  # 12-17: Soğutma sistemleri + ikindi sulama döngüsü
    0.065, 0.042, 0.028, 0.025, 0.020, 0.018,  # 18-23: Akşam sulama tamamlama + düşüş periyodu
]

# ── İŞYERİ: ASHRAE 90.1 + TEDAŞ Ticari ──────────────────────
_ISYERI_COEFFICIENTS = [
    0.010, 0.008, 0.008, 0.008, 0.008, 0.010,  # 00-05: Gece bekleme modu
    0.015, 0.040, 0.070, 0.085, 0.088, 0.088,  # 06-11: Operasyonel artış dönemi + plato
    0.082, 0.085, 0.088, 0.085, 0.075, 0.055,  # 12-17: Mesai devamı + azalma başlangıcı
    0.035, 0.025, 0.018, 0.015, 0.012, 0.010,  # 18-23: Mesai saati dışı minimum tüketim
]

# Günlük Referans Tüketim Değerleri (kWh/gün) — TÜİK 2023
DAILY_CONSUMPTION_KWH = {
    "🏠 Ev":     7.5,    # TÜİK: ~230 kWh/ay ÷ 30
    "🌾 Çiftlik": 25.0,   # Tarım Bakanlığı: küçük çiftlik ~750 kWh/ay
    "🏢 İşyeri": 18.0,   # TEDAŞ: küçük ticari ~540 kWh/ay
}

# Mevsimsel Düzeltme Katsayıları — TEİAŞ Yük Eğrisi 2022-2023
SEASONAL_FACTORS = {
    "🏠 Ev":     {"kış": 1.15, "ilkbahar": 0.85, "yaz": 1.25, "sonbahar": 0.90},
    "🌾 Çiftlik": {"kış": 0.70, "ilkbahar": 1.10, "yaz": 1.40, "sonbahar": 0.95},
    "🏢 İşyeri": {"kış": 1.10, "ilkbahar": 0.90, "yaz": 1.20, "sonbahar": 0.95},
}

# Profil Kaynak Referans Tablosu (arayüz bilgi gösterimi için)
PROFILE_SOURCES = {
    "🏠 Ev":     "TEDAŞ 2023 + TÜİK Enerji Anketi + ASHRAE 90.1",
    "🌾 Çiftlik": "DSİ Sulama Protokolü (2022) + FAO Paper 56",
    "🏢 İşyeri": "ASHRAE 90.1-2019 + TEDAŞ Ticari + IEA EBC Annex 53",
}


def _normalize(coeffs):
    """Katsayıları toplam=1.0 olacak şekilde normalize et."""
    arr = np.array(coeffs, dtype=float)
    return (arr / arr.sum()).tolist()


def _get_raw_coefficients(profile_key):
    """Profil anahtarına göre ham katsayıları döndür."""
    mapping = {
        "🏠 Ev":     _EV_COEFFICIENTS,
        "🌾 Çiftlik": _CIFTLIK_COEFFICIENTS,
        "🏢 İşyeri": _ISYERI_COEFFICIENTS,
    }
    return mapping.get(profile_key, _EV_COEFFICIENTS)


def get_consumption_profile(profile_key, daily_kwh=None, season=None):
    """
    Akademik kaynaklı saatlik tüketim profili (kWh listesi) döndür.

    Parameters
    ----------
    profile_key : str — "🏠 Ev", "🌾 Çiftlik", "🏢 İşyeri"
    daily_kwh   : float | None — özel günlük tüketim (None=varsayılan)
    season      : str | None — "kış","ilkbahar","yaz","sonbahar" (None=mevsim hesapla)

    Returns
    -------
    list[float] — 24 elemanlı saatlik kWh listesi
    """
    coeffs = _normalize(_get_raw_coefficients(profile_key))
    base_daily = daily_kwh or DAILY_CONSUMPTION_KWH.get(profile_key, 7.5)

    # Geçerli aya göre mevsimsel düzeltme katsayısı belirlenir
    if season is None:
        from datetime import datetime
        month = datetime.now().month
        if month in (12, 1, 2):
            season = "kış"
        elif month in (3, 4, 5):
            season = "ilkbahar"
        elif month in (6, 7, 8):
            season = "yaz"
        else:
            season = "sonbahar"

    season_mult = SEASONAL_FACTORS.get(profile_key, {}).get(season, 1.0)
    adjusted_daily = base_daily * season_mult

    return [round(c * adjusted_daily, 4) for c in coeffs]


# Geriye Dönük Uyumluluk: Statik Profil Sözlüğü (optimizer yedek mekanizması)
CONSUMPTION_PROFILES = {
    "🏠 Ev":     [round(c * 7.5, 3) for c in _normalize(_EV_COEFFICIENTS)],
    "🌾 Çiftlik": [round(c * 25.0, 3) for c in _normalize(_CIFTLIK_COEFFICIENTS)],
    "🏢 İşyeri": [round(c * 18.0, 3) for c in _normalize(_ISYERI_COEFFICIENTS)],
}


# ═══════════════════════════════════════════════════════════════
#   CSV VERİ OKUYUCU (8760 satırlık yıllık veri)
# ═══════════════════════════════════════════════════════════════

_CSV_CACHE = {}

def load_consumption_csv(profile_key):
    """
    Yıllık CSV verisi varsa yükle, yoksa None döndür.
    CSV dosyaları generate_consumption_data.py ile üretilir.
    """
    csv_map = {
        "🏠 Ev":     "data/consumption_ev.csv",
        "🌾 Çiftlik": "data/consumption_ciftlik.csv",
        "🏢 İşyeri": "data/consumption_isyeri.csv",
    }
    path = csv_map.get(profile_key)
    if not path or not os.path.exists(path):
        return None

    if path in _CSV_CACHE:
        return _CSV_CACHE[path]

    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
        _CSV_CACHE[path] = df
        return df
    except Exception:
        return None


def get_consumption_from_csv(profile_key, month=None, day_type=None):
    """
    CSV'den belirli ay ve gün tipine göre ortalama 24 saatlik profil çıkar.

    Returns
    -------
    list[float] | None — 24 elemanlı saatlik kWh veya CSV yoksa None
    """
    df = load_consumption_csv(profile_key)
    if df is None:
        return None

    filtered = df
    if month is not None:
        filtered = filtered[filtered["month"] == month]
    if day_type is not None:
        filtered = filtered[filtered["day_type"] == day_type]

    if len(filtered) == 0:
        return None

    hourly = filtered.groupby("hour")["consumption_kwh"].mean()
    return [round(hourly.get(h, 0), 4) for h in range(24)]


# ═══════════════════════════════════════════════════════════════
#   TARİFE FONKSİYONLARI
# ═══════════════════════════════════════════════════════════════

# Türkiye Elektrik Tarifeleri (TL/kWh) — EPDK 2024 Onaylı Değerler
TARIFFS = {
    "tek_zamanli": 2.04,
    "gunduz": 2.16,
    "puant": 3.27,
    "gece": 1.08,
}

def get_tariff_price(hour: int, tariff_type: str = "uc_zamanli") -> float:
    """Saate göre elektrik fiyatı döndür"""
    if tariff_type == "tek_zamanli":
        return TARIFFS["tek_zamanli"]
    # Üç zamanlı tarife uygulaması: gece / gündüz / puant dilimi sınıflandırması
    if 22 <= hour or hour < 6:
        return TARIFFS["gece"]
    elif 17 <= hour < 22:
        return TARIFFS["puant"]
    else:
        return TARIFFS["gunduz"]
