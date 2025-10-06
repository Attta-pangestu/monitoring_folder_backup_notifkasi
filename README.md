# Backup Monitor Application
## Comprehensive Database Backup Monitoring System

### Overview
Backup Monitor is a comprehensive database backup monitoring system with a PyQt5-based desktop interface. This application is designed to analyze, verify, and provide automatic notifications about database backup files in ZIP and BAK formats.

### Key Features
- ✅ **ZIP File Analysis**: Metadata extraction, integrity checking, and file listing
- ✅ **BAK File Validation**: SQL Server backup analysis without database connection
- ✅ **Multi-channel Notifications**: Email and WhatsApp
- ✅ **Comprehensive PDF Reports**: Generate detailed reports in PDF format
- ✅ **Automatic Extraction**: Batch extract and analyze backup files
- ✅ **Real-time Monitoring**: Detect and analyze new backup files automatically

### Technologies Used
- **Programming Language**: Python 3.x
- **UI Framework**: PyQt5 (Desktop GUI)
- **Processing Backend**: Python Standard Library + ReportLab
- **WhatsApp Service**: Node.js with whatsapp-web.js
- **Email System**: SMTP with Gmail
- **Package Management**: pip (Python) and npm (Node.js)

## Directory Structure

```
Backup_Monitor/
├── backup_monitor_qt.py          # Main application entry point
├── backup_monitor_methods.py     # Additional application methods
├── config/
│   └── config.ini                # System configuration
├── src/                          # Core application modules
│   ├── zip_metadata_viewer.py    # ZIP metadata analysis
│   ├── bak_metadata_analyzer.py  # BAK metadata analysis
│   ├── database_validator.py     # Database structure validation
│   ├── email_notifier.py          # Email notification system
│   ├── pdf_report_generator.py    # PDF report generator
│   ├── enhanced_zip_analyzer.py   # Advanced ZIP analysis
│   ├── enhanced_bak_analyzer.py  # Advanced BAK analysis
│   ├── enhanced_email_notifier.py # Enhanced email notifications
│   └── ...                       # Other supporting modules
├── wa_bot/                       # WhatsApp bot service
│   ├── server.js                 # Node.js HTTP server
│   ├── whatsappService.js        # WhatsApp Web service
│   ├── backupService.js          # Backup automation service
│   ├── simple_wa_bot.py          # Python integration with WhatsApp
│   └── package.json              # Node.js dependencies
├── ARCHITECTURE_DIAGRAM.md       # Application architecture diagram
├── EXECUTIVE_SUMMARY.md          # Executive summary of architecture
└── ARCHITECTURE_PRESENTATION.md  # Architecture presentation
```

## Installation and Setup

### Prerequisites
- Python 3.7+
- Node.js 14+
- Internet access for WhatsApp notifications
- Gmail account for email notifications

### Installing Python Dependencies
```bash
pip install -r requirements.txt
```

Main dependencies:
- PyQt5
- reportlab
- sqlalchemy
- python-dotenv

### Installing Node.js Dependencies
```bash
cd wa_bot
npm install
```

Main dependencies:
- whatsapp-web.js
- express
- puppeteer

### Configuration
1. Copy `config/config.ini.example` to `config/config.ini`
2. Edit email and notification settings
3. Adjust backup paths according to your environment

Example configuration:
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

## Usage

### Running the Application
```bash
python backup_monitor_qt.py
```

### Main Application Features

#### 1. ZIP File Analysis
- Select backup folder
- Click analysis button
- View ZIP metadata and file integrity

#### 2. Extraction and BAK Analysis
- Select ZIP backup file
- Click "Extract & Analyze"
- View BAK file analysis results

#### 3. PDF Reports
- Use "Generate PDF Report" button
- Save report to desired location
- Open report for review

#### 4. Automatic Notifications
- Configure email in `config/config.ini`
- Enable automatic monitoring
- Receive notifications for new backups

### Using WhatsApp Bot
```bash
cd wa_bot
node server.js
```

Access dashboard at `http://localhost:3000` to connect WhatsApp.

## Application Architecture

### Core Components

#### 1. User Interface (`backup_monitor_qt.py`)
Desktop interface based on PyQt5 that provides:
- File browser for backup directory
- Control panel for various actions
- Progress bar for long operations
- Analysis results area with organized tabs

