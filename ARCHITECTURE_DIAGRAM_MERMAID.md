# Diagram Arsitektur Visual Aplikasi Backup Monitor

## Struktur Aplikasi Utama

```mermaid
graph TD
    A[User Interface] --> B[Main Window<br/>backup_monitor_qt.py]
    B --> C[Worker Threads]
    B --> D[Email System]
    B --> E[UI Components]
    
    C --> C1[BackupAnalysisWorker]
    C --> C2[EmailWorker]
    
    C1 --> C1A[ZIP Analysis]
    C1 --> C1B[BAK Analysis]
    C1 --> C1C[Database Validation]
    
    D --> D1[EmailNotifier]
    D --> D2[Enhanced Email Notifier]
    
    E --> E1[File Browser Panel]
    E --> E2[Action Buttons]
    E --> E3[Progress Display]
    E --> E4[Results Panel]
```

## Modul Inti Aplikasi

```mermaid
graph TD
    Z[ZIP Processing Modules] --> Z1[zip_metadata_viewer.py]
    Z --> Z2[zip_validator.py]
    Z --> Z3[enhanced_zip_analyzer.py]
    
    B[BAK Processing Modules] --> B1[bak_metadata_analyzer.py]
    B --> B2[bak_file_reader.py]
    B --> B3[enhanced_bak_analyzer.py]
    B --> B4[tape_file_analyzer.py]
    
    D[Database Modules] --> D1[database_validator.py]
    D --> D2[enhanced_database_validator.py]
    D --> D3[quick_database_validator.py]
    
    R[Reporting Modules] --> R1[pdf_report_generator.py]
    R --> R2[email_notifier.py]
    R --> R3[enhanced_email_notifier.py]
    
    U[Utility Modules] --> U1[monitoring_controller.py]
    U --> U2[folder_monitor.py]
    U --> U3[gui.py]
```

## Arsitektur Aliran Data

```mermaid
graph LR
    A[User Input] --> B[GUI Event Handler]
    B --> C[Worker Thread Creation]
    C --> D[Background Processing]
    D --> E[Result Collection]
    E --> F[UI Update]
    F --> G[Notification Trigger]
    G --> H[Email/WhatsApp Sending]
```

## Komponen WhatsApp Bot

```mermaid
graph TD
    W[WhatsApp Bot System] --> W1[whatsappService.js]
    W --> W2[backupService.js]
    W --> W3[server.js]
    W --> W4[simple_wa_bot.py]
    
    W1 --> WA[WhatsApp Web Connection]
    W2 --> WB[Backup Automation]
    W3 --> WC[HTTP API Server]
    W4 --> WD[Python Integration]
```

## Flow Monitoring Backup

```mermaid
flowchart TD
    START([Mulai Aplikasi]) --> LOAD[Load Konfigurasi]
    LOAD --> SCAN[Scan Folder Backup]
    SCAN --> DISPLAY[Tampilkan File ZIP]
    DISPLAY --> USER_ACTION[Pilih Aksi User]
    
    USER_ACTION -->|Analisis ZIP| ANALYZE_ZIP[Analisis Metadata ZIP]
    ANALYZE_ZIP --> SHOW_ZIP_RESULTS[Tampilkan Hasil ZIP]
    SHOW_ZIP_RESULTS --> NOTIFY_ZIP[Kirim Notifikasi ZIP]
    
    USER_ACTION -->|Ekstrak & Analisis| EXTRACT[Ekstrak File ZIP]
    EXTRACT --> ANALYZE_BAK[Analisis File BAK]
    ANALYZE_BAK --> VALIDATE_DB[Validasi Database]
    VALIDATE_DB --> SHOW_FULL_RESULTS[Tampilkan Hasil Lengkap]
    SHOW_FULL_RESULTS --> NOTIFY_FULL[Kirim Notifikasi Lengkap]
    
    USER_ACTION -->|Laporan PDF| GENERATE_PDF[Buat Laporan PDF]
    GENERATE_PDF --> SAVE_PDF[Simpan File PDF]
    SAVE_PDF --> OPEN_PDF[Buka PDF]
    
    NOTIFY_ZIP --> END
    NOTIFY_FULL --> END
    OPEN_PDF --> END
    
    END([Selesai])
```

## Integrasi Sistem

```mermaid
graph TD
    PY[Python Backend] <---> JS[Node.js WhatsApp Bot]
    PY --> EMAIL[SMTP Email System]
    JS --> WHATSAPP[WhatsApp Web Service]
    PY --> FS[File System]
    FS --> BACKUP_DIR[(Backup Directory)]
    PY --> DB[(Database - Optional)]
    
    subgraph "Python Application"
        PY
        EMAIL
        FS
    end
    
    subgraph "Node.js Services"
        JS
        WHATSAPP
    end
    
    subgraph "External Systems"
        BACKUP_DIR
        DB
    end
```

## Komponen Konfigurasi

```mermaid
graph TD
    CONFIG[Configuration System] --> CONF_FILE[config.ini]
    CONFIG --> ENV_VARS[Environment Variables]
    CONFIG --> RUNTIME[RUNTIME Settings]
    
    CONF_FILE --> EMAIL_CONF[Email Settings]
    CONF_FILE --> DB_CONF[Database Settings]
    CONF_FILE --> NOTIF_CONF[Notification Settings]
    
    ENV_VARS --> BOT_CONF[WhatsApp Bot Settings]
    ENV_VARS --> PATH_CONF[Path Settings]
    
    RUNTIME --> UI_SETTINGS[UI Preferences]
    RUNTIME --> MONITOR_SETTINGS[Monitoring Settings]
```