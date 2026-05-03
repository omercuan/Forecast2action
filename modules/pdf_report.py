"""PDF Rapor - ReportLab (emoji->metin, guzel tasarim)"""
import io
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, PageBreak, KeepTogether,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_OK = True
    C_GREEN   = colors.HexColor("#00875A")
    C_GREEN2  = colors.HexColor("#00C853")
    C_TEAL    = colors.HexColor("#00BFA5")
    C_DARK    = colors.HexColor("#1A1F2B")
    C_GRAY    = colors.HexColor("#7F8C8D")
    C_LGRAY   = colors.HexColor("#ECF0F1")
    C_YELLOW  = colors.HexColor("#F39C12")
    C_RED     = colors.HexColor("#C0392B")
    C_WHITE   = colors.white
    C_BG      = colors.HexColor("#F0FBF4")
    W_PAGE    = A4[0] - 4*cm
except ImportError:
    REPORTLAB_OK = False
    C_GREEN = C_GREEN2 = C_TEAL = C_DARK = C_GRAY = None
    C_LGRAY = C_YELLOW = C_RED = C_WHITE = C_BG = None
    W_PAGE = 500

def _safe(text):
    """Emoji ve ozel karakterleri metin karsiligina cevir."""
    replacements = {
        "⚡":"[Enerji]","☀️":"[Gunes]","💨":"[Ruzgar]","🔋":"[Batarya]",
        "📊":"[Grafik]","📈":"[Artis]","📉":"[Dusus]","💰":"[Para]",
        "🎯":"[Hedef]","🔄":"[Dongu]","💸":"[Gelir]","🔧":"[Ayar]",
        "📡":"[Veri]","🟢":"[●]","🟡":"[◐]","🔴":"[○]","⚠️":"[!]",
        "✅":"[OK]","🌱":"[CO2]","🚀":"[Hizli]","📍":"[Konum]",
        "🕐":"[Saat]","🔍":"[Analiz]","📋":"[Rapor]","🏗️":"[Yatirim]",
        "🌳":"[Agac]","🚗":"[Arac]","💎":"[Karbon]","📅":"[Tarih]",
        "🌙":"[Gece]","⚙️":"[Sistem]","🤖":"[AI]","📄":"[PDF]",
        "▶":"","◀":"","→":">","←":"<","★":"*","☆":"*",
        "\u2019":"'","\u2018":"'","\u201c":'"',"\u201d":'"',
    }
    for k, v in replacements.items():
        text = str(text).replace(k, v)
    # Kalan emoji benzeri karakterleri temizle
    result = ""
    for ch in text:
        cp = ord(ch)
        if cp < 0x2000 or (0x2010 <= cp <= 0x2027) or (0x2030 <= cp <= 0x205E):
            result += ch
        elif cp < 0x10000 and not (0x1F000 <= cp <= 0x1FFFF):
            try:
                ch.encode("cp1252")
                result += ch
            except Exception:
                result += "?"
        else:
            result += "?"
    return result


def _st(name, **kw):
    return ParagraphStyle(name, **kw)


def _h_section(text, n=1):
    """Bolum basligi - renkli sol bant."""
    size = 14 if n == 1 else 11
    color = C_GREEN if n == 1 else C_TEAL
    return Paragraph(
        f'<font color="{color.hexval()}" size="{size}"><b>{_safe(text)}</b></font>',
        _st(f"h{n}", spaceBefore=10, spaceAfter=4, leading=size+4)
    )


def _body(text):
    return Paragraph(_safe(text), _st("bd", fontSize=9, leading=13, spaceAfter=2))


def _kv_table(rows, col_w=None):
    """Anahtar-Deger tablosu."""
    col_w = col_w or [7*cm, W_PAGE - 7*cm]
    safe_rows = [[_safe(str(c)) for c in row] for row in rows]
    tbl = Table(safe_rows, colWidths=col_w)
    hdr = len(safe_rows) > 0
    style = [
        ("FONTNAME",   (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",   (0,0), (-1,-1), 9),
        ("GRID",       (0,0), (-1,-1), 0.3, C_GRAY),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",(0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[C_WHITE, C_BG]),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
    ]
    if hdr:
        style += [
            ("BACKGROUND", (0,0), (-1,0), C_GREEN),
            ("TEXTCOLOR",  (0,0), (-1,0), C_WHITE),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,0), 9),
        ]
    tbl.setStyle(TableStyle(style))
    return tbl


def _divider():
    return HRFlowable(width="100%", thickness=0.5, color=C_TEAL, spaceAfter=6, spaceBefore=6)


