# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Database Backup Monitoring and Notification System** written in Python. The application monitors backup folders, validates ZIP files and database backups, extracts metadata, and sends email notifications about backup status and health.

## Common Commands

### Running the Application
```bash
# Main GUI application
python main.py

# Alternative GUI applications
python main_app.py
python main_app_backup.py
python main_app_refactored.py
```

### Testing Components
```bash
# Test backup analysis
python test_bak_analysis.py

# Test ZIP integrity checking
python check_bak_header.py

# Test PDF report generation
python test_pdf_system.py
python test_gui_pdf.py

# Test ZIP metadata viewer
python src/zip_metadata_viewer.py

# Test enhanced database validator
python src/enhanced_database_validator.py
```

### Configuration
- Configuration file: `config/config.ini`
- Email settings, database paths, and monitoring intervals are configured here

## Architecture Overview

### Core Components

1. **GUI Layer** (`src/gui.py`, `main_app*.py`)
   - Tkinter-based desktop application
   - Multiple entry points with different feature sets
   - Real-time monitoring controls and status display

2. **Monitoring Engine** (`src/monitoring_controller.py`)
   - Central coordination of all monitoring activities
   - ZIP file discovery and validation
   - Database analysis and health assessment
   - Date synchronization analysis

3. **Database Validators** (`src/enhanced_database_validator.py`, `src/database_validator.py`)
   - Multiple database format support (SQLite, Plantware TAPE format, Venus, Staging)
   - Backup file integrity checking
   - Metadata extraction and analysis
   - Table-specific analysis for different database types

4. **ZIP File Processing** (`src/zip_metadata_viewer.py`, `src/zip_validator.py`)
   - ZIP integrity validation
   - Metadata extraction (file lists, sizes, dates)
   - BAK file discovery within ZIP archives
   - Compression analysis

5. **Notification System** (`src/email_notifier.py`)
   - Email alert generation
   - HTML-formatted reports
   - Automatic monitoring alerts
   - Backup health summaries

6. **File Analysis** (`src/tape_file_analyzer.py`, `src/bak_file_reader.py`)
   - Plantware P3 TAPE format analysis
   - SQL Server backup file processing
   - Header parsing and validation

### Key Design Patterns

**Modular Architecture**: Each component is independently testable and replaceable
**Factory Pattern**: Database type detection and appropriate analyzer selection
**Observer Pattern**: Real-time GUI updates during background processing
**Strategy Pattern**: Different validation strategies for various database formats

### Database Support

- **SQLite3**: Standard SQLite databases
- **Plantware P3**: Proprietary TAPE format backup files
- **Venus**: Time attendance system databases
- **Staging**: GWScanner and related staging databases
- **SQL Server**: Via `sqlcmd` integration for restore operations

### Data Flow

1. **File Discovery**: Scan backup folders for ZIP files
2. **ZIP Validation**: Check integrity and extract metadata
3. **Database Detection**: Identify database types within ZIP files
4. **Content Analysis**: Extract table information, record counts, latest dates
5. **Health Assessment**: Compare backup dates, check for issues
6. **Reporting**: Generate HTML reports and send email notifications
7. **Monitoring**: Continuous background monitoring with alerts

## Important Implementation Details

### Configuration Management
- Uses `configparser` for INI file handling
- Email credentials stored in plain text (security consideration)
- Database paths and query tables configurable
- Monitoring intervals adjustable

### Error Handling
- Comprehensive exception handling throughout
- Graceful degradation for unsupported formats
- Detailed error logging and user feedback
- Continue processing even when some files fail

### Background Processing
- Threading for all long-running operations
- Progress indicators and status updates
- Non-blocking GUI operations
- Thread-safe logging and status updates

### Database Type Detection
- File header analysis for signature detection
- Filename pattern matching
- Table name analysis for SQLite databases
- Fallback mechanisms for unknown formats

### Date Synchronization
- Multi-source date extraction (file dates, database records, filenames)
- Cross-referencing between ZIP creation and database latest records
- Gap analysis and health scoring
- Automated recommendations based on date discrepancies

## Testing and Development

### Test Files Available
- `test_*.py` files for component testing
- Dummy data generation for testing
- Integration tests for email functionality
- GUI component tests

### Development Notes
- Python 3.10+ required
- Uses standard library modules primarily
- Some Windows-specific dependencies (`sqlcmd`, path handling)
- Email functionality requires SMTP server access

## Security Considerations

- Email credentials stored in config file (consider environment variables)
- File system access for backup folder scanning
- Database connection handling with proper cleanup
- Temporary file management with automatic cleanup