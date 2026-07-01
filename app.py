"""
Dashboard BI — Program MBG (Makan Bergizi Gratis) Nasional
Halaman utama: Fitur 1 — Executive Summary

Jalankan lokal:  streamlit run app.py
Navigasi ke fitur lain ada otomatis di sidebar (folder pages/).
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import gini_coefficient
from utils.filters import render_global_filters, get_satpen_column

st.set_page_config(
    page_title="Dashboard BI — Program MBG Nasional",
    layout="wide",
)

st.title("Dashboard BI — Program MBG Nasional")
st.caption("Fitur 1: Executive Summary — Ringkasan menyeluruh capaian program di seluruh Indonesia")

# ---------------------------------------------------------------------------
# Filter global (sidebar) — dipakai konsisten di semua halaman
# ---------------------------------------------------------------------------
df, tipe_sekolah = render_global_filters()
satpen_col = get_satpen_column(tipe_sekolah)

with st.expander("Tentang dataset & metodologi", expanded=False):
    st.markdown(
        f"""
        - Dataset berisi **{df.shape[0]:,} baris** laporan level kecamatan, mencakup **{df['provinsi_clean'].nunique()} dari 38 provinsi**
          resmi Indonesia (setelah filter aktif).
        - Beberapa provinsi belum/tidak terwakili karena kelengkapan pengumpulan data sumber yang tidak seragam — lihat **Fitur 7: Analisis Tren**
          dan halaman **Bonus: Anomali & Hipotesis** untuk detail kualitas data.
        - Tampilan saat ini: jenis sekolah **{tipe_sekolah}**.
        """
    )

st.markdown("---")
st.markdown("### Ringkasan Capaian (KPI Utama)")

total_satpen = int(df[satpen_col].sum())
total_laki = int(df["jumlah_laki"].sum())
total_perempuan = int(df["jumlah_perempuan"].sum())
total_penerima = int(df["jumlah_penerima_manfaat"].sum())
total_kondisi_khusus = int(df["jumlah_kondisi_khusus"].sum())
total_negeri = int(df["jumlah_satpen_negeri"].sum())
total_swasta = int(df["jumlah_satpen_swasta"].sum())

r1c1, r1c2, r1c3, r1c4 = st.columns(4)
r1c1.metric("Total Satuan Pendidikan", f"{total_satpen:,}")
r1c2.metric("Total Peserta Didik Laki-laki", f"{total_laki:,}")
r1c3.metric("Total Peserta Didik Perempuan", f"{total_perempuan:,}")
r1c4.metric("Total Penerima Manfaat", f"{total_penerima:,}")

r2c1, r2c2, r2c3 = st.columns(3)
r2c1.metric("Total Peserta Didik Berkondisi Khusus", f"{total_kondisi_khusus:,}")
r2c2.metric("Total Sekolah Negeri", f"{total_negeri:,}")
r2c3.metric("Total Sekolah Swasta", f"{total_swasta:,}")

st.caption(
    "**Insight:** " +
    (
        f"Penerima manfaat ({total_penerima:,}) hampir sama dengan jumlah laki-laki + perempuan tercatat "
        f"({total_laki + total_perempuan:,}) — konsisten secara matematis (setiap peserta didik = 1 penerima manfaat). "
        f"Proporsi sekolah negeri:swasta saat ini **{total_negeri/(total_negeri+total_swasta)*100:.1f}% : "
        f"{total_swasta/(total_negeri+total_swasta)*100:.1f}%**."
    )
)

st.markdown("---")
st.markdown("### Snapshot Komposisi")

g1, g2 = st.columns(2)
with g1:
    fig_gender = px.pie(
        names=["Laki-laki", "Perempuan"], values=[total_laki, total_perempuan],
        color=["Laki-laki", "Perempuan"], color_discrete_map={"Laki-laki": "#4C72B0", "Perempuan": "#DD8452"},
        title="Komposisi Gender Penerima Manfaat", hole=0.45,
    )
    st.plotly_chart(fig_gender, width="stretch")

with g2:
    fig_sekolah = px.pie(
        names=["Negeri", "Swasta"], values=[total_negeri, total_swasta],
        color=["Negeri", "Swasta"], color_discrete_map={"Negeri": "#55A868", "Swasta": "#C44E52"},
        title="Komposisi Sekolah Negeri vs Swasta", hole=0.45,
    )
    st.plotly_chart(fig_sekolah, width="stretch")

st.markdown("---")
st.markdown("###Top 10 Provinsi berdasarkan Total Penerima Manfaat")
top10 = (
    df.groupby("provinsi_clean", as_index=False)["jumlah_penerima_manfaat"].sum()
    .sort_values("jumlah_penerima_manfaat", ascending=False).head(10)
)
fig_top10 = px.bar(
    top10, x="jumlah_penerima_manfaat", y="provinsi_clean", orientation="h",
    color="jumlah_penerima_manfaat", color_continuous_scale="Reds",
    labels={"jumlah_penerima_manfaat": "Total Penerima Manfaat", "provinsi_clean": "Provinsi"},
    height=420,
)
fig_top10.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
st.plotly_chart(fig_top10, width="stretch")

gini_now = gini_coefficient(df.groupby("provinsi_clean")["jumlah_penerima_manfaat"].sum().values)
st.caption(
    f"**Insight:** Sepuluh provinsi teratas ini menyumbang **"
    f"{top10['jumlah_penerima_manfaat'].sum() / df['jumlah_penerima_manfaat'].sum() * 100:.1f}%** dari total "
    f"penerima manfaat nasional. Gini Index distribusi antar provinsi saat ini **{gini_now:.3f}** "
    f"(semakin mendekati 1 = semakin timpang). Detail lengkap ada di **Fitur 2: Analisis Wilayah**."
)

st.markdown("---")
st.success(
    "**Lanjutkan eksplorasi:** Gunakan menu navigasi di sidebar (kiri) untuk membuka fitur lain — "
    "Analisis Wilayah, Demografi, Kondisi Khusus, Penerima Manfaat, Sekolah, Tren, hingga Dashboard Interaktif penuh."
)

st.markdown("---")
st.caption(
    "Dashboard BI Program MBG Nasional — disusun untuk tujuan monitoring & evaluasi. "
    "Seluruh insight bersifat deskriptif berbasis data yang tersedia; perlu diverifikasi ke sumber resmi untuk pengambilan keputusan formal."
)
