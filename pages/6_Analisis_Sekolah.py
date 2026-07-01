"""Fitur 6 — Analisis Sekolah: kapasitas & komposisi negeri/swasta satuan pendidikan."""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.filters import render_global_filters, get_satpen_column

st.set_page_config(page_title="Fitur 6: Analisis Sekolah", page_icon="🏫", layout="wide")
st.title("Fitur 6: Analisis Sekolah")
st.caption("Fokus: kapasitas, komposisi negeri/swasta, dan distribusi satuan pendidikan")

df, tipe_sekolah = render_global_filters()
satpen_col = get_satpen_column(tipe_sekolah)

st.markdown(
    """
    > **Yang perlu disampaikan:** "Berapa banyak sekolah yang terlibat dalam program ini, dan bagaimana
    > komposisinya antara negeri dan swasta? Ini menentukan strategi distribusi logistik program ke depan."
    """
)

total_satpen = int(df["jumlah_satuan_pendidikan"].sum())
total_negeri = int(df["jumlah_satpen_negeri"].sum())
total_swasta = int(df["jumlah_satpen_swasta"].sum())

st.markdown("---")
c1, c2, c3 = st.columns(3)
c1.metric("Total Satuan Pendidikan", f"{total_satpen:,}")
c2.metric("Negeri", f"{total_negeri:,}", f"{total_negeri/total_satpen*100:.1f}%")
c3.metric("Swasta", f"{total_swasta:,}", f"{total_swasta/total_satpen*100:.1f}%")

# INSIGHT & HIPOTESIS - Overview
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight"):
        st.markdown(f"""
        **Komposisi Sekolah Nasional:**
        - Total sekolah: **{total_satpen:,}** satuan pendidikan
        - Komposisi: **{total_negeri/total_satpen*100:.1f}% negeri** vs **{total_swasta/total_satpen*100:.1f}% swasta**
        - {'Sekolah negeri mendominasi kapasitas layanan MBG' if total_negeri > total_swasta else 'Peran swasta cukup signifikan'}
        - {'Koordinasi dengan Kementerian Agama dan Pendidikan penting untuk sekolah negeri' if total_negeri > total_swasta else 'Kerjasama dengan yayasan swasta perlu diperkuat'}
        """)
with why_col:
    with st.popover("Why? (Hipotesis)"):
        st.markdown(f"""
        **Mengapa komposisi negeri vs swasta seperti ini?**
        - **Kebijakan Pendidikan:** {'Pemerintah memiliki kewajiban menyediakan akses pendidikan dasar melalui sekolah negeri' if total_negeri > total_swasta else 'Swasta berperan mengisi gap layanan pendidikan'}
        - **Distribusi Anggaran:** {'Sekolah negeri menerima alokasi APBN/APBD untuk operasional' if total_negeri > total_swasta else 'Sekolah swasta lebih mandiri secara finansial'}
        - **Jangkauan:** {'Negeri tersebar lebih luas hingga ke 3T' if total_negeri > total_swasta else 'Swasta terkonsentrasi di perkotaan'}
        - **Data Baseline:** Data Dapodik menunjukkan dominasi sekolah negeri secara nasional.
        """)

st.markdown("---")
st.markdown("### 🎓 Komposisi Negeri/Swasta per Jenjang Pendidikan")
by_jenjang = df.groupby("jenjang", as_index=False).agg(
    jumlah_satpen_negeri=("jumlah_satpen_negeri", "sum"), jumlah_satpen_swasta=("jumlah_satpen_swasta", "sum"),
    jumlah_penerima_manfaat=("jumlah_penerima_manfaat", "sum"),
).sort_values("jumlah_penerima_manfaat", ascending=False)
by_jenjang["total_satpen"] = by_jenjang["jumlah_satpen_negeri"] + by_jenjang["jumlah_satpen_swasta"]
by_jenjang["pct_swasta"] = by_jenjang["jumlah_satpen_swasta"] / by_jenjang["total_satpen"] * 100

