"""Fitur 5 — Analisis Penerima Manfaat: kecukupan distribusi bantuan vs kebutuhan layanan."""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.filters import render_global_filters, get_satpen_column

st.set_page_config(page_title="Fitur 5: Analisis Penerima Manfaat", page_icon="🍽️", layout="wide")
st.title("Fitur 5: Analisis Penerima Manfaat")
st.caption("Fokus: kecukupan & kesebandingan distribusi penerima manfaat terhadap kebutuhan layanan")

df, tipe_sekolah = render_global_filters()
satpen_col = get_satpen_column(tipe_sekolah)

st.markdown(
    """
    > **Yang perlu disampaikan:** "Total penerima manfaat besar, tapi pertanyaan pentingnya: apakah
    > jumlah ini SEBANDING dengan kebutuhan riil di lapangan — terutama untuk peserta didik berkondisi khusus
    > yang butuh penanganan lebih?"
    """
)

total_penerima = int(df["jumlah_penerima_manfaat"].sum())
total_kk = int(df["jumlah_kondisi_khusus"].sum())
total_satpen = int(df[satpen_col].sum())

st.markdown("---")
c1, c2, c3 = st.columns(3)
c1.metric("Total Penerima Manfaat", f"{total_penerima:,}")
c2.metric("Rata-rata Penerima/Satpen", f"{total_penerima/total_satpen:.1f}" if total_satpen else "N/A")
c3.metric("% Kebutuhan Layanan Khusus", f"{total_kk/total_penerima*100:.2f}%")

# INSIGHT & HIPOTESIS - Overview
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight"):
        st.markdown(f"""
        **Gambaran Umum Distribusi:**
        - Total penerima: **{total_penerima:,}** peserta didik
        - Rata-rata penerima per satpen: **{total_penerima/total_satpen:.1f}** 
        - Proporsi kebutuhan khusus: **{total_kk/total_penerima*100:.2f}%**
        - {'Beban layanan cukup berat dengan rata-rata > 100 siswa per satuan pendidikan' if total_penerima/total_satpen > 100 else 'Beban layanan relatif terkelola dengan baik'}
        """)
with why_col:
    with st.popover("Why? (Hipotesis)"):
        st.markdown(f"""
        **Mengapa distribusi penerima seperti ini?**
        - **Kepadatan Penduduk:** Wilayah dengan populasi padat memiliki konsentrasi penerima yang tinggi.
        - **Kebijakan Alokasi:** {'Program MBG diprioritaskan pada daerah dengan akses logistik yang baik' if total_penerima/total_satpen > 100 else 'Distribusi mempertimbangkan kapasitas layanan'}
        - **Data Baseline:** Jumlah penerima mengikuti data Dapodik yang sudah ada.
        - **Fase Awal Program:** {'Distribusi masih terkonsentrasi di wilayah dengan infrastruktur matang' if total_penerima/total_satpen > 100 else 'Program sudah mulai menjangkau wilayah yang lebih luas'}
        """)

st.markdown("---")
st.markdown("### Kesebandingan: Penerima Manfaat vs Kebutuhan Layanan Khusus")
st.caption(
    "Membandingkan pertumbuhan penerima manfaat dengan pertumbuhan kebutuhan layanan khusus per wilayah. "
    "Titik yang jauh dari garis tren menunjukkan ketidaksebandingan — bisa kekurangan ATAU kelebihan alokasi relatif."
)

level_pm = st.radio("Level analisis", ["Provinsi", "Kabupaten/Kota"], horizontal=True, key="level_pm")
group_col = "provinsi_clean" if level_pm == "Provinsi" else "kabkota_clean"

agg_pm = df.groupby(group_col, as_index=False).agg(
    jumlah_penerima_manfaat=("jumlah_penerima_manfaat", "sum"),
    jumlah_kondisi_khusus=("jumlah_kondisi_khusus", "sum"),
    jumlah_satuan_pendidikan=(satpen_col, "sum"),
)
agg_pm["pct_kondisi_khusus"] = agg_pm["jumlah_kondisi_khusus"] / agg_pm["jumlah_penerima_manfaat"].replace(0, np.nan) * 100

