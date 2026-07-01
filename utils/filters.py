"""
Komponen filter global yang dipasang di sidebar SETIAP halaman.
Memakai st.session_state supaya pilihan filter tetap konsisten saat
pengguna pindah antar halaman (native multipage Streamlit).
"""

import streamlit as st
import pandas as pd

from utils.data_loader import get_processed_data


def render_global_filters():
    """
    Render filter di sidebar dan kembalikan dataframe yang sudah difilter.
    Filter: Tahun, Provinsi, Kabupaten/Kota, Kecamatan, Jenjang.
    Filter Negeri/Swasta dikembalikan terpisah sebagai string ('Semua'/'Negeri'/'Swasta')
    karena diterapkan ke METRIK, bukan baris (lihat catatan di setiap halaman).
    """
    df_raw = get_processed_data()

    st.sidebar.header("Filter Dashboard")

    # --- Tahun ---
    tahun_opts = sorted(df_raw["tahun"].unique().tolist())
    if len(tahun_opts) > 1:
        tahun_sel = st.sidebar.multiselect("Tahun", tahun_opts, default=tahun_opts, key="filter_tahun")
    else:
        tahun_sel = tahun_opts
        st.sidebar.caption(f"Tahun data: **{tahun_opts[0]}** (data 1 tahun saja — lihat catatan di Fitur 7: Analisis Tren)")

    # --- Provinsi ---
    prov_opts = sorted(df_raw["provinsi_clean"].unique().tolist())
    prov_sel = st.sidebar.multiselect("Provinsi", prov_opts, default=[], help="Kosongkan = semua provinsi", key="filter_provinsi")

    # --- Kabupaten/Kota (cascading dari provinsi) ---
    if prov_sel:
        kabkota_opts = sorted(df_raw[df_raw["provinsi_clean"].isin(prov_sel)]["kabkota_clean"].unique().tolist())
    else:
        kabkota_opts = sorted(df_raw["kabkota_clean"].unique().tolist())
    kabkota_sel = st.sidebar.multiselect("Kabupaten/Kota", kabkota_opts, default=[], help="Kosongkan = semua. Pilih provinsi dulu untuk daftar lebih ringkas.", key="filter_kabkota")

    # --- Kecamatan (cascading dari kab/kota) ---
    if kabkota_sel:
        kec_opts = sorted(df_raw[df_raw["kabkota_clean"].isin(kabkota_sel)]["kecamatan_clean"].unique().tolist())
    elif prov_sel:
        kec_opts = sorted(df_raw[df_raw["provinsi_clean"].isin(prov_sel)]["kecamatan_clean"].unique().tolist())
    else:
        kec_opts = sorted(df_raw["kecamatan_clean"].unique().tolist())
    kec_sel = st.sidebar.multiselect("Kecamatan", kec_opts, default=[], help="Kosongkan = semua. Daftar menyesuaikan provinsi/kab-kota yang dipilih.", key="filter_kecamatan")

    # --- Jenjang ---
    jenjang_opts = sorted(df_raw["jenjang"].unique().tolist())
    jenjang_sel = st.sidebar.multiselect("Jenjang Pendidikan", jenjang_opts, default=jenjang_opts, key="filter_jenjang")

    # --- Negeri / Swasta (diterapkan ke metrik, bukan filter baris -- lihat docstring) ---
    st.sidebar.markdown("---")
    tipe_sekolah = st.sidebar.radio(
        "Tampilan Jenis Sekolah",
        options=["Semua", "Negeri", "Swasta"],
        help=(
            "Data hanya punya JUMLAH sekolah negeri vs swasta per kecamatan (bukan data peserta didik "
            "per jenis sekolah). Memilih 'Negeri'/'Swasta' di sini akan mengganti metrik jumlah satuan "
            "pendidikan yang ditampilkan ke kolom yang sesuai, sementara metrik peserta didik/penerima "
            "manfaat tetap memakai data agregat penuh (tidak bisa dipecah negeri/swasta di sumber data ini)."
        ),
        key="filter_tipe_sekolah",
    )

    # Terapkan filter baris (tahun, provinsi, kabkota, kecamatan, jenjang)
    df = df_raw[df_raw["tahun"].isin(tahun_sel)]
    df = df[df["jenjang"].isin(jenjang_sel)]
    if prov_sel:
        df = df[df["provinsi_clean"].isin(prov_sel)]
    if kabkota_sel:
        df = df[df["kabkota_clean"].isin(kabkota_sel)]
    if kec_sel:
        df = df[df["kecamatan_clean"].isin(kec_sel)]

    st.session_state["tipe_sekolah"] = tipe_sekolah
    st.session_state["df_filtered"] = df

    st.sidebar.markdown("---")
    st.sidebar.metric("Baris data ditampilkan", f"{df.shape[0]:,}")
    if df.empty:
        st.warning("Tidak ada data untuk kombinasi filter ini. Silakan ubah filter di sidebar.")
        st.stop()

    return df, tipe_sekolah


def get_satpen_column(tipe_sekolah: str) -> str:
    """Kembalikan nama kolom jumlah satuan pendidikan yang sesuai dengan filter tipe sekolah."""
    return {
        "Semua": "jumlah_satuan_pendidikan",
        "Negeri": "jumlah_satpen_negeri",
        "Swasta": "jumlah_satpen_swasta",
    }[tipe_sekolah]
