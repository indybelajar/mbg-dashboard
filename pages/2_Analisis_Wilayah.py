import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import gini_coefficient
from utils.filters import render_global_filters, get_satpen_column
from utils.province_coords import get_coords_df

# Wide layout
st.set_page_config(page_title="Fitur 2: Analisis Wilayah", page_icon=None, layout="wide")

# ---------------------------------------------------------------------------
# Minimal Header
# ---------------------------------------------------------------------------
st.title("Analisis Wilayah")
st.markdown("Distribusi geografis penerima manfaat & satuan pendidikan.")

df, tipe_sekolah = render_global_filters()
satpen_col = get_satpen_column(tipe_sekolah)

# ---------------------------------------------------------------------------
# Level Granularity Selection
# ---------------------------------------------------------------------------
col_radio, col_space = st.columns([1, 4])
with col_radio:
    level = st.radio("Level", ["Provinsi", "Kabupaten/Kota"], horizontal=True, key="level_wilayah")

group_col = "provinsi_clean" if level == "Provinsi" else "kabkota_clean"

# Data Aggregation
agg = df.groupby(group_col, as_index=False).agg(
    jumlah_penerima_manfaat=("jumlah_penerima_manfaat", "sum"),
    jumlah_satuan_pendidikan=(satpen_col, "sum"),
    jumlah_kondisi_khusus=("jumlah_kondisi_khusus", "sum"),
    n_kecamatan=("kecamatan_clean", "nunique"),
)

if level == "Kabupaten/Kota":
    prov_lookup = df.drop_duplicates("kabkota_clean").set_index("kabkota_clean")["provinsi_clean"]
    agg["provinsi_clean"] = agg["kabkota_clean"].map(prov_lookup)

st.markdown("---")

# ---------------------------------------------------------------------------
# TOP ROW: Map + Lorenz Curve
# ---------------------------------------------------------------------------
col_map, col_lorenz = st.columns([2, 1])

with col_map:
    st.subheader(f"Persebaran per {level}")
    if level == "Provinsi":
        coords = get_coords_df(agg["provinsi_clean"].tolist())
        agg["lat"] = agg["provinsi_clean"].map(lambda p: coords.get(p, (None, None))[0])
        agg["lon"] = agg["provinsi_clean"].map(lambda p: coords.get(p, (None, None))[1])
        map_df = agg.dropna(subset=["lat", "lon"])

        fig_map = px.scatter_geo(
            map_df, lat="lat", lon="lon", size="jumlah_penerima_manfaat", color="jumlah_penerima_manfaat",
            hover_name="provinsi_clean", color_continuous_scale="Blues", size_max=45,
            labels={"jumlah_penerima_manfaat": "Penerima"}, height=320, 
            hover_data={"jumlah_satuan_pendidikan": ":.0f", "jumlah_kondisi_khusus": ":.0f", "lat": False, "lon": False},
        )
        fig_map.update_geos(scope="asia", center={"lat": -2.5, "lon": 118}, projection_scale=4,
                            showcountries=True, countrycolor="#e5e7eb", showland=True, landcolor="#f3f4f6")
        fig_map.update_layout(margin=dict(l=0, r=0, t=20, b=0), coloraxis_colorbar=dict(title="Jml"))
        st.plotly_chart(fig_map, use_container_width=True)
        
        # INSIGHT & HIPOTESIS (Why) dalam Popover
        insight_col, why_col = st.columns(2)
        with insight_col:
            with st.popover("Insight"):
                st.markdown(f"**Konsentrasi Penerima:** Ukuran titik mencerminkan volume penerima. Terlihat jelas bahwa wilayah di Pulau Jawa dan Sumatera bagian utara memiliki konsentrasi penerima manfaat tertinggi.")
        with why_col:
            with st.popover("Why? (Hipotesis)"):
                st.markdown("""
                **Mengapa demikian?** 
                - **Faktor Demografi:** Pulau Jawa dan Sumatera memiliki kepadatan penduduk tertinggi. 
                - **Infrastruktur:** Akses distribusi logistik (rantai pasok) jauh lebih matang di wilayah barat Indonesia dibandingkan wilayah timur.
                - **Kebijakan:** Tahap awal implementasi program mungkin diprioritaskan pada wilayah dengan akses mudah untuk meminimalisir risiko gagal distribusi.
                """)
    else:
        st.info("Peta titik hanya tersedia di level Provinsi.")

