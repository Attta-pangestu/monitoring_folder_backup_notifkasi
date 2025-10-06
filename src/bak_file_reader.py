#!/usr/bin/env python3
"""
BAK File Reader Module
Tool khusus untuk membaca file .bak (database backup) langsung tanpa restore
"""

import os
import sqlite3
import zipfile
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import struct
import pandas as pd
from pathlib import Path

class BAKFileReader:
    def __init__(self):
        self.supported_formats = ['sqlite', 'tape', 'mysql', 'postgres']
        self.temp_extract_path = None
        self.current_connection = None

    def __del__(self):
        """Cleanup temp files"""
        self.cleanup()

    def cleanup(self):
        """Clean up temporary files and connections"""
        if self.current_connection:
            self.current_connection.close()
            self.current_connection = None

        if self.temp_extract_path and os.path.exists(self.temp_extract_path):
            try:
                shutil.rmtree(self.temp_extract_path)
            except:
                pass
            self.temp_extract_path = None

    def read_bak_file(self, file_path: str, extract_to_same_folder: bool = True) -> Dict:
        """
        Membaca file .bak dari berbagai sumber (ZIP atau langsung)

        Args:
            file_path: Path ke file .bak atau file ZIP yang berisi .bak
            extract_to_same_folder: Jika True, ekstrak ke folder yang sama dengan file ZIP
        """
        result = {
            'success': False,
            'file_type': 'unknown',
            'database_info': {},
            'tables': {},
            'extracted_path': None,
            'errors': [],
            'warnings': []
        }

        try:
            # Cleanup previous temp files
            self.cleanup()

            # Cek apakah file adalah ZIP
            if file_path.lower().endswith('.zip'):
                return self._read_bak_from_zip(file_path, extract_to_same_folder)
            elif file_path.lower().endswith(('.bak', '.db', '.sqlite', '.sqlite3')):
                return self._read_bak_direct(file_path)
            else:
                result['errors'].append("Unsupported file format. Only .zip, .bak, .db, .sqlite files are supported.")
                return result

        except Exception as e:
            result['errors'].append(f"Error reading BAK file: {str(e)}")
            return result

    def _read_bak_from_zip(self, zip_path: str, extract_to_same_folder: bool) -> Dict:
        """Membaca file .bak dari dalam ZIP"""
        result = {
            'success': False,
            'file_type': 'zip_container',
            'database_info': {},
            'tables': {},
            'extracted_path': None,
            'errors': [],
            'warnings': [],
            'zip_info': {}
        }

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Cari file .bak dalam ZIP atau file tanpa ekstensi yang mungkin database
                bak_files = []
                for f in zip_ref.namelist():
                    if f.lower().endswith('.bak'):
                        bak_files.append(f)
                    elif '.' not in f:  # File tanpa ekstensi
                        # Check file size - database files biasanya besar
                        info = zip_ref.getinfo(f)
                        if info.file_size > 1024 * 1024:  # > 1MB
                            bak_files.append(f)

                if not bak_files:
                    result['errors'].append("No .bak files found in ZIP")
                    return result

                # Gunakan file .bak pertama yang ditemukan
                bak_file = bak_files[0]
                result['zip_info']['bak_file'] = bak_file
                result['zip_info']['total_files'] = len(zip_ref.namelist())

                # Tentukan path ekstraksi
                if extract_to_same_folder:
                    extract_dir = os.path.dirname(zip_path)
                else:
                    extract_dir = tempfile.mkdtemp(prefix='bak_extract_')
                    self.temp_extract_path = extract_dir

                # Ekstrak file .bak
                extract_path = os.path.join(extract_dir, os.path.basename(bak_file))
                zip_ref.extract(bak_file, extract_dir)

                result['extracted_path'] = extract_path
                result['zip_info']['extracted_to'] = extract_path

                # Baca file .bak yang diekstrak
                bak_result = self._read_bak_direct(extract_path)

                # Merge results
                result.update(bak_result)
                result['success'] = bak_result['success']

                # Hapus file ekstrak setelah selesai dibaca
                if result.get('success', False) or True:  # Selalu hapus file ekstrak
                    try:
                        if os.path.exists(extract_path):
                            os.unlink(extract_path)
                            result['extracted_path'] = None
                            result['cleanup_note'] = f"Extracted file {extract_path} has been deleted"
                    except Exception as e:
                        result['warnings'].append(f"Could not delete extracted file {extract_path}: {e}")

        except Exception as e:
            result['errors'].append(f"Error reading ZIP file: {str(e)}")

        return result

    def _read_bak_direct(self, bak_path: str) -> Dict:
        """Membaca file .bak langsung"""
        result = {
            'success': False,
            'file_type': 'unknown',
            'database_info': {},
            'tables': {},
            'extracted_path': bak_path,
            'errors': [],
            'warnings': []
        }

        try:
            # Cek file signature untuk menentukan format
            with open(bak_path, 'rb') as f:
                header = f.read(32)

            # Deteksi format berdasarkan signature
            if header.startswith(b'SQLite format 3\000'):
                return self._read_sqlite_bak(bak_path)
            elif header.startswith(b'TAPE'):
                return self._read_tape_bak(bak_path)
            else:
                # Coba sebagai SQLite anyway
                try:
                    return self._read_sqlite_bak(bak_path)
                except:
                    result['errors'].append("Unknown or unsupported database format")
                    return result

        except Exception as e:
            result['errors'].append(f"Error reading BAK file: {str(e)}")
            return result

    def _read_sqlite_bak(self, bak_path: str) -> Dict:
        """Membaca file .bak format SQLite"""
        result = {
            'success': False,
            'file_type': 'sqlite',
            'database_info': {},
            'tables': {},
            'extracted_path': bak_path,
            'errors': [],
            'warnings': []
        }

        try:
            # Connect to database
            conn = sqlite3.connect(bak_path)
            self.current_connection = conn
            cursor = conn.cursor()

            # Get database info
            cursor.execute("PRAGMA database_list")
            db_info = cursor.fetchall()
            result['database_info']['databases'] = db_info

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
            result['database_info']['tables'] = tables
            result['database_info']['table_count'] = len(tables)

            # Analyze each table
            for table in tables:
                try:
                    table_info = self._analyze_sqlite_table(cursor, table)
                    result['tables'][table] = table_info
                except Exception as e:
                    result['warnings'].append(f"Could not analyze table {table}: {e}")

            # Get database metadata
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]

            result['database_info']['page_size'] = page_size
            result['database_info']['page_count'] = page_count
            result['database_info']['total_size'] = page_size * page_count

            # Detect database type
            db_type = self._detect_sqlite_database_type(tables)
            result['database_info']['detected_type'] = db_type

            result['success'] = True

        except sqlite3.Error as e:
            result['errors'].append(f"SQLite error: {str(e)}")
        except Exception as e:
            result['errors'].append(f"Database analysis error: {str(e)}")

        return result

    def _analyze_sqlite_table(self, cursor, table_name: str) -> Dict:
        """Analisis detail tabel SQLite"""
        table_info = {
            'columns': [],
            'record_count': 0,
            'sample_data': [],
            'date_columns': [],
            'latest_dates': {},
            'indexes': []
        }

        try:
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            table_info['columns'] = columns

            # Get record count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            table_info['record_count'] = cursor.fetchone()[0]

            # Get sample data (5 records)
            if table_info['record_count'] > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                sample_data = cursor.fetchall()
                table_info['sample_data'] = sample_data

            # Find date columns
            date_columns = []
            for col in columns:
                col_name = col[1].lower()
                if any(date_kw in col_name for date_kw in ['date', 'time', 'created', 'modified', 'updated']):
                    date_columns.append(col[1])

            table_info['date_columns'] = date_columns

            # Get latest dates from date columns
            for col_name in date_columns:
                try:
                    cursor.execute(f"SELECT MAX({col_name}) FROM {table_name} WHERE {col_name} IS NOT NULL")
                    max_date = cursor.fetchone()[0]
                    if max_date:
                        table_info['latest_dates'][col_name] = max_date
                except:
                    pass

            # Get indexes
            cursor.execute(f"PRAGMA index_list({table_name})")
            indexes = cursor.fetchall()
            table_info['indexes'] = indexes

        except Exception as e:
            table_info['error'] = str(e)

        return table_info

    def _detect_sqlite_database_type(self, tables: List[str]) -> str:
        """Deteksi tipe database berdasarkan nama tabel"""
        table_names_upper = [t.upper() for t in tables]

        # Check for Plantware
        plantware_tables = ['PR_TASKREG', 'PR_TASK', 'PR_PROJECT', 'PR_USER', 'PR_DEPARTMENT']
        if any(table in table_names_upper for table in plantware_tables):
            return 'plantware'

        # Check for Venus
        venus_tables = ['TA_MACHINE', 'TA_TRANSACTION', 'TA_LOG', 'TA_EMPLOYEE']
        if any(table in table_names_upper for table in venus_tables):
            return 'venus'

        # Check for Staging
        staging_tables = ['GWSCANNER', 'GW_LOG', 'SCANNER_DATA', 'GW_TRANSACTION']
        if any(table in table_names_upper for table in staging_tables):
            return 'staging'

        return 'generic_sqlite'

    def _read_tape_bak(self, bak_path: str) -> Dict:
        """Membaca file .bak format TAPE"""
        result = {
            'success': False,
            'file_type': 'tape',
            'database_info': {},
            'tables': {},
            'extracted_path': bak_path,
            'errors': [],
            'warnings': []
        }

        try:
            # Baca header tape
            with open(bak_path, 'rb') as f:
                header = f.read(64)

            result['database_info']['signature'] = header[:16].hex()
            result['database_info']['file_size'] = os.path.getsize(bak_path)

            if header.startswith(b'TAPE'):
                result['database_info']['format'] = 'TAPE format'
                result['database_info']['readable'] = False
                result['warnings'].append("TAPE format requires special tools to read")
            else:
                result['errors'].append("Unknown tape format")

        except Exception as e:
            result['errors'].append(f"Error reading tape file: {str(e)}")

        return result

    def get_table_data(self, table_name: str, limit: int = 100, offset: int = 0) -> Tuple[List[Dict], Dict]:
        """
        Get data from specific table
        Returns: (data, columns_info)
        """
        if not self.current_connection:
            raise Exception("No active database connection")

        try:
            cursor = self.current_connection.cursor()

            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]

            # Get data
            cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}")
            data = cursor.fetchall()

            # Convert to list of dicts
            result_data = []
            for row in data:
                row_dict = {}
                for i, value in enumerate(row):
                    row_dict[column_names[i]] = value
                result_data.append(row_dict)

            return result_data, columns_info

        except Exception as e:
            raise Exception(f"Error getting table data: {str(e)}")

    def execute_query(self, query: str) -> List[Dict]:
        """Execute custom query"""
        if not self.current_connection:
            raise Exception("No active database connection")

        try:
            cursor = self.current_connection.cursor()
            cursor.execute(query)

            # Get column names
            column_names = [desc[0] for desc in cursor.description]

            # Get data
            data = cursor.fetchall()

            # Convert to list of dicts
            result_data = []
            for row in data:
                row_dict = {}
                for i, value in enumerate(row):
                    row_dict[column_names[i]] = value
                result_data.append(row_dict)

            return result_data

        except Exception as e:
            raise Exception(f"Error executing query: {str(e)}")

    def get_database_summary(self, read_result: Dict) -> str:
        """Generate human-readable summary"""
        summary = []

        summary.append("BAK FILE READER SUMMARY")
        summary.append("=" * 50)

        if read_result.get('extracted_path'):
            summary.append(f"File: {read_result['extracted_path']}")

        summary.append(f"File Type: {read_result['file_type']}")
        summary.append(f"Success: {'YES' if read_result['success'] else 'NO'}")
        summary.append("")

        if read_result.get('zip_info'):
            summary.append("ZIP Information:")
            summary.append(f"  BAK File: {read_result['zip_info'].get('bak_file', 'N/A')}")
            summary.append(f"  Total Files: {read_result['zip_info'].get('total_files', 0)}")
            summary.append(f"  Extracted To: {read_result['zip_info'].get('extracted_to', 'N/A')}")
            summary.append("")

        if read_result.get('database_info'):
            db_info = read_result['database_info']
            summary.append("Database Information:")
            summary.append(f"  Detected Type: {db_info.get('detected_type', 'Unknown')}")
            summary.append(f"  Tables: {db_info.get('table_count', 0)}")

            if 'page_size' in db_info:
                summary.append(f"  Page Size: {db_info['page_size']:,} bytes")
                summary.append(f"  Page Count: {db_info['page_count']:,}")
                summary.append(f"  Total Size: {db_info['total_size']:,} bytes")
            summary.append("")

        if read_result.get('tables'):
            summary.append("Tables:")
            for table_name, table_info in read_result['tables'].items():
                summary.append(f"  {table_name}:")
                summary.append(f"    Records: {table_info.get('record_count', 0):,}")
                summary.append(f"    Columns: {len(table_info.get('columns', []))}")

                if table_info.get('latest_dates'):
                    summary.append("    Latest Dates:")
                    for col, date in table_info['latest_dates'].items():
                        summary.append(f"      {col}: {date}")

                if table_info.get('indexes'):
                    summary.append(f"    Indexes: {len(table_info['indexes'])}")
            summary.append("")

        if read_result.get('errors'):
            summary.append("Errors:")
            for error in read_result['errors']:
                summary.append(f"  * {error}")
            summary.append("")

        if read_result.get('warnings'):
            summary.append("Warnings:")
            for warning in read_result['warnings']:
                summary.append(f"  * {warning}")

        return "\n".join(summary)

# Test function
def test_bak_reader():
    """Test BAK file reader"""
    reader = BAKFileReader()

    # Test dengan file sample
    test_files = [
        'real_test_backups/plantware_backup_2025-10-04.zip',
        'real_test_backups/venus_backup_2025-10-04.zip',
        'real_test_backups/staging_backup_2025-10-04.zip'
    ]

    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n{'='*60}")
            print(f"Testing: {test_file}")
            print('='*60)

            # Read BAK file
            result = reader.read_bak_file(test_file, extract_to_same_folder=False)

            # Print summary
            print(reader.get_database_summary(result))

            # Show tables if successful
            if result['success'] and result['tables']:
                print("\nTable Details:")
                for table_name, table_info in result['tables'].items():
                    if table_info.get('record_count', 0) > 0:
                        print(f"\n{table_name} ({table_info['record_count']:,} records):")
                        print(f"  Columns: {[col[1] for col in table_info['columns'][:5]]}")

                        if table_info.get('sample_data'):
                            print(f"  Sample data (first 3 rows):")
                            for i, row in enumerate(table_info['sample_data'][:3]):
                                print(f"    Row {i+1}: {row}")

        else:
            print(f"File not found: {test_file}")

if __name__ == "__main__":
    test_bak_reader()