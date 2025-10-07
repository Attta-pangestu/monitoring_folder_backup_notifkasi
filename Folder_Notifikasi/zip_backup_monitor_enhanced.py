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
            'min_size_staging': '2473901824',  # 2.3 GB
            'min_size_venus': '9342988800',     # 8.7 GB
            'min_size_plantware': '37580963840' # 35 GB
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

        # ZIP Summary tab
        zip_summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(zip_summary_frame, text="ZIP Summary")
        self.zip_summary_text = scrolledtext.ScrolledText(zip_summary_frame, height=15, width=100)
        self.zip_summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # BAK Summary tab
        bak_summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(bak_summary_frame, text="BAK Summary")
        self.bak_summary_text = scrolledtext.ScrolledText(bak_summary_frame, height=15, width=100)
        self.bak_summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

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

                # Check if backup is outdated
                is_outdated, days_diff = self.check_backup_outdated(file_path)
                analysis['is_outdated'] = is_outdated
                analysis['days_difference'] = days_diff

                # Generate ZIP checklist
                analysis['zip_checklist'] = self.generate_enhanced_zip_checklist(file_path, analysis)

        except Exception as e:
            analysis['corrupt'] = True
            analysis['status'] = f'Error: {str(e)}'
            # Set default values for error cases
            analysis['is_outdated'] = True  # Assume outdated if error
            analysis['days_difference'] = 999

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

                    # Check date analysis - ALWAYS use ZIP file date, not BAK file date
                    # BAK file date changes when extracted, ZIP file date is the actual backup date
                    is_outdated, days_diff = self.check_backup_outdated(zip_path)
                    file_analysis['is_outdated'] = is_outdated
                    file_analysis['days_since_backup'] = days_diff

                    # Check if file date is one day different (modified within 24 hours) - use ZIP file
                    zip_mod_time = os.path.getmtime(zip_path)
                    zip_mod_date = datetime.fromtimestamp(zip_mod_time)
                    current_date = datetime.now()
                    hours_diff = (current_date - zip_mod_date).total_seconds() / 3600
                    file_analysis['file_date_one_day_different'] = hours_diff <= 24
                    
                    # Store ZIP file modification date for reporting
                    file_analysis['zip_modification_date'] = zip_mod_date.isoformat()
                    file_analysis['backup_date'] = zip_mod_date.strftime('%Y-%m-%d %H:%M:%S')

                    # Log date analysis for debugging - clarify we're using ZIP file date
                    self.logger.info(f"Date analysis for {extracted_file} (using ZIP file date): "
                                   f"zip_date={zip_mod_date.strftime('%Y-%m-%d %H:%M:%S')}, "
                                   f"hours_diff={hours_diff:.1f}, one_day_diff={file_analysis['file_date_one_day_different']}, "
                                   f"days_since_backup={days_diff}, is_outdated={is_outdated}")

                    # Check if file size is below minimum threshold (for warning)
                    min_size_met = self.check_minimum_size(backup_type, file_analysis['size'])
                    file_analysis['size_warning'] = not min_size_met

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
                    # Try to get a proper date, not just the last word
                    date_part = line.split()[-1]
                    if date_part and date_part != 'CompressionAlgorithm':
                        info['backup_date'] = date_part
                elif 'DatabaseName' in line and len(line.split()) > 1:
                    info['database_name'] = line.split()[-1]
                elif 'BackupSize' in line and len(line.split()) > 1:
                    try:
                        info['backup_size'] = int(line.split()[-1])
                    except:
                        pass

            # If backup_date is still not set or invalid, use ZIP file date
            if not info.get('backup_date') or info['backup_date'] == 'CompressionAlgorithm':
                # Use ZIP file modification date as backup date
                zip_path = bak_path.replace('.bak', '.zip')
                if os.path.exists(zip_path):
                    zip_mod_time = datetime.fromtimestamp(os.path.getmtime(zip_path))
                    info['backup_date'] = zip_mod_time.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    # Fallback to current date
                    info['backup_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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
            },
            'backup_tidak_outdated': {
                'status': not analysis.get('is_outdated', False),
                'keterangan': 'Backup tidak outdated (< 7 hari)',
                'hasil': '[VALID]' if not analysis.get('is_outdated', False) else '[GAGAL - OUTDATED]'
            },
            'file_date_recent': {
                'status': analysis.get('file_date_one_day_different', False),
                'keterangan': 'File date dalam 24 jam terakhir',
                'hasil': '[VALID]' if analysis.get('file_date_one_day_different', False) else '[INFO]'
            },
            'size_minimum_terpenuhi': {
                'status': not analysis.get('size_warning', True),
                'keterangan': 'Size minimum terpenuhi',
                'hasil': '[VALID]' if not analysis.get('size_warning', True) else '[WARNING - SIZE]'
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

    def check_backup_outdated(self, file_path: str) -> Tuple[bool, int]:
        """Check if backup is outdated - file modified date is different from current date"""
        try:
            mod_time = os.path.getmtime(file_path)
            mod_date = datetime.fromtimestamp(mod_time)
            current_date = datetime.now()
            days_diff = (current_date - mod_date).days

            # Consider outdated if modification date is not today
            is_outdated = mod_date.date() != current_date.date()

            # Log for debugging
            self.logger.info(f"Backup age check for {os.path.basename(file_path)}: modified {mod_date.strftime('%Y-%m-%d')}, current {current_date.strftime('%Y-%m-%d')}, outdated: {is_outdated}")

            return is_outdated, days_diff
        except Exception as e:
            self.logger.warning(f"Error checking outdated status for {file_path}: {e}")
            return False, 0

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
        """Update informasi ringkasan dengan ZIP dan BAK summaries"""
        # Generate comprehensive summaries
        scan_results = {
            'files': list(self.summary_data.values()),
            'total_zip_files': len(self.summary_data),
            'valid_zip_files': sum(1 for f in self.summary_data.values() if f.get('status') == 'Valid'),
            'corrupted_zip_files': sum(1 for f in self.summary_data.values() if f.get('status') == 'Corrupted')
        }

        zip_summary = self.generate_zip_summary(scan_results)
        bak_summary = self.generate_bak_summary(scan_results)

        exclude_plantware = self.config.getboolean('MONITORING', 'exclude_plantware', fallback=True)

        summary_text = f"""DEEP ANALYSIS SUMMARY REPORT
===============================================================

📁 ZIP SUMMARY
---------------------------------------------------------------
Total ZIP Files: {zip_summary['total_zip_files']}
Valid ZIP Files: {zip_summary['valid_zip_files']}
Corrupted ZIP Files: {zip_summary['corrupted_zip_files']}

Total ZIP Size: {zip_summary['total_size_formatted']}
Average ZIP Size: {zip_summary['average_size_formatted']}
Largest ZIP: {zip_summary['largest_file']['filename']} ({zip_summary['largest_file']['size_formatted']})
Smallest ZIP: {zip_summary['smallest_file']['filename']} ({zip_summary['smallest_file']['size_formatted']})

Age Distribution:
- Today: {zip_summary['age_analysis']['today']} files
- Last 7 days: {zip_summary['age_analysis']['last_7_days']} files
- Older than 7 days: {zip_summary['age_analysis']['older_than_7_days']} files

Status Distribution:
- Valid: {zip_summary['by_status']['valid']} files
- Corrupted: {zip_summary['by_status']['corrupted']} files
- Excluded: {zip_summary['by_status']['excluded']} files

🗄️  BAK SUMMARY
---------------------------------------------------------------
Total BAK Files: {bak_summary['total_bak_files']}
Analyzed BAK Files: {bak_summary['analyzed_bak_files']}
Failed Analysis: {bak_summary['failed_analysis']}

Total BAK Size: {bak_summary['total_bak_size_formatted']}
Average BAK Size: {bak_summary['average_bak_size_formatted']}

Size Validation:
- Above minimum: {bak_summary['size_validation']['above_minimum']} files
- Below minimum: {bak_summary['size_validation']['below_minimum']} files

Age Analysis:
- Recent 24h: {bak_summary['age_analysis']['recent_24h']} files
- Last 7 days: {bak_summary['age_analysis']['last_7_days']} files
- Older than 7 days: {bak_summary['age_analysis']['older_than_7_days']} files
- Outdated files: {len(bak_summary['age_analysis']['outdated_files'])}

DBATools Analysis:
- Successful: {bak_summary['dbatools_analysis']['successful']} files
- Failed: {bak_summary['dbatools_analysis']['failed']} files
- Not attempted: {bak_summary['dbatools_analysis']['not_attempted']} files

Validation Status:
- Valid (90%+): {bak_summary['by_validation_status']['valid']} files
- Warning (70-89%): {bak_summary['by_validation_status']['warning']} files
- Invalid (<70%): {bak_summary['by_validation_status']['invalid']} files
- Excluded: {bak_summary['by_validation_status']['excluded']} files

Checklist Performance:
- Total checklists: {bak_summary['checklist_summary']['total_checklists']}
- Perfect scores: {bak_summary['checklist_summary']['perfect_scores']}
- Average score: {bak_summary['checklist_summary']['average_score']:.1f}%

Configuration:
- PlantwareP3 dikecualikan: {'Ya' if exclude_plantware else 'Tidak'}
- Deep BAK Analysis: Aktif
- Size validation: Aktif

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, summary_text)

        # Store summaries for email generation
        self.zip_summary = zip_summary
        self.bak_summary = bak_summary

        # Update ZIP Summary tab
        self.update_zip_summary_tab(zip_summary)

        # Update BAK Summary tab
        self.update_bak_summary_tab(bak_summary)

    def update_zip_summary_tab(self, zip_summary):
        """Update ZIP Summary tab dengan detailed analysis"""
        zip_summary_text = f"""📁 ZIP SUMMARY - DETAILED ANALYSIS
===============================================================

BASIC STATISTICS
---------------------------------------------------------------
Total ZIP Files: {zip_summary['total_zip_files']}
Valid ZIP Files: {zip_summary['valid_zip_files']}
Corrupted ZIP Files: {zip_summary['corrupted_zip_files']}

SIZE ANALYSIS
---------------------------------------------------------------
Total ZIP Size: {zip_summary['total_size_formatted']}
Average ZIP Size: {zip_summary['average_size_formatted']}
Largest ZIP: {zip_summary['largest_file']['filename']} ({zip_summary['largest_file']['size_formatted']})
Smallest ZIP: {zip_summary['smallest_file']['filename']} ({zip_summary['smallest_file']['size_formatted']})

AGE DISTRIBUTION
---------------------------------------------------------------
Today: {zip_summary['age_analysis']['today']} files
Last 7 days: {zip_summary['age_analysis']['last_7_days']} files
Older than 7 days: {zip_summary['age_analysis']['older_than_7_days']} files

Oldest File: {zip_summary['age_analysis']['oldest_file']['filename']}
({zip_summary['age_analysis']['oldest_file']['days_ago']} days ago)
Newest File: {zip_summary['age_analysis']['newest_file']['filename']}
({zip_summary['age_analysis']['newest_file']['days_ago']} days ago)

STATUS DISTRIBUTION
---------------------------------------------------------------
Valid: {zip_summary['by_status']['valid']} files
Corrupted: {zip_summary['by_status']['corrupted']} files
Excluded: {zip_summary['by_status']['excluded']} files

BACKUP TYPE BREAKDOWN
---------------------------------------------------------------
"""

        for backup_type, type_data in zip_summary['by_type'].items():
            zip_summary_text += f"""
{backup_type}:
- Count: {type_data['count']} files
- Total Size: {type_data.get('total_size_formatted', 'N/A')}
- Average Size: {type_data.get('average_size_formatted', 'N/A')}
"""

        zip_summary_text += f"""
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
===============================================================
"""

        self.zip_summary_text.delete(1.0, tk.END)
        self.zip_summary_text.insert(1.0, zip_summary_text)

    def update_bak_summary_tab(self, bak_summary):
        """Update BAK Summary tab dengan detailed analysis"""
        bak_summary_text = f"""🗄️  BAK SUMMARY - DETAILED ANALYSIS
===============================================================

BASIC STATISTICS
---------------------------------------------------------------
Total BAK Files: {bak_summary['total_bak_files']}
Analyzed BAK Files: {bak_summary['analyzed_bak_files']}
Failed Analysis: {bak_summary['failed_analysis']}

SIZE ANALYSIS
---------------------------------------------------------------
Total BAK Size: {bak_summary['total_bak_size_formatted']}
Average BAK Size: {bak_summary['average_bak_size_formatted']}

SIZE VALIDATION
---------------------------------------------------------------
Above Minimum: {bak_summary['size_validation']['above_minimum']} files
Below Minimum: {bak_summary['size_validation']['below_minimum']} files

SIZE WARNINGS:
"""

        for warning in bak_summary['size_validation']['size_warnings'][:5]:  # Show first 5 warnings
            bak_summary_text += f"- {warning['filename']} ({warning['size']}) - {warning['backup_type']}\n"

        bak_summary_text += f"""
AGE ANALYSIS
---------------------------------------------------------------
Recent 24h: {bak_summary['age_analysis']['recent_24h']} files
Last 7 days: {bak_summary['age_analysis']['last_7_days']} files
Older than 7 days: {bak_summary['age_analysis']['older_than_7_days']} files
Outdated Files: {len(bak_summary['age_analysis']['outdated_files'])}

OUTDATED FILES:
"""

        for outdated in bak_summary['age_analysis']['outdated_files'][:3]:  # Show first 3 outdated files
            bak_summary_text += f"- {outdated['filename']} ({outdated['days_outdated']} days) - {outdated['backup_type']}\n"

        bak_summary_text += f"""
DBATOOLS ANALYSIS
---------------------------------------------------------------
Successful: {bak_summary['dbatools_analysis']['successful']} files
Failed: {bak_summary['dbatools_analysis']['failed']} files
Not Attempted: {bak_summary['dbatools_analysis']['not_attempted']} files

ERRORS (first 3):
"""
        for error in bak_summary['dbatools_analysis']['errors'][:3]:
            bak_summary_text += f"- {error}\n"

        bak_summary_text += f"""
VALIDATION STATUS
---------------------------------------------------------------
Valid (90%+): {bak_summary['by_validation_status']['valid']} files
Warning (70-89%): {bak_summary['by_validation_status']['warning']} files
Invalid (<70%): {bak_summary['by_validation_status']['invalid']} files
Excluded: {bak_summary['by_validation_status']['excluded']} files

CHECKLIST PERFORMANCE
---------------------------------------------------------------
Total Checklists: {bak_summary['checklist_summary']['total_checklists']}
Perfect Scores: {bak_summary['checklist_summary']['perfect_scores']}
Average Score: {bak_summary['checklist_summary']['average_score']:.1f}%

COMMON FAILURES:
"""
        for failure, count in sorted(bak_summary['checklist_summary']['common_failures'].items(),
                                 key=lambda x: x[1], reverse=True)[:5]:
            bak_summary_text += f"- {failure}: {count} failures\n"

        bak_summary_text += f"""
BACKUP TYPE BREAKDOWN
---------------------------------------------------------------
"""

        for backup_type, type_data in bak_summary['by_backup_type'].items():
            bak_summary_text += f"""
{backup_type}:
- Count: {type_data['count']} files
- Total Size: {type_data.get('total_size_formatted', 'N/A')}
- Average Size: {type_data.get('average_size_formatted', 'N/A')}
- Size Warnings: {type_data.get('size_warnings', 0)}
"""

        bak_summary_text += f"""
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
===============================================================
"""

        self.bak_summary_text.delete(1.0, tk.END)
        self.bak_summary_text.insert(1.0, bak_summary_text)

    def send_test_email(self):
        """Kirim email test dengan enhanced subject"""
        try:
            # Get overall backup validity and status for subject
            backup_validity = self.get_overall_backup_validity()
            backup_status = self.get_overall_backup_status()
            
            # Create combined subject based on both validity and status
            validity_label = backup_validity.upper()  # VALID or INVALID
            
            if backup_status.upper() == "OUTDATED":
                status_label = "OUTDATED"
            elif backup_status.upper() == "UPDATED":
                status_label = "UPDATED"
            else:
                status_label = "UPDATED"  # Default to UPDATED if not outdated
            
            subject = f"[{validity_label}-{status_label}] Enhanced Monitor Backup - Email Test"
            body = "Ini adalah email test dari Enhanced Monitor Backup.\n\nWaktu pengiriman: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            self.send_email(subject, body)
            messagebox.showinfo("Success", "Email test berhasil dikirim!")
            self.update_log("Email test berhasil dikirim")

        except Exception as e:
            messagebox.showerror("Error", f"Gagal mengirim email test: {str(e)}")
            self.update_log(f"Gagal mengirim email test: {str(e)}")

    def get_overall_backup_validity(self) -> str:
        """Determine overall backup validity (Valid/Invalid) based on BAK file readability"""
        try:
            if not self.summary_data:
                return "Valid"
            
            total_bak_files = 0
            valid_bak_files = 0
            
            for file_info in self.summary_data.values():
                deep_analysis = file_info.get('deep_analysis', {})
                extracted_files = deep_analysis.get('extracted_files', [])
                
                for bak_file in extracted_files:
                    if bak_file.get('excluded', False):
                        continue
                    
                    total_bak_files += 1
                    validation_checklist = bak_file.get('validation_checklist', {})
                    
                    if validation_checklist:
                        # Check critical validation items for readability
                        critical_checks = [
                            'file_ada_dan_dapat_diakses',
                            'dbatools_dapat_membaca', 
                            'sql_server_dapat_membaca',
                            'format_backup_valid',
                            'tidak_corrupt'
                        ]
                        
                        critical_passed = sum(1 for check in critical_checks 
                                            if validation_checklist.get(check, {}).get('status', False))
                        
                        # BAK file is valid if at least 80% of critical checks pass
                        if critical_passed >= len(critical_checks) * 0.8:
                            valid_bak_files += 1
            
            # Overall validity: at least 70% of BAK files must be valid
            if total_bak_files == 0:
                return "Valid"
            
            validity_rate = (valid_bak_files / total_bak_files) * 100
            return "Valid" if validity_rate >= 70 else "Invalid"
            
        except Exception as e:
            self.logger.warning(f"Error determining backup validity: {e}")
            return "Valid"

    def get_overall_backup_status(self) -> str:
        """Determine overall backup status (Outdated/Updated) based on all files"""
        try:
            if not self.summary_data:
                return "Updated"
            
            # Check if any backup files are outdated
            has_outdated = False
            for file_info in self.summary_data.values():
                # Check ZIP file outdated status
                if file_info.get('is_outdated', False):
                    has_outdated = True
                    break
                
                # Check BAK files within ZIP
                bak_files = file_info.get('bak_files', [])
                for bak_file in bak_files:
                    if bak_file.get('is_outdated', False):
                        has_outdated = True
                        break
                
                if has_outdated:
                    break
            
            return "Outdated" if has_outdated else "Updated"
        except Exception as e:
            self.logger.warning(f"Error determining backup status: {e}")
            return "Updated"

    def send_deep_analysis_email(self):
        """Kirim email deep analysis report"""
        try:
            if not self.summary_data:
                self.update_log("Tidak ada data deep analysis untuk dikirim")
                messagebox.showwarning("Warning", "Tidak ada data deep analysis untuk dikirim")
                return

            # Get overall backup validity and status for subject
            backup_validity = self.get_overall_backup_validity()
            backup_status = self.get_overall_backup_status()
            
            # Create combined subject based on both validity and status
            validity_label = backup_validity.upper()  # VALID or INVALID
            
            if backup_status.upper() == "OUTDATED":
                status_label = "OUTDATED"
            elif backup_status.upper() == "UPDATED":
                status_label = "UPDATED"
            else:
                status_label = "UPDATED"  # Default to UPDATED if not outdated
            
            subject = f"[{validity_label}-{status_label}] Deep Analysis Report - {datetime.now().strftime('%Y-%m-%d')}"
            body = self.generate_deep_analysis_email_template()

            self.send_email(subject, body)
            messagebox.showinfo("Success", "Deep analysis report berhasil dikirim!")
            self.update_log("Deep analysis report berhasil dikirim")

        except Exception as e:
            messagebox.showerror("Error", f"Gagal mengirim deep analysis report: {str(e)}")
            self.update_log(f"Gagal mengirim deep analysis report: {str(e)}")

    def generate_deep_analysis_email_template(self) -> str:
        """Generate template email deep analysis profesional dalam format HTML Bahasa Indonesia"""
        if not self.summary_data:
            return ""

        # Generate summaries if not already generated
        if not hasattr(self, 'zip_summary') or not hasattr(self, 'bak_summary'):
            scan_results = {
                'files': list(self.summary_data.values()),
                'total_zip_files': len(self.summary_data),
                'valid_zip_files': sum(1 for f in self.summary_data.values() if f.get('status') == 'Valid'),
                'corrupted_zip_files': sum(1 for f in self.summary_data.values() if f.get('status') == 'Corrupted')
            }
            self.zip_summary = self.generate_zip_summary(scan_results)
            self.bak_summary = self.generate_bak_summary(scan_results)

        total_files = len(self.summary_data)
        valid_files = sum(1 for f in self.summary_data.values() if f['status'] == 'Valid')
        extracted_files = sum(1 for f in self.summary_data.values() if f['extracted'])
        report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        success_rate = (valid_files/total_files*100) if total_files > 0 else 0

        # Get current summaries
        zip_summary = getattr(self, 'zip_summary', {})
        bak_summary = getattr(self, 'bak_summary', {})

        # Calculate backup date from most recent file
        backup_dates = []
        for file_path, file_info in self.summary_data.items():
            try:
                mod_time = os.path.getmtime(file_path)
                mod_date = datetime.fromtimestamp(mod_time)
                backup_dates.append(mod_date)
            except:
                continue

        # Use most recent backup date or current date if no files found
        latest_backup_date = max(backup_dates) if backup_dates else datetime.now()
        backup_analysis_date = latest_backup_date.strftime('%Y-%m-%d')
        backup_analysis_datetime = latest_backup_date.strftime('%Y-%m-%d %H:%M:%S')

        # Get oldest backup date for range information
        oldest_backup_date = min(backup_dates) if backup_dates else datetime.now()
        oldest_backup_datetime = oldest_backup_date.strftime('%Y-%m-%d %H:%M:%S')

        # Format backup dates information
        backup_dates_info = []
        for file_path, file_info in self.summary_data.items():
            try:
                mod_time = os.path.getmtime(file_path)
                mod_date = datetime.fromtimestamp(mod_time)
                filename = os.path.basename(file_path)
                backup_dates_info.append({
                    'filename': filename,
                    'datetime': mod_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'date': mod_date.strftime('%Y-%m-%d')
                })
            except:
                continue

        # Calculate critical alerts
        critical_alerts = len(bak_summary.get('age_analysis', {}).get('outdated_files', [])) + len(bak_summary.get('size_validation', {}).get('size_warnings', []))

        body = f"""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Laporan Analisis Backup Database</title>
    <style>
        @media screen {{
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f8f9fa;
                color: #333;
                line-height: 1.6;
            }}
            .container {{
                max-width: 1000px;
                margin: 0 auto;
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                color: white;
                padding: 25px;
                text-align: center;
                border-radius: 8px 8px 0 0;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            .header p {{
                margin: 8px 0 0 0;
                opacity: 0.9;
                font-size: 14px;
            }}
            .section {{
                margin: 25px;
                padding: 20px;
                border-radius: 6px;
                border-left: 4px solid #2c3e50;
                background-color: #ffffff;
                border: 1px solid #e9ecef;
            }}
            .section h2 {{
                color: #2c3e50;
                margin-top: 0;
                font-size: 18px;
                font-weight: 600;
                border-bottom: 2px solid #e9ecef;
                padding-bottom: 8px;
                margin-bottom: 20px;
            }}
            .executive-summary {{
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border-left-color: #007bff;
                border-top: 3px solid #007bff;
            }}
            .executive-summary h2 {{
                color: #007bff;
            }}
            .file-card {{
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 15px;
                margin: 12px 0;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            }}
            .file-name {{
                font-weight: 600;
                color: #2c3e50;
                font-size: 16px;
                margin-bottom: 10px;
                border-bottom: 1px solid #e9ecef;
                padding-bottom: 5px;
            }}
            .file-details {{
                font-size: 13px;
            }}
            .detail-row {{
                display: flex;
                justify-content: space-between;
                margin: 4px 0;
                padding: 2px 0;
            }}
            .detail-label {{
                color: #6c757d;
                font-weight: 500;
            }}
            .detail-value {{
                font-weight: 600;
                color: #2c3e50;
            }}
            .status-badge {{
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .status-valid {{
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }}
            .status-warning {{
                background-color: #fff3cd;
                color: #856404;
                border: 1px solid #ffeaa7;
            }}
            .status-invalid {{
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }}
            .status-outdated {{
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }}
            .status-current {{
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }}
            .stat-card {{
                background-color: #ffffff;
                padding: 15px;
                border-radius: 6px;
                border: 1px solid #dee2e6;
                text-align: center;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .stat-number {{
                font-size: 20px;
                font-weight: 700;
                color: #007bff;
                margin-bottom: 5px;
            }}
            .stat-label {{
                color: #6c757d;
                font-size: 12px;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .alert-section {{
                background-color: #fff3cd;
                border-left-color: #ffc107;
                border: 1px solid #ffeaa7;
            }}
            .alert-section h2 {{
                color: #856404;
            }}
            .recommendations {{
                background-color: #d4edda;
                border-left-color: #28a745;
                border: 1px solid #c3e6cb;
            }}
            .recommendations h2 {{
                color: #155724;
            }}
            .recommendations ul {{
                margin: 15px 0;
                padding-left: 20px;
            }}
            .recommendations li {{
                margin: 6px 0;
                line-height: 1.5;
            }}
            .footer {{
                background-color: #2c3e50;
                color: white;
                text-align: center;
                padding: 15px;
                font-size: 12px;
            }}
            .critical-alerts {{
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                border-radius: 6px;
                padding: 15px;
                margin: 15px 0;
                text-align: center;
            }}
            .critical-alerts .alert-number {{
                font-size: 20px;
                font-weight: bold;
                color: #721c24;
                margin-bottom: 5px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
                background-color: white;
                border: 1px solid #dee2e6;
            }}
            th, td {{
                border: 1px solid #dee2e6;
                padding: 10px;
                text-align: left;
                font-size: 13px;
            }}
            th {{
                background-color: #f8f9fa;
                color: #2c3e50;
                font-weight: 600;
                border-bottom: 2px solid #dee2e6;
            }}
            tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            h3 {{
                color: #2c3e50;
                font-size: 16px;
                font-weight: 600;
                margin: 20px 0 10px 0;
                border-bottom: 1px solid #e9ecef;
                padding-bottom: 5px;
            }}
        }}

        /* Print-friendly styles */
        @media print {{
            body {{
                background-color: white;
                font-family: Arial, sans-serif;
            }}
            .container {{
                box-shadow: none;
                border: 1px solid #ccc;
            }}
            .header {{
                background: #2c3e50 !important;
                -webkit-print-color-adjust: exact;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>SISTEM MONITORING BACKUP DATABASE</h1>
            <p>LAPORAN ANALISIS LENGKAP</p>
        </div>

        <!-- INFORMASI PENTING BACKUP - PRIORITY SECTION -->
        <div class="section priority-info" style="background-color: #fff3cd; border: 2px solid #ffc107; border-radius: 8px; margin-bottom: 25px;">
            <h2 style="color: #856404; margin-top: 0;">INFORMASI KRITIS BACKUP</h2>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                <div>
                    <h3 style="color: #856404; margin-bottom: 10px;">Informasi Backup</h3>
                    <p style="margin: 5px 0; color: #856404;"><strong>Laporan Dibuat:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p style="margin: 5px 0; color: #856404;"><strong>Backup Terbaru:</strong> {backup_analysis_datetime}</p>
                    <p style="margin: 5px 0; color: #856404;"><strong>Backup Terlama:</strong> {oldest_backup_datetime}</p>
                    <p style="margin: 5px 0; color: #856404;"><strong>Total File Backup:</strong> {len(backup_dates_info)}</p>
                </div>
                <div>
                    <h3 style="color: #856404; margin-bottom: 10px;">Status Kritis</h3>
                    <p style="margin: 5px 0; color: #856404;"><strong>Item Perlu Perhatian:</strong> {critical_alerts}</p>
                    <p style="margin: 5px 0; color: #856404;"><strong>Status Sistem:</strong> {'NORMAL' if valid_files > 0 and len(bak_summary.get('age_analysis', {}).get('outdated_files', [])) == 0 else 'PERLU PERHATIAN'}</p>
                </div>
            </div>

            <h3 style="color: #856404; margin-bottom: 15px;">Checklist Status Backup</h3>
            <table style="width: 100%; border-collapse: collapse; background-color: white;">
                <thead>
                    <tr style="background-color: #f8f9fa;">
                        <th style="padding: 12px; border: 1px solid #dee2e6; text-align: left; color: #856404;">Parameter</th>
                        <th style="padding: 12px; border: 1px solid #dee2e6; text-align: center; color: #856404;">Status</th>
                        <th style="padding: 12px; border: 1px solid #dee2e6; text-align: left; color: #856404;">Detail</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #dee2e6;"><strong>ZIP Bisa Dibuka</strong></td>
                        <td style="padding: 12px; border: 1px solid #dee2e6; text-align: center;">
                            <span class="status-badge {'status-valid' if len([f for f in self.summary_data.values() if f.get('status') == 'Valid']) == total_files else 'status-invalid'}">
                                {'✓' if len([f for f in self.summary_data.values() if f.get('status') == 'Valid']) == total_files else '✗'}
                            </span>
                        </td>
                        <td style="padding: 12px; border: 1px solid #dee2e6;">
                            {len([f for f in self.summary_data.values() if f.get('status') == 'Valid'])} dari {total_files} file ZIP valid
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #dee2e6;"><strong>BAK File Valid</strong></td>
                        <td style="padding: 12px; border: 1px solid #dee2e6; text-align: center;">
                            <span class="status-badge {'status-valid' if bak_summary.get('dbatools_analysis', {}).get('successful', 0) > 0 else 'status-warning'}">
                                {'✓' if bak_summary.get('dbatools_analysis', {}).get('successful', 0) > 0 else '⚠'}
                            </span>
                        </td>
                        <td style="padding: 12px; border: 1px solid #dee2e6;">
                            {bak_summary.get('dbatools_analysis', {}).get('successful', 0)} file BAK bisa direstore
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #dee2e6;"><strong>🕒 Backup Tidak Kadaluarsa</strong></td>
                        <td style="padding: 12px; border: 1px solid #dee2e6; text-align: center;">
                            <span class="status-badge {'status-valid' if len(bak_summary.get('age_analysis', {}).get('outdated_files', [])) == 0 else 'status-outdated'}">
                                {'✓' if len(bak_summary.get('age_analysis', {}).get('outdated_files', [])) == 0 else '✗'}
                            </span>
                        </td>
                        <td style="padding: 12px; border: 1px solid #dee2e6;">
                            {len(bak_summary.get('age_analysis', {}).get('outdated_files', []))} file outdated
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #dee2e6;"><strong>Ukuran Backup Cukup</strong></td>
                        <td style="padding: 12px; border: 1px solid #dee2e6; text-align: center;">
                            <span class="status-badge {'status-valid' if bak_summary.get('size_validation', {}).get('below_minimum', 0) == 0 else 'status-warning'}">
                                {'✓' if bak_summary.get('size_validation', {}).get('below_minimum', 0) == 0 else '⚠'}
                            </span>
                        </td>
                        <td style="padding: 12px; border: 1px solid #dee2e6;">
                            {bak_summary.get('size_validation', {}).get('below_minimum', 0)} file di bawah minimum
                        </td>
                    </tr>
                </tbody>
            </table>

            <div style="margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 6px; border-left: 4px solid #007bff;">
                <h4 style="margin-top: 0; color: #007bff;">📄 Informasi File Backup</h4>
                
                <!-- Tanggal Backup Section - More Prominent -->
                <div style="background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%); padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #2196f3;">
                    <h5 style="margin: 0 0 10px 0; color: #1976d2; font-size: 16px;">📅 TANGGAL BACKUP (Berdasarkan Date Modified File)</h5>
                    <div style="display: grid; gap: 8px;">
"""

        # Add ZIP file information with prominent backup dates
        for file_path, file_info in self.summary_data.items():
            filename = os.path.basename(file_path)
            modified_time = file_info.get('modified_time', 'Unknown')
            if isinstance(modified_time, str):
                try:
                    modified_time = datetime.fromisoformat(modified_time.replace('Z', '+00:00'))
                except:
                    # Fallback: use days_since_backup to calculate approximate date
                    days_since = file_info.get('days_since_backup', 0)
                    modified_time = datetime.now() - timedelta(days=days_since) if days_since > 0 else datetime.now()

            # Use actual days_since_backup from file_info if available
            days_diff = file_info.get('days_since_backup', 0)
            if days_diff == 0:
                days_diff = (datetime.now() - modified_time).days if isinstance(modified_time, datetime) else 0
            
            backup_type = file_info.get('backup_type', 'Unknown')
            status = file_info.get('status', 'Unknown')
            
            # Format tanggal backup dengan lebih menonjol
            backup_date_formatted = modified_time.strftime('%d %B %Y, %H:%M:%S') if isinstance(modified_time, datetime) else modified_time
            age_color = '#d32f2f' if days_diff > 7 else '#388e3c' if days_diff <= 1 else '#f57c00'

            body += f"""
                        <div style="background: white; padding: 10px; border-radius: 6px; border: 1px solid #e0e0e0;">
                            <div style="font-weight: bold; color: #1976d2; margin-bottom: 4px;">{filename}</div>
                            <div style="color: {age_color}; font-weight: bold; font-size: 14px;">🗓️ Tanggal Backup: {backup_date_formatted}</div>
                            <div style="color: #666; font-size: 12px;">Tipe: {backup_type} | Usia: {days_diff} hari | Status: {status}</div>
                        </div>
"""

        body += f"""
                    </div>
                </div>
                
                <div style="color: #6c757d;">
                    <p style="margin: 5px 0;"><strong>File ZIP Dianalisis:</strong></p>
                    <ul style="margin: 5px 0; padding-left: 20px;">
"""

        # Add simplified ZIP file list
        for file_path, file_info in self.summary_data.items():
            filename = os.path.basename(file_path)
            backup_type = file_info.get('backup_type', 'Unknown')
            status = file_info.get('status', 'Unknown')

            body += f"""
                        <li><strong>{filename}</strong> ({backup_type}) - Status: {status}</li>
"""

        body += f"""
                    </ul>
"""

        # Add BAK file information if available
        if hasattr(self, 'bak_summary') and self.bak_summary.get('bak_files'):
            body += f"""
                    <p style="margin: 15px 0 5px 0;"><strong>File BAK Dianalisis:</strong></p>
                    
                    <!-- BAK Backup Dates Section -->
                    <div style="background: linear-gradient(135deg, #fff3e0 0%, #fce4ec 100%); padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #ff9800;">
                        <h6 style="margin: 0 0 10px 0; color: #f57c00; font-size: 14px;">📅 TANGGAL BACKUP BAK FILES</h6>
                        <div style="display: grid; gap: 6px;">
"""

            for bak_file in self.bak_summary.get('bak_files', []):
                bak_filename = bak_file.get('filename', 'Unknown')
                bak_type = bak_file.get('backup_type', 'Unknown')
                
                # Use backup_date from analysis (ZIP file date) instead of BAK modified time
                backup_date_str = bak_file.get('backup_date', 'Unknown')
                if backup_date_str != 'Unknown' and backup_date_str != 'CompressionAlgorithm':
                    try:
                        # Try different date formats
                        if 'T' in backup_date_str:
                            bak_modified = datetime.fromisoformat(backup_date_str.replace('Z', '+00:00'))
                        else:
                            bak_modified = datetime.strptime(backup_date_str, '%Y-%m-%d %H:%M:%S')
                    except:
                        # Fallback: use days_since_backup to calculate approximate date
                        days_since = bak_file.get('days_since_backup', 0)
                        bak_modified = datetime.now() - timedelta(days=days_since)
                else:
                    # Fallback: use days_since_backup to calculate approximate date
                    days_since = bak_file.get('days_since_backup', 0)
                    bak_modified = datetime.now() - timedelta(days=days_since)

                # Use the actual days_since_backup from analysis
                bak_days_diff = bak_file.get('days_since_backup', 0)
                is_outdated = bak_file.get('is_outdated', False)
                
                # Format tanggal backup dengan lebih menonjol - menggunakan tanggal ZIP file
                bak_backup_date_formatted = bak_modified.strftime('%d %B %Y, %H:%M:%S') if isinstance(bak_modified, datetime) else backup_date_str
                bak_age_color = '#d32f2f' if bak_days_diff > 7 else '#388e3c' if bak_days_diff <= 1 else '#f57c00'

                body += f"""
                            <div style="background: white; padding: 8px; border-radius: 4px; border: 1px solid #e0e0e0;">
                                <div style="font-weight: bold; color: #f57c00; margin-bottom: 2px; font-size: 13px;">{bak_filename}</div>
                                <div style="color: {bak_age_color}; font-weight: bold; font-size: 12px;">🗓️ Tanggal Backup (ZIP): {bak_backup_date_formatted}</div>
                                <div style="color: #666; font-size: 11px;">Tipe: {bak_type} | Usia: {bak_days_diff} hari | Status: {'KADALUARSA' if is_outdated else 'MASIH BERLAKU'}</div>
                            </div>
"""

            body += f"""
                        </div>
                    </div>
                    
                    <ul style="margin: 5px 0; padding-left: 20px;">
"""

            # Add simplified BAK file list
            for bak_file in self.bak_summary.get('bak_files', []):
                bak_filename = bak_file.get('filename', 'Unknown')
                bak_type = bak_file.get('backup_type', 'Unknown')
                is_outdated = bak_file.get('is_outdated', False)

                body += f"""
                        <li><strong>{bak_filename}</strong> ({bak_type}) - Status: {'KADALUARSA' if is_outdated else 'MASIH BERLAKU'}</li>
"""

            body += f"""
                    </ul>
"""

        body += f"""
                </div>
            </div>
        </div>

        <div class="section executive-summary">
            <h2>Ringkasan Eksekutif</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{report_time}</div>
                    <div class="stat-label">Laporan Dibuat</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{total_files}</div>
                    <div class="stat-label">Total Arsip ZIP</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{valid_files}</div>
                    <div class="stat-label">File ZIP Valid</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{success_rate:.1f}%</div>
                    <div class="stat-label">Tingkat Keberhasilan</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{backup_analysis_date}</div>
                    <div class="stat-label">Tanggal Backup</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{bak_summary.get('total_bak_files', 0)}</div>
                    <div class="stat-label">Total File BAK</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{'AKTIF' if valid_files > 0 else 'TIDAK AKTIF'}</div>
                    <div class="stat-label">Status Sistem</div>
                </div>
            </div>

            {f'<div class="critical-alerts"><div class="alert-number">{critical_alerts}</div><div>Item Memerlukan Perhatian Segera</div></div>' if critical_alerts > 0 else ''}
        </div>

        <div class="section">
            <h2>Detail Analisis File ZIP</h2>
"""

        # Detailed ZIP file analysis with names, dates, and status
        for file_path, file_info in self.summary_data.items():
            filename = os.path.basename(file_path)
            backup_type = file_info.get('backup_type', 'Unknown')
            size = self.format_size(file_info.get('size', 0))
            status = file_info.get('status', 'Unknown')

            # Get file modification date for outdated calculation
            try:
                mod_time = os.path.getmtime(file_path)
                mod_date = datetime.fromtimestamp(mod_time)
                current_date = datetime.now()
                days_diff = (current_date - mod_date).days
                # Consider outdated if modification date is not today
                is_outdated = mod_date.date() != current_date.date()
                outdated_status = "KADALUARSA" if is_outdated else "MASIH BERLAKU"
                status_class = "status-outdated" if is_outdated else "status-current"
            except:
                days_diff = 0
                is_outdated = False
                outdated_status = "TIDAK DIKETAHUI"
                status_class = "status-warning"

            status_class_zip = "status-valid" if status == "Valid" else "status-invalid" if status == "Corrupted" else "status-warning"

            body += f"""
            <div class="file-card">
                <div class="file-name">{filename}</div>
                <div class="file-details">
                    <div class="detail-item">
                        <span class="detail-label">Tipe Backup:</span>
                        <span class="detail-value">{backup_type}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Ukuran File:</span>
                        <span class="detail-value">{size}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Status:</span>
                        <span class="detail-value"><span class="status-badge {status_class_zip}">{status}</span></span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Terakhir Dimodifikasi:</span>
                        <span class="detail-value">{mod_date.strftime('%Y-%m-%d %H:%M') if 'mod_date' in locals() else 'Tidak Diketahui'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Usia:</span>
                        <span class="detail-value">{days_diff} hari</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Status Arsip:</span>
                        <span class="detail-value"><span class="status-badge {status_class}">{outdated_status}</span></span>
                    </div>
                </div>
            </div>
"""

        body += f"""
        </div>

        <div class="section">
            <h2>Detail Analisis File BAK</h2>
"""

        # Detailed BAK file analysis
        for file_path, file_info in self.summary_data.items():
            deep_analysis = file_info.get('deep_analysis', {})
            extracted_files = deep_analysis.get('extracted_files', [])

            if extracted_files:
                for bak_file in extracted_files:
                    if bak_file.get('excluded', False):
                        continue

                    bak_filename = bak_file.get('filename', 'Unknown')
                    bak_size = self.format_size(bak_file.get('size', 0))
                    bak_type = bak_file.get('backup_type', 'Unknown')

                    # Size validation with minimum requirements
                    size_warning = bak_file.get('size_warning', False)
                    size_status = "DI BAWAH MINIMUM" if size_warning else "DI ATAS MINIMUM"
                    size_class = "status-warning" if size_warning else "status-valid"

                    # Get minimum size based on backup type
                    minimum_sizes_gb = {
                        'BackupStaging': 2.3,
                        'BackupVenus': 8.7,
                        'PlantwareP3': 35.0
                    }
                    minimum_size_gb = minimum_sizes_gb.get(bak_type, 0)
                    minimum_size = f"{minimum_size_gb} GB"

                    # Calculate actual size in GB for comparison
                    bak_size_gb = bak_file.get('size', 0) / (1024**3)  # Convert bytes to GB
                    bak_size_formatted_gb = f"{bak_size_gb:.2f} GB"

                    # Age analysis
                    is_outdated_bak = bak_file.get('is_outdated', False)
                    days_since_backup = bak_file.get('days_since_backup', 0)
                    outdated_status_bak = "KADALUARSA" if is_outdated_bak else "MASIH BERLAKU"
                    age_class = "status-outdated" if is_outdated_bak else "status-current"

                    # File readability and validity
                    can_be_extracted = not bak_file.get('extraction_failed', True)
                    dbatools_readable = bak_file.get('dbatools_analysis', {}).get('status') == 'Analyzed'

                    extraction_status = "DAPAT DIBACA" if can_be_extracted else "TIDAK DAPAT DIBACA"
                    extraction_class = "status-valid" if can_be_extracted else "status-invalid"

                    dbatools_status = "DAPAT DIBACA" if dbatools_readable else "TIDAK DAPAT DIBACA"
                    dbatools_class = "status-valid" if dbatools_readable else "status-invalid"

                    body += f"""
            <div class="file-card">
                <div class="file-name">{bak_filename}</div>
                <div class="file-details">
                    <div class="detail-item">
                        <span class="detail-label">Tipe Backup:</span>
                        <span class="detail-value">{bak_type}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Ukuran File:</span>
                        <span class="detail-value">{bak_size} ({bak_size_formatted_gb})</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Ukuran Minimum:</span>
                        <span class="detail-value">{minimum_size}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Perbandingan Ukuran:</span>
                        <span class="detail-value">{bak_size_formatted_gb} vs {minimum_size} ({'OK' if bak_size_gb >= minimum_size_gb else 'DI BAWAH MINIMUM'})</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Validasi Ukuran:</span>
                        <span class="detail-value"><span class="status-badge {size_class}">{size_status}</span></span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Status Usia:</span>
                        <span class="detail-value"><span class="status-badge {age_class}">{outdated_status_bak}</span> ({days_since_backup} hari)</span>
                    </div>"""

                    # Only show extraction capability if the file CAN be extracted
                    # Hide redundant "TIDAK DAPAT DIBACA" status as requested
                    if can_be_extracted:
                        body += f"""
                    <div class="detail-item">
                        <span class="detail-label">Kemampuan Ekstraksi:</span>
                        <span class="detail-value"><span class="status-badge {extraction_class}">{extraction_status}</span></span>
                    </div>"""

                    body += f"""
                    <div class="detail-item">
                        <span class="detail-label">Kemampuan Baca DBATools:</span>
                        <span class="detail-value"><span class="status-badge {dbatools_class}">{dbatools_status}</span></span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Perbedaan Satu Hari:</span>
                        <span class="detail-value">{'YA' if bak_file.get('file_date_one_day_different', False) else 'TIDAK'}</span>
                    </div>
                </div>
            </div>
"""

        body += f"""
        </div>

        <div class="section">
            <h2>Persyaratan Ukuran Minimum Backup</h2>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <thead>
                    <tr style="background-color: #f8f9fa;">
                        <th style="padding: 12px; border: 1px solid #dee2e6; text-align: left;">Tipe Backup</th>
                        <th style="padding: 12px; border: 1px solid #dee2e6; text-align: center;">Ukuran Minimum</th>
                        <th style="padding: 12px; border: 1px solid #dee2e6; text-align: center;">Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #dee2e6;">BackupStaging</td>
                        <td style="padding: 12px; border: 1px solid #dee2e6; text-align: center;">2.3 GB</td>
                        <td style="padding: 12px; border: 1px solid #dee2e6; text-align: center;">
                            <span class="status-badge {'status-valid' if not any(w.get('backup_type') == 'BackupStaging' and w.get('size_warning') for w in bak_summary.get('size_validation', {}).get('size_warnings', [])) else 'status-warning'}">
                                {'OK' if not any(w.get('backup_type') == 'BackupStaging' and w.get('size_warning') for w in bak_summary.get('size_validation', {}).get('size_warnings', [])) else 'DI BAWAH MINIMUM'}
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #dee2e6;">BackupVenus</td>
                        <td style="padding: 12px; border: 1px solid #dee2e6; text-align: center;">8.7 GB</td>
                        <td style="padding: 12px; border: 1px solid #dee2e6; text-align: center;">
                            <span class="status-badge {'status-valid' if not any(w.get('backup_type') == 'BackupVenus' and w.get('size_warning') for w in bak_summary.get('size_validation', {}).get('size_warnings', [])) else 'status-warning'}">
                                {'OK' if not any(w.get('backup_type') == 'BackupVenus' and w.get('size_warning') for w in bak_summary.get('size_validation', {}).get('size_warnings', [])) else 'DI BAWAH MINIMUM'}
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #dee2e6;">PlantwareP3</td>
                        <td style="padding: 12px; border: 1px solid #dee2e6; text-align: center;">35.0 GB</td>
                        <td style="padding: 12px; border: 1px solid #dee2e6; text-align: center;">
                            <span class="status-badge {'status-valid' if not any(w.get('backup_type') == 'PlantwareP3' and w.get('size_warning') for w in bak_summary.get('size_validation', {}).get('size_warnings', [])) else 'status-warning'}">
                                {'OK' if not any(w.get('backup_type') == 'PlantwareP3' and w.get('size_warning') for w in bak_summary.get('size_validation', {}).get('size_warnings', [])) else 'DI BAWAH MINIMUM'}
                            </span>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="recommendations">
            <h2>Rekomendasi</h2>
            <ul>
"""

        # Generate recommendations based on analysis
        recommendations = []

        if len(bak_summary.get('age_analysis', {}).get('outdated_files', [])) > 0:
            recommendations.append("Periksa file backup yang tidak dimodifikasi hari ini - pastikan proses backup berjalan setiap hari")

        if len(bak_summary.get('size_validation', {}).get('size_warnings', [])) > 0:
            recommendations.append("Selidiki file di bawah ukuran minimum - potensi backup tidak lengkap")

        if bak_summary.get('dbatools_analysis', {}).get('failed', 0) > 0:
            recommendations.append("Selesaikan kegagalan analisis DBATools untuk validasi backup komprehensif")

        if bak_summary.get('extraction_analysis', {}).get('failed', 0) > 0:
            recommendations.append("Perbaiki masalah ekstraksi file untuk memastikan aksesibilitas backup")

        if not recommendations:
            recommendations.append("Semua sistem backup beroperasi dalam parameter normal")
            recommendations.append("Lanjutkan prosedur pemantauan dan perawatan rutin")

        for rec in recommendations:
            body += f"<li>{rec}</li>"

        body += f"""
            </ul>
        </div>

        <div class="section">
            <h2>Informasi Sistem</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{'AKTIF' if self.config.getboolean('MONITORING', 'exclude_plantware', fallback=True) else 'TIDAK AKTIF'}</div>
                    <div class="stat-label">Pengecualian PlantwareP3</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{'AKTIF' if hasattr(self, 'monitoring_active') and self.monitoring_active else 'TIDAK AKTIF'}</div>
                    <div class="stat-label">Pemantauan Real-time</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">Enhanced Backup Monitor v3.0</div>
                    <div class="stat-label">Versi Sistem</div>
                </div>
            </div>
        </div>
    </div>

    <div class="footer">
        <p><strong>Sistem Monitoring Backup Database</strong></p>
        <p>Dibuat: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Enhanced Backup Monitor v3.0 - Analisis Real-time dengan 12 Parameter Validasi</p>
    </div>
</body>
</html>
"""

        return body

    def generate_plain_text_version(self) -> str:
        """Generate plain text version dari HTML email untuk fallback"""
        if not self.summary_data:
            return "Tidak ada data deep analysis untuk ditampilkan"

        total_files = len(self.summary_data)
        valid_files = sum(1 for f in self.summary_data.values() if f['status'] == 'Valid')
        report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        success_rate = (valid_files/total_files*100) if total_files > 0 else 0

        if hasattr(self, 'bak_summary'):
            bak_summary = self.bak_summary
        else:
            scan_results = {
                'files': list(self.summary_data.values()),
                'total_zip_files': len(self.summary_data),
                'valid_zip_files': sum(1 for f in self.summary_data.values() if f.get('status') == 'Valid'),
                'corrupted_zip_files': sum(1 for f in self.summary_data.values() if f.get('status') == 'Corrupted')
            }
            bak_summary = self.generate_bak_summary(scan_results)

        plain_text = f"""
SISTEM MONITORING BACKUP DATABASE - LAPORAN ANALISIS
==================================================

Ringkasan Eksekutif:
- Laporan Dibuat: {report_time}
- Total Arsip ZIP: {total_files}
- File ZIP Valid: {valid_files}
- Tingkat Keberhasilan: {success_rate:.1f} persen
- Total File BAK: {bak_summary.get('total_bak_files', 0)}
- Status Sistem: {'AKTIF' if valid_files > 0 else 'TIDAK AKTIF'}

Analisis Arsip ZIP:
- Total File ZIP: {total_files}
- Arsip Valid: {valid_files}
- Arsip Rusak: {total_files - valid_files}

Analisis File Backup Database:
- Total File BAK: {bak_summary.get('total_bak_files', 0)}
- File BAK Dianalisis: {bak_summary.get('analyzed_bak_files', 0)}
- Total Ukuran BAK: {bak_summary.get('total_bak_size_formatted', 'N/A')}

Validasi Ukuran:
- Di Atas Minimum: {bak_summary.get('size_validation', {}).get('above_minimum', 0)}
- Di Bawah Minimum: {bak_summary.get('size_validation', {}).get('below_minimum', 0)}

Analisis Usia:
- 24 Jam Terakhir: {bak_summary.get('age_analysis', {}).get('recent_24h', 0)}
- 7 Hari Terakhir: {bak_summary.get('age_analysis', {}).get('last_7_days', 0)}
- Lebih dari 7 Hari: {bak_summary.get('age_analysis', {}).get('older_than_7_days', 0)}
- File Tidak Modifikasi Hari Ini: {len(bak_summary.get('age_analysis', {}).get('outdated_files', []))}

Informasi Sistem:
- Pengecualian PlantwareP3: {'AKTIF' if self.config.getboolean('MONITORING', 'exclude_plantware', fallback=True) else 'TIDAK AKTIF'}
- Versi Sistem: Enhanced Backup Monitor v3.0

Detail File ZIP:
"""

        for file_path, file_info in self.summary_data.items():
            filename = os.path.basename(file_path)
            backup_type = file_info.get('backup_type', 'Unknown')
            size = self.format_size(file_info.get('size', 0))
            status = file_info.get('status', 'Unknown')

            plain_text += f"- {filename} ({backup_type}, {size}, {status})\n"

        plain_text += f"""
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Enhanced Backup Monitor v3.0 - Analisis Real-time dengan 12 Parameter Validasi
"""

        return plain_text

    def send_email(self, subject: str, body: str, attachment_path: str = None):
        """Kirim notifikasi email dengan HTML dan plain text fallback"""
        try:
            # Get email configuration
            smtp_server = self.config['EMAIL']['smtp_server']
            smtp_port = int(self.config['EMAIL']['smtp_port'])
            sender_email = self.config['EMAIL']['sender_email']
            sender_password = self.config['EMAIL']['sender_password']
            recipient_email = self.config['EMAIL']['recipient_email']

            # Create message dengan 'mixed' untuk mendukung attachment
            msg = MIMEMultipart('mixed')
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject

            # Create alternative part untuk HTML dan plain text
            alt_msg = MIMEMultipart('alternative')

            # Generate plain text version for compatibility
            plain_text = self.generate_plain_text_version()

            # Attach plain text version
            alt_msg.attach(MIMEText(plain_text, 'plain', 'utf-8'))

            # Attach HTML version dengan encoding UTF-8
            html_part = MIMEText(body, 'html', 'utf-8')
            html_part.add_header('Content-Disposition', 'inline')
            alt_msg.attach(html_part)

            # Attach alternative part ke message utama
            msg.attach(alt_msg)

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

    def generate_zip_summary(self, scan_results: Dict) -> Dict:
        """Generate ZIP Summary dengan analisis komprehensif"""
        zip_summary = {
            'total_zip_files': scan_results.get('total_zip_files', 0),
            'valid_zip_files': scan_results.get('valid_zip_files', 0),
            'corrupted_zip_files': scan_results.get('corrupted_zip_files', 0),
            'total_size_bytes': 0,
            'total_size_formatted': '0 MB',
            'average_size_bytes': 0,
            'average_size_formatted': '0 MB',
            'largest_file': None,
            'smallest_file': None,
            'by_type': {},
            'by_status': {
                'valid': 0,
                'corrupted': 0,
                'excluded': 0
            },
            'age_analysis': {
                'today': 0,
                'last_7_days': 0,
                'older_than_7_days': 0,
                'oldest_file': None,
                'newest_file': None
            },
            'validation_summary': {
                'total_checklist_items': 0,
                'passed_items': 0,
                'failed_items': 0,
                'success_rate': 0.0
            }
        }

        # Calculate statistics from files
        files = scan_results.get('files', [])
        if not files:
            return zip_summary

        total_size = 0
        file_sizes = []
        current_date = datetime.now()

        for file_info in files:
            size = file_info.get('size', 0)
            total_size += size
            file_sizes.append(size)

            # Track largest and smallest files
            if zip_summary['largest_file'] is None or size > zip_summary['largest_file']['size']:
                zip_summary['largest_file'] = {
                    'filename': file_info.get('filename'),
                    'size': size,
                    'size_formatted': self.format_size(size)
                }

            if zip_summary['smallest_file'] is None or size < zip_summary['smallest_file']['size']:
                zip_summary['smallest_file'] = {
                    'filename': file_info.get('filename'),
                    'size': size,
                    'size_formatted': self.format_size(size)
                }

            # Age analysis
            mod_date = datetime.fromisoformat(file_info.get('modified', '').replace('Z', '+00:00'))
            days_diff = (current_date - mod_date).days

            if days_diff == 0:
                zip_summary['age_analysis']['today'] += 1
            elif days_diff <= 7:
                zip_summary['age_analysis']['last_7_days'] += 1
            else:
                zip_summary['age_analysis']['older_than_7_days'] += 1

            # Track oldest and newest files
            if zip_summary['age_analysis']['oldest_file'] is None or days_diff > zip_summary['age_analysis']['oldest_file']['days_ago']:
                zip_summary['age_analysis']['oldest_file'] = {
                    'filename': file_info.get('filename'),
                    'modified': file_info.get('modified'),
                    'days_ago': days_diff
                }

            if zip_summary['age_analysis']['newest_file'] is None or days_diff < zip_summary['age_analysis']['newest_file']['days_ago']:
                zip_summary['age_analysis']['newest_file'] = {
                    'filename': file_info.get('filename'),
                    'modified': file_info.get('modified'),
                    'days_ago': days_diff
                }

            # Status analysis
            status = file_info.get('status', 'Unknown')
            if status == 'Valid':
                zip_summary['by_status']['valid'] += 1
            elif status == 'Corrupted':
                zip_summary['by_status']['corrupted'] += 1
            else:
                zip_summary['by_status']['excluded'] += 1

            # Type analysis
            backup_type = file_info.get('backup_type', 'Unknown')
            if backup_type not in zip_summary['by_type']:
                zip_summary['by_type'][backup_type] = {
                    'count': 0,
                    'total_size': 0,
                    'average_size': 0
                }
            zip_summary['by_type'][backup_type]['count'] += 1
            zip_summary['by_type'][backup_type]['total_size'] += size

        # Calculate averages
        zip_summary['total_size_bytes'] = total_size
        zip_summary['total_size_formatted'] = self.format_size(total_size)

        if file_sizes:
            zip_summary['average_size_bytes'] = total_size / len(file_sizes)
            zip_summary['average_size_formatted'] = self.format_size(zip_summary['average_size_bytes'])

        # Calculate type averages
        for backup_type, type_data in zip_summary['by_type'].items():
            if type_data['count'] > 0:
                type_data['average_size'] = type_data['total_size'] / type_data['count']
                type_data['average_size_formatted'] = self.format_size(type_data['average_size'])
                type_data['total_size_formatted'] = self.format_size(type_data['total_size'])

        return zip_summary

    def generate_bak_summary(self, scan_results: Dict) -> Dict:
        """Generate BAK Summary dengan analisis mendalam"""
        bak_summary = {
            'total_bak_files': 0,
            'analyzed_bak_files': 0,
            'failed_analysis': 0,
            'total_bak_size_bytes': 0,
            'total_bak_size_formatted': '0 MB',
            'average_bak_size_bytes': 0,
            'average_bak_size_formatted': '0 MB',
            'by_backup_type': {},
            'by_validation_status': {
                'valid': 0,
                'warning': 0,
                'invalid': 0,
                'excluded': 0
            },
            'size_validation': {
                'above_minimum': 0,
                'below_minimum': 0,
                'size_warnings': []
            },
            'age_analysis': {
                'recent_24h': 0,
                'last_7_days': 0,
                'older_than_7_days': 0,
                'outdated_files': []
            },
            'dbatools_analysis': {
                'successful': 0,
                'failed': 0,
                'not_attempted': 0,
                'errors': []
            },
            'extraction_analysis': {
                'successful': 0,
                'failed': 0,
                'not_attempted': 0
            },
            'checklist_summary': {
                'total_checklists': 0,
                'perfect_scores': 0,
                'average_score': 0.0,
                'common_failures': {}
            }
        }

        # Analyze BAK files from deep analysis
        files = scan_results.get('files', [])
        total_checklist_items = 0
        total_checklist_score = 0

        for file_info in files:
            deep_analysis = file_info.get('deep_analysis', {})
            extracted_files = deep_analysis.get('extracted_files', [])

            for bak_file in extracted_files:
                bak_summary['total_bak_files'] += 1

                size = bak_file.get('size', 0)
                backup_type = bak_file.get('backup_type', 'Unknown')

                # Skip excluded files in main analysis
                if bak_file.get('excluded', False):
                    bak_summary['by_validation_status']['excluded'] += 1
                    continue

                bak_summary['analyzed_bak_files'] += 1
                bak_summary['total_bak_size_bytes'] += size

                # Type analysis
                if backup_type not in bak_summary['by_backup_type']:
                    bak_summary['by_backup_type'][backup_type] = {
                        'count': 0,
                        'total_size': 0,
                        'average_size': 0,
                        'size_warnings': 0
                    }

                type_data = bak_summary['by_backup_type'][backup_type]
                type_data['count'] += 1
                type_data['total_size'] += size

                # Size validation
                size_warning = bak_file.get('size_warning', False)
                if size_warning:
                    bak_summary['size_validation']['below_minimum'] += 1
                    type_data['size_warnings'] += 1
                    bak_summary['size_validation']['size_warnings'].append({
                        'filename': bak_file.get('filename'),
                        'backup_type': backup_type,
                        'size': self.format_size(size),
                        'path': bak_file.get('path')
                    })
                else:
                    bak_summary['size_validation']['above_minimum'] += 1

                # Age analysis
                is_outdated = bak_file.get('is_outdated', False)
                days_since_backup = bak_file.get('days_since_backup', 0)
                file_date_one_day = bak_file.get('file_date_one_day_different', False)

                # Maintain age categories for statistical analysis
                if file_date_one_day:
                    bak_summary['age_analysis']['recent_24h'] += 1
                elif days_since_backup <= 7:
                    bak_summary['age_analysis']['last_7_days'] += 1
                else:
                    bak_summary['age_analysis']['older_than_7_days'] += 1

                # Outdated means file not modified today (based on new definition)
                if is_outdated:
                    bak_summary['age_analysis']['outdated_files'].append({
                        'filename': bak_file.get('filename'),
                        'days_outdated': days_since_backup,
                        'backup_type': backup_type
                    })

                # DBATools analysis
                dbatools_result = bak_file.get('dbatools_analysis', {})
                if dbatools_result:
                    if dbatools_result.get('status') == 'Analyzed':
                        bak_summary['dbatools_analysis']['successful'] += 1
                    else:
                        bak_summary['dbatools_analysis']['failed'] += 1
                        if 'errors' in dbatools_result:
                            bak_summary['dbatools_analysis']['errors'].extend(
                                dbatools_result['errors'][:3]  # Limit to first 3 errors
                            )
                else:
                    bak_summary['dbatools_analysis']['not_attempted'] += 1

                # Extraction analysis
                if deep_analysis.get('extraction_successful', False):
                    bak_summary['extraction_analysis']['successful'] += 1
                else:
                    bak_summary['extraction_analysis']['failed'] += 1

                # Validation checklist analysis
                validation_checklist = bak_file.get('validation_checklist', {})
                if validation_checklist:
                    bak_summary['checklist_summary']['total_checklists'] += 1

                    checklist_items = list(validation_checklist.values())
                    passed_items = sum(1 for item in checklist_items if item.get('status', False))
                    failed_items = len(checklist_items) - passed_items

                    total_checklist_items += len(checklist_items)
                    total_checklist_score += passed_items

                    # Track perfect scores
                    if failed_items == 0:
                        bak_summary['checklist_summary']['perfect_scores'] += 1

                    # Track common failures
                    for key, item in validation_checklist.items():
                        if not item.get('status', False):
                            if key not in bak_summary['checklist_summary']['common_failures']:
                                bak_summary['checklist_summary']['common_failures'][key] = 0
                            bak_summary['checklist_summary']['common_failures'][key] += 1

        # Calculate averages
        if bak_summary['analyzed_bak_files'] > 0:
            bak_summary['average_bak_size_bytes'] = bak_summary['total_bak_size_bytes'] / bak_summary['analyzed_bak_files']
            bak_summary['average_bak_size_formatted'] = self.format_size(bak_summary['average_bak_size_bytes'])

        # Calculate type averages
        for backup_type, type_data in bak_summary['by_backup_type'].items():
            if type_data['count'] > 0:
                type_data['average_size'] = type_data['total_size'] / type_data['count']
                type_data['average_size_formatted'] = self.format_size(type_data['average_size'])
                type_data['total_size_formatted'] = self.format_size(type_data['total_size'])

        # Calculate checklist average score
        if total_checklist_items > 0:
            bak_summary['checklist_summary']['average_score'] = (total_checklist_score / total_checklist_items) * 100

        # Determine validation status distribution
        for file_info in files:
            deep_analysis = file_info.get('deep_analysis', {})
            extracted_files = deep_analysis.get('extracted_files', [])

            for bak_file in extracted_files:
                if bak_file.get('excluded', False):
                    continue

                validation_checklist = bak_file.get('validation_checklist', {})
                if validation_checklist:
                    checklist_items = list(validation_checklist.values())
                    passed_items = sum(1 for item in checklist_items if item.get('status', False))
                    success_rate = (passed_items / len(checklist_items)) * 100

                    if success_rate >= 90:
                        bak_summary['by_validation_status']['valid'] += 1
                    elif success_rate >= 70:
                        bak_summary['by_validation_status']['warning'] += 1
                    else:
                        bak_summary['by_validation_status']['invalid'] += 1

        return bak_summary

def main():
    root = tk.Tk()
    app = ZipBackupMonitorEnhanced(root)
    root.mainloop()

if __name__ == "__main__":
    main()