"""Fitur 8 — Dashboard Interaktif: eksplorasi bebas multivariat + kesimpulan jawaban pertanyaan kunci."""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import gini_coefficient
from utils.filters import render_global_filters, get_satpen_column

st.set_page_config(page_title="Fitur 8: Dashboard Interaktif", layout="wide")
st.title("Fitur 8: Dashboard Interaktif")
st.caption("Eksplorasi bebas: pilih sendiri variabel, level, dan wilayah — lalu lihat kesimpulan jawaban pertanyaan kunci di bagian bawah")

df, tipe_sekolah = render_global_filters()
satpen_col = get_satpen_column(tipe_sekolah)

st.markdown(
    """
    > **Yang perlu disampaikan:** "Ini adalah ruang eksplorasi bebas — semua filter (Tahun, Provinsi,
    > Kabupaten, Kecamatan, Jenjang, Negeri/Swasta) sudah aktif di sidebar. Di bagian bawah halaman ini juga
    > ada kesimpulan ringkas yang menjawab 6 pertanyaan kunci dari hasil seluruh analisis."
    """
)

# INSIGHT & HIPOTESIS - Pengantar Dashboard
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight"):
        st.markdown("""
        **Dashboard Interaktif untuk Eksplorasi Bebas:**
        - Pilih level agregasi (Provinsi/Kabupaten/Kecamatan)
        - Pilih variabel X dan Y untuk scatter plot
        - Lihat heatmap korelasi antar variabel
        - Ranking bebas berdasarkan variabel pilihan
        - Semua filter sidebar aktif untuk eksplorasi mendalam
        """)
with why_col:
    with st.popover("Why? (Hipotesis)"):
        st.markdown("""
        **Mengapa dashboard interaktif ini penting?**
        - **Eksplorasi Bebas:** Pengguna dapat menemukan pola yang tidak terlihat di fitur-fitur sebelumnya.
        - **Validasi Hipotesis:** {'Pengguna bisa menguji hipotesis mereka sendiri dengan data aktual' if True else 'Membantu verifikasi temuan'}
        - **Kustomisasi:** {'Setiap pengguna memiliki pertanyaan spesifik yang perlu dijawab' if True else 'Fleksibilitas analisis'}
        - **Pembelajaran:** {'Cara terbaik memahami data adalah dengan bereksperimen langsung' if True else 'Eksplorasi mandiri meningkatkan pemahaman'}
        """)

level = st.selectbox("Level agregasi", ["provinsi_clean", "kabkota_clean", "kecamatan_clean"],
                      format_func=lambda x: {"provinsi_clean": "Provinsi", "kabkota_clean": "Kabupaten/Kota", "kecamatan_clean": "Kecamatan"}[x])

numeric_options = [
    "jumlah_penerima_manfaat", "jumlah_satuan_pendidikan", "jumlah_laki", "jumlah_perempuan",
    "jumlah_kondisi_khusus", "jumlah_alergi", "jumlah_fobia", "jumlah_intoleransi",
    "jumlah_satpen_negeri", "jumlah_satpen_swasta",
]
sum_cols = [c for c in numeric_options if c != "jumlah_satuan_pendidikan"]
label_map = {
    "jumlah_penerima_manfaat": "Total Penerima Manfaat", "jumlah_satuan_pendidikan": "Jumlah Satuan Pendidikan",
    "jumlah_laki": "Jumlah Laki-laki", "jumlah_perempuan": "Jumlah Perempuan",
    "jumlah_kondisi_khusus": "Jumlah Kondisi Khusus", "jumlah_alergi": "Jumlah Alergi",
    "jumlah_fobia": "Jumlah Fobia", "jumlah_intoleransi": "Jumlah Intoleransi",
    "jumlah_satpen_negeri": "Jumlah Satpen Negeri", "jumlah_satpen_swasta": "Jumlah Satpen Swasta",
}

