"""
Koordinat centroid 38 provinsi Indonesia (lintang, bujur).
Dihardcode supaya dashboard tidak bergantung pada layanan eksternal yang bisa
berubah/tidak tersedia saat dashboard di-deploy atau dinilai.

Sumber: kombinasi data administratif publik (centroid provinsi pra-2022)
dan data resmi UU pemekaran Papua 2022 untuk 4 provinsi baru.
"""

PROVINCE_COORDS = {
    "Aceh": (4.695135, 96.749399),
    "Sumatera Utara": (2.115355, 99.545097),
    "Sumatera Barat": (-0.739940, 100.800005),
    "Riau": (0.293347, 101.706829),
    "Jambi": (-1.485183, 102.438058),
    "Sumatera Selatan": (-3.319437, 103.914399),
    "Bengkulu": (-3.577847, 102.346388),
    "Lampung": (-4.558585, 105.406808),
    "Kepulauan Bangka Belitung": (-2.741051, 106.440587),
    "Kepulauan Riau": (3.945651, 108.142867),
    "D.K.I. Jakarta": (-6.211544, 106.845172),
    "Jawa Barat": (-7.090911, 107.668887),
    "Jawa Tengah": (-7.150975, 110.140259),
    "D.I. Yogyakarta": (-7.875385, 110.426209),
    "Jawa Timur": (-7.536064, 112.238402),
    "Banten": (-6.405817, 106.064018),
    "Bali": (-8.409518, 115.188916),
    "Nusa Tenggara Barat": (-8.652933, 117.361648),
    "Nusa Tenggara Timur": (-8.657382, 121.079371),
    "Kalimantan Barat": (-0.278781, 111.475285),
    "Kalimantan Tengah": (-1.681488, 113.382355),
    "Kalimantan Selatan": (-3.092642, 115.283759),
    "Kalimantan Timur": (1.640630, 116.419389),
    "Kalimantan Utara": (3.073301, 116.041824),
    "Sulawesi Utara": (0.624693, 123.975002),
    "Sulawesi Tengah": (-1.430025, 121.445618),
    "Sulawesi Selatan": (-3.668799, 119.974053),
    "Sulawesi Tenggara": (-4.144910, 122.174605),
    "Gorontalo": (0.699937, 122.446724),
    "Sulawesi Barat": (-2.844137, 119.232078),
    "Maluku": (-3.238462, 130.145273),
    "Maluku Utara": (1.570999, 127.808769),
    "Papua Barat": (-1.336115, 133.174716),
    "Papua Barat Daya": (-0.866460, 131.256900),
    "Papua": (-4.269928, 138.080353),
    "Papua Tengah": (-3.583330, 136.500000),
    "Papua Pegunungan": (-4.083330, 138.933300),
    "Papua Selatan": (-7.483330, 139.500000),
}


def get_coords_df(provinsi_list):
    """Kembalikan dict provinsi -> (lat, lon) untuk daftar provinsi yang diberikan, abaikan yang tidak ditemukan."""
    return {p: PROVINCE_COORDS[p] for p in provinsi_list if p in PROVINCE_COORDS}


def get_coords(provinsi_clean: str):
    """Kembalikan (lat, lon) untuk satu nama provinsi. (None, None) kalau tidak ditemukan."""
    return PROVINCE_COORDS.get(provinsi_clean, (None, None))
