# 🍽️ Dashboard BI — Program MBG Nasional

Dashboard Business Intelligence interaktif untuk monitoring & evaluasi program MBG (Makan Bergizi Gratis) nasional, dibangun dengan Streamlit + Plotly.

## Struktur Fitur (Multi-Page App)

| #     | Fitur                                                        | File                                    |
| ----- | ------------------------------------------------------------ | --------------------------------------- |
| 1     | Executive Summary                                            | `app.py`                                |
| 2     | Analisis Wilayah                                             | `pages/2__Analisis_Wilayah.py`          |
| 3     | Analisis Demografi                                           | `pages/3__Analisis_Demografi.py`        |
| 4     | Analisis Kondisi Khusus                                      | `pages/4__Analisis_Kondisi_Khusus.py`   |
| 5     | Analisis Penerima Manfaat                                    | `pages/5__Analisis_Penerima_Manfaat.py` |
| 6     | Analisis Sekolah                                             | `pages/6__Analisis_Sekolah.py`          |
| 7     | Analisis Tren                                                | `pages/7__Analisis_Tren.py`             |
| 8     | Dashboard Interaktif + Kesimpulan 6 Pertanyaan Kunci         | `pages/8_🎛️_Dashboard_Interaktif.py`    |
| Bonus | Multivariat Lanjutan (Clustering) & Skor Anomali + Hipotesis | `pages/9_🚩_Bonus_Anomali_Lanjutan.py`  |

Navigasi antar halaman otomatis muncul di sidebar (fitur native Streamlit multipage app).

## Filter Global (Sidebar, konsisten di semua halaman)

Tahun · Provinsi · Kabupaten/Kota · Kecamatan · Jenjang Pendidikan · Tipe Sekolah (Semua/Negeri/Swasta)

> **Catatan filter Negeri/Swasta:** dataset hanya punya _jumlah_ sekolah negeri vs swasta per kecamatan (bukan data peserta didik per jenis sekolah). Filter ini mengganti metrik jumlah satuan pendidikan yang dihitung, bukan memfilter baris data.

## Jalankan Lokal

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Struktur Project

```
mbg-dashboard/
├── app.py                          # Fitur 1: Executive Summary (entry point)
├── pages/                          # Fitur 2-8 + Bonus (auto-navigasi sidebar)
├── data/
│   └── mbg_dataset.csv
├── utils/
│   ├── data_loader.py              # load, cleaning, metrik turunan, agregasi, Gini
│   ├── filters.py                  # filter global sidebar (session_state)
│   ├── province_coords.py          # koordinat 38 provinsi untuk peta titik
│   └── hypothesis_engine.py        # skor anomali + bank hipotesis (fitur bonus)
├── requirements.txt
└── .streamlit/config.toml
```

## Deploy ke Streamlit Community Cloud

1. Push folder ini ke repo GitHub.
2. Buka https://share.streamlit.io → New app.
3. Pilih repo, branch `main`, main file path `app.py` (folder `pages/` otomatis terdeteksi).
4. Klik Deploy.

## Keterbatasan Data yang Diketahui

- Dataset mencakup ~36 dari 38 provinsi resmi Indonesia, level kecamatan.
- Hanya 1 tahun data (2026) — analisis tren tahun-ke-tahun belum bisa dilakukan secara harfiah (lihat Fitur 7 untuk detail & roadmap).
- Beberapa provinsi memiliki volume baris laporan yang jauh lebih kecil dibanding lainnya — indikasi kelengkapan pengumpulan data yang tidak seragam, bukan indikasi kecilnya pelaksanaan program di sana.
- Seluruh insight bersifat deskriptif/statistik, perlu verifikasi ke sumber resmi sebelum dijadikan dasar kebijakan.
