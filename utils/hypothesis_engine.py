"""
Modul skor anomali & bank hipotesis.

PRINSIP PENTING:
- Skor ini murni STATISTIK (seberapa jauh suatu entitas menyimpang dari pola umum).
  Skor tinggi != bukti kecurangan. Banyak penyebab yang sah (perbedaan demografi,
  karakteristik sekolah, kualitas pencatatan) bisa menghasilkan skor tinggi.
- Setiap jenis anomali punya >= 3 hipotesis non-kecurangan yang ditampilkan LEBIH DULU,
  baru diikuti satu hipotesis "memerlukan verifikasi lebih lanjut" di posisi terakhir,
  yang diberi label jelas dan tidak ditulis sebagai kesimpulan.
- Modul ini tidak pernah menyebut nama entitas spesifik di dalam teks hipotesis,
  supaya bank hipotesis tetap generik dan tidak menuduh satu daerah tertentu.
"""

import pandas as pd
import numpy as np

from utils.data_loader import detect_outliers_iqr

# ---------------------------------------------------------------------------
# Bank hipotesis per jenis sinyal anomali
# Setiap list disusun: penyebab paling umum/jinak -> penyebab yang butuh verifikasi
# ---------------------------------------------------------------------------
HYPOTHESES = {
    "rasio_tinggi": {
        "judul": "Rasio Penerima per Satuan Pendidikan Sangat Tinggi",
        "deskripsi": "Satu satuan pendidikan menanggung jumlah penerima manfaat yang jauh di atas rata-rata.",
        "hipotesis": [
            "Sekolah besar dengan banyak rombongan belajar/shift (umum terjadi di SD/SMP negeri padat siswa di kota besar).",
            "Data jumlah satuan pendidikan belum diperbarui setelah ada penggabungan sekolah (merger), sehingga satpen tercatat sedikit tapi siswa banyak.",
            "Kesalahan input pada kolom jumlah satuan pendidikan saat rekap data dari lapangan.",
            "Perlu verifikasi lebih lanjut: kemungkinan pencatatan jumlah penerima yang digelembungkan tanpa penambahan satuan pendidikan riil, untuk klaim alokasi anggaran lebih besar dari kebutuhan aktual.",
        ],
    },
    "rasio_rendah": {
        "judul": "Rasio Penerima per Satuan Pendidikan Sangat Rendah",
        "deskripsi": "Banyak satuan pendidikan tercatat namun penerima manfaat sedikit.",
        "hipotesis": [
            "Wilayah dengan banyak sekolah kecil/terpencil (umum di daerah 3T — terdepan, terluar, tertinggal).",
            "Data satuan pendidikan mencakup sekolah yang sudah tidak aktif/tutup tapi belum dihapus dari basis data.",
            "Periode pendataan penerima belum lengkap (baru sebagian sekolah melapor jumlah siswa).",
            "Perlu verifikasi lebih lanjut: kemungkinan satuan pendidikan fiktif/tidak aktif didaftarkan untuk tujuan administratif tertentu.",
        ],
    },
    "duplikat": {
        "judul": "Baris Data Duplikat Persis",
        "deskripsi": "Ditemukan baris dengan seluruh kolom identik pada sumber data.",
        "hipotesis": [
            "Kesalahan teknis saat menggabungkan beberapa file Excel/CSV dari berbagai sumber pelaporan daerah.",
            "Re-submission data revisi tanpa menghapus entri lama dari sistem.",
            "Proses entry data dilakukan oleh lebih dari satu petugas untuk lokasi yang sama tanpa koordinasi.",
            "Perlu verifikasi lebih lanjut: kemungkinan pencatatan ganda yang berkaitan dengan pengajuan klaim anggaran untuk entitas yang sama lebih dari sekali.",
        ],
    },
    "gender_ekstrem": {
        "judul": "Rasio Gender (Laki-laki/Perempuan) Ekstrem",
        "deskripsi": "Proporsi penerima laki-laki vs perempuan jauh dari rasio wajar (di luar 0,33x–3x).",
        "hipotesis": [
            "Karakteristik jenjang/jenis sekolah tertentu (contoh: SMK teknik mesin didominasi laki-laki, sekolah keputrian didominasi perempuan).",
            "Sekolah berbasis asrama/pesantren dengan segregasi gender.",
            "Kesalahan input saat memisahkan kolom jumlah laki-laki dan perempuan.",
            "Perlu verifikasi lebih lanjut: kemungkinan ketidaksesuaian data penerima riil di lapangan dengan yang dilaporkan.",
        ],
    },
    "kondisi_khusus_ekstrem": {
        "judul": "Persentase Kondisi Khusus (Alergi/Fobia/Intoleransi) Sangat Tinggi",
        "deskripsi": "Proporsi penerima dengan kondisi khusus jauh di atas rata-rata wilayah lain.",
        "hipotesis": [
            "Pencatatan yang memang lebih teliti/lengkap di wilayah tersebut dibanding wilayah lain yang under-report.",
            "Karakteristik kesehatan/lingkungan lokal yang sah (misal riwayat alergi makanan tertentu di suatu daerah).",
            "Kesalahan kategorisasi saat input data kondisi khusus.",
            "Perlu verifikasi lebih lanjut: kemungkinan pelaporan kondisi khusus yang dilebihkan untuk justifikasi anggaran menu/penanganan khusus tambahan.",
        ],
    },
    "missing_timestamp": {
        "judul": "Tidak Ada Timestamp Pengambilan Data yang Valid",
        "deskripsi": "Baris data tidak memiliki tanggal/waktu penarikan data (date_pull) yang bisa dibaca.",
        "hipotesis": [
            "Format tanggal yang tidak konsisten antar file sumber sehingga gagal terbaca sistem.",
            "Data diinput manual tanpa mengikuti template standar pengambilan data otomatis.",
            "Perlu verifikasi lebih lanjut: kelengkapan proses audit jejak data (data trail) untuk entitas ini perlu dicek ke sumber asli.",
        ],
    },
}

