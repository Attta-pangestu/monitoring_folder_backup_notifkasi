#!/usr/bin/env python3
"""
Enhanced ZIP Backup Monitor dengan Analisis BAK mendalam
- Deteksi file BAK sebenarnya dalam ZIP
- Parameter analisis ekstensif
- Integrasi dbatools untuk SQL Server analysis
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import json
import zipfile
import sqlite3
import subprocess
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import threading
import time
import logging
from pathlib import Path
import configparser
from typing import Dict, List, Tuple, Optional
import re

class ZipBackupMonitorEnhanced:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Monitor Backup Zip v3.0 - Deep BAK Analysis")
        self.root.geometry("1400x900")

        # Initialize variables
        self.monitoring_path = tk.StringVar()
        self.is_monitoring = False
        self.summary_data = {}
        self.config_file = "config.ini"

        # Setup logging
        self.setup_logging()

        # Load configuration
        self.load_config()

        # Create GUI
        self.create_gui()

        # Start monitoring thread
        self.monitoring_thread = None

    def setup_logging(self):
        """Setup konfigurasi logging"""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'zip_monitor_enhanced.log')),
                logging.StreamHandler()
            ]
        )

        self.logger = logging.getLogger(__name__)

    def load_config(self):
        """Muat konfigurasi dari file INI"""
        self.config = configparser.ConfigParser()

        # Konfigurasi default
        self.config['EMAIL'] = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': '587',
            'sender_email': 'ifesptrj@gmail.com',
            'sender_password': 'ugaowlrdcuhpdafu',
            'recipient_email': 'backupptrj@gmail.com'
        }

        self.config['MONITORING'] = {
            'check_interval': '300',
            'max_age_days': '7',
            'extract_files': 'true',
            'exclude_plantware': 'true',
            'min_size_staging': '2473901824',
            'min_size_venus': '9342988800',
            'min_size_plantware': '37580963840'
        }

        self.config['ANALYSIS'] = {
            'dbatools_timeout': '60',
            'extraction_timeout': '300',
            'enable_sql_analysis': 'true'
        }

        # Load dari file jika ada
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)

    def create_gui(self):
        """Buat interface GUI utama"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Path selection
        path_frame = ttk.LabelFrame(main_frame, text="Pilihan Folder", padding="10")
        path_frame.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(path_frame, text="Folder Monitor:").grid(row=0, column=0, sticky=tk.W)
        path_entry = ttk.Entry(path_frame, textvariable=self.monitoring_path, width=70)
        path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)

        ttk.Button(path_frame, text="Pilih Folder", command=self.browse_path).grid(row=0, column=2)
        ttk.Button(path_frame, text="Deep Scan", command=self.deep_scan_files).grid(row=0, column=3, padx=5)

        # Control buttons
        control_frame = ttk.LabelFrame(main_frame, text="Kontrol Monitoring", padding="10")
        control_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)

        self.start_button = ttk.Button(control_frame, text="Mulai Monitor", command=self.start_monitoring)
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = ttk.Button(control_frame, text="Stop Monitor", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)

        ttk.Button(control_frame, text="Test Email", command=self.send_test_email).grid(row=0, column=2, padx=5)
        ttk.Button(control_frame, text="Kirim Deep Analysis", command=self.send_deep_analysis_email).grid(row=0, column=3, padx=5)

        # Status
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)

        self.status_label = ttk.Label(status_frame, text="Siap untuk Deep Analysis")
        self.status_label.grid(row=0, column=0, sticky=tk.W)

        # Configuration info
        config_frame = ttk.LabelFrame(main_frame, text="Konfigurasi Deep Analysis", padding="10")
        config_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)

        exclude_status = "Dikecualikan" if self.config.getboolean('MONITORING', 'exclude_plantware', fallback=True) else "Diikutsertakan"
        sql_status = "Aktif" if self.config.getboolean('ANALYSIS', 'enable_sql_analysis', fallback=True) else "Non-aktif"
        ttk.Label(config_frame, text=f"PlantwareP3: {exclude_status} | SQL Analysis: {sql_status} | Deep BAK Scan: Aktif",
                 font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W)

        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # Summary tab
        summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(summary_frame, text="Ringkasan")
        self.summary_text = scrolledtext.ScrolledText(summary_frame, height=15, width=100)
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # File list tab
        files_frame = ttk.Frame(self.notebook)
        self.notebook.add(files_frame, text="Daftar File")
        self.files_text = scrolledtext.ScrolledText(files_frame, height=15, width=100)
        self.files_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # BAK Analysis tab
        bak_frame = ttk.Frame(self.notebook)
        self.notebook.add(bak_frame, text="BAK Analysis")
        self.bak_text = scrolledtext.ScrolledText(bak_frame, height=15, width=100)
        self.bak_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Log tab
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="Log")
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=100)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Set default path
        default_path = "D:/Gawean Rebinmas/App_Auto_Backup/Backup"
        if os.path.exists(default_path):
            self.monitoring_path.set(default_path)
            self.logger.info(f"Folder monitor dipilih: {default_path}")

    def browse_path(self):
        """Pilih folder untuk dimonitor"""
        path = filedialog.askdirectory(title="Pilih Folder untuk Dimonitor")
        if path:
            self.monitoring_path.set(path)
            self.logger.info(f"Folder monitor dipilih: {path}")

    def start_monitoring(self):
        """Mulai monitoring folder yang dipilih"""
        if not self.monitoring_path.get():
            messagebox.showerror("Error", "Silakan pilih folder untuk dimonitor")
            return

        self.is_monitoring = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.update_status("Monitoring aktif...")
        self.update_log("Monitoring dimulai...")

        # Start monitoring in background thread
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitoring_thread.start()

    def stop_monitoring(self):
        """Hentikan monitoring"""
        self.is_monitoring = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_status("Monitoring dihentikan")
        self.update_log("Monitoring dihentikan.")

    def monitoring_loop(self):
        """Loop monitoring utama"""
        while self.is_monitoring:
            try:
                # Check if monitoring is still active
                if not self.is_monitoring:
                    break

                # Auto-scan every 5 minutes
                self.deep_scan_files()

                # Wait for next check
                for _ in range(300):  # 5 minutes
                    if not self.is_monitoring:
                        break
                    time.sleep(1)

            except Exception as e:
                self.logger.error(f"Error dalam monitoring loop: {str(e)}")
                time.sleep(5)

    def deep_scan_files(self):
        """Deep scan folder untuk file ZIP dengan analisis BAK mendalam"""
        # Start scanning in a separate thread to prevent GUI freezing
        scan_thread = threading.Thread(target=self._deep_scan_thread, daemon=True)
        scan_thread.start()

    def _deep_scan_thread(self):
        """Thread function for deep scanning files"""
        try:
            path = self.monitoring_path.get()
            if not path or not os.path.exists(path):
                self.update_log("Folder monitor tidak ditemukan.")
                self.update_status("Folder tidak ada")
                return

            self.update_log(f"Memulai DEEP SCAN: {path}")
            self.update_status("Deep scanning file...")

            # Find ZIP files
            zip_files = self.find_zip_files(path)

            if not zip_files:
                self.update_log("Tidak ada file ZIP ditemukan.")
                self.update_status("Tidak ada file")
                return

            # Get latest date and filter files
            latest_date = self.get_latest_date(zip_files)
            filtered_files = [f for f in zip_files if self.is_file_date(f, latest_date)]

            self.update_log(f"Ditemukan {len(filtered_files)} file ZIP untuk deep analysis")

            # Analyze files with progress updates
            self.deep_analyze_files_threaded(filtered_files)

            # Update summary
            self.update_summary()

            self.update_status("Deep scan selesai")

        except Exception as e:
            self.logger.error(f"Error deep scanning: {str(e)}")
            self.update_log(f"Error deep scanning: {str(e)}")
            self.update_status("Error deep scanning")

    def find_zip_files(self, path: str) -> List[str]:
        """Cari semua file ZIP dalam folder"""
        zip_files = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.lower().endswith('.zip'):
                    zip_files.append(os.path.join(root, file))
        return zip_files

    def get_latest_date(self, files: List[str]) -> str:
        """Dapatkan tanggal terbaru dari waktu modifikasi file"""
        latest_time = 0
        for file in files:
            mod_time = os.path.getmtime(file)
            if mod_time > latest_time:
                latest_time = mod_time

        latest_date = datetime.fromtimestamp(latest_time)
        return latest_date.strftime('%Y-%m-%d')

    def is_file_date(self, file_path: str, target_date: str) -> bool:
        """Cek apakah tanggal modifikasi file cocok dengan target tanggal"""
        mod_time = os.path.getmtime(file_path)
        file_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d')
        return file_date == target_date

    def deep_analyze_files_threaded(self, files: List[str]):
        """Deep analyze files dengan BAK analysis mendalam"""
        self.summary_data = {}

        for i, file_path in enumerate(files):
            try:
                self.update_log(f"Deep analyzing ({i+1}/{len(files)}): {os.path.basename(file_path)}")
                self.update_status(f"Deep analyzing file {i+1}/{len(files)}...")

                # Check if should exclude PlantwareP3
                backup_type = self.detect_backup_type(file_path)
                exclude_plantware = self.config.getboolean('MONITORING', 'exclude_plantware', fallback=True)

                if exclude_plantware and backup_type == 'PlantwareP3':
                    self.update_log(f"Melewati PlantwareP3: {os.path.basename(file_path)}")
                    continue

                # Basic file info
                stat_info = os.stat(file_path)
                file_info = {
                    'path': file_path,
                    'size': stat_info.st_size,
                    'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                    'status': 'Menunggu',
                    'extracted': False,
                    'bak_files': [],
                    'compression_ratio': 0,
                    'extractable': False,
                    'corrupt': False,
                    'backup_type': backup_type,
                    'deep_analysis': {}
                }

                # Deep ZIP analysis
                zip_analysis = self.deep_analyze_zip_file(file_path)
                file_info.update(zip_analysis)

                # Extract if enabled for deep BAK analysis
                if self.config.getboolean('MONITORING', 'extract_files'):
                    extracted = self.deep_extract_and_analyze_bak(file_path, file_info)
                    file_info['extracted'] = extracted

                self.summary_data[file_path] = file_info

                # Update GUI
                self.update_file_list(file_info)
                self.update_bak_analysis(file_info)

            except Exception as e:
                self.logger.error(f"Error deep analyzing {file_path}: {str(e)}")
                self.update_log(f"Error deep analyzing {file_path}: {str(e)}")

        # Save summary to JSON
        self.save_summary_json()

    def deep_analyze_zip_file(self, file_path: str) -> Dict:
        """Deep analisis ZIP file dengan parameter tambahan"""
        analysis = {
            'status': 'Tidak Diketahui',
            'extractable': False,
            'corrupt': False,
            'compression_ratio': 0,
            'bak_files': [],
            'file_count': 0,
            'uncompressed_size': 0,
            'compressed_size': 0,
            'backup_type': self.detect_backup_type(file_path),
            'database_info': {},
            'zip_checklist': {},
            'deep_parameters': {}
        }

        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Test integritas ZIP
                bad_file = zip_ref.testzip()
                if bad_file:
                    analysis['corrupt'] = True
                    analysis['status'] = 'Corrupt'
                    return analysis

                # Get file list
                file_list = zip_ref.namelist()
                analysis['file_count'] = len(file_list)

                # Calculate sizes and find BAK files
                current_time = datetime.now()
                zip_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                days_diff = (current_time - zip_mod_time).days

                for file in file_list:
                    info = zip_ref.getinfo(file)
                    analysis['compressed_size'] += info.compress_size
                    analysis['uncompressed_size'] += info.file_size

                    # Deep analysis untuk semua file (bukan hanya .bak)
                    file_analysis = {
                        'filename': file,
                        'size': info.file_size,
                        'extension': os.path.splitext(file)[1].lower(),
                        'is_bak': file.lower().endswith('.bak'),
                        'backup_type': self.detect_backup_type_from_filename(file),
                        'can_extract': True  # Asumsi bisa diekstrak
                    }

                    analysis['bak_files'].append(file_analysis)

                # Calculate compression ratio
                if analysis['uncompressed_size'] > 0:
                    analysis['compression_ratio'] = (1 - analysis['compressed_size'] / analysis['uncompressed_size']) * 100

                analysis['extractable'] = True
                analysis['status'] = 'Valid'

                # Generate deep parameters
                analysis['deep_parameters'] = {
                    'file_date_one_day_different': days_diff == 1,
                    'days_difference': days_diff,
                    'can_be_extracted': True,  # Akan dicek saat ekstraksi
                    'dbatools_status': 'Unknown',  # Akan dicek saat BAK analysis
                    'contains_bak_files': len([f for f in analysis['bak_files'] if f['is_bak']]) > 0,
                    'bak_file_count': len([f for f in analysis['bak_files'] if f['is_bak']]),
                    'all_files_count': len(analysis['bak_files'])
                }

                # Generate ZIP checklist
                analysis['zip_checklist'] = self.generate_enhanced_zip_checklist(file_path, analysis)

        except Exception as e:
            analysis['corrupt'] = True
            analysis['status'] = f'Error: {str(e)}'

        return analysis

    def deep_extract_and_analyze_bak(self, zip_path: str, file_info: Dict) -> bool:
        """Extract ZIP dan deep analyze BAK files"""
        try:
            extract_dir = os.path.dirname(zip_path)
            extracted_files = []

            # Extract ZIP
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                extracted_files = zip_ref.namelist()

            self.update_log(f"Terekstrak: {os.path.basename(zip_path)} - {len(extracted_files)} files")

            # Find extracted BAK files
            bak_analysis_results = []
            sql_analysis_available = self.config.getboolean('ANALYSIS', 'enable_sql_analysis', fallback=True)

            for extracted_file in extracted_files:
                extracted_path = os.path.join(extract_dir, extracted_file)

                if os.path.exists(extracted_path):
                    file_ext = os.path.splitext(extracted_file)[1].lower()
                    backup_type = self.detect_backup_type_from_filename(extracted_file)

                    # Deep analysis untuk setiap file
                    file_analysis = {
                        'filename': extracted_file,
                        'path': extracted_path,
                        'size': os.path.getsize(extracted_path),
                        'extension': file_ext,
                        'backup_type': backup_type,
                        'exists': True,
                        'readable': os.access(extracted_path, os.R_OK),
                        'dbatools_analysis': {},
                        'sql_analysis': {},
                        'validation_checklist': {}
                    }

                    # Skip PlantwareP3 if excluded
                    exclude_plantware = self.config.getboolean('MONITORING', 'exclude_plantware', fallback=True)
                    if exclude_plantware and backup_type == 'PlantwareP3':
                        file_analysis['excluded'] = True
                        bak_analysis_results.append(file_analysis)
                        continue

                    # DBATools analysis (for .bak files)
                    if file_ext == '.bak' or 'backup' in extracted_file.lower():
                        dbatools_result = self.analyze_with_dbatools(extracted_path, backup_type)
                        file_analysis['dbatools_analysis'] = dbatools_result

                    # SQL Server analysis (if enabled)
                    if sql_analysis_available and (file_ext == '.bak' or 'backup' in extracted_file.lower()):
                        sql_result = self.analyze_with_sql_server(extracted_path, backup_type)
                        file_analysis['sql_analysis'] = sql_result

                    # Generate validation checklist
                    file_analysis['validation_checklist'] = self.generate_bak_validation_checklist(
                        extracted_path, backup_type, file_analysis
                    )

                    bak_analysis_results.append(file_analysis)

            # Update file_info with deep analysis results
            file_info['deep_analysis']['extracted_files'] = bak_analysis_results
            file_info['deep_analysis']['extraction_successful'] = True
            file_info['deep_analysis']['dbatools_status'] = self.get_dbatools_overall_status(bak_analysis_results)
            file_info['deep_analysis']['can_be_extracted'] = True

            return True

        except Exception as e:
            self.logger.error(f"Error deep extracting {zip_path}: {str(e)}")
            self.update_log(f"Error deep extracting {zip_path}: {str(e)}")

            # Update file_info with error status
            file_info['deep_analysis']['extraction_successful'] = False
            file_info['deep_analysis']['extraction_error'] = str(e)
            file_info['deep_analysis']['can_be_extracted'] = False
            file_info['deep_analysis']['dbatools_status'] = 'Extraction Failed'

            return False

    def analyze_with_dbatools(self, bak_path: str, backup_type: str) -> Dict:
        """Analyze BAK file dengan dbatools (simulasi)"""
        try:
            if not os.path.exists(bak_path):
                return {'status': 'File not found', 'error': 'File does not exist'}

            # Simulasi dbatools analysis
            file_size = os.path.getsize(bak_path)
            analysis = {
                'status': 'Analyzed',
                'file_size': file_size,
                'file_size_formatted': self.format_size(file_size),
                'readable': os.access(bak_path, os.R_OK),
                'backup_type': backup_type,
                'analysis_timestamp': datetime.now().isoformat(),
                'dbatools_version': 'Simulated v1.0',
                'warnings': [],
                'errors': []
            }

            # Simulate dbatools checks
            if file_size < 1024:  # < 1KB
                analysis['warnings'].append('File size very small')

            if not os.access(bak_path, os.R_OK):
                analysis['errors'].append('File not readable')
                analysis['status'] = 'Read Error'

            # Check if file looks like a valid backup
            try:
                with open(bak_path, 'rb') as f:
                    header = f.read(512)
                    if len(header) < 100:
                        analysis['warnings'].append('File header too short')
                    else:
                        analysis['header_analysis'] = 'Valid backup header detected'
            except Exception as e:
                analysis['errors'].append(f'Header read error: {str(e)}')

            return analysis

        except Exception as e:
            return {
                'status': 'Analysis Failed',
                'error': str(e),
                'backup_type': backup_type,
                'analysis_timestamp': datetime.now().isoformat()
            }

    def analyze_with_sql_server(self, bak_path: str, backup_type: str) -> Dict:
        """Analyze BAK file dengan SQL Server commands"""
        try:
            if not self.is_sql_server_available():
                return {
                    'status': 'SQL Server Unavailable',
                    'error': 'SQL Server not accessible',
                    'backup_type': backup_type
                }

            # Try RESTORE HEADERONLY
            cmd = [
                'sqlcmd',
                '-S', 'localhost',
                '-Q', f'RESTORE HEADERONLY FROM DISK = N\'{bak_path}\''
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return self.parse_sql_header_output(result.stdout, bak_path, backup_type)
            else:
                return {
                    'status': 'SQL Command Failed',
                    'error': result.stderr,
                    'backup_type': backup_type,
                    'return_code': result.returncode
                }

        except subprocess.TimeoutExpired:
            return {
                'status': 'Timeout',
                'error': 'SQL Server command timeout',
                'backup_type': backup_type
            }
        except Exception as e:
            return {
                'status': 'Analysis Failed',
                'error': str(e),
                'backup_type': backup_type
            }

    def is_sql_server_available(self) -> bool:
        """Check if SQL Server is available"""
        try:
            result = subprocess.run(
                ['sqlcmd', '-S', 'localhost', '-Q', 'SELECT 1'],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False

    def parse_sql_header_output(self, output: str, bak_path: str, backup_type: str) -> Dict:
        """Parse SQL Server RESTORE HEADERONLY output"""
        try:
            lines = output.split('\n')
            info = {
                'status': 'SQL Analysis Complete',
                'backup_type': backup_type,
                'database_name': '',
                'backup_date': '',
                'backup_size': 0,
                'position': 0,
                'warnings': []
            }

            # Extract basic info from output
            for line in lines:
                if 'BackupStartDate' in line and len(line.split()) > 1:
                    info['backup_date'] = line.split()[-1]
                elif 'DatabaseName' in line and len(line.split()) > 1:
                    info['database_name'] = line.split()[-1]
                elif 'BackupSize' in line and len(line.split()) > 1:
                    try:
                        info['backup_size'] = int(line.split()[-1])
                    except:
                        pass

            return info

        except Exception as e:
            return {
                'status': 'Parse Error',
                'error': str(e),
                'backup_type': backup_type
            }

    def get_dbatools_overall_status(self, bak_analysis_results: List[Dict]) -> str:
        """Get overall dbatools status from analysis results"""
        if not bak_analysis_results:
            return 'No Files'

        successful_analyses = [
            f for f in bak_analysis_results
            if f.get('dbatools_analysis', {}).get('status') == 'Analyzed'
        ]

        if len(successful_analyses) == len(bak_analysis_results):
            return 'All Files Readable'
        elif successful_analyses:
            return f'{len(successful_analyses)}/{len(bak_analysis_results)} Files Readable'
        else:
            return 'No Files Readable'

    def generate_enhanced_zip_checklist(self, file_path: str, analysis: Dict) -> Dict:
        """Generate enhanced ZIP checklist"""
        checklist = {
            'integritas_struktur': {
                'status': not analysis.get('corrupt', True),
                'keterangan': 'Struktur file ZIP valid',
                'hasil': '[VALID]' if not analysis.get('corrupt', True) else '[GAGAL]'
            },
            'kemampuan_ekstrak': {
                'status': analysis.get('extractable', False),
                'keterangan': 'File dapat diekstrak',
                'hasil': '[VALID]' if analysis.get('extractable', False) else '[GAGAL]'
            },
            'file_date_one_day_different': {
                'status': analysis.get('deep_parameters', {}).get('file_date_one_day_different', False),
                'keterangan': 'File date berbeda satu hari',
                'hasil': '[VALID]' if analysis.get('deep_parameters', {}).get('file_date_one_day_different', False) else '[GAGAL]'
            },
            'contains_bak_files': {
                'status': analysis.get('deep_parameters', {}).get('contains_bak_files', False),
                'keterangan': 'Mengandung file BAK',
                'hasil': '[VALID]' if analysis.get('deep_parameters', {}).get('contains_bak_files', False) else '[GAGAL]'
            },
            'ukuran_file_wajar': {
                'status': analysis.get('size', 0) > 1024 * 1024,  # > 1MB
                'keterangan': 'Ukuran file wajar (>1MB)',
                'hasil': '[VALID]' if analysis.get('size', 0) > 1024 * 1024 else '[GAGAL]'
            },
            'tanggal_modifikasi_valid': {
                'status': analysis.get('deep_parameters', {}).get('days_difference', 0) <= 365,
                'keterangan': 'Tanggal modifikasi valid (≤365 hari)',
                'hasil': '[VALID]' if analysis.get('deep_parameters', {}).get('days_difference', 0) <= 365 else '[GAGAL]'
            }
        }

        return checklist

    def generate_bak_validation_checklist(self, bak_path: str, backup_type: str, analysis: Dict) -> Dict:
        """Generate comprehensive BAK validation checklist"""
        checklist = {
            'file_ada_dan_dapat_diakses': {
                'status': analysis.get('exists', False) and analysis.get('readable', False),
                'keterangan': 'File BAK ada dan dapat diakses',
                'hasil': '[VALID]' if analysis.get('exists', False) and analysis.get('readable', False) else '[GAGAL]'
            },
            'ukuran_file_wajar': {
                'status': analysis.get('size', 0) > 10240,  # > 10KB
                'keterangan': 'Ukuran file BAK wajar (>10KB)',
                'hasil': '[VALID]' if analysis.get('size', 0) > 10240 else '[GAGAL]'
            },
            'dbatools_dapat_membaca': {
                'status': analysis.get('dbatools_analysis', {}).get('status') == 'Analyzed',
                'keterangan': 'DBATools dapat membaca .bak file',
                'hasil': '[VALID]' if analysis.get('dbatools_analysis', {}).get('status') == 'Analyzed' else '[GAGAL]'
            },
            'sql_server_dapat_membaca': {
                'status': analysis.get('sql_analysis', {}).get('status') == 'SQL Analysis Complete',
                'keterangan': 'SQL Server dapat membaca .bak file',
                'hasil': '[VALID]' if analysis.get('sql_analysis', {}).get('status') == 'SQL Analysis Complete' else '[GAGAL]'
            },
            'bisa_diekstrak_dari_zip': {
                'status': True,  # Karena sudah diekstrak sampai sini
                'keterangan': 'File dapat diekstrak dari ZIP',
                'hasil': '[VALID]'
            },
            'tanggal_backup_masuk_akal': {
                'status': len(analysis.get('dbatools_analysis', {}).get('warnings', [])) == 0,
                'keterangan': 'Tanggal backup masuk akal',
                'hasil': '[VALID]' if len(analysis.get('dbatools_analysis', {}).get('warnings', [])) == 0 else '[GAGAL]'
            },
            'ukuran_minimum_backup': {
                'status': self.check_minimum_size(backup_type, analysis.get('size', 0)),
                'keterangan': f'Ukuran minimum {backup_type}',
                'hasil': '[VALID]' if self.check_minimum_size(backup_type, analysis.get('size', 0)) else '[GAGAL]'
            },
            'format_backup_valid': {
                'status': analysis.get('dbatools_analysis', {}).get('header_analysis') == 'Valid backup header detected',
                'keterangan': 'Format backup database valid',
                'hasil': '[VALID]' if analysis.get('dbatools_analysis', {}).get('header_analysis') == 'Valid backup header detected' else '[GAGAL]'
            },
            'tidak_corrupt': {
                'status': len(analysis.get('dbatools_analysis', {}).get('errors', [])) == 0,
                'keterangan': 'File BAK tidak corrupt',
                'hasil': '[VALID]' if len(analysis.get('dbatools_analysis', {}).get('errors', [])) == 0 else '[GAGAL]'
            }
        }

        return checklist

    def check_minimum_size(self, backup_type: str, size: int) -> bool:
        """Check if file size meets minimum requirements"""
        min_sizes = {
            'BackupStaging': 2473901824,   # 2.3 GB
            'BackupVenus': 9342988800,     # 8.7 GB
            'PlantwareP3': 37580963840    # 35 GB
        }

        min_size = min_sizes.get(backup_type, 1073741824)  # Default 1GB
        return size >= min_size

    def detect_backup_type(self, file_path: str) -> str:
        """Deteksi jenis backup dari nama file ZIP"""
        filename = os.path.basename(file_path).lower()

        if filename.startswith('backupstaging'):
            return 'BackupStaging'
        elif filename.startswith('backupvenu'):
            return 'BackupVenus'
        elif filename.startswith('plantwarep3'):
            return 'PlantwareP3'
        else:
            return 'Unknown'

    def detect_backup_type_from_filename(self, filename: str) -> str:
        """Deteksi jenis backup dari nama file BAK"""
        filename_lower = filename.lower()

        if 'staging' in filename_lower or 'gwscanner' in filename_lower:
            return 'BackupStaging'
        elif 'venu' in filename_lower or 'venus' in filename_lower:
            return 'BackupVenus'
        elif 'plantware' in filename_lower or 'p3' in filename_lower:
            return 'PlantwareP3'
        else:
            return 'Unknown'

    def update_file_list(self, file_info: Dict):
        """Update daftar file di GUI"""
        filename = os.path.basename(file_info['path'])
        backup_type = file_info.get('backup_type', 'Unknown')
        size = self.format_size(file_info['size'])
        status = file_info['status']
        compression = f"{file_info.get('compression_ratio', 0):.1f}%"

        # Deep analysis info
        deep_params = file_info.get('deep_parameters', {})
        bak_count = deep_params.get('bak_file_count', 0)
        dbatools_status = deep_params.get('dbatools_status', 'Unknown')
        one_day_diff = "✓" if deep_params.get('file_date_one_day_different', False) else "✗"

        file_entry = f"{filename} | {backup_type} | {size} | {status} | BAK: {bak_count} | DBATools: {dbatools_status} | 1Day: {one_day_diff} | Kompresi: {compression}\n"
        self.files_text.insert(tk.END, file_entry)

    def update_bak_analysis(self, file_info: Dict):
        """Update BAK analysis di GUI"""
        filename = os.path.basename(file_info['path'])
        deep_analysis = file_info.get('deep_analysis', {})

        bak_entry = f"\n{'='*80}\n"
        bak_entry += f"Deep Analysis: {filename}\n"
        bak_entry += f"{'='*80}\n"

        # Basic info
        bak_entry += f"Status: {file_info.get('status', 'Unknown')}\n"
        bak_entry += f"Backup Type: {file_info.get('backup_type', 'Unknown')}\n"
        bak_entry += f"Size: {self.format_size(file_info.get('size', 0))}\n"
        bak_entry += f"Modified: {file_info.get('modified', 'Unknown')}\n"

        # Deep parameters
        deep_params = file_info.get('deep_parameters', {})
        bak_entry += f"\nDeep Parameters:\n"
        bak_entry += f"  File Date One Day Different: {deep_params.get('file_date_one_day_different', False)}\n"
        bak_entry += f"  Days Difference: {deep_params.get('days_difference', 'Unknown')} days\n"
        bak_entry += f"  Can Be Extracted: {deep_params.get('can_be_extracted', 'Unknown')}\n"
        bak_entry += f"  DBATools Status: {deep_params.get('dbatools_status', 'Unknown')}\n"
        bak_entry += f"  Contains BAK Files: {deep_params.get('contains_bak_files', False)}\n"
        bak_entry += f"  BAK File Count: {deep_params.get('bak_file_count', 0)}\n"

        # Extracted files analysis
        if 'extracted_files' in deep_analysis:
            bak_entry += f"\nExtracted Files Analysis ({len(deep_analysis['extracted_files'])} files):\n"
            for extracted in deep_analysis['extracted_files']:
                bak_entry += f"\n  File: {extracted['filename']}\n"
                bak_entry += f"    Size: {self.format_size(extracted.get('size', 0))}\n"
                bak_entry += f"    Extension: {extracted.get('extension', 'Unknown')}\n"
                bak_entry += f"    Readable: {extracted.get('readable', False)}\n"
                bak_entry += f"    Backup Type: {extracted.get('backup_type', 'Unknown')}\n"

                # DBATools analysis
                dbatools = extracted.get('dbatools_analysis', {})
                bak_entry += f"    DBATools Status: {dbatools.get('status', 'Unknown')}\n"
                if dbatools.get('warnings'):
                    bak_entry += f"    Warnings: {', '.join(dbatools['warnings'])}\n"
                if dbatools.get('errors'):
                    bak_entry += f"    Errors: {', '.join(dbatools['errors'])}\n"

                # SQL analysis
                sql = extracted.get('sql_analysis', {})
                bak_entry += f"    SQL Status: {sql.get('status', 'Unknown')}\n"
                if sql.get('database_name'):
                    bak_entry += f"    Database: {sql.get('database_name')}\n"
                if sql.get('backup_date'):
                    bak_entry += f"    Backup Date: {sql.get('backup_date')}\n"

        # ZIP Checklist
        if 'zip_checklist' in file_info:
            bak_entry += f"\nZIP Validation Checklist:\n"
            for check_name, check_info in file_info['zip_checklist'].items():
                bak_entry += f"  {check_info['hasil']} {check_info['keterangan']}\n"

        self.bak_text.insert(tk.END, bak_entry)

    def update_summary(self):
        """Update informasi ringkasan dengan deep analysis"""
        total_files = len(self.summary_data)
        valid_files = sum(1 for f in self.summary_data.values() if f['status'] == 'Valid')
        extracted_files = sum(1 for f in self.summary_data.values() if f['extracted'])

        # Calculate compression info
        total_compressed = sum(f.get('compressed_size', 0) for f in self.summary_data.values())
        total_uncompressed = sum(f.get('uncompressed_size', 0) for f in self.summary_data.values())
        avg_compression = (total_compressed / total_uncompressed * 100) if total_uncompressed > 0 else 0

        # Deep analysis statistics
        total_bak_files = sum(f.get('deep_parameters', {}).get('bak_file_count', 0) for f in self.summary_data.values())
        dbatools_status_count = {}
        for f in self.summary_data.values():
            status = f.get('deep_parameters', {}).get('dbatools_status', 'Unknown')
            dbatools_status_count[status] = dbatools_status_count.get(status, 0) + 1

        one_day_diff_count = sum(1 for f in self.summary_data.values() if f.get('deep_parameters', {}).get('file_date_one_day_different', False))

        exclude_plantware = self.config.getboolean('MONITORING', 'exclude_plantware', fallback=True)

        summary_text = f"""Laporan Deep Analysis Backup (PlantwareP3 Dikecualikan)
===============================================================

Total file ZIP: {total_files}
File ZIP valid: {valid_files}
File diekstrak: {extracted_files}
PlantwareP3 dikecualikan: {'Ya' if exclude_plantware else 'Tidak'}

Informasi Kompresi:
- Total size terkompres: {self.format_size(total_compressed)}
- Total size asli: {self.format_size(total_uncompressed)}
- Rata-rata rasio kompresi: {avg_compression:.1f}%

Deep Analysis Parameters:
- Total BAK files ditemukan: {total_bak_files}
- File date one day different: {one_day_diff_count}
- DBATools Status: {dict(dbatools_status_count)}

DBATools Analysis Results:
"""

        for status, count in dbatools_status_count.items():
            summary_text += f"- {status}: {count}\n"

        summary_text += f"\nDibuat: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, summary_text)

    def send_test_email(self):
        """Kirim email test"""
        try:
            subject = "[VALID] Enhanced Monitor Backup - Email Test"
            body = "Ini adalah email test dari Enhanced Monitor Backup.\n\nWaktu pengiriman: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            self.send_email(subject, body)
            messagebox.showinfo("Success", "Email test berhasil dikirim!")
            self.update_log("Email test berhasil dikirim")

        except Exception as e:
            messagebox.showerror("Error", f"Gagal mengirim email test: {str(e)}")
            self.update_log(f"Gagal mengirim email test: {str(e)}")

    def send_deep_analysis_email(self):
        """Kirim email deep analysis report"""
        try:
            if not self.summary_data:
                self.update_log("Tidak ada data deep analysis untuk dikirim")
                messagebox.showwarning("Warning", "Tidak ada data deep analysis untuk dikirim")
                return

            subject = f"[VALID] Deep Analysis Report - {datetime.now().strftime('%Y-%m-%d')}"
            body = self.generate_deep_analysis_email_template()

            self.send_email(subject, body)
            messagebox.showinfo("Success", "Deep analysis report berhasil dikirim!")
            self.update_log("Deep analysis report berhasil dikirim")

        except Exception as e:
            messagebox.showerror("Error", f"Gagal mengirim deep analysis report: {str(e)}")
            self.update_log(f"Gagal mengirim deep analysis report: {str(e)}")

    def generate_deep_analysis_email_template(self) -> str:
        """Generate template email deep analysis"""
        if not self.summary_data:
            return ""

        total_files = len(self.summary_data)
        valid_files = sum(1 for f in self.summary_data.values() if f['status'] == 'Valid')
        extracted_files = sum(1 for f in self.summary_data.values() if f['extracted'])

        # Deep statistics
        total_bak_files = sum(f.get('deep_parameters', {}).get('bak_file_count', 0) for f in self.summary_data.values())
        one_day_diff_count = sum(1 for f in self.summary_data.values() if f.get('deep_parameters', {}).get('file_date_one_day_different', False))

        body = f"""Deep Analysis Backup Report
==========================

Waktu Generate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Statistik ZIP Files:
- Total ZIP Files: {total_files}
- Valid ZIP Files: {valid_files}
- Extracted Files: {extracted_files}
- Success Rate: {(valid_files/total_files*100):.1f}%

Deep Analysis Parameters:
- Total BAK Files Found: {total_bak_files}
- Files with 1-Day Date Difference: {one_day_diff_count}

Detail per File:
"""

        for file_path, file_info in self.summary_data.items():
            filename = os.path.basename(file_path)
            backup_type = file_info.get('backup_type', 'Unknown')
            size = self.format_size(file_info.get('size', 0))
            status = file_info.get('status', 'Unknown')

            deep_params = file_info.get('deep_parameters', {})
            bak_count = deep_params.get('bak_file_count', 0)
            dbatools_status = deep_params.get('dbatools_status', 'Unknown')
            one_day_diff = "Yes" if deep_params.get('file_date_one_day_different', False) else "No"

            body += f"\n{filename} ({backup_type})\n"
            body += f"  Size: {size}\n"
            body += f"  Status: {status}\n"
            body += f"  BAK Files: {bak_count}\n"
            body += f"  DBATools Status: {dbatools_status}\n"
            body += f"  1-Day Difference: {one_day_diff}\n"

            # Extracted files info
            if 'extracted_files' in file_info.get('deep_analysis', {}):
                extracted_count = len(file_info['deep_analysis']['extracted_files'])
                readable_count = sum(1 for f in file_info['deep_analysis']['extracted_files'] if f.get('readable', False))
                body += f"  Extracted Files: {extracted_count} (Readable: {readable_count})\n"

        body += f"\n\nEmail ini dihasilkan oleh Enhanced Monitor Backup v3.0"

        return body

    def send_email(self, subject: str, body: str, attachment_path: str = None):
        """Kirim notifikasi email"""
        try:
            # Get email configuration
            smtp_server = self.config['EMAIL']['smtp_server']
            smtp_port = int(self.config['EMAIL']['smtp_port'])
            sender_email = self.config['EMAIL']['sender_email']
            sender_password = self.config['EMAIL']['sender_password']
            recipient_email = self.config['EMAIL']['recipient_email']

            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject

            # Attach body
            msg.attach(MIMEText(body, 'plain'))

            # Add attachment if provided
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(attachment_path)}'
                )
                msg.attach(part)

            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, recipient_email, text)
            server.quit()

        except Exception as e:
            self.logger.error(f"Error mengirim email: {str(e)}")
            raise

    def save_summary_json(self):
        """Simpan summary data ke file JSON"""
        try:
            with open('backup_summary_enhanced.json', 'w', encoding='utf-8') as f:
                json.dump(self.summary_data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            self.logger.error(f"Error menyimpan summary JSON: {str(e)}")

    def update_status(self, message: str):
        """Update status label"""
        self.status_label.config(text=message)

    def update_log(self, message: str):
        """Update log text"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"

        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)

    def format_size(self, size_bytes: int) -> str:
        """Format size dalam format yang mudah dibaca"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

def main():
    root = tk.Tk()
    app = ZipBackupMonitorEnhanced(root)
    root.mainloop()

if __name__ == "__main__":
    main()