with col_lorenz:
    st.subheader("Kurva Lorenz")
    sorted_vals = np.sort(agg["jumlah_penerima_manfaat"].values)
    cum_vals = np.cumsum(sorted_vals) / sorted_vals.sum()
    cum_pop = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
    gini_now = gini_coefficient(agg["jumlah_penerima_manfaat"].values)

    fig_lorenz = go.Figure()
    fig_lorenz.add_trace(go.Scatter(x=cum_pop, y=cum_vals, mode="lines", name="Aktual", fill="tozeroy", line=dict(color="#6366f1", width=2)))
    fig_lorenz.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Sempurna", line=dict(dash="dash", color="#9ca3af")))
    fig_lorenz.update_layout(
        xaxis_title="% Wilayah", yaxis_title="% Penerima", height=320,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
        margin=dict(l=0, r=0, t=20, b=0)
    )
    st.plotly_chart(fig_lorenz, use_container_width=True)
    st.metric("Koefisien Gini", f"{gini_now:.3f}")

    # INSIGHT & HIPOTESIS (Why) dalam Popover
    insight_col, why_col = st.columns(2)
    with insight_col:
        with st.popover("Insight"):
            if gini_now > 0.5:
                st.warning("Ketimpangan distribusi tinggi. Sebagian kecil wilayah menyerap porsi penerima manfaat yang sangat besar.")
            elif gini_now > 0.3:
                st.info("Ketimpangan sedang. Distribusi terkonsentrasi pada beberapa wilayah utama.")
            else:
                st.success("Distribusi relatif merata.")
    with why_col:
        with st.popover("Why? (Hipotesis)"):
            st.markdown(f"""
            **Mengapa terjadi ketimpangan?**
            - **Ketimpangan Ekonomi Dasar:** {level} dengan infrastruktur kesehatan dan pendidikan yang lebih baik cenderung memiliki data penerima yang lebih lengkap.
            - **Kebijakan Alokasi:** Karena program MBG terbatas pada anggaran awal, pengambilan keputusan mungkin masih bersifat *target-based* (berfokus pada wilayah berpenduduk padat) daripada *need-based*.
            - **Data Validasi:** Wilayah terpencil mungkin memiliki jumlah penerima yang terlihat kecil karena keterlambatan validasi data ke pusat.
            """)

st.markdown("---")

# ---------------------------------------------------------------------------
# BOTTOM ROW: Ranking, Scatter, & Table
# ---------------------------------------------------------------------------
col_bar, col_scatter = st.columns([1, 1])

with col_bar:
    st.subheader("Peringkat Penerima Manfaat")
    top_n = 10 
    top_df = agg.sort_values("jumlah_penerima_manfaat", ascending=False).head(top_n)

    fig_bar = px.bar(
        top_df, x="jumlah_penerima_manfaat", y=group_col, orientation="h",
        color="jumlah_penerima_manfaat", color_continuous_scale="Viridis",
        labels={"jumlah_penerima_manfaat": "Penerima", group_col: level}, 
        height=350,
    )
    fig_bar.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False,
                          xaxis_title=None, yaxis_title=None, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # INSIGHT & HIPOTESIS (Why)
    insight_col, why_col = st.columns(2)
    with insight_col:
        with st.popover("Insight"):
            st.markdown(f"**Wilayah Dominan:** 10 besar {level.lower()} di atas menyumbang lebih dari 50% total penerima manfaat secara nasional.")
    with why_col:
        with st.popover("Why? (Hipotesis)"):
            st.markdown(f"""
            **Mengapa ini terjadi?**
            - **Urbanisasi:** {level} di atas umumnya merupakan daerah dengan tingkat urbanisasi tinggi (seperti DKI Jakarta, Jawa Barat, Jawa Timur).
            - **Kepadatan Sekolah:** Wilayah ini memiliki jumlah satuan pendidikan yang sangat banyak, sehingga *coverage* program MBG menjadi lebih luas secara otomatis.
            """)

