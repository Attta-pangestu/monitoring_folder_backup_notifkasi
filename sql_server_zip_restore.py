#!/usr/bin/env python3
"""
SQL Server ZIP Restore and Table Reader
Module untuk extract ZIP, restore BAK ke SQL Server, dan baca tabel tertentu
"""

import os
import sys
import subprocess
import zipfile
import tempfile
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class SQLServerZipRestore:
    """Class untuk handle extract ZIP, restore database, dan baca tabel"""
    
    def __init__(self, server_name: str = "localhost"):
        self.server_name = server_name
        self.temp_dir = None
        self.restored_db_name = None
        self.keep_database = False
        
    def check_sql_server_connection(self) -> bool:
        """Cek koneksi ke SQL Server"""
        try:
            test_query = "SELECT @@VERSION"
            result = subprocess.run(['sqlcmd', '-S', self.server_name, '-U', 'sa', '-P', 'windows0819', '-Q', test_query],
                                  capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        except Exception:
            return False
    
    def extract_zip_file(self, zip_path: str) -> Optional[str]:
        """Extract ZIP file dan return path ke BAK file"""
        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"ZIP file tidak ditemukan: {zip_path}")
        
        try:
            print(f"   [INFO] Membuat direktori temporary...")
            # Use a SQL Server accessible directory instead of temp
            # Create directory in current working directory
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            self.temp_dir = os.path.join(os.getcwd(), f"sql_restore_{unique_id}")
            os.makedirs(self.temp_dir, exist_ok=True)
            print(f"   [OK] Direktori temporary: {self.temp_dir}")
            
            # Extract ZIP
            print(f"   [EXTRACT] Mengekstrak ZIP file...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                print(f"   [INFO] Ditemukan {len(file_list)} file dalam ZIP:")
                for file_name in file_list[:5]:  # Show first 5 files
                    print(f"      • {file_name}")
                if len(file_list) > 5:
                    print(f"      ... dan {len(file_list) - 5} file lainnya")
                
                zip_ref.extractall(self.temp_dir)
            print(f"   [OK] Ekstraksi ZIP selesai!")
            
            # Cari BAK file
            print(f"    Mencari file .bak...")
            bak_files = []
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    if file.lower().endswith('.bak'):
                        bak_path = os.path.join(root, file)
                        bak_size = os.path.getsize(bak_path) / (1024 * 1024)  # MB
                        bak_files.append(bak_path)
                        print(f"   [OK] Ditemukan BAK file: {file} ({bak_size:.1f} MB)")
            
            if not bak_files:
                raise ValueError("Tidak ada file .bak ditemukan dalam ZIP")
            
            # Return BAK file pertama yang ditemukan
            selected_bak = bak_files[0]
            print(f"    Menggunakan BAK file: {os.path.basename(selected_bak)}")
            return selected_bak
            
        except Exception as e:
            self.cleanup_temp_files()
            raise Exception(f"Error extracting ZIP: {str(e)}")
    
    def get_backup_logical_names(self, bak_path: str) -> Tuple[str, str]:
        """Dapatkan logical names dari backup file"""
        try:
            cmd = f'sqlcmd -S {self.server_name} -U sa -P windows0819 -Q "RESTORE FILELISTONLY FROM DISK = \'{bak_path}\'" -h -1'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                raise Exception(f"Cannot read backup file: {result.stderr}")
            
            # Parse output untuk dapatkan logical names
            lines = result.stdout.strip().split('\n')
            data_file = None
            log_file = None
            
            for line in lines:
                if line.strip() and not line.startswith('-'):
                    parts = line.split()
                    if len(parts) >= 3:
                        logical_name = parts[0]
                        file_type = parts[2] if len(parts) > 2 else ""
                        
                        if file_type == 'D' and not data_file:  # Data file
                            data_file = logical_name
                        elif file_type == 'L' and not log_file:  # Log file
                            log_file = logical_name
            
            if not data_file or not log_file:
                # Fallback: ambil 2 logical names pertama
                logical_names = []
                for line in lines:
                    if line.strip() and not line.startswith('-'):
                        parts = line.split()
                        if len(parts) >= 1:
                            logical_names.append(parts[0])
                
                if len(logical_names) >= 2:
                    data_file = logical_names[0]
                    log_file = logical_names[1]
                else:
                    raise Exception("Cannot determine logical file names from backup")
            
            return data_file, log_file
            
        except Exception as e:
            raise Exception(f"Error getting logical names: {str(e)}")

    def get_original_database_name(self, bak_path: str) -> str:
        """Dapatkan nama database asli dari backup file"""
        try:
            # Prioritas 1: Gunakan logical names yang lebih bersih
            data_file, _ = self.get_backup_logical_names(bak_path)
            if data_file:
                # Logical name biasanya mengandung nama database asli
                # Contoh: staging_PTRJ_iFES_Plantware -> staging_PTRJ_iFES_Plantware
                db_name = data_file.replace('_Data', '').replace('_Log', '')
                print(f"   [OK] Nama database dari logical name: {db_name}")
                return self._sanitize_database_name(db_name)
            
            # Prioritas 2: Coba extract dari header (dengan parsing yang lebih hati-hati)
            cmd = f'sqlcmd -S {self.server_name} -U sa -P windows0819 -Q "RESTORE HEADERONLY FROM DISK = \'{bak_path}\'" -h -1'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Parse output dengan lebih hati-hati
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('-') and len(line.strip()) < 200:  # Hindari baris yang terlalu panjang
                        # Coba ambil kata pertama yang masuk akal sebagai database name
                        words = line.split()
                        for word in words:
                            word = word.strip()
                            # Cek apakah ini nama database yang valid
                            if (len(word) > 3 and len(word) < 100 and 
                                not word.lower().startswith('backup') and 
                                not word.lower().startswith('database') and
                                not word.isdigit() and
                                'NULL' not in word.upper()):
                                print(f"   [OK] Nama database dari header: {word}")
                                return self._sanitize_database_name(word)
            
            raise Exception("Cannot determine original database name from backup")
            
        except Exception as e:
            print(f"   [WARN] Error mendapatkan nama database asli: {str(e)}")
            # Fallback ke nama file BAK
            bak_filename = os.path.basename(bak_path)
            db_name = os.path.splitext(bak_filename)[0]  # Remove .bak extension
            print(f"   [OK] Menggunakan nama file sebagai database name: {db_name}")
            return self._sanitize_database_name(db_name)
    
    def _sanitize_database_name(self, db_name: str) -> str:
        """Sanitize dan truncate nama database untuk memenuhi batasan SQL Server"""
        # SQL Server database name max length adalah 128 karakter
        MAX_DB_NAME_LENGTH = 128
        
        # Bersihkan input dari NULL dan karakter aneh
        if not db_name or db_name.strip() == '':
            db_name = 'UnknownDB'
        
        # Remove NULL values dan karakter kontrol
        db_name = db_name.replace('NULL', '').replace('\x00', '').replace('\n', '').replace('\r', '').replace('\t', ' ')
        
        # Remove karakter yang tidak diizinkan dan bersihkan spasi berlebih
        import re
        sanitized = re.sub(r'[^\w_]', '_', db_name.strip())
        sanitized = re.sub(r'_+', '_', sanitized)  # Replace multiple underscores with single
        sanitized = sanitized.strip('_')  # Remove leading/trailing underscores
        
        # Jika kosong setelah sanitasi, gunakan default
        if not sanitized:
            sanitized = 'CleanedDB'
        
        # Jika terlalu panjang, truncate dengan cara yang cerdas
        if len(sanitized) > MAX_DB_NAME_LENGTH:
            # Split by underscore dan ambil bagian penting
            parts = sanitized.split('_')
            
            # Prioritas: nama utama database, tanggal, lalu yang lain
            important_parts = []
            date_parts = []
            
            for part in parts:
                if not part:  # Skip empty parts
                    continue
                elif re.match(r'\d{4}', part):  # Tahun (2025, dll)
                    date_parts.append(part)
                elif re.match(r'\d{2}', part) and len(part) == 2:  # Bulan/tanggal
                    date_parts.append(part)
                elif part.lower() in ['backup', 'restore', 'temp']:
                    continue  # Skip these common suffixes
                else:
                    important_parts.append(part)
            
            # Gabungkan dengan prioritas
            result_parts = important_parts[:3] + date_parts[:2]  # Max 3 nama utama + 2 bagian tanggal
            result_name = '_'.join(result_parts)
            
            # Jika masih terlalu panjang, truncate
            if len(result_name) > MAX_DB_NAME_LENGTH:
                result_name = result_name[:MAX_DB_NAME_LENGTH-5] + '_' + str(abs(hash(sanitized)))[-4:]
            
            print(f"   [WARN] Nama database terlalu panjang ({len(sanitized)} chars)")
            print(f"   [OK] Dipotong menjadi: {result_name} ({len(result_name)} chars)")
            return result_name
        
        return sanitized
    
    def restore_database(self, bak_path: str, target_db_name: str = None) -> str:
        """Restore database dari BAK file"""
        if not target_db_name:
            # Dapatkan nama database asli dari backup file
            target_db_name = self.get_original_database_name(bak_path)
        
        try:
            # Cleanup existing restored databases first
            print(f"    Membersihkan database lama...")
            self.cleanup_old_restored_databases()
            
            print(f"    Menganalisis BAK file untuk mendapatkan logical names...")
            # Dapatkan logical names
            data_file, log_file = self.get_backup_logical_names(bak_path)
            print(f"   [OK] Logical names: Data='{data_file}', Log='{log_file}'")
            
            # Buat direktori untuk database files jika belum ada (using D: drive to avoid space issues)
            print(f"    Menyiapkan direktori database...")
            db_dir = "D:\\SQLData"
            if not os.path.exists(db_dir):
                try:
                    os.makedirs(db_dir)
                    print(f"   [OK] Direktori dibuat: {db_dir}")
                except:
                    # Jika gagal buat di D:\SQLData, gunakan default SQL Server path
                    db_dir = None
                    print(f"   [WARN] Menggunakan default SQL Server path")
            else:
                print(f"   [OK] Menggunakan direktori: {db_dir}")
            
            # Prepare restore command with authentication
            print(f"    Menyiapkan perintah restore untuk database: {target_db_name}")
            if db_dir:
                # Restore dengan specify file locations
                data_path = os.path.join(db_dir, f"{target_db_name}_Data.mdf")
                log_path = os.path.join(db_dir, f"{target_db_name}_Log.ldf")
                print(f"    Data file: {data_path}")
                print(f"    Log file: {log_path}")
                
                restore_cmd = f'''sqlcmd -S {self.server_name} -U sa -P windows0819 -Q "
                RESTORE DATABASE [{target_db_name}]
                FROM DISK = '{bak_path}'
                WITH MOVE '{data_file}' TO '{data_path}',
                MOVE '{log_file}' TO '{log_path}',
                REPLACE"'''
            else:
                # Simple restore tanpa specify path
                restore_cmd = f'sqlcmd -S {self.server_name} -U sa -P windows0819 -Q "RESTORE DATABASE [{target_db_name}] FROM DISK = \'{bak_path}\' WITH REPLACE"'
            
            # Execute restore
            print(f"   [WAIT] Menjalankan perintah restore... (ini mungkin memakan waktu)")
            result = subprocess.run(restore_cmd, shell=True, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.restored_db_name = target_db_name
                print(f"   [OK] Database berhasil di-restore!")
                
                # Grant permissions to sa user for the restored database
                print(f"    Mengatur permission untuk database...")
                permission_cmd = f'''sqlcmd -S {self.server_name} -U sa -P windows0819 -Q "
                USE [{target_db_name}];
                IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'sa')
                BEGIN
                    CREATE USER [sa] FOR LOGIN [sa];
                END
                ALTER ROLE db_owner ADD MEMBER [sa];"'''
                
                perm_result = subprocess.run(permission_cmd, shell=True, capture_output=True, text=True, timeout=30)
                if perm_result.returncode != 0:
                    print(f"   [WARN] Warning: Could not grant permissions to sa user: {perm_result.stderr}")
                else:
                    print(f"   [OK] Permission berhasil diatur!")
                return target_db_name
            else:
                print(f"   [ERROR] Restore gagal, mencoba simple restore...")
                print(f"    Error: {result.stderr}")
                # Jika gagal dengan logical names, coba simple restore
                simple_restore = f'sqlcmd -S {self.server_name} -U sa -P windows0819 -Q "RESTORE DATABASE [{target_db_name}] FROM DISK = \'{bak_path}\' WITH REPLACE"'
                print(f"   [WAIT] Menjalankan simple restore...")
                result = subprocess.run(simple_restore, shell=True, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    self.restored_db_name = target_db_name
                    print(f"   [OK] Simple restore berhasil!")
                    return target_db_name
                else:
                    print(f"   [ERROR] Simple restore juga gagal: {result.stderr}")
                    raise Exception(f"Restore failed: {result.stderr}")
                    
        except Exception as e:
            print(f"   [ERROR] Error saat restore database: {str(e)}")
            raise Exception(f"Error restoring database: {str(e)}")
    
    def get_database_tables(self, db_name: str) -> List[str]:
        """Dapatkan daftar tabel dalam database"""
        import time
        
        try:
            print(f"    Mencari tabel dalam database {db_name}...")
            
            # Wait and retry mechanism for database availability
            max_retries = 5
            retry_delay = 2  # seconds
            
            for attempt in range(max_retries):
                try:
                    # First, verify database exists and is accessible
                    check_db_query = f"SELECT name, state_desc FROM sys.databases WHERE name = '{db_name}'"
                    check_result = subprocess.run(['sqlcmd', '-S', self.server_name, '-U', 'sa', '-P', 'windows0819', '-Q', check_db_query, '-h', '-1'],
                                                capture_output=True, text=True, timeout=30)
                    
                    if check_result.returncode == 0:
                        output_lines = [line.strip() for line in check_result.stdout.split('\n') if line.strip() and not line.startswith('-') and '(' not in line]
                        db_found = False
                        db_state = "UNKNOWN"
                        
                        print(f"    Debug - Output dari database check:")
                        for line in output_lines:
                            print(f"      '{line}'")
                        
                        for line in output_lines:
                            # Cek apakah line mengandung nama database dan state
                            if db_name.lower() in line.lower():
                                db_found = True
                                # Parse state dari output - format: database_name state_desc
                                parts = line.split()
                                # Cari bagian yang bukan nama database sebagai state
                                for part in parts:
                                    if part.lower() != db_name.lower() and part.strip():
                                        db_state = part
                                        break
                                else:
                                    # Jika hanya ada nama database, assume online
                                    db_state = "ONLINE"
                                print(f"   [OK] Database {db_name} ditemukan dengan state: {db_state}")
                                break
                        
                        if db_found and db_state.upper() == "ONLINE":
                            print(f"   [OK] Database {db_name} siap digunakan!")
                            break
                        elif db_found:
                            print(f"   [WARN] Database {db_name} ditemukan tapi dalam state: {db_state}")
                            if attempt < max_retries - 1:
                                print(f"   [WAIT] Menunggu database menjadi online... {retry_delay} detik (percobaan {attempt + 1}/{max_retries})")
                                time.sleep(retry_delay)
                                continue
                        else:
                            print(f"   [WARN] Database {db_name} belum ditemukan dalam output")
                            if attempt < max_retries - 1:
                                print(f"   [WAIT] Menunggu database tersedia... {retry_delay} detik (percobaan {attempt + 1}/{max_retries})")
                                time.sleep(retry_delay)
                                continue
                    else:
                        print(f"   [ERROR] Error saat check database: {check_result.stderr}")
                        if attempt < max_retries - 1:
                            print(f"   [WAIT] Mencoba lagi dalam {retry_delay} detik... (percobaan {attempt + 1}/{max_retries})")
                            time.sleep(retry_delay)
                            continue
                    
                    if attempt == max_retries - 1:
                        print(f"   [ERROR] Database {db_name} tidak tersedia setelah {max_retries} percobaan!")
                        print(f"    Output terakhir: {check_result.stdout}")
                        print(f"   [ERROR] Error: {check_result.stderr}")
                        
                        # Coba list semua database untuk debugging
                        print(f"    Mencoba list semua database untuk debugging...")
                        list_db_query = "SELECT name FROM sys.databases"
                        list_result = subprocess.run(['sqlcmd', '-S', self.server_name, '-U', 'sa', '-P', 'windows0819', '-Q', list_db_query, '-W'],
                                                   capture_output=True, text=True, timeout=30)
                        if list_result.returncode == 0:
                            print(f"    Database yang tersedia:")
                            db_lines = [line.strip() for line in list_result.stdout.split('\n') if line.strip() and not line.startswith('-') and '(' not in line]
                            for line in db_lines:
                                print(f"      - {line}")
                                # Check if our database is in the list with a different case or format
                                if db_name.lower() in line.lower():
                                    print(f"    Found matching database: {line}")
                        
                        raise Exception(f"Database {db_name} does not exist or is not online")
                            
                except subprocess.TimeoutExpired:
                    if attempt < max_retries - 1:
                        print(f"   [WAIT] Timeout, mencoba lagi dalam {retry_delay} detik... (percobaan {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise Exception(f"Database check timeout after {max_retries} attempts")
            
            # Now get the tables
            print(f"    Mengambil daftar tabel...")
            query = f"USE [{db_name}]; SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME"
            result = subprocess.run(['sqlcmd', '-S', self.server_name, '-U', 'sa', '-P', 'windows0819', '-Q', query, '-h', '-1'],
                                  capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                tables = []
                # Process output with -h -1 flag (no headers, clean output)
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and 'rows affected' not in line and '---' not in line and 'Changed database context' not in line:
                        tables.append(line)
                print(f"   [OK] Ditemukan {len(tables)} tabel: {', '.join(tables[:5])}{' ...' if len(tables) > 5 else ''}")
                return tables
            else:
                print(f"   [ERROR] Error mendapatkan daftar tabel: {result.stderr}")
                raise Exception(f"Error getting tables: {result.stderr}")
                
        except Exception as e:
            print(f"   [ERROR] Error saat mengambil daftar tabel: {str(e)}")
            raise Exception(f"Error getting database tables: {str(e)}")
    
    def get_table_info(self, db_name: str, table_name: str) -> Dict:
        """Dapatkan informasi detail tentang tabel"""
        try:
            print(f"      Menganalisis tabel: {table_name}")
            info = {
                'table_name': table_name,
                'columns': [],
                'row_count': 0,
                'sample_data': [],
                'date_columns': [],
                'latest_dates': {}
            }
            
            # Get columns
            print(f"      Mengambil informasi kolom...")
            col_query = f"USE [{db_name}]; SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}' ORDER BY ORDINAL_POSITION"
            result = subprocess.run(['sqlcmd', '-S', self.server_name, '-U', 'sa', '-P', 'windows0819', '-Q', col_query, '-h', '-1', '-s', '|'],
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if '|' in line and line.strip():
                        parts = [p.strip() for p in line.split('|')]
                        if len(parts) >= 3:
                            info['columns'].append({
                                'name': parts[0],
                                'type': parts[1],
                                'nullable': parts[2]
                            })
                print(f"     [OK] Ditemukan {len(info['columns'])} kolom")
            
            # Get row count
            print(f"      Menghitung jumlah baris...")
            count_query = f"USE [{db_name}]; SELECT COUNT(*) FROM dbo.[{table_name}]"
            result = subprocess.run(['sqlcmd', '-S', self.server_name, '-U', 'sa', '-P', 'windows0819', '-Q', count_query, '-h', '-1'],
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.strip().isdigit():
                        info['row_count'] = int(line.strip())
                        break
                print(f"     [OK] Jumlah baris: {info['row_count']:,}")
            
            # Get sample data (first 5 rows)
            print(f"      Mengambil sample data...")
            sample_query = f"USE [{db_name}]; SELECT TOP 5 * FROM dbo.[{table_name}]"
            result = subprocess.run(['sqlcmd', '-S', self.server_name, '-U', 'sa', '-P', 'windows0819', '-Q', sample_query, '-h', '-1', '-s', '|', '-W'],
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                sample_lines = []
                for line in result.stdout.split('\n'):
                    if line.strip() and not line.startswith('-'):
                        sample_lines.append(line.strip())
                info['sample_data'] = sample_lines[:5]
                print(f"     [OK] Sample data diambil ({len(info['sample_data'])} baris)")
            
            # Find date columns
            print(f"      Mencari kolom tanggal...")
            date_query = f"USE [{db_name}]; SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}' AND DATA_TYPE IN ('datetime', 'date', 'datetime2', 'smalldatetime')"
            result = subprocess.run(['sqlcmd', '-S', self.server_name, '-U', 'sa', '-P', 'windows0819', '-Q', date_query, '-h', '-1'],
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    col_name = line.strip()
                    if col_name and not col_name.startswith('-'):
                        info['date_columns'].append(col_name)
                        
                        # Get latest date for this column
                        latest_query = f"USE [{db_name}]; SELECT TOP 1 [{col_name}] FROM dbo.[{table_name}] WHERE [{col_name}] IS NOT NULL ORDER BY [{col_name}] DESC"
                        date_result = subprocess.run(['sqlcmd', '-S', self.server_name, '-U', 'sa', '-P', 'windows0819', '-Q', latest_query, '-h', '-1'],
                                                   capture_output=True, text=True, timeout=30)
                        
                        if date_result.returncode == 0:
                            for date_line in date_result.stdout.split('\n'):
                                if date_line.strip() and not date_line.startswith('-'):
                                    info['latest_dates'][col_name] = date_line.strip()
                                    break
            
            return info
            
        except Exception as e:
            raise Exception(f"Error getting table info: {str(e)}")
    
    def find_specific_tables(self, db_name: str, table_patterns: List[str]) -> List[str]:
        """Cari tabel berdasarkan pattern tertentu (misal: GWSCANNER, dll)"""
        try:
            all_tables = self.get_database_tables(db_name)
            matching_tables = []
            
            for table in all_tables:
                for pattern in table_patterns:
                    if pattern.upper() in table.upper():
                        matching_tables.append(table)
                        break
            
            return matching_tables
            
        except Exception as e:
            raise Exception(f"Error finding specific tables: {str(e)}")
    
    def cleanup_temp_files(self):
        """Bersihkan temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
            except Exception:
                pass
    
    def cleanup_old_restored_databases(self):
        """Hapus database lama yang sudah di-restore sebelumnya"""
        try:
            print("    Membersihkan database lama...")
            
            # Dapatkan daftar database yang perlu dihapus
            # Sekarang kita akan hapus semua database kecuali system databases
            system_databases = ['master', 'model', 'msdb', 'tempdb']
            
            cmd = f'sqlcmd -S {self.server_name} -U sa -P windows0819 -Q "SELECT name FROM sys.databases WHERE name NOT IN (\'master\', \'model\', \'msdb\', \'tempdb\')" -h -1'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                databases_to_drop = []
                
                for line in lines:
                    db_name = line.strip()
                    if db_name and db_name not in system_databases and not db_name.startswith('-'):
                        databases_to_drop.append(db_name)
                
                # Drop setiap database
                for db_name in databases_to_drop:
                    try:
                        print(f"    Menghapus database: {db_name}")
                        
                        # Set database ke single user mode dulu
                        single_user_cmd = f'sqlcmd -S {self.server_name} -U sa -P windows0819 -Q "ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE" -t 30'
                        subprocess.run(single_user_cmd, shell=True, capture_output=True, text=True, timeout=60)
                        
                        # Drop database
                        drop_cmd = f'sqlcmd -S {self.server_name} -U sa -P windows0819 -Q "DROP DATABASE [{db_name}]" -t 30'
                        drop_result = subprocess.run(drop_cmd, shell=True, capture_output=True, text=True, timeout=60)
                        
                        if drop_result.returncode == 0:
                            print(f"   [OK] Database {db_name} berhasil dihapus")
                        else:
                            print(f"   [WARN] Gagal menghapus database {db_name}: {drop_result.stderr}")
                            
                    except Exception as e:
                        print(f"   [WARN] Error menghapus database {db_name}: {str(e)}")
                        continue
                
                if not databases_to_drop:
                    print("   [OK] Tidak ada database lama yang perlu dihapus")
            else:
                print(f"   [WARN] Gagal mendapatkan daftar database: {result.stderr}")
                
        except Exception as e:
            print(f"   [WARN] Error saat cleanup database: {str(e)}")

    def drop_restored_database(self, db_name: str = None):
        """Drop database yang sudah di-restore (untuk cleanup)"""
        if not db_name:
            db_name = self.restored_db_name
        
        if db_name:
            try:
                # Set database to single user mode first
                single_user_cmd = f'sqlcmd -S {self.server_name} -U sa -P windows0819 -Q "ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE"'
                subprocess.run(single_user_cmd, shell=True, capture_output=True, text=True, timeout=30)
                
                # Drop database
                drop_cmd = f'sqlcmd -S {self.server_name} -U sa -P windows0819 -Q "DROP DATABASE [{db_name}]"'
                result = subprocess.run(drop_cmd, shell=True, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    if db_name == self.restored_db_name:
                        self.restored_db_name = None
                    return True
                        
            except Exception:
                pass
        
        return False
    
    def __del__(self):
        """Cleanup saat object dihapus"""
        self.cleanup_temp_files()
        # Only drop database if keep_database is False
        if self.restored_db_name and not self.keep_database:
            self.drop_restored_database()


def extract_restore_and_analyze(zip_path: str, table_patterns: List[str] = None, keep_database: bool = False, progress_callback=None) -> Dict:
    """
    Function utama untuk extract ZIP, restore database, dan analisis tabel
    
    Args:
        zip_path: Path ke file ZIP yang berisi BAK file
        table_patterns: List pattern nama tabel yang dicari (default: ['GWSCANNER'])
        keep_database: Jika True, database tidak akan dihapus setelah analisis
        progress_callback: Function untuk callback progress updates
    
    Returns:
        Dict berisi hasil analisis
    """
    if not table_patterns:
        table_patterns = ['GWSCANNER']
    
    print("\n" + "="*60)
    print("[PROSES] MEMULAI PROSES EXTRACT, RESTORE & ANALYZE")
    print("="*60)
    print(f"[INFO] ZIP File: {os.path.basename(zip_path)}")
    print(f"[INFO] Mencari tabel: {', '.join(table_patterns)}")
    print(f"[INFO] Keep database: {'Ya' if keep_database else 'Tidak'}")
    
    restorer = SQLServerZipRestore()
    restorer.keep_database = keep_database  # Set the flag to prevent automatic deletion
    result = {
        'success': False,
        'error': None,
        'zip_path': zip_path,
        'bak_file': None,
        'database_name': None,
        'tables_found': [],
        'table_details': {},
        'cleanup_performed': False
    }
    
    try:
        # Check SQL Server connection
        if progress_callback:
            progress_callback("Checking SQL Server connection...")
        print("\n[CONN] Mengecek koneksi SQL Server...")
        if not restorer.check_sql_server_connection():
            raise Exception("Cannot connect to SQL Server")
        if progress_callback:
            progress_callback("SQL Server connection successful")
        print("[OK] Koneksi SQL Server berhasil!")

        # Extract ZIP
        if progress_callback:
            progress_callback(f"Extracting ZIP file: {os.path.basename(zip_path)}")
        print(f"\n[EXTRACT] Mengekstrak file ZIP: {os.path.basename(zip_path)}")
        print("   [WAIT] Proses ekstraksi dimulai...")
        bak_path = restorer.extract_zip_file(zip_path)
        result['bak_file'] = os.path.basename(bak_path)
        if progress_callback:
            progress_callback(f"ZIP extraction completed: {os.path.basename(bak_path)}")
        print(f"[OK] Ekstraksi selesai! BAK file: {os.path.basename(bak_path)}")

        # Restore database
        if progress_callback:
            progress_callback(f"Restoring database from: {os.path.basename(bak_path)}")
        print(f"\n[DB] Melakukan restore database dari: {os.path.basename(bak_path)}")
        print("   [WAIT] Proses restore dimulai...")
        db_name = restorer.restore_database(bak_path)
        result['database_name'] = db_name
        if progress_callback:
            progress_callback(f"Database restored successfully: {db_name}")
        print(f"[OK] Restore selesai! Database: {db_name}")

        # Find specific tables
        if progress_callback:
            progress_callback(f"Searching for tables with pattern: {', '.join(table_patterns)}")
        print(f"\n[SEARCH] Mencari tabel dengan pattern: {', '.join(table_patterns)}")
        matching_tables = restorer.find_specific_tables(db_name, table_patterns)
        result['tables_found'] = matching_tables
        if progress_callback:
            progress_callback(f"Found {len(matching_tables)} matching tables")
        print(f"[OK] Ditemukan {len(matching_tables)} tabel yang cocok:")
        for table in matching_tables:
            print(f"   • {table}")

        # Get detailed info for each matching table
        if matching_tables:
            if progress_callback:
                progress_callback("Analyzing table details...")
            print(f"\n[ANALYZE] Menganalisis detail tabel...")
            for i, table in enumerate(matching_tables, 1):
                if progress_callback:
                    progress_callback(f"Analyzing table {i}/{len(matching_tables)}: {table}")
                print(f"   [WAIT] Menganalisis tabel {i}/{len(matching_tables)}: {table}")
                table_info = restorer.get_table_info(db_name, table)
                result['table_details'][table] = table_info
                if progress_callback:
                    progress_callback(f"Completed analysis of {table}: {table_info.get('row_count', 0)} records")
                print(f"   [OK] Selesai - {table_info.get('row_count', 0)} records")

        result['success'] = True
        if progress_callback:
            progress_callback("Extract, restore & analysis completed successfully")
        print(f"\n[SUCCESS] PROSES SELESAI DENGAN SUKSES!")
        
    except Exception as e:
        result['error'] = str(e)
        print(f"\n[ERROR] ERROR: {str(e)}")
    
    finally:
        # Cleanup
        print(f"\n[CLEAN] Membersihkan file temporary...")
        restorer.cleanup_temp_files()
        if restorer.restored_db_name and not keep_database:
            print(f"[DELETE] Menghapus database test: {restorer.restored_db_name}")
            restorer.drop_restored_database()
            print("[OK] Cleanup selesai!")
            result['cleanup_performed'] = True
        elif restorer.restored_db_name and keep_database:
            print("[OK] Database disimpan untuk analisis lebih lanjut!")
            result['cleanup_performed'] = False
            result['database_kept'] = True
        else:
            print("[OK] Cleanup selesai!")
            result['cleanup_performed'] = True
    
    return result


if __name__ == "__main__":
    # Test function
    if len(sys.argv) > 1:
        zip_path = sys.argv[1]
        result = extract_restore_and_analyze(zip_path)
        
        print("=" * 80)
        print("SQL SERVER ZIP RESTORE ANALYSIS")
        print("=" * 80)
        print(f"ZIP File: {result['zip_path']}")
        print(f"Success: {result['success']}")
        
        if result['success']:
            print(f"BAK File: {result['bak_file']}")
            print(f"Database: {result['database_name']}")
            print(f"Tables Found: {len(result['tables_found'])}")
            
            for table_name, info in result['table_details'].items():
                print(f"\nTable: {table_name}")
                print(f"  Rows: {info['row_count']:,}")
                print(f"  Columns: {len(info['columns'])}")
                if info['latest_dates']:
                    print("  Latest Dates:")
                    for col, date in info['latest_dates'].items():
                        print(f"    {col}: {date}")
        else:
            print(f"Error: {result['error']}")
    else:
        print("Usage: python sql_server_zip_restore.py <zip_file_path>")