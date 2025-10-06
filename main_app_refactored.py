#!/usr/bin/env python3
"""
Backup Folder Monitor GUI
GUI untuk monitoring folder backup yang menampilkan list ZIP file terbaru
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
import zipfile
import json
import subprocess
from datetime import datetime
from pathlib import Path
import sys

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from zip_metadata_viewer import ZipMetadataViewer
from enhanced_database_validator import EnhancedDatabaseValidator
from tape_file_analyzer import TapeFileAnalyzer
from date_extraction_micro_feature import DateExtractionMicroFeature
from email_notifier import EmailNotifier
from bak_metadata_analyzer import BAKMetadataAnalyzer

class BackupFolderMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Backup Folder Monitor")
        self.root.geometry("1200x800")

        # Initialize components
        self.zip_viewer = ZipMetadataViewer()
        self.db_validator = EnhancedDatabaseValidator()
        self.tape_analyzer = TapeFileAnalyzer()
        self.date_extractor = DateExtractionMicroFeature()
        self.email_notifier = EmailNotifier()
        self.bak_analyzer = BAKMetadataAnalyzer()

        # Variables
        self.folder_path = tk.StringVar()
        self.current_zip_files = []
        self.selected_zip_index = None

        # Email configuration variables
        self.sender_email_var = tk.StringVar()
        self.sender_password_var = tk.StringVar()
        self.receiver_email_var = tk.StringVar()

        # Load email configuration
        self.load_email_config()

        # Style configuration
        self.setup_styles()

        # Create GUI
        self.create_widgets()

        # Load default folder
        self.load_default_folder()

    def setup_styles(self):
        """Setup ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure styles
        style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 10, 'bold'))
        style.configure('Action.TButton', font=('Arial', 9, 'bold'))

    def create_widgets(self):
        """Create main GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Left panel
        left_frame = ttk.LabelFrame(main_frame, text="Folder & Files", padding="10")
        left_frame.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(2, weight=1)

        # Folder selection
        folder_frame = ttk.Frame(left_frame)
        folder_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        folder_frame.columnconfigure(0, weight=1)

        ttk.Label(folder_frame, text="Backup Folder:", style='Header.TLabel').grid(row=0, column=0, sticky=tk.W)

        path_frame = ttk.Frame(folder_frame)
        path_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        path_frame.columnconfigure(0, weight=1)

        self.path_entry = ttk.Entry(path_frame, textvariable=self.folder_path, state='readonly')
        self.path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        ttk.Button(path_frame, text="Browse", command=self.browse_folder).grid(row=0, column=1)

        # Refresh button
        ttk.Button(left_frame, text="🔄 Refresh", command=self.refresh_files).grid(row=1, column=0, pady=(0, 10))

        # ZIP files list
        ttk.Label(left_frame, text="ZIP Files:", style='Header.TLabel').grid(row=2, column=0, sticky=tk.W)

        # Listbox with scrollbar
        list_frame = ttk.Frame(left_frame)
        list_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.zip_listbox = tk.Listbox(list_frame, height=15)
        self.zip_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.zip_listbox.bind('<<ListboxSelect>>', self.on_zip_select)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.zip_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.zip_listbox.configure(yscrollcommand=scrollbar.set)

        # Right panel
        right_frame = ttk.LabelFrame(main_frame, text="Actions & Details", padding="10")
        right_frame.grid(row=0, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)

        # Email Configuration Section
        email_frame = ttk.LabelFrame(right_frame, text="Email Configuration", padding="10")
        email_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        email_frame.columnconfigure(1, weight=1)
        email_frame.columnconfigure(2, weight=1)

        # Email configuration fields
        ttk.Label(email_frame, text="Sender Email:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(email_frame, textvariable=self.sender_email_var, show="*").grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))

        ttk.Label(email_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(email_frame, textvariable=self.sender_password_var, show="*").grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 5))

        ttk.Label(email_frame, text="Receiver:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(email_frame, textvariable=self.receiver_email_var).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(0, 5))

        # Email buttons
        email_btn_frame = ttk.Frame(email_frame)
        email_btn_frame.grid(row=3, column=0, columnspan=3, pady=(10, 0))

        ttk.Button(email_btn_frame, text="Test Connection", command=self.test_email_connection).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(email_btn_frame, text="Save Config", command=self.save_email_config).pack(side=tk.LEFT, padx=(0, 5))

        # Action buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)

        # Row 1: Main action buttons
        ttk.Button(button_frame, text="Check ZIP Integrity",
                  command=self.check_zip_integrity, style='Action.TButton').grid(row=0, column=0, padx=2, pady=2, sticky=(tk.W, tk.E))
        ttk.Button(button_frame, text="Extract Info",
                  command=self.extract_zip_info, style='Action.TButton').grid(row=0, column=1, padx=2, pady=2, sticky=(tk.W, tk.E))
        ttk.Button(button_frame, text="Send Test Notification",
                  command=self.send_test_notification, style='Action.TButton').grid(row=0, column=2, padx=2, pady=2, sticky=(tk.W, tk.E))

        # Row 2: Analysis buttons
        ttk.Button(button_frame, text="Analyze ZIP Metadata",
                  command=self.analyze_zip_metadata, style='Action.TButton').grid(row=1, column=0, padx=2, pady=2, sticky=(tk.W, tk.E))
        ttk.Button(button_frame, text="Analyze BAK Files",
                  command=self.analyze_bak_files, style='Action.TButton').grid(row=1, column=1, padx=2, pady=2, sticky=(tk.W, tk.E))
        ttk.Button(button_frame, text="Send Backup Report",
                  command=self.send_backup_report, style='Action.TButton').grid(row=1, column=2, padx=2, pady=2, sticky=(tk.W, tk.E))

        # Details text area
        self.details_text = scrolledtext.ScrolledText(right_frame, height=20, wrap=tk.WORD)
        self.details_text.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(1, weight=1)

        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, padx=(0, 5))
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.grid(row=0, column=1, sticky=tk.W)

        # Progress bar
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.grid(row=0, column=2, padx=(10, 0))

    def load_email_config(self):
        """Load email configuration from config file"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.ini')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        if 'sender_email' in line:
                            self.sender_email_var.set(line.split('=')[1].strip())
                        elif 'sender_password' in line:
                            self.sender_password_var.set(line.split('=')[1].strip())
                        elif 'receiver_email' in line:
                            self.receiver_email_var.set(line.split('=')[1].strip())
        except Exception as e:
            print(f"Error loading email config: {e}")

    def save_email_config(self):
        """Save email configuration to config file"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.ini')
            os.makedirs(os.path.dirname(config_path), exist_ok=True)

            with open(config_path, 'w') as f:
                f.write("[EMAIL]\n")
                f.write(f"sender_email = {self.sender_email_var.get()}\n")
                f.write(f"sender_password = {self.sender_password_var.get()}\n")
                f.write(f"receiver_email = {self.receiver_email_var.get()}\n")
                f.write(f"smtp_server = smtp.gmail.com\n")
                f.write(f"smtp_port = 587\n\n")
                f.write("[NOTIFICATION]\n")
                f.write(f"subject = Backup Monitoring Report\n")
                f.write(f"check_interval = 3600\n")

            messagebox.showinfo("Success", "Email configuration saved successfully!")
            self.update_status("Email configuration saved")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save email configuration: {str(e)}")

    def test_email_connection(self):
        """Test email connection configuration"""
        def test_connection():
            try:
                self.progress.start()
                self.update_status("Testing email connection...")

                # Update notifier with current values
                self.email_notifier.sender_email = self.sender_email_var.get()
                self.email_notifier.sender_password = self.sender_password_var.get()
                self.email_notifier.receiver_email = self.receiver_email_var.get()

                success, message = self.email_notifier.send_notification(
                    subject="Test Connection",
                    message="This is a test email to verify connection settings."
                )

                if success:
                    self.update_status("Email connection successful")
                    messagebox.showinfo("Success", "Email connection test successful!")
                else:
                    self.update_status("Email connection failed")
                    messagebox.showerror("Error", f"Email connection failed: {message}")

            except Exception as e:
                self.update_status("Email connection test failed")
                messagebox.showerror("Error", f"Connection test failed: {str(e)}")
            finally:
                self.progress.stop()

        threading.Thread(target=test_connection, daemon=True).start()

    def send_test_notification(self):
        """Send test notification"""
        def send_notification():
            try:
                self.progress.start()
                self.update_status("Sending test notification...")

                # Update notifier with current values
                self.email_notifier.sender_email = self.sender_email_var.get()
                self.email_notifier.sender_password = self.sender_password_var.get()
                self.email_notifier.receiver_email = self.receiver_email_var.get()

                backup_info = {
                    'filename': os.path.basename(self.current_zip_files[self.selected_zip_index]) if self.selected_zip_index is not None else "test_backup.zip",
                    'size': 125.5,
                    'backup_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'Test Mode',
                    'query_results': {
                        'Gwscannerdata': '3,820,963 records',
                        'Ffbscannerdata': '4,273,020 records'
                    },
                    'errors': []
                }

                success, message = self.email_notifier.send_backup_report(backup_info)

                if success:
                    self.update_status("Test notification sent")
                    messagebox.showinfo("Success", "Test notification sent successfully!")
                else:
                    self.update_status("Failed to send notification")
                    messagebox.showerror("Error", f"Failed to send notification: {message}")

            except Exception as e:
                self.update_status("Notification failed")
                messagebox.showerror("Error", f"Notification failed: {str(e)}")
            finally:
                self.progress.stop()

        threading.Thread(target=send_notification, daemon=True).start()

    def send_alert_test(self):
        """Send test alert"""
        def send_alert():
            try:
                self.progress.start()
                self.update_status("Sending test alert...")

                # Update notifier with current values
                self.email_notifier.sender_email = self.sender_email_var.get()
                self.email_notifier.sender_password = self.sender_password_var.get()
                self.email_notifier.receiver_email = self.receiver_email_var.get()

                success, message = self.email_notifier.send_alert(
                    "Test Alert",
                    "This is a test alert to verify alert notification functionality."
                )

                if success:
                    self.update_status("Test alert sent")
                    messagebox.showinfo("Success", "Test alert sent successfully!")
                else:
                    self.update_status("Failed to send alert")
                    messagebox.showerror("Error", f"Failed to send alert: {message}")

            except Exception as e:
                self.update_status("Alert test failed")
                messagebox.showerror("Error", f"Alert test failed: {str(e)}")
            finally:
                self.progress.stop()

        threading.Thread(target=send_alert, daemon=True).start()

    def analyze_zip_metadata(self):
        """Analyze ZIP file metadata"""
        if not self.selected_zip_index:
            messagebox.showwarning("Warning", "Please select a ZIP file first.")
            return

        zip_path = self.current_zip_files[self.selected_zip_index]
        self.update_status("Analyzing ZIP metadata...")
        self.progress.start()

        # Run in background thread
        threading.Thread(target=self._analyze_zip_metadata_thread, args=(zip_path,), daemon=True).start()

    def _analyze_zip_metadata_thread(self, zip_path):
        """Background thread for ZIP metadata analysis"""
        try:
            def progress_callback(message):
                self.root.after(0, self._update_progress_details, message)

            progress_callback("Starting ZIP metadata analysis...")

            # Analyze ZIP file metadata
            progress_callback("Analyzing ZIP file integrity...")
            zip_integrity = self.zip_viewer.check_zip_integrity(zip_path)

            progress_callback("Extracting ZIP metadata...")
            zip_metadata = self.zip_viewer.extract_zip_metadata(zip_path)

            # Analyze backup files within ZIP
            progress_callback("Analyzing backup files...")
            backup_analysis = self._analyze_backup_files(zip_path, zip_metadata, progress_callback)

            # Generate comprehensive report
            progress_callback("Generating analysis report...")
            analysis_result = {
                'zip_file': os.path.basename(zip_path),
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'zip_integrity': zip_integrity,
                'zip_metadata': zip_metadata,
                'backup_analysis': backup_analysis,
                'summary': self._generate_metadata_summary(zip_integrity, zip_metadata, backup_analysis)
            }

            self.root.after(0, self._show_zip_analysis_results, analysis_result)

        except Exception as e:
            self.root.after(0, self._show_error, f"ZIP metadata analysis failed: {str(e)}")

    def _analyze_backup_files(self, zip_path, zip_metadata, progress_callback):
        """Analyze backup files within ZIP"""
        backup_analysis = {
            'bak_files': [],
            'total_size': 0,
            'database_info': {},
            'file_analysis': {}
        }

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Find .bak files
                bak_files = [f for f in zip_ref.namelist() if f.lower().endswith('.bak')]

                for bak_file in bak_files:
                    progress_callback(f"Analyzing {bak_file}...")

                    # Get file info
                    file_info = zip_ref.getinfo(bak_file)
                    bak_analysis = {
                        'filename': bak_file,
                        'size': file_info.file_size,
                        'compressed_size': file_info.compress_size,
                        'compression_ratio': (1 - file_info.compress_size / file_info.file_size) * 100 if file_info.file_size > 0 else 0,
                        'modified': datetime(*file_info.date_time).strftime('%Y-%m-%d %H:%M:%S')
                    }

                    # Analyze database type from filename
                    db_type = self._identify_database_type(bak_file)
                    bak_analysis['database_type'] = db_type

                    backup_analysis['bak_files'].append(bak_analysis)
                    backup_analysis['total_size'] += file_info.file_size

                    # Store database info
                    if db_type:
                        backup_analysis['database_info'][db_type] = bak_analysis.copy()
                        backup_analysis['database_info'][db_type]['estimated_tables'] = self._estimate_tables_for_db(db_type)
                        backup_analysis['database_info'][db_type]['estimated_records'] = self._estimate_records_for_db(db_type)

        except Exception as e:
            backup_analysis['error'] = str(e)

        return backup_analysis

    def _identify_database_type(self, filename):
        """Identify database type from filename"""
        filename_lower = filename.lower()
        if 'staging' in filename_lower:
            return 'staging_PTRJ_iFES_Plantware'
        elif 'ptrj' in filename_lower:
            return 'db_ptrj'
        elif 'venus' in filename_lower or 'hr' in filename_lower:
            return 'VenusHR14'
        else:
            return 'unknown'

    def _estimate_tables_for_db(self, db_type):
        """Estimate number of tables for database type"""
        estimates = {
            'staging_PTRJ_iFES_Plantware': 29,
            'db_ptrj': 25,
            'VenusHR14': 35,
            'unknown': 20
        }
        return estimates.get(db_type, 20)

    def _estimate_records_for_db(self, db_type):
        """Estimate number of records for database type"""
        estimates = {
            'staging_PTRJ_iFES_Plantware': {'Gwscannerdata': 3800000, 'Ffbscannerdata': 4200000},
            'db_ptrj': {'Gwscannerdata': 3500000, 'Ffbscannerdata': 4000000},
            'VenusHR14': {'Employee_Info': 5000, 'TransactionIntegration': 100000},
            'unknown': {'estimated_total': 1000000}
        }
        return estimates.get(db_type, {'estimated_total': 1000000})

    def _generate_metadata_summary(self, zip_integrity, zip_metadata, backup_analysis):
        """Generate metadata analysis summary"""
        summary = {
            'total_bak_files': len(backup_analysis.get('bak_files', [])),
            'total_size_mb': backup_analysis.get('total_size', 0) / (1024 * 1024),
            'zip_valid': zip_integrity.get('is_valid', False),
            'databases_found': list(backup_analysis.get('database_info', {}).keys()),
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'compression_efficiency': 0
        }

        # Calculate compression efficiency
        if backup_analysis.get('bak_files'):
            total_original = sum(f['size'] for f in backup_analysis['bak_files'])
            total_compressed = sum(f['compressed_size'] for f in backup_analysis['bak_files'])
            summary['compression_efficiency'] = (1 - total_compressed / total_original) * 100 if total_original > 0 else 0

        return summary

    def _show_zip_analysis_results(self, result):
        """Show ZIP analysis results"""
        self.progress.stop()

        details = "\n" + "=" * 60 + "\n"
        details += "ZIP METADATA ANALYSIS RESULTS\n"
        details += "=" * 60 + "\n\n"

        # ZIP File Info
        details += f"ZIP File: {result['zip_file']}\n"
        details += f"Analysis Time: {result['analysis_time']}\n\n"

        # ZIP Integrity
        integrity = result['zip_integrity']
        details += "ZIP INTEGRITY:\n"
        details += f"   Status: {'✅ Valid' if integrity.get('is_valid') else '❌ Invalid'}\n"
        details += f"   Total Files: {integrity.get('total_files', 0)}\n"
        details += f"   ZIP Size: {integrity.get('total_size', 0) / (1024*1024):.2f} MB\n\n"

        # Backup Analysis
        backup_analysis = result['backup_analysis']
        details += "BACKUP FILES ANALYSIS:\n"
        details += f"   BAK Files Found: {len(backup_analysis.get('bak_files', []))}\n"
        details += f"   Total Size: {backup_analysis.get('total_size', 0) / (1024*1024):.2f} MB\n\n"

        for bak_file in backup_analysis.get('bak_files', []):
            details += f"   📦 {bak_file['filename']}:\n"
            details += f"      Size: {bak_file['size'] / (1024*1024):.2f} MB\n"
            details += f"      Compressed: {bak_file['compressed_size'] / (1024*1024):.2f} MB\n"
            details += f"      Compression: {bak_file['compression_ratio']:.1f}%\n"
            details += f"      Database Type: {bak_file['database_type']}\n"
            details += f"      Modified: {bak_file['modified']}\n\n"

        # Database Information
        db_info = backup_analysis.get('database_info', {})
        if db_info:
            details += "DATABASE INFORMATION:\n"
            for db_type, info in db_info.items():
                details += f"   🗄️  {db_type}:\n"
                details += f"      Estimated Tables: {info.get('estimated_tables', 0)}\n"
                if info.get('estimated_records'):
                    records = info['estimated_records']
                    if isinstance(records, dict):
                        for table, count in records.items():
                            details += f"      {table}: ~{count:,} records\n"
                    else:
                        details += f"      Estimated Records: ~{records:,}\n"
                details += "\n"

        # Summary
        summary = result['summary']
        details += "SUMMARY:\n"
        details += f"   Total BAK Files: {summary['total_bak_files']}\n"
        details += f"   Total Size: {summary['total_size_mb']:.2f} MB\n"
        details += f"   ZIP Valid: {'Yes' if summary['zip_valid'] else 'No'}\n"
        details += f"   Databases Found: {', '.join(summary['databases_found'])}\n"
        details += f"   Compression Efficiency: {summary['compression_efficiency']:.1f}%\n"

        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, details)
        self.update_status("ZIP metadata analysis completed")

    def analyze_bak_files(self):
        """Analyze BAK files within ZIP without SQL Server connection"""
        if not self.selected_zip_index:
            messagebox.showwarning("Warning", "Please select a ZIP file first.")
            return

        zip_path = self.current_zip_files[self.selected_zip_index]
        self.update_status("Analyzing BAK files...")
        self.progress.start()

        # Run in background thread
        threading.Thread(target=self._analyze_bak_files_thread, args=(zip_path,), daemon=True).start()

    def _analyze_bak_files_thread(self, zip_path):
        """Background thread for BAK files analysis"""
        try:
            def progress_callback(message):
                self.root.after(0, self._update_progress_details, message)

            progress_callback("Starting BAK files analysis...")

            # Open ZIP file
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Find BAK files
                bak_files = [f for f in zip_ref.namelist() if f.lower().endswith('.bak')]

                if not bak_files:
                    progress_callback("No BAK files found in ZIP")
                    self.root.after(0, lambda: self._show_error("No BAK files found in the selected ZIP"))
                    return

                progress_callback(f"Found {len(bak_files)} BAK files")

                # Analyze each BAK file
                bak_analyses = []
                for i, bak_file in enumerate(bak_files):
                    progress_callback(f"Analyzing {bak_file} ({i+1}/{len(bak_files)})...")

                    try:
                        # Analyze BAK file using the new analyzer
                        bak_analysis = self.bak_analyzer.analyze_bak_file(bak_file, zip_ref)
                        bak_analyses.append(bak_analysis)

                    except Exception as e:
                        bak_analyses.append({
                            'filename': bak_file,
                            'error': str(e),
                            'analysis_status': 'failed'
                        })

                # Generate comprehensive report
                progress_callback("Generating BAK analysis report...")
                analysis_result = {
                    'zip_file': os.path.basename(zip_path),
                    'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'total_bak_files': len(bak_files),
                    'bak_analyses': bak_analyses,
                    'summary': self._generate_bak_analysis_summary(bak_analyses)
                }

            self.root.after(0, self._show_bak_analysis_results, analysis_result)

        except Exception as e:
            self.root.after(0, self._show_error, f"BAK files analysis failed: {str(e)}")

    def _generate_bak_analysis_summary(self, bak_analyses):
        """Generate summary from BAK analyses"""
        summary = {
            'total_files': len(bak_analyses),
            'valid_files': 0,
            'corrupted_files': 0,
            'total_size_mb': 0,
            'databases_found': set(),
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'recommendations': []
        }

        for analysis in bak_analyses:
            # Count valid vs corrupted
            if analysis.get('validation', {}).get('is_valid_bak', False):
                summary['valid_files'] += 1
            else:
                summary['corrupted_files'] += 1

            # Sum file sizes
            summary['total_size_mb'] += analysis.get('file_size', 0) / (1024 * 1024)

            # Collect database names
            db_name = analysis.get('database_info', {}).get('database_name')
            if db_name:
                summary['databases_found'].add(db_name)

        # Convert set to list for JSON serialization
        summary['databases_found'] = list(summary['databases_found'])

        # Generate recommendations
        if summary['corrupted_files'] > 0:
            summary['recommendations'].append(f"⚠️ {summary['corrupted_files']} corrupted BAK files detected")

        if summary['valid_files'] == 0:
            summary['recommendations'].append("⚠️ No valid BAK files found")

        if summary['valid_files'] > 0:
            summary['recommendations'].append(f"✅ {summary['valid_files']} valid BAK files ready for restore")

        return summary

    def _show_bak_analysis_results(self, result):
        """Show BAK analysis results"""
        self.progress.stop()

        details = "\n" + "=" * 60 + "\n"
        details += "BAK FILES DEEP ANALYSIS RESULTS\n"
        details += "=" * 60 + "\n\n"

        # Basic Info
        details += f"ZIP File: {result['zip_file']}\n"
        details += f"Analysis Time: {result['analysis_time']}\n"
        details += f"Total BAK Files: {result['total_bak_files']}\n\n"

        # Summary
        summary = result['summary']
        details += "SUMMARY:\n"
        details += f"   Valid Files: {summary['valid_files']}\n"
        details += f"   Corrupted Files: {summary['corrupted_files']}\n"
        details += f"   Total Size: {summary['total_size_mb']:.2f} MB\n"
        details += f"   Databases Found: {', '.join(summary['databases_found']) if summary['databases_found'] else 'None'}\n\n"

        # Detailed Analysis
        details += "DETAILED BAK ANALYSIS:\n"
        for i, bak_analysis in enumerate(result['bak_analyses'], 1):
            details += f"\n{i}. {bak_analysis.get('filename', 'Unknown')}\n"
            details += f"   " + "-" * 50 + "\n"

            if bak_analysis.get('error'):
                details += f"   ❌ Error: {bak_analysis['error']}\n"
                continue

            # File info
            details += f"   📁 File Size: {bak_analysis.get('file_size', 0) / (1024*1024):.2f} MB\n"

            # Database info
            db_info = bak_analysis.get('database_info', {})
            if db_info:
                details += f"   🗄️  Database: {db_info.get('database_name', 'Unknown')}\n"
                if db_info.get('server_name'):
                    details += f"   🖥️  Server: {db_info['server_name']}\n"
                if db_info.get('backup_date'):
                    details += f"   📅 Backup Date: {db_info['backup_date']}\n"
                if db_info.get('backup_type'):
                    details += f"   📋 Backup Type: {db_info['backup_type']}\n"
                if db_info.get('database_version'):
                    details += f"   🔧 Version: {db_info['database_version']}\n"
                details += f"   📊 Estimated Tables: {db_info.get('estimated_tables', 0)}\n"

            # File structure
            structure = bak_analysis.get('file_structure', {})
            if structure:
                details += f"   🏗️  Structure:\n"
                details += f"      Data Blocks: {structure.get('data_blocks', 0)}\n"
                details += f"      Page Count: {structure.get('page_count', 0):,}\n"
                details += f"      Backup Sets: ~{structure.get('estimated_backup_sets', 0)}\n"

            # Validation
            validation = bak_analysis.get('validation', {})
            details += f"   ✅ Validation:\n"
            details += f"      Valid BAK: {'Yes' if validation.get('is_valid_bak', False) else 'No'}\n"
            details += f"      Corruption: {'Yes' if validation.get('corruption_detected', False) else 'No'}\n"
            details += f"      Integrity: {validation.get('file完整性', 'unknown')}\n"

            if validation.get('warnings'):
                details += f"   ⚠️  Warnings ({len(validation['warnings'])}):\n"
                for warning in validation['warnings'][:3]:  # Show first 3 warnings
                    details += f"      - {warning}\n"
                if len(validation['warnings']) > 3:
                    details += f"      ... and {len(validation['warnings']) - 3} more\n"

        # Recommendations
        if summary.get('recommendations'):
            details += f"\nRECOMMENDATIONS:\n"
            for rec in summary['recommendations']:
                details += f"   {rec}\n"

        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, details)
        self.update_status("BAK files analysis completed")

    def send_backup_report(self):
        """Send backup report via email"""
        if not self.selected_zip_index:
            messagebox.showwarning("Warning", "Please select a ZIP file first.")
            return

        zip_path = self.current_zip_files[self.selected_zip_index]
        self.update_status("Sending backup report...")
        self.progress.start()

        # Run in background thread
        threading.Thread(target=self._send_backup_report_thread, args=(zip_path,), daemon=True).start()

    def _send_backup_report_thread(self, zip_path):
        """Background thread for sending backup report"""
        try:
            def progress_callback(message):
                self.root.after(0, self._update_progress_details, message)

            progress_callback("Generating backup report...")

            # Analyze backup metadata
            analysis_result = self._analyze_backup_for_report(zip_path)

            # Send email report
            progress_callback("Sending email report...")

            # Update notifier with current values
            self.email_notifier.sender_email = self.sender_email_var.get()
            self.email_notifier.sender_password = self.sender_password_var.get()
            self.email_notifier.receiver_email = self.receiver_email_var.get()

            success, message = self.email_notifier.send_backup_report(analysis_result)

            if success:
                progress_callback("Backup report sent successfully!")
                self.root.after(0, lambda: messagebox.showinfo("Success", "Backup report sent successfully!"))
            else:
                progress_callback(f"Failed to send report: {message}")
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to send report: {message}"))

        except Exception as e:
            error_msg = f"Failed to send backup report: {str(e)}"
            progress_callback(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
        finally:
            self.root.after(0, self.progress.stop)

    def _analyze_backup_for_report(self, zip_path):
        """Analyze backup file for email report using deep BAK analysis"""
        try:
            # Get ZIP file info
            stat = os.stat(zip_path)
            file_size_mb = stat.st_size / (1024 * 1024)
            mod_time = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')

            # Analyze ZIP integrity
            zip_integrity = self.zip_viewer.check_zip_integrity(zip_path)

            # Deep BAK analysis
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                bak_files = [f for f in zip_ref.namelist() if f.lower().endswith('.bak')]

                bak_analyses = []
                for bak_file in bak_files:
                    try:
                        bak_analysis = self.bak_analyzer.analyze_bak_file(bak_file, zip_ref)
                        bak_analyses.append(bak_analysis)
                    except Exception as e:
                        bak_analyses.append({
                            'filename': bak_file,
                            'error': str(e),
                            'analysis_status': 'failed'
                        })

            # Prepare comprehensive report data
            report_data = {
                'filename': os.path.basename(zip_path),
                'size': round(file_size_mb, 2),
                'backup_date': mod_time,
                'status': 'Valid' if zip_integrity.get('is_valid') else 'Invalid',
                'query_results': {
                    'ZIP Integrity': f"{'Valid' if zip_integrity.get('is_valid') else 'Invalid'} ({zip_integrity.get('total_files', 0)} files)",
                    'BAK Files Found': f"{len(bak_files)} files",
                    'ZIP Size': f"{file_size_mb:.2f} MB",
                    'Analysis Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                'errors': []
            }

            # Analyze BAK files results
            valid_bak_files = 0
            corrupted_bak_files = 0
            total_bak_size = 0
            databases_found = set()

            for bak_analysis in bak_analyses:
                if bak_analysis.get('validation', {}).get('is_valid_bak', False):
                    valid_bak_files += 1
                else:
                    corrupted_bak_files += 1

                total_bak_size += bak_analysis.get('file_size', 0)

                # Extract database info
                db_name = bak_analysis.get('database_info', {}).get('database_name')
                if db_name:
                    databases_found.add(db_name)

                # Add detailed info for each BAK file
                bak_filename = bak_analysis.get('filename', 'Unknown')
                db_info = bak_analysis.get('database_info', {})

                # File validation status
                validation = bak_analysis.get('validation', {})
                if validation.get('is_valid_bak', False):
                    report_data['query_results'][f"{bak_filename} - Status"] = "✅ Valid"
                else:
                    report_data['query_results'][f"{bak_filename} - Status"] = "❌ Invalid"

                # Database information
                if db_name:
                    report_data['query_results'][f"{bak_filename} - Database"] = db_name

                if db_info.get('backup_date'):
                    report_data['query_results'][f"{bak_filename} - Backup Date"] = db_info['backup_date']

                if db_info.get('backup_type'):
                    report_data['query_results'][f"{bak_filename} - Type"] = db_info['backup_type']

                if db_info.get('estimated_tables'):
                    report_data['query_results'][f"{bak_filename} - Tables"] = f"~{db_info['estimated_tables']} tables"

                # File size
                bak_size_mb = bak_analysis.get('file_size', 0) / (1024 * 1024)
                report_data['query_results'][f"{bak_filename} - Size"] = f"{bak_size_mb:.2f} MB"

                # Integrity status
                integrity_status = bak_analysis.get('validation', {}).get('file完整性', 'unknown')
                report_data['query_results'][f"{bak_filename} - Integrity"] = integrity_status

                # Warnings if any
                warnings = validation.get('warnings', [])
                if warnings:
                    report_data['query_results'][f"{bak_filename} - Warnings"] = f"{len(warnings)} warning(s)"

            # Summary statistics
            report_data['query_results']['Valid BAK Files'] = f"{valid_bak_files} files"
            report_data['query_results']['Corrupted BAK Files'] = f"{corrupted_bak_files} files"
            report_data['query_results']['Total BAK Size'] = f"{total_bak_size / (1024*1024):.2f} MB"
            report_data['query_results']['Databases Found'] = ', '.join(databases_found) if databases_found else 'None'

            # Add compression ratio
            if total_bak_size > 0 and file_size_mb > 0:
                compression_ratio = (1 - total_bak_size / (file_size_mb * 1024 * 1024)) * 100
                report_data['query_results']['Compression Ratio'] = f"{compression_ratio:.1f}%"

            # Overall health assessment
            if corrupted_bak_files == 0 and valid_bak_files > 0:
                report_data['query_results']['Overall Health'] = "✅ Excellent"
            elif corrupted_bak_files <= valid_bak_files:
                report_data['query_results']['Overall Health'] = "⚠️ Good (some issues)"
            else:
                report_data['query_results']['Overall Health'] = "❌ Poor"

            return report_data

        except Exception as e:
            return {
                'filename': os.path.basename(zip_path),
                'size': 0,
                'backup_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'Error',
                'query_results': {},
                'errors': [f"Deep analysis failed: {str(e)}"]
            }

    def load_default_folder(self):
        """Load default backup folder"""
        default_path = "D:\\Gawean Rebinmas\\App_Auto_Backup\\Backup"
        if os.path.exists(default_path):
            self.folder_path.set(default_path)
            self.refresh_files()

    def browse_folder(self):
        """Browse for backup folder"""
        folder = filedialog.askdirectory(title="Select Backup Folder")
        if folder:
            self.folder_path.set(folder)
            self.refresh_files()

    def refresh_files(self):
        """Refresh ZIP files list"""
        folder = self.folder_path.get()
        if not folder or not os.path.exists(folder):
            self.zip_listbox.delete(0, tk.END)
            self.current_zip_files = []
            return

        try:
            # Get all ZIP files
            zip_files = []
            for file in os.listdir(folder):
                if file.lower().endswith('.zip'):
                    file_path = os.path.join(folder, file)
                    stat = os.stat(file_path)
                    zip_files.append({
                        'name': file,
                        'path': file_path,
                        'size': stat.st_size,
                        'modified': stat.st_mtime
                    })

            # Sort by modification time (newest first)
            zip_files.sort(key=lambda x: x['modified'], reverse=True)

            # Update listbox
            self.zip_listbox.delete(0, tk.END)
            self.current_zip_files = []

            for zip_info in zip_files:
                # Format display text
                size_mb = zip_info['size'] / (1024 * 1024)
                mod_time = datetime.fromtimestamp(zip_info['modified']).strftime('%Y-%m-%d %H:%M')
                display_text = f"{zip_info['name']} ({size_mb:.1f} MB) - {mod_time}"

                self.zip_listbox.insert(tk.END, display_text)
                self.current_zip_files.append(zip_info['path'])

            self.update_status(f"Found {len(zip_files)} ZIP files")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh files: {str(e)}")

    def on_zip_select(self, event):
        """Handle ZIP file selection"""
        selection = self.zip_listbox.curselection()
        if selection:
            self.selected_zip_index = selection[0]
            zip_path = self.current_zip_files[self.selected_zip_index]
            self.update_status(f"Selected: {os.path.basename(zip_path)}")

    def update_status(self, message):
        """Update status label"""
        self.status_label.config(text=message)
        self.root.update_idletasks()

    def check_zip_integrity(self):
        """Check ZIP file integrity"""
        if not self.selected_zip_index:
            messagebox.showwarning("Warning", "Please select a ZIP file first.")
            return

        zip_path = self.current_zip_files[self.selected_zip_index]
        self.update_status("Checking ZIP integrity...")
        self.progress.start()

        # Run in background thread
        threading.Thread(target=self._check_zip_integrity_thread, args=(zip_path,), daemon=True).start()

    def _check_zip_integrity_thread(self, zip_path):
        """Background thread for ZIP integrity check"""
        try:
            result = self.zip_viewer.check_zip_integrity(zip_path)
            self.root.after(0, self._show_integrity_results, result)
        except Exception as e:
            self.root.after(0, self._show_error, f"Integrity check failed: {str(e)}")

    def _show_integrity_results(self, result):
        """Show ZIP integrity check results"""
        self.progress.stop()

        details = f"ZIP Integrity Check Results\n"
        details += "=" * 50 + "\n\n"
        details += f"File: {os.path.basename(result['file_path'])}\n"
        details += f"Status: {'✅ Valid' if result['is_valid'] else '❌ Invalid'}\n"
        details += f"Total Files: {result['total_files']}\n"
        details += f"Total Size: {result['total_size'] / (1024*1024):.2f} MB\n\n"

        if result['errors']:
            details += "Errors:\n"
            for error in result['errors']:
                details += f"  • {error}\n"
        else:
            details += "No errors found.\n"

        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, details)
        self.update_status("Integrity check complete")

    def extract_zip_info(self):
        """Extract ZIP file information"""
        if not self.selected_zip_index:
            messagebox.showwarning("Warning", "Please select a ZIP file first.")
            return

        zip_path = self.current_zip_files[self.selected_zip_index]
        self.update_status("Extracting ZIP information...")
        self.progress.start()

        # Run in background thread
        threading.Thread(target=self._extract_zip_info_thread, args=(zip_path,), daemon=True).start()

    def _extract_zip_info_thread(self, zip_path):
        """Background thread for ZIP info extraction"""
        try:
            result = self.zip_viewer.extract_zip_metadata(zip_path)
            self.root.after(0, self._show_zip_info_results, result)
        except Exception as e:
            self.root.after(0, self._show_error, f"Info extraction failed: {str(e)}")

    def _show_zip_info_results(self, result):
        """Show ZIP information results"""
        self.progress.stop()

        details = f"ZIP File Information\n"
        details += "=" * 50 + "\n\n"
        details += f"File: {os.path.basename(result['file_path'])}\n"
        details += f"Size: {result['file_size'] / (1024*1024):.2f} MB\n"
        details += f"Created: {result['created_date']}\n"
        details += f"Total Files: {len(result['files'])}\n\n"

        details += "Files in ZIP:\n"
        for file_info in result['files'][:20]:  # Show first 20 files
            details += f"  📄 {file_info['filename']} ({file_info['file_size']} bytes)\n"

        if len(result['files']) > 20:
            details += f"  ... and {len(result['files']) - 20} more files\n"

        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, details)
        self.update_status("ZIP info extraction complete")

    def _update_progress_details(self, message):
        """Update progress details in real-time"""
        current_text = self.details_text.get(1.0, tk.END)
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, f"[{timestamp}] {message}\n\n{current_text}")
        self.root.update_idletasks()

    def _show_error(self, error_message):
        """Show error message"""
        messagebox.showerror("Error", error_message)
        self.update_status("Error occurred")
        self.progress.stop()

def main():
    """Main function"""
    root = tk.Tk()
    app = BackupFolderMonitorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()