with col_scatter:
    st.subheader("Kebutuhan vs Kapasitas")
    st.caption("Kondisi Khusus vs Jumlah Satpen")
    agg["rasio_kebutuhan_per_satpen"] = agg["jumlah_kondisi_khusus"] / agg["jumlah_satuan_pendidikan"].replace(0, np.nan)

    fig_scatter = px.scatter(
        agg, x="jumlah_satuan_pendidikan", y="jumlah_kondisi_khusus", size="jumlah_penerima_manfaat",
        hover_name=group_col, color="jumlah_penerima_manfaat", color_continuous_scale="Sunset",
        labels={"jumlah_satuan_pendidikan": "Jml Satpen", "jumlah_kondisi_khusus": "Jml Kebutuhan"},
        height=350,
        trendline="ols",
    )
    fig_scatter.update_layout(margin=dict(l=0, r=0, t=20, b=0), coloraxis_colorbar=dict(title="Penerima"))
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # INSIGHT & HIPOTESIS (Why)
    insight_col, why_col = st.columns(2)
    with insight_col:
        with st.popover("Insight"):
            st.markdown(f"**Korelasi Positif:** Terlihat garis tren yang naik — semakin banyak jumlah satuan pendidikan, semakin tinggi jumlah kasus kondisi khusus yang tercatat.")
    with why_col:
        with st.popover("Why? (Hipotesis)"):
            st.markdown("""
            **Mengapa korelasinya positif?**
            - **Efek Screening:** Wilayah dengan lebih banyak sekolah memiliki lebih banyak tenaga pengajar dan fasilitas untuk mendeteksi/melaporkan kondisi khusus (disabilitas, masalah gizi).
            - **Data Reporting:** Sekolah yang lebih banyak secara otomatis menghasilkan lebih banyak *entry point* data ke sistem MBG.
            - **Bukan berarti lebih parah:** Korelasi ini tidak serta merta membuktikan bahwa anak di daerah itu lebih banyak yang berkebutuhan khusus, tapi lebih kepada kapasitas deteksinya yang lebih tinggi.
            """)

st.markdown("---")
st.subheader("Wilayah Prioritas Intervensi")

# Show top 4
prioritas = agg.nlargest(4, "rasio_kebutuhan_per_satpen")[
    [group_col, "rasio_kebutuhan_per_satpen", "jumlah_kondisi_khusus", "jumlah_satuan_pendidikan"]
]

st.dataframe(
    prioritas.rename(columns={
        group_col: level, 
        "rasio_kebutuhan_per_satpen": "Rasio",
        "jumlah_kondisi_khusus": "Kebutuhan", 
        "jumlah_satuan_pendidikan": "Satpen"
    }),
    hide_index=True, 
    use_container_width=True,
    column_config={"Rasio": st.column_config.NumberColumn(format="%.2f")},
    height=160 
)

# INSIGHT & HIPOTESIS Utama
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight Prioritas"):
        st.markdown(f"**Sasaran Intervensi:** {level} dengan rasio tertinggi di atas adalah wilayah di mana kapasitas layanan (jumlah sekolah) sangat terbatas dibandingkan kebutuhan inklusif yang tercatat.")
with why_col:
    with st.popover("Why? (Hipotesis)"):
        st.markdown(f"""
        **Mengapa ini kandidat prioritas?**
        - **Beban Berat:** Satu sekolah di daerah tersebut harus menangani proporsi anak dengan kondisi khusus yang jauh lebih besar dari rata-rata nasional.
        - **Kesenjangan Sumber Daya:** Pelatihan guru dan alat bantu belajar inklusif di wilayah ini kemungkinan besar belum terdistribusi secara merata.
        - **Efek Domino:** Jika tidak segera diintervensi, beban sekolah yang terlalu tinggi dapat menurunkan kualitas pembelajaran secara menyeluruh.
        """)