# Backup Monitor Application
## Sistem Monitoring Backup Database Komprehensif

### Gambaran Umum
Aplikasi Backup Monitor adalah sistem monitoring backup database yang lengkap dengan antarmuka desktop berbasis PyQt5. Aplikasi ini dirancang untuk menganalisis, memverifikasi, dan memberikan notifikasi otomatis tentang file backup database dalam format ZIP dan BAK.

### Fitur Utama
- ✅ **Analisis File ZIP**: Metadata extraction, integrity checking, dan file listing
- ✅ **Validasi File BAK**: SQL Server backup analysis tanpa koneksi database
- ✅ **Notifikasi Multi-channel**: Email dan WhatsApp
- ✅ **Laporan PDF Komprehensif**: Generate laporan detail dalam format PDF
- ✅ **Ekstraksi Otomatis**: Ekstrak dan analisis file backup secara batch
- ✅ **Monitoring Real-time**: Deteksi dan analisis file backup baru secara otomatis

### Teknologi yang Digunakan
- **Bahasa Pemrograman**: Python 3.x
- **Framework UI**: PyQt5 (Desktop GUI)
- **Processing Backend**: Python Standard Library + ReportLab
- **WhatsApp Service**: Node.js dengan whatsapp-web.js
- **Email System**: SMTP dengan Gmail
- **Package Management**: pip (Python) dan npm (Node.js)

## Struktur Direktori

```
Backup_Monitor/
├── backup_monitor_qt.py          # Entry point aplikasi utama
├── backup_monitor_methods.py     # Metode tambahan aplikasi
├── config/
│   └── config.ini                # Konfigurasi sistem
├── src/                          # Modul inti aplikasi
│   ├── zip_metadata_viewer.py    # Analisis metadata ZIP
│   ├── bak_metadata_analyzer.py  # Analisis metadata BAK
│   ├── database_validator.py     # Validasi struktur database
│   ├── email_notifier.py          # Sistem notifikasi email
│   ├── pdf_report_generator.py    # Generator laporan PDF
│   ├── enhanced_zip_analyzer.py   # Analisis ZIP tingkat lanjut
│   ├── enhanced_bak_analyzer.py   # Analisis BAK tingkat lanjut
│   ├── enhanced_email_notifier.py # Notifikasi email tingkat lanjut
│   └── ...                       # Modul pendukung lainnya
├── wa_bot/                       # WhatsApp bot service
│   ├── server.js                 # Server HTTP Node.js
│   ├── whatsappService.js        # Service WhatsApp Web
│   ├── backupService.js          # Service backup automation
│   ├── simple_wa_bot.py          # Integrasi Python dengan WhatsApp
│   └── package.json              # Dependencies Node.js
├── ARCHITECTURE_DIAGRAM.md       # Diagram arsitektur aplikasi
├── EXECUTIVE_SUMMARY.md          # Ringkasan eksekutif arsitektur
└── ARCHITECTURE_PRESENTATION.md  # Presentasi arsitektur
```

## Instalasi dan Setup

### Prasyarat
- Python 3.7+
- Node.js 14+
- Akses internet untuk notifikasi WhatsApp
- Akun Gmail untuk notifikasi email

### Instalasi Python Dependencies
```bash
pip install -r requirements.txt
```

Dependencies utama:
- PyQt5
- reportlab
- sqlalchemy
- python-dotenv

### Instalasi Node.js Dependencies
```bash
cd wa_bot
npm install
```

Dependencies utama:
- whatsapp-web.js
- express
- puppeteer

### Konfigurasi
1. Salin `config/config.ini.example` ke `config/config.ini`
2. Edit pengaturan email dan notifikasi
3. Sesuaikan path backup sesuai dengan lingkungan Anda

Contoh konfigurasi:
```ini
[EMAIL]
sender_email = your_email@gmail.com
sender_password = your_app_password
receiver_email = recipient@gmail.com
smtp_server = smtp.gmail.com
smtp_port = 587

[NOTIFICATION]
subject = Monitoring Database Backup Report
check_interval = 3600
```

## Cara Penggunaan

### Menjalankan Aplikasi
```bash
python backup_monitor_qt.py
```

