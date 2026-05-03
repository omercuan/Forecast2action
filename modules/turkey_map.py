"""Türkiye İlleri Yenilenebilir Enerji Potansiyeli Haritası"""
import folium
import json
import os

# 81 il verisi (PVGIS + MENR referans değerler)
TURKEY_PROVINCES = [
    {"il": "Adana", "lat": 37.00, "lon": 35.32, "solar": 1650, "wind": 3.5},
    {"il": "Adıyaman", "lat": 37.76, "lon": 38.28, "solar": 1700, "wind": 2.8},
    {"il": "Afyonkarahisar", "lat": 38.74, "lon": 30.54, "solar": 1480, "wind": 3.2},
    {"il": "Ağrı", "lat": 39.72, "lon": 43.05, "solar": 1580, "wind": 3.0},
    {"il": "Aksaray", "lat": 38.37, "lon": 34.03, "solar": 1560, "wind": 3.1},
    {"il": "Amasya", "lat": 40.65, "lon": 35.83, "solar": 1360, "wind": 2.5},
    {"il": "Ankara", "lat": 39.93, "lon": 32.86, "solar": 1500, "wind": 3.3},
    {"il": "Antalya", "lat": 36.90, "lon": 30.71, "solar": 1700, "wind": 3.0},
    {"il": "Ardahan", "lat": 41.11, "lon": 42.70, "solar": 1450, "wind": 4.0},
    {"il": "Artvin", "lat": 41.18, "lon": 41.82, "solar": 1200, "wind": 2.5},
    {"il": "Aydın", "lat": 37.85, "lon": 27.85, "solar": 1600, "wind": 3.5},
    {"il": "Balıkesir", "lat": 39.65, "lon": 27.89, "solar": 1450, "wind": 5.5},
    {"il": "Bartın", "lat": 41.64, "lon": 32.34, "solar": 1150, "wind": 3.0},
    {"il": "Batman", "lat": 37.88, "lon": 41.13, "solar": 1720, "wind": 2.8},
    {"il": "Bayburt", "lat": 40.26, "lon": 40.23, "solar": 1400, "wind": 3.2},
    {"il": "Bilecik", "lat": 40.06, "lon": 30.00, "solar": 1350, "wind": 3.0},
    {"il": "Bingöl", "lat": 38.88, "lon": 40.49, "solar": 1580, "wind": 2.5},
    {"il": "Bitlis", "lat": 38.40, "lon": 42.11, "solar": 1600, "wind": 3.0},
    {"il": "Bolu", "lat": 40.73, "lon": 31.61, "solar": 1250, "wind": 2.8},
    {"il": "Burdur", "lat": 37.72, "lon": 30.29, "solar": 1550, "wind": 3.2},
    {"il": "Bursa", "lat": 40.19, "lon": 29.06, "solar": 1350, "wind": 3.5},
    {"il": "Çanakkale", "lat": 40.15, "lon": 26.41, "solar": 1400, "wind": 6.5},
    {"il": "Çankırı", "lat": 40.60, "lon": 33.62, "solar": 1400, "wind": 2.8},
    {"il": "Çorum", "lat": 40.55, "lon": 34.96, "solar": 1380, "wind": 2.5},
    {"il": "Denizli", "lat": 37.77, "lon": 29.09, "solar": 1550, "wind": 3.0},
    {"il": "Diyarbakır", "lat": 37.91, "lon": 40.24, "solar": 1720, "wind": 3.0},
    {"il": "Düzce", "lat": 40.84, "lon": 31.16, "solar": 1200, "wind": 2.5},
    {"il": "Edirne", "lat": 41.68, "lon": 26.56, "solar": 1350, "wind": 4.0},
    {"il": "Elazığ", "lat": 38.68, "lon": 39.23, "solar": 1600, "wind": 3.0},
    {"il": "Erzincan", "lat": 39.75, "lon": 39.49, "solar": 1500, "wind": 2.8},
    {"il": "Erzurum", "lat": 39.91, "lon": 41.28, "solar": 1520, "wind": 3.5},
    {"il": "Eskişehir", "lat": 39.78, "lon": 30.52, "solar": 1450, "wind": 3.3},
    {"il": "Gaziantep", "lat": 37.07, "lon": 37.38, "solar": 1680, "wind": 3.2},
    {"il": "Giresun", "lat": 40.91, "lon": 38.39, "solar": 1100, "wind": 2.5},
    {"il": "Gümüşhane", "lat": 40.46, "lon": 39.48, "solar": 1350, "wind": 2.8},
    {"il": "Hakkari", "lat": 37.58, "lon": 43.74, "solar": 1700, "wind": 3.0},
    {"il": "Hatay", "lat": 36.40, "lon": 36.35, "solar": 1680, "wind": 4.5},
    {"il": "Iğdır", "lat": 39.92, "lon": 44.05, "solar": 1600, "wind": 3.5},
    {"il": "Isparta", "lat": 37.76, "lon": 30.55, "solar": 1540, "wind": 3.0},
    {"il": "İstanbul", "lat": 41.01, "lon": 28.98, "solar": 1300, "wind": 4.5},
    {"il": "İzmir", "lat": 38.42, "lon": 27.14, "solar": 1550, "wind": 5.0},
    {"il": "Kahramanmaraş", "lat": 37.58, "lon": 36.94, "solar": 1650, "wind": 2.8},
    {"il": "Karabük", "lat": 41.20, "lon": 32.63, "solar": 1200, "wind": 2.5},
    {"il": "Karaman", "lat": 37.18, "lon": 33.23, "solar": 1600, "wind": 3.5},
    {"il": "Kars", "lat": 40.60, "lon": 43.10, "solar": 1500, "wind": 4.0},
    {"il": "Kastamonu", "lat": 41.39, "lon": 33.78, "solar": 1250, "wind": 2.8},
    {"il": "Kayseri", "lat": 38.73, "lon": 35.49, "solar": 1550, "wind": 3.5},
    {"il": "Kırıkkale", "lat": 39.85, "lon": 33.51, "solar": 1480, "wind": 3.0},
    {"il": "Kırklareli", "lat": 41.74, "lon": 27.23, "solar": 1320, "wind": 5.0},
    {"il": "Kırşehir", "lat": 39.15, "lon": 34.17, "solar": 1500, "wind": 3.2},
    {"il": "Kilis", "lat": 36.72, "lon": 37.12, "solar": 1700, "wind": 3.0},
    {"il": "Kocaeli", "lat": 40.77, "lon": 29.92, "solar": 1280, "wind": 3.5},
    {"il": "Konya", "lat": 37.87, "lon": 32.49, "solar": 1600, "wind": 3.5},
    {"il": "Kütahya", "lat": 39.42, "lon": 29.98, "solar": 1400, "wind": 3.0},
    {"il": "Malatya", "lat": 38.35, "lon": 38.31, "solar": 1620, "wind": 3.0},
    {"il": "Manisa", "lat": 38.61, "lon": 27.43, "solar": 1520, "wind": 4.0},
    {"il": "Mardin", "lat": 37.31, "lon": 40.74, "solar": 1750, "wind": 3.5},
    {"il": "Mersin", "lat": 36.80, "lon": 34.64, "solar": 1680, "wind": 3.5},
    {"il": "Muğla", "lat": 37.22, "lon": 28.36, "solar": 1600, "wind": 4.0},
    {"il": "Muş", "lat": 38.95, "lon": 41.75, "solar": 1550, "wind": 3.0},
    {"il": "Nevşehir", "lat": 38.63, "lon": 34.71, "solar": 1540, "wind": 3.2},
    {"il": "Niğde", "lat": 37.97, "lon": 34.68, "solar": 1580, "wind": 3.5},
    {"il": "Ordu", "lat": 41.00, "lon": 37.88, "solar": 1100, "wind": 2.5},
    {"il": "Osmaniye", "lat": 37.07, "lon": 36.25, "solar": 1650, "wind": 3.0},
    {"il": "Rize", "lat": 41.02, "lon": 40.52, "solar": 1000, "wind": 2.5},
    {"il": "Sakarya", "lat": 40.69, "lon": 30.40, "solar": 1250, "wind": 2.8},
    {"il": "Samsun", "lat": 41.29, "lon": 36.33, "solar": 1200, "wind": 3.5},
    {"il": "Şanlıurfa", "lat": 37.16, "lon": 38.80, "solar": 1780, "wind": 3.5},
    {"il": "Siirt", "lat": 37.93, "lon": 41.94, "solar": 1700, "wind": 2.8},
    {"il": "Sinop", "lat": 42.03, "lon": 35.15, "solar": 1150, "wind": 4.5},
    {"il": "Sivas", "lat": 39.75, "lon": 37.02, "solar": 1480, "wind": 3.0},
    {"il": "Şırnak", "lat": 37.52, "lon": 42.46, "solar": 1720, "wind": 3.0},
    {"il": "Tekirdağ", "lat": 41.00, "lon": 27.51, "solar": 1320, "wind": 5.0},
    {"il": "Tokat", "lat": 40.31, "lon": 36.55, "solar": 1350, "wind": 2.5},
    {"il": "Trabzon", "lat": 41.00, "lon": 39.72, "solar": 1050, "wind": 2.8},
    {"il": "Tunceli", "lat": 39.11, "lon": 39.55, "solar": 1550, "wind": 2.8},
    {"il": "Uşak", "lat": 38.68, "lon": 29.41, "solar": 1480, "wind": 3.0},
    {"il": "Van", "lat": 38.49, "lon": 43.38, "solar": 1650, "wind": 3.5},
    {"il": "Yalova", "lat": 40.66, "lon": 29.27, "solar": 1300, "wind": 3.5},
    {"il": "Yozgat", "lat": 39.82, "lon": 34.81, "solar": 1470, "wind": 3.2},
    {"il": "Zonguldak", "lat": 41.45, "lon": 31.80, "solar": 1100, "wind": 3.0},
]