fig_scatter = px.scatter(
    agg_pm, x="jumlah_penerima_manfaat", y="jumlah_kondisi_khusus", size="jumlah_satuan_pendidikan",
    hover_name=group_col, trendline="ols", log_x=True, log_y=True,
    labels={"jumlah_penerima_manfaat": "Total Penerima Manfaat", "jumlah_kondisi_khusus": "Jumlah Kondisi Khusus"},
    height=480,
)
st.plotly_chart(fig_scatter, use_container_width=True)

corr_pm = agg_pm[["jumlah_penerima_manfaat", "jumlah_kondisi_khusus"]].corr().iloc[0, 1]

# INSIGHT & HIPOTESIS - Kesebandingan
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight"):
        st.markdown(f"""
        **Kesebandingan Distribusi:**
        - Korelasi penerima vs kebutuhan khusus: **{corr_pm:.3f}**
        - {'Distribusi mengikuti kebutuhan dengan baik' if corr_pm > 0.6 else 'Masih ada ketidaksebandingan yang signifikan'}
        - {'Wilayah di atas garis tren = kebutuhan lebih tinggi dari alokasi (under-served)' if corr_pm < 0.8 else 'Sebagian besar wilayah telah teralokasi secara proporsional'}
        """)
with why_col:
    with st.popover("Why? (Hipotesis)"):
        st.markdown(f"""
        **Mengapa korelasinya {corr_pm:.3f}?**
        - **Alokasi Berbasis Data:** {'Pemerintah menggunakan data Dapodik yang cukup akurat untuk alokasi' if corr_pm > 0.6 else 'Masih ada gap antara data dan realita di lapangan'}
        - **Faktor Geografis:** Wilayah terpencil (3T) mungkin memiliki data yang kurang lengkap.
        - **Kapasitas Pelaporan:** {'Daerah dengan sistem pelaporan lebih baik menunjukkan korelasi lebih kuat' if corr_pm > 0.6 else 'Perlu peningkatan kualitas data di beberapa wilayah'}
        - **Prioritas Program:** {'Fokus awal pada wilayah dengan kebutuhan tinggi namun masih ada yang terlewat' if corr_pm < 0.8 else 'Distribusi sudah cukup merata'}
        """)

st.caption(
    f"**Insight — Menjawab pertanyaan: Apakah distribusi penerima manfaat sudah sebanding dengan kebutuhan?** "
    f"Korelasi antara total penerima manfaat dan jumlah kondisi khusus adalah **{corr_pm:.3f}** "
    f"({'cukup kuat — distribusi mengikuti kebutuhan secara umum' if corr_pm > 0.6 else 'masih ada variasi yang tidak terjelaskan — perlu pengecekan lebih lanjut per wilayah'})."
)

st.markdown("---")
st.markdown(f"### {level_pm} dengan Ketidaksebandingan Paling Mencolok")
st.caption("Wilayah dengan % kondisi khusus tinggi tapi kapasitas (jumlah satpen) relatif kecil — kandidat kekurangan layanan.")
agg_pm["rasio_kk_per_satpen"] = agg_pm["jumlah_kondisi_khusus"] / agg_pm["jumlah_satuan_pendidikan"].replace(0, np.nan)
risiko = agg_pm.nlargest(10, "rasio_kk_per_satpen")[[group_col, "jumlah_penerima_manfaat", "jumlah_kondisi_khusus", "jumlah_satuan_pendidikan", "rasio_kk_per_satpen"]]
st.dataframe(
    risiko.rename(columns={group_col: level_pm, "jumlah_penerima_manfaat": "Penerima", "jumlah_kondisi_khusus": "Kondisi Khusus",
                            "jumlah_satuan_pendidikan": "Jml Satpen", "rasio_kk_per_satpen": "Rasio KK/Satpen"}).round(2),
    hide_index=True, 
    use_container_width=True,
)

