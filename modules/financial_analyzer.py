"""Finansal Analiz Motoru — NPV, IRR, CO₂, Senaryo Analizi"""
import numpy as np


# ─── Sistem Sabitleri ─── #
CO2_GRID_INTENSITY = 0.432      # kg CO₂/kWh (Türkiye şebeke, TEİAŞ 2023)
CO2_TREE_EQUIV     = 21.77      # kg CO₂/yıl/ağaç (ortalama)
INFLATION_TR       = 0.45       # Yıllık TL enflasyon tahmini
PANEL_DEGRADATION  = 0.005      # %0.5/yıl panel bozunması
BATTERY_CYCLES_MAX = 4000       # Li-ion ömür döngüsü


def calculate_npv_irr(
    daily_savings_tl: float,
    capex_tl: float,
    system_lifetime_years: int = 25,
    discount_rate: float = 0.20,
    annual_opex_tl: float = None,
    electricity_price_escalation: float = 0.30,
) -> dict:
    """
    Net Bugünkü Değer (NBD/NPV) ve İç Verim Oranı (İVO/IRR) hesapla.
    Türkiye koşullarına göre gerçekçi parametre varsayımları.
    """
    if annual_opex_tl is None:
        annual_opex_tl = capex_tl * 0.01  # Yıllık işletme ve bakım maliyeti: %1 CAPEX

    cash_flows = [-capex_tl]  # Yıl 0: Başlangıç yatırım (CAPEX)

    for year in range(1, system_lifetime_years + 1):
        # Elektrik fiyat artışı ve yıllık panel performans bozunması dikkate alınır
        price_escalation = (1 + electricity_price_escalation) ** year
        panel_factor = (1 - PANEL_DEGRADATION) ** year
        annual_savings = daily_savings_tl * 365 * price_escalation * panel_factor
        net_cf = annual_savings - annual_opex_tl
        cash_flows.append(net_cf)

    # Net Bugünkü Değer (NBD / NPV) Hesaplaması
    npv = sum(cf / (1 + discount_rate) ** t for t, cf in enumerate(cash_flows))

    # İç Verim Oranı (IRR) — Newton-Raphson sayısal yöntemiyle hesaplanır
    irr = _calculate_irr(cash_flows)

    # Geri Ödeme Süresi — Kümülatif nakit akışı üzerinden hesaplanır
    cumulative = np.cumsum(cash_flows)
    payback = None
    for i, cum in enumerate(cumulative):
        if cum >= 0:
            # Kesirli yıl interpolasyonu uygulanır
            if i > 0:
                fraction = -cumulative[i - 1] / (cum - cumulative[i - 1])
                payback = i - 1 + fraction
            else:
                payback = 0.0
            break

    total_revenue = sum(cash_flows[1:])
    roi_pct = ((total_revenue - capex_tl * annual_opex_tl / capex_tl * system_lifetime_years) /
               capex_tl * 100) if capex_tl > 0 else 0

    return {
        "npv": npv,
        "irr": irr,
        "payback_years": payback,
        "cash_flows": cash_flows,
        "cumulative_cash_flows": cumulative.tolist(),
        "total_revenue_tl": total_revenue,
        "total_opex_tl": annual_opex_tl * system_lifetime_years,
        "roi_pct": roi_pct,
        "is_profitable": npv > 0,
        "years": list(range(system_lifetime_years + 1)),
    }


def calculate_co2_savings(
    daily_kwh_production: float,
    system_lifetime_years: int = 25,
) -> dict:
    """CO₂ tasarrufu ve eşdeğer çevre etkisi hesapla."""
    annual_kwh = daily_kwh_production * 365
    annual_co2_kg = annual_kwh * CO2_GRID_INTENSITY
    lifetime_co2_kg = annual_co2_kg * system_lifetime_years
    lifetime_co2_ton = lifetime_co2_kg / 1000

    equivalent_trees = annual_co2_kg / CO2_TREE_EQUIV
    equivalent_cars_off_road = annual_co2_kg / 4_600  # Ortalama binek aracı yıllık CO₂ salınımı
    equivalent_coal_kg = annual_co2_kg / 2.86          # Kömür yanması eşdeğerlik katsayısı

    return {
        "annual_kwh": annual_kwh,
        "annual_co2_kg": annual_co2_kg,
        "lifetime_co2_ton": lifetime_co2_ton,
        "equivalent_trees": equivalent_trees,
        "equivalent_cars": equivalent_cars_off_road,
        "equivalent_coal_kg": equivalent_coal_kg,
        "carbon_value_tl": lifetime_co2_ton * 450,  # ~450 TL/ton CO₂ Türkiye karbon fiyatı
    }


