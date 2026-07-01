"""Fitur 3 — Analisis Demografi: komposisi gender & jenjang pendidikan penerima manfaat."""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.filters import render_global_filters, get_satpen_column

st.set_page_config(page_title="Fitur 3: Analisis Demografi", layout="wide")
st.title("Fitur 3: Analisis Demografi")
st.caption("Komposisi gender dan jenjang pendidikan peserta didik penerima manfaat.")

df, tipe_sekolah = render_global_filters()
satpen_col = get_satpen_column(tipe_sekolah)

# --- KPI gender ---
st.divider()
st.subheader("Komposisi Gender Keseluruhan")

total_laki      = int(df["jumlah_laki"].sum())
total_perempuan = int(df["jumlah_perempuan"].sum())
rasio_LP        = total_laki / total_perempuan if total_perempuan > 0 else np.nan

c1, c2, c3 = st.columns(3)
c1.metric("Laki-laki",  f"{total_laki:,}",      f"{total_laki/(total_laki+total_perempuan)*100:.1f}%")
c2.metric("Perempuan",  f"{total_perempuan:,}",  f"{total_perempuan/(total_laki+total_perempuan)*100:.1f}%")
c3.metric("Rasio L/P",  f"{rasio_LP:.3f}",       help="1.0 = seimbang sempurna")

# INSIGHT & HIPOTESIS (Why) - Komposisi Gender
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight"):
        st.markdown(f"""
        **Komposisi Gender Nasional:**
        - Rasio L/P = **{rasio_LP:.3f}** 
        - {'Komposisi gender relatif seimbang (mendekati 1.0)' if 0.9 <= rasio_LP <= 1.1 else 'Terlihat ketimpangan gender yang cukup signifikan'}
        """)
with why_col:
    with st.popover("Why? (Hipotesis)"):
        st.markdown(f"""
        **Mengapa rasio L/P seperti ini?**
        - **Partisipasi Sekolah:** Secara nasional, angka partisipasi sekolah dasar dan menengah relatif seimbang antara laki-laki dan perempuan.
        - **Data Baseline:** Data MBG mengikuti data peserta didik riil dari Dapodik, sehingga mencerminkan demografi pendidikan Indonesia secara umum.
        - **Validasi Data:** {'Ketimpangan kecil ini bisa jadi karena perbedaan validasi data antar daerah' if 0.9 <= rasio_LP <= 1.1 else 'Ketimpangan signifikan mungkin menunjukkan adanya bias akses pendidikan gender di beberapa wilayah, perlu investigasi lebih lanjut.'}
        """)

# --- Distribusi per jenjang ---
st.divider()
st.subheader("Distribusi per Jenjang Pendidikan")

by_jenjang = (
    df.groupby("jenjang", as_index=False).agg(
        jumlah_laki=("jumlah_laki", "sum"),
        jumlah_perempuan=("jumlah_perempuan", "sum"),
        jumlah_penerima_manfaat=("jumlah_penerima_manfaat", "sum"),
        jumlah_kondisi_khusus=("jumlah_kondisi_khusus", "sum"),
    )
    .sort_values("jumlah_penerima_manfaat", ascending=False)
)
by_jenjang["rasio_LP"]           = by_jenjang["jumlah_laki"] / by_jenjang["jumlah_perempuan"].replace(0, np.nan)
by_jenjang["pct_kondisi_khusus"] = by_jenjang["jumlah_kondisi_khusus"] / by_jenjang["jumlah_penerima_manfaat"] * 100

j1, j2 = st.columns(2)
with j1:
    fig_jenjang = px.bar(
        by_jenjang, x="jenjang", y=["jumlah_laki", "jumlah_perempuan"],
        barmode="group",
        labels={"value": "Jumlah Peserta Didik", "jenjang": "Jenjang", "variable": "Gender"},
        color_discrete_sequence=["#1E6FD9", "#64A8F5"],
        height=420,
        title="Laki-laki vs Perempuan per Jenjang",
    )
    st.plotly_chart(fig_jenjang, use_container_width=True)

with j2:
    fig_rasio_jenjang = px.bar(
        by_jenjang, x="jenjang", y="rasio_LP",
        color="rasio_LP", color_continuous_scale="RdBu_r",
        labels={"rasio_LP": "Rasio L/P", "jenjang": "Jenjang"},
        height=420,
        title="Rasio Gender (L/P) per Jenjang",
    )
    fig_rasio_jenjang.add_hline(y=1.0, line_dash="dash", line_color="#555555",
                                 annotation_text="Seimbang (1.0)", annotation_position="top right")
    st.plotly_chart(fig_rasio_jenjang, use_container_width=True)

jenjang_timpang = by_jenjang.iloc[(by_jenjang["rasio_LP"] - 1).abs().argsort()[::-1]].iloc[0]

# INSIGHT & HIPOTESIS - Distribusi per Jenjang
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight"):
        st.markdown(f"""
        **Pola Gender per Jenjang:**
        - Jenjang dengan rasio gender paling timpang: **{jenjang_timpang['jenjang']}** (rasio L/P = {jenjang_timpang['rasio_LP']:.2f})
        - {'SMK seringkali didominasi oleh satu gender tergantung program kejuruan (teknik vs tata boga)' if 'SMK' in jenjang_timpang['jenjang'] else 'Faktor kurikulum dan minat siswa mempengaruhi komposisi gender'}
        """)
