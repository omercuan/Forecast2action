"""EPİAŞ Piyasa Fiyatı — eptr2 Kütüphanesi ile Gerçek Veri

eptr2 kütüphanesi kullanılarak doğrudan EPİAŞ Şeffaflık Platformu'ndan veri çekilir.
Kimlik bilgileri (username, password) otomatik olarak TGT/ST CAS akışını yönetir.
"""

import os
import numpy as np
import pandas as pd
import requests
from datetime import datetime, timedelta

# ─── EPİAŞ CAS Kimlik Doğrulama Endpoint'leri ────────────────────────────── #
_TGT_URL   = "https://giris.epias.com.tr/cas/v1/tickets"
_MCP_URL   = "https://seffaflik.epias.com.tr/transparency/service/market/mcp"

# ─── EPDK Tarifeleri ──────────────────────────────────────────────────── #
EPDK_TARIFF = {
    "3_zamanli": {
        "name": "EPDK 3 Zamanlı",
        "night": {"hours": list(range(22, 24)) + list(range(0, 6)), "price": 1.08},
        "day":   {"hours": list(range(6, 17)),                       "price": 2.16},
        "peak":  {"hours": list(range(17, 22)),                      "price": 3.27},
    },
    "flat": {"name": "Düz Tarife", "price": 2.20},
    "tou_summer": {
        "name": "Yaz TOU",
        "night": {"hours": list(range(23, 24)) + list(range(0, 7)), "price": 0.95},
        "day":   {"hours": list(range(7, 18)),                      "price": 2.35},
        "peak":  {"hours": list(range(18, 23)),                     "price": 3.80},
    },
}

def get_epdk_prices(tariff_key: str, hours: int = 48) -> list:
    """EPDK sabit tarifeden saatlik fiyat üret."""
    tariff = EPDK_TARIFF.get(tariff_key, EPDK_TARIFF["3_zamanli"])
    now = datetime.now()
    prices = []
    for h in range(hours):
        hour = (now.hour + h) % 24
        if tariff_key == "flat":
            prices.append(tariff["price"])
        else:
            if hour in tariff["night"]["hours"]:
                prices.append(tariff["night"]["price"])
            elif hour in tariff["peak"]["hours"]:
                prices.append(tariff["peak"]["price"])
            else:
                prices.append(tariff["day"]["price"])
    return prices


# ─────────────────────────────────────────────────────────────────────── #
#  TEMEL İŞLEV: EPİAŞ CAS TGT DOĞRULAMA (Doğrudan REST API)             #
# ─────────────────────────────────────────────────────────────────────── #
def _get_tgt(username: str, password: str) -> tuple:
    """
    TGT işlemini doğrudan eptr2'nin kendi metoduna bırakır.
    """
    try:
        from eptr2 import EPTR2
        eptr = EPTR2(username=username.strip(), password=password.strip(), recycle_tgt=False)
        eptr.get_tgt()
        if eptr.tgt and eptr.tgt.startswith("TGT-"):
            return eptr.tgt, None
        return None, "Geçersiz TGT veya giriş başarısız."
    except Exception as e:
        return None, f"Giriş hatası: {str(e)}"


