"""Batarya & Şebeke Optimizasyonu — Greedy Algoritma"""
import numpy as np
from modules.utils import CONSUMPTION_PROFILES

SOC_MIN_FRAC = 0.20   # Minimum şarj durumu: %20 (batarya ömrü koruma sınırı)
SOC_MAX_FRAC = 0.95   # Maksimum şarj durumu: %95 (tam şarjı önler; kimyasal gerilimi azaltır)
SOC_INIT_FRAC = 0.50  # Başlangıç şarj durumu: %50


class BatteryOptimizer:
    def optimize(self, production, prices, battery_kwh, battery_kw,
                 consumption_profile="🏠 Ev"):
        hours = len(production)
        consumption = self._get_consumption(consumption_profile, hours)
        soc_min = battery_kwh * SOC_MIN_FRAC   # Mutlak minimum enerji düzeyi (kWh)
        soc_max = battery_kwh * SOC_MAX_FRAC   # Mutlak maksimum enerji düzeyi (kWh)
        battery_soc = battery_kwh * SOC_INIT_FRAC  # Başlangıç şarj durumu (%50)

        # Saatlik sonuç listeleri
        bat_charge, bat_discharge = [], []
        grid_exp, grid_imp = [], []
        grid_action, soc_change, h_savings = [], [], []

        price_arr = np.array(prices[:hours])
        p_low = np.percentile(price_arr, 33) if len(price_arr) > 0 else 1
        p_high = np.percentile(price_arr, 67) if len(price_arr) > 0 else 2

        for h in range(hours):
            prod = production[h]
            cons = consumption[h]
            price = prices[h] if h < len(prices) else prices[-1]
            net = prod - cons

            charge = discharge = export = imp = savings = 0.0
            action = "Bekle"

            if net > 0:  # Fazla üretim
                if price < p_low and battery_soc < soc_max and battery_kwh > 0:
                    # Şarj işlemi: SoC_max sınırı aşılmadan şarj uygulanır
                    charge = min(net, battery_kw, soc_max - battery_soc)
                    battery_soc += charge
                    remaining = net - charge
                    if remaining > 0.01:
                        export = remaining
                        savings = export * price
                        action = f"Şarj+Sat ({charge:.1f}+{export:.1f})"
                    else:
                        action = f"Şarj ({charge:.1f} kWh)"
                elif price >= p_high:
                    export = net
                    savings = export * price
                    action = f"Sat ({export:.1f} kWh)"
                else:
                    if battery_soc < soc_max * 0.85 and battery_kwh > 0:
                        charge = min(net, battery_kw, soc_max - battery_soc)
                        battery_soc += charge
                        remaining = net - charge
                        if remaining > 0.01:
                            export = remaining
                            savings = export * price
                        action = f"Şarj ({charge:.1f})"
                    else:
                        export = net
                        savings = export * price * 0.8
                        action = f"Sat ({export:.1f})"
            else:  # Eksik üretim
                deficit = abs(net)
                # %20 minimum SoC sınırı korunur; bu seviyenin altına inilmez
                available = max(0.0, battery_soc - soc_min)
                if available > 0.05 and battery_kwh > 0 and price >= p_high:
                    discharge = min(deficit, battery_kw, available)
                    battery_soc -= discharge
                    remaining_def = deficit - discharge
                    if remaining_def > 0.01:
                        imp = remaining_def
                        savings = -(imp * price) + discharge * price * 0.8
                        action = f"Batarya+Al ({discharge:.1f}+{imp:.1f})"
                    else:
                        savings = discharge * price * 0.8
                        action = f"Batarya ({discharge:.1f})"
                else:
                    imp = deficit
                    savings = -(imp * price)
                    action = f"Al ({imp:.1f} kWh)  [SoC:{battery_soc/battery_kwh*100:.0f}%]"

            bat_charge.append(charge)
            bat_discharge.append(discharge)
            grid_exp.append(export)
            grid_imp.append(imp)
            grid_action.append(action)
            soc_change.append(charge - discharge)
            h_savings.append(savings)

        # Baseline: bataryasız senaryo
        baseline_cost = 0
        for i in range(hours):
            net_bl = production[i] - consumption[i]
            if net_bl < 0:
                baseline_cost -= abs(net_bl) * prices[min(i, len(prices) - 1)]
            else:
                baseline_cost += net_bl * prices[min(i, len(prices) - 1)] * 0.5

        optimized = sum(h_savings)
        total_savings = optimized - baseline_cost

        return {
            "method": "greedy",
            "timestamps": list(range(hours)),
            "production": list(production),
            "consumption": consumption,
            "battery_charge": bat_charge,
            "battery_discharge": bat_discharge,
            "battery_soc": [],   # Saatlik SoC takibi yapılmaz (LP çözümünde yapılır)
            "grid_export_hourly": grid_exp,
            "grid_import_hourly": grid_imp,
            "grid_action": grid_action,
            "battery_soc_change": soc_change,
            "hourly_savings": h_savings,
            "total_savings": abs(total_savings),
            "savings_pct": abs(total_savings / baseline_cost * 100) if baseline_cost != 0 else 0,
            "battery_cycles": sum(bat_charge) / battery_kwh if battery_kwh > 0 else 0,
            "grid_export_total": sum(grid_exp),
            "export_revenue": sum(grid_exp[i] * prices[min(i, len(prices) - 1)]
                                  for i in range(hours)),
            "soc_min_pct": SOC_MIN_FRAC * 100,   # Arayüz bilgisi: Minimum SoC yüzde değeri (%20)
            "soc_max_pct": SOC_MAX_FRAC * 100,   # Arayüz bilgisi: Maksimum SoC yüzde değeri (%95)
        }

    def _get_consumption(self, profile, hours, daily_kwh=None, season=None):
        """Akademik kaynaklı tüketim profili üret.

        Öncelik sırası:
        1. CSV verisi (varsa — generate_consumption_data.py ile üretilmiş)
        2. Akademik katsayılar × günlük_kWh × mevsim_çarpanı
        3. Geriye uyumlu sabit profil (fallback)
        """
        from modules.utils import (
            get_consumption_from_csv, get_consumption_profile, CONSUMPTION_PROFILES
        )

        # CSV veri kaynağından yükleme denenir
        csv_profile = get_consumption_from_csv(profile)
        if csv_profile:
            return [csv_profile[i % 24] for i in range(hours)]

        # Akademik katsayı tabanlı profil hesaplaması
        try:
            pattern = get_consumption_profile(profile, daily_kwh=daily_kwh, season=season)
        except Exception:
            pattern = CONSUMPTION_PROFILES.get(profile, CONSUMPTION_PROFILES["🏠 Ev"])

        return [pattern[i % 24] for i in range(hours)]
