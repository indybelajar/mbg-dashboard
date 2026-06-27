"""
Dashboard Interaktif MBG (Makan Bergizi Gratis) — Insight Ketimpangan & Red Flags
Dibangun dengan Streamlit + Plotly.

Jalankan lokal:  streamlit run app.py
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from utils.data_loader import (
    get_processed_data,
    aggregate_by_level,
    detect_outliers_iqr,
    gini_coefficient,
)
from utils.hypothesis_engine import (
    compute_anomaly_flags,
    compute_anomaly_score,
    get_triggered_hypotheses,
    aggregate_score_by_entity,
)

st.set_page_config(
    page_title="Dashboard MBG — Insight & Red Flags",
    page_icon="🍽️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Load data (cached)
# ---------------------------------------------------------------------------
df_raw = get_processed_data()

st.title("🍽️ Dashboard Interaktif Program MBG")
st.caption(
    "Eksplorasi bivariat & multivariat untuk menemukan ketimpangan antar daerah, "
    "anomali rasio, dan red flags kualitas pelaporan."
)

with st.expander("ℹ️ Tentang dataset ini", expanded=False):
    st.markdown(
        f"""
        - Dataset berisi **{df_raw.shape[0]:,} baris** laporan pada level **kecamatan**,
          mencakup **{df_raw['provinsi_clean'].nunique()} provinsi** (bukan 39 — beberapa provinsi
          di Indonesia belum/tidak terwakili dalam data ini, lihat tab **Red Flags**).
        - Data berasal dari **{df_raw['__source_file'].nunique()} file sumber berbeda** yang digabung,
          sehingga kelengkapan pelaporan antar provinsi sangat tidak seragam.
        - Terdeteksi **{int(df_raw['is_duplicate_row'].sum())} baris duplikat persis** — ini bisa jadi
          indikasi double-input data, bukan klaim ganda anggaran (perlu verifikasi manual ke sumber asli).
        """
    )

# ---------------------------------------------------------------------------
# Sidebar — filter & kontrol level granularitas (toggle provinsi/kab-kota/kecamatan)
# ---------------------------------------------------------------------------
st.sidebar.header("⚙️ Kontrol Data")

level = st.sidebar.radio(
    "Level agregasi",
    options=["provinsi", "kabupaten_kota", "kecamatan"],
    format_func=lambda x: {"provinsi": "Provinsi", "kabupaten_kota": "Kabupaten/Kota", "kecamatan": "Kecamatan"}[x],
    help="Mengatur granularitas seluruh dashboard. Level kecamatan = paling detail, provinsi = paling ringkas.",
)

jenjang_opts = sorted(df_raw["jenjang"].unique().tolist())
jenjang_sel = st.sidebar.multiselect("Jenjang pendidikan", jenjang_opts, default=jenjang_opts)

prov_opts = sorted(df_raw["provinsi_clean"].unique().tolist())
prov_sel = st.sidebar.multiselect("Provinsi (kosongkan = semua)", prov_opts, default=[])

# Terapkan filter ke data baris-mentah sebelum diagregasi
df_filtered = df_raw[df_raw["jenjang"].isin(jenjang_sel)]
if prov_sel:
    df_filtered = df_filtered[df_filtered["provinsi_clean"].isin(prov_sel)]

if df_filtered.empty:
    st.warning("Tidak ada data untuk kombinasi filter ini. Coba ubah filter di sidebar.")
    st.stop()

df_agg = aggregate_by_level(df_filtered, level)

# Hitung flag & skor anomali pada data baris-mentah (sebelum agregasi) agar deteksi tetap presisi
df_scored = compute_anomaly_flags(df_filtered)
df_scored = compute_anomaly_score(df_scored)

st.sidebar.markdown("---")
st.sidebar.metric("Jumlah baris ditampilkan", f"{df_agg.shape[0]:,}")
st.sidebar.metric("Total penerima manfaat", f"{int(df_filtered['jumlah_penerima_manfaat'].sum()):,}")

with st.expander("⚖️ Penting dibaca sebelum lanjut: dasar metodologi & batasan", expanded=False):
    st.markdown(
        """
        **Skor anomali & hipotesis di dashboard ini bersifat statistik deskriptif, bukan tuduhan atau kesimpulan hukum.**

        - Skor dihitung dari seberapa jauh suatu data menyimpang dari pola umum (outlier statistik), bukan dari bukti investigasi.
        - Setiap anomali punya beberapa kemungkinan penyebab yang SAH (kesalahan input, karakteristik wilayah/sekolah, kualitas pencatatan)
          — ini selalu ditampilkan lebih dulu sebelum hipotesis yang "memerlukan verifikasi lebih lanjut".
        - Hipotesis terkait potensi kecurangan/korupsi adalah **salah satu dari beberapa kemungkinan**, ditempatkan terakhir,
          dan **tidak pernah** disajikan sebagai kesimpulan akhir.
        - Sebelum menyebarluaskan temuan apa pun dari dashboard ini ke publik, **verifikasi ke sumber data resmi/instansi terkait** dulu.
        """
    )

LEVEL_LABEL = {"provinsi": "Provinsi", "kabupaten_kota": "Kabupaten/Kota", "kecamatan": "Kecamatan"}[level]

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview", "🔍 Eksplorasi Bivariat", "🕸️ Eksplorasi Multivariat", "🚩 Red Flags & Kualitas Data"
])

# ===========================================================================
# TAB 1 — OVERVIEW
# ===========================================================================
with tab1:
    st.markdown(
        """
        > 📢 **Yang perlu disampaikan di bagian ini:** "Program MBG menjangkau sekian penerima manfaat di seluruh
        > Indonesia — tapi distribusinya tidak rata. Sebagian kecil daerah menerima porsi sangat besar, sementara
        > banyak daerah lain hanya kebagian sedikit. Inilah gambaran ketimpangannya."
        """
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Penerima Manfaat", f"{int(df_agg['jumlah_penerima_manfaat'].sum()):,}")
    c2.metric("Total Satuan Pendidikan", f"{int(df_agg['jumlah_satuan_pendidikan'].sum()):,}")
    c3.metric(f"Jumlah {LEVEL_LABEL} Tercakup", f"{df_agg.shape[0]:,}")
    gini_now = gini_coefficient(df_agg["jumlah_penerima_manfaat"].values)
    c4.metric("Gini Index Distribusi Penerima", f"{gini_now:.3f}", help="0 = merata sempurna, 1 = sangat timpang")

    st.markdown(f"#### Peringkat {LEVEL_LABEL} berdasarkan Total Penerima Manfaat")
    top_n = st.slider("Tampilkan Top-N", 5, min(50, df_agg.shape[0]), min(15, df_agg.shape[0]))
    df_top = df_agg.sort_values("jumlah_penerima_manfaat", ascending=False).head(top_n)
    fig_bar = px.bar(
        df_top, x="jumlah_penerima_manfaat", y="label", orientation="h",
        color="jumlah_penerima_manfaat", color_continuous_scale="Reds",
        labels={"jumlah_penerima_manfaat": "Total Penerima Manfaat", "label": LEVEL_LABEL},
        height=max(350, top_n * 28),
    )
    fig_bar.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
    st.plotly_chart(fig_bar, width='stretch')

    st.markdown(f"#### Kurva Lorenz — Ketimpangan Distribusi Penerima Manfaat antar {LEVEL_LABEL}")
    sorted_vals = np.sort(df_agg["jumlah_penerima_manfaat"].values)
    cum_vals = np.cumsum(sorted_vals) / sorted_vals.sum()
    cum_pop = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
    fig_lorenz = go.Figure()
    fig_lorenz.add_trace(go.Scatter(x=cum_pop, y=cum_vals, mode="lines", name="Distribusi aktual", fill="tozeroy"))
    fig_lorenz.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Garis pemerataan sempurna", line=dict(dash="dash")))
    fig_lorenz.update_layout(
        xaxis_title=f"Kumulatif % {LEVEL_LABEL}", yaxis_title="Kumulatif % Penerima Manfaat", height=420
    )
    st.plotly_chart(fig_lorenz, width='stretch')
    st.caption(
        f"Semakin jauh kurva merah dari garis putus-putus, semakin timpang distribusi penerima manfaat "
        f"antar-{LEVEL_LABEL.lower()}. Gini index saat ini: **{gini_now:.3f}**."
    )
    st.success(
        "➡️ **Transisi ke tab berikutnya:** \"Sekarang kita sudah lihat *seberapa timpang* datanya. "
        "Pertanyaan selanjutnya: apakah ketimpangan ini wajar (misalnya karena jumlah sekolah/penduduk "
        "yang memang berbeda), atau ada pola yang aneh? Mari kita cek hubungan antar variabel.\""
    )

# ===========================================================================
# TAB 2 — EKSPLORASI BIVARIAT
# ===========================================================================
with tab2:
    st.markdown(
        """
        > 📢 **Yang perlu disampaikan di bagian ini:** "Sekarang kita cek hubungan dua variabel sekaligus —
        > misalnya, apakah jumlah sekolah berbanding lurus dengan jumlah penerima manfaat? Kalau ada titik yang
        > melenceng jauh dari pola umum (garis tren), itu sinyal pertama untuk digali lebih dalam."
        """
    )

    st.markdown("#### Scatter Plot Dinamis: Pilih 2 Variabel untuk Dieksplorasi")

    numeric_options = [
        "jumlah_penerima_manfaat", "jumlah_satuan_pendidikan", "jumlah_laki", "jumlah_perempuan",
        "jumlah_kondisi_khusus", "jumlah_satpen_negeri", "jumlah_satpen_swasta",
        "rasio_penerima_per_satpen", "rasio_gender_LP", "pct_kondisi_khusus", "pct_swasta",
    ]
    label_map = {
        "jumlah_penerima_manfaat": "Total Penerima Manfaat",
        "jumlah_satuan_pendidikan": "Jumlah Satuan Pendidikan",
        "jumlah_laki": "Jumlah Laki-laki",
        "jumlah_perempuan": "Jumlah Perempuan",
        "jumlah_kondisi_khusus": "Jumlah Kondisi Khusus",
        "jumlah_satpen_negeri": "Jumlah Satpen Negeri",
        "jumlah_satpen_swasta": "Jumlah Satpen Swasta",
        "rasio_penerima_per_satpen": "Rasio Penerima / Satpen",
        "rasio_gender_LP": "Rasio Gender (L/P)",
        "pct_kondisi_khusus": "% Kondisi Khusus",
        "pct_swasta": "% Sekolah Swasta",
    }

    colA, colB, colC = st.columns(3)
    with colA:
        x_var = st.selectbox("Variabel X", numeric_options, index=1, format_func=lambda x: label_map[x])
    with colB:
        y_var = st.selectbox("Variabel Y", numeric_options, index=0, format_func=lambda x: label_map[x])
    with colC:
        log_scale = st.checkbox("Skala log (X & Y)", value=True, help="Membantu jika rentang nilai sangat lebar")

    size_var = st.selectbox(
        "Ukuran titik berdasarkan (opsional)", ["(seragam)"] + numeric_options,
        format_func=lambda x: label_map.get(x, x),
    )

    fig_scatter = px.scatter(
        df_agg, x=x_var, y=y_var,
        size=None if size_var == "(seragam)" else size_var,
        color="provinsi_clean" if level != "provinsi" else None,
        hover_name="label",
        hover_data={c: True for c in numeric_options},
        log_x=log_scale, log_y=log_scale,
        labels={x_var: label_map[x_var], y_var: label_map[y_var]},
        height=520,
        trendline="ols",
    )
    st.plotly_chart(fig_scatter, width='stretch')

    corr_val = df_agg[[x_var, y_var]].replace([np.inf, -np.inf], np.nan).dropna().corr().iloc[0, 1]
    st.info(
        f"📈 Korelasi Pearson antara **{label_map[x_var]}** dan **{label_map[y_var]}**: **{corr_val:.3f}** "
        f"— {'korelasi cukup kuat' if abs(corr_val) > 0.5 else 'korelasi lemah'}."
    )

    st.markdown("#### Distribusi per Provinsi (Box Plot)")
    box_var = st.selectbox("Variabel untuk box plot", numeric_options, index=numeric_options.index("rasio_penerima_per_satpen"), format_func=lambda x: label_map[x], key="box_var")
    fig_box = px.box(
        df_filtered, x="provinsi_clean", y=box_var, points="outliers",
        labels={"provinsi_clean": "Provinsi", box_var: label_map[box_var]},
        height=500,
    )
    fig_box.update_xaxes(categoryorder="median descending", tickangle=45)
    st.plotly_chart(fig_box, width='stretch')
    st.caption("Box plot dihitung dari data level kecamatan (mentah) agar variasi internal tiap provinsi terlihat, terlepas dari level agregasi yang dipilih di sidebar.")
    st.success(
        "➡️ **Transisi ke tab berikutnya:** \"Membandingkan dua variabel saja kadang belum cukup. "
        "Yuk lihat banyak variabel sekaligus — apakah ada provinsi atau wilayah dengan profil yang "
        "benar-benar berbeda dari mayoritas?\""
    )

# ===========================================================================
# TAB 3 — EKSPLORASI MULTIVARIAT
# ===========================================================================
with tab3:
    st.markdown(
        """
        > 📢 **Yang perlu disampaikan di bagian ini:** "Sekarang kita lihat pola gabungan dari banyak variabel
        > sekaligus. Tujuannya: menemukan kelompok wilayah dengan 'profil' yang berbeda dari mayoritas —
        > ini sering jadi titik awal untuk pertanyaan investigatif yang lebih spesifik."
        """
    )

    st.markdown("#### Correlation Heatmap Antar Metrik")
    corr_matrix = df_agg[numeric_options].replace([np.inf, -np.inf], np.nan).fillna(0).corr()
    fig_heat = px.imshow(
        corr_matrix, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
        labels=dict(color="Korelasi"), height=520,
        x=[label_map[c] for c in corr_matrix.columns], y=[label_map[c] for c in corr_matrix.columns],
    )
    st.plotly_chart(fig_heat, width='stretch')
    st.caption("Cari pasangan metrik dengan korelasi tinggi (merah/biru tua) — ini sering jadi titik awal untuk pertanyaan 'kenapa dua hal ini berhubungan?'")

    st.markdown("---")
    st.markdown(f"#### Parallel Coordinates — Bandingkan Beberapa {LEVEL_LABEL} Sekaligus")
    default_n = min(10, df_agg.shape[0])
    top_for_pc = df_agg.sort_values("jumlah_penerima_manfaat", ascending=False).head(30)["label"].tolist()
    pc_sel = st.multiselect(
        f"Pilih {LEVEL_LABEL.lower()} (default: top 10 by penerima manfaat)",
        df_agg["label"].tolist(), default=top_for_pc[:default_n],
    )
    pc_vars = st.multiselect(
        "Variabel yang dibandingkan",
        numeric_options,
        default=["jumlah_penerima_manfaat", "jumlah_satuan_pendidikan", "rasio_penerima_per_satpen", "pct_kondisi_khusus", "pct_swasta"],
        format_func=lambda x: label_map[x],
    )
    if pc_sel and len(pc_vars) >= 2:
        df_pc = df_agg[df_agg["label"].isin(pc_sel)].copy()
        # Normalisasi 0-1 per kolom agar skala berbeda tetap sebanding secara visual
        df_pc_norm = df_pc.copy()
        for v in pc_vars:
            vmin, vmax = df_agg[v].min(), df_agg[v].max()
            df_pc_norm[v] = (df_pc[v] - vmin) / (vmax - vmin + 1e-9)

        fig_pc = go.Figure(data=go.Parcoords(
            line=dict(color=df_pc_norm[pc_vars[0]], colorscale="Viridis"),
            dimensions=[
                dict(label=label_map[v], values=df_pc_norm[v], tickvals=[0, 0.5, 1],
                     ticktext=[f"{df_pc[v].min():.1f}", f"{df_pc[v].median():.1f}", f"{df_pc[v].max():.1f}"])
                for v in pc_vars
            ],
        ))
        fig_pc.update_layout(height=480)
        st.plotly_chart(fig_pc, width='stretch')
        st.caption("Setiap garis = satu entitas. Garis yang melompat drastis antar sumbu menandakan profil yang tidak konsisten (misal: penerima tinggi tapi satpen sedikit).")
    else:
        st.info("Pilih minimal 2 variabel dan 1 entitas untuk menampilkan grafik.")

    st.markdown("---")
    st.markdown("#### Radar Chart — Profil Multivariat per Entitas")
    radar_vars = st.multiselect(
        "Variabel untuk radar chart", numeric_options,
        default=["rasio_penerima_per_satpen", "pct_kondisi_khusus", "pct_swasta", "rasio_gender_LP"],
        format_func=lambda x: label_map[x], key="radar_vars",
    )
    radar_entities = st.multiselect(
        f"Pilih {LEVEL_LABEL.lower()} untuk dibandingkan (maks 6 agar tetap terbaca)",
        df_agg["label"].tolist(), default=top_for_pc[:3], max_selections=6, key="radar_entities",
    )
    if radar_vars and radar_entities:
        fig_radar = go.Figure()
        for ent in radar_entities:
            row = df_agg[df_agg["label"] == ent].iloc[0]
            vals = []
            for v in radar_vars:
                vmin, vmax = df_agg[v].min(), df_agg[v].max()
                vals.append((row[v] - vmin) / (vmax - vmin + 1e-9))
            fig_radar.add_trace(go.Scatterpolar(r=vals + [vals[0]], theta=[label_map[v] for v in radar_vars] + [label_map[radar_vars[0]]], name=ent, fill="toself"))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), height=500, showlegend=True)
        st.plotly_chart(fig_radar, width='stretch')
        st.caption("Nilai dinormalisasi 0–1 relatif terhadap seluruh data pada level yang dipilih, agar bentuk radar antar entitas bisa dibandingkan langsung.")

    st.markdown("---")
    st.markdown("#### Clustering — Kelompok Provinsi dengan Profil Mirip (K-Means)")
    st.caption("Mengelompokkan entitas berdasarkan kemiripan rasio, untuk menemukan kelompok 'anomali' yang berbeda dari mayoritas.")
    cluster_vars = ["rasio_penerima_per_satpen", "pct_kondisi_khusus", "pct_swasta", "rasio_gender_LP"]
    k = st.slider("Jumlah cluster (K)", 2, 6, 3)
    df_cluster = df_agg[["label"] + cluster_vars].replace([np.inf, -np.inf], np.nan).dropna()
    if df_cluster.shape[0] >= k:
        X = StandardScaler().fit_transform(df_cluster[cluster_vars])
        km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X)
        df_cluster["cluster"] = km.labels_.astype(str)

        pca_vars_for_plot = cluster_vars[:2]
        fig_cluster = px.scatter(
            df_cluster, x=pca_vars_for_plot[0], y=pca_vars_for_plot[1], color="cluster",
            hover_name="label", labels={v: label_map[v] for v in pca_vars_for_plot},
            height=480, title=f"Cluster berdasarkan {label_map[pca_vars_for_plot[0]]} vs {label_map[pca_vars_for_plot[1]]}",
        )
        st.plotly_chart(fig_cluster, width='stretch')

        with st.expander("Lihat anggota tiap cluster"):
            for c in sorted(df_cluster["cluster"].unique()):
                members = df_cluster[df_cluster["cluster"] == c]["label"].tolist()
                st.markdown(f"**Cluster {c}** ({len(members)} entitas): {', '.join(members[:25])}{' ...' if len(members) > 25 else ''}")

        st.success(
            "➡️ **Transisi ke tab berikutnya:** \"Cluster yang menyendiri (jumlah anggota sedikit, jauh dari "
            "kelompok besar) adalah kandidat utama untuk diperiksa lebih detail. Sekarang kita masuk ke bagian "
            "yang paling konkret: skor anomali per entitas, lengkap dengan kemungkinan penyebabnya.\""
        )
    else:
        st.warning("Tidak cukup data untuk clustering dengan filter saat ini.")

# ===========================================================================
# TAB 4 — RED FLAGS & KUALITAS DATA
# ===========================================================================
with tab4:
    st.markdown(
        """
        > 📢 **Yang perlu disampaikan di bagian ini:** "Sekarang kita bedah satu per satu entitas yang
        > skornya paling tinggi. Untuk setiap anomali, kita TIDAK langsung simpulkan kecurangan — kita
        > lihat dulu semua kemungkinan penyebab yang masuk akal, baru di urutan terakhir kita catat
        > kemungkinan yang perlu diverifikasi lebih lanjut ke instansi terkait."
        """
    )
    st.markdown("### 🚩 Indikator Red Flags & Kualitas Pelaporan")
    st.caption("Bagian ini TIDAK menyimpulkan adanya korupsi/kecurangan — hanya menyoroti pola data yang layak diverifikasi lebih lanjut ke sumber resmi.")

    st.markdown("---")
    st.markdown("#### 0. Skor Anomali Komposit & Hipotesis Penyebab")
    st.caption(
        "Skor 0-100 dihitung dari gabungan beberapa sinyal (duplikasi, rasio ekstrem, anomali gender, dst). "
        "Semakin tinggi skor, semakin banyak sinyal yang terpicu bersamaan — bukan ukuran kepastian kecurangan."
    )

    sc1, sc2, sc3 = st.columns(3)
    n_tinggi = int((df_scored["kategori_risiko"] == "Tinggi").sum())
    n_sedang = int((df_scored["kategori_risiko"] == "Sedang").sum())
    n_rendah = int((df_scored["kategori_risiko"] == "Rendah").sum())
    sc1.metric("🟢 Risiko Rendah", f"{n_rendah:,} baris")
    sc2.metric("🟡 Risiko Sedang", f"{n_sedang:,} baris")
    sc3.metric("🔴 Risiko Tinggi", f"{n_tinggi:,} baris")

    fig_score_dist = px.histogram(
        df_scored, x="skor_anomali", color="kategori_risiko", nbins=20,
        color_discrete_map={"Rendah": "#4CAF50", "Sedang": "#FFC107", "Tinggi": "#D64550"},
        labels={"skor_anomali": "Skor Anomali", "count": "Jumlah Baris"}, height=350,
    )
    st.plotly_chart(fig_score_dist, width='stretch')

    st.markdown("##### 🔎 Bedah Entitas dengan Skor Tertinggi")
    df_scored_disp = df_scored.copy()
    df_scored_disp["entitas_label"] = (
        df_scored_disp["kecamatan_clean"] + ", " + df_scored_disp["kabkota_clean"]
        + " — " + df_scored_disp["provinsi_clean"] + " (" + df_scored_disp["jenjang"] + ")"
    )
    top_n_score = st.slider("Tampilkan berapa entitas teratas?", 5, 30, 10, key="top_n_score")
    top_scored = df_scored_disp.nlargest(top_n_score, "skor_anomali")

    pilihan_entitas = st.selectbox(
        "Pilih entitas untuk lihat detail hipotesis", top_scored["entitas_label"].tolist(),
    )
    row_detail = df_scored_disp[df_scored_disp["entitas_label"] == pilihan_entitas].iloc[0]

    st.markdown(f"**{pilihan_entitas}** — Skor Anomali: **{row_detail['skor_anomali']:.0f}/100** ({row_detail['kategori_risiko']})")
    hyps = get_triggered_hypotheses(row_detail)
    if hyps:
        for h in hyps:
            with st.expander(f"⚠️ {h['judul']}", expanded=False):
                st.caption(h["deskripsi"])
                st.markdown("**Kemungkinan penyebab (urut dari paling umum):**")
                for i, hipotesis_text in enumerate(h["hipotesis"], 1):
                    if i == len(h["hipotesis"]):
                        st.warning(f"{i}. {hipotesis_text}")
                    else:
                        st.markdown(f"{i}. {hipotesis_text}")
    else:
        st.success("Tidak ada flag anomali signifikan terpicu untuk entitas ini.")

    with st.expander("📋 Lihat tabel lengkap entitas berisiko tertinggi"):
        st.dataframe(
            top_scored[["entitas_label", "skor_anomali", "kategori_risiko", "jumlah_penerima_manfaat", "jumlah_satuan_pendidikan"]]
            .rename(columns={"entitas_label": "Entitas", "skor_anomali": "Skor", "kategori_risiko": "Kategori",
                              "jumlah_penerima_manfaat": "Penerima", "jumlah_satuan_pendidikan": "Jml Satpen"}),
            hide_index=True, width='stretch',
        )

    r1, r2, r3, r4 = st.columns(4)
    n_dup = int(df_filtered["is_duplicate_row"].sum())
    r1.metric("Baris Duplikat Persis", f"{n_dup}", help="Baris dengan seluruh kolom identik — potensi double-input")
    n_missing_date = int(df_filtered["date_pull_parsed"].isna().sum())
    r2.metric("Baris Tanpa Timestamp Valid", f"{n_missing_date}")
    n_prov_all = 38  # jumlah provinsi resmi Indonesia per data terakhir (termasuk DOB Papua & lainnya)
    n_prov_present = df_raw["provinsi_clean"].nunique()
    r3.metric("Provinsi Tercakup", f"{n_prov_present} / {n_prov_all}", help="Provinsi resmi yang tidak muncul sama sekali di dataset ini")
    outlier_mask = detect_outliers_iqr(df_filtered["rasio_penerima_per_satpen"])
    r4.metric("Baris Outlier Rasio Ekstrem", f"{int(outlier_mask.sum())}")

    st.markdown("---")
    st.markdown("#### 1. Provinsi dengan Volume Laporan Sangat Tidak Seimbang")
    rep_count = df_raw.groupby("provinsi_clean").size().sort_values(ascending=False)
    fig_rep = px.bar(
        x=rep_count.values, y=rep_count.index, orientation="h",
        labels={"x": "Jumlah Baris Laporan", "y": "Provinsi"}, height=700,
        color=rep_count.values, color_continuous_scale="Oranges",
    )
    fig_rep.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
    st.plotly_chart(fig_rep, width='stretch')
    st.caption(
        f"Provinsi dengan baris laporan sangat sedikit (mis. hanya 1) bukan berarti pelaksanaan MBG di sana kecil — "
        f"bisa jadi datanya memang belum lengkap terkumpul/digabung dalam dataset ini."
    )

    st.markdown("---")
    st.markdown("#### 2. Entitas dengan Rasio Penerima/Satpen Paling Ekstrem (Atas & Bawah)")
    df_rasio_sorted = df_filtered.copy()
    df_rasio_sorted["entitas"] = df_rasio_sorted["kecamatan_clean"] + ", " + df_rasio_sorted["kabkota_clean"] + " — " + df_rasio_sorted["provinsi_clean"]
    top_high = df_rasio_sorted.nlargest(10, "rasio_penerima_per_satpen")[["entitas", "jenjang", "jumlah_penerima_manfaat", "jumlah_satuan_pendidikan", "rasio_penerima_per_satpen"]]
    top_low = df_rasio_sorted[df_rasio_sorted["jumlah_satuan_pendidikan"] > 0].nsmallest(10, "rasio_penerima_per_satpen")[["entitas", "jenjang", "jumlah_penerima_manfaat", "jumlah_satuan_pendidikan", "rasio_penerima_per_satpen"]]

    cL, cR = st.columns(2)
    with cL:
        st.markdown("**Rasio tertinggi** (1 satpen menanggung sangat banyak penerima)")
        st.dataframe(top_high.rename(columns={
            "entitas": "Lokasi", "jenjang": "Jenjang", "jumlah_penerima_manfaat": "Penerima",
            "jumlah_satuan_pendidikan": "Jml Satpen", "rasio_penerima_per_satpen": "Rasio"
        }), hide_index=True, width='stretch')
    with cR:
        st.markdown("**Rasio terendah** (satpen banyak, penerima sedikit)")
        st.dataframe(top_low.rename(columns={
            "entitas": "Lokasi", "jenjang": "Jenjang", "jumlah_penerima_manfaat": "Penerima",
            "jumlah_satuan_pendidikan": "Jml Satpen", "rasio_penerima_per_satpen": "Rasio"
        }), hide_index=True, width='stretch')

    st.markdown("---")
    st.markdown("#### 3. Baris Duplikat Persis (Layak Diverifikasi)")
    if n_dup > 0:
        dup_rows = df_filtered[df_filtered["is_duplicate_row"]][
            ["provinsi_clean", "kabkota_clean", "kecamatan_clean", "jenjang", "jumlah_penerima_manfaat", "__source_file"]
        ].sort_values(["provinsi_clean", "kabkota_clean", "kecamatan_clean"])
        st.dataframe(dup_rows.rename(columns={
            "provinsi_clean": "Provinsi", "kabkota_clean": "Kab/Kota", "kecamatan_clean": "Kecamatan",
            "jenjang": "Jenjang", "jumlah_penerima_manfaat": "Penerima", "__source_file": "File Sumber"
        }), hide_index=True, width='stretch', height=300)
    else:
        st.success("Tidak ada baris duplikat persis pada filter saat ini.")

    st.markdown("---")
    st.markdown("#### 4. Anomali Rasio Gender Ekstrem")
    st.caption("Rasio Laki/Perempuan yang jauh dari ~1.0 bisa jadi wajar (jenjang SMK tertentu, pesantren, dll) tapi tetap layak dicek konteksnya.")
    gender_outlier = df_filtered[(df_filtered["rasio_gender_LP"] > 3) | (df_filtered["rasio_gender_LP"] < 0.33)]
    gender_outlier_disp = gender_outlier[["provinsi_clean", "kabkota_clean", "kecamatan_clean", "jenjang", "jumlah_laki", "jumlah_perempuan", "rasio_gender_LP"]].sort_values("rasio_gender_LP", ascending=False)
    st.dataframe(gender_outlier_disp.rename(columns={
        "provinsi_clean": "Provinsi", "kabkota_clean": "Kab/Kota", "kecamatan_clean": "Kecamatan", "jenjang": "Jenjang",
        "jumlah_laki": "Laki-laki", "jumlah_perempuan": "Perempuan", "rasio_gender_LP": "Rasio L/P"
    }), hide_index=True, width='stretch', height=300)
    st.caption(f"Ditemukan {gender_outlier.shape[0]} baris dengan rasio gender di luar rentang wajar (>3x atau <0.33x).")

    st.markdown("---")
    st.info(
        "🎯 **Kalimat penutup presentasi yang disarankan:** \"Dari eksplorasi ini, kita menemukan beberapa "
        "entitas dengan pola data yang menyimpang signifikan dari mayoritas. Ini bukan bukti kecurahan — "
        "ini adalah daftar prioritas untuk diverifikasi lebih lanjut ke dinas/instansi terkait. Langkah "
        "selanjutnya yang disarankan: konfirmasi data riil di lapangan untuk entitas-entitas skor tertinggi.\""
    )

st.markdown("---")
st.caption(
    "Dashboard ini dibuat untuk eksplorasi data terbuka program MBG. Semua temuan di sini bersifat "
    "deskriptif/statistik, bukan kesimpulan hukum — perlu diverifikasi ke sumber data resmi sebelum disebarluaskan."
)