### Fitur Utama Aplikasi

#### 1. Analisis File ZIP
- Pilih folder backup
- Klik tombol analisis
- Lihat metadata ZIP dan integritas file

#### 2. Ekstraksi dan Analisis BAK
- Pilih file ZIP backup
- Klik "Ekstrak & Analisis"
- Lihat hasil analisis file BAK

#### 3. Laporan PDF
- Gunakan tombol "Generate PDF Report"
- Simpan laporan ke lokasi yang diinginkan
- Buka laporan untuk review

#### 4. Notifikasi Otomatis
- Konfigurasi email di `config/config.ini`
- Aktifkan monitoring otomatis
- Terima notifikasi untuk backup baru

### Penggunaan WhatsApp Bot
```bash
cd wa_bot
node server.js
```

Akses dashboard di `http://localhost:3000` untuk menghubungkan WhatsApp.

## Arsitektur Aplikasi

### Komponen Inti

#### 1. User Interface (`backup_monitor_qt.py`)
Antarmuka desktop berbasis PyQt5 yang menyediakan:
- File browser untuk direktori backup
- Panel kontrol untuk berbagai aksi
- Progress bar untuk operasi panjang
- Area hasil analisis dengan tab terorganisir

Arsitektur UI:
```
┌─────────────────────────────────────────────────────────┐
│                    Main Window                          │
├─────────────────────────┬───────────────────────────────┤
│   File Browser Panel    │    Action & Detail Panel      │
│                         │                               │
│ ┌─────────────────────┐  │  ┌─────────────────────────┐  │
│ │ Email Configuration │  │  │ Action Buttons          │  │
│ ├─────────────────────┤  │  │ - Check ZIP Integrity  │  │
│ │ Backup Folder       │  │  │ - Extract ZIP Info      │  │
│ │ Selection           │  │  │ - Analyze BAK Files     │  │
│ ├─────────────────────┤  │  │ - Send Backup Report    │  │
│ │ Backup Summary      │  │  │ - Extract All Files     │  │
│ ├─────────────────────┤  │  │ └─────────────────────────┘  │
│ │ ZIP Files Table     │  │  │                             │
│ └─────────────────────┘  │  │ Progress Bar                │
│                          │  │                             │
│                          │  │ Summary Data Report Panel   │
│                          │  │ ┌─────────────────────────┐ │
│                          │  │ │ ZIP Summary             │ │
│                          │  │ ├─────────────────────────┤ │
│                          │  │ │ BAK Analysis            │ │
│                          │  │ ├─────────────────────────┤ │
│                          │  │ │ System Status           │ │
│                          │  │ └─────────────────────────┘ │
│                          │  │                             │
│                          │  │ Analysis Results Area       │
│                          │  │                             │
└─────────────────────────┴──┴─────────────────────────────┘
```

#### 2. Worker System
Sistem berbasis thread worker untuk pemrosesan background:
- **BackupAnalysisWorker**: Menganalisis file ZIP dan BAK
- **EmailWorker**: Mengirim notifikasi email
- **MonitoringController**: Mengontrol monitoring otomatis

#### 3. Analysis Modules
Modul analisis spesifik untuk tipe file berbeda:
- **ZIP Metadata Viewer**: Analisis file ZIP
- **BAK Metadata Analyzer**: Analisis file BAK SQL Server
- **Database Validator**: Validasi struktur database
- **PDF Report Generator**: Pembuatan laporan PDF

#### 4. Notification System
Sistem notifikasi multi-channel:
- **Email Notifier**: Pengiriman email dengan SMTP
- **WhatsApp Service**: Notifikasi via WhatsApp Web
- **Enhanced Notifiers**: Template dan fitur tingkat lanjut

### Alur Kerja Aplikasi

#### Startup Process
1. **Inisialisasi Aplikasi**
   ```
   User membuka aplikasi → Load konfigurasi → Setup UI → 
   Inisialisasi thread pool → Scan folder backup → Tampilkan file ZIP
   ```

2. **Manual Analysis**
   ```
   User pilih file ZIP → Klik tombol aksi → 
   Worker thread mulai proses → Tampilkan progress → 
   Hasil ditampilkan di UI → Opsi kirim notifikasi/laporan
   ```

