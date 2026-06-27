"""
Modul pemuatan & pembersihan data MBG (Makan Bergizi Gratis).
Berisi fungsi untuk:
- memuat CSV mentah
- membersihkan & menstandardisasi nama provinsi
- menghitung metrik turunan (rasio-rasio indikator anomali/ketimpangan)
- agregasi dinamis berdasarkan level (provinsi / kab-kota / kecamatan)
"""

import pandas as pd
import numpy as np
import streamlit as st

RAW_PATH = "data/mbg_dataset.csv"

NUMERIC_COLS = [
    "jumlah_satuan_pendidikan", "jumlah_laki", "jumlah_perempuan",
    "jumlah_alergi", "jumlah_fobia", "jumlah_intoleransi",
    "jumlah_penerima_manfaat", "jumlah_kondisi_khusus",
    "jumlah_satpen_negeri", "jumlah_satpen_swasta",
]


@st.cache_data(show_spinner=False)
def load_raw(path: str = RAW_PATH) -> pd.DataFrame:
    """Load CSV mentah dan rapikan tipe data dasar."""
    df = pd.read_csv(path)

    # Bersihkan prefix "Prov." / "Kab." / "Kota" / "Kec." agar nama lebih ringkas untuk ditampilkan
    df["provinsi_clean"] = df["provinsi"].str.replace(r"^Prov\.\s*", "", regex=True).str.strip()
    df["kabkota_clean"] = df["kabupaten_kota"].str.strip()
    df["kecamatan_clean"] = df["kecamatan"].str.strip()

    # Parse tanggal pull (formatnya tidak konsisten di sumber data -> errors='coerce')
    df["date_pull_parsed"] = pd.to_datetime(df["date_pull"], errors="coerce")

    # Tandai baris yang duplikat penuh (potensi double-input / double-counting)
    df["is_duplicate_row"] = df.duplicated(keep=False)

    for c in NUMERIC_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    return df


def add_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tambahkan metrik turunan yang jadi dasar insight:
    - rasio penerima per satuan pendidikan (indikator beban/anomali kapasitas)
    - rasio gender (indikator kewajaran demografis)
    - persentase kondisi khusus (alergi+fobia+intoleransi) dari total penerima
    - persentase sekolah swasta dari total satuan pendidikan
    """
    df = df.copy()
    eps = 1e-9  # hindari pembagian dengan nol

    df["rasio_penerima_per_satpen"] = df["jumlah_penerima_manfaat"] / (df["jumlah_satuan_pendidikan"] + eps)
    df["rasio_gender_LP"] = df["jumlah_laki"] / (df["jumlah_perempuan"] + eps)
    df["pct_kondisi_khusus"] = np.where(
        df["jumlah_penerima_manfaat"] > 0,
        df["jumlah_kondisi_khusus"] / df["jumlah_penerima_manfaat"] * 100,
        0,
    )
    df["pct_swasta"] = np.where(
        df["jumlah_satuan_pendidikan"] > 0,
        df["jumlah_satpen_swasta"] / df["jumlah_satuan_pendidikan"] * 100,
        0,
    )
    df["total_kondisi_khusus_raw"] = df["jumlah_alergi"] + df["jumlah_fobia"] + df["jumlah_intoleransi"]
    return df


@st.cache_data(show_spinner=False)
def get_processed_data(path: str = RAW_PATH) -> pd.DataFrame:
    df = load_raw(path)
    df = add_derived_metrics(df)
    return df


def aggregate_by_level(df: pd.DataFrame, level: str) -> pd.DataFrame:
    """
    Agregasi dinamis berdasarkan level granularitas.
    level: 'provinsi' | 'kabupaten_kota' | 'kecamatan'
    Mengembalikan dataframe teragregasi dengan metrik dihitung ulang dari angka mentah
    (bukan rata-rata dari rasio per baris, supaya valid secara matematis).
    """
    level_map = {
        "provinsi": ["provinsi_clean"],
        "kabupaten_kota": ["provinsi_clean", "kabkota_clean"],
        "kecamatan": ["provinsi_clean", "kabkota_clean", "kecamatan_clean"],
    }
    group_cols = level_map[level]

    agg = df.groupby(group_cols, as_index=False).agg(
        jumlah_satuan_pendidikan=("jumlah_satuan_pendidikan", "sum"),
        jumlah_laki=("jumlah_laki", "sum"),
        jumlah_perempuan=("jumlah_perempuan", "sum"),
        jumlah_alergi=("jumlah_alergi", "sum"),
        jumlah_fobia=("jumlah_fobia", "sum"),
        jumlah_intoleransi=("jumlah_intoleransi", "sum"),
        jumlah_penerima_manfaat=("jumlah_penerima_manfaat", "sum"),
        jumlah_kondisi_khusus=("jumlah_kondisi_khusus", "sum"),
        jumlah_satpen_negeri=("jumlah_satpen_negeri", "sum"),
        jumlah_satpen_swasta=("jumlah_satpen_swasta", "sum"),
        n_baris_laporan=("jumlah_penerima_manfaat", "count"),
        n_duplikat=("is_duplicate_row", "sum"),
    )

    eps = 1e-9
    agg["rasio_penerima_per_satpen"] = agg["jumlah_penerima_manfaat"] / (agg["jumlah_satuan_pendidikan"] + eps)
    agg["rasio_gender_LP"] = agg["jumlah_laki"] / (agg["jumlah_perempuan"] + eps)
    agg["pct_kondisi_khusus"] = np.where(
        agg["jumlah_penerima_manfaat"] > 0,
        agg["jumlah_kondisi_khusus"] / agg["jumlah_penerima_manfaat"] * 100,
        0,
    )
    agg["pct_swasta"] = np.where(
        agg["jumlah_satuan_pendidikan"] > 0,
        agg["jumlah_satpen_swasta"] / agg["jumlah_satuan_pendidikan"] * 100,
        0,
    )

    # Label tampilan ringkas sesuai level
    if level == "provinsi":
        agg["label"] = agg["provinsi_clean"]
    elif level == "kabupaten_kota":
        agg["label"] = agg["kabkota_clean"] + " (" + agg["provinsi_clean"] + ")"
    else:
        agg["label"] = agg["kecamatan_clean"] + ", " + agg["kabkota_clean"]

    return agg


def detect_outliers_iqr(series: pd.Series, k: float = 1.5):
    """Deteksi outlier dengan metode IQR. Mengembalikan boolean mask."""
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - k * iqr, q3 + k * iqr
    return (series < lower) | (series > upper)


def gini_coefficient(values: np.ndarray) -> float:
    """Hitung koefisien Gini sebagai ukuran ketimpangan distribusi (0=merata, 1=sangat timpang)."""
    values = np.sort(np.array(values, dtype=float))
    values = values[values >= 0]
    n = len(values)
    if n == 0 or values.sum() == 0:
        return 0.0
    cum = np.cumsum(values)
    return float((n + 1 - 2 * np.sum(cum) / cum[-1]) / n)
