"""AI Öneri Motoru — Kural Tabanlı Akıllı Tavsiye Sistemi"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class SystemContext:
    """Sistem bağlamı: tahmin + optimizasyon + finansal sonuçlar."""
    system_type: str
    installed_kw: float
    city: str
    lat: float
    lon: float
    battery_kwh: float = 0.0
    # Tahmin sonuçları
    total_production_kwh: Optional[float] = None
    avg_confidence: Optional[float] = None
    low_production_hours: Optional[int] = None
    # Optimizasyon sonuçları
    total_savings_tl: Optional[float] = None
    battery_cycles: Optional[float] = None
    export_revenue_tl: Optional[float] = None
    # Finansal
    npv: Optional[float] = None
    irr: Optional[float] = None
    payback_years: Optional[float] = None
    # Anomali
    anomaly_detected: bool = False
    anomaly_severity: Optional[str] = None


class AIAdvisor:
    """Kural tabanlı AI Öneri Motoru."""

    def generate_recommendations(self, ctx: SystemContext) -> list[dict]:
        """Bağlama göre öneri listesi üret. Her öneri: {icon, title, detail, priority}."""
        recommendations = []

        # ─── Üretim analizi önerileri ─── #
        if ctx.total_production_kwh is not None:
            daily_avg = ctx.total_production_kwh / 2  # 48h → günlük
            recommendations.extend(self._production_recs(ctx, daily_avg))

        # ─── Batarya önerileri ─── #
        if ctx.battery_kwh > 0:
            recommendations.extend(self._battery_recs(ctx))

        # ─── Finansal öneriler ─── #
        if ctx.npv is not None:
            recommendations.extend(self._financial_recs(ctx))

        # ─── Lokasyon önerileri ─── #
        recommendations.extend(self._location_recs(ctx))

        # ─── Anomali önerileri ─── #
        if ctx.anomaly_detected:
            recommendations.extend(self._anomaly_recs(ctx))

        # Önceliğe göre sırala
        priority_order = {"🔴 Kritik": 0, "🟠 Yüksek": 1, "🟡 Orta": 2, "🟢 Bilgi": 3}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 99))

        return recommendations[:8]  # Max 8 öneri

    def generate_summary(self, ctx: SystemContext) -> str:
        """Tek cümlelik sistem özeti."""
        is_solar = "☀️" in ctx.system_type or "Güneş" in ctx.system_type

        parts = []

        if ctx.total_production_kwh is not None:
            daily = ctx.total_production_kwh / 2
            parts.append(f"günlük ~{daily:.1f} kWh üretim")

        if ctx.total_savings_tl is not None:
            daily_sav = ctx.total_savings_tl / 2
            parts.append(f"günde ~{daily_sav:.0f} TL tasarruf")

        if ctx.payback_years is not None:
            parts.append(f"{ctx.payback_years:.1f} yılda geri ödeme")

        system_name = "Güneş Enerjisi Sistemi" if is_solar else "Rüzgar Enerji Sistemi"
        loc = ctx.city
        kw = ctx.installed_kw

        if parts:
            return f"📍 {loc}'daki {kw} kW {system_name}: {', '.join(parts)}."
        return f"📍 {loc} için {kw} kW {system_name} analizi tamamlandı."

    # ─── Özel öneri grupları ─── #

    def _production_recs(self, ctx: SystemContext, daily_kwh: float) -> list[dict]:
        recs = []
        is_solar = "☀️" in ctx.system_type or "Güneş" in ctx.system_type

        if ctx.avg_confidence and ctx.avg_confidence < 60:
            recs.append({
                "icon": "⚠️",
                "title": "Düşük Tahmin Güveni",
                "detail": f"Ortalama güven skoru %{ctx.avg_confidence:.0f}. "
                          f"Bulutlu hava tahminleri belirsizliği artırıyor. "
                          f"Önemli kararlar için P10 senaryosunu baz alın.",
                "priority": "🟠 Yüksek",
            })

        if ctx.low_production_hours and ctx.low_production_hours > 18:
            recs.append({
                "icon": "🌙",
                "title": "Yüksek Düşük-Üretim Süresi",
                "detail": f"48 saatin {ctx.low_production_hours} saatinde üretim 0.5 kW altında. "
                          f"{'Gece ve bulutlu saatleri optimize etmek için batarya kapasitesini artırın.' if ctx.battery_kwh > 0 else 'Batarya ekleyerek gece tüketimini karşılayabilirsiniz.'}",
                "priority": "🟡 Orta",
            })

        if is_solar and ctx.lat < 37:
            recs.append({
                "icon": "☀️",
                "title": "Güneyde Yüksek Panel Sıcaklığı Riski",
                "detail": f"{ctx.city} enleminde ({ctx.lat:.1f}°) yaz aylarında panel sıcaklığı "
                          f"70°C'yi aşabilir. Bifacial panel veya soğutma aralığı bırakarak "
                          f"%8-12 ek verim elde edebilirsiniz.",
                "priority": "🟡 Orta",
            })

        if daily_kwh > ctx.installed_kw * 4:
            recs.append({
                "icon": "🏆",
                "title": "Mükemmel Üretim Performansı",
                "detail": f"Günlük {daily_kwh:.1f} kWh üretim, kurulu güç başına "
                          f"{daily_kwh/ctx.installed_kw:.1f} kWh/kWp. Bu değer Türkiye ortalamasının üzerinde.",
                "priority": "🟢 Bilgi",
            })

        return recs

    def _battery_recs(self, ctx: SystemContext) -> list[dict]:
        recs = []

        if ctx.battery_cycles and ctx.battery_cycles > 2.5:
            recs.append({
                "icon": "🔋",
                "title": "Yüksek Batarya Kullanım Yoğunluğu",
                "detail": f"48 saatte {ctx.battery_cycles:.1f} döngü — günlük {ctx.battery_cycles/2:.1f} döngü. "
                          f"Li-ion batarya için optimal aralık günde 0.5-1 döngüdür. "
                          f"Kapasite artırımı veya şarj stratejisi değişikliği önerilir.",
                "priority": "🟠 Yüksek",
            })

        if ctx.battery_kwh < ctx.installed_kw * 1.5:
            recs.append({
                "icon": "📈",
                "title": "Batarya Kapasitesi Artırılabilir",
                "detail": f"Mevcut {ctx.battery_kwh} kWh kapasite, {ctx.installed_kw} kW sisteminiz için "
                          f"alt sınırda. Optimal oran 1.5-2x kurulu güç (~{ctx.installed_kw*2:.0f} kWh). "
                          f"Kapasite artırımı %20-35 daha fazla tasarruf sağlayabilir.",
                "priority": "🟡 Orta",
            })

        if ctx.export_revenue_tl and ctx.export_revenue_tl > 0:
            recs.append({
                "icon": "💡",
                "title": "Şebekeye Satış Geliri",
                "detail": f"48 saatte {ctx.export_revenue_tl:.0f} TL şebeke satış geliri. "
                          f"YEKDEM lisanssız üretim kotanızı kontrol edin (≤10 kW tam muafiyet). "
                          f"Yıllık projeksiyon: ~{ctx.export_revenue_tl/2*365:.0f} TL.",
                "priority": "🟢 Bilgi",
            })

        return recs

    def _financial_recs(self, ctx: SystemContext) -> list[dict]:
        recs = []

        if ctx.npv and ctx.npv < 0:
            recs.append({
                "icon": "🔴",
                "title": "Negatif NPV — Yatırım Gözden Geçirilmeli",
                "detail": f"Mevcut parametrelerle NPV negatif ({ctx.npv:,.0f} TL). "
                          f"Sistem boyutunu küçültmeyi, teşvik programlarını (YEKDEM, KOSGEB) "
                          f"veya farklı finansman modelini değerlendirin.",
                "priority": "🔴 Kritik",
            })
        elif ctx.npv and ctx.npv > 0:
            recs.append({
                "icon": "✅",
                "title": "Pozitif NPV — Karlı Yatırım",
                "detail": f"Net Bugünkü Değer: +{ctx.npv:,.0f} TL. "
                          f"{'IRR %' + str(ctx.irr) + ' ile piyasa faizinin üzerinde.' if ctx.irr else ''} "
                          f"KOSGEB ve devlet teşvikleri ile NPV daha da artabilir.",
                "priority": "🟢 Bilgi",
            })

        if ctx.payback_years and ctx.payback_years > 10:
            recs.append({
                "icon": "📅",
                "title": "Uzun Geri Ödeme Süresi",
                "detail": f"{ctx.payback_years:.1f} yıllık geri ödeme süresini kısaltmak için: "
                          f"1) KOSGEB hibe (%30-50 destek), "
                          f"2) Banka yeşil kredi (düşük faiz), "
                          f"3) Kiracı modeli (sıfır sermaye) araştırın.",
                "priority": "🟡 Orta",
            })
        elif ctx.payback_years and ctx.payback_years < 7:
            recs.append({
                "icon": "🚀",
                "title": "Hızlı Geri Ödeme",
                "detail": f"Sadece {ctx.payback_years:.1f} yılda geri ödeme — mükemmel performans! "
                          f"Sistem büyütmeyi veya ikinci bir tesis kurmayı değerlendirin.",
                "priority": "🟢 Bilgi",
            })

        return recs

    def _location_recs(self, ctx: SystemContext) -> list[dict]:
        recs = []
        is_solar = "☀️" in ctx.system_type or "Güneş" in ctx.system_type

        # Güneş için uygun il kontrolü
        if is_solar:
            high_solar_cities = ["Şanlıurfa", "Gaziantep", "Mardin", "Antalya", "Adana",
                                  "Hatay", "Diyarbakır", "Batman", "Kilis"]
            low_solar_cities = ["Rize", "Artvin", "Trabzon", "Giresun", "Ordu", "Zonguldak"]

            if any(city in ctx.city for city in high_solar_cities):
                recs.append({
                    "icon": "🌟",
                    "title": f"{ctx.city} — Yüksek Güneş Potansiyeli",
                    "detail": f"Güneydoğu konumunuz ({ctx.lat:.1f}°N) Türkiye'nin en yüksek "
                              f"radyasyon değerlerine sahip. Optimum panel açısı ~{max(20, 37-int(ctx.lat))}° "
                              f"güneye yönelik. Bifacial panel ile %10-15 ek kazanç mümkün.",
                    "priority": "🟢 Bilgi",
                })
            elif any(city in ctx.city for city in low_solar_cities):
                recs.append({
                    "icon": "⚠️",
                    "title": f"{ctx.city} — Bulutlu İklim Uyarısı",
                    "detail": f"Karadeniz iklimi güneş sistemi verimliliğini düşürür. "
                              f"Mikro-inverter teknolojisi ile gölgeli koşullarda %15-20 "
                              f"daha iyi performans elde edin. Hibrit rüzgar+güneş sistemi önerilebilir.",
                    "priority": "🟠 Yüksek",
                })
        else:  # Rüzgar
            high_wind_cities = ["Çanakkale", "Balıkesir", "İzmir", "Tekirdağ",
                                 "Kırklareli", "Sinop", "İstanbul"]
            if any(city in ctx.city for city in high_wind_cities):
                recs.append({
                    "icon": "💨",
                    "title": f"{ctx.city} — Yüksek Rüzgar Potansiyeli",
                    "detail": f"Ege/Marmara konumunuz yüksek rüzgar potansiyeline sahip. "
                              f"Dikey eksenli türbin (VAWT) kentsel alanlarda, yatay eksenli (HAWT) "
                              f"açık arazide daha verimli. Hub yüksekliğini 50m+ tutun.",
                    "priority": "🟢 Bilgi",
                })

        return recs

    def _anomaly_recs(self, ctx: SystemContext) -> list[dict]:
        severity = ctx.anomaly_severity or "UYARI"
        recs = [{
            "icon": "🚨",
            "title": f"Sistem Anomalisi — {severity}",
            "detail": "Anlık üretim beklentinin önemli altında. Acil kontrol listesi: "
                      "1) Paneller/kanatlar fiziksel kontrolü, "
                      "2) İnvertör alarm LED'leri, "
                      "3) DC kablo termik görüntüsü, "
                      "4) Akü BMS hata kodu sorgusu.",
            "priority": "🔴 Kritik" if severity == "KRİTİK" else "🟠 Yüksek",
        }]
        return recs