def scenario_analysis(
    daily_savings_tl: float,
    capex_tl: float,
    system_lifetime_years: int = 25,
) -> dict:
    """İyimser / Baz / Kötümser senaryo analizi."""
    scenarios = {
        "🐻 Kötümser": {
            "discount_rate": 0.25,
            "price_escalation": 0.20,
            "label": "Düşük elektrik artışı, yüksek iskonto",
        },
        "📊 Baz": {
            "discount_rate": 0.20,
            "price_escalation": 0.30,
            "label": "EPDK tahmini senaryo",
        },
        "🚀 İyimser": {
            "discount_rate": 0.15,
            "price_escalation": 0.40,
            "label": "Yüksek elektrik artışı, düşük iskonto",
        },
    }

    results = {}
    for name, params in scenarios.items():
        r = calculate_npv_irr(
            daily_savings_tl=daily_savings_tl,
            capex_tl=capex_tl,
            system_lifetime_years=system_lifetime_years,
            discount_rate=params["discount_rate"],
            electricity_price_escalation=params["price_escalation"],
        )
        r["label"] = params["label"]
        results[name] = r
    return results


def battery_lifetime_estimate(daily_cycles: float, battery_kwh: float) -> dict:
    """Batarya ömrü tahmini."""
    if daily_cycles <= 0:
        return {"lifetime_years": 15, "replacement_cost_tl": battery_kwh * 3500}
    lifetime_years = BATTERY_CYCLES_MAX / (daily_cycles * 365)
    replacement_cost = battery_kwh * 3500  # ~3500 TL/kWh Li-ion 2024
    return {
        "lifetime_years": min(lifetime_years, 15),
        "total_cycles": BATTERY_CYCLES_MAX,
        "replacement_cost_tl": replacement_cost,
        "annual_depreciation_tl": replacement_cost / max(1, lifetime_years),
    }


def estimate_capex(system_type: str, installed_kw: float, battery_kwh: float = 0) -> dict:
    """Kurulum maliyeti tahmini (Türkiye 2024 piyasa fiyatları)."""
    if "☀️" in system_type or "Güneş" in system_type or system_type == "solar":
        panel_cost = installed_kw * 8_500      # ~8500 TL/kWp
        inverter_cost = installed_kw * 2_500
        mounting_cost = installed_kw * 1_500
        installation_cost = installed_kw * 2_000
        other_cost = installed_kw * 1_000
        equipment_total = panel_cost + inverter_cost + mounting_cost + installation_cost + other_cost
    else:  # Rüzgar
        equipment_total = installed_kw * 25_000  # ~25k TL/kW küçük rüzgar

    battery_cost = battery_kwh * 3_500 if battery_kwh > 0 else 0
    total = equipment_total + battery_cost

    return {
        "total_capex_tl": total,
        "equipment_tl": equipment_total,
        "battery_tl": battery_cost,
        "per_kw_tl": equipment_total / max(1, installed_kw),
        "cost_breakdown": {
            "Panel/Türbin": equipment_total * 0.5,
            "İnvertör": equipment_total * 0.16,
            "Montaj": equipment_total * 0.10,
            "İşçilik": equipment_total * 0.13,
            "Diğer": equipment_total * 0.11,
            "Batarya": battery_cost,
        },
    }


# ─── İç Yardımcı Fonksiyon ─── #
def _calculate_irr(cash_flows: list, max_iter: int = 200, tol: float = 1e-6) -> float | None:
    """Newton-Raphson ile IRR hesapla — OverflowError korumalı."""
    # Başlangıç oranını sıfır geçişine göre belirle
    rate = 0.1

    for _ in range(max_iter):
        try:
            # rate < -1 olursa (1+rate) negatif/sıfır → güvenli sınır koy
            if rate <= -1.0:
                rate = -0.9999

            npv  = sum(cf / (1.0 + rate) ** t       for t, cf in enumerate(cash_flows))
            dnpv = sum(-t * cf / (1.0 + rate) ** (t + 1) for t, cf in enumerate(cash_flows))

            # Türev sıfıra yakınsa dur (bölme patlamaması için)
            if abs(dnpv) < 1e-12:
                break

            new_rate = rate - npv / dnpv

            # Sayısal patlama kontrolü
            if not (-1.0 < new_rate < 100.0):  # IRR %100'ü geçemez, -1'in altına düşemez
                return None  # Yakınsamadı, güvenli şekilde None döndür

            if abs(new_rate - rate) < tol:
                return round(new_rate * 100, 2)  # Yüzde olarak döndür

            rate = new_rate

        except (OverflowError, ZeroDivisionError, ValueError):
            return None  # Hata durumunda güvenli çıkış

    return None  # max_iter doldu, yakınsamadı