# INSIGHT & HIPOTESIS - Ketidaksebandingan
if len(risiko) > 0:
    top_risiko = risiko.iloc[0]
    insight_col, why_col = st.columns(2)
    with insight_col:
        with st.popover("Insight Prioritas"):
            st.markdown(f"""
            **Wilayah dengan Beban Tertinggi:**
            - {level_pm}: **{top_risiko[group_col]}**
            - Rasio KK/Satpen: **{top_risiko['rasio_kk_per_satpen']:.2f}**
            - {'Setiap satuan pendidikan harus menangani > 1 kasus kondisi khusus rata-rata' if top_risiko['rasio_kk_per_satpen'] > 1 else 'Beban masih relatif terkendali'}
            - Total kebutuhan: {int(top_risiko['jumlah_kondisi_khusus']):,} kasus
            """)
    with why_col:
        with st.popover(" Why? (Hipotesis)"):
            st.markdown(f"""
            **Mengapa {top_risiko[group_col]} menjadi prioritas?**
            - **Keterbatasan Kapasitas:** Jumlah satuan pendidikan tidak sebanding dengan jumlah kebutuhan.
            - **Fokus Konsentrasi:** {'Wilayah ini mungkin memiliki sekolah-sekolah besar dengan populasi siswa tinggi' if top_risiko['rasio_kk_per_satpen'] > 1 else 'Distribusi sekolah cukup untuk kebutuhan saat ini'}
            - **Kebutuhan Spesifik:** Tingginya kasus kondisi khusus membutuhkan penanganan lebih intensif.
            - **Risiko Kualitas:** Beban yang terlalu tinggi dapat menurunkan kualitas layanan MBG.
            """)

st.markdown("---")
st.markdown("### Distribusi Rasio Penerima per Satuan Pendidikan")
df["rasio_penerima_per_satpen_tmp"] = df["jumlah_penerima_manfaat"] / df[satpen_col].replace(0, np.nan)
fig_hist = px.histogram(
    df.dropna(subset=["rasio_penerima_per_satpen_tmp"]), x="rasio_penerima_per_satpen_tmp", nbins=40,
    labels={"rasio_penerima_per_satpen_tmp": "Rasio Penerima per Satuan Pendidikan"}, height=380,
)
st.plotly_chart(fig_hist, use_container_width=True)
median_rasio = df["rasio_penerima_per_satpen_tmp"].median()

# INSIGHT & HIPOTESIS - Distribusi Rasio
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight"):
        st.markdown(f"""
        **Distribusi Beban Satuan Pendidikan:**
        - Median rasio nasional: **{median_rasio:.0f}** siswa per satpen
        - {'Distribusi cenderung miring ke kanan — beberapa sekolah menanggung beban sangat berat' if median_rasio < 100 else 'Sebagian besar sekolah memiliki beban yang relatif seimbang'}
        - Wilayah di atas median → potensi overcrowding
        - Wilayah di bawah median → kemungkinan sekolah di 3T/kapasitas rendah
        """)
with why_col:
    with st.popover("Why? (Hipotesis)"):
        st.markdown(f"""
        **Mengapa variasi rasio ini terjadi?**
        - **Urbanisasi:** {'Sekolah di perkotaan memiliki populasi siswa jauh lebih besar' if median_rasio < 100 else 'Distribusi siswa cukup merata antar wilayah'}
        - **Kebijakan Zonasi:** Sistem zonasi mempengaruhi distribusi siswa per sekolah.
        - **Infrastruktur:** {'Wilayah dengan infrastruktur baik menarik lebih banyak siswa' if median_rasio < 100 else 'Infrastruktur pendidikan sudah tersebar merata'}
        - **Data Validasi:** {'Sekolah kecil di 3T mungkin memiliki data yang belum lengkap' if median_rasio > 100 else 'Data sudah cukup terverifikasi'}
        - **Lihat Fitur 6** untuk analisis lebih detail kapasitas sekolah.
        """)

st.caption(
    f"**Insight:** Median rasio penerima per satuan pendidikan secara nasional adalah **{median_rasio:.0f}**. "
    f"Wilayah jauh di atas median berisiko kapasitas sekolah tidak memadai; jauh di bawah median bisa jadi sekolah kecil/wilayah 3T — "
    f"lihat **Fitur 6: Analisis Sekolah** untuk konteks lebih lanjut."
)

st.markdown("---")
st.success("**Lanjutkan ke Fitur 6: Analisis Sekolah** untuk eksplorasi kapasitas & komposisi satuan pendidikan.")