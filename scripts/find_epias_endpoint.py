# -*- coding: utf-8 -*-
"""EPiAS yeni API endpoint araştırması"""
import requests, json
from datetime import datetime, timedelta

now = datetime.now()
start = now.strftime("%Y-%m-%dT%H:00:00+03:00")
end   = (now + timedelta(hours=4)).strftime("%Y-%m-%dT%H:00:00+03:00")

BASE = "https://seffaflik.epias.com.tr"

CANDIDATES = [
    # Yeni electricity-service REST
    ("GET",  f"{BASE}/electricity-service/v1/markets/dam/data/mcp",
     {"startDate": start, "endDate": end}),
    ("GET",  f"{BASE}/electricity-service/v1/markets/dam/data/clearing-quantity",
     {"startDate": start, "endDate": end}),
    ("POST", f"{BASE}/electricity-service/v1/markets/ptf",
     {"startDate": start, "endDate": end}),
    # Orjinal eski URL (ne donduruyor gormek icin)
    ("POST", f"{BASE}/transparency/service/market/ptf",
     {"startDate": now.strftime("%Y-%m-%dT%H:00:00"),
      "endDate":   (now + timedelta(hours=4)).strftime("%Y-%m-%dT%H:00:00")}),
    # PTF yeni path deneme
    ("GET",  f"{BASE}/electricity-service/v1/markets/bpm/data/balancing-power-market-trade-history",
     {"startDate": start, "endDate": end}),
    # swagger endpoint var mi?
    ("GET",  f"{BASE}/electricity-service/swagger-ui.html", {}),
    ("GET",  f"{BASE}/electricity-service/v3/api-docs", {}),
]

HEADERS_JSON = {"Accept": "application/json", "Content-Type": "application/json"}

for method, url, params in CANDIDATES:
    short = url.replace(BASE, "")
    try:
        if method == "GET":
            r = requests.get(url, params=params, headers=HEADERS_JSON, timeout=5)
        else:
            r = requests.post(url, json=params, headers=HEADERS_JSON, timeout=5)
        print(f"[{r.status_code}] {method} {short}")
        if r.status_code not in (404, 405):
            print("  -> Body:", r.text[:300])
    except requests.exceptions.Timeout:
        print(f"[TIMEOUT] {method} {short}")
    except Exception as e:
        print(f"[ERR] {method} {short} -> {type(e).__name__}: {str(e)[:100]}")
    print()