# Bobot kontribusi tiap flag ke skor komposit (total maksimum = 100)
WEIGHTS = {
    "flag_duplikat": 30,
    "flag_rasio_tinggi": 25,
    "flag_gender_ekstrem": 15,
    "flag_kondisi_khusus_ekstrem": 15,
    "flag_rasio_rendah": 10,
    "flag_missing_timestamp": 5,
}

FLAG_TO_HYPOTHESIS_KEY = {
    "flag_rasio_tinggi": "rasio_tinggi",
    "flag_rasio_rendah": "rasio_rendah",
    "flag_duplikat": "duplikat",
    "flag_gender_ekstrem": "gender_ekstrem",
    "flag_kondisi_khusus_ekstrem": "kondisi_khusus_ekstrem",
    "flag_missing_timestamp": "missing_timestamp",
}


def compute_anomaly_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Hitung flag boolean untuk setiap jenis anomali pada level baris (kecamatan-jenjang).
    Tidak mengubah df asli — mengembalikan copy dengan kolom flag tambahan.
    """
    df = df.copy()

    outlier_mask_high = detect_outliers_iqr(df["rasio_penerima_per_satpen"])
    median_rasio = df["rasio_penerima_per_satpen"].median()
    df["flag_rasio_tinggi"] = outlier_mask_high & (df["rasio_penerima_per_satpen"] > median_rasio)
    df["flag_rasio_rendah"] = outlier_mask_high & (df["rasio_penerima_per_satpen"] <= median_rasio) & (df["jumlah_satuan_pendidikan"] > 0)

    df["flag_duplikat"] = df["is_duplicate_row"]
    df["flag_gender_ekstrem"] = (df["rasio_gender_LP"] > 3) | (df["rasio_gender_LP"] < 0.33)

    kk_outlier = detect_outliers_iqr(df["pct_kondisi_khusus"])
    df["flag_kondisi_khusus_ekstrem"] = kk_outlier & (df["pct_kondisi_khusus"] > df["pct_kondisi_khusus"].median())

    df["flag_missing_timestamp"] = df["date_pull_parsed"].isna()

    return df


def compute_anomaly_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tambahkan kolom skor_anomali (0-100) dan kategori_risiko berdasarkan flag yang terpicu.
    Harus dipanggil setelah compute_anomaly_flags().
    """
    df = df.copy()
    flag_cols = list(WEIGHTS.keys())

    score = np.zeros(len(df))
    for col, w in WEIGHTS.items():
        score += df[col].astype(int).values * w

    df["skor_anomali"] = score
    df["kategori_risiko"] = pd.cut(
        df["skor_anomali"], bins=[-1, 24, 49, 100],
        labels=["Rendah", "Sedang", "Tinggi"],
    )
    return df


def get_triggered_hypotheses(row: pd.Series) -> list:
    """
    Untuk satu baris data (Series) yang sudah punya kolom flag_*, kembalikan
    daftar dict {judul, deskripsi, hipotesis} untuk setiap flag yang aktif.
    """
    triggered = []
    for flag_col, hyp_key in FLAG_TO_HYPOTHESIS_KEY.items():
        if flag_col in row.index and bool(row[flag_col]):
            triggered.append(HYPOTHESES[hyp_key])
    return triggered


def aggregate_score_by_entity(df_with_score: pd.DataFrame, group_cols: list) -> pd.DataFrame:
    """
    Agregasi skor anomali ke level entitas (provinsi/kabkota) dengan mengambil
    rata-rata skor dan menghitung berapa baris yang masuk kategori 'Tinggi'.
    """
    flag_cols = list(WEIGHTS.keys())
    agg = df_with_score.groupby(group_cols, as_index=False).agg(
        skor_anomali_rata2=("skor_anomali", "mean"),
        skor_anomali_maks=("skor_anomali", "max"),
        n_baris_risiko_tinggi=("kategori_risiko", lambda s: (s == "Tinggi").sum()),
        n_baris_total=("skor_anomali", "count"),
        **{f"n_{c}": (c, "sum") for c in flag_cols},
    )
    agg["pct_baris_risiko_tinggi"] = (agg["n_baris_risiko_tinggi"] / agg["n_baris_total"] * 100).round(1)
    return agg
