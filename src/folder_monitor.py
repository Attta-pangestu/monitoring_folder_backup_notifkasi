import os
import zipfile
import tempfile
import shutil
import re
from datetime import datetime, timedelta
import sqlite3
from typing import List, Dict, Tuple

class FolderMonitor:
    def __init__(self):
        self.monitoring_path = ""
        self.temp_dir = None

    def set_monitoring_path(self, path: str):
        """Set path folder yang akan dimonitoring"""
        self.monitoring_path = path

    def get_latest_zip_files_by_date(self) -> Tuple[List[str], str]:
        """
        Mendapatkan file zip terbaru berdasarkan tanggal
        Returns: (list_of_zip_files, latest_date)
        """
        if not self.monitoring_path or not os.path.exists(self.monitoring_path):
            return [], ""

        # Pattern untuk mencari tanggal dalam format yang umum
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{2}-\d{2}-\d{4})',  # DD-MM-YYYY
            r'(\d{4}_\d{2}_\d{2})',  # YYYY_MM_DD
            r'(\d{2}_\d{2}_\d{4})',  # DD_MM_YYYY
            r'(\d{8})',              # YYYYMMDD
            r'(\d{6})',              # YYMMDD
        ]

        zip_files = []
        date_groups = {}
        invalid_zips = []

        # Scan semua file zip
        for file in os.listdir(self.monitoring_path):
            if file.lower().endswith('.zip'):
                file_path = os.path.join(self.monitoring_path, file)

                # Validasi ZIP file
                if not self._validate_zip_file(file_path):
                    invalid_zips.append(file)
                    continue

                zip_files.append(file_path)

                # Ekstrak tanggal dari filename
                file_date = None
                for pattern in date_patterns:
                    match = re.search(pattern, file)
                    if match:
                        date_str = match.group(1)
                        # Konversi ke format YYYY-MM-DD
                        file_date = self._normalize_date(date_str)
                        break

                if not file_date:
                    # Jika tidak ada tanggal di filename, gunakan modification time
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    file_date = mod_time.strftime('%Y-%m-%d')

                if file_date not in date_groups:
                    date_groups[file_date] = []
                date_groups[file_date].append(file_path)

        # Log invalid ZIP files
        if invalid_zips:
            print(f"Warning: {len(invalid_zips)} invalid ZIP files found: {invalid_zips}")

        if not date_groups:
            return [], ""

        # Sort tanggal dan ambil yang terbaru
        sorted_dates = sorted(date_groups.keys(), reverse=True)
        latest_date = sorted_dates[0]

        return date_groups[latest_date], latest_date

    def _normalize_date(self, date_str: str) -> str:
        """Normalisasi format tanggal ke YYYY-MM-DD"""
        # Ganti underscore dengan dash
        date_str = date_str.replace('_', '-')

        # Coba parsing berbagai format
        formats = [
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%Y%m%d',
            '%y%m%d',
            '%m-%d-%Y',
            '%Y-%m-%d'
        ]

        for fmt in formats:
            try:
                if len(date_str.replace('-', '')) == 8:  # YYYYMMDD
                    dt = datetime.strptime(date_str, '%Y%m%d')
                elif len(date_str.replace('-', '')) == 6:  # YYMMDD
                    dt = datetime.strptime(date_str, '%y%m%d')
                else:
                    dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue

        # Jika gagal parsing, return tanggal hari ini
        return datetime.now().strftime('%Y-%m-%d')

    def _validate_zip_file(self, zip_path: str) -> bool:
        """Validasi integrity file ZIP"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Test ZIP integrity
                zip_ref.testzip()
                # Check if ZIP is not empty
                if len(zip_ref.namelist()) == 0:
                    return False
                return True
        except Exception as e:
            print(f"Invalid ZIP file {zip_path}: {str(e)}")
            return False

    def extract_zip_files(self, zip_files: List[str], extract_to: str = None) -> Dict[str, List[str]]:
        """
        Ekstrak multiple file zip ke directory
        Returns: Dictionary dengan filename sebagai key dan list extracted files sebagai value
        """
        if not extract_to:
            self.temp_dir = tempfile.mkdtemp(prefix="backup_monitor_")
            extract_to = self.temp_dir

        extracted_data = {}

        for zip_file in zip_files:
            try:
                zip_name = os.path.basename(zip_file)
                extract_path = os.path.join(extract_to, zip_name.replace('.zip', ''))
                os.makedirs(extract_path, exist_ok=True)

                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)

                # Dapatkan list file yang diekstrak
                extracted_files = []
                for root, dirs, files in os.walk(extract_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        extracted_files.append(file_path)

                extracted_data[zip_name] = extracted_files

            except Exception as e:
                print(f"Error extracting {zip_file}: {str(e)}")

        return extracted_data

    def find_bak_files(self, extracted_data: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Cari file .bak dari hasil ekstrak"""
        bak_files = {}

        for zip_name, files in extracted_data.items():
            bak_files_for_zip = []
            for file_path in files:
                if file_path.lower().endswith('.bak'):
                    bak_files_for_zip.append(file_path)
            bak_files[zip_name] = bak_files_for_zip

        return bak_files

    def analyze_bak_files(self, bak_files: Dict[str, List[str]]) -> Dict[str, Dict]:
        """Analisis file .bak dan query data"""
        results = {}

        for zip_name, files in bak_files.items():
            zip_results = {
                'status': 'Success',
                'tables': {},
                'errors': []
            }

            for bak_file in files:
                try:
                    bak_result = self._analyze_single_bak(bak_file)
                    zip_results['tables'].update(bak_result['tables'])
                    zip_results['errors'].extend(bak_result['errors'])

                except Exception as e:
                    zip_results['errors'].append(f"Error analyzing {os.path.basename(bak_file)}: {str(e)}")
                    zip_results['status'] = 'Error'

            if zip_results['errors']:
                zip_results['status'] = 'Warning'

            results[zip_name] = zip_results

        return results

    def _analyze_single_bak(self, bak_file_path: str) -> Dict:
        """Analisis single file .bak dengan query khusus per database"""
        result = {
            'tables': {},
            'errors': [],
            'database_type': self._detect_database_type(bak_file_path)
        }

        try:
            # Koneksi ke database SQLite
            conn = sqlite3.connect(bak_file_path)
            cursor = conn.cursor()

            # Get table list
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [table[0] for table in cursor.fetchall()]

            # Query berdasarkan database type
            if result['database_type'] == 'Plantware':
                result.update(self._query_plantware(cursor, tables))
            elif result['database_type'] == 'Venus':
                result.update(self._query_venus(cursor, tables))
            elif result['database_type'] == 'Staging':
                result.update(self._query_staging(cursor, tables))
            else:
                # Default query untuk database tidak dikenal
                result.update(self._query_default(cursor, tables))

            conn.close()

        except Exception as e:
            result['errors'].append(f"Database connection error: {str(e)}")

        return result

    def _detect_database_type(self, bak_file_path: str) -> str:
        """Deteksi tipe database berdasarkan filename atau tabel yang ada"""
        filename = os.path.basename(bak_file_path).lower()

        if 'plantware' in filename:
            return 'Plantware'
        elif 'venus' in filename:
            return 'Venus'
        elif 'staging' in filename:
            return 'Staging'
        else:
            # Deteksi berdasarkan tabel yang ada
            try:
                conn = sqlite3.connect(bak_file_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [table[0].upper() for table in cursor.fetchall()]

                if 'PR_TASKREG' in tables:
                    return 'Plantware'
                elif 'TA_MACHINE' in tables:
                    return 'Venus'
                elif 'GWSCANNER' in tables:
                    return 'Staging'

                conn.close()
            except:
                pass

            return 'Unknown'

    def _query_plantware(self, cursor, tables: List[str]) -> Dict:
        """Query khusus untuk database Plantware"""
        result = {'tables': {}, 'errors': []}

        # Query tabel PR_TASKREG
        if 'PR_TASKREG' in [t.upper() for t in tables]:
            try:
                # Get total records
                cursor.execute("SELECT COUNT(*) FROM PR_TASKREG")
                total_count = cursor.fetchone()[0]

                # Get latest record date - coba beberapa kolom tanggal
                date_columns = ['TASK_DATE', 'CREATED_DATE', 'MODIFIED_DATE', 'START_DATE', 'END_DATE']
                latest_date = None

                for col in date_columns:
                    try:
                        cursor.execute(f"SELECT MAX({col}) FROM PR_TASKREG")
                        result_max = cursor.fetchone()
                        if result_max and result_max[0]:
                            latest_date = result_max[0]
                            break
                    except:
                        continue

                if latest_date:
                    result['tables']['PR_TASKREG'] = f"{total_count} records (latest: {latest_date})"
                else:
                    result['tables']['PR_TASKREG'] = f"{total_count} records"

            except Exception as e:
                result['tables']['PR_TASKREG'] = f"Error: {str(e)}"
                result['errors'].append(f"Error querying PR_TASKREG: {str(e)}")

        return result

    def _query_venus(self, cursor, tables: List[str]) -> Dict:
        """Query khusus untuk database Venus"""
        result = {'tables': {}, 'errors': []}

        # Query tabel TA_MACHINE
        if 'TA_MACHINE' in [t.upper() for t in tables]:
            try:
                # Get total records
                cursor.execute("SELECT COUNT(*) FROM TA_MACHINE")
                total_count = cursor.fetchone()[0]

                # Get latest record date
                date_columns = ['MACHINE_DATE', 'CREATED_DATE', 'MODIFIED_DATE', 'LAST_UPDATE', 'TIMESTAMP']
                latest_date = None

                for col in date_columns:
                    try:
                        cursor.execute(f"SELECT MAX({col}) FROM TA_MACHINE")
                        result_max = cursor.fetchone()
                        if result_max and result_max[0]:
                            latest_date = result_max[0]
                            break
                    except:
                        continue

                if latest_date:
                    result['tables']['TA_MACHINE'] = f"{total_count} records (latest: {latest_date})"
                else:
                    result['tables']['TA_MACHINE'] = f"{total_count} records"

            except Exception as e:
                result['tables']['TA_MACHINE'] = f"Error: {str(e)}"
                result['errors'].append(f"Error querying TA_MACHINE: {str(e)}")

        return result

    def _query_staging(self, cursor, tables: List[str]) -> Dict:
        """Query khusus untuk database Staging"""
        result = {'tables': {}, 'errors': []}

        # Query tabel GWSCANNER
        if 'GWSCANNER' in [t.upper() for t in tables]:
            try:
                # Get total records
                cursor.execute("SELECT COUNT(*) FROM GWSCANNER")
                total_count = cursor.fetchone()[0]

                # Get latest record date
                date_columns = ['SCAN_DATE', 'CREATED_DATE', 'MODIFIED_DATE', 'TIMESTAMP', 'LOG_DATE']
                latest_date = None

                for col in date_columns:
                    try:
                        cursor.execute(f"SELECT MAX({col}) FROM GWSCANNER")
                        result_max = cursor.fetchone()
                        if result_max and result_max[0]:
                            latest_date = result_max[0]
                            break
                    except:
                        continue

                if latest_date:
                    result['tables']['GWSCANNER'] = f"{total_count} records (latest: {latest_date})"
                else:
                    result['tables']['GWSCANNER'] = f"{total_count} records"

            except Exception as e:
                result['tables']['GWSCANNER'] = f"Error: {str(e)}"
                result['errors'].append(f"Error querying GWSCANNER: {str(e)}")

        return result

    def _query_default(self, cursor, tables: List[str]) -> Dict:
        """Query default untuk database tidak dikenal"""
        result = {'tables': {}, 'errors': []}

        # Default tables to query
        default_tables = ['Users', 'Transactions', 'Logs', 'Audit', 'Products', 'Orders', 'Customers']

        for table in default_tables:
            if table in tables:
                try:
                    # Coba query count
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]

                    # Coba query tanggal terakhir
                    date_columns = ['created_at', 'timestamp', 'date', 'updated_at', 'log_date', 'created_time']
                    last_date = None

                    for col in date_columns:
                        try:
                            cursor.execute(f"SELECT MAX({col}) FROM {table}")
                            result_max = cursor.fetchone()
                            if result_max and result_max[0]:
                                last_date = result_max[0]
                                break
                        except:
                            continue

                    if last_date:
                        result['tables'][table] = f"{count} records (last: {last_date})"
                    else:
                        result['tables'][table] = f"{count} records"

                except Exception as e:
                    result['tables'][table] = f"Error: {str(e)}"
                    result['errors'].append(f"Error querying {table}: {str(e)}")

        return result

    def cleanup_temp_files(self):
        """Bersihkan temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None

    def get_monitoring_summary(self) -> Dict:
        """Get complete monitoring summary"""
        summary = {
            'monitoring_path': self.monitoring_path,
            'latest_date': '',
            'zip_files': [],
            'extracted_data': {},
            'bak_files': {},
            'analysis_results': {},
            'status': 'Ready',
            'errors': []
        }

        try:
            # Get latest zip files
            zip_files, latest_date = self.get_latest_zip_files_by_date()
            summary['latest_date'] = latest_date
            summary['zip_files'] = [os.path.basename(f) for f in zip_files]

            if not zip_files:
                summary['status'] = 'No files found'
                summary['errors'].append('No zip files found in monitoring directory')
                return summary

            # Extract files
            extracted_data = self.extract_zip_files(zip_files)
            summary['extracted_data'] = {k: len(v) for k, v in extracted_data.items()}

            # Find .bak files
            bak_files = self.find_bak_files(extracted_data)
            summary['bak_files'] = {k: len(v) for k, v in bak_files.items()}

            # Analyze .bak files
            analysis_results = self.analyze_bak_files(bak_files)
            summary['analysis_results'] = analysis_results

            # Check overall status
            has_errors = any('errors' in result and result['errors'] for result in analysis_results.values())
            if has_errors:
                summary['status'] = 'Warning'

        except Exception as e:
            summary['status'] = 'Error'
            summary['errors'].append(str(e))

        return summary

    def __del__(self):
        """Cleanup saat object di-destroy"""
        self.cleanup_temp_files()