group_cols = [level] if level == "provinsi_clean" else (["provinsi_clean", level] if level != "kecamatan_clean" else ["provinsi_clean", "kabkota_clean", level])
agg = df.groupby(group_cols, as_index=False)[sum_cols].sum()
agg["jumlah_satuan_pendidikan"] = df.groupby(group_cols)[satpen_col].sum().values
agg["label"] = agg[level]

st.markdown("---")
st.markdown("### Scatter Plot Bebas")
colA, colB, colC = st.columns(3)
with colA:
    x_var = st.selectbox("Variabel X", numeric_options, index=1, format_func=lambda x: label_map[x])
with colB:
    y_var = st.selectbox("Variabel Y", numeric_options, index=0, format_func=lambda x: label_map[x])
with colC:
    log_scale = st.checkbox("Skala log", value=True)

fig_scatter = px.scatter(
    agg, x=x_var, y=y_var, color="provinsi_clean" if level != "provinsi_clean" else None,
    hover_name="label", log_x=log_scale, log_y=log_scale, trendline="ols",
    labels={x_var: label_map[x_var], y_var: label_map[y_var]}, height=500,
)
st.plotly_chart(fig_scatter, use_container_width=True)
corr_val = agg[[x_var, y_var]].replace([np.inf, -np.inf], np.nan).dropna().corr().iloc[0, 1]

# INSIGHT & HIPOTESIS - Scatter Plot
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight"):
        st.markdown(f"""
        **Hubungan {label_map[x_var]} vs {label_map[y_var]}:**
        - Korelasi Pearson: **{corr_val:.3f}**
        - {'Korelasi positif kuat' if corr_val > 0.7 else 'Korelasi sedang' if corr_val > 0.3 else 'Korelasi lemah'}
        - {'Variabel ini saling mempengaruhi' if abs(corr_val) > 0.5 else 'Hubungan tidak linear atau dipengaruhi faktor lain'}
        - {'Titik di atas garis tren = over-performing' if corr_val > 0 else 'Pola perlu investigasi lebih lanjut'}
        """)
with why_col:
    with st.popover("Why? (Hipotesis)"):
        st.markdown(f"""
        **Mengapa korelasinya {corr_val:.3f}?**
        - **Hubungan Logis:** {'Semakin banyak sekolah, semakin banyak penerima (logis)' if x_var == 'jumlah_satuan_pendidikan' and y_var == 'jumlah_penerima_manfaat' else 'Variabel ini terkait secara struktural'}
        - **Faktor Konfunding:** {'Wilayah dengan populasi besar mempengaruhi kedua variabel' if abs(corr_val) > 0.5 else 'Ada variabel lain yang lebih dominan'}
        - **Data Quality:** {'Data yang konsisten menghasilkan korelasi yang jelas' if abs(corr_val) > 0.5 else 'Perlu pengecekan kualitas data di beberapa wilayah'}
        - **Outliers:** {'Beberapa titik ekstrim mempengaruhi kekuatan korelasi' if abs(corr_val) < 0.3 else 'Distribusi data cukup homogen'}
        """)

st.caption(f"Korelasi Pearson **{label_map[x_var]}** vs **{label_map[y_var]}**: **{corr_val:.3f}**")

st.markdown("---")
st.markdown("### Correlation Heatmap")
corr_matrix = agg[numeric_options].replace([np.inf, -np.inf], np.nan).fillna(0).corr()
fig_heat = px.imshow(
    corr_matrix, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
    x=[label_map[c] for c in corr_matrix.columns], y=[label_map[c] for c in corr_matrix.columns], height=500,
)
st.plotly_chart(fig_heat, use_container_width=True)