def _get_wind_color(norm):
    """Rüzgar hızı normalize değerine göre renk döndür (mavi tonları)"""
    # Düşük rüzgar: koyu gri-mavi, yüksek rüzgar: parlak cyan
    r = int(30 + 50 * (1 - norm))
    g = int(80 + 175 * norm)
    b = int(120 + 135 * norm)
    return f"#{r:02x}{g:02x}{b:02x}"


def _get_solar_color(norm):
    """Güneş radyasyonu normalize değerine göre renk döndür"""
    r = int(255 * (1 - norm))
    g = int(200 * norm)
    b = 30
    return f"#{r:02x}{g:02x}{b:02x}"


def _get_wind_class(speed):
    """Rüzgar hızına göre uygunluk sınıfı döndür"""
    if speed >= 6.0:
        return "Mükemmel 🌟"
    elif speed >= 5.0:
        return "Çok İyi ✅"
    elif speed >= 4.0:
        return "İyi 👍"
    elif speed >= 3.0:
        return "Orta ⚡"
    else:
        return "Düşük ⚠️"


def _estimate_wind_capacity_factor(speed):
    """Basit kapasite faktörü tahmini (Weibull tabanlı yaklaşım)"""
    if speed < 2.5:
        return 0.08
    elif speed < 3.5:
        return 0.15
    elif speed < 4.5:
        return 0.22
    elif speed < 5.5:
        return 0.30
    elif speed < 6.5:
        return 0.35
    else:
        return 0.40


