# Database Backup Monitor

Aplikasi untuk monitoring dan notifikasi backup database secara otomatis.

## Fitur

- **Monitoring Backup**: Memantau file backup database (.zip yang berisi .bak)
- **Email Notifikasi**: Mengirim notifikasi otomatis ke email
- **Query Database**: Mengeksekusi query sederhana untuk mendapatkan tanggal terakhir
- **GUI Interface**: Interface pengguna yang mudah digunakan
- **Configurable**: Konfigurasi email dan pengaturan melalui file config

## Struktur Folder

```
Notiikasi_Database/
├── src/
│   ├── email_notifier.py    # Modul pengiriman email
│   ├── gui.py               # Interface GUI
│   └── backup_monitor.py    # Logika monitoring backup
├── config/
│   └── config.ini          # File konfigurasi
├── tests/                  # Folder testing
├── main.py                 # File utama untuk menjalankan aplikasi
├── requirements.txt       # Dependencies
└── README.md              # Dokumentasi
```

## Instalasi

1. Pastikan Python 3.x sudah terinstall
2. Clone atau download repository ini
3. Install dependencies (jika diperlukan):
   ```bash
   pip install -r requirements.txt
   ```

## Konfigurasi

Edit file `config/config.ini`:

```ini
[EMAIL]
sender_email = ifesptrj@gmail.com
sender_password = ptrj@123
receiver_email = backupptrj@gmail.com
smtp_server = smtp.gmail.com
smtp_port = 587

[DATABASE]
backup_path =
query_tables =

[NOTIFICATION]
subject = Monitoring Database Backup Report
check_interval = 3600
```

## Cara Penggunaan

1. Jalankan aplikasi:
   ```bash
   python main.py
   ```

2. Di GUI:
   - Cek konfigurasi email (sudah terisi otomatis dari config)
   - Pilih file backup.zip untuk dianalisis
   - Gunakan tombol testing untuk memverifikasi fungsi email
   - Generate dummy report untuk testing

## Testing

### Test Email Connection
- Klik tombol "Test Email Connection" untuk memverifikasi pengaturan email

### Send Test Notification
- Klik tombol "Send Test Notification" untuk mengirim email notifikasi test

### Generate Dummy Report
- Klik tombol "Generate Dummy Report" untuk membuat laporan dummy

## Cara Kerja

1. Aplikasi membaca file backup (.zip)
2. Mengekstrak dan mencari file .bak
3. Membuka file .bak sebagai database SQLite
4. Mengeksekusi query untuk mendapatkan data terakhir
5. Membuat laporan dan mengirim email notifikasi

## Security Notes

- Password email disimpan di config.ini (untuk production, gunakan environment variables)
- Pastikan email sender memiliki akses untuk mengirim email via SMTP
- Untuk Gmail, pastikan "Less secure app access" diaktifkan

## Troubleshooting

### Email tidak terkirim
- Pastikan password email benar
- Cek koneksi internet
- Untuk Gmail, pastikan "Less secure app access" diaktifkan
- Cek firewall dan antivirus

### Database tidak bisa dibuka
- Pastikan file .bak adalah database SQLite yang valid
- Cek file tidak corrupt
- Pastikan ada izin untuk membaca file

## Future Enhancements

- Monitoring otomatis dengan schedule
- Support untuk jenis database lain (MySQL, PostgreSQL)
- Dashboard monitoring real-time
- History log yang lebih detail
- Export laporan ke PDF/Excel