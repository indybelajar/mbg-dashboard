"""Fitur 4 — Analisis Kondisi Khusus: alergi, fobia, intoleransi peserta didik."""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import detect_outliers_iqr
from utils.filters import render_global_filters, get_satpen_column

st.set_page_config(page_title="Fitur 4: Analisis Kondisi Khusus", layout="wide")
st.title("Fitur 4: Analisis Kondisi Khusus")
st.caption("Peserta didik dengan alergi, fobia, dan intoleransi makanan — kebutuhan menu khusus dalam program MBG.")

df, tipe_sekolah = render_global_filters()
satpen_col = get_satpen_column(tipe_sekolah)

total_alergi     = int(df["jumlah_alergi"].sum())
total_fobia      = int(df["jumlah_fobia"].sum())
total_intoleransi= int(df["jumlah_intoleransi"].sum())
total_kk         = int(df["jumlah_kondisi_khusus"].sum())
total_penerima   = int(df["jumlah_penerima_manfaat"].sum())

st.divider()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Alergi",          f"{total_alergi:,}")
c2.metric("Fobia",           f"{total_fobia:,}")
c3.metric("Intoleransi",     f"{total_intoleransi:,}")
c4.metric("Total Kondisi Khusus", f"{total_kk:,}", f"{total_kk/total_penerima*100:.2f}% dari penerima")

# INSIGHT & HIPOTESIS - Overview Kondisi Khusus
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight"):
        kondisi_terbanyak = max([("Alergi", total_alergi), ("Fobia", total_fobia), ("Intoleransi", total_intoleransi)], key=lambda x: x[1])
        st.markdown(f"""
        **Gambaran Umum Kondisi Khusus:**
        - Total kondisi khusus: **{total_kk:,}** ({total_kk/total_penerima*100:.2f}% dari penerima)
        - Jenis terbanyak: **{kondisi_terbanyak[0]}** ({kondisi_terbanyak[1]:,} kasus)
        - {'Alergi mendominasi karena merupakan kondisi yang paling terdeteksi dan dilaporkan di sekolah' if kondisi_terbanyak[0] == 'Alergi' else 'Pola ini menunjukkan kebutuhan penanganan yang berbeda-beda'}
        """)
with why_col:
    with st.popover("Why? (Hipotesis)"):
        st.markdown(f"""
        **Mengapa distribusi kondisi khusus seperti ini?**
        - **Deteksi Medis:** Alergi lebih mudah terdeteksi melalui screening kesehatan rutin di sekolah dibandingkan fobia.
        - **Pelaporan:** {'Kasus alergi makanan paling sering dilaporkan orang tua saat pendaftaran sekolah' if kondisi_terbanyak[0] == 'Alergi' else 'Fobia dan intoleransi memerlukan observasi lebih lanjut'}
        - **Kesadaran:** Masyarakat lebih aware terhadap alergi makanan dibandingkan kondisi psikologis seperti fobia.
        """)

# --- Proporsi & per jenjang ---
st.divider()
b1, b2 = st.columns(2)

with b1:
    fig_pie = px.pie(
        names=["Alergi", "Fobia", "Intoleransi"],
        values=[total_alergi, total_fobia, total_intoleransi],
        title="Proporsi Jenis Kondisi Khusus",
        hole=0.5,
        color_discrete_sequence=["#1E6FD9", "#64A8F5", "#A8C8F8"],
    )
    fig_pie.update_traces(textposition="outside", textinfo="percent+label")
    fig_pie.update_layout(showlegend=False)
    st.plotly_chart(fig_pie, use_container_width=True)

with b2:
    by_jenjang_kk = (
        df.groupby("jenjang", as_index=False)
        .agg(
            jumlah_alergi=("jumlah_alergi", "sum"),
            jumlah_fobia=("jumlah_fobia", "sum"),
            jumlah_intoleransi=("jumlah_intoleransi", "sum"),
        )
        .sort_values("jumlah_alergi", ascending=False)
    )
    fig_jenjang_kk = px.bar(
        by_jenjang_kk, x="jenjang",
        y=["jumlah_alergi", "jumlah_fobia", "jumlah_intoleransi"],
        barmode="stack",
        title="Kondisi Khusus per Jenjang Pendidikan",
        labels={"value": "Jumlah", "jenjang": "Jenjang", "variable": "Jenis Kondisi"},
        color_discrete_sequence=["#1E6FD9", "#64A8F5", "#A8C8F8"],
        height=420,
    )
    st.plotly_chart(fig_jenjang_kk, use_container_width=True)

# INSIGHT & HIPOTESIS - Kondisi Khusus per Jenjang
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight"):
        by_jenjang_kk["total"] = by_jenjang_kk["jumlah_alergi"] + by_jenjang_kk["jumlah_fobia"] + by_jenjang_kk["jumlah_intoleransi"]
        jenjang_tertinggi = by_jenjang_kk.loc[by_jenjang_kk["total"].idxmax(), "jenjang"]
        st.markdown(f"""
        **Distribusi per Jenjang:**
        - Jenjang dengan kondisi khusus tertinggi: **{jenjang_tertinggi}**
        - {'Semakin tinggi jenjang, semakin banyak kondisi khusus yang terdeteksi karena screening berkelanjutan' if jenjang_tertinggi in ['SMA', 'SMK'] else 'Deteksi dini di jenjang dasar sangat penting untuk intervensi awal'}
        """)