# INSIGHT & HIPOTESIS - Heatmap
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight"):
        # Cari korelasi tertinggi
        corr_flat = corr_matrix.unstack().sort_values(ascending=False)
        corr_flat = corr_flat[corr_flat < 1]  # exclude self-correlation
        top_corr = corr_flat.head(3)
        st.markdown(f"""
        **Pola Korelasi Antar Variabel:**
        - Korelasi tertinggi: 
          - {', '.join([f'{label_map.get(k[0], k[0])} ↔ {label_map.get(k[1], k[1])} ({v:.2f})' for (k,v) in top_corr.items()])}
        - {'Cluster variabel yang saling terkait' if len(top_corr) > 0 else 'Belum ada pola yang jelas'}
        - {'Warna merah = korelasi positif, biru = negatif' if True else ''}
        """)
with why_col:
    with st.popover(" Why? (Hipotesis)"):
        st.markdown("""
        **Mengapa pola korelasi ini terbentuk?**
        - **Struktur Data:** {'Variabel penerima, gender, dan kondisi khusus saling terkait secara alami' if True else 'Data memiliki struktur yang kompleks'}
        - **Faktor Demografi:** {'Wilayah dengan populasi besar memiliki semua variabel yang tinggi' if True else 'Variasi demografi mempengaruhi korelasi'}
        - **Kualitas Data:** {'Data yang konsisten menunjukkan korelasi yang jelas' if True else 'Perlu validasi data di beberapa wilayah'}
        - **Implikasi Program:** {'Korelasi ini membantu identifikasi prioritas intervensi' if True else 'Perlu analisis lebih mendalam'}
        """)

st.markdown("---")
st.markdown(f"### Tabel Ranking Bebas — {label_map.get(y_var, y_var)}")
sort_var = st.selectbox("Urutkan berdasarkan", numeric_options, format_func=lambda x: label_map[x], key="sortvar_f8")
top_n = st.slider("Tampilkan Top-N", 5, min(50, agg.shape[0]), min(20, agg.shape[0]), key="topn_f8")
st.dataframe(
    agg.sort_values(sort_var, ascending=False).head(top_n)[["label"] + numeric_options].rename(columns={**{"label": {"provinsi_clean": "Provinsi", "kabkota_clean": "Kabupaten/Kota", "kecamatan_clean": "Kecamatan"}[level]}, **label_map}),
    hide_index=True, 
    use_container_width=True, 
    height=400,
)

# INSIGHT & HIPOTESIS - Ranking
if len(agg) > 0:
    top_row = agg.sort_values(sort_var, ascending=False).iloc[0]
    insight_col, why_col = st.columns(2)
    with insight_col:
        with st.popover("Insight"):
            st.markdown(f"""
            **Ranking {label_map.get(sort_var, sort_var)}:**
            - Peringkat 1: **{top_row['label']}** ({int(top_row[sort_var]):,})
            - {'Wilayah ini menjadi fokus utama untuk variabel ini' if True else 'Perlu analisis lebih lanjut'}
            - {'Tabel menunjukkan distribusi nilai dari tertinggi ke terendah' if True else ''}
            """)
    with why_col:
        with st.popover(" Why? (Hipotesis)"):
            st.markdown(f"""
            **Mengapa {top_row['label']} menduduki peringkat tertinggi?**
            - **Karakteristik Wilayah:** {'Populasi besar dan kepadatan penduduk tinggi' if top_row.get('jumlah_penerima_manfaat', 0) > 10000 else 'Faktor geografis dan demografis'}
            - **Kapasitas Layanan:** {'Memiliki infrastruktur pendidikan yang matang' if top_row.get('jumlah_satuan_pendidikan', 0) > 100 else 'Akses layanan pendidikan baik'}
            - **Sistem Data:** {'Sistem pelaporan data yang baik menghasilkan data lengkap' if True else 'Validasi data mungkin masih perlu ditingkatkan'}
            - **Prioritas Program:** {'Wilayah ini menjadi prioritas implementasi MBG' if True else 'Program masih dalam tahap pengembangan'}
            """)