def _build_cover(city, kw, stype, fin=None, co2=None):
    items = []
    items.append(Spacer(1, 2.5*cm))

    # Baslik kutusu
    title_data = [[
        Paragraph(
            '<font color="#00875A" size="26"><b>Forecast2Action</b></font>',
            _st("ct", alignment=TA_CENTER, leading=32)
        )
    ]]
    title_tbl = Table(title_data, colWidths=[W_PAGE])
    title_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), C_DARK),
        ("TOPPADDING", (0,0), (-1,-1), 18),
        ("BOTTOMPADDING",(0,0),(-1,-1), 10),
        ("ROUNDEDCORNERS",(0,0),(-1,-1), 8),
    ]))
    items.append(title_tbl)
    items.append(Spacer(1, 0.3*cm))

    # Alt baslik
    stype_tr = "Gunes Enerji Sistemi" if stype == "solar" else "Ruzgar Enerji Sistemi"
    items.append(Paragraph(
        f'<font color="{C_TEAL.hexval()}" size="13">'
        f'Yenilenebilir Enerji Karar Destek Raporu — {stype_tr}</font>',
        _st("sub", alignment=TA_CENTER, spaceAfter=20)
    ))

    # Meta bilgi karti
    date_str = datetime.now().strftime("%d.%m.%Y  %H:%M")
    meta = [
        ["Bilgi", "Deger"],
        ["Lokasyon", _safe(city)],
        ["Kurulu Guc", f"{kw} kW"],
        ["Sistem Tipi", stype_tr],
        ["Rapor Tarihi", date_str],
        ["Uygulama", "Forecast2Action — DU Hackathon 2026"],
        ["Ekip", "CodeXEnergy"],
    ]
    if fin:
        npv = fin.get("npv", 0)
        pb  = fin.get("payback_years")
        meta.append(["NPV (Net Bugunki Deger)", f"{npv:,.0f} TL"])
        if pb:
            meta.append(["Geri Odeme Suresi", f"{pb:.1f} yil"])
    if co2:
        meta.append(["CO2 Tasarrufu (omur boyunca)", f"{co2.get('lifetime_co2_ton',0):.1f} ton"])

    items.append(_kv_table(meta, col_w=[6*cm, W_PAGE-6*cm]))
    items.append(Spacer(1, 1*cm))

    # Alt bilgi bandı
    items.append(Paragraph(
        '<font color="#7F8C8D" size="8">Bu rapor Forecast2Action sistemi tarafindan otomatik olusturulmustur. '
        'Fizik+ML hibrit model | PVGIS gercek veri | EPİAS spot fiyat | LP optimal batarya</font>',
        _st("note", alignment=TA_CENTER)
    ))
    return items


