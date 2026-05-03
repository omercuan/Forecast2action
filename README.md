# ⚡ Forecast2Action

**Yenilenebilir Enerji Karar Destek Sistemi** — DU Hackathon 2026 | CodeXEnergy

> Küçük ve orta ölçekli güneş/rüzgar enerjisi üreticileri için geliştirilmiş otonom bir akıllı asistandır. Hava durumunu yüksek hassasiyetle elektrik üretimine çevirir, EPİAŞ fiyatlarına göre batarya kullanımını optimize eder ve üretim hatalarını yapay zeka ile tespit eder.

### 📺 Proje Sunumu (Pitch Deck)
Jüri değerlendirmesi için hazırladığımız proje sunum dosyasına aşağıdaki bağlantıdan ulaşabilirsiniz:
👉 **[Sunum Dosyasına Git (Google Drive) - LİNKİ BURAYA YAPIŞTIRIN](https://drive.google.com/...)**

## 🎯 Çözdüğü 3 Ana Problem

1. **☀️ Üretim Belirsizliği:** "Yarın saat saat kaç kWh üreteceğim?" → Hibrit (Fizik+ML) model ile 48 saatlik üretim tahmini ve P10/P50/P90 güven aralığı hesaplaması.
2. **💰 Fiyat Optimizasyonu:** "Enerjiyi şebekeye ne zaman satmalıyım?" → EPİAŞ Canlı PTF verileri kullanılarak **MPC (Model Predictive Control)** ve Linear Programming algoritmalarıyla bataryanın şarj/deşarj döngüsü optimize edilir, maksimum kar sağlanır.
3. **🔧 Arıza & Anomali:** "Sistemimde fark etmediğim bir arıza var mı?" → Z-score ve IsolationForest algoritmaları ile çift katmanlı anomali tespiti.

## 🏗️ Sistem Mimarisi

```
Forecast2Action Motoru
├── 1. Veri ve Tahmin Katmanı (Fizik + ML)
│   ├── Open-Meteo & PVGIS API entegrasyonu
│   └── LightGBM Quantile Regression (Belirsizlik bandı)
│
├── 2. Finans ve Optimizasyon Katmanı (Matematiksel Karar)
│   ├── eptr2 kütüphanesi ile EPİAŞ Şeffaflık Platformu (Canlı PTF)
│   ├── Greedy Heuristic, Linear Programming (Optimal) ve **MPC (Model Predictive Control)** Algoritmaları
│   └── NPV, ROI, IRR Finansal Fizibilite Hesaplamaları
│
└── 3. IoT & Raporlama Katmanı (Endüstriyel Çıktı)
    ├── MQTT tabanlı Canlı İnverter Simülasyonu
    └── ReportLab ile Kurumsal PDF Rapor Üretimi
```

## 🚀 Kurulum & Lokal Kullanım (Sadece 3 Komut)

Proje tamamen Python tabanlıdır ve Streamlit ile geliştirilmiştir. JavaScript, HTML veya CSS bilgisine gerek kalmadan saniyeler içinde ayağa kalkar.

```bash
git clone https://github.com/USERNAME/forecast2action.git
cd forecast2action
pip install -r requirements.txt
streamlit run app.py
```

## 📊 Öne Çıkan Özellikler

| Özellik | Kullanılan Teknoloji / Yöntem |
|---------|----------|
| **Canlı Piyasa Fiyatları** | EPİAŞ CAS TGT & REST API Entegrasyonu |
| **Gelişmiş Batarya Optimizasyonu**| `MPC (Model Öngörülü Kontrol)` ve `Doğrusal Programlama` (SciPy) |
| **Üretim Tahmini** | `LightGBM` Quantile Regression (P10/P50/P90) |
| **Anomali Tespiti** | `scikit-learn` IsolationForest & Z-Score |
| **Türkiye Potansiyel Haritası**| `Folium` & GeoJSON ile İnteraktif Kloroplet Harita |
| **PDF Rapor & IoT** | `reportlab` ile dökümantasyon, `paho-mqtt` ile endüstri standardı |

## 🛠️ Teknolojik Altyapı Stoku

- **UI & Frontend:** Streamlit (Tamamen Python ile Full-Stack)
- **Veri Analizi:** Pandas, Numpy, SciPy
- **Makine Öğrenmesi:** Scikit-Learn, LightGBM
- **Veri Görselleştirme:** Plotly Express, Folium
- **Endüstriyel Araçlar:** eptr2 (EPİAŞ), paho-mqtt (IoT), ReportLab (PDF)

## 👥 Ekip & Organizasyon

Bu proje **DU Hackathon 2026 — CodeXEnergy Challenge** kapsamında 36 saatlik geliştirme sürecinde sıfırdan tasarlanmış ve kodlanmıştır.

## 📄 Lisans

MIT License
