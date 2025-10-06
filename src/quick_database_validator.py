#!/usr/bin/env python3
"""
Quick Database Validator Module
Versi cepat untuk mendeteksi dan mengecek database tanpa membuka seluruh file
"""

import os
import sqlite3
import zipfile
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Optional

class QuickDatabaseValidator:
    def __init__(self):
        self.supported_databases = ['plantware', 'venus', 'staging']

    def validate_backup_databases(self, zip_files: List[str]) -> Dict:
        """
        Validasi database dari multiple ZIP files (versi cepat)
        """
        results = {
            'validation_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_zip_files': len(zip_files),
            'databases_found': {},
            'latest_dates': {},
            'errors': [],
            'warnings': []
        }

        for zip_file in zip_files:
            try:
                zip_result = self._validate_single_zip_quick(zip_file)

                # Merge results
                for db_type, db_info in zip_result.get('databases', {}).items():
                    if db_type not in results['databases_found']:
                        results['databases_found'][db_type] = []
                    results['databases_found'][db_type].append({
                        'zip_file': os.path.basename(zip_file),
                        'zip_path': zip_file,
                        'database_info': db_info,
                        'latest_date': zip_result.get('latest_dates', {}).get(db_type),
                        'record_count': db_info.get('total_records', 0)
                    })

                # Merge latest dates
                for db_type, latest_date in zip_result.get('latest_dates', {}).items():
                    if db_type not in results['latest_dates'] or latest_date > results['latest_dates'][db_type]:
                        results['latest_dates'][db_type] = latest_date

                # Merge errors and warnings
                results['errors'].extend(zip_result.get('errors', []))
                results['warnings'].extend(zip_result.get('warnings', []))

            except Exception as e:
                results['errors'].append(f"Error processing ZIP {zip_file}: {str(e)}")

        return results

    def _validate_single_zip_quick(self, zip_path: str) -> Dict:
        """Validasi database dalam satu file ZIP (versi cepat)"""
        result = {
            'zip_file': os.path.basename(zip_path),
            'databases': {},
            'latest_dates': {},
            'errors': [],
            'warnings': []
        }

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Cek integrity ZIP
                try:
                    test_result = zip_ref.testzip()
                    if test_result is not None:
                        result['errors'].append(f"ZIP file corrupted: {test_result}")
                        return result
                except Exception as e:
                    result['errors'].append(f"ZIP integrity check failed: {e}")
                    return result

                # Cari file database
                database_files = self._find_database_files_quick(zip_ref)

                if not database_files:
                    result['warnings'].append(f"No database files found in {os.path.basename(zip_path)}")
                    return result

                # Analisis setiap file database (coba yang pertama saja)
                for db_file in database_files[:1]:  # Coba hanya file pertama
                    try:
                        db_analysis = self._analyze_database_quick(zip_ref, db_file)

                        if db_analysis['database_type'] != 'unknown':
                            result['databases'][db_analysis['database_type']] = db_analysis

                            # Track latest date
                            latest_date = self._get_database_latest_date(db_analysis)
                            if latest_date:
                                result['latest_dates'][db_analysis['database_type']] = latest_date

                        break  # Hanya proses satu file database

                    except Exception as e:
                        result['errors'].append(f"Error analyzing {db_file}: {str(e)}")

        except Exception as e:
            result['errors'].append(f"Error processing ZIP {zip_path}: {str(e)}")

        return result

    def _find_database_files_quick(self, zip_ref: zipfile.ZipFile) -> List[str]:
        """Cari file database dalam ZIP (versi cepat)"""
        database_files = []

        for file_info in zip_ref.infolist():
            filename = file_info.filename

            # Skip directories
            if filename.endswith('/'):
                continue

            # Cek berdasarkan ekstensi
            ext = os.path.splitext(filename)[1].lower()
            known_db_extensions = ['.bak', '.db', '.mdf', '.ldf', '.dbf', '.mdb', '.accdb', '.sqlite', '.sqlite3']

            if ext in known_db_extensions:
                database_files.append(filename)
                continue

            # Cek berdasarkan nama file dan ukuran
            if (file_info.file_size > 1024 * 1024 and  # > 1MB
                any(keyword in filename.lower() for keyword in ['plantware', 'p3', 'venus', 'staging', 'backup'])):
                database_files.append(filename)

        return database_files

    def _analyze_database_quick(self, zip_ref: zipfile.ZipFile, db_filename: str) -> Dict:
        """Analisis file database (versi cepat)"""
        analysis = {
            'database_type': 'unknown',
            'filename': db_filename,
            'file_size_mb': 0,
            'tables': [],
            'total_records': 0,
            'latest_dates': {},
            'errors': [],
            'warnings': []
        }

        try:
            # Get file info
            file_info = None
            for info in zip_ref.infolist():
                if info.filename == db_filename:
                    file_info = info
                    break

            if not file_info:
                analysis['errors'].append("File not found in ZIP")
                return analysis

            analysis['file_size_mb'] = round(file_info.file_size / (1024 * 1024), 2)

            # Extract file header untuk deteksi
            try:
                with zip_ref.open(db_filename) as f:
                    header = f.read(100)  # Baca header

                    # Cek SQLite signature
                    if header.startswith(b'SQLite format 3\000'):
                        # Buka database dengan SQLite
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
                            # Copy file ke temp
                            zip_ref.extract(db_filename, temp_dir=os.path.dirname(temp_file.name))
                            temp_file_path = temp_file.name

                        try:
                            conn = sqlite3.connect(temp_file_path)
                            cursor = conn.cursor()

                            # Get all tables
                            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                            tables = [row[0] for row in cursor.fetchall()]
                            analysis['tables'] = tables

                            # Detect database type
                            analysis['database_type'] = self._detect_database_type(tables)

                            # Get total records dari beberapa tabel utama
                            total_records = 0
                            latest_date = None

                            for table in tables:
                                try:
                                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                                    count = cursor.fetchone()[0]
                                    total_records += count

                                    # Coba cari tanggal terbaru
                                    latest_date = self._find_latest_date_in_table(cursor, table, latest_date)

                                except:
                                    pass

                            analysis['total_records'] = total_records
                            if latest_date:
                                analysis['latest_dates']['overall'] = latest_date

                            conn.close()

                        except Exception as e:
                            analysis['errors'].append(f"Database analysis error: {e}")
                        finally:
                            # Clean up
                            try:
                                os.unlink(temp_file_path)
                            except:
                                pass

                    else:
                        analysis['warnings'].append("File is not a SQLite database")

            except Exception as e:
                analysis['errors'].append(f"Error reading file: {e}")

        except Exception as e:
            analysis['errors'].append(f"Analysis error: {e}")

        return analysis

    def _detect_database_type(self, tables: List[str]) -> str:
        """Detect database type based on table names"""
        table_names_upper = [t.upper() for t in tables]

        # Check for Plantware specific tables
        plantware_indicators = ['PR_TASKREG', 'PR_TASK', 'PR_PROJECT', 'PR_USER', 'PR_DEPARTMENT']
        if any(indicator in table_names_upper for indicator in plantware_indicators):
            return 'plantware'

        # Check for Venus specific tables
        venus_indicators = ['TA_MACHINE', 'TA_TRANSACTION', 'TA_LOG', 'TA_EMPLOYEE']
        if any(indicator in table_names_upper for indicator in venus_indicators):
            return 'venus'

        # Check for Staging specific tables
        staging_indicators = ['GWSCANNER', 'GW_LOG', 'SCANNER_DATA', 'GW_TRANSACTION']
        if any(indicator in table_names_upper for indicator in staging_indicators):
            return 'staging'

        return 'unknown'

    def _find_latest_date_in_table(self, cursor, table_name: str, current_latest: Optional[str]) -> Optional[str]:
        """Cari tanggal terbaru di tabel"""
        try:
            # Coba beberapa kolom tanggal yang umum
            date_columns = ['DATE', 'TIME', 'DATETIME', 'CREATED_DATE', 'MODIFIED_DATE',
                           'TASK_DATE', 'TRANSACTION_DATE', 'SCAN_DATE', 'LOG_DATE']

            # Get table columns
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]

            # Cari kolom yang mengandung tanggal
            for col in columns:
                col_upper = col.upper()
                if any(date_col in col_upper for date_col in date_columns):
                    try:
                        cursor.execute(f"SELECT MAX({col}) FROM {table_name} WHERE {col} IS NOT NULL")
                        max_date = cursor.fetchone()[0]
                        if max_date:
                            if current_latest is None or max_date > current_latest:
                                current_latest = max_date
                    except:
                        pass

        except Exception:
            pass

        return current_latest

    def _get_database_latest_date(self, db_analysis: Dict) -> Optional[str]:
        """Get latest date from database analysis"""
        return db_analysis.get('latest_dates', {}).get('overall')

    def get_database_summary(self, validation_result: Dict) -> str:
        """Generate human-readable summary of validation results"""
        summary = []

        summary.append("DATABASE VALIDATION SUMMARY")
        summary.append("=" * 50)
        summary.append(f"ZIP Files Processed: {validation_result['total_zip_files']}")
        summary.append(f"Validation Time: {validation_result['validation_timestamp']}")
        summary.append("")

        # Databases Found
        summary.append("DATABASES FOUND:")
        for db_type, db_list in validation_result.get('databases_found', {}).items():
            summary.append(f"   {db_type.upper()}: {len(db_list)} files")
            for db_info in db_list:
                summary.append(f"      * {db_info['zip_file']}")
                if db_info.get('latest_date'):
                    summary.append(f"        Latest Date: {db_info['latest_date']}")
                if db_info.get('record_count'):
                    summary.append(f"        Records: {db_info['record_count']:,}")
                if db_info.get('database_info', {}).get('file_size_mb'):
                    summary.append(f"        Size: {db_info['database_info']['file_size_mb']:.2f} MB")
        summary.append("")

        # Latest Dates
        summary.append("LATEST DATES:")
        for db_type, latest_date in validation_result.get('latest_dates', {}).items():
            summary.append(f"   {db_type.upper()}: {latest_date}")
        summary.append("")

        # Errors and Warnings
        if validation_result.get('errors'):
            summary.append("ERRORS:")
            for error in validation_result['errors']:
                summary.append(f"   * {error}")
            summary.append("")

        if validation_result.get('warnings'):
            summary.append("WARNINGS:")
            for warning in validation_result['warnings']:
                summary.append(f"   * {warning}")
            summary.append("")

        return "\n".join(summary)

# Test function
def test_quick_validator():
    """Test the quick validator"""
    validator = QuickDatabaseValidator()

    # Test with the specific file
    test_file = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup\PlantwareP3 2025-10-04 11;33;53.zip"

    if os.path.exists(test_file):
        print(f"Testing with: {test_file}")
        result = validator.validate_backup_databases([test_file])

        print("\nValidation Result:")
        print(validator.get_database_summary(result))
    else:
        print(f"Test file not found: {test_file}")

if __name__ == "__main__":
    test_quick_validator()