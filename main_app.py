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

        # Action buttons - Simplified to just essential buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)

        # Row 1: Main action buttons
        ttk.Button(button_frame, text="Check ZIP Integrity", 
                  command=self.check_zip_integrity, style='Action.TButton').grid(row=0, column=0, padx=2, pady=2, sticky=(tk.W, tk.E))
        ttk.Button(button_frame, text="Extract Info", 
                  command=self.extract_zip_info, style='Action.TButton').grid(row=0, column=1, padx=2, pady=2, sticky=(tk.W, tk.E))
        ttk.Button(button_frame, text="Extract, Restore & Analyze", 
                  command=self.extract_restore_and_analyze_database, style='Action.TButton').grid(row=0, column=2, padx=2, pady=2, sticky=(tk.W, tk.E))

        # Details text area
        self.details_text = scrolledtext.ScrolledText(right_frame, height=20, wrap=tk.WORD)
        self.details_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

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

    def load_default_folder(self):
        """Load default backup folder"""
        default_path = "D:\\Backup"
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

    def extract_restore_and_analyze_database(self):
        """Extract, restore and analyze database from ZIP - Combined functionality"""
        if not self.selected_zip_index:
            messagebox.showwarning("Warning", "Please select a ZIP file first.")
            return

        zip_path = self.current_zip_files[self.selected_zip_index]
        self.update_status("Starting extract, restore and analysis...")
        self.progress.start()

        # Run in background thread
        threading.Thread(target=self._extract_and_restore_database_thread, args=(zip_path,), daemon=True).start()

    def _extract_and_restore_database_thread(self, zip_path):
        """Background thread for extract, restore and analyze"""
        try:
            def progress_callback(message):
                self.root.after(0, self._update_progress_details, message)

            # Step 1: Drop existing databases first
            progress_callback("Dropping existing databases...")
            self._drop_existing_databases(progress_callback)

            # Step 2: Extract, restore and analyze
            progress_callback("Starting extract, restore and analysis...")
            result = extract_restore_and_analyze(zip_path, progress_callback=progress_callback)

            # Step 3: Generate summary report
            progress_callback("Generating summary report...")
            result['summary'] = self._generate_summary_report(result)

            self.root.after(0, self._show_extract_restore_results, result)
        except Exception as e:
            self.root.after(0, self._show_error, f"Extract and restore failed: {str(e)}")

    def _drop_existing_databases(self, progress_callback=None):
        """Drop existing databases before restore"""
        databases_to_drop = ['staging_PTRJ_iFES_Plantware', 'db_ptrj', 'VenusHR14']
        dropped_databases = []

        for db_name in databases_to_drop:
            try:
                if progress_callback:
                    progress_callback(f"Checking database: {db_name}...")

                # Check if database exists
                check_query = f"SELECT name FROM sys.databases WHERE name = '{db_name}'"
                result = subprocess.run(['sqlcmd', '-S', 'localhost', '-U', 'sa', '-P', 'windows0819', '-Q', check_query, '-h', '-1'],
                                      capture_output=True, text=True, timeout=30)

                if result.returncode == 0 and db_name in result.stdout:
                    if progress_callback:
                        progress_callback(f"Dropping database: {db_name}...")

                    # Set single user mode and drop
                    single_user_cmd = f'sqlcmd -S localhost -U sa -P windows0819 -Q "ALTER DATABASE [{db_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE"'
                    drop_cmd = f'sqlcmd -S localhost -U sa -P windows0819 -Q "DROP DATABASE [{db_name}]"'

                    subprocess.run(single_user_cmd, shell=True, capture_output=True, text=True, timeout=30)
                    drop_result = subprocess.run(drop_cmd, shell=True, capture_output=True, text=True, timeout=30)

                    if drop_result.returncode == 0:
                        dropped_databases.append(db_name)
                        if progress_callback:
                            progress_callback(f"✅ Dropped database: {db_name}")
                    else:
                        if progress_callback:
                            progress_callback(f"❌ Failed to drop {db_name}: {drop_result.stderr}")
                else:
                    if progress_callback:
                        progress_callback(f"Database {db_name} not found - skipping")

            except Exception as e:
                if progress_callback:
                    progress_callback(f"Error dropping {db_name}: {str(e)}")
                continue

        return dropped_databases

    def _generate_summary_report(self, result):
        """Generate summary report from the results"""
        summary = {
            'total_tables_analyzed': 0,
            'total_records': 0,
            'latest_dates': {},
            'databases_processed': [],
            'backup_file': os.path.basename(result.get('bak_file', 'Unknown')),
            'extraction_success': result.get('success', False),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Extract table information from analysis
        if result.get('analysis') and result['analysis'].get('tables_found'):
            summary['total_tables_analyzed'] = len(result['analysis']['tables_found'])
            summary['databases_processed'] = ['staging_PTRJ_iFES_Plantware']

        # Extract record counts and latest dates
        if result.get('analysis'):
            analysis = result['analysis']

            if analysis.get('gwscanner_data'):
                gw_data = analysis['gwscanner_data']
                summary['total_records'] += gw_data.get('total_records', 0)
                if gw_data.get('latest_dates'):
                    summary['latest_dates']['Gwscannerdata'] = gw_data['latest_dates']

            if analysis.get('scanner_data'):
                scan_data = analysis['scanner_data']
                summary['total_records'] += scan_data.get('total_records', 0)
                if scan_data.get('latest_dates'):
                    summary['latest_dates']['Ffbscannerdata'] = scan_data['latest_dates']

        return summary

    def _update_progress_details(self, message):
        """Update progress details in real-time"""
        current_text = self.details_text.get(1.0, tk.END)
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, f"[{timestamp}] {message}\n\n{current_text}")
        self.root.update_idletasks()

    def _show_extract_restore_results(self, result):
        """Show extract, restore and analysis results"""
        self.progress.stop()

        details = "\n" + "=" * 60 + "\n"
        details += "EXTRACT, RESTORE & ANALYSIS COMPLETE\n"
        details += "=" * 60 + "\n\n"
        
        # Extraction results
        if result.get('extraction'):
            ext = result['extraction']
            details += "EXTRACTION RESULTS:\n"
            details += f"   ZIP File: {os.path.basename(ext.get('zip_file', 'Unknown'))}\n"
            details += f"   BAK Files Found: {len(ext.get('bak_files', []))}\n"
            for bak in ext.get('bak_files', []):
                details += f"     • {os.path.basename(bak)}\n"
            details += "\n"
        
        # Restore results
        if result.get('restore'):
            rest = result['restore']
            details += "RESTORE RESULTS:\n"
            details += f"   Database: {rest.get('database_name', 'Unknown')}\n"
            details += f"   Status: {'Success' if rest.get('success') else 'Failed'}\n"
            if rest.get('success'):
                details += f"   Data File: {rest.get('data_file', 'N/A')}\n"
                details += f"   Log File: {rest.get('log_file', 'N/A')}\n"
            else:
                details += f"   Error: {rest.get('error', 'Unknown error')}\n"
            details += "\n"
        
        # Analysis results
        if result.get('analysis'):
            analysis = result['analysis']
            details += "ANALYSIS RESULTS:\n"
            
            if analysis.get('tables_found'):
                details += f"   Tables Found: {len(analysis['tables_found'])}\n"
                for table in analysis['tables_found'][:10]:  # Show first 10
                    details += f"     • {table}\n"
                if len(analysis['tables_found']) > 10:
                    details += f"     ... and {len(analysis['tables_found']) - 10} more tables\n"
            
            if analysis.get('gwscanner_data'):
                gw_data = analysis['gwscanner_data']
                details += f"\n   GWSCANNER Data:\n"
                details += f"     Records: {gw_data.get('total_records', 0)}\n"
                if gw_data.get('date_range'):
                    details += f"     Date Range: {gw_data['date_range']['start']} to {gw_data['date_range']['end']}\n"
                if gw_data.get('sample_data'):
                    details += f"     Sample Records: {len(gw_data['sample_data'])}\n"
            
            if analysis.get('scanner_data'):
                scan_data = analysis['scanner_data']
                details += f"\n   SCANNER Data:\n"
                details += f"     Records: {scan_data.get('total_records', 0)}\n"
                if scan_data.get('date_range'):
                    details += f"     Date Range: {scan_data['date_range']['start']} to {scan_data['date_range']['end']}\n"
            
            if analysis.get('performance'):
                perf = analysis['performance']
                details += f"\n   Performance:\n"
                details += f"     Total Time: {perf.get('total_time', 0):.2f}s\n"
                details += f"     Restore Time: {perf.get('restore_time', 0):.2f}s\n"
                details += f"     Analysis Time: {perf.get('analysis_time', 0):.2f}s\n"
        
        # Cleanup info
        if result.get('cleanup'):
            cleanup = result['cleanup']
            details += f"\nCLEANUP:\n"
            details += f"   Database Removed: {'Yes' if cleanup.get('database_dropped') else 'No'}\n"
            details += f"   Temp Files Cleaned: {'Yes' if cleanup.get('temp_files_cleaned') else 'No'}\n"
        
        # Add summary report if available
        if result.get('summary'):
            summary = result['summary']
            details += "\n" + "=" * 60 + "\n"
            details += "SUMMARY REPORT\n"
            details += "=" * 60 + "\n"
            details += f"   Backup File: {summary.get('backup_file', 'Unknown')}\n"
            details += f"   Processed: {summary.get('timestamp', 'Unknown')}\n"
            details += f"   Status: {'Success' if summary.get('extraction_success') else 'Failed'}\n"
            details += f"   Databases Processed: {', '.join(summary.get('databases_processed', []))}\n"
            details += f"   Tables Analyzed: {summary.get('total_tables_analyzed', 0)}\n"
            details += f"   Total Records: {summary.get('total_records', 0):,}\n"

            if summary.get('latest_dates'):
                details += "\n   LATEST DATES BY TABLE:\n"
                for table, dates in summary['latest_dates'].items():
                    details += f"     {table}:\n"
                    for date_col, date_val in dates.items():
                        details += f"       {date_col}: {date_val}\n"

        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, details)
        self.update_status("Extract, restore and analysis completed successfully")

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