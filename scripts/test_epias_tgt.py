# -*- coding: utf-8 -*-
"""EPiAS TGT auth + PTF endpoint discovery"""
import requests
from datetime import datetime, timedelta

TGT_URL = "https://giris.epias.com.tr/cas/v1/tickets"

# Test TGT endpoint (sahte bilgi - 401 beklenir ama URL dogru mu?)
print("1) TGT endpoint testi (sahte bilgi)...")
try:
    r = requests.post(
        TGT_URL,
        data={"username": "test_user", "password": "test_pass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=5,
    )
    print(f"   Status: {r.status_code}")
    print(f"   Body: {r.text[:300]}")
    print(f"   Headers: Location={r.headers.get('Location', 'N/A')}")
except requests.exceptions.Timeout:
    print("   TIMEOUT")
except Exception as e:
    print(f"   ERR: {type(e).__name__}: {str(e)[:150]}")

print()

# PTF endpoint - simdi TGT ile dene
# Yeni PTF endpoint'i bul
now = datetime.now()
CANDIDATES_V2 = [
    "https://seffaflik.epias.com.tr/electricity-service/v1/markets/dam/data/mcp",
    "https://seffaflik.epias.com.tr/electricity-service/v1/markets/ptf/data",
    "https://seffaflik.epias.com.tr/transparency-api/v1/markets/dam/data/mcp",
    "https://seffaflik.epias.com.tr/electricity-service/v1/markets/dam/data/dam-clearing-quantity",
]
print("2) PTF/MCP endpoint aramasi (TGT olmadan 401 veya 403 beklenir)...")
for url in CANDIDATES_V2:
    try:
        r2 = requests.get(
            url,
            params={"startDate": now.strftime("%Y-%m-%dT%H:00:00+03:00"),
                    "endDate": (now + timedelta(hours=2)).strftime("%Y-%m-%dT%H:00:00+03:00")},
            headers={"Accept": "application/json", "TGT": "dummy-tgt"},
            timeout=5,
        )
        short = url.split("epias.com.tr")[-1]
        print(f"   [{r2.status_code}] {short}")
        if r2.status_code in (200, 401, 403):
            print(f"          -> {r2.text[:200]}")
    except requests.exceptions.Timeout:
        print(f"   [TIMEOUT] {url.split('epias.com.tr')[-1]}")
    except Exception as e:
        print(f"   [ERR] {str(e)[:80]}")
