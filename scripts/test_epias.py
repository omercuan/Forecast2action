# -*- coding: utf-8 -*-
import requests, json, sys
from datetime import datetime, timedelta

now = datetime.now()
payload = {
    "startDate": now.strftime("%Y-%m-%dT%H:00:00"),
    "endDate": (now + timedelta(hours=4)).strftime("%Y-%m-%dT%H:00:00"),
}
print("Payload:", json.dumps(payload))
print("Testing EPiAS API...")

# Test 1: eski endpoint
try:
    resp = requests.post(
        "https://seffaflik.epias.com.tr/transparency/service/market/ptf",
        json=payload,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=6,
    )
    print("Status:", resp.status_code)
    print("Headers:", dict(resp.headers))
    print("Body (500c):", resp.text[:500])
except requests.exceptions.Timeout:
    print("HATA: TIMEOUT (6s icinde cevap gelmedi)")
except requests.exceptions.ConnectionError as e:
    print("HATA: CONNECTION ERROR:", str(e)[:300])
except Exception as e:
    print("HATA:", type(e).__name__, str(e)[:300])

print()

# Test 2: yeni v1 API (EPIAS 2024 donusum)
print("Testing new EPIAS v1 REST API...")
try:
    r2 = requests.get(
        "https://seffaflik.epias.com.tr/electricity-service/v1/markets/dam/data/mcp",
        params={"startDate": now.strftime("%Y-%m-%dT%H:00:00"),
                "endDate": (now + timedelta(hours=4)).strftime("%Y-%m-%dT%H:00:00")},
        headers={"Accept": "application/json"},
        timeout=6,
    )
    print("Status:", r2.status_code)
    print("Body (500c):", r2.text[:500])
except requests.exceptions.Timeout:
    print("HATA: TIMEOUT yeni API da")
except requests.exceptions.ConnectionError as e:
    print("HATA: CONNECTION yeni API:", str(e)[:200])
except Exception as e:
    print("HATA:", type(e).__name__, str(e)[:200])

print()

# Test 3: temel DNS testi
print("Testing basic connectivity (google.com)...")
try:
    r3 = requests.get("https://www.google.com", timeout=5)
    print("google.com OK, status:", r3.status_code)
except Exception as e:
    print("google.com FAIL:", str(e)[:100])

print()

# Test 4: seffaflik DNS
print("Testing seffaflik.epias.com.tr DNS...")
try:
    r4 = requests.get("https://seffaflik.epias.com.tr", timeout=6)
    print("seffaflik OK, status:", r4.status_code)
except requests.exceptions.Timeout:
    print("seffaflik TIMEOUT - sunucu erisilebilir ama cevap vermiyor")
except requests.exceptions.ConnectionError as e:
    print("seffaflik CONNECTION FAIL (DNS/firewall):", str(e)[:200])
except Exception as e:
    print("seffaflik:", type(e).__name__, str(e)[:200])
