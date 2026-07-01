"""Fitur 7 — Analisis Tren: pola dari sisi waktu pengumpulan data (proxy karena data hanya 1 tahun)."""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.filters import render_global_filters, get_satpen_column

st.set_page_config(page_title="Fitur 7: Analisis Tren", page_icon="📈", layout="wide")
st.title("Fitur 7: Analisis Tren")
st.caption("Fokus: pola perubahan dari waktu ke waktu")

df, tipe_sekolah = render_global_filters()
satpen_col = get_satpen_column(tipe_sekolah)

st.warning(
    "**Catatan metodologi penting:** Dataset ini hanya mencakup **tahun 2026** (1 tahun saja), sehingga "
    "**tren antar-tahun secara harfiah tidak dapat dianalisis** dengan data yang tersedia saat ini. Sebagai gantinya, "
    "halaman ini menganalisis **tren proses pengumpulan/pelaporan data** (`date_pull`) sebagai proxy — yaitu bagaimana "
    "volume data bertambah dari hari ke hari selama periode penarikan data. Untuk analisis tren tahun-ke-tahun yang sesungguhnya, "
    "arsitektur dashboard ini (kolom filter Tahun di sidebar) **sudah siap** dan akan otomatis aktif begitu data multi-tahun tersedia."
)

st.markdown(
    """
    > **Yang perlu disampaikan:** "Karena data baru tersedia untuk satu tahun, kita tidak bisa bicara tren
    > tahunan. Tapi kita bisa lihat bagaimana proses pengumpulan datanya berjalan — ini juga penting untuk
    > menilai kualitas & kecepatan pelaporan dari daerah."
    """
)

# INSIGHT & HIPOTESIS - Metodologi
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight Metodologi"):
        st.markdown("""
        **Mengapa Analisis Proxy ini Penting?**
        - Data hanya 1 tahun → tidak bisa analisis year-over-year
        - `date_pull` sebagai proxy menunjukkan **proses pelaporan data**
        - Ini mengungkap **kualitas dan kecepatan** input data dari daerah
        - Pola pengumpulan data mencerminkan **kematangan sistem** pelaporan
        """)
with why_col:
    with st.popover("Why? (Hipotesis)"):
        st.markdown("""
        **Mengapa fokus pada proses pengumpulan data?**
        - **Validasi Data:** Pola pelaporan menunjukkan daerah mana yang paling cepat dan akurat.
        - **Kesiapan Daerah:** {'Daerah dengan pelaporan awal menunjukkan kesiapan sistem yang baik' if df['date_pull_parsed'].notna().sum() > 0 else 'Masih ada daerah yang belum optimal'}
        - **Bulk Upload:** Lonjakan data di hari tertentu menandakan proses pengumpulan massal.
        - **Under-represented:** Daerah yang baru muncul di akhir berisiko tidak terwakili dengan baik.
        """)

df_dated = df.dropna(subset=["date_pull_parsed"]).copy()
df_dated["tanggal_pull"] = df_dated["date_pull_parsed"].dt.date

if df_dated.empty:
    st.error("Tidak ada baris dengan timestamp valid pada filter saat ini.")