UI Architecture:
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
Thread-based worker system for background processing:
- **BackupAnalysisWorker**: Analyzes ZIP and BAK files
- **EmailWorker**: Sends email notifications
- **MonitoringController**: Controls automatic monitoring

#### 3. Analysis Modules
Specific analysis modules for different file types:
- **ZIP Metadata Viewer**: ZIP file analysis
- **BAK Metadata Analyzer**: SQL Server BAK file analysis
- **Database Validator**: Database structure validation
- **PDF Report Generator**: PDF report creation

#### 4. Notification System
Multi-channel notification system:
- **Email Notifier**: Email sending with SMTP
- **WhatsApp Service**: Notifications via WhatsApp Web
- **Enhanced Notifiers**: Advanced templates and features

### Application Workflow

#### Startup Process
1. **Application Initialization**
   ```
   User opens application → Load configuration → Setup UI → 
   Initialize thread pool → Scan backup folder → Display ZIP files
   ```

2. **Manual Analysis**
   ```
   User selects ZIP file → Click action button → 
   Worker thread starts process → Show progress → 
   Results displayed in UI → Option to send notifications/reports
   ```

3. **Batch Processing**
   ```
   User clicks "Extract All" → Confirm extraction → 
   Process ZIP file extraction one by one → 
   Analyze extracted BAK files → 
   Generate comprehensive report → Send notifications/email
   ```

4. **Automatic Monitoring**
   ```
   Monitoring system runs → Detect latest backups → 
   Automatic analysis → Generate report → 
   Send email/WhatsApp → Update UI status
   ```

## API and Integration

### REST API (WhatsApp Service)
Main endpoints:
- `GET /health` - Service health status
- `POST /notify` - Send custom notifications
- `POST /backup/report` - Send backup reports
- `GET /status` - System monitoring status

### Python Integration
Python modules can be used independently:
```python
from src.zip_metadata_viewer import ZipMetadataViewer
from src.bak_metadata_analyzer import BAKMetadataAnalyzer
from src.email_notifier import EmailNotifier

# Usage example
viewer = ZipMetadataViewer()
metadata = viewer.extract_zip_metadata("backup.zip")
```

## Security and Best Practices

### Credential Management
- Email passwords stored in `config.ini`
- Use App Password for Gmail (not main account password)
- Environment variables for sensitive secrets

### File Access Control
- File path validation to prevent directory traversal
- Permission checking before file operations
- Automatic temporary file cleanup

### Error Handling
- Comprehensive logging for debugging
- Graceful degradation when components fail
- User-friendly error messages

## Development and Contributing

### Development Structure
```
src/
├── __init__.py
├── zip_metadata_viewer.py     # ZIP file analysis
├── bak_metadata_analyzer.py   # BAK file analysis  
├── database_validator.py      # Database validation
├── email_notifier.py           # Email notifications
├── pdf_report_generator.py    # PDF reports
└── ...
```

### Testing
Unit testing using Python unittest:
```bash
python -m unittest discover tests/
```

### Contributing Guidelines
1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

### Coding Standards
- PEP 8 for Python code style
- Docstrings for function documentation
- Type hints for parameters and return values
- Comments for complex logic

## Troubleshooting

### Common Issues

#### 1. Email Notifications Not Sent
- Check email credentials in `config.ini`
- Ensure App Password is used (not Gmail account password)
- Verify internet connection

#### 2. WhatsApp Bot Not Connecting
- Ensure Node.js version 14+ is installed
- Run `npm install` in `wa_bot` directory
- Check internet connection and firewall

#### 3. Error Reading ZIP Files
- Check ZIP file integrity
- Ensure file is not being used by another application
- Verify file access permissions

### Logging
Application logs available at:
- `backup_monitor.log` for general logs
- `backup_monitor_debug.log` for detailed debugging

Use appropriate logging level:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

## License and Support

### License
This application is released under the MIT license. See `LICENSE` file for details.

### Support
For technical support:
- Open issues in GitHub repository
- Contact development team for enterprise support
- Consult application documentation and logs

### Community
Join user community for:
- Sharing usage experiences
- Getting tips and tricks
- Contributing to new feature development

---

*This documentation was automatically generated based on source code analysis. For more detailed information about application architecture, see `ARCHITECTURE_DIAGRAM.md` and `EXECUTIVE_SUMMARY.md` files.*