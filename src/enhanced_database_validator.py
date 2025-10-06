#!/usr/bin/env python3
"""
Enhanced Database Validator Module

Module yang ditingkatkan untuk menangani berbagai format database backup
termasuk file tanpa ekstensi dan mendukung pengecekan tanggal terbaru
"""

import os
import sqlite3
import zipfile
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import struct

# Import tape analyzer
from tape_file_analyzer import TapeFileAnalyzer

class EnhancedDatabaseValidator:
    def __init__(self):
        self.supported_databases = ['plantware', 'venus', 'staging', 'tape_format']
        self.temp_connections = {}
        self.database_signatures = {
            b'SQLite format 3\000': 'sqlite3',
            b'\x00\x01\x00\x00': 'ms_access',
            b'\x53\x51\x4C\x69\x74\x65': 'sqlite3_alt',
            b'\x50\x4B\x03\x04': 'zip_container',
            b'TAPE': 'tape_format',
        }
        self.tape_analyzer = TapeFileAnalyzer()

    def validate_backup_databases(self, zip_files: List[str]) -> Dict:
        """
        Validasi database dari multiple ZIP files
        Returns: Dictionary dengan hasil validasi lengkap
        """
        results = {
            'validation_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_zip_files': len(zip_files),
            'databases_found': {},
            'latest_dates': {},
            'validation_summary': {},
            'errors': [],
            'warnings': [],
            'zip_integrity': {}
        }

        for zip_file in zip_files:
            try:
                # Cek integrity ZIP terlebih dahulu
                integrity_result = self._check_zip_integrity(zip_file)
                results['zip_integrity'][os.path.basename(zip_file)] = integrity_result

                if not integrity_result['is_valid']:
                    results['errors'].append(f"ZIP file {os.path.basename(zip_file)} is corrupted: {integrity_result['error']}")
                    continue

                # Validasi database dalam ZIP
                zip_result = self._validate_single_zip(zip_file)

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

    def _check_zip_integrity(self, zip_path: str) -> Dict:
        """Cek integrity file ZIP"""
        result = {
            'is_valid': True,
            'error': None,
            'file_count': 0,
            'total_size': 0,
            'compressed_size': 0
        }

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Test ZIP integrity
                test_result = zip_ref.testzip()
                if test_result is not None:
                    result['is_valid'] = False
                    result['error'] = f"Corrupted file: {test_result}"
                    return result

                # Get file info
                file_infos = zip_ref.infolist()
                result['file_count'] = len(file_infos)

                for file_info in file_infos:
                    result['total_size'] += file_info.file_size
                    result['compressed_size'] += file_info.compress_size

        except Exception as e:
            result['is_valid'] = False
            result['error'] = str(e)

        return result

    def _validate_single_zip(self, zip_path: str) -> Dict:
        """Validasi database dalam satu file ZIP"""
        result = {
            'zip_file': os.path.basename(zip_path),
            'databases': {},
            'latest_dates': {},
            'errors': [],
            'warnings': [],
            'file_analysis': []
        }

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Cari file database (termasuk tanpa ekstensi)
                database_files = self._find_database_files(zip_ref)

                if not database_files:
                    result['warnings'].append(f"No database files found in {os.path.basename(zip_path)}")
                    return result

                # Analisis setiap file database
                for db_file in database_files:
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
                            # Ekstrak file ke temporary
                            with zip_ref.open(db_file) as source:
                                shutil.copyfileobj(source, temp_file)

                            temp_file_path = temp_file.name

                        # Analisis database
                        db_analysis = self._analyze_database_file(temp_file_path, db_file)

                        if db_analysis['database_type'] != 'unknown':
                            result['databases'][db_analysis['database_type']] = db_analysis

                            # Track latest date
                            latest_date = self._get_database_latest_date(db_analysis)
                            if latest_date:
                                result['latest_dates'][db_analysis['database_type']] = latest_date

                        # Tambahkan ke file analysis
                        result['file_analysis'].append({
                            'filename': db_file,
                            'analysis': db_analysis
                        })

                    except Exception as e:
                        result['errors'].append(f"Error analyzing {db_file}: {str(e)}")
                    finally:
                        # Clean up temp file
                        if 'temp_file_path' in locals():
                            try:
                                os.unlink(temp_file_path)
                            except:
                                pass

        except Exception as e:
            result['errors'].append(f"Error processing ZIP {zip_path}: {str(e)}")

        return result

    def _find_database_files(self, zip_ref: zipfile.ZipFile) -> List[str]:
        """Cari file database dalam ZIP (termasuk tanpa ekstensi)"""
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

            # Cek berdasarkan ukuran file (file database biasanya besar)
            if file_info.file_size > 1024 * 1024:  # > 1MB
                # Cek apakah ini adalah database dengan membaca signature
                try:
                    with zip_ref.open(filename) as f:
                        header = f.read(64)  # Baca lebih banyak untuk deteksi yang lebih baik

                        # Cek SQLite signature
                        if header.startswith(b'SQLite format 3\000'):
                            database_files.append(filename)
                            continue

                        # Cek TAPE signature (untuk Plantware P3)
                        if header.startswith(b'TAPE'):
                            database_files.append(filename)
                            continue

                        # Cek signature lainnya
                        for signature, db_type in self.database_signatures.items():
                            if header.startswith(signature):
                                database_files.append(filename)
                                break

                        # Khusus untuk file Plantware (berdasarkan nama file)
                        if any(keyword in filename.lower() for keyword in ['plantware', 'p3']):
                            # Selalu anggap sebagai database file untuk Plantware
                            database_files.append(filename)
                            continue

                except Exception as e:
                    # Jika tidak bisa dibaca, coba tambahkan saja jika ukurannya besar dan nama mencurigakan
                    if (file_info.file_size > 10 * 1024 * 1024 and  # > 10MB
                        any(keyword in filename.lower() for keyword in ['plantware', 'p3', 'venus', 'staging'])):
                        database_files.append(filename)

            # Khusus untuk file tanpa ekstensi dengan nama yang mencurigakan
            if not ext and any(keyword in filename.lower() for keyword in ['plantware', 'p3', 'venus', 'staging', 'backup']):
                database_files.append(filename)

        return database_files

    def _analyze_database_file(self, db_path: str, original_filename: str) -> Dict:
        """Analisis file database"""
        analysis = {
            'database_type': 'unknown',
            'original_filename': original_filename,
            'file_path': db_path,
            'file_size_mb': round(os.path.getsize(db_path) / (1024 * 1024), 2),
            'tables': [],
            'key_tables_info': {},
            'latest_dates': {},
            'record_counts': {},
            'table_details': {},
            'errors': [],
            'warnings': [],
            'format_info': {}
        }

        try:
            # Coba baca file header terlebih dahulu
            with open(db_path, 'rb') as f:
                header = f.read(64)

            # Cek apakah ini adalah TAPE format
            if header.startswith(b'TAPE'):
                return self._analyze_tape_database(db_path, original_filename)

            # Jika bukan TAPE, coba sebagai SQLite
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # Get database info
                cursor.execute("PRAGMA database_list")
                db_info = cursor.fetchall()

                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                analysis['tables'] = tables

                # Detect database type
                analysis['database_type'] = self._detect_database_type(tables)

                # Get table details
                for table in tables:
                    try:
                        cursor.execute(f"PRAGMA table_info({table})")
                        columns = cursor.fetchall()

                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]

                        analysis['table_details'][table] = {
                            'columns': columns,
                            'record_count': count
                        }
                    except Exception as e:
                        analysis['warnings'].append(f"Could not analyze table {table}: {e}")

                # Analyze based on database type
                if analysis['database_type'] == 'plantware':
                    analysis['key_tables_info'] = self._analyze_plantware_database(cursor)
                elif analysis['database_type'] == 'venus':
                    analysis['key_tables_info'] = self._analyze_venus_database(cursor)
                elif analysis['database_type'] == 'staging':
                    analysis['key_tables_info'] = self._analyze_staging_database(cursor)

                # Get total records
                analysis['total_records'] = sum(
                    table_info.get('record_count', 0)
                    for table_info in analysis['table_details'].values()
                )

                conn.close()

            except sqlite3.Error as e:
                analysis['errors'].append(f"SQLite error: {str(e)}")
                # Fallback ke tape analysis jika SQLite gagal
                if any(keyword in original_filename.lower() for keyword in ['plantware', 'p3']):
                    return self._analyze_tape_database(db_path, original_filename)
            except Exception as e:
                analysis['errors'].append(f"Database analysis error: {str(e)}")

        except Exception as e:
            analysis['errors'].append(f"File analysis error: {str(e)}")

        return analysis

    def _analyze_tape_database(self, db_path: str, original_filename: str) -> Dict:
        """Analisis database format TAPE"""
        analysis = {
            'database_type': 'tape_format',
            'original_filename': original_filename,
            'file_path': db_path,
            'file_size_mb': round(os.path.getsize(db_path) / (1024 * 1024), 2),
            'tables': [],
            'key_tables_info': {},
            'latest_dates': {},
            'record_counts': {},
            'table_details': {},
            'errors': [],
            'warnings': [],
            'format_info': {}
        }

        try:
            # Gunakan tape analyzer untuk analisis
            tape_analysis = self.tape_analyzer.analyze_tape_file(db_path, original_filename)

            # Convert tape analysis ke database analysis format
            analysis['format_info'] = tape_analysis
            analysis['database_type'] = 'plantware'  # Asumsi Plantware untuk TAPE format

            # Extract information from tape analysis
            if tape_analysis.get('date_info'):
                analysis['latest_dates'] = tape_analysis['date_info']

            if tape_analysis.get('estimated_records'):
                analysis['record_counts']['total_estimated'] = tape_analysis['estimated_records']

            if tape_analysis.get('header_info'):
                analysis['format_info']['header'] = tape_analysis['header_info']

            # Extract tanggal dari filename
            if 'filename_date' in tape_analysis.get('date_info', {}):
                analysis['latest_dates']['filename_date'] = tape_analysis['date_info']['filename_date']

            # Add analysis notes
            analysis['warnings'].extend(tape_analysis.get('warnings', []))
            analysis['errors'].extend(tape_analysis.get('errors', []))

            # Add specific information about tape format
            analysis['format_info']['format_type'] = 'TAPE (Plantware P3 Backup)'
            analysis['format_info']['readable'] = False
            analysis['format_info']['requires_special_tools'] = True

            # Estimasi total records
            estimated_records = tape_analysis.get('estimated_records', 0)
            analysis['record_counts']['total_estimated'] = estimated_records
            analysis['total_records'] = estimated_records

        except Exception as e:
            analysis['errors'].append(f"Tape analysis error: {str(e)}")

        return analysis

    def _detect_database_type(self, tables: List[str]) -> str:
        """Detect database type based on table names"""
        # Jika tables kosong (biasanya untuk tape format), cek berdasarkan format info
        if not tables:
            return 'plantware'  # Asumsi Plantware untuk tape format

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

        # Jika tidak ada tables yang terdeteksi, tapi file besar, kemungkinan Plantware tape format
        return 'plantware'

    def _analyze_plantware_database(self, cursor) -> Dict:
        """Analyze Plantware database specifically"""
        info = {}

        # Analyze PR_TASKREG table
        if self._table_exists(cursor, 'PR_TASKREG'):
            info['PR_TASKREG'] = self._analyze_table_with_dates(
                cursor, 'PR_TASKREG',
                ['TASK_DATE', 'CREATED_DATE', 'MODIFIED_DATE', 'START_DATE', 'END_DATE']
            )

        # Analyze PR_TASK table
        if self._table_exists(cursor, 'PR_TASK'):
            info['PR_TASK'] = self._analyze_table_with_dates(
                cursor, 'PR_TASK',
                ['TASK_DATE', 'CREATED_DATE', 'MODIFIED_DATE']
            )

        # Analyze PR_PROJECT table
        if self._table_exists(cursor, 'PR_PROJECT'):
            info['PR_PROJECT'] = self._analyze_table_with_dates(
                cursor, 'PR_PROJECT',
                ['PROJECT_DATE', 'CREATED_DATE', 'MODIFIED_DATE']
            )

        return info

    def _analyze_venus_database(self, cursor) -> Dict:
        """Analyze Venus database specifically"""
        info = {}

        # Analyze TA_TRANSACTION table
        if self._table_exists(cursor, 'TA_TRANSACTION'):
            info['TA_TRANSACTION'] = self._analyze_table_with_dates(
                cursor, 'TA_TRANSACTION',
                ['TRANSACTION_DATE', 'CREATE_DATE', 'LOG_DATE']
            )

        # Analyze TA_MACHINE table
        if self._table_exists(cursor, 'TA_MACHINE'):
            info['TA_MACHINE'] = self._analyze_table_with_dates(
                cursor, 'TA_MACHINE',
                ['INSTALL_DATE', 'LAST_SERVICE_DATE']
            )

        return info

    def _analyze_staging_database(self, cursor) -> Dict:
        """Analyze Staging database specifically"""
        info = {}

        # Analyze GWSCANNER table
        if self._table_exists(cursor, 'GWSCANNER'):
            info['GWSCANNER'] = self._analyze_table_with_dates(
                cursor, 'GWSCANNER',
                ['SCAN_DATE', 'CREATE_DATE', 'UPDATE_DATE']
            )

        # Analyze GW_TRANSACTION table
        if self._table_exists(cursor, 'GW_TRANSACTION'):
            info['GW_TRANSACTION'] = self._analyze_table_with_dates(
                cursor, 'GW_TRANSACTION',
                ['TRANSACTION_DATE', 'CREATE_DATE']
            )

        return info

    def _table_exists(self, cursor, table_name: str) -> bool:
        """Check if table exists"""
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            return cursor.fetchone() is not None
        except:
            return False

    def _analyze_table_with_dates(self, cursor, table_name: str, date_columns: List[str]) -> Dict:
        """Analyze table with date columns"""
        info = {
            'record_count': 0,
            'date_columns_found': [],
            'latest_dates': {},
            'recent_records': {}
        }

        try:
            # Get record count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            info['record_count'] = cursor.fetchone()[0]

            # Check which date columns exist
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]

            for date_col in date_columns:
                if date_col in columns:
                    info['date_columns_found'].append(date_col)

                    # Get latest date
                    try:
                        cursor.execute(f"SELECT MAX({date_col}) FROM {table_name} WHERE {date_col} IS NOT NULL")
                        latest_date = cursor.fetchone()[0]
                        if latest_date:
                            info['latest_dates'][date_col] = latest_date
                    except:
                        pass

                    # Get recent records count (last 30 days)
                    try:
                        thirty_days_ago = datetime.now() - timedelta(days=30)
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {date_col} >= ?",
                                     (thirty_days_ago.strftime('%Y-%m-%d'),))
                        recent_count = cursor.fetchone()[0]
                        info['recent_records'][date_col] = recent_count
                    except:
                        pass

        except Exception as e:
            info['error'] = str(e)

        return info

    def _get_database_latest_date(self, db_analysis: Dict) -> Optional[str]:
        """Get latest date from database analysis"""
        latest_date = None

        # Check key tables info
        for table_info in db_analysis.get('key_tables_info', {}).values():
            for date_col, date_val in table_info.get('latest_dates', {}).items():
                if date_val and (latest_date is None or date_val > latest_date):
                    latest_date = date_val

        # Check table details
        for table_detail in db_analysis.get('table_details', {}).values():
            for date_col, date_val in table_detail.get('latest_dates', {}).items():
                if date_val and (latest_date is None or date_val > latest_date):
                    latest_date = date_val

        return latest_date

    def get_database_summary(self, validation_result: Dict) -> str:
        """Generate human-readable summary of validation results"""
        summary = []

        summary.append("DATABASE VALIDATION SUMMARY")
        summary.append("=" * 50)
        summary.append(f"ZIP Files Processed: {validation_result['total_zip_files']}")
        summary.append(f"Validation Time: {validation_result['validation_timestamp']}")
        summary.append("")

        # ZIP Integrity
        summary.append("ZIP INTEGRITY CHECK:")
        for zip_name, integrity in validation_result.get('zip_integrity', {}).items():
            status = "[OK] Valid" if integrity['is_valid'] else "[ERROR] Corrupted"
            summary.append(f"   {zip_name}: {status}")
            if not integrity['is_valid']:
                summary.append(f"      Error: {integrity['error']}")
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

                # Additional info for tape format
                if 'database_info' in db_info and db_info['database_info'].get('format_info'):
                    format_info = db_info['database_info']['format_info']
                    if format_info.get('format_type') == 'TAPE (Plantware P3 Backup)':
                        summary.append(f"        Format: {format_info['format_type']}")
                        summary.append(f"        Size: {db_info['database_info']['file_size_mb']:.2f} MB")
                        summary.append(f"        Status: Requires special tools to read")

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
def test_enhanced_validator():
    """Test the enhanced validator"""
    validator = EnhancedDatabaseValidator()

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
    test_enhanced_validator()