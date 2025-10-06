#!/usr/bin/env python3
"""
ZIP Metadata Viewer Module
Modul untuk menampilkan metadata file ZIP secara sederhana dan bertahap
"""

import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import time

class ZipMetadataViewer:
    def __init__(self):
        self.latest_zips = []
    
    def check_zip_integrity(self, zip_path: str) -> Dict:
        """
        Memeriksa integritas file ZIP
        
        Args:
            zip_path: Path ke file ZIP
            
        Returns:
            Dictionary dengan hasil pemeriksaan integritas
        """
        result = {
            'is_valid': False,
            'total_files': 0,
            'corrupted_files': [],
            'error': None,
            'file_path': zip_path,
            'file_size': 0,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            # Cek apakah file ada
            if not os.path.exists(zip_path):
                result['error'] = f"File tidak ditemukan: {zip_path}"
                return result
            
            # Dapatkan ukuran file
            result['file_size'] = os.path.getsize(zip_path)
            
            # Test buka ZIP file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Test integrity dengan testzip()
                bad_file = zip_ref.testzip()
                
                if bad_file is not None:
                    result['corrupted_files'].append(bad_file)
                    result['error'] = f"File rusak ditemukan: {bad_file}"
                else:
                    result['is_valid'] = True
                
                # Hitung total file
                result['total_files'] = len(zip_ref.namelist())
                
                # Coba baca info setiap file
                for file_info in zip_ref.infolist():
                    try:
                        # Test baca header file
                        zip_ref.getinfo(file_info.filename)
                    except Exception as e:
                        result['corrupted_files'].append(file_info.filename)
                        if result['error'] is None:
                            result['error'] = f"Error membaca file: {file_info.filename}"
                
                # Update status berdasarkan file rusak
                if result['corrupted_files']:
                    result['is_valid'] = False
                    
        except zipfile.BadZipFile:
            result['error'] = "File ZIP rusak atau tidak valid"
        except Exception as e:
            result['error'] = f"Error: {str(e)}"
        
        return result
    
    def extract_zip_metadata(self, zip_path: str) -> Dict:
        """
        Mengekstrak metadata lengkap dari file ZIP
        
        Args:
            zip_path: Path ke file ZIP
            
        Returns:
            Dictionary dengan metadata ZIP
        """
        result = {
            'success': False,
            'file_path': zip_path,
            'file_name': os.path.basename(zip_path),
            'file_size': 0,
            'file_size_mb': 0,
            'created_time': None,
            'modified_time': None,
            'total_files': 0,
            'total_compressed_size': 0,
            'total_uncompressed_size': 0,
            'compression_ratio': 0,
            'files': [],
            'bak_files': [],
            'directories': [],
            'file_types': {},
            'error': None,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            # Informasi file sistem
            if os.path.exists(zip_path):
                stat = os.stat(zip_path)
                result['file_size'] = stat.st_size
                result['file_size_mb'] = round(stat.st_size / (1024 * 1024), 2)
                result['created_time'] = datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                result['modified_time'] = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            # Analisis isi ZIP
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                files_info = []
                bak_files = []
                directories = set()
                file_types = {}
                total_compressed = 0
                total_uncompressed = 0
                
                for file_info in zip_ref.infolist():
                    # Informasi file
                    file_detail = {
                        'filename': file_info.filename,
                        'size_bytes': file_info.file_size,
                        'size_mb': round(file_info.file_size / (1024 * 1024), 2),
                        'compressed_size': file_info.compress_size,
                        'compression_ratio': round((1 - file_info.compress_size / file_info.file_size) * 100, 2) if file_info.file_size > 0 else 0,
                        'date_time': datetime(*file_info.date_time).strftime('%Y-%m-%d %H:%M:%S') if file_info.date_time else 'Unknown',
                        'is_directory': file_info.filename.endswith('/'),
                        'file_extension': os.path.splitext(file_info.filename)[1].lower()
                    }
                    
                    files_info.append(file_detail)
                    
                    # Akumulasi ukuran
                    total_compressed += file_info.compress_size
                    total_uncompressed += file_info.file_size
                    
                    # Cek apakah file BAK
                    if file_info.filename.lower().endswith('.bak'):
                        bak_files.append(file_detail)
                    
                    # Direktori
                    if file_info.filename.endswith('/'):
                        directories.add(file_info.filename)
                    else:
                        # Tambahkan direktori parent
                        parent_dir = os.path.dirname(file_info.filename)
                        if parent_dir:
                            directories.add(parent_dir + '/')
                    
                    # Tipe file
                    ext = file_detail['file_extension']
                    if ext:
                        file_types[ext] = file_types.get(ext, 0) + 1
                
                # Update hasil
                result['success'] = True
                result['total_files'] = len(files_info)
                result['total_compressed_size'] = total_compressed
                result['total_uncompressed_size'] = total_uncompressed
                result['compression_ratio'] = round((1 - total_compressed / total_uncompressed) * 100, 2) if total_uncompressed > 0 else 0
                result['files'] = files_info
                result['bak_files'] = bak_files
                result['directories'] = sorted(list(directories))
                result['file_types'] = file_types
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def find_latest_zip_files(self, folder_path: str, days: int = 7) -> List[Dict]:
        """
        Mencari file ZIP terbaru dalam folder
        
        Args:
            folder_path: Path ke folder backup
            days: Jumlah hari ke belakang untuk mencari file
        
        Returns:
            List dictionary dengan informasi file ZIP
        """
        zip_files = []
        
        if not os.path.exists(folder_path):
            return zip_files
        
        # Cari semua file ZIP
        for file in os.listdir(folder_path):
            if file.lower().endswith('.zip'):
                file_path = os.path.join(folder_path, file)
                
                try:
                    # Dapatkan informasi file
                    stat = os.stat(file_path)
                    file_info = {
                        'filename': file,
                        'full_path': file_path,
                        'size_bytes': stat.st_size,
                        'size_mb': round(stat.st_size / (1024 * 1024), 2),
                        'created_time': datetime.fromtimestamp(stat.st_ctime),
                        'modified_time': datetime.fromtimestamp(stat.st_mtime),
                        'created_str': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                        'modified_str': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    }
                    zip_files.append(file_info)
                    
                except Exception as e:
                    print(f"Error reading file {file}: {e}")
        
        # Urutkan berdasarkan tanggal modifikasi (terbaru dulu)
        zip_files.sort(key=lambda x: x['modified_time'], reverse=True)
        
        self.latest_zips = zip_files
        return zip_files
    
    def display_zip_metadata(self, zip_files: List[Dict]) -> None:
        """
        Menampilkan metadata file ZIP dengan format yang mudah dibaca
        """
        if not zip_files:
            print("Tidak ada file ZIP ditemukan.")
            return
        
        print("=" * 80)
        print("FILE ZIP TERBARU DITEMUKAN")
        print("=" * 80)
        
        for i, zip_info in enumerate(zip_files, 1):
            print(f"\n{i}. {zip_info['filename']}")
            print(f"   📁 Ukuran: {zip_info['size_mb']} MB ({zip_info['size_bytes']:,} bytes)")
            print(f"   📅 Dibuat: {zip_info['created_str']}")
            print(f"   🔄 Dimodifikasi: {zip_info['modified_str']}")
            
            # Coba baca isi ZIP
            try:
                with zipfile.ZipFile(zip_info['full_path'], 'r') as zip_ref:
                    files_in_zip = zip_ref.namelist()
                    print(f"   📦 Berisi {len(files_in_zip)} file:")
                    
                    # Tampilkan maksimal 5 file pertama
                    for j, file_in_zip in enumerate(files_in_zip[:5]):
                        print(f"      - {file_in_zip}")
                    
                    if len(files_in_zip) > 5:
                        print(f"      ... dan {len(files_in_zip) - 5} file lainnya")
                        
            except Exception as e:
                print(f"   ❌ Error membaca ZIP: {e}")
        
        print("\n" + "=" * 80)
    
    def get_zip_contents_detailed(self, zip_path: str) -> Dict:
        """
        Mendapatkan informasi detail isi file ZIP
        """
        result = {
            'success': False,
            'files': [],
            'bak_files': [],
            'total_files': 0,
            'error': None
        }
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                files_info = []
                bak_files = []
                
                for file_info in zip_ref.infolist():
                    file_detail = {
                        'filename': file_info.filename,
                        'size_bytes': file_info.file_size,
                        'size_mb': round(file_info.file_size / (1024 * 1024), 2),
                        'compressed_size': file_info.compress_size,
                        'date_time': datetime(*file_info.date_time).strftime('%Y-%m-%d %H:%M:%S') if file_info.date_time else 'Unknown'
                    }
                    files_info.append(file_detail)
                    
                    # Cek apakah file BAK (database backup)
                    if file_info.filename.lower().endswith('.bak'):
                        bak_files.append(file_detail)
                
                result['success'] = True
                result['files'] = files_info
                result['bak_files'] = bak_files
                result['total_files'] = len(files_info)
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def display_zip_analysis_menu(self, zip_files: List[Dict]) -> Optional[str]:
        """
        Menampilkan menu untuk memilih file ZIP yang akan dianalisis
        """
        if not zip_files:
            print("Tidak ada file ZIP untuk dianalisis.")
            return None
        
        print("\n" + "=" * 60)
        print("PILIH FILE ZIP UNTUK ANALISIS DETAIL")
        print("=" * 60)
        
        for i, zip_info in enumerate(zip_files, 1):
            print(f"{i}. {zip_info['filename']} ({zip_info['size_mb']} MB)")
        
        print(f"{len(zip_files) + 1}. Analisis SEMUA file")
        print("0. Kembali")
        
        try:
            choice = input(f"\nPilih nomor (0-{len(zip_files) + 1}): ").strip()
            
            if choice == '0':
                return None
            elif choice == str(len(zip_files) + 1):
                return 'ALL'
            elif choice.isdigit() and 1 <= int(choice) <= len(zip_files):
                return zip_files[int(choice) - 1]['full_path']
            else:
                print("Pilihan tidak valid!")
                return None
                
        except KeyboardInterrupt:
            print("\nOperasi dibatalkan.")
            return None
    
    def analyze_selected_zip(self, zip_path: str) -> None:
        """
        Menganalisis file ZIP yang dipilih secara detail
        """
        print(f"\n🔍 MENGANALISIS: {os.path.basename(zip_path)}")
        print("=" * 60)
        
        # Dapatkan detail isi ZIP
        contents = self.get_zip_contents_detailed(zip_path)
        
        if not contents['success']:
            print(f"❌ Error: {contents['error']}")
            return
        
        print(f"📦 Total file dalam ZIP: {contents['total_files']}")
        print(f"💾 File database (.bak): {len(contents['bak_files'])}")
        
        if contents['bak_files']:
            print(f"\n📋 DAFTAR FILE DATABASE:")
            for bak_file in contents['bak_files']:
                print(f"   • {bak_file['filename']}")
                print(f"     Ukuran: {bak_file['size_mb']} MB")
                print(f"     Tanggal: {bak_file['date_time']}")
        
        # Tanya apakah ingin ekstrak dan cek database
        print(f"\n❓ Apakah ingin mengekstrak dan mengecek tanggal terbaru di database?")
        choice = input("   Ketik 'y' untuk ya, atau tekan Enter untuk tidak: ").strip().lower()
        
        if choice == 'y':
            self.extract_and_check_database(zip_path, contents['bak_files'])
    
    def extract_and_check_database(self, zip_path: str, bak_files: List[Dict]) -> None:
        """
        Ekstrak file ZIP dan cek tanggal terbaru di database
        """
        print(f"\n🔄 MENGEKSTRAK DAN MENGANALISIS DATABASE...")
        
        # Import database validator
        try:
            from database_validator import DatabaseValidator
            validator = DatabaseValidator()
            
            # Validasi database dalam ZIP
            result = validator.validate_backup_databases([zip_path])
            
            print(f"\n📊 HASIL ANALISIS DATABASE:")
            print(f"   ZIP yang diproses: {result['total_zip_files']}")
            print(f"   Database ditemukan: {len(result['databases_found'])}")
            
            # Tampilkan detail setiap database
            for db_type, db_info in result['databases_found'].items():
                if db_info:
                    print(f"\n   🗄️  {db_type.upper()} Database:")
                    for db_detail in db_info:
                        print(f"      File: {db_detail['zip_file']}")
                        if 'latest_date' in db_detail and db_detail['latest_date']:
                            print(f"      Tanggal terbaru: {db_detail['latest_date']}")
                        else:
                            print(f"      Tanggal terbaru: Tidak dapat dibaca")
                        
                        if 'record_count' in db_detail:
                            print(f"      Jumlah record: {db_detail['record_count']}")
            
        except ImportError:
            print("❌ Module database_validator tidak ditemukan.")
        except Exception as e:
            print(f"❌ Error saat analisis database: {e}")

def main():
    """
    Fungsi utama untuk menjalankan ZIP metadata viewer
    """
    viewer = ZipMetadataViewer()
    
    # Minta input folder
    folder_path = input("Masukkan path folder backup (atau tekan Enter untuk 'real_test_backups'): ").strip()
    if not folder_path:
        folder_path = "real_test_backups"
    
    print(f"\n🔍 Mencari file ZIP di: {folder_path}")
    
    # Cari file ZIP terbaru
    zip_files = viewer.find_latest_zip_files(folder_path)
    
    if not zip_files:
        print("❌ Tidak ada file ZIP ditemukan.")
        return
    
    # Tampilkan metadata
    viewer.display_zip_metadata(zip_files)
    
    # Menu analisis
    while True:
        selected_zip = viewer.display_zip_analysis_menu(zip_files)
        
        if selected_zip is None:
            break
        elif selected_zip == 'ALL':
            print("\n🔄 Menganalisis SEMUA file ZIP...")
            for zip_info in zip_files:
                viewer.analyze_selected_zip(zip_info['full_path'])
                print("\n" + "-" * 60)
        else:
            viewer.analyze_selected_zip(selected_zip)

if __name__ == "__main__":
    main()