fig_jenjang_ns = px.bar(
    by_jenjang, x="jenjang", y=["jumlah_satpen_negeri", "jumlah_satpen_swasta"], barmode="stack",
    labels={"value": "Jumlah Satuan Pendidikan", "jenjang": "Jenjang", "variable": "Jenis Sekolah"},
    color_discrete_sequence=["#55A868", "#C44E52"], height=420,
)
st.plotly_chart(fig_jenjang_ns, use_container_width=True)

jenjang_swasta_tinggi = by_jenjang.nlargest(1, "pct_swasta").iloc[0]

# INSIGHT & HIPOTESIS - Komposisi per Jenjang
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight"):
        st.markdown(f"""
        **Komposisi per Jenjang:**
        - Jenjang dengan swasta tertinggi: **{jenjang_swasta_tinggi['jenjang']}** ({jenjang_swasta_tinggi['pct_swasta']:.1f}% swasta)
        - {'PAUD/TK didominasi swasta karena banyak didirikan oleh yayasan/komunitas' if 'PAUD' in jenjang_swasta_tinggi['jenjang'] or 'TK' in jenjang_swasta_tinggi['jenjang'] else 'SMK swasta dominan di bidang kejuruan tertentu'}
        - {'SMA/MA menunjukkan pola seimbang antara negeri dan swasta' if 'SMA' in jenjang_swasta_tinggi['jenjang'] or 'MA' in jenjang_swasta_tinggi['jenjang'] else 'Distribusi bervariasi antar jenjang'}
        """)
with why_col:
    with st.popover("Why? (Hipotesis)"):
        st.markdown(f"""
        **Mengapa {jenjang_swasta_tinggi['jenjang']} memiliki swasta tertinggi?**
        - **Karakteristik Jenjang:** {'Pendidikan anak usia dini banyak dikelola swasta karena fleksibilitas kurikulum' if 'PAUD' in jenjang_swasta_tinggi['jenjang'] or 'TK' in jenjang_swasta_tinggi['jenjang'] else 'Program kejuruan spesifik lebih banyak di swasta'}
        - **Minat Masyarakat:** {'Orang tua lebih memilih PAUD swasta karena kualitas dan kedekatan' if 'PAUD' in jenjang_swasta_tinggi['jenjang'] or 'TK' in jenjang_swasta_tinggi['jenjang'] else 'Swasta menawarkan spesialisasi yang lebih beragam'}
        - **Investasi Swasta:** {'Yayasan pendidikan banyak berkonsentrasi di jenjang ini' if 'PAUD' in jenjang_swasta_tinggi['jenjang'] or 'TK' in jenjang_swasta_tinggi['jenjang'] else 'Dunia usaha banyak membuka SMK swasta'}
        """)

st.caption(
    f"**Insight:** Jenjang dengan proporsi sekolah swasta tertinggi adalah **{jenjang_swasta_tinggi['jenjang']}** "
    f"({jenjang_swasta_tinggi['pct_swasta']:.1f}% swasta) — relevan untuk strategi koordinasi distribusi logistik "
    f"karena sekolah swasta umumnya punya jalur administrasi terpisah dari sekolah negeri."
)

st.markdown("---")
st.markdown("### Distribusi Geografis Kapasitas Sekolah")
level_sekolah = st.radio("Level analisis", ["Provinsi", "Kabupaten/Kota"], horizontal=True, key="level_sekolah")
group_col = "provinsi_clean" if level_sekolah == "Provinsi" else "kabkota_clean"

agg_sekolah = df.groupby(group_col, as_index=False).agg(
    jumlah_satpen_negeri=("jumlah_satpen_negeri", "sum"), jumlah_satpen_swasta=("jumlah_satpen_swasta", "sum"),
    jumlah_penerima_manfaat=("jumlah_penerima_manfaat", "sum"),
)
agg_sekolah["total_satpen"] = agg_sekolah["jumlah_satpen_negeri"] + agg_sekolah["jumlah_satpen_swasta"]
agg_sekolah["pct_swasta"] = agg_sekolah["jumlah_satpen_swasta"] / agg_sekolah["total_satpen"].replace(0, np.nan) * 100
agg_sekolah["rasio_penerima_per_satpen"] = agg_sekolah["jumlah_penerima_manfaat"] / agg_sekolah["total_satpen"].replace(0, np.nan)