with why_col:
    with st.popover("Why? (Hipotesis)"):
        st.markdown(f"""
        **Mengapa terjadi perbedaan antar jenjang?**
        - **Karakteristik Jenjang:** Pada SMK, program kejuruan tertentu seperti Teknik Mesin cenderung didominasi laki-laki, sementara Tata Boga dan Tata Busana didominasi perempuan.
        - **Sosiokultural:** Di beberapa daerah, anak perempuan lebih banyak putus sekolah di jenjang menengah atas karena faktor pernikahan dini atau peran gender tradisional.
        - **Ketersediaan Sekolah:** {'SMK memiliki variasi program yang berbeda, mempengaruhi komposisi gender di setiap sekolah' if 'SMK' in jenjang_timpang['jenjang'] else 'Perbedaan akses sekolah di setiap jenjang juga mempengaruhi komposisi gender'}
        """)

# --- Tabel lengkap ---
st.divider()
st.subheader("Tabel Ringkasan per Jenjang")

st.dataframe(
    by_jenjang.rename(columns={
        "jenjang":                  "Jenjang",
        "jumlah_laki":              "Laki-laki",
        "jumlah_perempuan":         "Perempuan",
        "jumlah_penerima_manfaat":  "Total Penerima",
        "jumlah_kondisi_khusus":    "Kondisi Khusus",
        "rasio_LP":                 "Rasio L/P",
        "pct_kondisi_khusus":       "% Kondisi Khusus",
    }).round(2),
    hide_index=True, 
    use_container_width=True,
)

jenjang_inklusif = by_jenjang.nlargest(1, "pct_kondisi_khusus").iloc[0]

# INSIGHT & HIPOTESIS - Kondisi Khusus
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight"):
        st.markdown(f"""
        **Kebutuhan Layanan Inklusif:**
        - Jenjang dengan % kondisi khusus tertinggi: **{jenjang_inklusif['jenjang']}** ({jenjang_inklusif['pct_kondisi_khusus']:.2f}%)
        - {'Jenjang PAUD/SD cenderung memiliki deteksi dini yang lebih baik terhadap kondisi khusus' if 'PAUD' in jenjang_inklusif['jenjang'] or 'SD' in jenjang_inklusif['jenjang'] else 'Kebutuhan inklusif bervariasi antar jenjang pendidikan'}
        """)
with why_col:
    with st.popover("Why? (Hipotesis)"):
        st.markdown(f"""
        **Mengapa jenjang ini memiliki kebutuhan inklusif tertinggi?**
        - **Deteksi Dini:** {'Pada jenjang PAUD/SD, screening kesehatan dan perkembangan lebih intensif dilakukan' if 'PAUD' in jenjang_inklusif['jenjang'] or 'SD' in jenjang_inklusif['jenjang'] else 'Deteksi kondisi khusus lebih optimal di jenjang ini'}
        - **Konsentrasi Siswa:** Semakin tinggi jenjang, semakin banyak siswa yang terkonsentrasi, sehingga jumlah kasus terlihat lebih besar.
        - **Pelaporan Data:** Sekolah dengan sistem pelaporan yang baik memiliki data kondisi khusus yang lebih lengkap.
        """)

# --- Rasio gender per provinsi ---
st.divider()
st.subheader("Rasio Gender per Provinsi")

by_prov_gender = (
    df.groupby("provinsi_clean", as_index=False)
    .agg(jumlah_laki=("jumlah_laki", "sum"), jumlah_perempuan=("jumlah_perempuan", "sum"))
)
by_prov_gender["rasio_LP"] = (
    by_prov_gender["jumlah_laki"] / by_prov_gender["jumlah_perempuan"].replace(0, np.nan)
)
by_prov_gender = by_prov_gender.dropna(subset=["rasio_LP"]).sort_values("rasio_LP", ascending=False)

fig_prov_gender = px.bar(
    by_prov_gender.sort_values("rasio_LP"),
    x="rasio_LP", y="provinsi_clean", orientation="h",
    color="rasio_LP", color_continuous_scale="RdBu_r",
    labels={"rasio_LP": "Rasio L/P", "provinsi_clean": "Provinsi"},
    height=max(420, len(by_prov_gender) * 22),
    title="Rasio Gender (L/P) seluruh Provinsi — garis tengah = seimbang",
)
fig_prov_gender.add_vline(x=1.0, line_dash="dash", line_color="#555555")
fig_prov_gender.update_layout(coloraxis_showscale=False)
st.plotly_chart(fig_prov_gender, use_container_width=True)

# INSIGHT & HIPOTESIS - Rasio Gender per Provinsi
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight"):
        prov_dominan_laki = by_prov_gender.nlargest(3, "rasio_LP")
        prov_dominan_perempuan = by_prov_gender.nsmallest(3, "rasio_LP")
        st.markdown(f"""
        **Variasi Gender per Provinsi:**
        - Dominan laki-laki: {', '.join(prov_dominan_laki['provinsi_clean'].head(3).tolist())}
        - Dominan perempuan: {', '.join(prov_dominan_perempuan['provinsi_clean'].head(3).tolist())}
        - Warna merah = dominan laki-laki, biru = dominan perempuan
        """)
with why_col:
    with st.popover("Why? (Hipotesis)"):
        st.markdown("""
        **Mengapa terjadi variasi antar provinsi?**
        - **Kebijakan Pendidikan Lokal:** Setiap provinsi memiliki kebijakan dan program pendidikan yang berbeda, mempengaruhi partisipasi gender.
        - **Budaya Lokal:** Norma sosial dan budaya di beberapa daerah masih membatasi akses pendidikan untuk perempuan.
        - **Ketersediaan Sekolah:** Provinsi dengan lebih banyak sekolah kejuruan teknis cenderung memiliki rasio L/P lebih tinggi.
        - **Migrasi:** Wilayah dengan tingkat urbanisasi tinggi mungkin memiliki pola migrasi yang berbeda antar gender.
        """)

st.divider()
st.caption("Warna merah = dominan laki-laki, biru = dominan perempuan. Garis putus-putus = rasio 1.0 (seimbang).")