3. **Batch Processing**
   ```
   User klik "Extract All" → Konfirmasi ekstraksi → 
   Proses ekstraksi file ZIP satu per satu → 
   Analisis file BAK yang diekstrak → 
   Generate laporan komprehensif → Kirim notifikasi/email
   ```

4. **Automatic Monitoring**
   ```
   Sistem monitoring berjalan → Deteksi backup terbaru → 
   Analisis otomatis → Generate laporan → 
   Kirim email/WhatsApp → Update status UI
   ```

## API dan Integrasi

### REST API (WhatsApp Service)
Endpoint utama:
- `GET /health` - Status kesehatan service
- `POST /notify` - Kirim notifikasi kustom
- `POST /backup/report` - Kirim laporan backup
- `GET /status` - Status monitoring sistem

### Python Integration
Modul Python dapat digunakan secara independen:
```python
from src.zip_metadata_viewer import ZipMetadataViewer
from src.bak_metadata_analyzer import BAKMetadataAnalyzer
from src.email_notifier import EmailNotifier

# Contoh penggunaan
viewer = ZipMetadataViewer()
metadata = viewer.extract_zip_metadata("backup.zip")
```

## Security dan Best Practices

### Credential Management
- Password email disimpan di `config.ini`
- Gunakan App Password untuk Gmail (bukan password akun utama)
- Environment variables untuk secret sensitif

### File Access Control
- Validasi path file untuk mencegah directory traversal
- Permission checking sebelum operasi file
- Temporary file cleanup otomatis

### Error Handling
- Logging komprehensif untuk debugging
- Graceful degradation saat komponen gagal
- User-friendly error messages

## Development dan Contributing

### Struktur Development
```
src/
├── __init__.py
├── zip_metadata_viewer.py     # Analisis ZIP files
├── bak_metadata_analyzer.py   # Analisis BAK files  
├── database_validator.py      # Validasi database
├── email_notifier.py           # Notifikasi email
├── pdf_report_generator.py    # Laporan PDF
└── ...
```

### Testing
Unit testing menggunakan Python unittest:
```bash
python -m unittest discover tests/
```

### Contributing Guidelines
1. Fork repository
2. Buat branch fitur
3. Commit perubahan
4. Push ke branch
5. Buat Pull Request

### Coding Standards
- PEP 8 untuk Python code style
- Docstrings untuk dokumentasi fungsi
- Type hints untuk parameter dan return values
- Comment kompleks logic

## Troubleshooting

### Common Issues

#### 1. Email Notifikasi Tidak Terkirim
- Periksa kredensial email di `config.ini`
- Pastikan App Password digunakan (bukan password akun Gmail)
- Verifikasi koneksi internet

#### 2. WhatsApp Bot Tidak Terhubung
- Pastikan Node.js versi 14+ terinstal
- Jalankan `npm install` di direktori `wa_bot`
- Periksa koneksi internet dan firewall

#### 3. Error Saat Membaca File ZIP
- Periksa integritas file ZIP
- Pastikan file tidak sedang digunakan aplikasi lain
- Verifikasi permission akses file

### Logging
Log aplikasi tersedia di:
- `backup_monitor.log` untuk log umum
- `backup_monitor_debug.log` untuk debugging detail

Gunakan level logging yang sesuai:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

## License dan Support

### Lisensi
Aplikasi ini dirilis di bawah lisensi MIT. Lihat file `LICENSE` untuk detail lebih lanjut.

### Support
Untuk dukungan teknis:
- Buka issue di GitHub repository
- Hubungi tim pengembang untuk enterprise support
- Konsultasikan dokumentasi dan log aplikasi

### Community
Gabung komunitas pengguna untuk:
- Berbagi pengalaman penggunaan
- Mendapatkan tips dan trik
- Kontribusi pengembangan fitur baru

---

*Dokumentasi ini dibuat secara otomatis berdasarkan analisis kode sumber aplikasi. Untuk informasi lebih detail tentang arsitektur aplikasi, lihat file `ARCHITECTURE_DIAGRAM.md` dan `EXECUTIVE_SUMMARY.md`.*