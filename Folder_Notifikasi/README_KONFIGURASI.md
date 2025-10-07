# Konfigurasi Monitor Backup Zip

## File Konfigurasi

### config.ini
File konfigurasi utama untuk aplikasi Monitor Backup Zip.

### [EMAIL] - Konfigurasi Email
```
[EMAIL]
smtp_server = smtp.gmail.com
smtp_port = 587
sender_email = ifesptrj@gmail.com
sender_password = ugaowlrdcuhpdafu
recipient_email = backupptrj@gmail.com
```

**Detail Konfigurasi Email:**
- **Email Pengirim:** ifesptrj@gmail.com
- **Email Penerima:** backupptrj@gmail.com
- **Password:** ugaowlrdcuhpdafu (App Password Google)
- **Server SMTP:** smtp.gmail.com
- **Port:** 587

### [MONITORING] - Pengaturan Monitoring
```
[MONITORING]
check_interval = 300          # Interval pengecekan dalam detik (5 menit)
max_age_days = 7             # Maksimal hari backup sebelum dianggap overdue
extract_files = true         # Otomatis ekstrak file ZIP (true/false)
```

### [LOGGING] - Pengaturan Log
```
[LOGGING]
log_level = INFO              # Level log (DEBUG, INFO, WARNING, ERROR)
log_file = logs/zip_monitor.log  # Lokasi file log
max_log_size = 10485760       # Maksimal ukuran file log (10MB)
backup_count = 5             # Jumlah backup file log
```

## Cara Menggunakan Aplikasi

### 1. Menjalankan Aplikasi
```bash
python zip_backup_monitor.py
```

### 2. Konfigurasi Folder Monitor
- Klik tombol "Pilih Folder" untuk memilih folder yang akan dimonitor
- Atau ketik path folder secara manual

### 3. Memulai Monitoring
- Klik "Mulai Monitor" untuk memulai monitoring otomatis
- Atau klik "Scan Sekarang" untuk scan manual

### 4. Melihat Hasil
- Tab **Ringkasan**: Menampilkan statistik monitoring
- Tab **Daftar File**: Menampilkan detail setiap file
- Tab **Log**: Menampilkan log aktivitas

## Fitur Email Notifikasi

### Email Test
- Klik "Test Email" untuk mengirim email test
- Memverifikasi konfigurasi email sudah benar

### Alert Backup Terlambat
- Sistem otomatis mengirim email jika backup terlambat
- Threshold: 7 hari (bisa diubah di config.ini)

### Laporan Summary
- Email otomatis dikirim setelah scan selesai
- Berisi statistik file ZIP, rasio kompresi, dan analisis BAK

## Persyaratan Email

### Untuk Gmail (Google Account)
1. **2-Factor Authentication** harus aktif
2. **App Password** harus di-generate:
   - Kunjungi: https://myaccount.google.com/apppasswords
   - Pilih app: "Mail"
   - Pilih device: "Windows Computer"
   - Copy password yang di-generate

### Jika Email Gagal Terkirim
1. Pastikan 2FA aktif di Google Account
2. Generate ulang App Password
3. Periksa firewall dan koneksi internet
4. Pastikan SMTP server dan port benar

## Struktur Folder

```
Folder_Notifikasi/
├── zip_backup_monitor.py      # Aplikasi utama
├── config.ini                 # File konfigurasi
├── requirements.txt           # Dependensi Python
├── backup_summary.json        # Hasil analisis (auto-generated)
├── logs/                      # Folder log
│   └── zip_monitor.log       # File log
└── README_KONFIGURASI.md      # Dokumentasi ini
```

## Troubleshooting

### Email Tidak Terkirim
1. Cek konfigurasi email di config.ini
2. Pastikan App Password masih valid
3. Test koneksi dengan "Test Email"
4. Periksa log di folder logs/

### File ZIP Tidak Terdeteksi
1. Pastikan folder monitor sudah dipilih
2. Cek apakah file ada di subfolder
3. Pastikan file berekstensi .zip

### Error Ekstraksi File
1. Pastikan file ZIP tidak corrupt
2. Cek izin akses folder
3. Pastikan cukup ruang disk

## Support

Jika mengalami masalah:
1. Periksa log di `logs/zip_monitor.log`
2. Cek konfigurasi di `config.ini`
3. Test dengan "Test Email"
4. Restart aplikasi jika perlu