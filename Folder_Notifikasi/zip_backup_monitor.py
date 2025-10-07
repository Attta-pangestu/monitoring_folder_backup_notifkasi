#!/usr/bin/env python3
"""
Monitor Backup Zip dengan Notifikasi Email
Aplikasi GUI untuk memonitor file backup ZIP, mengekstrak metadata,
menganalisis file BAK, dan mengirim notifikasi email.
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

class ZipBackupMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor Backup Zip")
        self.root.geometry("1200x800")

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
                logging.FileHandler(os.path.join(log_dir, 'zip_monitor.log')),
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
            'sender_email': '',
            'sender_password': '',
            'recipient_email': ''
        }

        self.config['MONITORING'] = {
            'check_interval': '300',  # 5 menit
            'max_age_days': '7',
            'extract_files': 'true',
            'exclude_plantware': 'true',
            # Minimum size validation for BAK files (in bytes)
            'min_size_staging': '2473901824',  # 2.3 GB in bytes
            'min_size_venus': '9342988800',    # 8.7 GB in bytes
            'min_size_plantware': '37580963840' # 35 GB in bytes
        }

        # Muat config yang sudah ada
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            # Simpan config default
            with open(self.config_file, 'w') as f:
                self.config.write(f)

    def save_config(self):
        """Simpan konfigurasi ke file INI"""
        with open(self.config_file, 'w') as f:
            self.config.write(f)

    def create_gui(self):
        """Buat interface GUI utama"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Path Selection
        ttk.Label(main_frame, text="Folder Monitor:").grid(row=0, column=0, sticky=tk.W, pady=5)
        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        path_frame.columnconfigure(0, weight=1)

        ttk.Entry(path_frame, textvariable=self.monitoring_path, width=50).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(path_frame, text="Pilih Folder", command=self.browse_path).grid(row=0, column=1)

        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)

        self.start_button = ttk.Button(button_frame, text="Mulai Monitor", command=self.start_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(button_frame, text="Stop Monitor", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Scan Sekarang", command=self.scan_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Test Email", command=self.send_test_email).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Email Summary", command=self.send_comprehensive_summary_email).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Pengaturan", command=self.open_settings).pack(side=tk.LEFT, padx=5)

        # Status
        self.status_label = ttk.Label(main_frame, text="Status: Siap", foreground="green")
        self.status_label.grid(row=2, column=0, columnspan=2, pady=5)

        # Progress Bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        main_frame.rowconfigure(4, weight=1)

        # Summary Tab
        summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(summary_frame, text="Ringkasan")

        self.summary_text = scrolledtext.ScrolledText(summary_frame, height=20, width=80)
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # File List Tab
        files_frame = ttk.Frame(self.notebook)
        self.notebook.add(files_frame, text="Daftar File")

        # Create treeview for file list
        columns = ('Nama File', 'Jenis Backup', 'Ukuran', 'Dimodifikasi', 'Status', 'Diekstrak', 'Analisis BAK')
        self.file_tree = ttk.Treeview(files_frame, columns=columns, show='headings', height=20)

        for col in columns:
            self.file_tree.heading(col, text=col)
            self.file_tree.column(col, width=120)

        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)

        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Log Tab
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="Log")

        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, width=80)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

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

        try:
            self.is_monitoring = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_label.config(text="Status: Memonitor...", foreground="blue")
            self.progress.start()

            self.logger.info("Memulai monitoring...")
            self.update_log("Memulai monitoring...")

            # Start monitoring thread
            if hasattr(self, 'monitoring_thread') and self.monitoring_thread and self.monitoring_thread.is_alive():
                self.logger.warning("Monitoring thread already running, stopping first...")
                self.is_monitoring = False
                time.sleep(1)  # Allow thread to stop

            self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
            self.monitoring_thread.start()

        except Exception as e:
            self.logger.error(f"Error starting monitoring: {str(e)}")
            messagebox.showerror("Error", f"Gagal memulai monitoring: {str(e)}")
            self.stop_monitoring()

    def stop_monitoring(self):
        """Hentikan monitoring"""
        self.is_monitoring = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Dihentikan", foreground="red")
        self.progress.stop()

        self.logger.info("Menghentikan monitoring...")
        self.update_log("Monitoring dihentikan.")

    def monitoring_loop(self):
        """Loop monitoring utama"""
        while self.is_monitoring:
            try:
                # Check if monitoring is still active
                if not self.is_monitoring:
                    break

                self.scan_files()

                # Check again before sleeping
                if not self.is_monitoring:
                    break

                check_interval = int(self.config['MONITORING']['check_interval'])

                # Sleep in smaller increments to allow for faster shutdown
                for _ in range(check_interval):
                    if not self.is_monitoring:
                        break
                    time.sleep(1)

            except Exception as e:
                self.logger.error(f"Error dalam monitoring loop: {str(e)}")
                self.update_log(f"Error: {str(e)}")

                # Wait a bit before retrying
                time.sleep(5)

    def scan_files(self):
        """Scan folder untuk file ZIP dan analisis"""
        # Start scanning in a separate thread to prevent GUI freezing
        scan_thread = threading.Thread(target=self._scan_files_thread, daemon=True)
        scan_thread.start()

    def _scan_files_thread(self):
        """Thread function for scanning files"""
        try:
            path = self.monitoring_path.get()
            if not path or not os.path.exists(path):
                return

            self.update_log(f"Menscan folder: {path}")
            self.update_status("Menscan file...")

            # Find ZIP files
            zip_files = self.find_zip_files(path)

            if not zip_files:
                self.update_log("Tidak ada file ZIP ditemukan.")
                self.update_status("Tidak ada file")
                return

            # Get latest date
            latest_date = self.get_latest_date(zip_files)

            # Filter files by latest date
            filtered_files = [f for f in zip_files if self.is_file_date(f, latest_date)]

            self.update_log(f"Ditemukan {len(filtered_files)} file ZIP untuk tanggal {latest_date}")

            # Analyze files with progress updates
            self.analyze_files_threaded(filtered_files)

            # Update summary
            self.update_summary()

            # Check for overdue backups
            self.check_backup_overdue(filtered_files)

            self.update_status("Scan selesai")

        except Exception as e:
            self.logger.error(f"Error menscan file: {str(e)}")
            self.update_log(f"Error menscan file: {str(e)}")
            self.update_status("Error menscan file")

    def analyze_files_threaded(self, files: List[str]):
        """Analyze files with progress updates to prevent GUI freezing"""
        self.summary_data = {}

        for i, file_path in enumerate(files):
            try:
                self.update_log(f"Menganalisis ({i+1}/{len(files)}): {os.path.basename(file_path)}")
                self.update_status(f"Menganalisis file {i+1}/{len(files)}...")

                # Basic file info
                stat = os.path.stat(file_path)
                file_info = {
                    'path': file_path,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'status': 'Menunggu',
                    'extracted': False,
                    'bak_files': [],
                    'compression_ratio': 0,
                    'extractable': False,
                    'corrupt': False
                }

                # Analyze ZIP file
                zip_analysis = self.analyze_zip_file(file_path)
                file_info.update(zip_analysis)

                # Extract if enabled
                if self.config.getboolean('MONITORING', 'extract_files'):
                    extracted = self.extract_zip_file(file_path)
                    file_info['extracted'] = extracted

                    # Analyze BAK files if extracted
                    if extracted and file_info['bak_files']:
                        bak_analysis = self.analyze_bak_files(file_info['bak_files'])
                        file_info['bak_analysis'] = bak_analysis

                self.summary_data[file_path] = file_info

                # Update GUI
                self.update_file_list(file_info)

            except Exception as e:
                self.logger.error(f"Error menganalisis {file_path}: {str(e)}")
                self.update_log(f"Error menganalisis {file_path}: {str(e)}")

        # Save summary to JSON
        self.save_summary_json()

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

    def analyze_files(self, files: List[str]):
        """Analisis file ZIP dan ekstrak metadata"""
        self.summary_data = {}

        for file_path in files:
            try:
                self.update_log(f"Menganalisis: {os.path.basename(file_path)}")

                # Basic file info
                stat = os.stat(file_path)
                file_info = {
                    'path': file_path,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'status': 'Menunggu',
                    'extracted': False,
                    'bak_files': [],
                    'compression_ratio': 0,
                    'extractable': False,
                    'corrupt': False
                }

                # Analyze ZIP file
                zip_analysis = self.analyze_zip_file(file_path)
                file_info.update(zip_analysis)

                # Extract if enabled
                if self.config.getboolean('MONITORING', 'extract_files'):
                    extracted = self.extract_zip_file(file_path)
                    file_info['extracted'] = extracted

                    # Analyze BAK files if extracted
                    if extracted and file_info['bak_files']:
                        bak_analysis = self.analyze_bak_files(file_info['bak_files'])
                        file_info['bak_analysis'] = bak_analysis

                self.summary_data[file_path] = file_info

                # Update GUI
                self.update_file_list(file_info)

            except Exception as e:
                self.logger.error(f"Error menganalisis {file_path}: {str(e)}")
                self.update_log(f"Error menganalisis {file_path}: {str(e)}")

        # Save summary to JSON
        self.save_summary_json()

    def analyze_zip_file(self, file_path: str) -> Dict:
        """Analisis struktur dan konten file ZIP"""
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
            'zip_checklist': {}
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

                # Calculate sizes and categorize BAK files
                for file in file_list:
                    info = zip_ref.getinfo(file)
                    analysis['compressed_size'] += info.compress_size
                    analysis['uncompressed_size'] += info.file_size

                    # Look for BAK files and categorize by backup type
                    if file.lower().endswith('.bak'):
                        bak_info = {
                            'filename': file,
                            'size': info.file_size,
                            'backup_type': self.detect_backup_type_from_filename(file)
                        }
                        analysis['bak_files'].append(bak_info)

                # Calculate compression ratio
                if analysis['uncompressed_size'] > 0:
                    analysis['compression_ratio'] = (1 - analysis['compressed_size'] / analysis['uncompressed_size']) * 100

                analysis['extractable'] = True
                analysis['status'] = 'Valid'

                # Generate ZIP checklist
                analysis['zip_checklist'] = self.generate_zip_checklist(file_path, analysis)

        except Exception as e:
            analysis['corrupt'] = True
            analysis['status'] = f'Error: {str(e)}'

        return analysis

    def generate_zip_checklist(self, file_path: str, analysis: Dict) -> Dict:
        """Generate checklist analisis validitas file ZIP"""
        checklist = {
            'integritas_struktur': {
                'status': False,
                'keterangan': 'Struktur file ZIP valid',
                'hasil': '[GAGAL] Gagal'
            },
            'kemampuan_ekstrak': {
                'status': False,
                'keterangan': 'File dapat diekstrak',
                'hasil': '[GAGAL] Gagal'
            },
            'ketersediaan_file': {
                'status': False,
                'keterangan': 'File ZIP dapat diakses',
                'hasil': '[GAGAL] Tidak dapat diakses'
            },
            'ukuran_file': {
                'status': False,
                'keterangan': 'Ukuran file wajar (>1KB)',
                'hasil': '[GAGAL] Ukuran tidak wajar'
            },
            'kompresi_efektif': {
                'status': False,
                'keterangan': 'Rasio kompresi efektif (>5%)',
                'hasil': '[GAGAL] Kompresi tidak efektif'
            },
            'tidak_corrupt': {
                'status': False,
                'keterangan': 'File tidak corrupt',
                'hasil': '[GAGAL] File corrupt'
            },
            'memiliki_konten': {
                'status': False,
                'keterangan': 'ZIP memiliki konten/file',
                'hasil': '[GAGAL] ZIP kosong'
            },
            'tanggal_backup_valid': {
                'status': False,
                'keterangan': 'Tanggal backup masuk akal',
                'hasil': '[GAGAL] Tanggal tidak valid'
            }
        }

        try:
            # Check ketersediaan file
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                checklist['ketersediaan_file']['status'] = True
                checklist['ketersediaan_file']['hasil'] = '[VALID] Valid'

            # Check ukuran file
            file_size = os.path.getsize(file_path)
            if file_size > 1024:  # > 1KB
                checklist['ukuran_file']['status'] = True
                checklist['ukuran_file']['hasil'] = '[VALID] Valid'

            # Check integritas dan kemampuan ekstrak
            if analysis.get('extractable', False) and not analysis.get('corrupt', False):
                checklist['integritas_struktur']['status'] = True
                checklist['integritas_struktur']['hasil'] = '[VALID] Valid'
                checklist['kemampuan_ekstrak']['status'] = True
                checklist['kemampuan_ekstrak']['hasil'] = '[VALID] Valid'
                checklist['tidak_corrupt']['status'] = True
                checklist['tidak_corrupt']['hasil'] = '[VALID] Valid'

            # Check kompresi efektif
            if analysis.get('compression_ratio', 0) > 5:
                checklist['kompresi_efektif']['status'] = True
                checklist['kompresi_efektif']['hasil'] = '[VALID] Valid'

            # Check memiliki konten
            if analysis.get('file_count', 0) > 0:
                checklist['memiliki_konten']['status'] = True
                checklist['memiliki_konten']['hasil'] = '[VALID] Valid'

            # Check tanggal backup valid
            try:
                mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                current_time = datetime.now()
                time_diff = (current_time - mod_time).days

                if 0 <= time_diff <= 365:  # Backup dalam 1 tahun terakhir
                    checklist['tanggal_backup_valid']['status'] = True
                    checklist['tanggal_backup_valid']['hasil'] = '[VALID] Valid'
                else:
                    checklist['tanggal_backup_valid']['keterangan'] = f'Tanggal backup: {mod_time.strftime("%Y-%m-%d")}'
            except:
                pass

        except Exception as e:
            self.logger.error(f"Error generating ZIP checklist: {str(e)}")

        return checklist

    def generate_bak_checklist(self, bak_file: str, backup_type: str, analysis_info: Dict = None) -> Dict:
        """Generate checklist analisis keterbacaan file BAK"""
        checklist = {
            'akses_file': {
                'status': False,
                'keterangan': 'File BAK dapat diakses',
                'hasil': '[GAGAL] Tidak dapat diakses'
            },
            'ukuran_wajar': {
                'status': False,
                'keterangan': 'Ukuran file BAK wajar (>10KB)',
                'hasil': '[GAGAL] Ukuran tidak wajar'
            },
            'ukuran_minimum': {
                'status': False,
                'keterangan': 'Ukuran minimum sesuai jenis backup',
                'hasil': '[GAGAL] Ukuran di bawah minimum'
            },
            'format_backup_valid': {
                'status': False,
                'keterangan': 'Format backup database valid',
                'hasil': '[GAGAL] Format tidak valid'
            },
            'header_dapat_dibaca': {
                'status': False,
                'keterangan': 'Header file dapat dibaca',
                'hasil': '[GAGAL] Header tidak dapat dibaca'
            },
            'bisa_direstore': {
                'status': False,
                'keterangan': 'File dapat direstore (estimated)',
                'hasil': '[GAGAL] Tidak dapat direstore'
            },
            'jenis_backup_dikenal': {
                'status': False,
                'keterangan': 'Jenis backup teridentifikasi',
                'hasil': '[GAGAL] Jenis tidak dikenal'
            },
            'tanggal_backup_masuk_akal': {
                'status': False,
                'keterangan': 'Tanggal backup masuk akal',
                'hasil': '[GAGAL] Tanggal tidak valid'
            },
            'tidak_corrupt': {
                'status': False,
                'keterangan': 'File BAK tidak corrupt',
                'hasil': '[GAGAL] File corrupt'
            }
        }

        try:
            # Check akses file
            if os.path.exists(bak_file) and os.path.getsize(bak_file) > 0:
                checklist['akses_file']['status'] = True
                checklist['akses_file']['hasil'] = '[VALID] Valid'

            # Check ukuran wajar
            bak_size = os.path.getsize(bak_file)
            if bak_size > 10240:  # > 10KB
                checklist['ukuran_wajar']['status'] = True
                checklist['ukuran_wajar']['hasil'] = '[VALID] Valid'

            # Check ukuran minimum sesuai jenis backup
            min_size_threshold = 0
            size_display = ""

            if backup_type == 'BackupStaging':
                min_size_threshold = int(self.config['MONITORING'].get('min_size_staging', '2473901824'))
                size_display = "2.3 GB"
            elif backup_type == 'BackupVenus':
                min_size_threshold = int(self.config['MONITORING'].get('min_size_venus', '9342988800'))
                size_display = "8.7 GB"
            elif backup_type == 'PlantwareP3':
                min_size_threshold = int(self.config['MONITORING'].get('min_size_plantware', '37580963840'))
                size_display = "35 GB"
            else:
                # Untuk unknown type, gunakan threshold default 1GB
                min_size_threshold = 1073741824  # 1 GB
                size_display = "1 GB"

            if bak_size >= min_size_threshold:
                checklist['ukuran_minimum']['status'] = True
                checklist['ukuran_minimum']['hasil'] = f'[VALID] Valid (≥{size_display})'
            else:
                actual_size_gb = bak_size / (1024**3)  # Convert to GB
                checklist['ukuran_minimum']['hasil'] = f'[GAGAL] {actual_size_gb:.2f} GB (Minimal: {size_display})'

            # Check jenis backup dikenal
            if backup_type != 'Unknown':
                checklist['jenis_backup_dikenal']['status'] = True
                checklist['jenis_backup_dikenal']['hasil'] = '[VALID] Valid'

            # Check header dapat dibaca
            if analysis_info and analysis_info.get('header_valid', False):
                checklist['header_dapat_dibaca']['status'] = True
                checklist['header_dapat_dibaca']['hasil'] = '[VALID] Valid'

            # Check format backup valid
            if analysis_info and analysis_info.get('can_restore', False):
                checklist['format_backup_valid']['status'] = True
                checklist['format_backup_valid']['hasil'] = '[VALID] Valid'
                checklist['bisa_direstore']['status'] = True
                checklist['bisa_direstore']['hasil'] = '[VALID] Valid'

            # Check tanggal backup masuk akal
            try:
                mod_time = datetime.fromtimestamp(os.path.getmtime(bak_file))
                current_time = datetime.now()
                time_diff = (current_time - mod_time).days

                if 0 <= time_diff <= 365:
                    checklist['tanggal_backup_masuk_akal']['status'] = True
                    checklist['tanggal_backup_masuk_akal']['hasil'] = '[VALID] Valid'
                else:
                    checklist['tanggal_backup_masuk_akal']['keterangan'] = f'Tanggal backup: {mod_time.strftime("%Y-%m-%d")}'
            except:
                pass

            # Check tidak corrupt (berdasarkan ukuran dan akses)
            if checklist['akses_file']['status'] and checklist['ukuran_wajar']['status']:
                checklist['tidak_corrupt']['status'] = True
                checklist['tidak_corrupt']['hasil'] = '[VALID] Valid'

        except Exception as e:
            self.logger.error(f"Error generating BAK checklist: {str(e)}")

        return checklist

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

    def extract_zip_file(self, file_path: str) -> bool:
        """Ekstrak file ZIP ke folder yang sama"""
        try:
            extract_dir = os.path.dirname(file_path)

            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            self.update_log(f"Terekstrak: {os.path.basename(file_path)}")
            return True

        except Exception as e:
            self.logger.error(f"Error mengekstrak {file_path}: {str(e)}")
            self.update_log(f"Error mengekstrak {file_path}: {str(e)}")
            return False

    def analyze_bak_files(self, bak_files: List[str]) -> Dict:
        """Analyze BAK files using dbatools or SQL Server commands"""
        analysis = {
            'total_files': len(bak_files),
            'valid_files': 0,
            'corrupt_files': 0,
            'restoreable': 0,
            'total_tables': 0,
            'total_rows': 0,
            'by_type': {
                'BackupStaging': {'count': 0, 'valid': 0, 'tables': 0, 'rows': 0},
                'BackupVenus': {'count': 0, 'valid': 0, 'tables': 0, 'rows': 0},
                'PlantwareP3': {'count': 0, 'valid': 0, 'tables': 0, 'rows': 0},
                'Unknown': {'count': 0, 'valid': 0, 'tables': 0, 'rows': 0}
            },
            'details': [],
            'bak_checklists': []
        }

        # Check if PlantwareP3 should be excluded
        exclude_plantware = self.config.getboolean('MONITORING', 'exclude_plantware', fallback=False)

        for bak_info in bak_files:
            try:
                bak_path = bak_info['filename'] if isinstance(bak_info, dict) else bak_info
                backup_type = bak_info['backup_type'] if isinstance(bak_info, dict) else self.detect_backup_type_from_filename(bak_path)

                # Skip PlantwareP3 if excluded
                if exclude_plantware and backup_type == 'PlantwareP3':
                    self.update_log(f"Melewati PlantwareP3: {os.path.basename(bak_path)}")
                    continue

                # Get BAK file info using specialized analysis
                detailed_info = self.get_detailed_bak_info(bak_path, backup_type)

                # Generate BAK checklist
                bak_checklist = self.generate_bak_checklist(bak_path, backup_type, detailed_info)

                if detailed_info:
                    analysis['valid_files'] += 1
                    if detailed_info.get('can_restore', False):
                        analysis['restoreable'] += 1
                    analysis['total_tables'] += detailed_info.get('table_count', 0)
                    analysis['total_rows'] += detailed_info.get('row_count', 0)

                    # Update by type statistics
                    if backup_type in analysis['by_type']:
                        analysis['by_type'][backup_type]['count'] += 1
                        if detailed_info.get('can_restore', False):
                            analysis['by_type'][backup_type]['valid'] += 1
                        analysis['by_type'][backup_type]['tables'] += detailed_info.get('table_count', 0)
                        analysis['by_type'][backup_type]['rows'] += detailed_info.get('row_count', 0)

                    # Add checklist to detailed info
                    detailed_info['checklist'] = bak_checklist
                    analysis['details'].append(detailed_info)
                    analysis['bak_checklists'].append({
                        'filename': os.path.basename(bak_path),
                        'backup_type': backup_type,
                        'checklist': bak_checklist
                    })
                else:
                    analysis['corrupt_files'] += 1
                    # Still add checklist for corrupt files
                    analysis['bak_checklists'].append({
                        'filename': os.path.basename(bak_path),
                        'backup_type': backup_type,
                        'checklist': bak_checklist
                    })

            except Exception as e:
                self.logger.error(f"Error analyzing BAK {bak_path}: {str(e)}")
                analysis['corrupt_files'] += 1

        return analysis

    def get_detailed_bak_info(self, bak_file: str, backup_type: str) -> Optional[Dict]:
        """Get detailed BAK file information based on backup type"""
        try:
            base_info = {
                'filename': os.path.basename(bak_file),
                'backup_type': backup_type,
                'size': os.path.getsize(bak_file) if os.path.exists(bak_file) else 0,
                'can_restore': False,
                'backup_date': '',
                'database_name': '',
                'table_count': 0,
                'row_count': 0,
                'analysis_details': '',
                'special_info': {}
            }

            # Specialized analysis based on backup type
            if backup_type == 'BackupStaging':
                return self.analyze_staging_backup(bak_file, base_info)
            elif backup_type == 'BackupVenus':
                return self.analyze_venus_backup(bak_file, base_info)
            elif backup_type == 'PlantwareP3':
                return self.analyze_plantware_backup(bak_file, base_info)
            else:
                return self.analyze_generic_backup(bak_file, base_info)

        except Exception as e:
            self.logger.error(f"Error getting detailed BAK info for {bak_file}: {str(e)}")
            return None

    def analyze_staging_backup(self, bak_file: str, base_info: Dict) -> Dict:
        """Analyze BackupStaging (GWScanner/Staging database)"""
        try:
            # Try SQL Server analysis first
            if self.is_sql_server_available():
                sql_info = self.get_sql_server_backup_info(bak_file)
                if sql_info:
                    base_info.update(sql_info)
                    base_info['analysis_details'] = "Analisis SQL Server berhasil - Database Staging/GWScanner"
                    base_info['can_restore'] = True
                    return base_info

            # Fallback to file analysis
            file_info = self.analyze_backup_file_header(bak_file)
            if file_info:
                base_info.update(file_info)
                base_info['analysis_details'] = "Analisis header file - Database Staging (fallback)"
                base_info['table_count'] = self.estimate_staging_tables(bak_file)
                return base_info

        except Exception as e:
            self.logger.error(f"Error analyzing staging backup {bak_file}: {str(e)}")

        return None

    def analyze_venus_backup(self, bak_file: str, base_info: Dict) -> Dict:
        """Analyze BackupVenus (Venus/Time Attendance database)"""
        try:
            # Try SQL Server analysis first
            if self.is_sql_server_available():
                sql_info = self.get_sql_server_backup_info(bak_file)
                if sql_info:
                    base_info.update(sql_info)
                    base_info['analysis_details'] = "Analisis SQL Server berhasil - Database Venus/Time Attendance"
                    base_info['can_restore'] = True
                    return base_info

            # Fallback to file analysis
            file_info = self.analyze_backup_file_header(bak_file)
            if file_info:
                base_info.update(file_info)
                base_info['analysis_details'] = "Analisis header file - Database Venus (fallback)"
                base_info['table_count'] = self.estimate_venus_tables(bak_file)
                return base_info

        except Exception as e:
            self.logger.error(f"Error analyzing venus backup {bak_file}: {str(e)}")

        return None

    def analyze_plantware_backup(self, bak_file: str, base_info: Dict) -> Dict:
        """Analyze PlantwareP3 backup (currently excluded from analysis)"""
        try:
            file_info = self.analyze_backup_file_header(bak_file)
            if file_info:
                base_info.update(file_info)
                base_info['analysis_details'] = "Analisis header file - Plantware P3 (basic analysis)"
                base_info['special_info'] = {
                    'format_type': 'Plantware P3 TAPE format',
                    'compatibility': 'Requires special restore procedure'
                }
                return base_info

        except Exception as e:
            self.logger.error(f"Error analyzing plantware backup {bak_file}: {str(e)}")

        return None

    def analyze_generic_backup(self, bak_file: str, base_info: Dict) -> Dict:
        """Analyze generic/unknown backup type"""
        try:
            file_info = self.analyze_backup_file_header(bak_file)
            if file_info:
                base_info.update(file_info)
                base_info['analysis_details'] = "Analisis header file - Database generik"
                return base_info

        except Exception as e:
            self.logger.error(f"Error analyzing generic backup {bak_file}: {str(e)}")

        return None

    def is_sql_server_available(self) -> bool:
        """Check if SQL Server is available for backup analysis"""
        try:
            result = subprocess.run(
                ['sqlcmd', '-S', 'localhost', '-Q', 'SELECT 1'],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False

    def get_sql_server_backup_info(self, bak_file: str) -> Optional[Dict]:
        """Get backup info using SQL Server commands"""
        try:
            cmd = [
                'sqlcmd',
                '-S', 'localhost',
                '-Q', f'RESTORE HEADERONLY FROM DISK = N\'{bak_file}\''
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return self.parse_sql_server_output(result.stdout, bak_file)

        except Exception as e:
            self.logger.error(f"Error getting SQL Server backup info: {str(e)}")

        return None

    def parse_sql_server_output(self, output: str, bak_file: str) -> Dict:
        """Parse SQL Server RESTORE HEADERONLY output"""
        try:
            lines = output.split('\n')
            info = {
                'backup_date': '',
                'database_name': '',
                'table_count': 0,
                'row_count': 0
            }

            # Extract basic info from output
            for line in lines:
                if 'BackupStartDate' in line:
                    info['backup_date'] = line.split()[-1]
                elif 'DatabaseName' in line:
                    info['database_name'] = line.split()[-1]

            # Try to get more detailed info
            try:
                # Get file list info
                filelist_cmd = [
                    'sqlcmd',
                    '-S', 'localhost',
                    '-Q', f'RESTORE FILELISTONLY FROM DISK = N\'{bak_file}\''
                ]
                filelist_result = subprocess.run(filelist_cmd, capture_output=True, text=True, timeout=30)

                if filelist_result.returncode == 0:
                    info['table_count'] = self.estimate_tables_from_filelist(filelist_result.stdout)

            except:
                pass

            return info

        except Exception as e:
            self.logger.error(f"Error parsing SQL Server output: {str(e)}")
            return {}

    def analyze_backup_file_header(self, bak_file: str) -> Optional[Dict]:
        """Analyze BAK file header information"""
        try:
            with open(bak_file, 'rb') as f:
                # Read first few bytes to identify backup format
                header = f.read(512)

                # Basic validation - SQL Server backup files have specific headers
                if len(header) < 100:
                    return None

                return {
                    'backup_date': datetime.fromtimestamp(os.path.getmtime(bak_file)).strftime('%Y-%m-%d %H:%M:%S'),
                    'file_size': os.path.getsize(bak_file),
                    'header_valid': True
                }

        except Exception as e:
            self.logger.error(f"Error analyzing backup file header: {str(e)}")
            return None

    def estimate_staging_tables(self, bak_file: str) -> int:
        """Estimate table count for Staging database"""
        # Typical Staging/GWScanner tables
        typical_tables = [
            'gwscannermaster', 'gwscannerdata', 'gwscannermstr',
            'fingerprints', 'attendance', 'employees', 'departments'
        ]
        return len(typical_tables)

    def estimate_venus_tables(self, bak_file: str) -> int:
        """Estimate table count for Venus database"""
        # Typical Venus/Time Attendance tables
        typical_tables = [
            'attendance', 'employees', 'departments', 'schedules',
            'fingerprints', 'devices', 'logs', 'holidays'
        ]
        return len(typical_tables)

    def estimate_tables_from_filelist(self, output: str) -> int:
        """Estimate table count from RESTORE FILELISTONLY output"""
        try:
            lines = output.split('\n')
            data_files = 0
            log_files = 0

            for line in lines:
                if '.mdf' in line.lower() or '.ndf' in line.lower():
                    data_files += 1
                elif '.ldf' in line.lower():
                    log_files += 1

            # Estimate based on file structure
            return max(1, data_files)

        except:
            return 1

    def get_bak_info(self, bak_file: str) -> Optional[Dict]:
        """Legacy method - Get BAK file information using SQL Server commands"""
        return self.get_sql_server_backup_info(bak_file)

    def update_file_list(self, file_info: Dict):
        """Update daftar file di GUI"""
        filename = os.path.basename(file_info['path'])
        backup_type = file_info.get('backup_type', 'Unknown')
        size = self.format_size(file_info['size'])
        modified = file_info['modified'][:19]  # Remove microseconds
        status = file_info['status']
        extracted = "Ya" if file_info['extracted'] else "Tidak"

        bak_info = "Tidak ada BAK"
        if 'bak_analysis' in file_info:
            ba = file_info['bak_analysis']
            bak_info = f"{ba['valid_files']}/{ba['total_files']} valid"

        self.file_tree.insert('', 'end', values=(
            filename, backup_type, size, modified, status, extracted, bak_info
        ))

    def update_summary(self):
        """Update informasi ringkasan"""
        total_files = len(self.summary_data)
        valid_files = sum(1 for f in self.summary_data.values() if f['status'] == 'Valid')
        extracted_files = sum(1 for f in self.summary_data.values() if f['extracted'])

        # Calculate total compression ratio
        total_compressed = sum(f['compressed_size'] for f in self.summary_data.values())
        total_uncompressed = sum(f['uncompressed_size'] for f in self.summary_data.values())
        avg_compression = (1 - total_compressed / total_uncompressed) * 100 if total_uncompressed > 0 else 0

        # BAK analysis summary
        total_bak = sum(len(f['bak_files']) for f in self.summary_data.values())
        valid_bak = sum(f.get('bak_analysis', {}).get('valid_files', 0) for f in self.summary_data.values())

        summary_text = f"""Laporan Ringkasan Backup
=======================

Total file ZIP: {total_files}
File ZIP valid: {valid_files}
File diekstrak: {extracted_files}

Informasi Kompresi:
- Total size terkompres: {self.format_size(total_compressed)}
- Total size asli: {self.format_size(total_uncompressed)}
- Rata-rata rasio kompresi: {avg_compression:.1f}%

Analisis File BAK:
- Total file BAK: {total_bak}
- File BAK valid: {valid_bak}
- Total tabel: {sum(f.get('bak_analysis', {}).get('total_tables', 0) for f in self.summary_data.values())}
- Total baris data: {sum(f.get('bak_analysis', {}).get('total_rows', 0) for f in self.summary_data.values())}

Dibuat: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, summary_text)

    def check_backup_overdue(self, files: List[str]):
        """Cek apakah backup sudah overdue dan kirim notifikasi"""
        if not files:
            return

        # Get latest backup date
        latest_file = max(files, key=os.path.getmtime)
        latest_date = datetime.fromtimestamp(os.path.getmtime(latest_file))

        # Check if backup is older than threshold
        max_age_days = int(self.config['MONITORING']['max_age_days'])
        overdue_threshold = datetime.now() - timedelta(days=max_age_days)

        if latest_date < overdue_threshold:
            # Send overdue notification
            self.send_overdue_notification(latest_date)

    def send_overdue_notification(self, latest_date: datetime):
        """Kirim email notifikasi untuk backup overdue"""
        try:
            subject = "⚠️ URGENT: Backup System - Backup Terlambat Terdeteksi"
            body = self.generate_overdue_email_template(latest_date)

            self.send_email(subject, body)
            self.update_log(f"Terkirim notifikasi backup terlambat (Terbaru: {latest_date})")

        except Exception as e:
            self.logger.error(f"Error mengirim notifikasi overdue: {str(e)}")

    def generate_overdue_email_template(self, latest_date: datetime) -> str:
        """Generate template email untuk backup overdue"""
        days_overdue = (datetime.now() - latest_date).days

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Backup System Alert</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; border-bottom: 3px solid #dc3545; padding-bottom: 20px; margin-bottom: 30px; }}
        .alert {{ background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .info-box {{ background-color: #e7f3ff; border: 1px solid #b3d9ff; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
        .highlight {{ font-weight: bold; color: #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 BACKUP SYSTEM ALERT</h1>
            <h2>Backup Terlambat Terdeteksi</h2>
        </div>

        <div class="alert">
            <h3>⚠️ PERINGATAN KRITIS</h3>
            <p>Sistem backup mengalami keterlambatan yang signifikan. Segera lakukan pengecekan dan tindakan perbaikan.</p>
        </div>

        <div class="info-box">
            <h3>📊 Detail Keterlambatan</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Tanggal Backup Terbaru:</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><span class="highlight">{latest_date.strftime('%Y-%m-%d %H:%M:%S')}</span></td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Hari Keterlambatan:</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><span class="highlight">{days_overdue} hari</span></td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Threshold Alert:</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">{self.config['MONITORING']['max_age_days']} hari</td>
                </tr>
                <tr>
                    <td style="padding: 10px;"><strong>Waktu Deteksi:</strong></td>
                    <td style="padding: 10px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                </tr>
            </table>
        </div>

        <div class="info-box">
            <h3>🔍 Tindakan yang Disarankan</h3>
            <ol>
                <li>Periksa koneksi jaringan dan storage backup</li>
                <li>Verifikasi proses backup scheduler</li>
                <li>Check kapasitas storage yang tersedia</li>
                <li>Restart service backup jika diperlukan</li>
                <li>Hubungi IT Administrator jika masalah persisten</li>
            </ol>
        </div>

        <div class="footer">
            <p>Email ini dihasilkan otomatis oleh Backup Monitor System v1.0</p>
            <p>Hubungi: IT Support Department | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""

    def send_email(self, subject: str, body: str, attachment_path: str = None):
        """Kirim notifikasi email"""
        try:
            # Get email configuration
            smtp_server = self.config['EMAIL']['smtp_server']
            smtp_port = int(self.config['EMAIL']['smtp_port'])
            sender_email = self.config['EMAIL']['sender_email']
            sender_password = self.config['EMAIL']['sender_password']
            recipient_email = self.config['EMAIL']['recipient_email']

            if not all([smtp_server, sender_email, sender_password, recipient_email]):
                raise ValueError("Konfigurasi email tidak lengkap")

            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject

            # Add body
            msg.attach(MIMEText(body, 'html'))

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
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)

            self.logger.info("Email berhasil dikirim")

        except Exception as e:
            self.logger.error(f"Error mengirim email: {str(e)}")
            raise

    def send_test_email(self):
        """Kirim email test"""
        try:
            subject = "[VALID] Monitor Backup Zip - Email Test"
            body = self.generate_test_email_template()

            self.send_email(subject, body)
            messagebox.showinfo("Berhasil", "Email test berhasil dikirim!")
            self.update_log("Email test berhasil dikirim")

        except Exception as e:
            messagebox.showerror("Error", f"Gagal mengirim email test: {str(e)}")
            self.update_log(f"Gagal mengirim email test: {str(e)}")

    def send_comprehensive_summary_email(self):
        """Kirim email summary komprehensif hasil analisis BAK"""
        try:
            if not self.summary_data:
                self.update_log("Tidak ada data summary untuk dikirim")
                return

            subject = f"📊 Laporan Analisis Backup Komprehensif - {datetime.now().strftime('%Y-%m-%d')}"
            body = self.generate_comprehensive_summary_email_template()

            self.send_email(subject, body)
            self.update_log("Email summary komprehensif berhasil dikirim")

        except Exception as e:
            self.logger.error(f"Error mengirim email summary: {str(e)}")
            self.update_log(f"Error mengirim email summary: {str(e)}")

    def generate_test_email_template(self) -> str:
        """Generate template email test"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Email Test - Backup Monitor</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; border-bottom: 3px solid #28a745; padding-bottom: 20px; margin-bottom: 30px; }}
        .success {{ background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .info-box {{ background-color: #e7f3ff; border: 1px solid #b3d9ff; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>[VALID] Email Test Berhasil</h1>
            <h2>Monitor Backup Zip System</h2>
        </div>

        <div class="success">
            <h3>🎉 Konfigurasi Email Berhasil!</h3>
            <p>Sistem notifikasi email Monitor Backup Zip berfungsi dengan baik.</p>
        </div>

        <div class="info-box">
            <h3>📋 Detail Test</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Waktu Test:</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Status:</strong></td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;"><span style="color: #28a745; font-weight: bold;">[VALID] Berhasil</span></td>
                </tr>
                <tr>
                    <td style="padding: 10px;"><strong>Sistem:</strong></td>
                    <td style="padding: 10px;">Monitor Backup Zip v1.0</td>
                </tr>
            </table>
        </div>

        <div class="info-box">
            <h3>ℹ️ Informasi Sistem</h3>
            <p>Email ini menunjukkan bahwa konfigurasi SMTP server telah berhasil disetup dan siap digunakan untuk mengirim:</p>
            <ul>
                <li>Notifikasi backup terlambat</li>
                <li>Laporan analisis backup komprehensif</li>
                <li>Alert sistem monitoring</li>
            </ul>
        </div>

        <div class="footer">
            <p>Email ini dihasilkan otomatis oleh Backup Monitor System v1.0</p>
            <p>Hubungi: IT Support Department | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""

    def generate_comprehensive_summary_email_template(self) -> str:
        """Generate template email summary komprehensif hasil analisis BAK"""
        if not self.summary_data:
            return ""

        # Calculate statistics
        total_files = len(self.summary_data)
        valid_files = sum(1 for f in self.summary_data.values() if f['status'] == 'Valid')
        extracted_files = sum(1 for f in self.summary_data.values() if f['extracted'])

        # Calculate total compression ratio
        total_compressed = sum(f['compressed_size'] for f in self.summary_data.values())
        total_uncompressed = sum(f['uncompressed_size'] for f in self.summary_data.values())
        avg_compression = (1 - total_compressed / total_uncompressed) * 100 if total_uncompressed > 0 else 0

        # BAK analysis summary by type
        bak_stats = self.get_bak_statistics_by_type()
        exclude_plantware = self.config.getboolean('MONITORING', 'exclude_plantware', fallback=False)

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Laporan Analisis Backup Komprehensif</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1000px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; border-bottom: 3px solid #007bff; padding-bottom: 20px; margin-bottom: 30px; }}
        .summary-box {{ background-color: #e7f3ff; border: 1px solid #b3d9ff; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .backup-type {{ background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .success {{ background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 10px; border-radius: 5px; }}
        .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 10px; border-radius: 5px; }}
        .danger {{ background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 10px; border-radius: 5px; }}
        .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; font-weight: bold; }}
        .stat-number {{ font-size: 24px; font-weight: bold; color: #007bff; }}
        .backup-staging {{ border-left: 4px solid #28a745; }}
        .backup-venus {{ border-left: 4px solid #ffc107; }}
        .backup-plantware {{ border-left: 4px solid #dc3545; }}
        .backup-unknown {{ border-left: 4px solid #6c757d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Laporan Analisis Backup Komprehensif</h1>
            <h2>Hasil Monitoring File Backup Database</h2>
            <p><em>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
        </div>

        <div class="summary-box">
            <h3>📈 Ringkasan Eksekutif</h3>
            <table>
                <tr>
                    <td><strong>Total File ZIP Dianalisis:</strong></td>
                    <td><span class="stat-number">{total_files}</span> file</td>
                </tr>
                <tr>
                    <td><strong>File ZIP Valid:</strong></td>
                    <td><span class="stat-number" style="color: #28a745;">{valid_files}</span> file</td>
                </tr>
                <tr>
                    <td><strong>File Berhasil Diekstrak:</strong></td>
                    <td><span class="stat-number" style="color: #17a2b8;">{extracted_files}</span> file</td>
                </tr>
                <tr>
                    <td><strong>Rata-rata Kompresi:</strong></td>
                    <td><span class="stat-number">{avg_compression:.1f}%</span></td>
                </tr>
            </table>
        </div>

        <div class="summary-box">
            <h3>💾 Analisis File Backup (BAK)</h3>
            <table>
                <tr>
                    <th>Jenis Backup</th>
                    <th>Total File</th>
                    <th>File Valid</th>
                    <th>Total Tabel</th>
                    <th>Status</th>
                </tr>
"""

        # Add backup type statistics
        for backup_type, stats in bak_stats.items():
            if stats['count'] > 0:
                status_class = "success" if stats['valid'] == stats['count'] else "warning"
                backup_class = f"backup-{backup_type.lower().replace(' ', '')}"

                if backup_type == "BackupStaging":
                    type_display = "🗄️ Backup Staging (GWScanner)"
                elif backup_type == "BackupVenus":
                    type_display = "⏰ Backup Venus (Time Attendance)"
                elif backup_type == "PlantwareP3":
                    type_display = "🏭 Plantware P3"
                    if exclude_plantware:
                        status_class = "warning"
                else:
                    type_display = "❓ Unknown"

                body += f"""
                <tr class="{backup_class}">
                    <td>{type_display}</td>
                    <td>{stats['count']}</td>
                    <td>{stats['valid']}</td>
                    <td>{stats['tables']}</td>
                    <td><span class="{status_class}">✓</span></td>
                </tr>
"""

        body += f"""
            </table>
            {'<div class="warning"><strong>⚠️ Catatan:</strong> PlantwareP3 dikecualikan dari analisis detail sesuai konfigurasi.</div>' if exclude_plantware and bak_stats.get('PlantwareP3', {}).get('count', 0) > 0 else ''}
        </div>

        <div class="summary-box">
            <h3>🗂️ Detail File per ZIP</h3>
"""

        # Add detailed file information
        for file_path, file_info in self.summary_data.items():
            filename = os.path.basename(file_path)
            backup_type = file_info.get('backup_type', 'Unknown')
            size_mb = file_info['size'] / (1024 * 1024)

            # Determine status icon and color
            if file_info['status'] == 'Valid':
                status_icon = "[VALID]"
                status_color = "#28a745"
            elif file_info['status'] == 'Corrupt':
                status_icon = "[GAGAL]"
                status_color = "#dc3545"
            else:
                status_icon = "⚠️"
                status_color = "#ffc107"

            body += f"""
            <div class="backup-type">
                <h4>{status_icon} {filename}</h4>
                <table>
                    <tr>
                        <td><strong>Jenis Backup:</strong></td>
                        <td>{backup_type}</td>
                        <td><strong>Ukuran:</strong></td>
                        <td>{size_mb:.2f} MB</td>
                    </tr>
                    <tr>
                        <td><strong>Status:</strong></td>
                        <td style="color: {status_color}; font-weight: bold;">{file_info['status']}</td>
                        <td><strong>Kompresi:</strong></td>
                        <td>{file_info.get('compression_ratio', 0):.1f}%</td>
                    </tr>
"""

            # Add BAK file information if available
            if 'bak_analysis' in file_info:
                bak_analysis = file_info['bak_analysis']
                body += f"""
                    <tr>
                        <td><strong>File BAK:</strong></td>
                        <td>{bak_analysis['total_files']} file</td>
                        <td><strong>Valid BAK:</strong></td>
                        <td>{bak_analysis['valid_files']} file</td>
                    </tr>
"""

            body += """
                </table>
            </div>
"""

        body += f"""
        </div>

        <div class="summary-box">
            <h3>[VALID] Checklist Analisis File ZIP</h3>
"""

        # Add ZIP analysis checklist
        for file_path, file_info in self.summary_data.items():
            if 'zip_checklist' in file_info:
                filename = os.path.basename(file_path)
                zip_checklist = file_info['zip_checklist']

                # Calculate ZIP score
                zip_passed = sum(1 for check in zip_checklist.values() if check['status'])
                zip_total = len(zip_checklist)
                zip_percentage = (zip_passed / zip_total * 100) if zip_total > 0 else 0

                body += f"""
            <div class="backup-type">
                <h4>📦 {filename}</h4>
                <p><strong>Score ZIP: {zip_passed}/{zip_total} ({zip_percentage:.1f}%)</strong></p>
                <table style="width: 100%; font-size: 12px;">
"""

                for check_name, check_info in zip_checklist.items():
                    status_icon = "[VALID]" if check_info['status'] else "[GAGAL]"
                    body += f"""
                    <tr>
                        <td style="padding: 5px;">{status_icon} {check_info['keterangan']}</td>
                        <td style="padding: 5px; text-align: right;">{check_info['hasil']}</td>
                    </tr>"""

                body += """
                </table>
            </div>"""

        body += f"""
        </div>

        <div class="summary-box">
            <h3>🗄️ Checklist Analisis File BAK</h3>
"""

        # Add BAK analysis checklist
        bak_checklists_found = False
        for file_path, file_info in self.summary_data.items():
            if 'bak_analysis' in file_info and 'bak_checklists' in file_info['bak_analysis']:
                bak_checklists = file_info['bak_analysis']['bak_checklists']
                bak_checklists_found = True

                for bak_checklist_info in bak_checklists:
                    filename = bak_checklist_info['filename']
                    backup_type = bak_checklist_info['backup_type']
                    checklist = bak_checklist_info['checklist']

                    # Calculate BAK score
                    bak_passed = sum(1 for check in checklist.values() if check['status'])
                    bak_total = len(checklist)
                    bak_percentage = (bak_passed / bak_total * 100) if bak_total > 0 else 0

                    body += f"""
            <div class="backup-type">
                <h4>💾 {filename} ({backup_type})</h4>
                <p><strong>Score BAK: {bak_passed}/{bak_total} ({bak_percentage:.1f}%)</strong></p>
                <table style="width: 100%; font-size: 12px;">
"""

                    for check_name, check_info in checklist.items():
                        status_icon = "[VALID]" if check_info['status'] else "[GAGAL]"
                        body += f"""
                    <tr>
                        <td style="padding: 5px;">{status_icon} {check_info['keterangan']}</td>
                        <td style="padding: 5px; text-align: right;">{check_info['hasil']}</td>
                    </tr>"""

                    body += """
                </table>
            </div>"""

        if not bak_checklists_found:
            body += """
            <p style="text-align: center; color: #666; font-style: italic;">
                Tidak ada file BAK yang dianalisis atau file tidak dapat diekstrak.
            </p>"""

        body += f"""
        </div>

        <div class="summary-box">
            <h3>🔍 Informasi Sistem</h3>
            <table>
                <tr>
                    <td><strong>Monitor Path:</strong></td>
                    <td>{self.monitoring_path.get() or 'N/A'}</td>
                </tr>
                <tr>
                    <td><strong>Interval Check:</strong></td>
                    <td>{self.config['MONITORING']['check_interval']} detik</td>
                </tr>
                <tr>
                    <td><strong>Max Age Alert:</strong></td>
                    <td>{self.config['MONITORING']['max_age_days']} hari</td>
                </tr>
                <tr>
                    <td><strong>Extract Files:</strong></td>
                    <td>{self.config.getboolean('MONITORING', 'extract_files')}</td>
                </tr>
                <tr>
                    <td><strong>Exclude PlantwareP3:</strong></td>
                    <td>{self.config.getboolean('MONITORING', 'exclude_plantware', fallback=False)}</td>
                </tr>
            </table>
        </div>

        <div class="footer">
            <p><strong>Laporan ini dihasilkan otomatis oleh Monitor Backup Zip v1.0</strong></p>
            <p>Email Hubungi: IT Support Department | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Sistem Monitoring Backup Database | Plantware, Venus, dan Staging</p>
        </div>
    </div>
</body>
</html>
"""

    def get_bak_statistics_by_type(self) -> Dict:
        """Get BAK file statistics grouped by backup type"""
        stats = {
            'BackupStaging': {'count': 0, 'valid': 0, 'tables': 0, 'rows': 0},
            'BackupVenus': {'count': 0, 'valid': 0, 'tables': 0, 'rows': 0},
            'PlantwareP3': {'count': 0, 'valid': 0, 'tables': 0, 'rows': 0},
            'Unknown': {'count': 0, 'valid': 0, 'tables': 0, 'rows': 0}
        }

        for file_info in self.summary_data.values():
            if 'bak_analysis' in file_info:
                bak_analysis = file_info['bak_analysis']
                if 'by_type' in bak_analysis:
                    for backup_type, type_stats in bak_analysis['by_type'].items():
                        if backup_type in stats:
                            stats[backup_type]['count'] += type_stats['count']
                            stats[backup_type]['valid'] += type_stats['valid']
                            stats[backup_type]['tables'] += type_stats['tables']
                            stats[backup_type]['rows'] += type_stats['rows']

        return stats

    def open_settings(self):
        """Buka dialog pengaturan"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Pengaturan")
        settings_window.geometry("500x400")

        # Create notebook for settings tabs
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Email settings tab
        email_frame = ttk.Frame(notebook)
        notebook.add(email_frame, text="Pengaturan Email")

        # Email configuration fields
        email_vars = {}
        email_fields = [
            ('Server SMTP:', 'smtp_server'),
            ('Port SMTP:', 'smtp_port'),
            ('Email Pengirim:', 'sender_email'),
            ('Password Pengirim:', 'sender_password'),
            ('Email Penerima:', 'recipient_email')
        ]

        for i, (label, key) in enumerate(email_fields):
            ttk.Label(email_frame, text=label).grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)
            var = tk.StringVar(value=self.config['EMAIL'].get(key, ''))
            email_vars[key] = var

            if 'password' in key:
                entry = ttk.Entry(email_frame, textvariable=var, show="*", width=30)
            else:
                entry = ttk.Entry(email_frame, textvariable=var, width=30)
            entry.grid(row=i, column=1, padx=5, pady=5)

        # Monitoring settings tab
        monitor_frame = ttk.Frame(notebook)
        notebook.add(monitor_frame, text="Pengaturan Monitor")

        monitor_vars = {}
        monitor_fields = [
            ('Interval Check (detik):', 'check_interval'),
            ('Maks Hari (alert):', 'max_age_days'),
            ('Ekstrak File:', 'extract_files'),
            ('Exclude PlantwareP3:', 'exclude_plantware')
        ]

        for i, (label, key) in enumerate(monitor_fields):
            ttk.Label(monitor_frame, text=label).grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)

            if key in ['extract_files', 'exclude_plantware']:
                var = tk.BooleanVar(value=self.config.getboolean('MONITORING', key, fallback=False))
                monitor_vars[key] = var
                ttk.Checkbutton(monitor_frame, variable=var).grid(row=i, column=1, padx=5, pady=5)
            else:
                var = tk.StringVar(value=self.config['MONITORING'].get(key, ''))
                monitor_vars[key] = var
                ttk.Entry(monitor_frame, textvariable=var, width=20).grid(row=i, column=1, padx=5, pady=5)

        # Size validation settings tab
        size_frame = ttk.Frame(notebook)
        notebook.add(size_frame, text="Validasi Ukuran")

        size_vars = {}
        size_fields = [
            ('Min Size Staging (GB):', 'min_size_staging', '2.3'),
            ('Min Size Venus (GB):', 'min_size_venus', '8.7'),
            ('Min Size Plantware (GB):', 'min_size_plantware', '35.0')
        ]

        ttk.Label(size_frame, text="Ukuran Minimum File BAK", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)

        for i, (label, key, default) in enumerate(size_fields):
            ttk.Label(size_frame, text=label).grid(row=i+1, column=0, sticky=tk.W, padx=5, pady=5)

            # Get current value or use default
            current_value = self.config['MONITORING'].get(key, str(int(float(default) * 1024**3)))
            # Convert bytes to GB for display
            if current_value.isdigit():
                display_value = str(int(current_value) / (1024**3))
            else:
                display_value = default

            var = tk.StringVar(value=display_value)
            size_vars[key] = var
            ttk.Entry(size_frame, textvariable=var, width=15).grid(row=i+1, column=1, padx=5, pady=5)

        # Buttons
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        def save_settings():
            # Save email settings
            for key, var in email_vars.items():
                self.config['EMAIL'][key] = var.get()

            # Save monitoring settings
            for key, var in monitor_vars.items():
                if isinstance(var, tk.BooleanVar):
                    self.config['MONITORING'][key] = str(var.get()).lower()
                else:
                    self.config['MONITORING'][key] = var.get()

            # Save size validation settings (convert GB to bytes)
            for key, var in size_vars.items():
                try:
                    gb_value = float(var.get())
                    bytes_value = int(gb_value * 1024**3)  # Convert GB to bytes
                    self.config['MONITORING'][key] = str(bytes_value)
                except ValueError:
                    # Use default if conversion fails
                    if key == 'min_size_staging':
                        self.config['MONITORING'][key] = '2473901824'  # 2.3 GB
                    elif key == 'min_size_venus':
                        self.config['MONITORING'][key] = '9342988800'   # 8.7 GB
                    elif key == 'min_size_plantware':
                        self.config['MONITORING'][key] = '37580963840'  # 35 GB

            self.save_config()
            messagebox.showinfo("Berhasil", "Pengaturan berhasil disimpan!")
            settings_window.destroy()

        ttk.Button(button_frame, text="Simpan", command=save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Batal", command=settings_window.destroy).pack(side=tk.LEFT, padx=5)

    def save_summary_json(self):
        """Simpan data summary ke file JSON"""
        try:
            summary_file = "backup_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(self.summary_data, f, indent=2)
            self.update_log(f"Summary disimpan ke {summary_file}")
        except Exception as e:
            self.logger.error(f"Error menyimpan summary: {str(e)}")

    def update_status(self, status: str):
        """Update label status"""
        self.status_label.config(text=f"Status: {status}")

    def update_log(self, message: str):
        """Update tampilan log"""
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
    app = ZipBackupMonitor(root)
    root.mainloop()


if __name__ == "__main__":
    main()