def _build_forecast_section(forecast, stype):
    items = [_h_section("1. Uretim Tahmini (48 Saat)")]

    total  = forecast.get("total_production", 0)
    max_p  = forecast.get("max_production", 0)
    max_h  = forecast.get("max_hour", "N/A")
    conf   = forecast.get("avg_confidence", 0)
    low_h  = forecast.get("low_production_hours", 0)
    p50    = forecast.get("p50", [])
    p10    = forecast.get("p10", [])
    p90    = forecast.get("p90", [])

    daily  = total / 2 if total else 0
    conf_label = "Yuksek" if conf > 70 else ("Orta" if conf > 50 else "Dusuk")

    ozet = [
        ["Gosterge", "Deger", "Yorum"],
        ["Toplam Tahmin Uretim (P50)", f"{total:.1f} kWh", f"Gunluk ort: {daily:.1f} kWh"],
        ["Maks. Anlik Guc (P50)",     f"{max_p:.2f} kW",  f"Pik saat: {_safe(str(max_h))[:16]}"],
        ["Ortalama Guven Skoru",       f"%{conf:.0f}",     conf_label],
        ["Dusuk Uretim Saati (<0.5kW)", f"{low_h} saat",  f"48 saatin %{low_h/48*100:.0f}'i"],
    ]
    if p10 and p90:
        ozet.append(["P10 (Kotumser Senaryo)", f"{sum(p10):.1f} kWh", "Alt sinir"])
        ozet.append(["P90 (Iyimser Senaryo)",  f"{sum(p90):.1f} kWh", "Ust sinir"])
        bant = sum(p90) - sum(p10)
        ozet.append(["Belirsizlik Bandi (P90-P10)", f"{bant:.1f} kWh", f"Ort band: {bant/48:.2f} kW/saat"])

    items.append(_kv_table(ozet, col_w=[6*cm, 3.5*cm, W_PAGE-9.5*cm]))
    items.append(Spacer(1, 0.3*cm))

    # Saatlik ozet tablo (her 3 saat)
    if p50:
        items.append(_h_section("Saatlik Uretim Ozeti (her 3 saat)", n=2))
        rows = [["Saat", "P10 (kW)", "P50 (kW)", "P90 (kW)", "Guven %"]]
        confidences = forecast.get("confidence", [100]*48)
        for i in range(0, min(len(p50), 48), 3):
            rows.append([
                f"{i:02d}:00",
                f"{p10[i]:.2f}" if i < len(p10) else "-",
                f"{p50[i]:.2f}",
                f"{p90[i]:.2f}" if i < len(p90) else "-",
                f"%{confidences[i]:.0f}" if i < len(confidences) else "-",
            ])
        col_w = [2*cm, 3*cm, 3*cm, 3*cm, 3*cm]
        safe_rows = [[_safe(str(c)) for c in r] for r in rows]
        tbl = Table(safe_rows, colWidths=col_w)
        tbl.setStyle(TableStyle([
            ("FONTNAME",    (0,0), (-1,-1), "Helvetica"),
            ("FONTSIZE",    (0,0), (-1,-1), 8),
            ("GRID",        (0,0), (-1,-1), 0.3, C_GRAY),
            ("BACKGROUND",  (0,0), (-1,0), C_DARK),
            ("TEXTCOLOR",   (0,0), (-1,0), C_WHITE),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("ALIGN",       (1,0), (-1,-1), "CENTER"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[C_WHITE, C_BG]),
            ("TOPPADDING",  (0,0), (-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ]))
        items.append(tbl)

    return items


def _build_optimization_section(opt):
    items = [_h_section("2. Batarya Optimizasyon Sonuclari")]

    method  = opt.get("method", "greedy")
    savings = opt.get("total_savings", 0)
    pct     = opt.get("savings_pct", 0)
    cycles  = opt.get("battery_cycles", 0)
    revenue = opt.get("export_revenue", 0)
    lp_obj  = opt.get("lp_objective")

    method_tr = "Linear Programming (Optimal - scipy HiGHS)" if method == "linear_programming" else "Greedy Algoritma"

    ozet = [
        ["Gosterge", "Deger", "Aciklama"],
        ["Optimizasyon Yontemi", method_tr, ""],
        ["Toplam Tasarruf (48 saat)", f"{savings:.2f} TL", f"%{pct:.1f} iyilestirme"],
        ["Yillik Projeksiyon", f"{savings/2*365:,.0f} TL", "48h->gun->yil"],
        ["Batarya Dongu Sayisi", f"{cycles:.2f}", "Optimal: <1/gun"],
        ["Sebekeye Satis Geliri", f"{revenue:.2f} TL", "48 saatte"],
    ]
    if lp_obj is not None:
        ozet.append(["LP Optimal Net Gelir", f"{lp_obj:.2f} TL", "Matematiksel garantili"])

    items.append(_kv_table(ozet, col_w=[6*cm, 4*cm, W_PAGE-10*cm]))
    items.append(Spacer(1, 0.3*cm))

    # Aksiyon tablosu
    actions = opt.get("grid_action", [])
    h_sav   = opt.get("hourly_savings", [])
    prod    = opt.get("production", [])
    cons    = opt.get("consumption", [])
    b_soc   = opt.get("battery_soc", [])

    if actions:
        items.append(_h_section("48 Saat Aksiyon Plani", n=2))
        rows = [["Saat", "Uretim kW", "Tuketim kW", "Aksiyon", "Tasarruf TL"]]
        for i in range(min(len(actions), 48)):
            pr = f"{prod[i]:.2f}" if i < len(prod) else "-"
            co = f"{cons[i]:.2f}" if i < len(cons) else "-"
            sv = f"{h_sav[i]:.2f}" if i < len(h_sav) else "-"
            rows.append([f"{i:02d}:00", pr, co, _safe(actions[i])[:22], sv])

        safe_rows = [[_safe(str(c)) for c in r] for r in rows]
        tbl = Table(safe_rows, colWidths=[1.8*cm, 2.2*cm, 2.4*cm, 6.5*cm, 2.5*cm])
        tbl.setStyle(TableStyle([
            ("FONTNAME",    (0,0), (-1,-1), "Helvetica"),
            ("FONTSIZE",    (0,0), (-1,-1), 7.5),
            ("GRID",        (0,0), (-1,-1), 0.3, C_GRAY),
            ("BACKGROUND",  (0,0), (-1,0), C_GREEN),
            ("TEXTCOLOR",   (0,0), (-1,0), C_WHITE),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[C_WHITE, C_BG]),
            ("ALIGN",       (1,0), (-1,-1), "CENTER"),
            ("ALIGN",       (3,1), (3,-1), "LEFT"),
            ("TOPPADDING",  (0,0), (-1,-1), 3),
            ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ]))
        items.append(tbl)

    return items


def _build_price_section(price_info):
    items = [_h_section("3. Elektrik Fiyat Analizi")]
    source = price_info.get("source", "unknown")
    src_label = "EPİAS Canli Veri" if source == "epias_live" else "Simulasyon (EPİAS erisimi yok)"

    data = [
        ["Gosterge", "Deger"],
        ["Veri Kaynagi",    src_label],
        ["Ortalama Fiyat",  f"{price_info.get('avg_price', 0):.3f} TL/kWh"],
        ["Maksimum Fiyat",  f"{price_info.get('max_price', 0):.3f} TL/kWh"],
        ["Minimum Fiyat",   f"{price_info.get('min_price', 0):.3f} TL/kWh"],
    ]
    prices = price_info.get("prices", [])
    if prices:
        import statistics
        data.append(["Fiyat Std Sapmasi", f"{statistics.stdev(prices):.3f} TL/kWh"])

    items.append(_kv_table(data))
    return items


def _build_financial_section(fin, co2, cap):
    items = [_h_section("4. Finansal Analiz")]

    npv = fin.get("npv", 0)
    irr = fin.get("irr")
    pb  = fin.get("payback_years")
    total_capex = cap.get("total_capex_tl", 0) if cap else 0

    fin_data = [
        ["Finansal Gosterge", "Deger", "Yorum"],
        ["Toplam Yatirim (CAPEX)", f"{total_capex:,.0f} TL", "Panel+Invertor+Montaj+Batarya"],
        ["Net Bugunki Deger (NPV)", f"{npv:,.0f} TL", "Karli" if npv > 0 else "Zarar"],
        ["Ic Verim Orani (IRR)", f"%{irr:.1f}" if irr else "-", "Piyasa ustu" if irr and irr > 20 else ""],
        ["Geri Odeme Suresi", f"{pb:.1f} yil" if pb else "-", "Hedef: <10 yil"],
    ]
    cf = fin.get("cash_flows", [])
    if cf:
        fin_data.append(["Toplam Nakit Akisi", f"{sum(cf[1:]):,.0f} TL", "Yatirim haric"])

    items.append(_kv_table(fin_data, col_w=[6*cm, 4*cm, W_PAGE-10*cm]))
    items.append(Spacer(1, 0.4*cm))

    if co2:
        items.append(_h_section("Cevre Etkisi", n=2))
        co2_data = [
            ["Cevre Gostergesi", "Deger"],
            ["Yillik CO2 Tasarrufu", f"{co2.get('annual_co2_kg', 0):.0f} kg"],
            ["Omur Boyunca CO2 Tasarrufu", f"{co2.get('lifetime_co2_ton', 0):.1f} ton"],
            ["Esde. Agac/Yil", f"{co2.get('equivalent_trees', 0):.0f} agac"],
            ["Esde. Tasit/Yil", f"{co2.get('equivalent_cars', 0):.1f} arac"],
            ["Karbon Degeri", f"{co2.get('carbon_value_tl', 0):,.0f} TL"],
        ]
        items.append(_kv_table(co2_data))

    return items


def generate_pdf_report(
    city, system_kw, system_type,
    forecast, optimization=None, anomalies=None,
    price_info=None, fin_result=None, co2_result=None, capex_data=None,
):
    if not REPORTLAB_OK:
        raise ImportError("reportlab kurulu degil: pip install reportlab")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2.2*cm,
        title=f"Forecast2Action — {city} Raporu",
        author="Forecast2Action — CodeXEnergy",
    )
    story = []

    # Kapak
    story += _build_cover(city, system_kw, system_type, fin_result, co2_result)
    story.append(PageBreak())

    # 1. Tahmin
    story += _build_forecast_section(forecast, system_type)
    story.append(_divider())

    # 2. Optimizasyon
    if optimization:
        story.append(PageBreak())
        story += _build_optimization_section(optimization)
        story.append(_divider())

    # 3. Fiyat
    if price_info:
        story += _build_price_section(price_info)
        story.append(_divider())

    # 4. Finansal
    if fin_result:
        story.append(PageBreak())
        story += _build_financial_section(
            fin_result,
            co2_result or {},
            capex_data or {},
        )
        story.append(_divider())

    # Footer
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=C_GREEN2))
    story.append(Spacer(1, 0.15*cm))
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    story.append(Paragraph(
        f'<font size="7.5" color="#7F8C8D">'
        f'Forecast2Action  |  Uretildi: {now_str}  |  '
        f'DU Hackathon 2026  |  CodeXEnergy  |  '
        f'Fizik+PVGIS ML  |  LP Batarya  |  EPİAS  |  MQTT IoT'
        f'</font>',
        _st("ftr", alignment=TA_CENTER)
    ))

    doc.build(story)
    return buf.getvalue()