top_n_sekolah = st.slider("Tampilkan Top-N", 5, min(30, agg_sekolah.shape[0]), min(15, agg_sekolah.shape[0]), key="topn_sekolah")
top_sekolah = agg_sekolah.sort_values("total_satpen", ascending=False).head(top_n_sekolah)
fig_top_sekolah = px.bar(
    top_sekolah, x="total_satpen", y=group_col, orientation="h", color="pct_swasta", color_continuous_scale="RdYlGn_r",
    labels={"total_satpen": "Total Satuan Pendidikan", group_col: level_sekolah, "pct_swasta": "% Swasta"},
    height=max(350, top_n_sekolah * 28),
)
fig_top_sekolah.update_layout(yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig_top_sekolah, use_container_width=True)

# INSIGHT & HIPOTESIS - Distribusi Geografis
if len(top_sekolah) > 0:
    top_wilayah = top_sekolah.iloc[0]
    insight_col, why_col = st.columns(2)
    with insight_col:
        with st.popover("Insight"):
            st.markdown(f"""
            **Konsentrasi Sekolah:**
            - {level_sekolah} dengan sekolah terbanyak: **{top_wilayah[group_col]}**
            - Total: **{int(top_wilayah['total_satpen']):,}** sekolah
            - {'Wilayah dengan populasi padat membutuhkan banyak sekolah' if top_wilayah['total_satpen'] > 1000 else 'Distribusi sekolah relatif merata'}
            - Warna: {'Hijau = dominan negeri' if top_wilayah['pct_swasta'] < 40 else 'Merah = dominan swasta'}
            """)
    with why_col:
        with st.popover("Why? (Hipotesis)"):
            st.markdown(f"""
            **Mengapa {top_wilayah[group_col]} memiliki banyak sekolah?**
            - **Kepadatan Penduduk:** {'Wilayah ini memiliki populasi usia sekolah yang sangat besar' if top_wilayah['total_satpen'] > 1000 else 'Populasi siswa tersebar merata'}
            - **Pusat Pendidikan:** {'Merupakan pusat pendidikan di wilayahnya dengan banyak perguruan tinggi yang menjadi feeder' if top_wilayah['total_satpen'] > 1000 else 'Merupakan daerah dengan akses pendidikan yang baik'}
            - **Investasi Pendidikan:** {'Pemerintah daerah mengalokasikan anggaran pendidikan besar' if top_wilayah['total_satpen'] > 1000 else 'Investasi pendidikan masih perlu ditingkatkan'}
            """)

st.caption("Warna menunjukkan persentase sekolah swasta (hijau = mayoritas negeri, merah = mayoritas swasta).")

st.markdown("---")
st.markdown("### Rasio Beban: Penerima Manfaat per Satuan Pendidikan")
st.caption(f"Memakai kolom: **{tipe_sekolah}** sesuai filter sidebar.")
fig_box_rasio = px.box(
    df.assign(rasio=df["jumlah_penerima_manfaat"] / df[satpen_col].replace(0, np.nan)),
    x="jenjang", y="rasio", points="outliers",
    labels={"rasio": "Rasio Penerima/Satpen", "jenjang": "Jenjang"}, height=450,
)
st.plotly_chart(fig_box_rasio, use_container_width=True)

# INSIGHT & HIPOTESIS - Rasio Beban
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight"):
        rasio_median = df["jumlah_penerima_manfaat"] / df[satpen_col].replace(0, np.nan)
        median_val = rasio_median.median()
        jenjang_outlier = df.groupby("jenjang").apply(
            lambda x: (x["jumlah_penerima_manfaat"] / x[satpen_col].replace(0, np.nan)).max()
        ).idxmax()
        st.markdown(f"""
        **Beban Sekolah per Jenjang:**
        - Median nasional: **{median_val:.0f}** siswa per satpen
        - Jenjang dengan beban tertinggi: **{jenjang_outlier}**
        - {'Box plot lebar = variasi beban antar sekolah tinggi' if fig_box_rasio else 'Distribusi relatif konsisten'}
        - Outlier terbanyak: **{jenjang_outlier}** → perlu standarisasi kapasitas
        """)