def create_turkey_map(map_mode="solar"):
    """81 il güneş/rüzgar potansiyeli haritası — katmanlı.
    
    Args:
        map_mode: 'solar', 'wind', veya 'both' (her iki katman da gösterilir)
    """
    m = folium.Map(location=[39.0, 35.5], zoom_start=6,
                   tiles="CartoDB dark_matter")

    solar_vals = [p["solar"] for p in TURKEY_PROVINCES]
    wind_vals = [p["wind"] for p in TURKEY_PROVINCES]
    s_min, s_max = min(solar_vals), max(solar_vals)
    w_min, w_max = min(wind_vals), max(wind_vals)

    # ─── Güneş Katmanı ─── #
    if map_mode in ("solar", "both"):
        solar_group = folium.FeatureGroup(name="☀️ Güneş Potansiyeli", show=(map_mode != "wind"))
        for prov in TURKEY_PROVINCES:
            norm = (prov["solar"] - s_min) / (s_max - s_min) if s_max > s_min else 0.5
            color = _get_solar_color(norm)

            popup_html = f"""
            <div style='font-family:Arial; min-width:220px;'>
                <h4 style='margin:0; color:#333;'>📍 {prov['il']}</h4>
                <hr style='margin:4px 0;'>
                <b>☀️ Güneş Radyasyonu:</b> {prov['solar']} kWh/m²/yıl<br>
                <b>💨 Ort. Rüzgar Hızı:</b> {prov['wind']:.1f} m/s<br>
                <b>⚡ 5kW GES Üretim:</b> ~{prov['solar']*5*0.85/1000:.0f} MWh/yıl<br>
                <b>💰 Yıllık Tasarruf:</b> ~{prov['solar']*5*0.85*2.04/1000:.0f} TL<br>
            </div>
            """

            folium.CircleMarker(
                location=[prov["lat"], prov["lon"]],
                radius=8 + 10 * norm,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{prov['il']}: {prov['solar']} kWh/m²",
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                weight=2,
            ).add_to(solar_group)
        solar_group.add_to(m)

    # ─── Rüzgar Katmanı ─── #
    if map_mode in ("wind", "both"):
        wind_group = folium.FeatureGroup(name="💨 Rüzgar Potansiyeli", show=(map_mode != "solar"))
        for prov in TURKEY_PROVINCES:
            w_norm = (prov["wind"] - w_min) / (w_max - w_min) if w_max > w_min else 0.5
            w_color = _get_wind_color(w_norm)
            wind_class = _get_wind_class(prov["wind"])
            cf = _estimate_wind_capacity_factor(prov["wind"])
            annual_mwh = 10 * cf * 8760 / 1000  # 10 kW türbin, yıllık MWh

            popup_html = f"""
            <div style='font-family:Arial; min-width:240px;'>
                <h4 style='margin:0; color:#333;'>📍 {prov['il']}</h4>
                <hr style='margin:4px 0;'>
                <b>💨 Ort. Rüzgar Hızı:</b> {prov['wind']:.1f} m/s<br>
                <b>📊 Rüzgar Sınıfı:</b> {wind_class}<br>
                <b>⚙️ Kapasite Faktörü:</b> %{cf*100:.0f}<br>
                <b>⚡ 10kW Türbin Üretim:</b> ~{annual_mwh:.1f} MWh/yıl<br>
                <b>💰 Yıllık Gelir:</b> ~{annual_mwh*1000*2.04:.0f} TL<br>
                <hr style='margin:4px 0;'>
                <b>☀️ Güneş:</b> {prov['solar']} kWh/m²/yıl<br>
            </div>
            """

            folium.CircleMarker(
                location=[prov["lat"], prov["lon"]],
                radius=8 + 12 * w_norm,
                popup=folium.Popup(popup_html, max_width=320),
                tooltip=f"{prov['il']}: {prov['wind']:.1f} m/s 💨",
                color=w_color,
                fill=True,
                fill_color=w_color,
                fill_opacity=0.75,
                weight=2,
            ).add_to(wind_group)
        wind_group.add_to(m)

    # ─── Katman kontrolü ─── #
    if map_mode == "both":
        folium.LayerControl(collapsed=False).add_to(m)

    # ─── Lejant ─── #
    if map_mode == "solar":
        legend_html = """
        <div style="position:fixed; bottom:30px; left:30px; z-index:1000;
                    background:rgba(0,0,0,0.8); padding:12px; border-radius:8px;
                    font-size:12px; color:white; font-family:Arial;">
            <b>☀️ Güneş Potansiyeli (kWh/m²/yıl)</b><br>
            <span style="color:#00c81e;">●</span> Yüksek (1700+)<br>
            <span style="color:#8c9a1e;">●</span> Orta (1400-1700)<br>
            <span style="color:#ff001e;">●</span> Düşük (&lt;1400)
        </div>
        """
    elif map_mode == "wind":
        legend_html = """
        <div style="position:fixed; bottom:30px; left:30px; z-index:1000;
                    background:rgba(0,0,0,0.8); padding:12px; border-radius:8px;
                    font-size:12px; color:white; font-family:Arial;">
            <b>💨 Rüzgar Potansiyeli (m/s)</b><br>
            <span style="color:#50ffff;">●</span> Yüksek (5.0+ m/s)<br>
            <span style="color:#40b4c8;">●</span> Orta (3.5-5.0 m/s)<br>
            <span style="color:#507888;">●</span> Düşük (&lt;3.5 m/s)<br>
            <hr style="margin:6px 0; border-color:#555;">
            <b>Rüzgar Sınıfları:</b><br>
            🌟 Mükemmel: 6+ m/s<br>
            ✅ Çok İyi: 5-6 m/s<br>
            👍 İyi: 4-5 m/s<br>
            ⚡ Orta: 3-4 m/s<br>
            ⚠️ Düşük: &lt;3 m/s
        </div>
        """
    else:  # both
        legend_html = """
        <div style="position:fixed; bottom:30px; left:30px; z-index:1000;
                    background:rgba(0,0,0,0.85); padding:14px; border-radius:10px;
                    font-size:12px; color:white; font-family:Arial; max-width:220px;">
            <b>☀️ Güneş (kWh/m²/yıl)</b><br>
            <span style="color:#00c81e;">●</span> Yüksek (1700+)
            <span style="color:#8c9a1e;">●</span> Orta
            <span style="color:#ff001e;">●</span> Düşük<br>
            <hr style="margin:6px 0; border-color:#555;">
            <b>💨 Rüzgar (m/s)</b><br>
            <span style="color:#50ffff;">●</span> Yüksek (5+)
            <span style="color:#40b4c8;">●</span> Orta
            <span style="color:#507888;">●</span> Düşük<br>
            <small>Katmanları açıp kapatmak için<br>sağ üst kontrolü kullanın.</small>
        </div>
        """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m


def get_province_data(province_name: str):
    """İl bazlı veri getir"""
    for p in TURKEY_PROVINCES:
        if p["il"] == province_name:
            return p
    return None