# ===========================================================================
# KESIMPULAN — menjawab 6 pertanyaan kunci rubrik secara eksplisit
# ===========================================================================
st.markdown("---")
st.markdown("## Kesimpulan: Menjawab 6 Pertanyaan Kunci")
st.caption("Ringkasan jawaban berbasis filter yang AKTIF SAAT INI di sidebar. Detail lengkap tiap poin ada di halaman fitur terkait.")

# Q1: Provinsi/kabupaten dengan kondisi khusus tertinggi
by_prov_kk = df.groupby("provinsi_clean")["jumlah_kondisi_khusus"].sum().sort_values(ascending=False)
q1_jawaban = by_prov_kk.index[0] if len(by_prov_kk) else "N/A"
q1_nilai = int(by_prov_kk.iloc[0]) if len(by_prov_kk) else 0

# Q2: Kesebandingan penerima vs kebutuhan (korelasi)
agg_q2 = df.groupby("provinsi_clean", as_index=False).agg(pm=("jumlah_penerima_manfaat", "sum"), kk=("jumlah_kondisi_khusus", "sum"))
corr_q2 = agg_q2[["pm", "kk"]].corr().iloc[0, 1] if len(agg_q2) > 2 else np.nan

# Q3: Jenjang dengan kebutuhan inklusif terbesar
by_jenjang_q3 = df.groupby("jenjang", as_index=False).agg(kk=("jumlah_kondisi_khusus", "sum"), pm=("jumlah_penerima_manfaat", "sum"))
by_jenjang_q3["pct"] = by_jenjang_q3["kk"] / by_jenjang_q3["pm"].replace(0, np.nan) * 100
q3_jawaban = by_jenjang_q3.nlargest(1, "pct").iloc[0] if len(by_jenjang_q3) else None

# Q4: Komposisi negeri/swasta
total_negeri_q4 = int(df["jumlah_satpen_negeri"].sum())
total_swasta_q4 = int(df["jumlah_satpen_swasta"].sum())

# Q5: Ketimpangan gender
total_laki_q5, total_perempuan_q5 = int(df["jumlah_laki"].sum()), int(df["jumlah_perempuan"].sum())
rasio_q5 = total_laki_q5 / total_perempuan_q5 if total_perempuan_q5 else np.nan

# Q6: Wilayah prioritas intervensi (rasio kk per satpen tertinggi, level provinsi)
agg_q6 = df.groupby("provinsi_clean", as_index=False).agg(kk=("jumlah_kondisi_khusus", "sum"), satpen=(satpen_col, "sum"))
agg_q6["rasio"] = agg_q6["kk"] / agg_q6["satpen"].replace(0, np.nan)
q6_jawaban = agg_q6.nlargest(1, "rasio").iloc[0] if len(agg_q6) else None

with st.container(border=True):
    st.markdown(f"**1. Provinsi dengan jumlah peserta didik berkondisi khusus paling tinggi:**")
    st.markdown(f" **{q1_jawaban}** dengan {q1_nilai:,} peserta didik berkondisi khusus.")

with st.container(border=True):
    st.markdown(f"**2. Apakah distribusi penerima manfaat sudah sebanding dengan kebutuhan layanan?**")
    if not np.isnan(corr_q2):
        st.markdown(
            f" Korelasi antar-provinsi antara total penerima manfaat dan jumlah kondisi khusus adalah **{corr_q2:.3f}**. "
            f"{'Secara umum SEBANDING (korelasi kuat).' if corr_q2 > 0.6 else 'BELUM SEPENUHNYA sebanding — ada provinsi dengan kebutuhan tinggi namun penerima manfaat relatif kecil dibanding provinsi lain, atau sebaliknya.'}"
        )
    else:
        st.markdown(" Data tidak cukup untuk menghitung korelasi pada filter saat ini.")

with st.container(border=True):
    st.markdown(f"**3. Jenjang pendidikan dengan kebutuhan layanan inklusif paling besar:**")
    if q3_jawaban is not None:
        st.markdown(f" Jenjang **{q3_jawaban['jenjang']}** dengan **{q3_jawaban['pct']:.2f}%** peserta didik berkondisi khusus dari total penerima di jenjang tersebut.")