with why_col:
    with st.popover("Why? (Hipotesis)"):
        st.markdown(f"""
        **Mengapa beban sekolah bervariasi?**
        - **Urbanisasi:** {'Sekolah di perkotaan kelebihan siswa, 3T kekurangan' if median_val > 50 else 'Distribusi siswa cukup merata'}
        - **Kebijakan Zonasi:** {'Penerapan PPDB zonasi menciptakan konsentrasi di sekolah favorit' if median_val > 50 else 'Zonasi membantu pemerataan'}
        - **Kualitas Sekolah:** {'Sekolah favorit di jenjang tertentu menerima siswa jauh di atas kapasitas' if median_val > 50 else 'Kualitas sekolah relatif merata'}
        - **Fasilitas:** {'Sekolah dengan fasilitas lengkap menarik lebih banyak siswa' if median_val > 50 else 'Fasilitas sekolah cukup terstandarisasi'}
        """)

st.caption(
    "**Insight:** Jenjang dengan rentang box plot lebih lebar/lebih banyak outlier menunjukkan variasi kapasitas sekolah "
    "yang tidak konsisten antar wilayah — perlu standarisasi alokasi guru/fasilitas."
)

st.markdown("---")
st.markdown("### Tabel Lengkap per Wilayah")
st.dataframe(
    agg_sekolah.sort_values("total_satpen", ascending=False).rename(columns={
        group_col: level_sekolah, "jumlah_satpen_negeri": "Negeri", "jumlah_satpen_swasta": "Swasta",
        "total_satpen": "Total Satpen", "pct_swasta": "% Swasta", "rasio_penerima_per_satpen": "Rasio Penerima/Satpen",
        "jumlah_penerima_manfaat": "Total Penerima",
    }).round(2), hide_index=True, use_container_width=True, height=350,
)

# INSIGHT & HIPOTESIS - Tabel Lengkap
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight"):
        wilayah_tertinggi = agg_sekolah.nlargest(1, "rasio_penerima_per_satpen")
        if len(wilayah_tertinggi) > 0:
            st.markdown(f"""
            **Ringkasan Kapasitas:**
            - {level_sekolah} dengan beban tertinggi: **{wilayah_tertinggi.iloc[0][group_col]}** 
            - Rasio: {wilayah_tertinggi.iloc[0]['rasio_penerima_per_satpen']:.1f} siswa per sekolah
            - {'Prioritas intervensi untuk penambahan kapasitas sekolah' if wilayah_tertinggi.iloc[0]['rasio_penerima_per_satpen'] > 100 else 'Beban masih dalam batas wajar'}
            """)
with why_col:
    with st.popover("Why? (Hipotesis)"):
        st.markdown("""
        **Faktor yang Mempengaruhi Kapasitas Sekolah:**
        - **Alokasi Guru:** Ketersediaan guru mempengaruhi kapasitas tampung sekolah.
        - **Infrastruktur:** Jumlah ruang kelas dan fasilitas menentukan daya tampung.
        - **Aksesibilitas:** {'Wilayah perkotaan dengan akses mudah memiliki sekolah besar' if 'DKI' in str(agg_sekolah.iloc[0][group_col]) else 'Akses transportasi mempengaruhi distribusi siswa'}
        - **Prioritas Program:** {'MBG difokuskan di sekolah-sekolah besar untuk efisiensi' if 'DKI' in str(agg_sekolah.iloc[0][group_col]) else 'Program mempertimbangkan pemerataan akses'}
        """)

st.markdown("---")
st.success("**Lanjutkan ke Fitur 7: Analisis Tren** untuk melihat pola dari sisi waktu pengumpulan data.")