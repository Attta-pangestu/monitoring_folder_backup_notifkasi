# Sistem Monitoring Database Backup

## Deskripsi
Sistem monitoring ini dirancang untuk memvalidasi folder backup yang berisi banyak file ZIP dan memeriksa tanggal terbaru pada database Plantware, Venus, dan Staging.

## Fitur Utama

### 1. Validasi ZIP Files
- **Validasi Integritas**: Memeriksa apakah file ZIP dapat dibaca dan tidak corrupt
- **Ekstraksi Tanggal**: Mengambil tanggal dari nama file ZIP
- **Analisis Konten**: Memeriksa file .bak di dalam ZIP
- **Deteksi Database**: Mengidentifikasi jenis database (Plantware, Venus, Staging)

### 2. Validasi Database
- **Plantware**: Memeriksa tabel `PR_TASKREG`
- **Venus**: Memeriksa tabel `TA_MACHINE` 
- **Staging**: Memeriksa tabel `GWSCANNER`
- **Analisis Tanggal**: Mencari tanggal terbaru di setiap tabel
- **Jumlah Record**: Menghitung total record dan record terbaru

### 3. Perbandingan Tanggal
- Membandingkan tanggal ZIP dengan tanggal database
- Mendeteksi sinkronisasi data
- Memberikan rekomendasi berdasarkan analisis

## Cara Penggunaan

### 1. Menjalankan Aplikasi
```bash
cd "d:\Gawean Rebinmas\App_Auto_Backup\Notiikasi_Database"
python src/gui.py
```

### 2. Fitur GUI Baru
- **Validate ZIP Files**: Memvalidasi semua file ZIP di folder
- **Check Databases**: Memeriksa database di dalam ZIP files
- **Full Monitoring**: Menjalankan monitoring lengkap dengan perbandingan tanggal

### 3. Monitoring Folder
1. Pilih folder yang berisi file ZIP backup
2. Klik "Full Monitoring" untuk analisis lengkap
3. Lihat hasil di Activity Log

## Struktur File Baru

### zip_validator.py
Modul untuk validasi file ZIP:
- `ZipValidator.validate_zip()`: Validasi file ZIP tunggal
- `ZipValidator.validate_multiple_zips()`: Validasi multiple ZIP files
- `ZipValidator.extract_date_from_filename()`: Ekstraksi tanggal dari nama file

### database_validator.py
Modul untuk validasi database:
- `DatabaseValidator.validate_databases()`: Validasi database di ZIP files
- `DatabaseValidator.analyze_plantware()`: Analisis database Plantware
- `DatabaseValidator.analyze_venus()`: Analisis database Venus
- `DatabaseValidator.analyze_staging()`: Analisis database Staging

### monitoring_controller.py
Controller utama untuk koordinasi monitoring:
- `MonitoringController.monitor_folder()`: Monitoring folder lengkap
- `MonitoringController.compare_dates()`: Perbandingan tanggal
- `MonitoringController.generate_summary()`: Generate laporan summary

## Format Laporan

### Summary Monitoring
```
=== MONITORING SUMMARY ===
Folder: [path_folder]
Total ZIP Files: [jumlah]
Valid ZIP Files: [jumlah_valid]
Invalid ZIP Files: [jumlah_invalid]

=== DATABASE ANALYSIS ===
Plantware Databases: [jumlah]
Venus Databases: [jumlah] 
Staging Databases: [jumlah]

=== DATE SYNCHRONIZATION ===
Latest ZIP Date: [tanggal]
Latest DB Date: [tanggal]
Sync Status: [status]
```

### Detail Report
- Daftar semua file ZIP dengan status validasi
- Analisis setiap database dengan jumlah record
- Tanggal terbaru dari setiap tabel
- Rekomendasi berdasarkan analisis

## Troubleshooting

### Error Import Module
Jika terjadi error import, pastikan semua file berada di direktori yang benar:
```
src/
├── gui.py
├── zip_validator.py
├── database_validator.py
├── monitoring_controller.py
├── folder_monitor.py
└── email_notifier.py
```

### Error Database Connection
- Pastikan file .bak dapat diekstrak dari ZIP
- Periksa format database SQLite
- Pastikan tabel yang dicari ada di database

## Konfigurasi

### Database Tables
- **Plantware**: `PR_TASKREG` (kolom tanggal: TGLREG, TGLUPDATE, TGLKIRIM)
- **Venus**: `TA_MACHINE` (kolom tanggal: TANGGAL, WAKTU_UPDATE, CREATED_DATE)
- **Staging**: `GWSCANNER` (kolom tanggal: SCAN_DATE, UPDATE_DATE, CREATED_AT)

### Format Tanggal ZIP
Sistem dapat mendeteksi format tanggal berikut dari nama file:
- YYYY-MM-DD
- YYYYMMDD
- DD-MM-YYYY
- DD/MM/YYYY

## Rekomendasi Penggunaan

1. **Monitoring Harian**: Jalankan "Full Monitoring" setiap hari
2. **Validasi ZIP**: Gunakan "Validate ZIP Files" untuk cek cepat
3. **Check Database**: Gunakan "Check Databases" untuk analisis database saja
4. **Auto Monitoring**: Aktifkan untuk monitoring otomatis berkala

## Log dan Debugging

Semua aktivitas dicatat di Activity Log GUI dengan informasi:
- Timestamp setiap operasi
- Status validasi ZIP files
- Hasil analisis database
- Error dan warning messages
- Summary hasil monitoring