"""GeoJSON Choropleth Haritası — İl Sınırları Renkli Harita

Türkiye il sınırlarını GeoJSON olarak çekip Folium Choropleth katmanı ile
güneş/rüzgar potansiyelini renkli dolgu olarak gösterir.

GeoJSON kaynağı: GitHub/okankoc13 Turkey provinces (MIT Lisans)
Alternatif: gadm.org Türkiye NUTS-3 şekilleri (kamuya açık)
"""

import streamlit as st
import requests
import json
import folium
from folium import Choropleth, GeoJson
from folium.plugins import FloatImage
import numpy as np

# ─── GeoJSON URL (herkese açık, lisanssız) ────────────────────────────────────
TURKEY_GEOJSON_URL = (
    "https://raw.githubusercontent.com/okankoc13/turkey-geojson/"
    "master/Turkey_provinces.geojson"
)
FALLBACK_GEOJSON_URL = (
    "https://raw.githubusercontent.com/cihadturhan/tr-geojson/"
    "master/geo/tr-cities-utf8.json"
)


@st.cache_data(ttl=86400, show_spinner="🗺️ İl sınırları yükleniyor...")
def load_turkey_geojson() -> dict:
    """
    Türkiye il sınırları GeoJSON'ını indir ve önbellekle.
    Başarısız olursa basit bounding-box fallback döner.
    """
    for url in [TURKEY_GEOJSON_URL, FALLBACK_GEOJSON_URL]:
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            # Feature'lara 'name' property ekle (tutarsız key'leri normalize et)
            for feat in data.get("features", []):
                props = feat.get("properties", {})
                name = (
                    props.get("NAME_1") or
                    props.get("name") or
                    props.get("il") or
                    props.get("ADM1_TR") or ""
                )
                props["province_name"] = name.strip()
                feat["properties"] = props
            return data
        except Exception:
            continue
    return None


def create_choropleth_map(province_data: list, metric: str = "solar") -> folium.Map:
    """
    Türkiye il sınırlarıyla renkli choropleth haritası oluştur.

    Parameters
    ----------
    province_data : list[dict]
        Her dict'te: il, lat, lon, solar (kWh/m²/yıl), wind (m/s) alanları
    metric        : "solar" | "wind"

    Returns
    -------
    folium.Map — Streamlit'te st_folium() ile gösterilebilir
    """
    geojson_data = load_turkey_geojson()

    m = folium.Map(
        location=[39.0, 35.5],
        zoom_start=6,
        tiles="CartoDB positron",
    )

    # ── İl verilerini dict'e dönüştür ─────────────────────────────────────────
    values_by_province = {p["il"]: p.get(metric, 0) for p in province_data}

    if geojson_data:
        # ── GeoJSON Choropleth ─────────────────────────────────────────────────
        if metric == "solar":
            color_scheme  = "YlOrRd"
            legend_name   = "Güneş Radyasyonu (kWh/m²/yıl)"
            fill_color    = "YlOrRd"
        else:
            color_scheme  = "Blues"
            legend_name   = "Ortalama Rüzgar Hızı (m/s)"
            fill_color    = "Blues"

        # Folium Choropleth doğrudan dict yerine list+key ister
        data_pairs = [
            [prov, val] for prov, val in values_by_province.items()
        ]

        Choropleth(
            geo_data=geojson_data,
            data=data_pairs,
            columns=[0, 1],
            key_on="feature.properties.province_name",
            fill_color=fill_color,
            fill_opacity=0.75,
            line_opacity=0.5,
            line_color="#666",
            nan_fill_color="#cccccc",
            nan_fill_opacity=0.3,
            legend_name=legend_name,
            highlight=True,
            name=f"{'☀️ Güneş' if metric == 'solar' else '💨 Rüzgar'} Choropleth",
        ).add_to(m)

        # ── Tooltip: her ile tıklandığında veri göster ──────────────────────
        def _style(feat):
            return {
                "fillOpacity": 0,
                "weight": 0,
                "color": "transparent",
            }

        def _highlight(feat):
            return {
                "fillOpacity": 0.2,
                "weight": 2,
                "color": "#333",
            }

        def _tooltip_fields(feat):
            name = feat.get("properties", {}).get("province_name", "?")
            val  = values_by_province.get(name, "N/A")
            unit = "kWh/m²/yıl" if metric == "solar" else "m/s"
            return f"<b>{name}</b><br>{'☀️' if metric == 'solar' else '💨'} {val} {unit}"

        GeoJson(
            geojson_data,
            style_function=_style,
            highlight_function=_highlight,
            tooltip=folium.GeoJsonTooltip(
                fields=["province_name"],
                aliases=["İl:"],
                localize=True,
                sticky=False,
            ),
        ).add_to(m)

    # ── Her zaman CircleMarker'lar da ekle (GeoJSON üstüne) ───────────────────
    vals = [p.get(metric, 0) for p in province_data]
    v_min, v_max = min(vals), max(vals)

    for prov in province_data:
        val  = prov.get(metric, 0)
        norm = (val - v_min) / (v_max - v_min + 1e-9)
        color = _metric_color(norm, metric)

        if metric == "solar":
            tooltip_txt = f"{prov['il']}: {val} kWh/m²/yıl ☀️"
            popup_html  = (
                f"<b>{prov['il']}</b><br>"
                f"☀️ Güneş: <b>{val}</b> kWh/m²/yıl<br>"
                f"💨 Rüzgar: {prov.get('wind', '-')} m/s<br>"
                f"⚡ 5kW yıllık: ~{val*5*0.85/1000:.0f} MWh"
            )
        else:
            cf  = _wind_cf(val)
            tooltip_txt = f"{prov['il']}: {val:.1f} m/s 💨"
            popup_html  = (
                f"<b>{prov['il']}</b><br>"
                f"💨 Rüzgar: <b>{val:.1f}</b> m/s<br>"
                f"⚙️ Kapasite Faktörü: %{cf*100:.0f}<br>"
                f"⚡ 10kW/yıl: ~{10*cf*8.76:.0f} MWh"
            )

        folium.CircleMarker(
            location=[prov["lat"], prov["lon"]],
            radius=5 + 8 * norm,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=tooltip_txt,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            weight=1.5,
        ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m


# ─── Yardımcı Fonksiyonlar ────────────────────────────────────────────────────

def _metric_color(norm: float, metric: str) -> str:
    """Normalize değere göre hex renk üret."""
    if metric == "solar":
        r = int(255 * norm)
        g = int(180 * norm)
        b = 20
    else:
        r = 30
        g = int(100 + 155 * norm)
        b = int(200 * norm + 55)
    return f"#{min(255,r):02x}{min(255,g):02x}{min(255,b):02x}"


def _wind_cf(speed: float) -> float:
    """Basit kapasite faktörü tahmini."""
    if speed < 2.5:   return 0.08
    elif speed < 3.5: return 0.15
    elif speed < 4.5: return 0.22
    elif speed < 5.5: return 0.30
    elif speed < 6.5: return 0.35
    else:             return 0.40
