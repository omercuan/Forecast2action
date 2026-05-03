"""Test mevsim duzeltme"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import importlib.util
sys.path.insert(0, '.')
spec = importlib.util.spec_from_file_location('utils', 'modules/utils.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# Actual season test with Turkish chars
for season in ["kış", "ilkbahar", "yaz", "sonbahar"]:
    ev = m.get_consumption_profile("🏠 Ev", season=season)
    cif = m.get_consumption_profile("🌾 Çiftlik", season=season)
    isy = m.get_consumption_profile("🏢 İşyeri", season=season)
    print(f"{season:>10}: Ev={sum(ev):.1f}  Ciftlik={sum(cif):.1f}  Isyeri={sum(isy):.1f} kWh/gun")

print("\nMevsim otomatik (current month):")
ev_auto = m.get_consumption_profile("🏠 Ev")
print(f"  Ev auto: {sum(ev_auto):.1f} kWh/gun")

print("\nOK!")
