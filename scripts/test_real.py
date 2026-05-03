# -*- coding: utf-8 -*-
import requests
from datetime import datetime, timedelta

USERNAME = "buraksenol3017@gmail.com"
PASSWORD = "Qweasd.123"

# 1. TGT
CAS_URL = "https://giris.epias.com.tr/cas/v1/tickets"
print("1. TGT ALINIYOR...")
r1 = requests.post(CAS_URL, data={"username": USERNAME, "password": PASSWORD},
                   headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "text/plain"}, timeout=5)
print(f"   Status: {r1.status_code}")
if r1.status_code != 201:
    print("   Hata:", r1.text)
    exit(1)
tgt = r1.text.strip()
print(f"   TGT: {tgt[:30]}...")

# 2. ST
SERVICE_URL = "https://seffaflik.epias.com.tr/electricity-service/v1/markets/dam/data/mcp"
print(f"\n2. ST ALINIYOR... ({SERVICE_URL})")
r2 = requests.post(f"{CAS_URL}/{tgt}", data={"service": SERVICE_URL},
                   headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "text/plain"}, timeout=5)
print(f"   Status: {r2.status_code}")
if r2.status_code != 200:
    print("   Hata:", r2.text)
    exit(1)
st = r2.text.strip()
print(f"   ST: {st[:30]}...")

# 3. PTF Veri Çekme
print("\n3. PTF VERISI ÇEKILIYOR...")
now = datetime.now()
payload = {
    "startDate": now.strftime("%Y-%m-%dT%H:00:00+03:00"),
    "endDate": (now + timedelta(hours=4)).strftime("%Y-%m-%dT%H:00:00+03:00")
}
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Bearer {st}"
}
r3 = requests.post(SERVICE_URL, json=payload, headers=headers, timeout=5)
print(f"   Status: {r3.status_code}")
if r3.status_code == 200:
    print("   BASARILI:", str(r3.json())[:300])
else:
    print("   Hata:", r3.text[:300])

# ALTERNATIF URL TESTI:
SERVICE_URL_2 = "https://seffaflik.epias.com.tr/transparency-api/v1/markets/dam/data/mcp"
print(f"\nALTERNATIF ST ALINIYOR... ({SERVICE_URL_2})")
r4 = requests.post(f"{CAS_URL}/{tgt}", data={"service": SERVICE_URL_2},
                   headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "text/plain"}, timeout=5)
st2 = r4.text.strip() if r4.status_code == 200 else "NONE"
print(f"   ST2 Status: {r4.status_code}")

if st2 != "NONE":
    print("ALTERNATIF PTF ÇEKILIYOR...")
    headers["Authorization"] = f"Bearer {st2}"
    r5 = requests.get(SERVICE_URL_2, params=payload, headers={"Accept": "application/json", "TGT": st2}, timeout=5)
    print(f"   Status (GET + TGT): {r5.status_code}")
    print("   Body:", r5.text[:200])

