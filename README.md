# 🍽️ Dashboard Interaktif MBG (Makan Bergizi Gratis)

Dashboard eksplorasi data MBG berbasis Streamlit untuk menemukan **ketimpangan antar daerah**, **anomali rasio**, dan **red flags kualitas pelaporan** dari data program MBG.

## Fitur

- **Toggle level data**: Provinsi / Kabupaten-Kota / Kecamatan
- **Tab Overview**: ranking & Kurva Lorenz (ketimpangan distribusi)
- **Tab Bivariat**: scatter plot dinamis (pilih sumbu X/Y bebas) + box plot per provinsi
- **Tab Multivariat**: correlation heatmap, parallel coordinates, radar chart, clustering K-Means
- **Tab Red Flags**: duplikat data, rasio ekstrem, ketidakseimbangan volume laporan antar provinsi, anomali gender

## Jalankan Lokal

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Struktur Project

```
mbg-dashboard/
├── app.py                  # entry point Streamlit
├── data/
│   └── mbg_dataset.csv     # dataset MBG
├── utils/
│   └── data_loader.py      # load, cleaning, metrik turunan, agregasi
├── requirements.txt
└── .streamlit/config.toml  # tema warna
```

## Deploy ke Streamlit Community Cloud

1. Push folder ini ke repo GitHub (public atau private).
2. Buka https://share.streamlit.io → New app.
3. Pilih repo, branch `main`, main file path `app.py`.
4. Klik Deploy.

## Catatan

Dataset mencakup 36 dari ~38 provinsi Indonesia, level kecamatan, hasil gabungan beberapa file sumber sehingga kelengkapan antar provinsi tidak seragam. Semua insight bersifat deskriptif dan perlu verifikasi lanjutan ke sumber resmi.