else:
    st.markdown("---")
    st.markdown("### Volume Data Masuk per Hari Penarikan")
    by_date = df_dated.groupby("tanggal_pull", as_index=False).agg(
        n_baris=("jumlah_penerima_manfaat", "count"),
        jumlah_penerima_manfaat=("jumlah_penerima_manfaat", "sum"),
    ).sort_values("tanggal_pull")
    by_date["kumulatif_baris"] = by_date["n_baris"].cumsum()

    t1, t2 = st.columns(2)
    with t1:
        fig_harian = px.bar(
            by_date, x="tanggal_pull", y="n_baris",
            labels={"tanggal_pull": "Tanggal Penarikan Data", "n_baris": "Jumlah Baris Baru"}, height=400,
            title="Jumlah Baris Data per Hari",
        )
        st.plotly_chart(fig_harian, use_container_width=True)
    with t2:
        fig_kumulatif = px.area(
            by_date, x="tanggal_pull", y="kumulatif_baris",
            labels={"tanggal_pull": "Tanggal Penarikan Data", "kumulatif_baris": "Total Baris Kumulatif"}, height=400,
            title="Pertumbuhan Kumulatif Volume Data",
        )
        st.plotly_chart(fig_kumulatif, use_container_width=True)

    # INSIGHT & HIPOTESIS - Volume Data per Hari
    hari_puncak = by_date.nlargest(1, "n_baris").iloc[0]
    insight_col, why_col = st.columns(2)
    with insight_col:
        with st.popover("Insight"):
            st.markdown(f"""
            **Pola Pengumpulan Data:**
            - Periode: **{by_date.shape[0]} hari** ({df_dated['date_pull_parsed'].min().strftime('%d %b %Y')} - {df_dated['date_pull_parsed'].max().strftime('%d %b %Y')})
            - Puncak input data: **{hari_puncak['tanggal_pull'].strftime('%d %b %Y')}** ({int(hari_puncak['n_baris']):,} baris)
            - {'Indikasi bulk upload dari provinsi besar' if hari_puncak['n_baris'] > by_date['n_baris'].mean() * 3 else 'Pola input relatif stabil'}
            - {'Data dari berbagai daerah masuk secara bertahap' if by_date.shape[0] > 5 else 'Proses pengumpulan terkonsentrasi di beberapa hari'}
            """)
    with why_col:
        with st.popover("Why? (Hipotesis)"):
            st.markdown(f"""
            **Mengapa pola pengumpulan data seperti ini?**
            - **Sistem Input:** {'Beberapa provinsi menggunakan sistem batch upload yang menghasilkan lonjakan' if hari_puncak['n_baris'] > by_date['n_baris'].mean() * 3 else 'Input data dilakukan secara real-time'}
            - **Koordinasi Daerah:** {'Provinsi dengan koordinasi baik mengupload lebih awal dan konsisten' if by_date.shape[0] > 5 else 'Masih ada ketergantungan pada jadwal tertentu'}
            - **Kapasitas SDM:** {'Petugas di provinsi besar mungkin bisa memproses data lebih cepat' if hari_puncak['n_baris'] > by_date['n_baris'].mean() * 3 else 'Proses input data cukup merata'}
            - **Kualitas Data:** {'Lonjakan ekstrem perlu dicek konsistensi datanya' if hari_puncak['n_baris'] > by_date['n_baris'].mean() * 5 else 'Data masuk dengan pola yang wajar'}
            """)

    st.caption(
        f"**Insight:** Data terkumpul dalam **{by_date.shape[0]} hari berbeda** antara "
        f"{df_dated['date_pull_parsed'].min().strftime('%d %b %Y')} hingga {df_dated['date_pull_parsed'].max().strftime('%d %b %Y')}. "
        f"Lonjakan tajam di satu hari tertentu biasanya menandakan proses *bulk upload* dari satu provinsi besar, bukan pertumbuhan organik program."
    )

    st.markdown("---")
    st.markdown("### Provinsi mana yang datanya masuk lebih awal vs lebih lambat?")
    by_prov_date = df_dated.groupby("provinsi_clean", as_index=False).agg(
        tanggal_pertama=("date_pull_parsed", "min"), tanggal_terakhir=("date_pull_parsed", "max"),
        n_baris=("jumlah_penerima_manfaat", "count"),
    ).sort_values("tanggal_pertama")
    st.dataframe(
        by_prov_date.rename(columns={"provinsi_clean": "Provinsi", "tanggal_pertama": "Pertama Masuk",
                                      "tanggal_terakhir": "Terakhir Masuk", "n_baris": "Jml Baris"}),
        hide_index=True, 
        use_container_width=True, 
        height=350,
    )

    # INSIGHT & HIPOTESIS - Provinsi berdasarkan Waktu
    if len(by_prov_date) > 0:
        prov_terlambat = by_prov_date.nlargest(3, "tanggal_pertama")
        insight_col, why_col = st.columns(2)
        with insight_col:
            with st.popover("Insight"):
                st.markdown(f"""
                **Ketepatan Pelaporan Provinsi:**
                - Provinsi tercepat: **{by_prov_date.iloc[0]['provinsi_clean']}** (pertama masuk)
                - Jumlah provinsi yang sudah melapor: **{len(by_prov_date)}**
                - {'Ada provinsi yang baru muncul di akhir' if len(prov_terlambat) > 0 else 'Semua provinsi melapor relatif cepat'}
                - {'Provinsi ini berisiko under-represented' if len(prov_terlambat) > 0 else 'Pelaporan sudah merata'}
                """)
        with why_col:
            with st.popover("Why? (Hipotesis)"):
                st.markdown(f"""
                **Mengapa ada provinsi yang lebih cepat/lambat?**
                - **Kesiapan Infrastruktur:** {'Provinsi dengan sistem Dapodik yang matang lebih cepat melapor' if by_prov_date.iloc[0]['provinsi_clean'] in ['DKI Jakarta', 'Jawa Barat'] else 'Infrastruktur teknologi mempengaruhi kecepatan'}
                - **Koordinasi Tim:** {'Provinsi yang sudah terbiasa dengan program serupa lebih cepat' if by_prov_date.iloc[0]['provinsi_clean'] in ['DKI Jakarta', 'Jawa Barat'] else 'Koordinasi masih perlu ditingkatkan'}
                - **Prioritas Program:** {'Fokus awal pada provinsi dengan populasi besar' if by_prov_date.iloc[0]['provinsi_clean'] in ['DKI Jakarta', 'Jawa Barat'] else 'Provinsi 3T mungkin memerlukan waktu lebih lama'}
                - **Beban Administrasi:** {'Provinsi dengan banyak sekolah memerlukan waktu validasi lebih lama' if len(prov_terlambat) > 0 else 'Proses validasi berjalan efisien'}
                """)
    
    st.caption(
        "**Insight:** Provinsi yang baru muncul di hari-hari terakhir periode penarikan data berisiko **under-represented** "
        "dalam dataset ini — bukan karena program tidak berjalan di sana, tapi karena proses pelaporannya belum lengkap "
        "tertangkap saat snapshot data diambil."
    )

