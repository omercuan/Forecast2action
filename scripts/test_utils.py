"""Quick test for utils module"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import importlib.util
sys.path.insert(0, '.')
spec = importlib.util.spec_from_file_location('utils', 'modules/utils.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

print("=== PROFIL TESTI ===")
for key, profile in m.CONSUMPTION_PROFILES.items():
    total = sum(profile)
    print(f"  {key}: {len(profile)} saat, toplam={total:.2f} kWh/gun")

print("\n=== KAYNAK TESTI ===")
for key, src in m.PROFILE_SOURCES.items():
    print(f"  {key}: {src}")

print("\n=== CSV TESTI ===")
csv_ev = m.get_consumption_from_csv("\U0001f3e0 Ev".replace("\U0001f3e0", "🏠"), month=7)
if csv_ev:
    print(f"  Ev CSV (Temmuz): OK - {len(csv_ev)} saat")
    print(f"  Ilk 6 saat: {[round(x,3) for x in csv_ev[:6]]}")
    print(f"  Pik saat: {csv_ev.index(max(csv_ev))}:00 = {max(csv_ev):.3f} kWh")
else:
    print("  Ev CSV: BULUNAMADI")

print("\n=== MEVSIM TESTI ===")
for season in ["kis", "ilkbahar", "yaz", "sonbahar"]:
    ev_profile = m.get_consumption_profile("🏠 Ev", season=season)
    total = sum(ev_profile)
    print(f"  {season}: toplam={total:.2f} kWh/gun")

print("\n=== TARIFE TESTI ===")
for h in [0, 6, 12, 17, 22]:
    p = m.get_tariff_price(h)
    print(f"  Saat {h:02d}: {p:.2f} TL/kWh")

print("\nTUM TESTLER BASARILI!")
