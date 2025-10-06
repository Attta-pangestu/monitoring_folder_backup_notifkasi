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
from datetime import datetime
from pathlib import Path
import sys

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from zip_metadata_viewer import ZipMetadataViewer
from enhanced_database_validator import EnhancedDatabaseValidator
from tape_file_analyzer import TapeFileAnalyzer
from date_extraction_micro_feature import DateExtractionMicroFeature
from sql_server_zip_restore import extract_restore_and_analyze, SQLServerZipRestore

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
        self.sql_restore = SQLServerZipRestore()

        # Variables
        self.folder_path = tk.StringVar()
        self.current_zip_files = []
        self.selected_zip_index = None

        # Style configuration
        self.setup_styles()

        # Create GUI
        self.create_widgets()

        # Load default folder
        self.load_default_folder()

    def setup_styles(self):
        """Setup styles untuk GUI"""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure styles
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Section.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Zip.TButton', font=('Arial', 10))
        style.configure('Status.TLabel', font=('Arial', 10))

        # Configure treeview style
        style.configure('Treeview', font=('Arial', 10))
        style.configure('Treeview.Heading', font=('Arial', 10, 'bold'))

    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text="🔍 BACKUP FOLDER MONITOR",
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, pady=(0, 20))

        # Folder Selection Section
        folder_frame = ttk.LabelFrame(main_frame, text="📁 Folder Selection", padding="10")
        folder_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        folder_frame.columnconfigure(1, weight=1)

        ttk.Label(folder_frame, text="Backup Folder:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(folder_frame, textvariable=self.folder_path, width=70).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        ttk.Button(folder_frame, text="Browse", command=self.browse_folder).grid(row=0, column=2, pady=2, padx=(5, 0))
        ttk.Button(folder_frame, text="🔍 Scan", command=self.scan_folder).grid(row=0, column=3, pady=2, padx=(5, 0))

        # Main Content Area
        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)

        # Left Panel - ZIP Files List
        left_frame = ttk.LabelFrame(content_frame, text="📦 ZIP Files", padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)

        # ZIP Files Treeview
        columns = ('Size', 'Created', 'Modified', 'Files')
        self.zip_tree = ttk.Treeview(left_frame, columns=columns, height=15)
        self.zip_tree.heading('#0', text='File Name')
        self.zip_tree.heading('Size', text='Size (MB)')
        self.zip_tree.heading('Created', text='Created')
        self.zip_tree.heading('Modified', text='Modified')
        self.zip_tree.heading('Files', text='Files')

        # Configure column widths
        self.zip_tree.column('#0', width=300, minwidth=200)
        self.zip_tree.column('Size', width=80, minwidth=60)
        self.zip_tree.column('Created', width=150, minwidth=120)
        self.zip_tree.column('Modified', width=150, minwidth=120)
        self.zip_tree.column('Files', width=60, minwidth=50)

        # Scrollbar for treeview
        tree_scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.zip_tree.yview)
        self.zip_tree.configure(yscrollcommand=tree_scroll.set)

        self.zip_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Bind selection event
        self.zip_tree.bind('<<TreeviewSelect>>', self.on_zip_selected)

        # Right Panel - Details
        right_frame = ttk.LabelFrame(content_frame, text="📋 File Details", padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)

        # Action buttons
        action_frame = ttk.Frame(right_frame)
        action_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Button(action_frame, text="🔄 Extract, Restore & Analyze", command=self.extract_and_restore_database).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="🔒 Check ZIP Integrity", command=self.check_zip_integrity).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="📤 Extract Info", command=self.extract_zip_info).pack(side=tk.LEFT, padx=2)

        # Details text
        self.details_text = scrolledtext.ScrolledText(right_frame, height=20, width=50, wrap=tk.WORD)
        self.details_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.details_text.config(font=('Courier', 9))

        # Status Bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

        self.status_label = ttk.Label(status_frame, text="Ready", style='Status.TLabel')
        self.status_label.pack(side=tk.LEFT)

        # Progress bar
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', length=200)
        self.progress.pack(side=tk.RIGHT)

    def load_default_folder(self):
        """Load default backup folder"""
        default_folder = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup"
        if os.path.exists(default_folder):
            self.folder_path.set(default_folder)
            self.scan_folder()
        else:
            # Fallback to test backups
            fallback_folder = "real_test_backups"
            if os.path.exists(fallback_folder):
                self.folder_path.set(fallback_folder)
                self.scan_folder()

    def browse_folder(self):
        """Browse for folder selection"""
        folder_selected = filedialog.askdirectory(title="Select Backup Folder")
        if folder_selected:
            self.folder_path.set(folder_selected)
            self.scan_folder()

    def scan_folder(self):
        """Scan folder for ZIP files"""
        folder = self.folder_path.get()
        if not folder or not os.path.exists(folder):
            messagebox.showerror("Error", "Please select a valid folder!")
            return

        self.update_status(f"Scanning folder: {folder}")
        self.progress.start()

        # Run scan in background thread
        thread = threading.Thread(target=self._scan_folder_thread, args=(folder,))
        thread.daemon = True
        thread.start()

    def _scan_folder_thread(self, folder):
        """Thread function for scanning folder"""
        try:
            # Find ZIP files
            zip_files = self.zip_viewer.find_latest_zip_files(folder)

            # Update GUI in main thread
            self.root.after(0, self._update_zip_list, zip_files)

        except Exception as e:
            self.root.after(0, self._show_error, f"Error scanning folder: {e}")

    def _update_zip_list(self, zip_files):
        """Update ZIP files list in GUI"""
        self.current_zip_files = zip_files
        self.zip_tree.delete(*self.zip_tree.get_children())

        if not zip_files:
            self.update_status("No ZIP files found")
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(tk.END, "No ZIP files found in selected folder.")
            return

        # Add ZIP files to treeview
        for i, zip_info in enumerate(zip_files):
            try:
                with zipfile.ZipFile(zip_info['full_path'], 'r') as zip_ref:
                    file_count = len(zip_ref.namelist())
            except:
                file_count = "ERROR"

            values = (
                f"{zip_info['size_mb']:.2f}",
                zip_info['created_str'],
                zip_info['modified_str'],
                file_count
            )

            self.zip_tree.insert('', 'end', iid=i, text=zip_info['filename'], values=values)

        self.update_status(f"Found {len(zip_files)} ZIP files")
        self.progress.stop()

        # Auto-select first file
        if zip_files:
            self.zip_tree.selection_set(0)
            self.on_zip_selected(None)

    def on_zip_selected(self, event):
        """Handle ZIP file selection"""
        selection = self.zip_tree.selection()
        if selection:
            self.selected_zip_index = int(selection[0])
            self.show_zip_details()

    def show_zip_details(self):
        """Show details of selected ZIP file"""
        if self.selected_zip_index is None or self.selected_zip_index >= len(self.current_zip_files):
            return

        zip_info = self.current_zip_files[self.selected_zip_index]

        # Clear details
        self.details_text.delete(1.0, tk.END)

        # Show basic info
        details = f"📁 File: {zip_info['filename']}\n"
        details += f"📊 Size: {zip_info['size_mb']:.2f} MB ({zip_info['size_bytes']:,} bytes)\n"
        details += f"📅 Created: {zip_info['created_str']}\n"
        details += f"🔄 Modified: {zip_info['modified_str']}\n"
        details += f"🔗 Path: {zip_info['full_path']}\n\n"

        # Try to get ZIP contents
        try:
            with zipfile.ZipFile(zip_info['full_path'], 'r') as zip_ref:
                files_in_zip = zip_ref.namelist()

                details += f"📦 Total Files: {len(files_in_zip)}\n"
                details += f"📋 File List:\n"
                details += "-" * 50 + "\n"

                for i, filename in enumerate(files_in_zip[:20]):  # Show first 20 files
                    details += f"{i+1:3d}. {filename}\n"

                if len(files_in_zip) > 20:
                    details += f"... and {len(files_in_zip) - 20} more files\n"

                # Count .bak files
                bak_files = [f for f in files_in_zip if f.lower().endswith('.bak')]
                if bak_files:
                    details += f"\n🗄️ Database Files (.bak): {len(bak_files)}\n"
                    for bak_file in bak_files:
                        details += f"   • {bak_file}\n"

        except Exception as e:
            details += f"\n❌ Error reading ZIP: {e}\n"

        self.details_text.insert(tk.END, details)

    def analyze_selected_zip(self):
        """Analyze selected ZIP file"""
        if self.selected_zip_index is None:
            messagebox.showwarning("Warning", "Please select a ZIP file first!")
            return

        zip_info = self.current_zip_files[self.selected_zip_index]
        self.update_status(f"Analyzing {zip_info['filename']}...")
        self.progress.start()

        # Run analysis in background thread
        thread = threading.Thread(target=self._analyze_zip_thread, args=(zip_info,))
        thread.daemon = True
        thread.start()

    def _analyze_zip_thread(self, zip_info):
        """Thread function for analyzing ZIP"""
        try:
            # Get detailed contents
            contents = self.zip_viewer.get_zip_contents_detailed(zip_info['full_path'])

            # Update GUI in main thread
            self.root.after(0, self._show_analysis_results, zip_info, contents)

        except Exception as e:
            self.root.after(0, self._show_error, f"Error analyzing ZIP: {e}")

    def _show_analysis_results(self, zip_info, contents):
        """Show analysis results"""
        self.details_text.delete(1.0, tk.END)

        details = f"🔍 ANALYSIS RESULTS: {zip_info['filename']}\n"
        details += "=" * 60 + "\n\n"

        if not contents['success']:
            details += f"❌ Error: {contents['error']}\n"
        else:
            details += f"✅ Analysis successful!\n\n"
            details += f"📦 Total Files: {contents['total_files']}\n"
            details += f"💾 Database Files: {len(contents['bak_files'])}\n\n"

            if contents['bak_files']:
                details += "🗄️ DATABASE FILES:\n"
                details += "-" * 40 + "\n"
                for bak_file in contents['bak_files']:
                    details += f"File: {bak_file['filename']}\n"
                    details += f"Size: {bak_file['size_mb']:.2f} MB\n"
                    details += f"Compressed: {bak_file['compressed_size']:,} bytes\n"
                    details += f"Date: {bak_file['date_time']}\n\n"
            else:
                details += "⚠️ No database files (.bak) found!\n\n"

            # Show file type summary
            file_types = {}
            for file_info in contents['files']:
                ext = Path(file_info['filename']).suffix.lower()
                file_types[ext] = file_types.get(ext, 0) + 1

            details += "📊 FILE TYPE SUMMARY:\n"
            details += "-" * 40 + "\n"
            for ext, count in sorted(file_types.items()):
                details += f"{ext or '(no extension)'}: {count} files\n"

        self.details_text.insert(tk.END, details)
        self.update_status("Analysis complete")
        self.progress.stop()

    def check_zip_database(self):
        """Check database in selected ZIP"""
        if self.selected_zip_index is None:
            messagebox.showwarning("Warning", "Please select a ZIP file first!")
            return

        zip_info = self.current_zip_files[self.selected_zip_index]
        self.update_status(f"Checking database in {zip_info['filename']}...")
        self.progress.start()

        # Run database check in background thread
        thread = threading.Thread(target=self._check_database_thread, args=(zip_info,))
        thread.daemon = True
        thread.start()

    def check_zip_integrity(self):
        """Check ZIP file integrity"""
        if self.selected_zip_index is None:
            messagebox.showwarning("Warning", "Please select a ZIP file first!")
            return

        zip_info = self.current_zip_files[self.selected_zip_index]
        self.update_status(f"Checking ZIP integrity for {zip_info['filename']}...")
        self.progress.start()

        # Run integrity check in background thread
        thread = threading.Thread(target=self._check_integrity_thread, args=(zip_info,))
        thread.daemon = True
        thread.start()

    def analyze_tape_format(self):
        """Analyze tape format files in ZIP"""
        if self.selected_zip_index is None:
            messagebox.showwarning("Warning", "Please select a ZIP file first!")
            return

        zip_info = self.current_zip_files[self.selected_zip_index]
        self.update_status(f"Analyzing tape format in {zip_info['filename']}...")
        self.progress.start()

        # Run tape analysis in background thread
        thread = threading.Thread(target=self._analyze_tape_thread, args=(zip_info,))
        thread.daemon = True
        thread.start()

    def _check_database_thread(self, zip_info):
        """Thread function for checking database"""
        try:
            # Validate database in ZIP
            result = self.db_validator.validate_backup_databases([zip_info['full_path']])

            # Update GUI in main thread
            self.root.after(0, self._show_database_results, zip_info, result)

        except Exception as e:
            self.root.after(0, self._show_error, f"Error checking database: {e}")

    def _extract_and_restore_database_thread(self, zip_info):
        """Thread function for extracting and restoring database using SQL Server"""
        try:
            # Step 1: Extract ZIP, restore to SQL Server, and analyze
            self.root.after(0, self._update_status_message, "[START] Database Extraction & Restore Process")
            self.root.after(0, self._update_progress_details, "Initializing SQL Server connection...")

            self.root.after(0, self._update_status_message, "[STEP 1] Extracting ZIP and restoring to SQL Server...")
            self.root.after(0, self._update_progress_details, f"Processing {zip_info['filename']}...")

            # Use new SQL Server restore functionality with keep_database=True
            table_patterns = ['GWSCANNER', 'SCANNER', 'DATA', 'LOG']  # Tables to look for
            restore_result = extract_restore_and_analyze(zip_info['full_path'], table_patterns, keep_database=True)

            if not restore_result['success']:
                self.root.after(0, self._show_error, f"SQL Server restore failed: {restore_result['error']}")
                return

            self.root.after(0, self._update_progress_details, f"[OK] Database restored: {restore_result['database_name']}")
            self.root.after(0, self._update_progress_details, f"[OK] Found {len(restore_result['tables_found'])} matching tables")

            # Step 2: Extract date data from the restored database
            self.root.after(0, self._update_status_message, "[STEP 2] Extracting date data from restored database...")
            
            def progress_callback(message):
                self.root.after(0, self._update_progress_details, message)

            # Create a new date extractor configured for the restored database
            restored_date_extractor = DateExtractionMicroFeature(
                server='localhost',
                username='sa', 
                password='windows0819',
                database_name=restore_result['database_name']
            )

            # Extract data from the restored database
            extracted_file = restored_date_extractor.extract_all_date_data(progress_callback)

            if not extracted_file:
                self.root.after(0, self._show_error, "Failed to extract date data from restored database")
                return

            # Step 3: Create comprehensive analysis results
            self.root.after(0, self._update_status_message, "[STEP 3] Analyzing restored database data...")
            
            # Create combined analysis results
            analysis_results = {
                'restored_database': {
                    'zip_file': zip_info['filename'],
                    'bak_file': restore_result['bak_file'],
                    'database_name': restore_result['database_name'],
                    'tables_found': restore_result['tables_found'],
                    'table_details': restore_result['table_details'],
                    'cleanup_performed': restore_result['cleanup_performed'],
                    'database_kept': restore_result.get('database_kept', False),
                    'extracted_date_file': extracted_file
                },
                'analysis': {
                    'total_tables_analyzed': len(restore_result['tables_found']),
                    'total_records': sum([info['row_count'] for info in restore_result['table_details'].values()]),
                    'latest_dates': {}
                }
            }

            # Extract latest dates from table details
            for table_name, table_info in restore_result['table_details'].items():
                if 'latest_dates' in table_info and table_info['latest_dates']:
                    analysis_results['analysis']['latest_dates'][table_name] = table_info['latest_dates']

            self.root.after(0, self._update_status_message, "[COMPLETE] Database restore and analysis completed successfully")
            self.root.after(0, self._show_extract_restore_results, zip_info, analysis_results)

        except Exception as e:
            error_msg = f"Error during database extraction and restore: {str(e)}"
            print(f"[ERROR] {error_msg}")
            self.root.after(0, self._show_error, error_msg)
        finally:
            # Stop progress indicator
            self.root.after(0, lambda: self.progress.stop())

    def _analyze_extracted_database(self, extracted_dir, current_data_file):
        """Analyze extracted database data"""
        results = {
            'extraction_successful': True,
            'extracted_files': [],
            'database_analysis': {},
            'current_data_comparison': {},
            'latest_dates': {},
            'backup_data': {}
        }

        try:
            # Step 1: Analyze extracted .bak files to get backup metadata
            self.root.after(0, self._update_progress_details, "[ANALYZE] Reading backup database files...")
            backup_analysis = self._analyze_backup_files(extracted_dir)
            results['backup_data'] = backup_analysis

            # Step 2: List extracted files
            for root, dirs, files in os.walk(extracted_dir):
                for file in files:
                    if file.endswith('.bak'):
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path)
                        results['extracted_files'].append({
                            'filename': file,
                            'path': file_path,
                            'size_mb': file_size / (1024 * 1024)
                        })

            # Analyze current database data
            if os.path.exists(current_data_file):
                with open(current_data_file, 'r') as f:
                    current_data = json.load(f)

                results['database_analysis'] = current_data

                # Extract latest dates from current data
                if 'database_results' in current_data:
                    for db_name, db_data in current_data['database_results'].items():
                        if 'error' not in db_data:
                            for table_name, table_data in db_data.items():
                                if 'error' not in table_data and 'summary_statistics' in table_data:
                                    stats = table_data['summary_statistics']
                                    results['latest_dates'][f"{db_name}.{table_name}"] = {
                                        'start_date': stats.get('data_period_start'),
                                        'end_date': stats.get('data_period_end'),
                                        'total_records': stats.get('total_records', 0),
                                        'days_span': stats.get('total_days_span', 0),
                                        'records_per_day': stats.get('records_per_day', 0)
                                    }

        except Exception as e:
            results['extraction_successful'] = False
            results['error'] = str(e)

        return results

    def _analyze_backup_files(self, extracted_dir):
        """Analyze .bak files to extract metadata and latest dates"""
        backup_analysis = {
            'databases_found': {},
            'total_files': 0,
            'analysis_summary': {}
        }

        try:
            for root, dirs, files in os.walk(extracted_dir):
                for file in files:
                    if file.endswith('.bak'):
                        backup_analysis['total_files'] += 1
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path)

                        # Extract database name from filename
                        db_name = self._extract_database_name_from_filename(file)
                        if db_name not in backup_analysis['databases_found']:
                            backup_analysis['databases_found'][db_name] = []

                        # Get file metadata
                        file_metadata = {
                            'filename': file,
                            'path': file_path,
                            'size_mb': file_size / (1024 * 1024),
                            'modified_time': datetime.fromtimestamp(os.path.getmtime(file_path)),
                            'table_info': self._extract_table_info_from_bak(file_path, file)
                        }

                        backup_analysis['databases_found'][db_name].append(file_metadata)

                        # Show progress
                        self.root.after(0, self._update_progress_details,
                                      f"[SCAN] Found {file} ({file_size / (1024 * 1024):.1f} MB)")

        except Exception as e:
            self.root.after(0, self._update_progress_details, f"[ERROR] analyzing backup files: {str(e)}")

        return backup_analysis

    def _extract_database_name_from_filename(self, filename):
        """Extract database name from backup filename"""
        # Remove .bak extension and common backup patterns
        name = filename.lower().replace('.bak', '')

        # Common database name patterns
        if 'ptrj' in name:
            return 'db_ptrj'
        elif 'staging' in name or 'ifes' in name:
            return 'staging_PTRJ_iFES_Plantware'
        elif 'venus' in name or 'hr' in name:
            return 'VenusHR14'
        else:
            return 'unknown'

    def _extract_table_info_from_bak(self, bak_file_path, filename):
        """Extract table information from .bak file (basic metadata)"""
        table_info = {
            'estimated_tables': [],
            'backup_type': 'full',
            'compression_ratio': 'unknown',
            'file_analysis': 'SQL Server backup file detected'
        }

        try:
            # Read first few bytes to identify SQL Server backup
            with open(bak_file_path, 'rb') as f:
                header = f.read(100)
                if b'SQL Server' in header or b'Microsoft' in header:
                    table_info['backup_format'] = 'SQL Server Native'
                else:
                    table_info['backup_format'] = 'Unknown'

            # Estimate based on filename patterns
            filename_lower = filename.lower()
            if any(keyword in filename_lower for keyword in ['gwscanner', 'scanner']):
                table_info['estimated_tables'] = ['Gwscannerdata', 'Ffbscannerdata']
                table_info['database_type'] = 'Staging/Scanner'
            elif any(keyword in filename_lower for keyword in ['task', 'payroll', 'pr_']):
                table_info['estimated_tables'] = ['PR_Taskreg', 'PR_Trans', 'PR_Master']
                table_info['database_type'] = 'Production/Payroll'
            elif any(keyword in filename_lower for keyword in ['fuel', 'in_']):
                table_info['estimated_tables'] = ['IN_FUELISSUE', 'IN_Master']
                table_info['database_type'] = 'Production/Inventory'
            elif any(keyword in filename_lower for keyword in ['hr', 'attendance', 'ta']):
                table_info['estimated_tables'] = ['HR_T_TAMachine', 'HR_M_Employee']
                table_info['database_type'] = 'HR/Attendance'
            else:
                table_info['estimated_tables'] = ['Multiple tables estimated']
                table_info['database_type'] = 'General Database'

        except Exception as e:
            table_info['error'] = str(e)

        return table_info

    def _show_extract_restore_results(self, zip_info, results):
        """Show extract and restore results"""
        # Keep progress information and add final results
        current_text = self.details_text.get(1.0, tk.END)

        # Add separator and results
        details = "\n" + "=" * 60 + "\n"
        details += "🎯 FINAL RESULTS\n"
        details += "=" * 60 + "\n\n"
        details += f"📁 ZIP File: {zip_info['filename']}\n\n"

        if not results['extraction_successful']:
            details += "❌ EXTRACTION FAILED\n"
            details += f"Error: {results.get('error', 'Unknown error')}\n"
        else:
            details += "✅ EXTRACTION SUCCESSFUL\n\n"

            # Show extracted database files
            details += f"📦 EXTRACTED DATABASE FILES: {len(results['extracted_files'])}\n"
            details += "-" * 40 + "\n"
            for file_info in results['extracted_files']:
                details += f"• {file_info['filename']}\n"
                details += f"  Size: {file_info['size_mb']:.2f} MB\n"

            # Show latest dates from current database
            if results['latest_dates']:
                details += f"\n[INFO] LATEST DATES FROM CURRENT DATABASE:\n"
                details += "-" * 50 + "\n"
                for table_key, date_info in results['latest_dates'].items():
                    latest_date = date_info.get('end_date', 'N/A')
                    details += f"DATABASE TABLE: {table_key}\n"
                    details += f"  Latest Date: {latest_date}\n"
                    details += f"  Total Records: {date_info.get('total_records', 0):,}\n"
                    details += f"  Period: {date_info.get('start_date', 'N/A')} to {latest_date}\n"
                    details += f"  Data Span: {date_info.get('days_span', 0)} days\n"
                    details += f"  Daily Average: {date_info.get('records_per_day', 0):.1f} records/day\n\n"

            # Show backup file analysis
            if results.get('backup_data'):
                backup_data = results['backup_data']
                details += f"\n[INFO] BACKUP FILE ANALYSIS:\n"
                details += "-" * 50 + "\n"
                details += f"Total .bak files found: {backup_data.get('total_files', 0)}\n\n"

                for db_name, files in backup_data.get('databases_found', {}).items():
                    details += f"DATABASE: {db_name}\n"
                    details += "-" * 30 + "\n"
                    for file_info in files:
                        details += f"  File: {file_info['filename']}\n"
                        details += f"  Size: {file_info['size_mb']:.2f} MB\n"
                        details += f"  Modified: {file_info['modified_time']}\n"
                        if 'table_info' in file_info:
                            table_info = file_info['table_info']
                            details += f"  Type: {table_info.get('database_type', 'Unknown')}\n"
                            details += f"  Format: {table_info.get('backup_format', 'Unknown')}\n"
                            estimated_tables = table_info.get('estimated_tables', [])
                            if estimated_tables:
                                details += f"  Estimated Tables: {', '.join(estimated_tables)}\n"
                        details += "\n"

            # Show database analysis summary
            if results['database_analysis'] and 'database_results' in results['database_analysis']:
                details += f"\n📊 DATABASE ANALYSIS SUMMARY:\n"
                details += "-" * 40 + "\n"

                db_results = results['database_analysis']['database_results']
                total_databases = len([db for db in db_results.values() if 'error' not in db])
                total_tables = sum(len([t for t in db.values() if 'error' not in t]) for db in db_results.values() if 'error' not in db)

                details += f"Databases Analyzed: {total_databases}\n"
                details += f"Tables Analyzed: {total_tables}\n"

                # Show database-specific information
                for db_name, db_data in db_results.items():
                    if 'error' not in db_data:
                        details += f"\n{db_name.upper()}:\n"
                        for table_name, table_data in db_data.items():
                            if 'error' not in table_data and 'summary_statistics' in table_data:
                                stats = table_data['summary_statistics']
                                details += f"  • {table_name}: {stats.get('total_records', 0):,} records\n"

        # Append results to existing progress text
        self.details_text.insert(tk.END, details)

        # Add completion message with timestamp
        from datetime import datetime
        completion_time = datetime.now().strftime("%H:%M:%S")
        self.details_text.insert(tk.END, f"\n[{completion_time}] ✅ PROCESS COMPLETED SUCCESSFULLY!\n")

        self.update_status("Database extraction & restore complete")
        self.progress.stop()

    def _update_status_message(self, message):
        """Update status message during extraction"""
        self.update_status(message)

    def _update_progress_details(self, message):
        """Update progress details in the details text area"""
        # Get current text and append new message
        current_text = self.details_text.get(1.0, tk.END)

        # Add timestamp for new progress entries
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")

        # If this is the first progress message, clear the details area
        if "DATABASE EXTRACTION & RESTORE RESULTS" not in current_text:
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(tk.END, f"🔄 DATABASE EXTRACTION & RESTORE PROGRESS\n")
            self.details_text.insert(tk.END, "=" * 60 + "\n\n")

        # Append new progress message
        self.details_text.insert(tk.END, f"[{timestamp}] {message}\n")

        # Auto-scroll to bottom
        self.details_text.see(tk.END)

        # Update status bar with brief message
        brief_message = message.split('\n')[0]  # Take first line only
        self.update_status(brief_message)

    def _show_database_results(self, zip_info, result):
        """Show database check results"""
        self.details_text.delete(1.0, tk.END)

        # Use enhanced validator's summary method
        details = "DATABASE CHECK RESULTS\n"
        details += "=" * 60 + "\n\n"

        # ZIP Integrity
        if 'zip_integrity' in result and zip_info['filename'] in result['zip_integrity']:
            integrity = result['zip_integrity'][zip_info['filename']]
            status = "[OK] Valid" if integrity['is_valid'] else "[ERROR] Corrupted"
            details += f"ZIP Integrity: {status}\n"
            if not integrity['is_valid']:
                details += f"Error: {integrity['error']}\n"
            details += f"File Count: {integrity['file_count']}\n"
            details += f"Total Size: {integrity['total_size']:,} bytes\n"
            details += f"Compressed: {integrity['compressed_size']:,} bytes\n\n"

        # Databases Found
        details += f"Databases Found: {len(result['databases_found'])}\n"
        if result['databases_found']:
            for db_type, db_list in result['databases_found'].items():
                details += f"\n{db_type.upper()} DATABASES:\n"
                details += "-" * 40 + "\n"
                for db_info in db_list:
                    details += f"File: {db_info['zip_file']}\n"
                    if db_info.get('latest_date'):
                        details += f"Latest Date: {db_info['latest_date']}\n"
                    if db_info.get('record_count'):
                        details += f"Records: {db_info['record_count']:,}\n"
                    if 'database_info' in db_info and db_info['database_info'].get('file_size_mb'):
                        details += f"Size: {db_info['database_info']['file_size_mb']:.2f} MB\n"
        else:
            details += "\nNo recognizable databases found\n"

        # Latest Dates
        if result.get('latest_dates'):
            details += f"\nLATEST DATES:\n"
            details += "-" * 40 + "\n"
            for db_type, latest_date in result['latest_dates'].items():
                details += f"{db_type.upper()}: {latest_date}\n"

        # File Analysis (if available)
        if 'file_analysis' in result:
            details += f"\nFILE ANALYSIS:\n"
            details += "-" * 40 + "\n"
            for file_analysis in result['file_analysis']:
                filename = file_analysis['filename']
                analysis = file_analysis['analysis']
                details += f"File: {filename}\n"
                details += f"Type: {analysis['database_type']}\n"
                details += f"Size: {analysis['file_size_mb']:.2f} MB\n"
                if analysis['tables']:
                    details += f"Tables: {len(analysis['tables'])}\n"
                    # Show first 5 tables
                    for i, table in enumerate(analysis['tables'][:5]):
                        details += f"  - {table}\n"
                    if len(analysis['tables']) > 5:
                        details += f"  ... and {len(analysis['tables']) - 5} more\n"

        # Errors and Warnings
        if result.get('errors'):
            details += f"\nERRORS:\n"
            details += "-" * 40 + "\n"
            for error in result['errors']:
                details += f"* {error}\n"

        if result.get('warnings'):
            details += f"\nWARNINGS:\n"
            details += "-" * 40 + "\n"
            for warning in result['warnings']:
                details += f"* {warning}\n"

        self.details_text.insert(tk.END, details)
        self.update_status("Database check complete")
        self.progress.stop()

    def extract_and_restore_database(self):
        """Extract and restore database from selected ZIP"""
        if self.selected_zip_index is None:
            messagebox.showwarning("Warning", "Please select a ZIP file first!")
            return

        zip_info = self.current_zip_files[self.selected_zip_index]
        self.update_status(f"Extracting and restoring database from {zip_info['filename']}...")
        self.progress.start()

        # Run extraction and restore in background thread
        thread = threading.Thread(target=self._extract_and_restore_database_thread, args=(zip_info,))
        thread.daemon = True
        thread.start()

    def extract_zip_info(self):
        """Extract detailed info from selected ZIP"""
        if self.selected_zip_index is None:
            messagebox.showwarning("Warning", "Please select a ZIP file first!")
            return

        zip_info = self.current_zip_files[self.selected_zip_index]

        # Show extraction dialog
        self.show_extraction_dialog(zip_info)

    def show_extraction_dialog(self, zip_info):
        """Show extraction options dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Extract ZIP Info")
        dialog.geometry("500x400")

        # Main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(main_frame, text=f"📦 Extract Info: {zip_info['filename']}",
                               font=('Arial', 12, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 10))

        # Options
        options_frame = ttk.LabelFrame(main_frame, text="Extract Options", padding="10")
        options_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        self.extract_metadata = tk.BooleanVar(value=True)
        self.extract_file_list = tk.BooleanVar(value=True)
        self.extract_database_info = tk.BooleanVar(value=True)

        ttk.Checkbutton(options_frame, text="Extract Metadata", variable=self.extract_metadata).grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="Extract File List", variable=self.extract_file_list).grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="Extract Database Info", variable=self.extract_database_info).grid(row=2, column=0, sticky=tk.W, pady=2)

        # Result area
        result_frame = ttk.LabelFrame(main_frame, text="Extracted Info", padding="10")
        result_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        result_text = scrolledtext.ScrolledText(result_frame, height=10, width=50)
        result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        result_text.config(font=('Courier', 9))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, pady=(10, 0))

        def extract_info():
            """Extract information based on selected options"""
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, "Extracting information...\n")

            try:
                with zipfile.ZipFile(zip_info['full_path'], 'r') as zip_ref:
                    info = []

                    if self.extract_metadata.get():
                        info.append("📋 METADATA:")
                        info.append(f"File: {zip_info['filename']}")
                        info.append(f"Size: {zip_info['size_mb']:.2f} MB")
                        info.append(f"Created: {zip_info['created_str']}")
                        info.append(f"Modified: {zip_info['modified_str']}")
                        info.append("")

                    if self.extract_file_list.get():
                        info.append("📦 FILE LIST:")
                        files = zip_ref.namelist()
                        for i, filename in enumerate(files):
                            info.append(f"{i+1:3d}. {filename}")
                        info.append("")

                    if self.extract_database_info.get():
                        info.append("🗄️ DATABASE FILES:")
                        bak_files = [f for f in zip_ref.namelist() if f.lower().endswith('.bak')]
                        for bak_file in bak_files:
                            info.append(f"• {bak_file}")
                        info.append("")

                    result_text.delete(1.0, tk.END)
                    result_text.insert(tk.END, "\n".join(info))

            except Exception as e:
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, f"Error extracting info: {e}")

        ttk.Button(button_frame, text="Extract", command=extract_info).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def update_status(self, message):
        """Update status bar"""
        self.status_label.config(text=message)

    def _check_integrity_thread(self, zip_info):
        """Thread function for checking ZIP integrity"""
        try:
            # Check integrity using enhanced validator
            integrity_result = self.db_validator._check_zip_integrity(zip_info['full_path'])

            # Update GUI in main thread
            self.root.after(0, self._show_integrity_results, zip_info, integrity_result)

        except Exception as e:
            self.root.after(0, self._show_error, f"Error checking ZIP integrity: {e}")

    def _analyze_tape_thread(self, zip_info):
        """Thread function for analyzing tape format"""
        try:
            # Extract files and analyze tape format
            analysis_results = []

            with zipfile.ZipFile(zip_info['full_path'], 'r') as zip_ref:
                files = zip_ref.namelist()

                for filename in files:
                    # Skip directories
                    if filename.endswith('/'):
                        continue

                    try:
                        # Extract to temp file for analysis
                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                            with zip_ref.open(filename) as source:
                                # Only read first 1MB for analysis
                                temp_file.write(source.read(1024*1024))
                            temp_file_path = temp_file.name

                        try:
                            analysis = self.tape_analyzer.analyze_tape_file(temp_file_path, filename)
                            analysis_results.append((filename, analysis))
                        finally:
                            os.unlink(temp_file_path)

                    except Exception as e:
                        analysis_results.append((filename, {'error': str(e)}))

            # Update GUI in main thread
            self.root.after(0, self._show_tape_analysis_results, zip_info, analysis_results)

        except Exception as e:
            self.root.after(0, self._show_error, f"Error analyzing tape format: {e}")

    def _show_integrity_results(self, zip_info, integrity_result):
        """Show ZIP integrity results"""
        self.details_text.delete(1.0, tk.END)

        details = "ZIP INTEGRITY CHECK\n"
        details += "=" * 60 + "\n\n"
        details += f"File: {zip_info['filename']}\n\n"

        if integrity_result['is_valid']:
            details += "STATUS: [OK] VALID\n"
            details += f"File Count: {integrity_result['file_count']}\n"
            details += f"Total Size: {integrity_result['total_size']:,} bytes\n"
            details += f"Compressed Size: {integrity_result['compressed_size']:,} bytes\n"
            details += f"Compression Ratio: {(1 - integrity_result['compressed_size'] / integrity_result['total_size']) * 100:.1f}%\n"
        else:
            details += "STATUS: [ERROR] CORRUPTED\n"
            details += f"Error: {integrity_result['error']}\n"

        self.details_text.insert(tk.END, details)
        self.update_status("Integrity check complete")
        self.progress.stop()

    def _show_tape_analysis_results(self, zip_info, analysis_results):
        """Show tape format analysis results"""
        self.details_text.delete(1.0, tk.END)

        details = "TAPE FORMAT ANALYSIS\n"
        details += "=" * 60 + "\n\n"
        details += f"ZIP File: {zip_info['filename']}\n\n"

        for filename, analysis in analysis_results:
            details += f"File: {filename}\n"
            details += "-" * 40 + "\n"

            if 'error' in analysis:
                details += f"ERROR: {analysis['error']}\n"
            else:
                details += f"Format: {analysis['file_format']}\n"
                details += f"Size: {analysis['file_size_mb']:.2f} MB\n"

                if analysis.get('signature'):
                    details += f"Signature: {analysis['signature']}\n"

                if analysis.get('date_info'):
                    details += "Date Info:\n"
                    for key, value in analysis['date_info'].items():
                        details += f"  {key}: {value}\n"

                if analysis.get('estimated_records'):
                    details += f"Estimated Records: {analysis['estimated_records']:,}\n"

                if analysis.get('analysis_notes'):
                    details += "Notes:\n"
                    for note in analysis['analysis_notes']:
                        details += f"  * {note}\n"

                if analysis.get('warnings'):
                    details += "Warnings:\n"
                    for warning in analysis['warnings']:
                        details += f"  * {warning}\n"

            details += "\n"

        self.details_text.insert(tk.END, details)
        self.update_status("Tape analysis complete")
        self.progress.stop()

    def _show_error(self, error_message):
        """Show error message"""
        messagebox.showerror("Error", error_message)
        self.update_status("Error occurred")
        self.progress.stop()

    def _show_quick_restore_success(self, result):
        """Show quick restore success results"""
        self.progress.stop()
        
        details = f"✅ Quick Restore Successful!\n\n"
        details += f"Database Name: {result['database_name']}\n"
        details += f"Data File: {result['data_file']}\n"
        details += f"Log File: {result['log_file']}\n"
        details += f"Restore Time: {result.get('restore_time', 'N/A')}\n\n"
        
        if result.get('tables'):
            details += f"Tables Found: {len(result['tables'])}\n"
            for table in result['tables'][:10]:  # Show first 10 tables
                details += f"  • {table}\n"
            if len(result['tables']) > 10:
                details += f"  ... and {len(result['tables']) - 10} more tables\n"
        
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, details)
        self.update_status("Quick restore completed successfully")

    def advanced_restore_dialog(self):
        """Show advanced restore options dialog"""
        if not self.selected_zip_index:
            messagebox.showwarning("Warning", "Please select a ZIP file first.")
            return

        # Create advanced restore dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Advanced Restore Options")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Main frame
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Database name
        ttk.Label(main_frame, text="Database Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        db_name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=db_name_var, width=40).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)

        # Data path
        ttk.Label(main_frame, text="Data Path:").grid(row=1, column=0, sticky=tk.W, pady=5)
        data_path_var = tk.StringVar(value="D:\\SQLData")
        data_path_frame = ttk.Frame(main_frame)
        data_path_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Entry(data_path_frame, textvariable=data_path_var, width=30).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(data_path_frame, text="Browse", 
                  command=lambda: self._browse_folder(data_path_var)).pack(side=tk.RIGHT, padx=(5, 0))

        # Log path
        ttk.Label(main_frame, text="Log Path:").grid(row=2, column=0, sticky=tk.W, pady=5)
        log_path_var = tk.StringVar(value="D:\\SQLData")
        log_path_frame = ttk.Frame(main_frame)
        log_path_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Entry(log_path_frame, textvariable=log_path_var, width=30).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(log_path_frame, text="Browse", 
                  command=lambda: self._browse_folder(log_path_var)).pack(side=tk.RIGHT, padx=(5, 0))

        # Options
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        replace_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Replace existing database", variable=replace_var).pack(anchor=tk.W)

        verify_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Verify backup after restore", variable=verify_var).pack(anchor=tk.W)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Restore", 
                  command=lambda: self._start_advanced_restore(dialog, db_name_var.get(), 
                                                             data_path_var.get(), log_path_var.get(),
                                                             replace_var.get(), verify_var.get())).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        main_frame.columnconfigure(1, weight=1)

    def _browse_folder(self, path_var):
        """Browse for folder"""
        folder = filedialog.askdirectory(initialdir=path_var.get())
        if folder:
            path_var.set(folder)

    def _start_advanced_restore(self, dialog, db_name, data_path, log_path, replace, verify):
        """Start advanced restore with custom options"""
        dialog.destroy()
        
        zip_path = self.current_zip_files[int(self.selected_zip_index.get())]
        
        self.update_status("Starting advanced restore...")
        self.progress.start()
        
        # Run in background thread
        thread = threading.Thread(target=self._advanced_restore_thread, 
                                args=(zip_path, db_name, data_path, log_path, replace, verify))
        thread.daemon = True
        thread.start()

    def _advanced_restore_thread(self, zip_path, db_name, data_path, log_path, replace, verify):
        """Background thread for advanced restore"""
        try:
            result = self.sql_restore.restore_from_zip(
                zip_path=zip_path,
                database_name=db_name if db_name else None,
                data_path=data_path,
                log_path=log_path,
                replace_existing=replace,
                verify_backup=verify
            )
            
            if result['success']:
                self.root.after(0, self._show_advanced_restore_success, result)
            else:
                self.root.after(0, self._show_restore_error, result['error'])
                
        except Exception as e:
            self.root.after(0, self._show_restore_error, str(e))

    def _show_advanced_restore_success(self, result):
        """Show advanced restore success results"""
        self.progress.stop()
        
        details = f"✅ Advanced Restore Successful!\n\n"
        details += f"Database Name: {result['database_name']}\n"
        details += f"Data File: {result['data_file']}\n"
        details += f"Log File: {result['log_file']}\n"
        details += f"Restore Time: {result.get('restore_time', 'N/A')}\n\n"
        
        if result.get('verification'):
            details += f"Backup Verification: {'✅ Passed' if result['verification'] else '❌ Failed'}\n\n"
        
        if result.get('tables'):
            details += f"Tables Found: {len(result['tables'])}\n"
            for table in result['tables'][:15]:  # Show first 15 tables
                details += f"  • {table}\n"
            if len(result['tables']) > 15:
                details += f"  ... and {len(result['tables']) - 15} more tables\n"
        
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, details)
        self.update_status("Advanced restore completed successfully")

    def _show_restore_error(self, error_msg):
        """Show restore error"""
        self.progress.stop()
        self.update_status("Restore failed")
        
        details = f"❌ Restore Failed\n\n"
        details += f"Error: {error_msg}\n\n"
        details += "Please check:\n"
        details += "• SQL Server is running\n"
        details += "• Sufficient disk space available\n"
        details += "• Valid backup file in ZIP\n"
        details += "• Proper permissions\n"
        
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, details)
        
        messagebox.showerror("Restore Error", f"Failed to restore database:\n{error_msg}")

    def list_restored_databases(self):
        """List all restored databases"""
        self.update_status("Listing restored databases...")
        self.progress.start()
        
        thread = threading.Thread(target=self._list_databases_thread)
        thread.daemon = True
        thread.start()

    def _list_databases_thread(self):
        """Background thread to list databases"""
        try:
            databases = self.sql_restore.list_databases()
            self.root.after(0, self._show_database_list, databases)
        except Exception as e:
            self.root.after(0, self._show_database_list_error, str(e))

    def _show_database_list(self, databases):
        """Show database list"""
        self.progress.stop()
        
        details = f"📋 Restored Databases ({len(databases)} found)\n\n"
        
        for db in databases:
            details += f"🗄️ {db['name']}\n"
            details += f"   Size: {db.get('size', 'Unknown')}\n"
            details += f"   Created: {db.get('create_date', 'Unknown')}\n"
            details += f"   Status: {db.get('state_desc', 'Unknown')}\n\n"
        
        if not databases:
            details += "No databases found.\n"
            details += "Try restoring a backup first.\n"
        
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, details)
        self.update_status(f"Found {len(databases)} databases")

    def _show_database_list_error(self, error_msg):
        """Show database list error"""
        self.progress.stop()
        self.update_status("Failed to list databases")
        
        details = f"❌ Failed to List Databases\n\n"
        details += f"Error: {error_msg}\n"
        
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, details)

    def cleanup_test_databases(self):
        """Cleanup test databases"""
        result = messagebox.askyesno("Confirm Cleanup", 
                                   "This will remove all test databases with names starting with 'D_Drive_Staging_DB'.\n\n"
                                   "Are you sure you want to continue?")
        if not result:
            return
        
        self.update_status("Cleaning up test databases...")
        self.progress.start()
        
        thread = threading.Thread(target=self._cleanup_databases_thread)
        thread.daemon = True
        thread.start()

    def _cleanup_databases_thread(self):
        """Background thread to cleanup databases"""
        try:
            result = self.sql_restore.cleanup_test_databases()
            self.root.after(0, self._show_cleanup_result, result)
        except Exception as e:
            self.root.after(0, self._show_cleanup_error, str(e))

    def _show_cleanup_result(self, result):
        """Show cleanup results"""
        self.progress.stop()
        
        details = f"🗑️ Database Cleanup Complete\n\n"
        details += f"Databases Removed: {result.get('removed_count', 0)}\n\n"
        
        if result.get('removed_databases'):
            details += "Removed Databases:\n"
            for db in result['removed_databases']:
                details += f"  • {db}\n"
        
        if result.get('errors'):
            details += "\nErrors:\n"
            for error in result['errors']:
                details += f"  ❌ {error}\n"
        
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, details)
        self.update_status(f"Cleanup complete - {result.get('removed_count', 0)} databases removed")

    def _show_cleanup_error(self, error_msg):
        """Show cleanup error"""
        self.progress.stop()
        self.update_status("Cleanup failed")
        
        details = f"❌ Cleanup Failed\n\n"
        details += f"Error: {error_msg}\n"
        
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, details)
        
        messagebox.showerror("Cleanup Error", f"Failed to cleanup databases:\n{error_msg}")

def main():
    """Main function"""
    root = tk.Tk()
    app = BackupFolderMonitorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()