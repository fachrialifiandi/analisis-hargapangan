from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from datetime import datetime, timedelta

# ================= KONFIGURASI =================
TOTAL_HARI = 1
ALAMAT_WEB = "https://panelharga.badanpangan.go.id/harga-eceran-daerah"
NAMA_FILE_HASIL = "data_pangan.xlsx"

DAFTAR_KOMODITAS = [
    "Beras SPHP", "Cabai Rawit Merah", "Bawang Putih Bonggol",
    "Bawang Merah", "Daging Sapi Murni", "Daging Ayam Ras",
    "Telur Ayam Ras", "Gula Konsumsi", "Garam Konsumsi",
    "Minyak Goreng Curah"
]

DATA_KOORDINAT = {
    "ACEH": (-4.6951, 96.7494),
    "SUMATERA UTARA": (2.1154, 99.5451),
    "SUMATERA BARAT": (-0.7399, 100.8000),
    "RIAU": (0.2933, 101.7068),
    "JAMBI": (-1.6101, 103.6131),
    "SUMATERA SELATAN": (-3.3194, 104.9145),
    "BENGKULU": (-3.5778, 102.3464),
    "LAMPUNG": (-4.5586, 105.4068),
    "KEP. BANGKA BELITUNG": (-2.7411, 106.4406),
    "KEP. RIAU": (3.9457, 108.1429),
    "DKI JAKARTA": (-6.2088, 106.8456),
    "JAWA BARAT": (-6.9175, 107.6191),
    "JAWA TENGAH": (-7.1510, 110.1403),
    "DI YOGYAKARTA": (-7.7956, 110.3695),
    "JAWA TIMUR": (-7.5361, 112.2384),
    "BANTEN": (-6.4058, 106.0640),
    "BALI": (-8.4095, 115.1889),
    "NUSA TENGGARA BARAT": (-8.6529, 117.3616),
    "NUSA TENGGARA TIMUR": (-8.6574, 121.0794),
    "KALIMANTAN BARAT": (-0.2787, 111.4753),
    "KALIMANTAN TENGAH": (-1.6815, 113.3824),
    "KALIMANTAN SELATAN": (-3.0926, 115.2838),
    "KALIMANTAN TIMUR": (0.5387, 116.4194),
    "KALIMANTAN UTARA": (3.0731, 116.0414),
    "SULAWESI UTARA": (0.6247, 123.9750),
    "SULAWESI TENGAH": (-1.4300, 121.4456),
    "SULAWESI SELATAN": (-3.6687, 119.9740),
    "SULAWESI TENGGARA": (-4.1449, 122.1746),
    "GORONTALO": (0.6999, 122.4467),
    "SULAWESI BARAT": (-2.8441, 119.2321),
    "MALUKU": (-3.2385, 130.1453),
    "MALUKU UTARA": (1.5709, 127.8087),
    "PAPUA BARAT": (-1.3361, 133.1747),
    "PAPUA": (-4.2699, 138.0804)
}

driver = webdriver.Chrome()
driver.maximize_window()
driver.get(ALAMAT_WEB)
time.sleep(5)

kumpulan_data = []

# ================= MULAI KERJA =================
for hari_ke in range(TOTAL_HARI):
    waktu_target = datetime.now() - timedelta(days=hari_ke)
    tanggal_str = waktu_target.strftime("%Y-%m-%d")
    print(f"\n📅 [{hari_ke+1}/{TOTAL_HARI}] Memproses Tanggal: {tanggal_str}")

    for nama_makanan in DAFTAR_KOMODITAS:
        print(f"   👉 Mengambil: {nama_makanan}", end="")

        # --- 1. PILIH KOMODITAS (MENGGUNAKAN XPATH ANDA) ---
        try:
            # Tunggu elemen ID 'select-komoditas' muncul
            elemen_dropdown = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="select-komoditas"]'))
            )

            # Masukkan ke fungsi Select
            pilih_menu = Select(elemen_dropdown)

            # A. Coba pilih berdasarkan teks persis (Exact Match)
            try:
                pilih_menu.select_by_visible_text(nama_makanan)
            except:
                # B. Jika gagal, cari manual yang MIRIP (Partial Match)
                # Ini berguna misal kita tulis "Garam" tapi di web "Garam Halus"
                found = False
                for opsi in pilih_menu.options:
                    # Cari teks yang mengandung kata kunci (Case insensitive)
                    if nama_makanan.lower() in opsi.text.lower():
                        pilih_menu.select_by_visible_text(opsi.text)
                        found = True
                        break

                if not found:
                    raise Exception(
                        f"Menu '{nama_makanan}' tidak ditemukan di dropdown")

        except Exception as e:
            print(f"(Error: {e})")
            continue

        # --- 2. ISI TANGGAL ---
        kotak_input = driver.find_elements(By.CSS_SELECTOR, "input.input")
        if len(kotak_input) >= 2:
            driver.execute_script(
                f"arguments[0].value = '{tanggal_str}';", kotak_input[0])
            driver.execute_script(
                f"arguments[0].value = '{tanggal_str}';", kotak_input[1])

        # --- 3. KLIK TOMBOL CARI ---
        tombols = driver.find_elements(By.TAG_NAME, "button")
        for btn in tombols:
            class_btn = btn.get_attribute("class")
            if class_btn and "primary" in class_btn:
                driver.execute_script("arguments[0].click();", btn)
                break

        # --- 4. TUNGGU DATA LOAD ---
        time.sleep(random.uniform(3, 5))

        # --- 5. AMBIL DATA ---
        soup = BeautifulSoup(driver.page_source, "html.parser")
        tabel = soup.find("table")

        if tabel:
            baris_tabel = tabel.find_all("tr")
            jumlah_sukses = 0
            for baris in baris_tabel:
                kolom = baris.find_all("td")
                teks_kolom = [k.text.strip() for k in kolom]

                if len(teks_kolom) > 2:
                    nama_lokasi = teks_kolom[0]

                    lat, long = 0, 0
                    for key, val in DATA_KOORDINAT.items():
                        if key in nama_lokasi.upper():
                            lat, long = val
                            break

                    teks_kolom.append(lat)
                    teks_kolom.append(long)
                    teks_kolom.insert(0, nama_makanan)
                    teks_kolom.insert(0, tanggal_str)
                    kumpulan_data.append(teks_kolom)
                    jumlah_sukses += 1

            print(f" ({jumlah_sukses} baris)")
        else:
            print(" ⚠️ Tabel Kosong")

driver.quit()

# ================= SIMPAN KE EXCEL =================
print(f"\total Data terkumpul: {len(kumpulan_data)}")

if len(kumpulan_data) > 0:
    df = pd.DataFrame(kumpulan_data)
    judul_kolom = ["Tanggal", "Komoditas", "Provinsi",
                   "Harga", "Perubahan (%)", "Latitude", "Longtitude"]

    if df.shape[1] > len(judul_kolom):
        sisa = df.shape[1] - len(judul_kolom)
        for i in range(sisa):
            judul_kolom.append(f"Info_{i}")
    df.columns = judul_kolom[:df.shape[1]]

    df.to_excel(NAMA_FILE_HASIL, index=False)
    print(f"💾File Excel Tersimpan: {NAMA_FILE_HASIL}")
else:
    print("Tidak ada data yang berhasil diambil.")