with why_col:
    with st.popover("Why? (Hipotesis)"):
        st.markdown(f"""
        **Mengapa jenjang {jenjang_tertinggi} memiliki kondisi khusus tertinggi?**
        - **Konsentrasi Siswa:** Jenjang ini memiliki populasi siswa yang besar, sehingga secara absolut jumlah kasusnya lebih tinggi.
        - **Screening Berkelanjutan:** {'Siswa di jenjang SMA/SMK telah melalui lebih banyak screening kesehatan dari jenjang sebelumnya' if jenjang_tertinggi in ['SMA', 'SMK'] else 'Deteksi kondisi khusus lebih masif dilakukan di jenjang ini'}
        - **Data Historis:** Riwayat kesehatan siswa terkumpul dari jenjang sebelumnya.
        """)

# --- Ranking wilayah ---
st.divider()
st.subheader("Wilayah dengan Kondisi Khusus Tertinggi")

level_kk = st.radio("Level analisis", ["Provinsi", "Kabupaten/Kota"], horizontal=True, key="level_kk")
group_col = "provinsi_clean" if level_kk == "Provinsi" else "kabkota_clean"

by_wilayah_kk = df.groupby(group_col, as_index=False).agg(
    jumlah_kondisi_khusus=("jumlah_kondisi_khusus", "sum"),
    jumlah_penerima_manfaat=("jumlah_penerima_manfaat", "sum"),
    jumlah_alergi=("jumlah_alergi", "sum"),
    jumlah_fobia=("jumlah_fobia", "sum"),
    jumlah_intoleransi=("jumlah_intoleransi", "sum"),
)
by_wilayah_kk["pct_kondisi_khusus"] = (
    by_wilayah_kk["jumlah_kondisi_khusus"] / by_wilayah_kk["jumlah_penerima_manfaat"] * 100
)

col_kk1, col_kk2, col_kk3 = st.columns(3)
top_n_kk    = col_kk1.slider("Jumlah ditampilkan", 5, min(30, by_wilayah_kk.shape[0]),
                              min(10, by_wilayah_kk.shape[0]), key="topn_kk")
metric_kk   = col_kk2.radio("Urutkan berdasarkan", ["Jumlah absolut", "Persentase"], horizontal=True, key="metric_kk")
sort_col    = "jumlah_kondisi_khusus" if metric_kk == "Jumlah absolut" else "pct_kondisi_khusus"
x_label     = "Jumlah Kondisi Khusus"  if metric_kk == "Jumlah absolut" else "% dari Penerima Manfaat"

top_kk   = by_wilayah_kk.sort_values(sort_col, ascending=False).head(top_n_kk)
fig_top_kk = px.bar(
    top_kk, x=sort_col, y=group_col, orientation="h",
    color=sort_col, color_continuous_scale="Blues",
    labels={sort_col: x_label, group_col: level_kk},
    height=max(350, top_n_kk * 28),
)
fig_top_kk.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
st.plotly_chart(fig_top_kk, use_container_width=True)

top1 = top_kk.iloc[0]

# INSIGHT & HIPOTESIS - Ranking Wilayah
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight"):
        st.markdown(f"""
        **Konsentrasi Wilayah:**
        - {level_kk} dengan kondisi khusus tertinggi: **{top1[group_col]}**
        - {int(top1['jumlah_kondisi_khusus']):,} kasus ({top1['pct_kondisi_khusus']:.2f}% dari penerima)
        - {'Wilayah ini membutuhkan perhatian khusus dalam penyediaan menu alternatif MBG' if top1['pct_kondisi_khusus'] > 5 else 'Meskipun absolut tinggi, persentasenya masih dalam batas wajar'}
        """)
with why_col:
    with st.popover("Why? (Hipotesis)"):
        st.markdown(f"""
        **Mengapa {top1[group_col]} memiliki kasus tertinggi?**
        - **Populasi Besar:** {'Wilayah ini memiliki jumlah sekolah dan siswa yang sangat banyak' if level_kk == 'Provinsi' else 'Daerah ini merupakan pusat pendidikan dengan banyak sekolah'}
        - **Sistem Pelaporan:** Infrastruktur kesehatan sekolah yang lebih baik menghasilkan pelaporan yang lebih lengkap.
        - **Keragaman Menu:** Di wilayah dengan beragam makanan tradisional, risiko alergi dan intoleransi mungkin lebih tinggi.
        """)

# --- Negeri vs Swasta ---
st.divider()
st.subheader("Kapasitas Layanan: Negeri vs Swasta per Jenjang")
st.caption(
    "Catatan: dataset hanya mencatat jumlah sekolah negeri/swasta per kecamatan, bukan jumlah peserta "
    "kondisi khusus per jenis sekolah. Analisis ini menunjukkan kapasitas penyedia layanan, "
    "bukan distribusi penerima per jenis sekolah."
)

