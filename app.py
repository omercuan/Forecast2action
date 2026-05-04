"""
Forecast2Action — Yenilenebilir Enerji Karar Destek Sistemi
DU Hackathon 2026 | CodeXEnergy
"""
import streamlit as st
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
from datetime import datetime

# ─────────────────── PAGE CONFIG ─────────────────── #
st.set_page_config(
    page_title="Forecast2Action | Enerji Karar Destek",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────── DURUM BAŞLANGICI ─────────────────── #
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = True
if "lang" not in st.session_state:
    st.session_state["lang"] = "TR"

# ─────────────────── ÇEVİRİ SÖZLÜĞÜ ─────────────────── #
_TR = {
    "page_title": "Forecast2Action | Enerji Karar Destek",
    "subtitle": "Yenilenebilir Enerji Karar Destek Sistemi — DU Hackathon 2026",
    "settings": "⚙️ Sistem Ayarları",
    "location": "📍 Lokasyon",
    "city": "Şehir Seç",
    "facility": "🏢 Tesis Profili",
    "facility_opts": ["🏠 Ev (Müstakil)", "🚜 Tarım / Çiftlik", "🏢 Ticari / İş Yeri", "🏭 Endüstriyel / Fabrika"],
    "sys_type": "🔌 Sistem Tipi",
    "sys_opts": ["☀️ Güneş (GES)", "💨 Rüzgar"],
    "install": "⚡ Kurulum Detayları",
    "inst_kw": "Kurulu Güç (kW)",
    "turbine_kw": "Türbin Gücü (kW)",
    "tilt": "Panel Eğimi (°)",
    "loss": "Sistem Kaybı (%)",
    "azimuth": "Azimut (°)",
    "hub": "Kanat Yüksekliği (m)",
    "battery": "🔋 Batarya",
    "has_bat": "Batarya var",
    "bat_cap": "Kapasite (kWh)",
    "bat_kw": "Max Şarj (kW)",
    "epias_exp": "🔑 EPİAŞ API Kimlik Bilgileri",
    "epias_cap": "Kayıt: kayit.epias.com.tr | TGT 8 saat geçerli",
    "epias_user": "Kullanıcı Adı",
    "epias_pass": "Şifre",
    "epias_test": "🔗 Bağlantı Test Et",
    "epias_ok": "🟢 EPİAŞ bağlı",
    "epias_fail": "🔴 Bağlantı başarısız",
    "epias_none": "⚪ Bağlanılmadı — simülasyon aktif",
    "calc_btn": "🚀 Tahmin Hesapla",
    "tab1": "📊 Tahmin Sonuçları",
    "tab2": "⚡ Aksiyon Planı",
    "tab3": "🔍 Sistem İzleme",
    "tab4": "🗺️ Türkiye Potansiyel Haritası",
    "tab5": "💰 Finansal Analiz",
    "tab6": "🤖 AI Önerileri",
    "tab7": "📡 IoT & PDF Rapor",
    "light_theme": "☀️ Açık Tema",
    "dark_theme": "🌙 Koyu Tema",
    "lang_btn": "🇬🇧 English",
    "no_forecast": "👈 Sol panelden parametreleri ayarlayıp **Tahmin Hesapla** butonuna basın.",
    "opt_warn": "⚠️ Önce **Tahmin Sonuçları** sekmesinden hesaplama yapın!",
    "pin": "📍 Pin",
    "spinner_model": "🤖 Hibrit model (Fizik+ML) çalışıyor...",
    "done": "✅ Tahmin tamamlandı!",
}
_EN = {
    "page_title": "Forecast2Action | Energy Decision Support",
    "subtitle": "Renewable Energy Decision Support System — DU Hackathon 2026",
    "settings": "⚙️ System Settings",
    "location": "📍 Location",
    "city": "Select City",
    "facility": "🏢 Facility Profile",
    "facility_opts": ["🏠 Home (Residential)", "🚜 Agriculture / Farm", "🏢 Commercial / Office", "🏭 Industrial / Factory"],
    "sys_type": "🔌 System Type",
    "sys_opts": ["☀️ Solar (PV)", "💨 Wind"],
    "install": "⚡ Installation Details",
    "inst_kw": "Installed Power (kW)",
    "turbine_kw": "Turbine Power (kW)",
    "tilt": "Panel Tilt (°)",
    "loss": "System Loss (%)",
    "azimuth": "Azimuth (°)",
    "hub": "Hub Height (m)",
    "battery": "🔋 Battery",
    "has_bat": "Has Battery",
    "bat_cap": "Capacity (kWh)",
    "bat_kw": "Max Charge (kW)",
    "epias_exp": "🔑 EPİAŞ API Credentials",
    "epias_cap": "Register: kayit.epias.com.tr | TGT valid 8 hours",
    "epias_user": "Username",
    "epias_pass": "Password",
    "epias_test": "🔗 Test Connection",
    "epias_ok": "🟢 EPİAŞ connected",
    "epias_fail": "🔴 Connection failed",
    "epias_none": "⚪ Not connected — simulation active",
    "calc_btn": "🚀 Run Forecast",
    "tab1": "📊 Forecast Results",
    "tab2": "⚡ Action Plan",
    "tab3": "🔍 System Monitor",
    "tab4": "🗺️ Turkey Potential Map",
    "tab5": "💰 Financial Analysis",
    "tab6": "🤖 AI Recommendations",
    "tab7": "📡 IoT & PDF Report",
    "light_theme": "☀️ Light Theme",
    "dark_theme": "🌙 Dark Theme",
    "lang_btn": "🇹🇷 Türkçe",
    "no_forecast": "👈 Set parameters in the left panel and click **Run Forecast**.",
    "opt_warn": "⚠️ Please run a forecast from the **Forecast Results** tab first!",
    "pin": "📍 Pin",
    "spinner_model": "🤖 Hybrid model (Physics+ML) running...",
    "done": "✅ Forecast complete!",
}
_T = _TR if st.session_state["lang"] == "TR" else _EN

# ─────────────────── CUSTOM CSS ─────────────────── #
_dark = st.session_state["dark_mode"]

# Tema değişkenlerini belirle
if _dark:
    _bg          = "#0e1117"
    _sec_bg      = "#1a1f2b"
    _input_bg    = "#1a1f2b"
    _card_bg     = "linear-gradient(135deg, #1a1f2b 0%, #2d3748 100%)"
    _text        = "#e0e0e0"
    _text_muted  = "#888"
    _border      = "rgba(0,200,83,0.3)"
    _metric_text = "#e0e0e0"
    _tab_text    = "#e0e0e0"
    _sidebar_bg  = "#1a1f2b"
    _toggle_icon = "☀️"
    _toggle_label= "Açık Tema"
    _plotly_tmpl = "plotly_dark"
else:
    _bg          = "#dde3ee"
    _sec_bg      = "#ffffff"
    _input_bg    = "#ffffff"
    _card_bg     = "linear-gradient(135deg, #ffffff 0%, #eaeff8 100%)"
    _text        = "#0d1117"
    _text_muted  = "#3a4a5c"
    _border      = "rgba(0,130,60,0.45)"
    _metric_text = "#0d1117"
    _tab_text    = "#0d1117"
    _sidebar_bg  = "#cdd5e4"
    _toggle_icon = "🌙"
    _toggle_label= "Koyu Tema"
    _plotly_tmpl = "plotly_white"

# Plotly şablonunu session_state'e kaydet (grafik fonksiyonlarında kullanılır)
st.session_state["plotly_template"] = _plotly_tmpl

st.markdown(f"""
<style>
/* ═══ GENEL TEMA ═══ */
html, body, [data-testid="stApp"] {{
    background-color: {_bg} !important;
    color: {_text} !important;
}}
[data-testid="stSidebar"] {{
    background-color: {_sidebar_bg} !important;
}}
[data-testid="stSidebar"] * {{
    color: {_text} !important;
}}
div[data-testid="stMetric"] {{
    background: {_card_bg};
    border: 1px solid {_border};
    border-radius: 12px;
    padding: 1rem;
}}
div[data-testid="stMetricValue"],
div[data-testid="stMetricLabel"] {{
    color: {_metric_text} !important;
}}
.stTabs [data-baseweb="tab-list"] {{
    background-color: {_sec_bg} !important;
}}
.stTabs [data-baseweb="tab"] {{
    color: {_tab_text} !important;
    font-size: 1rem;
    font-weight: 600;
}}
.stTabs [aria-selected="true"] {{
    color: #00C853 !important;
    border-bottom: 2px solid #00C853 !important;
}}
[data-testid="stExpander"] {{
    background-color: {_sec_bg} !important;
    border: 1px solid {_border} !important;
    border-radius: 8px !important;
}}
[data-testid="stExpander"] * {{
    color: {_text} !important;
}}
div[data-testid="stDataFrame"] {{
    background-color: {_sec_bg} !important;
}}
/* Input (kutu) arkaplanları (Selectbox, Number Input vb.) */
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="base-input"] > input {{
    background-color: {_input_bg} !important;
    color: {_text} !important;
}}
p, span, label, div {{
    color: {_text};
}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body { font-family: 'Inter', sans-serif; }

.main-title {
    text-align: center;
    background: linear-gradient(135deg, #00C853, #00E5FF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.8rem;
    font-weight: 700;
    margin-bottom: 0;
}
.sub-title {
    text-align: center;
    color: #888;
    font-size: 1.1rem;
    margin-bottom: 1.5rem;
}
.metric-box {
    background: var(--card-bg, inherit); /* CSS değişkeni kullanılabilir ancak biz yukarıda doğrudan enjekte ediyoruz */
    border: 1px solid #00C853;
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
}
/* stMetric stilleri yukarıdaki dinamik CSS bloğunda (satır 169) `_card_bg` ile eziliyor. 
   Buradaki sabit stilleri kaldırıyoruz ki beyaz temada dark kalmasın. */
.stTabs [data-baseweb="tab"] {
    font-size: 1rem;
    font-weight: 600;
}
footer { visibility: hidden; }

/* ═══ BUTONLAR — premium gradient stil ═══ */
/* Primary buton — data-testid ile güvenli selector */
[data-testid="baseButton-primary"],
button[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #00C853 0%, #00897B 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.65rem 1.6rem !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 4px 18px rgba(0,200,83,0.4) !important;
    transition: all 0.2s ease !important;
    min-height: 2.75rem !important;
    width: auto !important;
}
[data-testid="baseButton-primary"]:hover {
    background: linear-gradient(135deg, #00E676 0%, #00ACC1 100%) !important;
    box-shadow: 0 6px 24px rgba(0,200,83,0.55) !important;
    transform: translateY(-2px) !important;
    color: #fff !important;
}
[data-testid="baseButton-primary"]:active {
    transform: translateY(0) !important;
    box-shadow: 0 2px 8px rgba(0,200,83,0.3) !important;
}
/* Primary buton içindeki tüm text elementleri görünür olsun */
[data-testid="baseButton-primary"] p,
[data-testid="baseButton-primary"] span,
[data-testid="baseButton-primary"] div {
    color: #fff !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    visibility: visible !important;
    display: inline !important;
}
/* Secondary buton */
[data-testid="baseButton-secondary"],
button[data-testid="baseButton-secondary"] {
    background: linear-gradient(135deg, #1e2636 0%, #2d3748 100%) !important;
    color: #e0e0e0 !important;
    border: 1px solid rgba(0,200,83,0.45) !important;
    border-radius: 10px !important;
    padding: 0.6rem 1.4rem !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
    min-height: 2.5rem !important;
}
[data-testid="baseButton-secondary"]:hover {
    border-color: #00C853 !important;
    color: #00E676 !important;
    background: linear-gradient(135deg, #1e2636 0%, #1a3028 100%) !important;
    box-shadow: 0 4px 14px rgba(0,200,83,0.25) !important;
    transform: translateY(-1px) !important;
}
[data-testid="baseButton-secondary"] p,
[data-testid="baseButton-secondary"] span,
[data-testid="baseButton-secondary"] div {
    color: inherit !important;
    font-size: 0.95rem !important;
    visibility: visible !important;
    display: inline !important;
}
/* Download butonu */
[data-testid="baseButton-downloadButton"],
button[data-testid="baseButton-downloadButton"],
div[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, #1565C0 0%, #0D47A1 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.65rem 1.6rem !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 15px rgba(21,101,192,0.45) !important;
    transition: all 0.2s ease !important;
    min-height: 2.75rem !important;
}
div[data-testid="stDownloadButton"] > button:hover {
    background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%) !important;
    box-shadow: 0 6px 22px rgba(21,101,192,0.6) !important;
    transform: translateY(-2px) !important;
}

/* ═══════════════════════════════════════════════════════════════
   HATA 1: Sidebar collapse button — "keyboard_double_arrow_right"
   Material Symbols font yüklenmeyince icon ismi metin olarak görünür.
   Çözüm: font-family override + width/height kısıtlama + text-indent hack
   ═══════════════════════════════════════════════════════════════ */

/* Material Symbols font override — tüm icon span'larına uygula */
span[class*="material-symbols"],
span[class*="material-icons"],
.material-symbols-rounded,
.material-icons,
[data-testid="stSidebarCollapseButton"] span,
[data-testid="stSidebarNav"] span {
    font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
    font-size: 1.25rem !important;
    font-weight: normal !important;
    font-style: normal !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    display: inline-block !important;
    white-space: nowrap !important;
    word-wrap: normal !important;
    direction: ltr !important;
    -webkit-font-feature-settings: 'liga' !important;
    -webkit-font-smoothing: antialiased !important;
}

/* Sidebar collapse/expand icon fallback hide */
[data-testid="stSidebarCollapseButton"] {
    color: rgba(255, 255, 255, 0.7) !important;
}
[data-testid="stSidebarCollapseButton"] svg {
    display: block !important;
}

/* ═══════════════════════════════════════════════════════════════
   HATA 2: Expander başlık metni üst üste gelme
   Streamlit expander summary elementi flex olmalı, svg ile text hizalanmalı
   ═══════════════════════════════════════════════════════════════ */

/* Streamlit 1.x expander */
.streamlit-expanderHeader {
    align-items: center !important;
    line-height: 1.4 !important;
    gap: 6px !important;
    white-space: normal !important;
    overflow: visible !important;
}
.streamlit-expanderHeader p {
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.4 !important;
}

/* Streamlit 1.3+ expander (details/summary) */
details > summary {
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
    cursor: pointer !important;
    line-height: 1.4 !important;
    overflow: visible !important;
    white-space: normal !important;
}
details > summary > * {
    flex-shrink: 0 !important;
}
details > summary > p,
details > summary > span:not([class^="material"]) {
    flex-shrink: 1 !important;
    margin: 0 !important;
    line-height: 1.4 !important;
}

/* data-testid based expander selector (yeni Streamlit) */
[data-testid="stExpander"] summary {
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    line-height: 1.4 !important;
    overflow: hidden !important;
    white-space: nowrap !important;
}
/* Expander ok SVG'si — boyut sabitle, taşma önle */
[data-testid="stExpander"] summary svg {
    flex-shrink: 0 !important;
    min-width: 16px !important;
    width: 16px !important;
    height: 16px !important;
    overflow: visible !important;
}
/* Expander başlık metni */
[data-testid="stExpander"] summary p {
    margin: 0 !important;
    line-height: 1.4 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    flex: 1 !important;
    min-width: 0 !important;
}
/* Expander içindeki Material icon span'ları — taşmayı önle */
[data-testid="stExpander"] summary span[data-testid] {
    display: none !important;
}

/* ═══ DATAFRAME / TOOLTIP üst üste gelme düzeltmesi ═══ */
div[role="tooltip"],
div[data-radix-popper-content-wrapper] {
    z-index: 9999 !important;
    max-width: 320px !important;
    word-break: break-word !important;
    white-space: normal !important;
}
div[data-testid="stMetricDelta"] {
    overflow: hidden !important;
    white-space: nowrap !important;
    text-overflow: ellipsis !important;
    max-width: 100% !important;
}
div[data-testid="stMetricDelta"] svg {
    flex-shrink: 0 !important;
    vertical-align: middle !important;
}
div[data-testid="stMetricLabel"],
div[data-testid="stMetricValue"] {
    overflow: hidden !important;
    white-space: nowrap !important;
    text-overflow: ellipsis !important;
}
div[data-testid="stMetricValue"] {
    font-size: clamp(1rem, 2vw, 1.6rem) !important;
}
div[data-testid="stSelectbox"] label,
div[data-testid="stSlider"] label,
div[data-testid="stNumberInput"] label,
div[data-testid="stTextInput"] label {
    white-space: normal !important;
    overflow: visible !important;
    line-height: 1.4 !important;
}
div[data-testid="stCaptionContainer"] p {
    white-space: normal !important;
    overflow: visible !important;
    line-height: 1.5 !important;
}
.stTabs [data-baseweb="tab"] {
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────── HEADER ─────────────────── #
st.markdown('<h1 class="main-title">⚡ Forecast2Action</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Yenilenebilir Enerji Karar Destek Sistemi — DU Hackathon 2026</p>', unsafe_allow_html=True)

# ─────────────────── SIDEBAR ─────────────────── #
from modules.utils import CITIES

with st.sidebar:
    # ── Kontrol Satırı: Tema + Dil ──
    _t_col, _l_col = st.columns(2)
    with _t_col:
        _tlabel = _T["light_theme"] if st.session_state["dark_mode"] else _T["dark_theme"]
        if st.button(_tlabel, key="theme_toggle_btn", use_container_width=True):
            st.session_state["dark_mode"] = not st.session_state["dark_mode"]
            st.rerun()
    with _l_col:
        if st.button(_T["lang_btn"], key="lang_toggle_btn", use_container_width=True):
            st.session_state["lang"] = "EN" if st.session_state["lang"] == "TR" else "TR"
            st.rerun()

    st.header(_T["settings"])

    # --- Lokasyon ---
    st.subheader(_T["location"])
    selected_city = st.selectbox(_T["city"], list(CITIES.keys()), index=0)
    city_info = CITIES[selected_city]
    lat = city_info["lat"]
    lon = city_info["lon"]

    # Mini harita
    m_side = folium.Map(location=[lat, lon], zoom_start=8, tiles="CartoDB dark_matter",
                        width=280, height=200)
    folium.Marker([lat, lon], popup=selected_city,
                  icon=folium.Icon(color="green", icon="bolt", prefix="fa")).add_to(m_side)
    map_data = st_folium(m_side, width=280, height=200, key="sidebar_map")

    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        st.success(f"📍 Pin: {lat:.4f}, {lon:.4f}")

    st.divider()

    # --- Tesis Tipi ---
    st.subheader(_T["facility"])
    facility_type = st.selectbox(_T["facility"], _T["facility_opts"],
                                 label_visibility="collapsed")
    _fac_idx = _T["facility_opts"].index(facility_type)
    if _fac_idx == 0:
        def_kw, def_bat_kwh, def_bat_kw = 5, 5, 3
    elif _fac_idx == 1:
        def_kw, def_bat_kwh, def_bat_kw = 50, 100, 50
    elif _fac_idx == 2:
        def_kw, def_bat_kwh, def_bat_kw = 250, 500, 200
    else:
        def_kw, def_bat_kwh, def_bat_kw = 2000, 4000, 1500

    st.divider()

    # --- Sistem Tipi ---
    st.subheader(_T["sys_type"])
    system_type = st.radio(_T["sys_type"], _T["sys_opts"], horizontal=True,
                           label_visibility="collapsed")

    st.subheader(_T["install"])
    if "☀️" in system_type or "Solar" in system_type:
        col1, col2 = st.columns(2)
        with col1:
            installed_kw = st.number_input(_T["inst_kw"], 1, 10000, def_kw)
            tilt = st.slider(_T["tilt"], 0, 90, 30)
        with col2:
            loss = st.slider(_T["loss"], 5, 25, 14)
            azimuth = st.slider(_T["azimuth"], -180, 180, 0)
        hub_height = 50
    else:
        installed_kw = st.number_input(_T["turbine_kw"], 1, 10000, def_kw)
        hub_height = st.slider(_T["hub"], 10, 100, 50)
        tilt, azimuth, loss = 30, 0, 14

    st.divider()

    # --- Batarya ---
    st.subheader(_T["battery"])
    has_battery = st.checkbox(_T["has_bat"], value=True)
    if has_battery:
        battery_kwh = st.number_input(_T["bat_cap"], 1, 10000, def_bat_kwh)
        battery_kw = st.number_input(_T["bat_kw"], 1, 5000, def_bat_kw)
    else:
        battery_kwh, battery_kw = 0, 0

    # --- EPİAŞ Kimlik ---
    with st.expander(_T["epias_exp"], expanded=False):
        st.caption(_T["epias_cap"])

        epias_user = st.text_input(
            _T["epias_user"], value=st.session_state.get("epias_user", ""),
            key="epias_user_input", placeholder="epias@epias.com.tr"
        )
        epias_pass = st.text_input(
            _T["epias_pass"], type="password", value="",
            key="epias_pass_input", placeholder="••••••••"
        )
        if st.button(_T["epias_test"], key="epias_test_btn"):
            if epias_user and epias_pass:
                from modules.epias_price import _get_tgt, clear_tgt_cache
                clear_tgt_cache()
                with st.spinner("TGT alınıyor..."):
                    tgt, err = _get_tgt(epias_user, epias_pass)
                if tgt:
                    st.session_state["epias_user"] = epias_user
                    st.session_state["epias_pass"] = epias_pass
                    st.session_state["epias_tgt_ok"] = True
                    st.success("✅ TGT alındı! Gerçek PTF verisi kullanılacak.")
                else:
                    st.session_state["epias_tgt_ok"] = False
                    st.error(f"❌ {err}")
            else:
                st.warning("Kullanıcı adı ve şifre girin.")
        tgt_ok = st.session_state.get("epias_tgt_ok")
        if tgt_ok is True:
            st.success(_T["epias_ok"])
        elif tgt_ok is False:
            st.error(_T["epias_fail"])
        else:
            st.caption(_T["epias_none"])

    st.divider()

    # --- Hesapla ---
    calculate_btn = st.button(_T["calc_btn"], type="primary", use_container_width=True)

# ─────────────────── MAIN TABS ─────────────────── #
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    _T["tab1"], _T["tab2"], _T["tab3"], _T["tab4"],
    _T["tab5"], _T["tab6"], _T["tab7"],
])

# ═══════════════════════════════════════════════════ #
#                    TAB 1: TAHMİN                    #
# ═══════════════════════════════════════════════════ #
with tab1:
    if calculate_btn:
        from modules.data_provider import get_weather_forecast
        from modules.forecast_engine import ForecastEngine

        weather_df = get_weather_forecast(lat, lon, hours=48)
        engine = ForecastEngine()

        with st.spinner("🤖 Hibrit model (Fizik+ML) çalışıyor..."):
            if "☀️" in system_type:
                forecast = engine.predict_solar(weather_df, installed_kw, tilt, azimuth, loss)
            else:
                forecast = engine.predict_wind(weather_df, installed_kw, hub_height)

        st.session_state["forecast"] = forecast
        st.session_state["weather_df"] = weather_df
        st.session_state["system_params"] = {
            "type": system_type, "installed_kw": installed_kw,
            "battery_kwh": battery_kwh, "battery_kw": battery_kw,
        }
        st.success("✅ Tahmin tamamlandı!")

    if "forecast" in st.session_state:
        forecast = st.session_state["forecast"]

        # Metrikler
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("⚡ Toplam Üretim (48h)", f"{forecast['total_production']:.1f} kWh",
                       f"~{forecast['total_production']/2:.1f} kWh/gün")
        with c2:
            st.metric("📈 Pik Üretim", f"{forecast['max_production']:.2f} kW",
                       forecast["max_hour"][:16])
        with c3:
            avg_c = forecast["avg_confidence"]
            st.metric("🎯 Ortalama Güven", f"%{avg_c:.0f}",
                       "Yüksek" if avg_c > 70 else "Orta")
        with c4:
            st.metric("🌙 Düşük Üretim", f"{forecast['low_production_hours']} saat", "< 0.5 kW")

        st.divider()

        # Ana grafik: belirsizlik bandı
        fig = go.Figure()

        # P90 (üst çizgi - görünmez)
        fig.add_trace(go.Scatter(
            x=forecast["timestamps"], y=forecast["p90"],
            mode="lines", line_color="rgba(0,200,83,0)",
            showlegend=False, name="P90",
        ))
        # P10 (alt çizgi - dolgu ile)
        fig.add_trace(go.Scatter(
            x=forecast["timestamps"], y=forecast["p10"],
            fill="tonexty", mode="lines", line_color="rgba(0,200,83,0)",
            fillcolor="rgba(0,200,83,0.15)", name="Belirsizlik Bandı (P10-P90)",
        ))
        # P50 (ana tahmin)
        fig.add_trace(go.Scatter(
            x=forecast["timestamps"], y=forecast["p50"],
            mode="lines+markers", name="Beklenen Üretim (P50)",
            line=dict(color="#00C853", width=3), marker=dict(size=5),
        ))

        fig.update_layout(
            title="📊 48 Saatlik Üretim Tahmini — Belirsizlik Bandı ile",
            xaxis_title="Zaman", yaxis_title="Üretim (kW)",
            hovermode="x unified", height=500,
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Detay tablo
        with st.expander("📋 Saatlik Detay Tablosu"):
            df = pd.DataFrame({
                "Saat": [str(t)[:16] for t in forecast["timestamps"]],
                "Üretim (kW)": [round(v, 2) for v in forecast["p50"]],
                "Min (P10)": [round(v, 2) for v in forecast["p10"]],
                "Max (P90)": [round(v, 2) for v in forecast["p90"]],
                "Güven %": [round(v, 1) for v in forecast["confidence"]],
            })
            st.dataframe(df, use_container_width=True, height=400)
    else:
        st.info("👈 Sol panelden parametreleri ayarlayıp **Tahmin Hesapla** butonuna basın.")

# ═══════════════════════════════════════════════════ #
#                 TAB 2: OPTİMİZASYON                 #
# ═══════════════════════════════════════════════════ #
with tab2:
    if "forecast" in st.session_state:
        from modules.battery_optimizer import BatteryOptimizer
        from modules.lp_optimizer import LPOptimizer
        from modules.mpc_optimizer import MPCOptimizer
        from modules.epias_price import get_epias_ptf, get_epdk_prices, build_price_dataframe
        from modules.utils import get_tariff_price, PROFILE_SOURCES, DAILY_CONSUMPTION_KWH

        st.subheader("⚡ Batarya & Satış Optimizasyonu")

        col_a, col_b, col_c = st.columns([2, 1, 1])
        with col_a:
            price_scenario = st.selectbox("💹 Fiyat Kaynağı",
                ["⏰ 3 Zamanlı (EPDK)", "📡 EPİAŞ Spot Piyasası (PTF)",
                 "🏷️ Tek Zamanlı (Sabit)", "✏️ Özel Giriş"])
        with col_b:
            consumption_profile = st.selectbox("Tüketim Profili",
                ["🏠 Ev", "🌾 Çiftlik", "🏢 İşyeri"])
        with col_c:
            optimizer_mode = st.selectbox("Optimizasyon Motoru",
                ["Linear Programming (Optimal)",
                 "Model Predictive Control (MPC)",
                 "Greedy Heuristic (Hızlı)"])

        # Profil kaynak bilgisi
        profile_source = PROFILE_SOURCES.get(consumption_profile, "")
        daily_kwh_default = DAILY_CONSUMPTION_KWH.get(consumption_profile, 7.5)
        st.caption(f"📚 **Veri Kaynağı:** {profile_source} | "
                   f"📊 Günlük ort. tüketim: **{daily_kwh_default:.1f} kWh/gün**")

        # ── Fiyat oluştur ──
        if "EPİAŞ" in price_scenario:
            _eu = st.session_state.get("epias_user", "")
            _ep = st.session_state.get("epias_pass", "")
            with st.spinner("📡 EPİAŞ fiyat verisi alınıyor..."):
                price_data = get_epias_ptf(hours=48, username=_eu, password=_ep)
            prices = price_data["prices"]
            src = price_data.get("source", "unknown")
            src_badge = "🟢 EPİAŞ Canlı" if src == "epias_live" else "🟡 Simülasyon"
            st.info(f"{src_badge} | Ort: {price_data['avg_price']:.3f} TL/kWh "
                    f"| Min: {price_data['min_price']:.3f} | Maks: {price_data['max_price']:.3f}")
            if price_data.get("tgt_error"):
                st.warning(f"⚠️ TGT: {price_data['tgt_error']}")
            elif price_data.get("info") and src == "epias_mock":
                st.caption(f"ℹ️ {price_data['info']} — Gerçek veri için sol panelden EPİAŞ girişi yapın.")
            # Fiyat grafiği
            price_df = build_price_dataframe(price_data, hours=48)
            fig_price = go.Figure()
            colors_map = {"🌙 Gece": "#2979FF", "🟡 Gündüz": "#FFD600", "🔴 Puant": "#FF1744"}
            for period, grp in price_df.groupby("tariff_period"):
                fig_price.add_trace(go.Bar(
                    x=grp.index, y=grp["price_tl_kwh"],
                    name=period, marker_color=colors_map.get(period, "#888")))
            fig_price.update_layout(
                title="📊 Saatlik Elektrik Fiyatı",
                yaxis_title="Fiyat (TL/kWh)",   # SOL KISIM
                xaxis_title="Zaman (Saat İndeksi)", # ALT KISIM
                barmode="stack", height=220, template="plotly_dark",
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=35, b=20), showlegend=True)
            st.plotly_chart(fig_price, use_container_width=True)
            st.session_state["price_info"] = price_data
        elif "Tek Zamanlı" in price_scenario:
            fixed_p = st.slider("Birim Fiyat (TL/kWh)", 0.5, 5.0, 2.04, 0.1)
            prices = [fixed_p] * 48
        elif "Özel" in price_scenario:
            c1, c2, c3 = st.columns(3)
            with c1:
                off_peak = st.number_input("Gece (22-06)", 0.5, 5.0, 1.08, 0.1)
            with c2:
                mid_peak = st.number_input("Gündüz (06-17)", 0.5, 5.0, 2.16, 0.1)
            with c3:
                peak = st.number_input("Puant (17-22)", 0.5, 8.0, 3.27, 0.1)
            prices = []
            for h in range(48):
                hr = h % 24
                if 22 <= hr or hr < 6:
                    prices.append(off_peak)
                elif 17 <= hr < 22:
                    prices.append(peak)
                else:
                    prices.append(mid_peak)
        else:  # 3 Zamanlı EPDK
            prices = [get_tariff_price(h % 24) for h in range(48)]

        if st.button("🎯 Optimizasyon Hesapla", type="primary"):
            use_lp  = "Linear" in optimizer_mode
            use_mpc = "MPC" in optimizer_mode
            if use_mpc:
                spinner_msg = "⏳ MPC kayan ufuk optimizasyonu (6h horizon)..."
            elif use_lp:
                spinner_msg = "⏳ LP optimal çözüm (scipy HiGHS)..."
            else:
                spinner_msg = "⏳ Greedy optimizasyon..."
            with st.spinner(spinner_msg):
                if use_mpc:
                    optimizer = MPCOptimizer(horizon=6)
                elif use_lp:
                    optimizer = LPOptimizer()
                else:
                    optimizer = BatteryOptimizer()
                result = optimizer.optimize(
                    production=st.session_state["forecast"]["p50"],
                    prices=prices,
                    battery_kwh=battery_kwh,
                    battery_kw=battery_kw,
                    consumption_profile=consumption_profile,
                )
            st.session_state["opt_result"] = result
            st.session_state["opt_prices"] = prices
            method_label = result.get("method", "greedy")
            if method_label == "linear_programming":
                lp_obj = result.get("lp_objective", 0)
                st.success(f"✅ LP Optimal çözüm! Net gelir: **{lp_obj:.2f} TL**")
            elif method_label == "mpc":
                lp_obj = result.get("lp_objective", 0)
                hz = result.get("mpc_horizon", 6)
                st.success(f"✅ MPC ({hz}s ufuk) tamamlandı! Net gelir: **{lp_obj:.2f} TL**")
            else:
                st.success("✅ Greedy optimizasyon tamamlandı!")

        if "opt_result" in st.session_state:
            result = st.session_state["opt_result"]
            prices = st.session_state["opt_prices"]

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("💰 Tasarruf", f"{result['total_savings']:.2f} TL",
                           f"+%{result['savings_pct']:.1f}")
            with c2:
                st.metric("🔋 Batarya Döngüsü", f"{result['battery_cycles']:.1f}",
                           "Optimal" if result["battery_cycles"] < 2 else "Yüksek")
            with c3:
                st.metric("📤 Şebekeye Satış", f"{result['grid_export_total']:.1f} kWh",
                           f"{result['export_revenue']:.2f} TL")

            st.divider()

            # Akış grafiği
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=result["timestamps"], y=result["production"],
                                   name="Üretim", marker_color="#FFD600"))
            fig2.add_trace(go.Bar(x=result["timestamps"], y=result["battery_charge"],
                                   name="Batarya Şarj", marker_color="#00C853"))
            fig2.add_trace(go.Bar(x=result["timestamps"],
                                   y=[-x for x in result["battery_discharge"]],
                                   name="Batarya Deşarj", marker_color="#FF9100"))
            fig2.add_trace(go.Scatter(x=result["timestamps"], y=result["consumption"],
                                       name="Tüketim", mode="lines",
                                       line=dict(color="#FF1744", width=2, dash="dot")))

            fig2.update_layout(
                title="📊 48 Saatlik Enerji Akış Planı",
                xaxis_title="Saat", yaxis_title="Enerji (kWh)",
                barmode="relative", height=500,
                template="plotly_dark",
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig2, use_container_width=True)

            # Aksiyon tablosu
            with st.expander("📋 Saatlik Aksiyon Planı"):
                act_df = pd.DataFrame({
                    "Saat": result["timestamps"],
                    "Üretim": [round(v, 2) for v in result["production"]],
                    "Tüketim": [round(v, 2) for v in result["consumption"]],
                    "Batarya ΔSoC": [round(v, 2) for v in result["battery_soc_change"]],
                    "İşlem": result["grid_action"],
                    "Fiyat (TL)": [round(prices[min(i, len(prices)-1)], 2)
                                    for i in result["timestamps"]],
                    "Kazanç (TL)": [round(v, 2) for v in result["hourly_savings"]],
                })
                st.dataframe(act_df, use_container_width=True, height=400)

            # Yıllık projeksiyon
            daily_savings = result["total_savings"] / 2  # 48h → 1 gün
            st.info(f"📅 **Yıllık Projeksiyon:** ~{daily_savings * 365:.0f} TL tasarruf "
                    f"(günlük ort. {daily_savings:.2f} TL)")

    else:
        st.warning("⚠️ Önce **Tahmin Sonuçları** sekmesinden hesaplama yapın!")

# ═══════════════════════════════════════════════════ #
#                  TAB 3: İZLEME                      #
# ═══════════════════════════════════════════════════ #
with tab3:
    if "forecast" in st.session_state:
        from modules.anomaly_detector import AnomalyDetector

        st.subheader("🔍 Canlı Sistem İzleme")
        izleme_mode = st.radio("Kaynak", ["🎬 Simülasyon", "📡 MQTT IoT (Gerçek)"],
                               horizontal=True, key="izleme_mode")

        if "MQTT" in izleme_mode:
            from modules.mqtt_client import get_mqtt_client
            st.info("📡 MQTT broker bağlantısı — broker adresi girin veya simülasyon modu kullanın.")
            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                mqtt_broker = st.text_input("Broker", "localhost", key="mqtt_broker")
            with m_col2:
                mqtt_port = st.number_input("Port", 1, 65535, 1883, key="mqtt_port")
            with m_col3:
                mqtt_id = st.text_input("Inverter ID", "inv001", key="mqtt_id")
            client = get_mqtt_client(mqtt_broker, int(mqtt_port), mqtt_id)
            latest = client.get_latest()
            sim_flag = latest.get("simulated", True)
            status_badge = "🟡 Simülasyon" if (sim_flag or not client.is_connected) else "🟢 Canlı MQTT"
            st.caption(f"Bağlantı durumu: {status_badge}")
            if latest:
                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("⚡ Anlık Güç", f"{latest.get('power_kw', 0):.2f} kW")
                mc2.metric("⚡ Gerilim", f"{latest.get('voltage', 0):.1f} V")
                mc3.metric("🌡️ Panel Sıcaklık", f"{latest.get('temp', 0):.1f} °C")
                mc4.metric("📶 Durum", str(latest.get('status', '-')).upper())
                hist = client.get_history(n=30)
                if len(hist) > 1:
                    pw_vals = [h.get('power_kw', 0) for h in hist]
                    fig_mqtt = go.Figure()
                    fig_mqtt.add_trace(go.Scatter(y=pw_vals, mode='lines+markers',
                        line=dict(color='#00C853', width=2),
                        name='Anlık Güç (kW)'))
                    fig_mqtt.update_layout(title="📡 MQTT Canlı Güç Akışı",
                        yaxis_title="kW", height=280, template="plotly_dark",
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig_mqtt, use_container_width=True)
            else:
                st.warning("Henüz veri alınamadı. Sayfayı yenileyin.")
        else:
            st.info("🎬 **Demo Modu:** Gerçek tesis için IoT/MQTT entegrasyonu gerekir.")

        col_ctrl1, col_ctrl2 = st.columns([1, 1])
        with col_ctrl1:
            sim_hour = st.slider("Simülasyon Saati", 0, 47, 12)
        with col_ctrl2:
            simulate_anomaly = st.checkbox("⚠️ Anomali Simüle Et")

        forecast = st.session_state["forecast"]
        detector = AnomalyDetector()

        expected = forecast["p50"][sim_hour]

        # Simüle ölçüm
        if simulate_anomaly:
            actual = expected * 0.45  # %55 düşük
        else:
            rng = np.random.RandomState(sim_hour)
            actual = expected * (0.92 + 0.16 * rng.random())

        # Anomali tespiti
        hist = forecast["p50"][max(0, sim_hour - 7):sim_hour]
        anomaly_result = detector.detect(actual=actual, expected=expected,
                                          historical=hist if hist else None)

        # Metrik kartları
        c1, c2, c3 = st.columns(3)
        with c1:
            delta = ((actual / expected - 1) * 100) if expected > 0 else 0
            st.metric("🔴 Anlık Üretim", f"{actual:.2f} kW", f"{delta:+.1f}%")
        with c2:
            st.metric("🎯 Beklenen", f"{expected:.2f} kW", "Tahmin")
        with c3:
            pr = (actual / expected * 100) if expected > 0 else 0
            pr_label = "Normal ✅" if 85 < pr < 115 else "⚠️ Sapma"
            st.metric("📊 Performans Oranı", f"{pr:.0f}%", pr_label)

        # Alarm
        if anomaly_result.get("alert"):
            st.error(f"""
            🚨 **ANOMALİ TESPİT EDİLDİ — {anomaly_result['severity']}**

            **Mesaj:** {anomaly_result['message']}
            **Z-Score:** {anomaly_result['z_score']:.2f}

            **Olası Nedenler:**
            {"".join(['- ' + c + chr(10) for c in anomaly_result.get('possible_causes', [])])}

            **Önerilen Aksiyon:** Sistem görsel kontrolü yapın, inverter loglarını inceleyin.
            """)
        else:
            st.success(f"✅ Sistem normal çalışıyor (Z-score: {anomaly_result.get('z_score', 0):.2f})")

        st.divider()

        # Son 10 saat performans grafiği
        start_h = max(0, sim_hour - 10)
        hours_range = list(range(start_h, sim_hour + 1))
        expected_vals = [forecast["p50"][h] for h in hours_range]
        actual_vals = []
        for h in hours_range:
            exp = forecast["p50"][h]
            if simulate_anomaly and h == sim_hour:
                actual_vals.append(exp * 0.45)
            else:
                rng_h = np.random.RandomState(h)
                actual_vals.append(exp * (0.92 + 0.16 * rng_h.random()))

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=hours_range, y=expected_vals, mode="lines",
                                   name="Beklenen", line=dict(color="#2979FF", dash="dash", width=2)))
        fig3.add_trace(go.Scatter(x=hours_range, y=actual_vals, mode="lines+markers",
                                   name="Gerçekleşen", line=dict(color="#00E676", width=3),
                                   marker=dict(size=8)))

        # Anomali noktası
        if anomaly_result.get("alert"):
            fig3.add_trace(go.Scatter(
                x=[sim_hour], y=[actual], mode="markers",
                marker=dict(size=16, color="#FF1744", symbol="x"),
                name="⚠️ Anomali",
            ))

        fig3.update_layout(
            title=f"Son {len(hours_range)} Saat — Gerçekleşen vs Beklenen (Saat: {sim_hour})",
            xaxis_title="Saat", yaxis_title="Üretim (kW)", height=400,
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.warning("⚠️ Önce **Tahmin Sonuçları** sekmesinden hesaplama yapın!")

# ═══════════════════════════════════════════════════ #
#             TAB 4: TÜRKİYE HARİTASI                #
# ═══════════════════════════════════════════════════ #
with tab4:
    from modules.turkey_map import create_turkey_map, TURKEY_PROVINCES, _estimate_wind_capacity_factor
    from modules.choropleth_map import create_choropleth_map

    st.subheader("🗺️ Türkiye Yenilenebilir Enerji Potansiyel Haritası")
    st.caption("81 il için güneş radyasyonu ve rüzgar hızı verileri (PVGIS & MENR referans)")

    # Harita türü + modu
    map_col1, map_col2 = st.columns([1, 3])
    with map_col1:
        map_type = st.radio("🗺️ Harita Türü",
            ["🔵 Daire İşaretçi", "🎨 GeoJSON Choropleth (Yeni)"],
            key="map_type_radio")
        map_mode = st.radio(
            "Katman",
            ["☀️ Güneş", "💨 Rüzgar", "☀️+💨 Her İkisi"],
            index=0,
            key="map_mode_radio",
        )

    # Map mode string'e çevir
    if "Rüzgar" in map_mode and "Güneş" not in map_mode:
        mode_str = "wind"
    elif "Her İkisi" in map_mode:
        mode_str = "both"
    else:
        mode_str = "solar"

    with map_col2:
        if "Choropleth" in map_type:
            st.info("🎨 **GeoJSON Choropleth:** İl sınırları renkli dolgu ile gösterilir. "
                    "GeoJSON GitHub'dan otomatik çekilir. İl sınırlarına tıklayarak detay görün.")
        elif mode_str == "wind":
            st.info("💨 **Rüzgar Haritası:** Daireler rüzgar hızına göre boyutlanır.")
        elif mode_str == "both":
            st.info("☀️💨 **Kombine Harita:** Sağ üst katman kontrolü ile geçiş yapın.")
        else:
            st.info("☀️ **Güneş Haritası:** Daireler güneş radyasyonuna göre boyutlanır.")

    if "Choropleth" in map_type:
        metric_key = "wind" if mode_str == "wind" else "solar"
        with st.spinner("🗺️ GeoJSON choropleth harita oluşturuluyor..."):
            turkey_m = create_choropleth_map(TURKEY_PROVINCES, metric=metric_key)
        st_folium(turkey_m, width=None, height=580, key="turkey_choropleth")
    else:
        turkey_m = create_turkey_map(map_mode=mode_str)
        st_folium(turkey_m, width=None, height=550, key="turkey_map")

    # İl karşılaştırma
    st.divider()
    st.subheader("📊 İl Karşılaştırması")

    # DataFrame oluştur
    compare_df = pd.DataFrame(TURKEY_PROVINCES)
    compare_df.columns = ["İl", "Enlem", "Boylam", "Güneş (kWh/m²/yıl)", "Rüzgar (m/s)"]
    compare_df["5kW GES Üretim (MWh/yıl)"] = (
        compare_df["Güneş (kWh/m²/yıl)"] * 5 * 0.85 / 1000
    ).round(1)
    compare_df["GES Yıllık Tasarruf (TL)"] = (
        compare_df["Güneş (kWh/m²/yıl)"] * 5 * 0.85 * 2.04 / 1000
    ).round(0)
    compare_df["Kapasite Faktörü (%)"] = compare_df["Rüzgar (m/s)"].apply(
        lambda x: round(_estimate_wind_capacity_factor(x) * 100, 0)
    )
    compare_df["10kW RES Üretim (MWh/yıl)"] = compare_df["Rüzgar (m/s)"].apply(
        lambda x: round(10 * _estimate_wind_capacity_factor(x) * 8760 / 1000, 1)
    )
    compare_df["RES Yıllık Gelir (TL)"] = (
        compare_df["10kW RES Üretim (MWh/yıl)"] * 1000 * 2.04
    ).round(0)

    # Grafik seçimi
    chart_type = st.radio(
        "Grafik Türü",
        ["☀️ Güneş Top 10", "💨 Rüzgar Top 10", "📊 Karşılaştırmalı"],
        horizontal=True,
        key="chart_type_radio",
    )

    if chart_type == "☀️ Güneş Top 10":
        solar_sorted = compare_df.sort_values("Güneş (kWh/m²/yıl)", ascending=False).head(10)
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            x=solar_sorted["İl"], y=solar_sorted["Güneş (kWh/m²/yıl)"],
            marker_color=["#00C853" if i == 0 else "#1a1f2b" for i in range(10)],
            marker_line=dict(color="#00C853", width=1),
            text=solar_sorted["Güneş (kWh/m²/yıl)"], textposition="outside",
        ))
        fig4.update_layout(
            title="☀️ En Yüksek Güneş Potansiyeli — Top 10 İl",
            yaxis_title="kWh/m²/yıl", height=400,
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig4, use_container_width=True)

    elif chart_type == "💨 Rüzgar Top 10":
        wind_sorted = compare_df.sort_values("Rüzgar (m/s)", ascending=False).head(10)
        fig_wind = go.Figure()
        fig_wind.add_trace(go.Bar(
            x=wind_sorted["İl"], y=wind_sorted["Rüzgar (m/s)"],
            marker_color=["#00BCD4" if i == 0 else "#1a2a3b" for i in range(10)],
            marker_line=dict(color="#00BCD4", width=1),
            text=[f"{v:.1f} m/s" for v in wind_sorted["Rüzgar (m/s)"]],
            textposition="outside",
        ))
        # Yatay referans çizgileri
        fig_wind.add_hline(y=5.0, line_dash="dash", line_color="#4CAF50",
                           annotation_text="Çok İyi (5+ m/s)", annotation_position="top left")
        fig_wind.add_hline(y=4.0, line_dash="dot", line_color="#FFC107",
                           annotation_text="İyi (4+ m/s)", annotation_position="top left")
        fig_wind.update_layout(
            title="💨 En Yüksek Rüzgar Potansiyeli — Top 10 İl",
            yaxis_title="Ortalama Rüzgar Hızı (m/s)", height=400,
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_wind, use_container_width=True)

        # Rüzgar top 10 ek bilgi
        st.markdown("#### 💨 Rüzgar Potansiyeli Detayları")
        wind_detail = wind_sorted[["İl", "Rüzgar (m/s)", "Kapasite Faktörü (%)",
                                    "10kW RES Üretim (MWh/yıl)", "RES Yıllık Gelir (TL)"]].reset_index(drop=True)
        wind_detail.index = wind_detail.index + 1
        st.dataframe(wind_detail, use_container_width=True)

    else:  # Karşılaştırmalı
        # Güneş vs Rüzgar scatter
        fig_compare = go.Figure()
        fig_compare.add_trace(go.Scatter(
            x=compare_df["Güneş (kWh/m²/yıl)"],
            y=compare_df["Rüzgar (m/s)"],
            mode="markers+text",
            text=compare_df["İl"],
            textposition="top center",
            textfont=dict(size=8, color="rgba(255,255,255,0.7)"),
            marker=dict(
                size=10,
                color=compare_df["Rüzgar (m/s)"],
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="Rüzgar (m/s)"),
                line=dict(width=1, color="white"),
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "☀️ Güneş: %{x} kWh/m²/yıl<br>"
                "💨 Rüzgar: %{y:.1f} m/s<br>"
                "<extra></extra>"
            ),
        ))
        # Çeyrek alanları
        fig_compare.add_hline(y=4.0, line_dash="dash", line_color="rgba(0,188,212,0.4)")
        fig_compare.add_vline(x=1500, line_dash="dash", line_color="rgba(0,200,83,0.4)")

        # Alan etiketleri
        fig_compare.add_annotation(x=1700, y=6.0, text="🌟 Hibrit Cennet",
                                    showarrow=False, font=dict(color="#00E676", size=12))
        fig_compare.add_annotation(x=1100, y=2.5, text="⚠️ Düşük Potansiyel",
                                    showarrow=False, font=dict(color="#FF5252", size=11))
        fig_compare.add_annotation(x=1700, y=2.5, text="☀️ Güneş Odaklı",
                                    showarrow=False, font=dict(color="#FFD600", size=11))
        fig_compare.add_annotation(x=1100, y=6.0, text="💨 Rüzgar Odaklı",
                                    showarrow=False, font=dict(color="#00BCD4", size=11))

        fig_compare.update_layout(
            title="☀️💨 Güneş vs Rüzgar — İl Bazlı Karşılaştırma",
            xaxis_title="Güneş Radyasyonu (kWh/m²/yıl)",
            yaxis_title="Ort. Rüzgar Hızı (m/s)",
            height=550,
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_compare, use_container_width=True)

    with st.expander("📋 Tüm İller — Güneş & Rüzgar Tablosu"):
        display_df = compare_df[["İl", "Güneş (kWh/m²/yıl)", "Rüzgar (m/s)",
                                  "5kW GES Üretim (MWh/yıl)", "GES Yıllık Tasarruf (TL)",
                                  "Kapasite Faktörü (%)", "10kW RES Üretim (MWh/yıl)",
                                  "RES Yıllık Gelir (TL)"]].sort_values(
                                      "Güneş (kWh/m²/yıl)", ascending=False).reset_index(drop=True)
        display_df.index = display_df.index + 1
        st.dataframe(display_df, use_container_width=True, height=500)

# ═══════════════════════════════════════════════════ #
#              TAB 5: FİNANSAL ANALİZ                #
# ═══════════════════════════════════════════════════ #
with tab5:
    from modules.financial_analyzer import (
        calculate_npv_irr, calculate_co2_savings,
        scenario_analysis, estimate_capex, battery_lifetime_estimate,
    )

    st.subheader("💰 Finansal Analiz & Yatırım Değerlendirmesi")

    # ─── Parametreler ─── #
    col_fin1, col_fin2, col_fin3 = st.columns(3)
    with col_fin1:
        fin_lifetime = st.slider("Sistem Ömrü (yıl)", 10, 30, 25, key="fin_lifetime")
        fin_discount = st.slider("İskonto Oranı (%)", 10, 35, 20, key="fin_discount")
    with col_fin2:
        fin_price_esc = st.slider("Yıllık Elektrik Fiyat Artışı (%)", 10, 60, 30, key="fin_esc")
        custom_capex = st.number_input("Özel Kurulum Maliyeti (TL, 0=otomatik)", 0, 5_000_000, 0, step=10000, key="capex_input")
    with col_fin3:
        elec_price = st.number_input("Elektrik Birim Fiyatı (TL/kWh)", 1.0, 10.0, 2.04, 0.1, key="elec_fin")

    if st.button("📊 Finansal Analiz Hesapla", type="primary", key="fin_btn"):
        # Tahmin verisi varsa kullan, yoksa tahmini değer
        if "forecast" in st.session_state:
            total_prod = st.session_state["forecast"]["total_production"]
            daily_kwh = total_prod / 2  # 48h → günlük
        else:
            # Tipik değer tahmini
            daily_kwh = installed_kw * 4.0 if "☀️" in system_type else installed_kw * 3.0
            st.info("ℹ️ Tahmin verisi yok — tipik üretim değerleri kullanılıyor. Önce Tab 1'den hesaplayın.")

        daily_savings_tl = daily_kwh * elec_price

        # CAPEX hesapla
        if custom_capex > 0:
            capex_data = {
                "total_capex_tl": custom_capex,
                "equipment_tl": custom_capex * 0.85,
                "battery_tl": custom_capex * 0.15 if battery_kwh > 0 else 0,
                "per_kw_tl": custom_capex / max(1, installed_kw),
                "cost_breakdown": {"Ekipman": custom_capex * 0.85, "Batarya": custom_capex * 0.15},
            }
        else:
            capex_data = estimate_capex(system_type, installed_kw, battery_kwh)

        total_capex = capex_data["total_capex_tl"]

        # NPV / IRR
        fin_result = calculate_npv_irr(
            daily_savings_tl=daily_savings_tl,
            capex_tl=total_capex,
            system_lifetime_years=fin_lifetime,
            discount_rate=fin_discount / 100,
            electricity_price_escalation=fin_price_esc / 100,
        )

        # CO₂
        co2_result = calculate_co2_savings(daily_kwh, fin_lifetime)

        # Senaryo analizi
        scenarios = scenario_analysis(daily_savings_tl, total_capex, fin_lifetime)

        # Batarya ömrü
        bat_cycles = st.session_state.get("opt_result", {}).get("battery_cycles", 0.5)
        bat_life = battery_lifetime_estimate(bat_cycles / 2, battery_kwh) if battery_kwh > 0 else None

        st.session_state["fin_result"] = fin_result
        st.session_state["co2_result"] = co2_result
        st.session_state["scenarios"] = scenarios
        st.session_state["capex_data"] = capex_data
        st.session_state["bat_life"] = bat_life
        st.session_state["daily_kwh_fin"] = daily_kwh
        st.success("✅ Finansal analiz tamamlandı!")

    if "fin_result" in st.session_state:
        fin_result = st.session_state["fin_result"]
        co2_result = st.session_state["co2_result"]
        scenarios = st.session_state["scenarios"]
        capex_data = st.session_state["capex_data"]
        bat_life = st.session_state.get("bat_life")
        daily_kwh_fin = st.session_state.get("daily_kwh_fin", 0)

        # ─── Ana Metrikler ─── #
        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1:
            npv_val = fin_result["npv"]
            st.metric("💰 NPV (NBD)", f"{npv_val:,.0f} TL",
                      "✅ Karlı" if npv_val > 0 else "❌ Zararlı")
        with mc2:
            irr_val = fin_result.get("irr")
            st.metric("📈 IRR (İVO)", f"%{irr_val:.1f}" if irr_val is not None else "—",
                      "Piyasa üstü" if (irr_val is not None and irr_val > 20) else "Düşük")
        with mc3:
            pb = fin_result.get("payback_years")
            st.metric("📅 Geri Ödeme", f"{pb:.1f} yıl" if pb is not None else "—",
                      "🚀 Hızlı" if (pb is not None and pb < 8) else None)
        with mc4:
            st.metric("🌱 CO₂ Tasarrufu", f"{co2_result['lifetime_co2_ton']:.1f} ton",
                      f"≈{co2_result['equivalent_trees']:.0f} ağaç/yıl")

        st.divider()

        # ─── Nakit Akışı Grafiği ─── #
        fig_cf = go.Figure()
        years = fin_result["years"]
        cum_cf = fin_result["cumulative_cash_flows"]
        annual_cf = fin_result["cash_flows"]

        fig_cf.add_trace(go.Bar(
            x=years[1:], y=annual_cf[1:],
            name="Yıllık Nakit Akışı",
            marker_color=["#00C853" if v > 0 else "#FF1744" for v in annual_cf[1:]],
        ))
        fig_cf.add_trace(go.Scatter(
            x=years, y=cum_cf,
            name="Kümülatif Nakit Akışı",
            line=dict(color="#FFD600", width=3),
            mode="lines+markers",
        ))
        fig_cf.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.4)")

        # Geri ödeme noktası
        pb_y = fin_result.get("payback_years")
        if pb_y:
            fig_cf.add_vline(x=pb_y, line_dash="dot", line_color="#00E5FF",
                             annotation_text=f"Geri Ödeme: {pb_y:.1f}y",
                             annotation_font_color="#00E5FF")

        fig_cf.update_layout(
            title="📊 Proje Nakit Akışı Analizi",
            xaxis_title="Yıl", yaxis_title="TL",
            template="plotly_dark", height=450,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_cf, use_container_width=True)

        # ─── Senaryo Karşılaştırması ─── #
        st.subheader("🔀 Senaryo Analizi")
        sc_cols = st.columns(3)
        for i, (sc_name, sc_data) in enumerate(scenarios.items()):
            with sc_cols[i]:
                sc_npv = sc_data["npv"]
                sc_irr = sc_data.get("irr")
                sc_pb = sc_data.get("payback_years")
                
                sc_irr_str = f"%{sc_irr:.1f}" if sc_irr is not None else "—"
                sc_pb_str = f"{sc_pb:.1f} yıl" if sc_pb is not None else "—"
                
                color = "#00C853" if sc_npv > 0 else "#FF5252"
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#1a1f2b,#2d3748);
                            border:1px solid {color}; border-radius:12px; padding:16px;">
                    <h4 style="color:{color};margin:0">{sc_name}</h4>
                    <small style="color:#aaa">{sc_data['label']}</small><br><br>
                    <b>NPV:</b> {sc_npv:,.0f} TL<br>
                    <b>IRR:</b> {sc_irr_str}<br>
                    <b>Geri Ödeme:</b> {sc_pb_str}
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        # ─── CO₂ & Çevre ─── #
        st.subheader("🌱 Çevre Etkisi")
        env_c1, env_c2, env_c3 = st.columns(3)
        with env_c1:
            st.metric("🌳 Eşdeğer Ağaç", f"{co2_result['equivalent_trees']:.0f} ağaç/yıl")
        with env_c2:
            st.metric("🚗 Araç Eşdeğeri", f"{co2_result['equivalent_cars']:.1f} araç/yıl")
        with env_c3:
            st.metric("💎 Karbon Değeri", f"{co2_result['carbon_value_tl']:,.0f} TL",
                      f"{fin_result['years'][-1]} yıl toplam")

        # ─── Maliyet Dağılımı ─── #
        st.subheader("🏗️ Kurulum Maliyeti Dağılımı")
        cost_items = {k: v for k, v in capex_data["cost_breakdown"].items() if v > 0}
        fig_pie = go.Figure(go.Pie(
            labels=list(cost_items.keys()),
            values=list(cost_items.values()),
            hole=0.45,
            marker=dict(colors=["#00C853", "#00BCD4", "#FFD600", "#FF9100", "#9C27B0", "#FF5252"]),
        ))
        fig_pie.update_layout(
            title=f"💰 Toplam Kurulum: {capex_data['total_capex_tl']:,.0f} TL",
            template="plotly_dark", height=380,
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

        if bat_life:
            st.info(f"🔋 **Batarya Ömrü:** ~{bat_life['lifetime_years']:.1f} yıl | "
                    f"Yenileme Maliyeti: {bat_life['replacement_cost_tl']:,.0f} TL | "
                    f"Yıllık Amortisman: {bat_life['annual_depreciation_tl']:,.0f} TL")
    else:
        st.info("👈 Parametreleri ayarlayıp **Finansal Analiz Hesapla** butonuna basın.")

# ═══════════════════════════════════════════════════ #
#              TAB 6: AI ÖNERİLERİ                   #
# ═══════════════════════════════════════════════════ #
with tab6:
    from modules.ai_advisor import AIAdvisor, SystemContext

    st.subheader("🤖 AI Öneri Motoru")
    st.caption("Sistem verilerinize göre otomatik üretilen akıllı öneriler")

    advisor = AIAdvisor()

    # Bağlam oluştur
    forecast_data = st.session_state.get("forecast", {})
    opt_data = st.session_state.get("opt_result", {})
    fin_data = st.session_state.get("fin_result", {})
    anomaly_flag = False  # Demo

    ctx = SystemContext(
        system_type=system_type,
        installed_kw=installed_kw,
        city=selected_city,
        lat=lat,
        lon=lon,
        battery_kwh=battery_kwh,
        total_production_kwh=forecast_data.get("total_production"),
        avg_confidence=forecast_data.get("avg_confidence"),
        low_production_hours=forecast_data.get("low_production_hours"),
        total_savings_tl=opt_data.get("total_savings"),
        battery_cycles=opt_data.get("battery_cycles"),
        export_revenue_tl=opt_data.get("export_revenue"),
        npv=fin_data.get("npv"),
        irr=fin_data.get("irr"),
        payback_years=fin_data.get("payback_years"),
        anomaly_detected=anomaly_flag,
    )

    # Özet kutusu
    summary = advisor.generate_summary(ctx)
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1a2b1a,#1a3030);
                border:1px solid #00C853; border-radius:12px; padding:18px; margin-bottom:20px;">
        <h4 style="color:#00C853;margin:0">📋 Sistem Özeti</h4>
        <p style="color:#eee;margin:8px 0 0 0">{summary}</p>
    </div>
    """, unsafe_allow_html=True)

    recommendations = advisor.generate_recommendations(ctx)

    if recommendations:
        for rec in recommendations:
            prio_colors = {
                "🔴 Kritik": "#FF1744",
                "🟠 Yüksek": "#FF9100",
                "🟡 Orta": "#FFD600",
                "🟢 Bilgi": "#00C853",
            }
            color = prio_colors.get(rec["priority"], "#888")
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#1a1f2b,#2d3748);
                        border-left:4px solid {color}; border-radius:8px;
                        padding:14px 18px; margin-bottom:12px;">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="font-size:1.1rem;font-weight:700;color:#eee">
                        {rec['icon']} {rec['title']}
                    </span>
                    <span style="font-size:0.8rem;color:{color};font-weight:600">
                        {rec['priority']}
                    </span>
                </div>
                <p style="color:#bbb;margin:8px 0 0 0;font-size:0.93rem">{rec['detail']}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ Sistem analiz edildi — kritik öneri yok. Daha fazla öneri için önce tahmin hesaplayın.")

    st.divider()
    st.markdown("#### 📚 Faydalı Kaynaklar")
    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        st.markdown("""
        **🏛️ Resmi Kaynaklar**
        - [EPDK Tarifeler](https://www.epdk.gov.tr)
        - [TEİAŞ Şebeke](https://www.teias.gov.tr)
        - [YEGM Teşvikler](https://www.yegm.gov.tr)
        """)
    with col_r2:
        st.markdown("""
        **📊 Veri Kaynakları**
        - [PVGIS Solar](https://re.jrc.ec.europa.eu/pvg_tools)
        - [Open-Meteo](https://open-meteo.com)
        - [IRENA Raporlar](https://www.irena.org)
        """)
    with col_r3:
        st.markdown("""
        **💰 Finansman**
        - [KOSGEB Destek](https://www.kosgeb.gov.tr)
        - [Yeşil Kredi (TCMB)](https://www.tcmb.gov.tr)
        - [KfW Turkey](https://www.kfw.de)
        """)

# ═══════════════════════════════════════════════════ #
#           TAB 7: IoT & PDF RAPOR                   #
# ═══════════════════════════════════════════════════ #
with tab7:
    st.subheader("📡 IoT İzleme & 📄 PDF Rapor")

    # ── PDF Rapor ──────────────────────────────────────────────────────
    st.markdown("### 📄 Tek Tıkla PDF Rapor")
    st.caption("Tahmin, optimizasyon, fiyat ve anomali sonuçlarını profesyonel A4 PDF'e aktar.")

    has_forecast = "forecast" in st.session_state
    has_opt      = "opt_result" in st.session_state

    if has_forecast:
        if st.button("📄 PDF Raporu Oluştur", type="primary", key="pdf_gen_btn"):
            try:
                from modules.pdf_report import generate_pdf_report
                with st.spinner("📄 PDF oluşturuluyor..."):
                    pdf_bytes = generate_pdf_report(
                        city=selected_city,
                        system_kw=installed_kw,
                        system_type="solar" if "☀️" in system_type else "wind",
                        forecast=st.session_state["forecast"],
                        optimization=st.session_state.get("opt_result"),
                        price_info=st.session_state.get("price_info"),
                        fin_result=st.session_state.get("fin_result"),
                        co2_result=st.session_state.get("co2_result"),
                        capex_data=st.session_state.get("capex_data"),
                    )
                st.session_state["pdf_bytes"] = pdf_bytes
                st.success("✅ PDF hazır! Aşağıdan indirebilirsiniz.")
            except ImportError as e:
                st.error(f"ReportLab kurulu değil: {e}. `pip install reportlab` çalıştırın.")
            except Exception as e:
                st.error(f"PDF oluşturma hatası: {e}")

        if "pdf_bytes" in st.session_state:
            fname = f"forecast2action_{selected_city}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            st.download_button(
                label="⬇️ PDF İndir",
                data=st.session_state["pdf_bytes"],
                file_name=fname,
                mime="application/pdf",
                use_container_width=True,
                key="pdf_download_btn",
            )
    else:
        st.warning("⚠️ Önce **Tahmin Sonuçları** sekmesinden hesaplama yapın, sonra PDF oluşturun.")

    st.divider()

    # ── MQTT Canlı Telemetri Özeti ──────────────────────────────────────
    st.markdown("### 📡 MQTT IoT — İnverter Telemetri Özeti")
    from modules.mqtt_client import get_mqtt_client

    m2col1, m2col2, m2col3 = st.columns(3)
    with m2col1:
        t7_broker = st.text_input("Broker IP", "localhost", key="t7_broker")
    with m2col2:
        t7_port = st.number_input("Port", 1, 65535, 1883, key="t7_port")
    with m2col3:
        t7_id = st.text_input("Inverter ID", "inv001", key="t7_id")

    client7 = get_mqtt_client(t7_broker, int(t7_port), t7_id)
    latest7 = client7.get_latest()
    hist7   = client7.get_history(n=24)

    sim7 = latest7.get("simulated", True)
    badge7 = "🟡 Simülasyon Modu" if (sim7 or not client7.is_connected) else "🟢 Canlı MQTT"
    st.caption(f"Durum: {badge7} | Broker: {t7_broker}:{t7_port} | ID: {t7_id}")

    if latest7:
        t7c1, t7c2, t7c3, t7c4 = st.columns(4)
        t7c1.metric("⚡ Güç",    f"{latest7.get('power_kw',0):.3f} kW")
        t7c2.metric("🔌 Voltaj", f"{latest7.get('voltage',0):.1f} V")
        t7c3.metric("🌡️ Sıcaklık", f"{latest7.get('temp',0):.1f} °C")
        t7c4.metric("📶 Durum",  str(latest7.get('status','-')).upper())

    if len(hist7) > 2:
        pw7 = [h.get('power_kw', 0) for h in hist7]
        fig7 = go.Figure()
        fig7.add_trace(go.Scatter(y=pw7, mode='lines+markers', fill='tozeroy',
            line=dict(color='#00C853', width=2), fillcolor='rgba(0,200,83,0.15)',
            name='Güç (kW)'))
        fig7.update_layout(title="📡 MQTT Telemetri — Son Ölçümler",
            yaxis_title="kW", height=300, template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig7, use_container_width=True)

    st.markdown("""
    **Gerçek inverter bağlantısı için:**
    ```
    Topic: solar/<inverter_id>/power  → anlık güç (W)
    Topic: solar/<inverter_id>/temp   → panel sıcaklığı
    Topic: solar/<inverter_id>/status → online/fault/idle
    ```
    Desteklenen: SMA, Huawei SUN2000, Growatt, Fronius (standart MQTT topic yapısı)
    """)

# ─────────────────── FOOTER ─────────────────── #
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p><strong>Forecast2Action</strong> | DU Hackathon 2026 — CodeXEnergy</p>
    <p>Fizik+PVGIS ML • LP Batarya • EPİAŞ Fiyat • MQTT IoT • Choropleth Harita • PDF Rapor • AI Öneriler</p>
</div>
""", unsafe_allow_html=True)
