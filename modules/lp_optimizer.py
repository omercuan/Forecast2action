"""Batarya Optimizasyonu — Linear Programming (Greedy yerine Optimal)

scipy.optimize.linprog kullanarak 48 saatlik tahmin ufkunda
batarya şarj/deşarj kararını matematiksel olarak optimize eder.

Amaç: net geliri MAXIMIZE et (linprog minimize ettiği için negatif gelir minimize edilir)
Kısıtlar:
  - Batarya SoC her saat [SoC_min, SoC_max] arasında kalmalı
  - Şarj gücü ≤ max_charge_kw
  - Deşarj gücü ≤ max_discharge_kw
  - Şebeke import/export ≥ 0
  - Enerji dengesi: üretim + import + discharge = tüketim + export + charge
"""

import numpy as np
from modules.utils import CONSUMPTION_PROFILES

try:
    from scipy.optimize import linprog
    SCIPY_OK = True
except ImportError:
    SCIPY_OK = False


class LPOptimizer:
    """scipy.linprog tabanlı optimal batarya planlaması."""

    def optimize(self, production, prices, battery_kwh, battery_kw,
                 consumption_profile="🏠 Ev", soc_init_frac=0.50,
                 soc_min_frac=0.20, soc_max_frac=0.95,
                 charge_eff=0.95, discharge_eff=0.95):
        """
        Parameters
        ----------
        production        : list[float] — saatlik tahmin edilen üretim (kW)
        prices            : list[float] — saatlik elektrik fiyatı (TL/kWh)
        battery_kwh       : float       — batarya kapasitesi (kWh)
        battery_kw        : float       — max şarj/deşarj gücü (kW)
        consumption_profile: str        — tüketim profili
        soc_init_frac     : float       — başlangıç doluluk oranı (0-1)
        soc_min_frac      : float       — min doluluk oranı
        soc_max_frac      : float       — max doluluk oranı
        charge_eff        : float       — şarj verimliliği
        discharge_eff     : float       — deşarj verimliliği

        Returns
        -------
        dict — BatteryOptimizer ile aynı format
        """
        if not SCIPY_OK:
            # scipy kütüphanesi mevcut değilse greedy algoritmaya geçiş yapılır
            from modules.battery_optimizer import BatteryOptimizer
            return BatteryOptimizer().optimize(
                production, prices, battery_kwh, battery_kw, consumption_profile)

        hours = len(production)
        consumption = self._get_consumption(consumption_profile, hours)
        prices_arr = np.array(prices[:hours], dtype=float)
        prod_arr = np.array(production[:hours], dtype=float)
        cons_arr = np.array(consumption[:hours], dtype=float)

        SoC_min = battery_kwh * soc_min_frac
        SoC_max = battery_kwh * soc_max_frac
        SoC_init = battery_kwh * soc_init_frac

        # ── Karar Değişkeni Gösterimi (her saat için sırasıyla) ──
        # x = [c_0…c_T, d_0…d_T, e_0…e_T, i_0…i_T, s_0…s_T]
        # c: şarj (kWh), d: deşarj (kWh), e: şebekeye ihracat (kWh),
        # i: şebekeden ithalat (kWh), s: şarj durumu — SoC (kWh)
        T = hours
        N = 5 * T  # toplam değişken sayısı

        idx_c = slice(0,   T)         # charge
        idx_d = slice(T,   2*T)       # discharge
        idx_e = slice(2*T, 3*T)       # export
        idx_i = slice(3*T, 4*T)       # import
        idx_s = slice(4*T, 5*T)       # SoC

        # ── Amaç Fonksiyonu: -(ihracat_geliri - ithalat_maliyeti) minimize et ──
        c_obj = np.zeros(N)
        c_obj[idx_e] = -prices_arr          # Şebekeye ihracat geliri (minimize için negatif)
        c_obj[idx_i] = +prices_arr          # Şebekeden ithalat maliyeti

        # ── Değişken Kutu Sınırları ──
        bounds = (
            [(0, battery_kw)] * T +        # charge
            [(0, battery_kw)] * T +        # discharge
            [(0, None)] * T +              # export
            [(0, None)] * T +              # import
            [(SoC_min, SoC_max)] * T       # SoC
        )

        # ── Eşitlik Kısıtları — Matematiksel Model Özeti ──
        # 1) Enerji Dengesi: Üretim + İthalat + Deşarj = Tüketim + İhracat + Şarj
        #    → Şarj - Deşarj + İhracat - İthalat = Üretim - Tüketim
        # 2) SoC Güncelleme: s[t] = s[t-1] + c[t]*eta_c - d[t]/eta_d
        #    → -c[t]*eta_c + d[t]/eta_d + s[t] - s[t-1] = 0  (t≥1)
        #    → -c[0]*eta_c + d[0]/eta_d + s[0] = SoC_başlangıç

        A_eq = np.zeros((2 * T, N))
        b_eq = np.zeros(2 * T)

        for t in range(T):
            # Enerji dengesi kısıtı (satır indeksi: t)
            A_eq[t, t]      =  1.0   # charge
            A_eq[t, T+t]    = -1.0   # discharge
            A_eq[t, 2*T+t]  =  1.0   # export
            A_eq[t, 3*T+t]  = -1.0   # import
            b_eq[t] = prod_arr[t] - cons_arr[t]

            # SoC güncelleme kısıtı (satır indeksi: T+t)
            A_eq[T+t, t]    = -charge_eff         # Şarj işlemi SoC'u artırır
            A_eq[T+t, T+t]  = 1.0 / discharge_eff  # Deşarj işlemi SoC'u azaltır
            A_eq[T+t, 4*T+t] = 1.0            # s[t]
            if t == 0:
                b_eq[T+t] = SoC_init
            else:
                A_eq[T+t, 4*T+t-1] = -1.0     # -s[t-1]
                b_eq[T+t] = 0.0

        # ── LP Çözümü — HiGHS Sözçözücü ──
        result = linprog(
            c_obj,
            A_eq=A_eq, b_eq=b_eq,
            bounds=bounds,
            method="highs",
            options={"disp": False}
        )

        if result.status != 0:
            # LP çözümü başarısız olursa greedy algoritma devreye alınır
            from modules.battery_optimizer import BatteryOptimizer
            fb = BatteryOptimizer().optimize(
                production, prices, battery_kwh, battery_kw, consumption_profile)
            fb["method"] = "greedy_fallback"
            return fb

        x = result.x
        charge_arr    = x[idx_c]
        discharge_arr = x[idx_d]
        export_arr    = x[idx_e]
        import_arr    = x[idx_i]
        soc_arr       = x[idx_s]

        # ── Saatlik Operasyon Etiketi Üretimi ──
        actions = []
        for t in range(T):
            c, d, e, im = charge_arr[t], discharge_arr[t], export_arr[t], import_arr[t]
            if c > 0.05 and e > 0.05:
                actions.append(f"Şarj+Sat ({c:.1f}+{e:.1f})")
            elif c > 0.05:
                actions.append(f"Şarj ({c:.1f} kWh)")
            elif d > 0.05 and e > 0.05:
                actions.append(f"Bat+Sat ({d:.1f}+{e:.1f})")
            elif d > 0.05:
                actions.append(f"Batarya ({d:.1f} kWh)")
            elif e > 0.05:
                actions.append(f"Sat ({e:.1f} kWh)")
            elif im > 0.05:
                actions.append(f"Al ({im:.1f} kWh)")
            else:
                actions.append("Bekle")

        hourly_savings = (
            export_arr * prices_arr - import_arr * prices_arr
        )

        # Karşılaştırma tabanı: Bataryasız çalışma senaryosu
        baseline_cost = 0.0
        for t in range(T):
            net_bl = prod_arr[t] - cons_arr[t]
            p = prices_arr[t]
            if net_bl < 0:
                baseline_cost -= abs(net_bl) * p
            else:
                baseline_cost += net_bl * p * 0.5

        optimized = float(hourly_savings.sum())
        total_savings = optimized - baseline_cost

        return {
            "method": "linear_programming",
            "timestamps": list(range(T)),
            "production": prod_arr.tolist(),
            "consumption": cons_arr.tolist(),
            "battery_charge": charge_arr.tolist(),
            "battery_discharge": discharge_arr.tolist(),
            "battery_soc": soc_arr.tolist(),
            "grid_export_hourly": export_arr.tolist(),
            "grid_import_hourly": import_arr.tolist(),
            "grid_action": actions,
            "battery_soc_change": (charge_arr - discharge_arr).tolist(),
            "hourly_savings": hourly_savings.tolist(),
            "total_savings": abs(total_savings),
            "savings_pct": abs(total_savings / baseline_cost * 100) if baseline_cost != 0 else 0,
            "battery_cycles": float(charge_arr.sum() / battery_kwh) if battery_kwh > 0 else 0,
            "grid_export_total": float(export_arr.sum()),
            "export_revenue": float((export_arr * prices_arr).sum()),
            "lp_objective": -result.fun,
            "soc_min_pct": soc_min_frac * 100,   # Arayüz bilgisi: Minimum SoC yüzde değeri
            "soc_max_pct": soc_max_frac * 100,   # Arayüz bilgisi: Maksimum SoC yüzde değeri
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