by_ns = df.groupby("jenjang", as_index=False).agg(
    jumlah_satpen_negeri=("jumlah_satpen_negeri", "sum"),
    jumlah_satpen_swasta=("jumlah_satpen_swasta", "sum"),
)
total_n = by_ns["jumlah_satpen_negeri"].sum()
total_s = by_ns["jumlah_satpen_swasta"].sum()

fig_ns = px.bar(
    by_ns, x="jenjang", y=["jumlah_satpen_negeri", "jumlah_satpen_swasta"],
    barmode="group",
    labels={"value": "Jumlah Satuan Pendidikan", "jenjang": "Jenjang", "variable": "Jenis Sekolah"},
    color_discrete_sequence=["#1E6FD9", "#A8C8F8"],
    height=420,
)
st.plotly_chart(fig_ns, use_container_width=True)

# INSIGHT & HIPOTESIS - Negeri vs Swasta
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight"):
        st.markdown(f"""
        **Kapasitas Layanan:**
        - Komposisi: **{total_n/(total_n+total_s)*100:.1f}% negeri** vs **{total_s/(total_n+total_s)*100:.1f}% swasta**
        - {'Sekolah negeri mendominasi kapasitas layanan secara struktural' if total_n > total_s else 'Sekolah swasta memiliki peran signifikan'}
        """)
with why_col:
    with st.popover("Why? (Hipotesis)"):
        st.markdown(f"""
        **Mengapa komposisi negeri vs swasta seperti ini?**
        - **Kebijakan Pemerintah:** {'Pemerintah memiliki lebih banyak sekolah negeri untuk menjamin akses pendidikan dasar' if total_n > total_s else 'Di beberapa daerah, swasta mengisi kekosongan layanan pendidikan'}
        - **Distribusi Anggaran:** Sekolah negeri menerima alokasi anggaran lebih besar untuk menangani kondisi khusus.
        - **Kapasitas SDM:** {'Guru dan tenaga kesehatan di sekolah negeri lebih terstandarisasi' if total_n > total_s else 'Sekolah swasta memiliki fleksibilitas dalam penanganan kasus khusus'}
        """)

# --- Anomali ---
st.divider()
st.subheader("Deteksi Anomali Persentase Kondisi Khusus")

df["pct_kondisi_khusus_row"] = np.where(
    df["jumlah_penerima_manfaat"] > 0,
    df["jumlah_kondisi_khusus"] / df["jumlah_penerima_manfaat"] * 100, 0
)
outlier_mask = detect_outliers_iqr(df["pct_kondisi_khusus_row"])
n_outlier    = int(outlier_mask.sum())

# INSIGHT & HIPOTESIS - Anomali
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight"):
        st.markdown(f"""
        **Anomali Data:**
        - Ditemukan **{n_outlier}** kecamatan-jenjang dengan persentase kondisi khusus ekstrem
        - {'Data ini perlu diverifikasi karena bisa jadi kesalahan input atau karakteristik unik' if n_outlier > 0 else 'Tidak ditemukan anomali signifikan, data relatif konsisten'}
        """)
with why_col:
    with st.popover("Why? (Hipotesis)"):
        st.markdown(f"""
        **Mengapa anomali ini terjadi?**
        - **Kesalahan Input:** {'Petugas mungkin salah menginput data kondisi khusus' if n_outlier > 0 else 'Data terverifikasi dengan baik'}
        - **Kasus Khusus:** Beberapa kecamatan mungkin memiliki karakteristik unik (misalnya panti asuhan atau sekolah inklusi).
        - **Pelaporan Tidak Konsisten:** {'Standar pelaporan berbeda antar daerah menyebabkan variasi ekstrim' if n_outlier > 0 else 'Standar pelaporan relatif konsisten'}
        - **Perlu Investigasi:** {'Anomali ini menjadi prioritas untuk verifikasi data lapangan' if n_outlier > 0 else 'Sistem data sudah baik'}
        """)

st.caption(
    f"Ditemukan **{n_outlier} baris** kecamatan-jenjang dengan persentase kondisi khusus jauh di luar pola umum "
    f"(deteksi metode IQR). Ini bisa jadi kesalahan input atau karakteristik wilayah tertentu."
)

if n_outlier > 0:
    outlier_df = (
        df[outlier_mask][["provinsi_clean", "kabkota_clean", "kecamatan_clean", "jenjang",
                           "jumlah_kondisi_khusus", "jumlah_penerima_manfaat", "pct_kondisi_khusus_row"]]
        .sort_values("pct_kondisi_khusus_row", ascending=False)
        .head(15)
    )
    st.dataframe(
        outlier_df.rename(columns={
            "provinsi_clean":        "Provinsi",
            "kabkota_clean":         "Kab/Kota",
            "kecamatan_clean":       "Kecamatan",
            "jenjang":               "Jenjang",
            "jumlah_kondisi_khusus": "Kondisi Khusus",
            "jumlah_penerima_manfaat":"Penerima",
            "pct_kondisi_khusus_row":"%",
        }).round(2),
        hide_index=True, 
        use_container_width=True,
    )