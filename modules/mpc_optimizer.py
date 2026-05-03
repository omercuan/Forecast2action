"""MPC — Model Predictive Control Optimizasyonu

Kayan ufuklu (rolling-horizon) LP tabanlı batarya optimizasyonu.
Her adımda N saatlik ufku LP ile çözer, yalnızca ilk kararı uygular,
sonra bir saat kayar ve yeniden çözer.

Neden MPC?
- Gerçek endüstri standardı (Tesla Powerwall, SCADA sistemleri)
- Tahmin belirsizliğine karşı doğal sağlamlık
- Gelecekteki fiyat/üretim bilgisini değerlendirirken anlık kararlar alır

Referans:
  Morari & Lee (1999), Model predictive control: past, present and future,
  Computers & Chemical Engineering, 23(4-5), 667-682.
"""

import numpy as np
from modules.utils import CONSUMPTION_PROFILES

try:
    from scipy.optimize import linprog
    SCIPY_OK = True
except ImportError:
    SCIPY_OK = False


class MPCOptimizer:
    """
    Model Predictive Control tabanlı batarya optimizasyonu.

    Her saat için:
      1. [t, t+horizon) aralığında LP çöz
      2. Yalnızca t anındaki şarj/deşarj kararını uygula
      3. t+1'e geç ve tekrar çöz
    """

    def __init__(self, horizon: int = 6):
        """
        Parameters
        ----------
        horizon : int
            Kayan ufuk uzunluğu (saat). Varsayılan 6.
            Daha büyük ufuk → daha iyi karar, daha yavaş hesap.
        """
        self.horizon = horizon

    def optimize(
        self,
        production,
        prices,
        battery_kwh,
        battery_kw,
        consumption_profile="🏠 Ev",
        soc_init_frac: float = 0.50,
        soc_min_frac: float = 0.20,
        soc_max_frac: float = 0.95,
        charge_eff: float = 0.95,
        discharge_eff: float = 0.95,
    ) -> dict:
        """
        Parameters
        ----------
        production         : list[float] — saatlik üretim tahmini (kW)
        prices             : list[float] — saatlik fiyat (TL/kWh)
        battery_kwh        : float       — batarya kapasitesi
        battery_kw         : float       — max şarj/deşarj gücü
        consumption_profile: str         — tüketim profili
        soc_init_frac      : float       — başlangıç SoC oranı
        soc_min_frac       : float       — minimum SoC oranı
        soc_max_frac       : float       — maksimum SoC oranı
        charge_eff         : float       — şarj verimliliği
        discharge_eff      : float       — deşarj verimliliği

        Returns
        -------
        dict — BatteryOptimizer/LPOptimizer ile uyumlu sonuç formatı
        """
        if not SCIPY_OK:
            from modules.battery_optimizer import BatteryOptimizer
            result = BatteryOptimizer().optimize(
                production, prices, battery_kwh, battery_kw, consumption_profile
            )
            result["method"] = "greedy_fallback"
            return result

        hours = len(production)
        consumption = self._get_consumption(consumption_profile, hours)

        prod_arr  = np.array(production[:hours], dtype=float)
        cons_arr  = np.array(consumption[:hours], dtype=float)
        price_arr = np.array(prices[:hours], dtype=float)

        SoC_min  = battery_kwh * soc_min_frac
        SoC_max  = battery_kwh * soc_max_frac
        soc_cur  = battery_kwh * soc_init_frac   # mevcut SoC

        # Sonuç dizileri
        charge_arr    = np.zeros(hours)
        discharge_arr = np.zeros(hours)
        export_arr    = np.zeros(hours)
        import_arr    = np.zeros(hours)
        soc_arr       = np.zeros(hours)
        actions       = []
        horizon_lens  = []  # debug: her adımda kullanılan ufuk

        for t in range(hours):
            h_end = min(t + self.horizon, hours)
            N = h_end - t  # bu adımda kullanılan ufuk

            horizon_lens.append(N)
            if N == 0:
                soc_arr[t] = soc_cur
                actions.append("Bekle")
                continue

            # Ufuk içindeki veriler
            p_seg   = prod_arr[t:h_end]
            c_seg   = cons_arr[t:h_end]
            pr_seg  = price_arr[t:h_end]

            # LP çöz — yalnızca bu ufuk için
            lp_result = self._solve_horizon_lp(
                p_seg, c_seg, pr_seg,
                battery_kwh, battery_kw,
                soc_cur, SoC_min, SoC_max,
                charge_eff, discharge_eff,
            )

            if lp_result is None:
                # LP başarısız → greedy karar
                c_t, d_t, e_t, im_t, soc_next = self._greedy_step(
                    prod_arr[t], cons_arr[t], price_arr[t],
                    soc_cur, SoC_min, SoC_max, battery_kw,
                    np.percentile(price_arr, 33),
                    np.percentile(price_arr, 67),
                )
            else:
                # Yalnızca ilk adım uygulanır (MPC prensibi)
                c_t   = float(lp_result["charge"][0])
                d_t   = float(lp_result["discharge"][0])
                e_t   = float(lp_result["export"][0])
                im_t  = float(lp_result["import_"][0])
                soc_next = soc_cur + c_t * charge_eff - d_t / discharge_eff
                soc_next = float(np.clip(soc_next, SoC_min, SoC_max))

            # Kaydet
            charge_arr[t]    = c_t
            discharge_arr[t] = d_t
            export_arr[t]    = e_t
            import_arr[t]    = im_t
            soc_arr[t]       = soc_next
            soc_cur          = soc_next

            # Aksiyon etiketi
            if c_t > 0.05 and e_t > 0.05:
                actions.append(f"Şarj+Sat ({c_t:.1f}+{e_t:.1f})")
            elif c_t > 0.05:
                actions.append(f"Şarj ({c_t:.1f} kWh)")
            elif d_t > 0.05 and e_t > 0.05:
                actions.append(f"Bat+Sat ({d_t:.1f}+{e_t:.1f})")
            elif d_t > 0.05:
                actions.append(f"Batarya ({d_t:.1f} kWh)")
            elif e_t > 0.05:
                actions.append(f"Sat ({e_t:.1f} kWh)")
            elif im_t > 0.05:
                actions.append(f"Al ({im_t:.1f} kWh)")
            else:
                actions.append("Bekle")

        # Tasarruf hesapla
        hourly_savings = export_arr * price_arr - import_arr * price_arr

        # Baseline: bataryasız
        baseline_cost = 0.0
        for t in range(hours):
            net_bl = prod_arr[t] - cons_arr[t]
            p = price_arr[t]
            if net_bl < 0:
                baseline_cost -= abs(net_bl) * p
            else:
                baseline_cost += net_bl * p * 0.5

        optimized = float(hourly_savings.sum())
        total_savings = optimized - baseline_cost

        return {
            "method": "mpc",
            "mpc_horizon": self.horizon,
            "timestamps": list(range(hours)),
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
            "savings_pct": (
                abs(total_savings / baseline_cost * 100) if baseline_cost != 0 else 0
            ),
            "battery_cycles": (
                float(charge_arr.sum() / battery_kwh) if battery_kwh > 0 else 0
            ),
            "grid_export_total": float(export_arr.sum()),
            "export_revenue": float((export_arr * price_arr).sum()),
            "lp_objective": float(hourly_savings.sum()),
            "soc_min_pct": soc_min_frac * 100,
            "soc_max_pct": soc_max_frac * 100,
        }

    # ──────────────────────────────────────────────────────── #
    #   Yardımcı: tek ufuk LP                                  #
    # ──────────────────────────────────────────────────────── #
    def _solve_horizon_lp(
        self, prod, cons, prices,
        battery_kwh, battery_kw,
        soc_init, SoC_min, SoC_max,
        charge_eff, discharge_eff,
    ):
        """
        N saatlik küçük LP — MPC ufku için.
        Değişkenler: [c(T), d(T), e(T), i(T), s(T)]
        """
        T = len(prod)
        N = 5 * T

        idx_c = slice(0,   T)
        idx_d = slice(T,   2*T)
        idx_e = slice(2*T, 3*T)
        idx_i = slice(3*T, 4*T)
        idx_s = slice(4*T, 5*T)

        c_obj = np.zeros(N)
        c_obj[idx_e] = -prices   # geliri maksimize et
        c_obj[idx_i] = +prices   # maliyeti minimize et

        bounds = (
            [(0, battery_kw)] * T +
            [(0, battery_kw)] * T +
            [(0, None)]       * T +
            [(0, None)]       * T +
            [(SoC_min, SoC_max)] * T
        )

        A_eq = np.zeros((2 * T, N))
        b_eq = np.zeros(2 * T)

        for t in range(T):
            # Enerji dengesi
            A_eq[t, t]      =  1.0    # charge
            A_eq[t, T+t]    = -1.0    # discharge
            A_eq[t, 2*T+t]  =  1.0    # export
            A_eq[t, 3*T+t]  = -1.0    # import
            b_eq[t] = prod[t] - cons[t]

            # SoC güncelleme
            A_eq[T+t, t]      = -charge_eff
            A_eq[T+t, T+t]    =  1.0 / discharge_eff
            A_eq[T+t, 4*T+t]  =  1.0
            if t == 0:
                b_eq[T+t] = soc_init
            else:
                A_eq[T+t, 4*T+t-1] = -1.0
                b_eq[T+t] = 0.0

        try:
            res = linprog(
                c_obj,
                A_eq=A_eq, b_eq=b_eq,
                bounds=bounds,
                method="highs",
                options={"disp": False},
            )
            if res.status != 0:
                return None
            x = res.x
            return {
                "charge":    x[idx_c],
                "discharge": x[idx_d],
                "export":    x[idx_e],
                "import_":   x[idx_i],
                "soc":       x[idx_s],
            }
        except Exception:
            return None

    # ──────────────────────────────────────────────────────── #
    #   Yardımcı: LP başarısız olduğunda greedy adım           #
    # ──────────────────────────────────────────────────────── #
    def _greedy_step(
        self, prod, cons, price,
        soc, SoC_min, SoC_max, battery_kw,
        p_low, p_high,
    ):
        net = prod - cons
        charge = discharge = export_ = import_ = 0.0

        if net > 0:
            if price <= p_low and soc < SoC_max:
                charge  = min(net, battery_kw, SoC_max - soc)
                export_ = max(0.0, net - charge)
            else:
                export_ = net
        else:
            deficit   = abs(net)
            available = max(0.0, soc - SoC_min)
            if available > 0.05 and price >= p_high:
                discharge = min(deficit, battery_kw, available)
                import_   = max(0.0, deficit - discharge)
            else:
                import_ = deficit

        soc_next = soc + charge - discharge
        soc_next = float(np.clip(soc_next, SoC_min, SoC_max))
        return charge, discharge, export_, import_, soc_next

    # ──────────────────────────────────────────────────────── #
    #   Yardımcı: tüketim profili                              #
    # ──────────────────────────────────────────────────────── #
    def _get_consumption(self, profile, hours, daily_kwh=None, season=None):
        from modules.utils import (
            get_consumption_from_csv, get_consumption_profile, CONSUMPTION_PROFILES
        )
        csv_profile = get_consumption_from_csv(profile)
        if csv_profile:
            return [csv_profile[i % 24] for i in range(hours)]
        try:
            pattern = get_consumption_profile(profile, daily_kwh=daily_kwh, season=season)
        except Exception:
            pattern = CONSUMPTION_PROFILES.get(profile, CONSUMPTION_PROFILES["🏠 Ev"])
        return [pattern[i % 24] for i in range(hours)]