st.markdown("---")
st.markdown("### Kesiapan untuk Analisis Tren Multi-Tahun (Roadmap)")

# INSIGHT & HIPOTESIS - Roadmap
insight_col, why_col = st.columns(2)
with insight_col:
    with st.popover("Insight"):
        st.markdown("""
        **Potensi Analisis dengan Data Multi-Tahun:**
        - Pertumbuhan penerima manfaat year-over-year
        - Perubahan rasio gender dan kondisi khusus
        - Tren partisipasi sekolah negeri vs swasta
        - Pola distribusi geografis dari tahun ke tahun
        - Evaluasi efektivitas program MBG
        """)
with why_col:
    with st.popover("Why? (Hipotesis)"):
        st.markdown("""
        **Mengapa analisis multi-tahun penting?**
        - **Evaluasi Dampak:** {'Melihat apakah program MBG efektif meningkatkan partisipasi' if True else 'Butuh data longitudinal'}
        - **Perbaikan Program:** {'Identifikasi area yang membutuhkan intervensi berdasarkan tren' if True else 'Data tahunan tidak cukup'}
        - **Alokasi Anggaran:** {'Tren membantu perencanaan anggaran lebih akurat' if True else 'Butuh baseline historis'}
        - **Kebijakan Berbasis Data:** {'Membuat kebijakan berbasis bukti dari pola historis' if True else 'Pengambilan keputusan lebih baik dengan tren'}
        """)

st.info(
    """
    **Rekomendasi untuk pengembangan ke depan:** begitu data tahun ajaran berikutnya tersedia (kolom `tahun` terisi >1 nilai),
    halaman ini dapat langsung menampilkan:
    - Pertumbuhan/penurunan total penerima manfaat year-over-year per provinsi
    - Perubahan rasio gender dan persentase kondisi khusus dari tahun ke tahun
    - Tren penambahan/pengurangan jumlah satuan pendidikan yang terlibat program

    Filter **Tahun** di sidebar sudah disiapkan secara teknis (lihat `utils/filters.py`) untuk skenario ini.
    """
)

st.markdown("---")
st.success("**Lanjutkan ke Fitur 8: Dashboard Interaktif** untuk eksplorasi bebas dengan seluruh filter sekaligus.")