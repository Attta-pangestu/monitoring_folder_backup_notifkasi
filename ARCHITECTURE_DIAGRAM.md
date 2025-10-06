# Diagram Arsitektur Aplikasi Backup Monitor

## Gambaran Umum

Aplikasi Backup Monitor adalah sistem monitoring backup database yang komprehensif dengan antarmuka PyQt5. Aplikasi ini mampu menganalisis file ZIP backup, mengekstrak dan menganalisis file BAK database, serta mengirimkan laporan via email.

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                                    APLIKASI UTAMA                                  │
├────────────────────────────────────────────────────────────────────────────────────┤
│                             backup_monitor_qt.py (ENTRY POINT)                     │
│                         (PyQt5 GUI Application - Main Window)                    │
└────────────────────────────────────────────────────────────────────────────────────┘
                                    │    │    │
                         ┌──────────┘    │    └──────────┐
                         ▼               ▼               ▼
        ┌─────────────────────────┐    ┌─────────────┐    ┌──────────────────────────┐
        │    WORKER THREADS       │    │   EMAIL     │    │    USER INTERFACE        │
        │                         │    │             │    │                          │
        │ BackupAnalysisWorker    │    │ EmailWorker │    │ BackupMonitorWindow      │
        │ (QRunnable)             │    │ (QRunnable) │    │ (QMainWindow)            │
        └─────────────────────────┘    └─────────────┘    └──────────────────────────┘
                  │                           │                       │
        ┌─────────┴─────────┐        ┌────────┴────────┐     ┌──────────┴─────────┐
        ▼                 ▼        ▼                 ▼     ▼                    ▼
 WorkerSignals    ZipMetadataViewer     EmailNotifier      UI COMPONENTS    ACTION BUTTONS
(Progress,Error)   (ZIP Analysis)     (Email Sending)    (Tables,Buttons)  (Analysis,Report)

┌────────────────────────────────────────────────────────────────────────────────────┐
│                                 MODUL INTI APLIKASI                                │
├────────────────────────────────────────────────────────────────────────────────────┤

MODUL ANALISIS ZIP & BAK
├── src/zip_metadata_viewer.py
│   ├── Menganalisis metadata file ZIP
│   ├── Memeriksa integritas ZIP
│   ├── Mengekstrak informasi file dalam ZIP
│   └── Mencari file BAK dalam ZIP
│
├── src/bak_metadata_analyzer.py
│   ├── Menganalisis metadata file BAK
│   ├── Memeriksa validitas backup SQL Server
│   ├── Mengekstrak informasi database
│   └── Memvalidasi integritas file BAK
│
└── src/database_validator.py
    ├── Memvalidasi struktur database
    ├── Mengecek tanggal backup terbaru
    └── Memverifikasi isi database

MODUL NOTIFIKASI & LAPORAN
├── src/email_notifier.py
│   ├── Mengirim email notifikasi
│   ├── Mengirim laporan backup
│   └── Mengirim alert/peringatan
│
├── src/pdf_report_generator.py
│   ├── Membuat laporan PDF komprehensif
│   ├── Menampilkan hasil analisis
│   └── Menghasilkan ringkasan visual
│
└── src/enhanced_email_notifier.py
    ├── Notifikasi yang ditingkatkan
    └── Template email yang lebih baik

┌────────────────────────────────────────────────────────────────────────────────────┐
│                                 KOMPONEN ANTARMUKA                                 │
├────────────────────────────────────────────────────────────────────────────────────┤

PANEL UTAMA UI
├── File Browser Panel (Kiri)
│   ├── Konfigurasi Email
│   ├── Pemilihan Folder Backup
│   ├── Ringkasan Backup
│   └── Tabel File ZIP
│
└── Action & Detail Panel (Kanan)
    ├── Tombol Aksi Utama
    │   ├── Check ZIP Integrity
    │   ├── Extract ZIP Info
    │   ├── Analyze BAK Files
    │   ├── Send Backup Report
    │   └── Extract All Files
    │
    ├── Progress Bar
    │
    ├── Summary Data Report Panel
    │   ├── Tab ZIP Summary
    │   ├── Tab BAK Analysis
    │   └── Tab System Status
    │
    └── Analysis Results Area
        ├── Detail teks hasil analisis
        └── Terminal output (simulasi)

┌────────────────────────────────────────────────────────────────────────────────────┐
│                               KONFIGURASI & PENYIMPANAN                            │
├────────────────────────────────────────────────────────────────────────────────────┤

KONFIGURASI APLIKASI
├── config/config.ini
│   ├── Pengaturan Email
│   ├── Pengaturan Database
│   └── Pengaturan Notifikasi
│
├── .env (wa_bot)
│   └── Variabel lingkungan WhatsApp Bot
│
└── Penyimpanan Sementara
    ├── temp_extract/ (Ekstraksi sementara)
    └── extracted_backups/ (Ekstraksi permanen)

┌────────────────────────────────────────────────────────────────────────────────────┐
│                                 WHATSAPP BOT SERVICE                               │
├────────────────────────────────────────────────────────────────────────────────────┤

whatsappService.js
├── Koneksi ke WhatsApp Web
├── Pengiriman notifikasi via WhatsApp
└── Monitoring status backup

backupService.js
├── Service backup automation
├── Penjadwalan backup
└── Integrasi dengan sistem monitoring

server.js
├── Server HTTP untuk API
├── Endpoint untuk trigger backup
└── Monitoring status sistem

