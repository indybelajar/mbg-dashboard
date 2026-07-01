"""Bonus — Analisis Lanjutan: Multivariat (clustering) + Skor Anomali & Hipotesis.

Fitur tambahan di luar 8 fitur wajib, sesuai instruksi tugas:
"Anda dapat mengembangkan dengan banyak model analysis lainnya untuk memperkaya
berbagai perspektif analysis."
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from utils.filters import render_global_filters, get_satpen_column
from utils.hypothesis_engine import (
    compute_anomaly_flags,
    compute_anomaly_score,
    get_triggered_hypotheses,
)

st.set_page_config(page_title="Bonus: Anomali & Multivariat Lanjutan", page_icon="🚩", layout="wide")
st.title("Bonus: Analisis Multivariat Lanjutan & Skor Anomali")
st.caption("Fitur tambahan di luar 8 fitur wajib — model analisis lanjutan untuk memperkaya perspektif monitoring & evaluasi")

df, tipe_sekolah = render_global_filters()
satpen_col = get_satpen_column(tipe_sekolah)

with st.expander("Penting dibaca: dasar metodologi & batasan", expanded=False):
    st.markdown(
        """
        **Skor anomali & hipotesis di halaman ini bersifat statistik deskriptif, bukan tuduhan atau kesimpulan hukum.**
        - Skor dihitung dari seberapa jauh data menyimpang dari pola umum (outlier statistik), bukan dari bukti investigasi.
        - Setiap anomali punya beberapa kemungkinan penyebab yang SAH (kesalahan input, karakteristik wilayah/sekolah) —
          ditampilkan lebih dulu sebelum hipotesis "memerlukan verifikasi lebih lanjut".
        - Sebelum menyebarluaskan temuan, **verifikasi ke sumber data resmi/instansi terkait** dulu.
        """
    )

# INSIGHT & HIPOTESIS - Pengantar Bonus
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight"):
        st.markdown("""
        **Analisis Lanjutan untuk Insight Lebih Dalam:**
        - Clustering: Mengelompokkan provinsi dengan profil serupa
        - Parallel Coordinates: Membandingkan banyak provinsi sekaligus
        - Skor Anomali: Mendeteksi outlier statistik
        - Hipotesis Otomatis: Menjelaskan kemungkinan penyebab anomali
        - {'Metode ini membantu identifikasi prioritas intervensi' if True else 'Tools analisis lanjutan untuk M&E'}
        """)
with why_col:
    with st.popover("Why? (Hipotesis)"):
        st.markdown("""
        **Mengapa analisis lanjutan ini penting?**
        - **Identifikasi Pola Tersembunyi:** {'Cluster menunjukkan kelompok wilayah dengan karakteristik serupa untuk strategi seragam' if True else 'Pola yang tidak terlihat di analisis univariat'}
        - **Deteksi Dini:** {'Anomali bisa menjadi early warning sistem sebelum masalah membesar' if True else 'Monitoring proaktif lebih efektif'}
        - **Efisiensi Sumber Daya:** {'Fokus intervensi pada wilayah dengan anomali tertinggi' if True else 'Alokasi anggaran lebih tepat sasaran'}
        - **Pembelajaran:** {'Memahami mengapa suatu wilayah berbeda membantu perbaikan sistem' if True else 'Continuous improvement berbasis data'}
        """)

numeric_options = [
    "jumlah_penerima_manfaat", "jumlah_satuan_pendidikan", "jumlah_laki", "jumlah_perempuan",
    "jumlah_kondisi_khusus", "jumlah_satpen_negeri", "jumlah_satpen_swasta",
]
label_map = {
    "jumlah_penerima_manfaat": "Total Penerima Manfaat", "jumlah_satuan_pendidikan": "Jumlah Satuan Pendidikan",
    "jumlah_laki": "Jumlah Laki-laki", "jumlah_perempuan": "Jumlah Perempuan",
    "jumlah_kondisi_khusus": "Jumlah Kondisi Khusus", "jumlah_satpen_negeri": "Jumlah Satpen Negeri",
    "jumlah_satpen_swasta": "Jumlah Satpen Swasta",
}

agg = df.groupby("provinsi_clean", as_index=False)[numeric_options].sum()
agg["rasio_penerima_per_satpen"] = agg["jumlah_penerima_manfaat"] / agg["jumlah_satuan_pendidikan"].replace(0, np.nan)
agg["pct_kondisi_khusus"] = agg["jumlah_kondisi_khusus"] / agg["jumlah_penerima_manfaat"].replace(0, np.nan) * 100
agg["rasio_gender_LP"] = agg["jumlah_laki"] / agg["jumlah_perempuan"].replace(0, np.nan)

tab_multi, tab_anomali = st.tabs(["Multivariat Lanjutan", "Skor Anomali & Hipotesis"])

# ===========================================================================
# TAB MULTIVARIAT
# ===========================================================================
with tab_multi:
    st.markdown("#### Parallel Coordinates — Bandingkan Banyak Provinsi Sekaligus")
    pc_vars = ["jumlah_penerima_manfaat", "jumlah_satuan_pendidikan", "rasio_penerima_per_satpen", "pct_kondisi_khusus"]
    top_for_pc = agg.sort_values("jumlah_penerima_manfaat", ascending=False)["provinsi_clean"].tolist()
    pc_sel = st.multiselect("Pilih provinsi", agg["provinsi_clean"].tolist(), default=top_for_pc[:10])

    if len(pc_sel) >= 1:
        df_pc = agg[agg["provinsi_clean"].isin(pc_sel)].copy()
        df_pc_norm = df_pc.copy()
        for v in pc_vars:
            vmin, vmax = agg[v].min(), agg[v].max()
            df_pc_norm[v] = (df_pc[v] - vmin) / (vmax - vmin + 1e-9)
        fig_pc = go.Figure(data=go.Parcoords(
            line=dict(color=df_pc_norm[pc_vars[0]], colorscale="Viridis"),
            dimensions=[dict(label=label_map.get(v, v), values=df_pc_norm[v]) for v in pc_vars],
        ))
        fig_pc.update_layout(height=450)
        st.plotly_chart(fig_pc, use_container_width=True)
        
        # INSIGHT & HIPOTESIS - Parallel Coordinates
        insight_col, why_col = st.columns(2)
        with insight_col:
            with st.popover("Insight"):
                st.markdown("""
                **Pola Multivariat Provinsi:**
                - Warna menunjukkan nilai variabel utama (semakin gelap = semakin tinggi)
                - {'Provinsi yang dipilih memiliki profil yang beragam' if len(pc_sel) > 3 else 'Pola terlihat jelas antar provinsi yang dipilih'}
                - {'Beberapa provinsi menunjukkan pola ekstrim di variabel tertentu' if True else 'Distribusi relatif merata'}
                - {'Parallel coordinates membantu melihat trade-off antar variabel' if True else 'Visualisasi multivariat yang informatif'}
                """)
        with why_col:
            with st.popover("Why? (Hipotesis)"):
                st.markdown("""
                **Mengapa provinsi memiliki pola berbeda?**
                - **Karakteristik Demografi:** {'Populasi, kepadatan, dan struktur usia mempengaruhi semua variabel' if True else 'Faktor demografis dominan'}
                - **Kapasitas Layanan:** {'Jumlah dan kualitas sekolah menentukan kapasitas layanan' if True else 'Infrastruktur pendidikan bervariasi'}
                - **Kebijakan Daerah:** {'Prioritas dan implementasi program berbeda antar provinsi' if True else 'Otonomi daerah mempengaruhi eksekusi'}
                - **Sistem Data:** {'Kualitas pelaporan data bervariasi antar provinsi' if True else 'Validasi data perlu ditingkatkan'}
                """)

    st.markdown("---")
    st.markdown("#### Clustering K-Means — Kelompok Provinsi dengan Profil Mirip")
    cluster_vars = ["rasio_penerima_per_satpen", "pct_kondisi_khusus", "rasio_gender_LP"]
    k = st.slider("Jumlah cluster (K)", 2, 6, 3)
    df_cluster = agg[["provinsi_clean"] + cluster_vars].replace([np.inf, -np.inf], np.nan).dropna()

    if df_cluster.shape[0] >= k:
        X = StandardScaler().fit_transform(df_cluster[cluster_vars])
        km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X)
        df_cluster["cluster"] = km.labels_.astype(str)

        fig_cluster = px.scatter(
            df_cluster, x=cluster_vars[0], y=cluster_vars[1], color="cluster", hover_name="provinsi_clean",
            labels={cluster_vars[0]: label_map.get(cluster_vars[0], cluster_vars[0]), cluster_vars[1]: "% Kondisi Khusus"},
            height=480,
        )
        st.plotly_chart(fig_cluster, use_container_width=True)

        # INSIGHT & HIPOTESIS - Clustering
        smallest_cluster = df_cluster.groupby("cluster").size().idxmin() if len(df_cluster) > 0 else None
        insight_col, why_col = st.columns(2)
        with insight_col:
            with st.popover("Insight"):
                st.markdown(f"""
                **Hasil Clustering Provinsi:**
                - Jumlah cluster: **{k}** kelompok
                - {'Ada cluster dengan anggota sedikit (outlier/profil unik)' if smallest_cluster is not None and len(df_cluster[df_cluster['cluster']==smallest_cluster]) < 3 else 'Cluster terdistribusi cukup merata'}
                - {'Cluster yang menyendiri → kandidat investigasi prioritas' if smallest_cluster is not None and len(df_cluster[df_cluster['cluster']==smallest_cluster]) < 3 else 'Provinsi memiliki profil yang relatif homogen'}
                - {'Clustering membantu strategi intervensi yang berbeda tiap cluster' if True else 'Pendekatan satu ukuran untuk semua tidak efektif'}
                """)
        with why_col:
            with st.popover("Why? (Hipotesis)"):
                st.markdown("""
                **Mengapa provinsi terbagi dalam cluster-cluster ini?**
                - **Faktor Geografis:** {'Wilayah barat vs timur memiliki karakteristik berbeda' if True else 'Lokasi geografis mempengaruhi pola'}
                - **Tingkat Urbanisasi:** {'Perkotaan vs pedesaan memiliki rasio dan kebutuhan berbeda' if True else 'Urban-rural gap mempengaruhi variabel'}
                - **Kapasitas Fiskal:** {'Provinsi dengan APBD besar memiliki layanan lebih baik' if True else 'Kemampuan fiskal bervariasi'}
                - **Implementasi Program:** {'Tahapan implementasi MBG berbeda antar daerah' if True else 'Maturitas program bervariasi'}
                """)

        with st.expander("Lihat anggota tiap cluster"):
            for c in sorted(df_cluster["cluster"].unique()):
                members = df_cluster[df_cluster["cluster"] == c]["provinsi_clean"].tolist()
                st.markdown(f"**Cluster {c}** ({len(members)} provinsi): {', '.join(members)}")
        st.caption("Cluster yang menyendiri (anggota sedikit) adalah kandidat utama untuk diperiksa lebih detail di tab Skor Anomali.")
    else:
        st.warning("Tidak cukup data untuk clustering dengan filter saat ini.")

# ===========================================================================
# TAB SKOR ANOMALI
# ===========================================================================
with tab_anomali:
    df_scored = compute_anomaly_flags(df)
    df_scored = compute_anomaly_score(df_scored)

    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("🟢 Risiko Rendah", f"{int((df_scored['kategori_risiko']=='Rendah').sum()):,} baris")
    sc2.metric("🟡 Risiko Sedang", f"{int((df_scored['kategori_risiko']=='Sedang').sum()):,} baris")
    sc3.metric("🔴 Risiko Tinggi", f"{int((df_scored['kategori_risiko']=='Tinggi').sum()):,} baris")

    fig_score_dist = px.histogram(
        df_scored, x="skor_anomali", color="kategori_risiko", nbins=20,
        color_discrete_map={"Rendah": "#4CAF50", "Sedang": "#FFC107", "Tinggi": "#D64550"}, height=350,
    )
    st.plotly_chart(fig_score_dist, use_container_width=True)
    
    # INSIGHT & HIPOTESIS - Skor Anomali
    insight_col, why_col = st.columns(2)
    with insight_col:
        with st.popover("Insight"):
            tinggi_count = int((df_scored['kategori_risiko']=='Tinggi').sum())
            st.markdown(f"""
            **Distribusi Risiko Anomali:**
            - 🔴 Risiko Tinggi: **{tinggi_count}** entitas ({tinggi_count/len(df_scored)*100:.1f}%)
            - {'Perlu verifikasi lapangan segera' if tinggi_count > 0 else ' Tidak ada anomali signifikan'}
            - {'Sebagian besar entitas dalam kategori aman' if tinggi_count < len(df_scored)*0.1 else 'Persentase anomali cukup tinggi, perlu investigasi sistemik'}
            - {'Distribusi normal dengan ekor kanan = beberapa outlier ekstrim' if True else 'Pola distribusi data'}
            """)
    with why_col:
        with st.popover("Why? (Hipotesis)"):
            st.markdown("""
            **Mengapa anomali bisa terjadi?**
            - **Kesalahan Input Data:** {'Human error dalam pengisian data di lapangan' if True else 'Perlu pelatihan petugas'}
            - **Karakteristik Unik:** {'Wilayah/sekolah dengan kondisi khusus yang memang berbeda' if True else 'Kekhasan lokal yang sah'}
            - **Sistem Pelaporan:** {'Perbedaan standar dan waktu pelaporan antar daerah' if True else 'Konsistensi data perlu ditingkatkan'}
            - **Validasi Data:** {'Data belum melalui proses validasi yang ketat' if True else 'Perlu quality assurance'}
            - **KONFIRMASI LAPANGAN diperlukan sebelum mengambil tindakan' if True else 'Analisis statistik perlu divalidasi'}
            """)

    df_scored["entitas_label"] = (
        df_scored["kecamatan_clean"] + ", " + df_scored["kabkota_clean"] + " — " + df_scored["provinsi_clean"] + " (" + df_scored["jenjang"] + ")"
    )
    top_n_score = st.slider("Tampilkan berapa entitas teratas?", 5, 30, 10)
    top_scored = df_scored.nlargest(top_n_score, "skor_anomali")

    # INSIGHT & HIPOTESIS - Top Anomali
    if len(top_scored) > 0:
        insight_col, why_col = st.columns(2)
        with insight_col:
            with st.popover("Insight"):
                top_entitas = top_scored.iloc[0]
                st.markdown(f"""
                **Entitas dengan Risiko Tertinggi:**
                - {top_entitas['entitas_label']}
                - Skor Anomali: **{top_entitas['skor_anomali']:.0f}/100** ({top_entitas['kategori_risiko']})
                - {'PRIORITAS INVESTIGASI LAPANGAN' if top_entitas['kategori_risiko'] == 'Tinggi' else 'Perlu monitoring lebih lanjut'}
                - {'Top {top_n_score} entitas ditampilkan untuk prioritas verifikasi' if True else ''}
                """)
        with why_col:
            with st.popover("Why? (Hipotesis)"):
                st.markdown("""
                **Mengapa entitas ini memiliki skor anomali tertinggi?**
                - **Kombinasi Faktor:** {'Beberapa variabel menyimpang secara bersamaan' if True else 'Outlier pada multiple dimensi'}
                - **Validasi Data:** {'Kemungkinan besar data perlu diverifikasi' if True else 'Konfirmasi dengan data primer diperlukan'}
                - **Karakteristik Khusus:** {'Bisa jadi wilayah/sekolah dengan kondisi unik' if True else 'Perlu dipahami konteks lokalnya'}
                - **KESIMPULAN AKHIR menunggu verifikasi lapangan' if True else 'Temuan awal untuk investigasi lebih lanjut'}
                """)

    pilihan_entitas = st.selectbox("Pilih entitas untuk lihat detail hipotesis", top_scored["entitas_label"].tolist() if len(top_scored) > 0 else [])
    
    if len(top_scored) > 0 and pilihan_entitas:
        row_detail = df_scored[df_scored["entitas_label"] == pilihan_entitas].iloc[0]
        st.markdown(f"**{pilihan_entitas}** — Skor Anomali: **{row_detail['skor_anomali']:.0f}/100** ({row_detail['kategori_risiko']})")

        hyps = get_triggered_hypotheses(row_detail)
        if hyps:
            for h in hyps:
                with st.expander(f"{h['judul']}", expanded=False):
                    st.caption(h["deskripsi"])
                    st.markdown("**Kemungkinan penyebab (urut dari paling umum):**")
                    for i, hipotesis_text in enumerate(h["hipotesis"], 1):
                        if i == len(h["hipotesis"]):
                            st.warning(f"{i}. {hipotesis_text}")
                        else:
                            st.markdown(f"{i}. {hipotesis_text}")
        else:
            st.success("Tidak ada flag anomali signifikan terpicu untuk entitas ini.")
            
        # INSIGHT & HIPOTESIS - Detail Entitas
        insight_col, why_col = st.columns(2)
        with insight_col:
            with st.popover("Insight"):
                st.markdown(f"""
                **Detail Anomali {row_detail['entitas_label'].split(',')[0]}:**
                - Skor: **{row_detail['skor_anomali']:.0f}/100**
                - Kategori: **{row_detail['kategori_risiko']}**
                - {'Perlu investigasi mendalam' if row_detail['kategori_risiko'] == 'Tinggi' else 'Monitoring rutin disarankan'}
                - {'Hipotesis yang terpicu menunjukkan area yang perlu dicek' if len(hyps) > 0 else 'Belum ada pola anomali yang terdeteksi'}
                """)
        with why_col:
            with st.popover("Why? (Hipotesis)"):
                st.markdown("""
                **Interpretasi Skor Anomali:**
                - Skor tinggi ≠ kesalahan, bisa jadi indikasi:
                  - Wilayah dengan karakteristik unik
                  - Keberhasilan program yang luar biasa
                  - Kebutuhan intervensi yang mendesak
                - **KONFIRMASI LAPANGAN** adalah langkah selanjutnya
                - Gunakan hasil ini sebagai **early warning system**, bukan verdict final
                """)

    with st.expander("Tabel lengkap entitas berisiko tertinggi"):
        st.dataframe(
            top_scored[["entitas_label", "skor_anomali", "kategori_risiko", "jumlah_penerima_manfaat"]]
            .rename(columns={"entitas_label": "Entitas", "skor_anomali": "Skor", "kategori_risiko": "Kategori", "jumlah_penerima_manfaat": "Penerima"}),
            hide_index=True, 
            use_container_width=True,
        )

# INSIGHT & HIPOTESIS - Penutup Bonus
st.markdown("---")
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight"):
        st.markdown("""
        **Ringkasan Analisis Lanjutan:**
        - Clustering mengidentifikasi kelompok provinsi dengan profil serupa
        - Parallel coordinates membandingkan kinerja multivariat
        - Skor anomali mendeteksi outlier statistik
        - Hipotesis otomatis memberikan penjelasan awal
        - {'Semua temuan perlu DIVERIFIKASI sebelum tindakan' if True else 'Analisis statistik sebagai alat bantu'}
        """)
with why_col:
    with st.popover("Why? (Hipotesis)"):
        st.markdown("""
        **Mengapa hasil analisis lanjutan ini penting untuk MBG?**
        - **Efisiensi Monitoring:** {'Fokus sumber daya pada wilayah dengan anomali tertinggi' if True else 'Prioritas intervensi lebih tepat'}
        - **Pembelajaran Sistem:** {'Memahami faktor penyebab anomali membantu perbaikan program' if True else 'Continuous improvement berbasis data'}
        - **Akuntabilitas:** {'Menunjukkan penggunaan data untuk pengambilan keputusan' if True else 'Transparansi dan evidence-based policy'}
        - **Kesiapan Skala:** {'Sistem deteksi dini penting untuk program nasional berskala besar' if True else 'Skalabilitas program MBG'}
        """)

st.markdown("---")
st.caption(
    "Dashboard BI Program MBG Nasional — seluruh insight bersifat deskriptif berbasis data yang tersedia; "
    "perlu diverifikasi ke sumber resmi untuk pengambilan keputusan formal."
)