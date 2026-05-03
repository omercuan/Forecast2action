# -*- coding: utf-8 -*-
"""EPiAS PTF endpoint + header format bulucu - gercek TGT ile"""
import os, sys, requests
from datetime import datetime, timedelta

# --- TGT al ---
USERNAME = os.environ.get("EPIAS_USERNAME") or input("EPiAS kullanici adi: ")
PASSWORD = os.environ.get("EPIAS_PASSWORD") or input("EPiAS sifre: ")

print(f"\nTGT aliniyor: {USERNAME}")
r = requests.post(
    "https://giris.epias.com.tr/cas/v1/tickets",
    data={"username": USERNAME, "password": PASSWORD},
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=8,
)
print(f"TGT Status: {r.status_code}")
print(f"TGT Body  : {r.text[:300]}")
print(f"TGT Loc   : {r.headers.get('Location', 'N/A')}")

if r.status_code != 201:
    print("TGT alinamadi! Kimlik bilgilerini kontrol et.")
    sys.exit(1)

# TGT degeri - hem body hem location dene
tgt_body     = r.text.strip()
tgt_location = r.headers.get("Location", "")
print(f"\ntgt_body    : {tgt_body[:80]}")
print(f"tgt_location: {tgt_location[:80]}")

# --- Parametreler ---
now   = datetime.now()
start = now.strftime("%Y-%m-%dT%H:00:00+03:00")
end   = (now + timedelta(hours=4)).strftime("%Y-%m-%dT%H:00:00+03:00")
start2 = now.strftime("%Y-%m-%dT%H:00:00")
end2   = (now + timedelta(hours=4)).strftime("%Y-%m-%dT%H:00:00")

# --- Deneyecegimiz kombinasyonlar ---
ENDPOINTS = [
    ("GET",  "https://seffaflik.epias.com.tr/transparency-api/v1/markets/dam/data/mcp",
     {"startDate": start, "endDate": end}),
    ("GET",  "https://seffaflik.epias.com.tr/transparency-api/v1/markets/dam/data/mcp",
     {"startDate": start2, "endDate": end2}),
    ("POST", "https://seffaflik.epias.com.tr/transparency-api/v1/markets/dam/data/mcp",
     {"startDate": start, "endDate": end}),
    ("GET",  "https://seffaflik.epias.com.tr/transparency-api/v1/markets/ptf",
     {"startDate": start, "endDate": end}),
    ("POST", "https://seffaflik.epias.com.tr/transparency/service/market/ptf",
     {"startDate": start2, "endDate": end2}),
    ("GET",  "https://seffaflik.epias.com.tr/transparency-api/v1/markets/dam/data/side-payments",
     {"startDate": start, "endDate": end}),
]

HEADER_VARIANTS = [
    {"TGT": tgt_body},
    {"Authorization": f"Bearer {tgt_body}"},
    {"tgt-ticket": tgt_body},
    {"TGT": tgt_location} if tgt_location else None,
    {"Authorization": f"TGT {tgt_body}"},
]
HEADER_VARIANTS = [h for h in HEADER_VARIANTS if h]

COMMON = {"Accept": "application/json", "Content-Type": "application/json"}

print("\n" + "="*60)
print("ENDPOINT + HEADER TARAMA BASLADI")
print("="*60)

for method, url, params in ENDPOINTS:
    short = url.split("epias.com.tr")[-1]
    for hv in HEADER_VARIANTS:
        headers = {**COMMON, **hv}
        hk = list(hv.keys())[0]
        try:
            if method == "GET":
                resp = requests.get(url, params=params, headers=headers, timeout=6)
            else:
                resp = requests.post(url, json=params, headers=headers, timeout=6)
            
            print(f"[{resp.status_code}] {method} {short} | header={hk}")
            if resp.status_code == 200:
                print(f"  *** BASARILI! Body: {resp.text[:400]}")
                print("\nBULUNDU! Endpoint ve header formati yukarida.")
                sys.exit(0)
            elif resp.status_code not in (404,):
                print(f"  -> {resp.text[:150]}")
        except requests.exceptions.Timeout:
            print(f"[TIMEOUT] {method} {short} | header={hk}")
        except Exception as e:
            print(f"[ERR] {str(e)[:80]}")

print("\nHicbir endpoint calismadi.")