def _get_st(tgt_url: str, service: str) -> str | None:
    """TGT URL'sinden Service Ticket (ST) alır."""
    try:
        resp = requests.post(
            tgt_url,
            data={"service": service},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.text.strip()
        return None
    except Exception:
        return None


def clear_tgt_cache():
    pass


def get_epias_ptf(hours: int = 48,
                  username: str | None = None,
                  password: str | None = None) -> dict:
    """
    EPİAŞ CAS sistemi üzerinden PTF (Piyasa Takas Fiyatı) verisi çeker.
    Kimlik yoksa veya hata varsa simülasyon döner — asla exception fırlatmaz.
    """
    usr = (username or os.environ.get("EPIAS_USERNAME", "")).strip()
    pwd = (password or os.environ.get("EPIAS_PASSWORD", "")).strip()

    if not (usr and pwd):
        return _mock_epias_prices(hours)

    try:
        # 1) TGT al
        tgt, err = _get_tgt(usr, pwd)
        if not tgt:
            return {**_mock_epias_prices(hours), "tgt_error": err}

        # 2) Gerçek TGT ise eptr2 üzerinden MCP verisi çek
        from eptr2 import EPTR2
        from datetime import timedelta
        tgt_d = {
            "tgt": tgt,
            "tgt_exp":   (datetime.now() + timedelta(hours=1, minutes=45)).timestamp(),
            "tgt_exp_0": (datetime.now() + timedelta(hours=1, minutes=45)).timestamp(),
        }
        eptr = EPTR2(username=usr, password=pwd, tgt_d=tgt_d, recycle_tgt=False)

        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date   = (datetime.now() + timedelta(days=(hours // 24) + 1)).strftime("%Y-%m-%d")
        df_res     = eptr.call("mcp", start_date=start_date, end_date=end_date)

        if df_res is None or df_res.empty:
            return {**_mock_epias_prices(hours), "tgt_error": "Veri bulunamadı (boş dataframe)"}

        df_res     = df_res.head(hours)
        prices_kwh = (df_res["price"] / 1000.0).tolist()
        timestamps = df_res["date"].astype(str).tolist()

        # Dizi yeterliliği kontrolü
        while len(prices_kwh) < hours:
            prices_kwh.append(prices_kwh[-1] if prices_kwh else 2.20)
            timestamps.append("")

        return {
            "prices":     prices_kwh,
            "source":     "epias_live",
            "avg_price":  float(np.mean(prices_kwh)),
            "max_price":  float(np.max(prices_kwh)),
            "min_price":  float(np.min(prices_kwh)),
            "timestamps": timestamps,
        }

    except Exception as e:
        return {**_mock_epias_prices(hours),
                "tgt_error": f"EPİAŞ API Hatası: {str(e)[:150]}"}


def _fetch_mcp_rest(hours: int, st: str | None) -> tuple:
    """ST kullanarak MCP verisini doğrudan REST API üzerinden çeker."""
    try:
        start = datetime.now().strftime("%Y-%m-%dT00:00:00+03:00")
        end   = (datetime.now() + timedelta(days=(hours // 24) + 1)).strftime("%Y-%m-%dT23:59:59+03:00")
        params = {"startDate": start, "endDate": end}
        headers = {"Accept": "application/json"}
        if st:
            headers["ticket"] = st
        resp = requests.get(_MCP_URL, params=params, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("body", {}).get("mcpList", [])
            prices = [item.get("price", 2200) / 1000.0 for item in items[:hours]]
            timestamps = [item.get("date", "")[:16] for item in items[:hours]]
            if prices:
                return prices, timestamps
    except Exception:
        pass
    return [], []


# ─────────────────────────────────────────────────────────────────────── #
#  SİMÜLASYON: KİMLİK DOĞRULAMASI OLMADAN YEDEKLEMELİ VERİ ÜRETİMİ     #
# ─────────────────────────────────────────────────────────────────────── #
def _mock_epias_prices(hours: int, error: str = "") -> dict:
    """2024 Türkiye spot piyasa profiline dayalı gerçekçi simülasyon."""
    now  = datetime.now()
    seed = int(now.strftime("%Y%m%d")) % 9999
    rng  = np.random.RandomState(seed)

    profile = np.array([
        0.62, 0.58, 0.55, 0.54, 0.55, 0.60,
        0.78, 0.92, 1.05, 1.12, 1.15, 1.18,
        1.20, 1.18, 1.12, 1.08, 1.10, 1.28,
        1.52, 1.68, 1.62, 1.40, 1.12, 0.82,
    ])
    base = 2.35

    prices, timestamps = [], []
    for h in range(hours):
        hr  = (now.hour + h) % 24
        p   = base * profile[hr] * (1 + 0.05 * np.sin(2 * np.pi * h / 168))
        p  *= (1 + rng.randn() * 0.10)
        prices.append(max(0.50, round(p, 3)))
        timestamps.append((now + timedelta(hours=h)).strftime("%Y-%m-%d %H:00"))

    return {
        "prices":     prices,
        "source":     "epias_mock",
        "avg_price":  float(np.mean(prices)),
        "max_price":  float(np.max(prices)),
        "min_price":  float(np.min(prices)),
        "timestamps": timestamps,
        "info":       "EPİAŞ Spot Simülasyonu — 2024 piyasa profili",
    }


def build_price_dataframe(price_data: dict, hours: int = 48) -> pd.DataFrame:
    """Görselleştirme için fiyat DataFrame'i."""
    now    = datetime.now()
    prices = price_data.get("prices", [2.20] * hours)
    tss    = price_data.get("timestamps") or [
        (now + timedelta(hours=h)).strftime("%Y-%m-%d %H:00") for h in range(hours)
    ]
    df = pd.DataFrame({
        "timestamp":    pd.to_datetime(tss[:hours]),
        "price_tl_kwh": prices[:hours],
    })
    df["hour"] = df["timestamp"].dt.hour
    df["tariff_period"] = df["hour"].apply(
        lambda h: "🌙 Gece" if h in list(range(22, 24)) + list(range(0, 6))
                  else ("🔴 Puant" if h in range(17, 22) else "🟡 Gündüz")
    )
    return df