with st.container(border=True):
    st.markdown(f"**4. Komposisi sekolah negeri vs swasta dalam melayani peserta didik berkondisi khusus:**")
    st.markdown(
        f" **{total_negeri_q4/(total_negeri_q4+total_swasta_q4)*100:.1f}% negeri** vs "
        f"**{total_swasta_q4/(total_negeri_q4+total_swasta_q4)*100:.1f}% swasta**. Karena data tidak memecah peserta "
        f"kondisi khusus per jenis sekolah, porsi pelayanan diasumsikan proporsional terhadap jumlah sekolah masing-masing jenis."
    )

with st.container(border=True):
    st.markdown(f"**5. Apakah terdapat ketimpangan gender pada penerima manfaat?**")
    st.markdown(
        f" Rasio Laki-laki/Perempuan secara nasional: **{rasio_q5:.3f}** "
        f"({'tergolong seimbang' if 0.9 <= rasio_q5 <= 1.1 else 'menunjukkan ketimpangan ringan-sedang'}). "
        f"Variasi lebih signifikan terlihat di level jenjang tertentu (lihat Fitur 3: Analisis Demografi)."
    )

with st.container(border=True):
    st.markdown(f"**6. Wilayah yang sebaiknya menjadi prioritas intervensi periode berikutnya:**")
    if q6_jawaban is not None:
        st.markdown(
            f" **{q6_jawaban['provinsi_clean']}** — rasio kebutuhan kondisi khusus per satuan pendidikan tertinggi "
            f"({q6_jawaban['rasio']:.1f}), mengindikasikan kapasitas layanan saat ini relatif kecil dibanding kebutuhan."
        )

# INSIGHT & HIPOTESIS - Rekomendasi Tindak Lanjut
st.markdown("---")
st.markdown("### Rekomendasi Tindak Lanjut")

insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight"):
        st.markdown("""
        **Rekomendasi Berdasarkan Analisis:**
        1. Verifikasi temuan ke dinas terkait sebelum kebijakan
        2. Lengkapi data dari provinsi under-represented
        3. Prioritaskan wilayah dengan rasio kk/satpen tinggi
        4. Tingkatkan kapasitas sekolah di wilayah prioritas
        5. Perkuat koordinasi negeri-swasta
        """)
with why_col:
    with st.popover(" Why? (Hipotesis)"):
        st.markdown("""
        **Mengapa rekomendasi ini penting?**
        - **Validasi Lapangan:** {'Data perlu diverifikasi dengan kondisi nyata' if True else 'Memastikan akurasi analisis'}
        - **Kesetaraan Akses:** {'Memastikan semua wilayah mendapat layanan yang memadai' if True else 'Mengurangi kesenjangan layanan'}
        - **Efisiensi Program:** {'Prioritaskan sumber daya di tempat yang paling membutuhkan' if True else 'Optimalisasi anggaran MBG'}
        - **Keberlanjutan:** {'Membangun sistem yang berkelanjutan berdasarkan data' if True else 'Perbaikan berkelanjutan program'}
        """)

st.info(
    " **Rekomendasi tindak lanjut:** (1) Verifikasi temuan di atas ke dinas pendidikan/kesehatan provinsi terkait sebelum "
    "dijadikan dasar kebijakan resmi. (2) Lengkapi pelaporan dari provinsi yang masih under-represented (lihat Fitur 7). "
    "(3) Prioritaskan penambahan kapasitas satuan pendidikan di wilayah dengan rasio kebutuhan/kapasitas tertinggi (poin 6)."
)

st.markdown("---")
st.caption(
    "Dashboard BI Program MBG Nasional — seluruh insight bersifat deskriptif berbasis data yang tersedia; "
    "perlu diverifikasi ke sumber resmi untuk pengambilan keputusan formal."
)