┌────────────────────────────────────────────────────────────────────────────────────┐
│                                 ARSITEKTUR ALIRAN DATA                             │
├────────────────────────────────────────────────────────────────────────────────────┤

1. STARTUP
   User membuka aplikasi → Load konfigurasi → Scan folder backup → Tampilkan file ZIP

2. ANALISIS MANUAL
   User pilih file ZIP → Click tombol aksi → Worker thread mulai proses → 
   Tampilkan progress → Hasil ditampilkan di UI → Opsi kirim email/laporan

3. EKSTRAKSI & ANALISIS BATCH
   User click "Extract All" → Konfirmasi ekstraksi → 
   Proses ekstraksi file ZIP satu per satu → 
   Analisis file BAK yang diekstrak → 
   Generate laporan komprehensif → 
   Kirim notifikasi/email

4. NOTIFIKASI OTOMATIS
   Sistem monitoring berjalan → Deteksi backup terbaru → 
   Analisis otomatis → Generate laporan → 
   Kirim email/WhatsApp → Update status UI

5. LAPORAN PDF
   User minta laporan PDF → Generate dari hasil analisis → 
   Simpan sebagai file PDF → Opsi buka otomatis

┌────────────────────────────────────────────────────────────────────────────────────┐
│                                 TEKNOLOGI & LIBRARY                                │
├────────────────────────────────────────────────────────────────────────────────────┤

FRONTEND/UI
├── PyQt5 (Antarmuka Desktop)
├── HTML/CSS (Template email & laporan)
└── ReportLab (Pembuatan PDF)

BACKEND/PROCESSING
├── Python Standard Library
│   ├── zipfile (Manipulasi ZIP)
│   ├── os/pathlib (Akses file sistem)
│   ├── smtplib/email (Email)
│   └── json (Parsing data)
├── SQLAlchemy (Opsional untuk database)
└── subprocess (Eksekusi command eksternal)

WHATSAPP BOT
├── Node.js
├── whatsapp-web.js
├── Express.js (Server API)
└── Puppeteer (Browser automation)

DEPENDENCIES MANAGEMENT
├── pip (Python packages)
├── npm (Node.js packages)
└── Virtual Environment (Python)

┌────────────────────────────────────────────────────────────────────────────────────┐
│                                 WORKFLOW UTAMA                                     │
├────────────────────────────────────────────────────────────────────────────────────┤

WORKFLOW MONITORING BACKUP
┌────────────────────────────────────────────────────────────────────────────────────┐
│ 1. Inisialisasi Aplikasi                                                           │
│    ┌─────────────────────────────────────────────────────────────────────────────┐ │
│    │ backup_monitor_qt.py                                                        │ │
│    │ ├── Load config/config.ini                                                  │ │
│    │ ├── Setup UI components                                                     │ │
│    │ ├── Inisialisasi thread pool                                                │ │
│    │ └── Scan default backup folder                                              │ │
│    └─────────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────────┐
│ 2. Analisis File ZIP                                                               │
│    ┌─────────────────────────────────────────────────────────────────────────────┐ │
│    │ User klik tombol analisis                                                   │ │
│    │ ├── Buat BackupAnalysisWorker                                               │ │
│    │ ├── Jalankan di thread pool                                                 │ │
│    │ ├── Worker: analisis ZIP metadata                                          │ │
│    │ ├── Worker: cek integritas ZIP                                             │ │
│    │ ├── Worker: cari file BAK dalam ZIP                                         │ │
│    │ └── Return hasil ke UI                                                     │ │
│    └─────────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────────┐
│ 3. Ekstraksi & Analisis BAK                                                        │
│    ┌─────────────────────────────────────────────────────────────────────────────┐ │
│    │ User klik ekstrak & analisis                                                │ │
│    │ ├── Worker: ekstrak file ZIP                                                │ │
│    │ ├── Worker: analisis file BAK yang diekstrak                                │ │
│    │ ├── Worker: validasi struktur BAK                                           │ │
│    │ ├── Worker: ekstrak metadata database                                       │ │
│    │ └── Return hasil analisis lengkap                                          │ │
│    └─────────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────────┐
│ 4. Pembuatan Laporan                                                               │
│    ┌─────────────────────────────────────────────────────────────────────────────┐ │
│    │ User minta laporan                                                          │ │
│    │ ├── Generate laporan PDF dari hasil analisis                                │ │
│    │ ├── Format data dengan ReportLab                                            │ │
│    │ ├── Simpan file PDF                                                         │ │
│    │ └── Tampilkan dialog sukses                                                 │ │
│    └─────────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────────┐
│ 5. Notifikasi                                                                      │
│    ┌─────────────────────────────────────────────────────────────────────────────┐ │
│    │ Email atau WhatsApp                                                         │ │
│    │ ├── Siapkan template notifikasi                                             │ │
│    │ ├── Masukkan data hasil analisis                                            │ │
│    │ ├── Kirim via EmailNotifier                                                 │ │
│    │ └── Atau via WhatsApp Service                                              │ │
│    └─────────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────────┐
│ 6. WhatsApp Integration                                                             │
│    ┌─────────────────────────────────────────────────────────────────────────────┐ │
│    │ wa_bot/                                                                     │ │
│    │ ├── whatsappService.js (kirim notifikasi)                                   │ │
│    │ ├── backupService.js (service backup)                                      │ │
│    │ ├── server.js (API endpoint)                                               │ │
│    │ └── simple_wa_bot.py (Python integration)                                  │ │
│    └─────────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────────┘