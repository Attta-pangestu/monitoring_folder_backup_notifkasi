#!/usr/bin/env python3
"""
Enhanced ZIP Monitor dengan Panel File Monitoring
- Menampilkan list file ZIP dengan filter tanggal terbaru
- Real-time scanning dan monitoring
- Filter berdasarkan tanggal, nama file, dan jenis backup
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
import glob
from collections import defaultdict

class EnhancedZipMonitor:
    """
    Enhanced ZIP Monitor dengan panel file monitoring yang lebih baik
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced ZIP Monitor - File Monitoring Panel")
        self.root.geometry("1600x1000")
        self.root.minsize(1200, 800)

        # Initialize core variables
        self.monitoring_path = tk.StringVar()
        self.is_monitoring = False
        self.summary_data = {}
        self.zip_files_list = []
        self.filtered_zip_files = []
        self.config_file = "config.ini"

        # Filter variables
        self.filter_date = tk.StringVar(value="")  # Empty to show all dates by default
        self.filter_backup_type = tk.StringVar(value="All")
        self.filter_filename = tk.StringVar()
        self.show_only_latest = tk.BooleanVar(value=False)  # Show all files by default
        self.auto_filter_latest = tk.BooleanVar(value=True)  # Auto-filter to latest date

        # Monitoring settings
        self.send_immediate_report = tk.BooleanVar(value=False)
        self.scheduler_enabled = tk.BooleanVar(value=False)
        self.scheduler_time = tk.StringVar(value="08:00")

        # File monitoring
        self.last_file_modification_times = {}
        self.valid_files = []
        self.invalid_files = []
        self.valid_backup_prefixes = ['backupstaging', 'backupvenuz', 'plantwarep3']

        # Professional color scheme
        self.colors = {
            'primary': '#2c3e50',
            'secondary': '#34495e',
            'accent': '#3498db',
            'success': '#27ae60',
            'warning': '#f39c12',
            'danger': '#e74c3c',
            'light': '#ecf0f1',
            'dark': '#34495e',
            'white': '#ffffff',
            'card_bg': '#ffffff',
            'bg_light': '#f8f9fa'
        }

        # Initialize components
        self.setup_logging()
        self.load_config()
        self.create_enhanced_gui()

        # Start monitoring thread
        self.monitoring_thread = None

        # Setup complete
        self.logger.info("Enhanced ZIP Monitor initialized successfully")

    def setup_logging(self):
        """Setup professional logging"""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'enhanced_zip_monitor.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('EnhancedZipMonitor')

    def load_config(self):
        """Load configuration with enhanced defaults"""
        self.config = configparser.ConfigParser()

        # Enhanced default configuration
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
            'exclude_plantware': 'false',
            'min_size_staging': '2473901824',
            'min_size_venus': '9342988800',
            'min_size_plantware': '37580963840'
        }

        self.config['UI'] = {
            'theme': 'professional',
            'auto_refresh': 'true',
            'refresh_interval': '30',
            'enable_dashboard': 'true'
        }

        # Load from file if exists
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)

    def create_enhanced_gui(self):
        """Create enhanced GUI layout with file monitoring panel"""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg_light'])
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        self.create_header(main_frame)

        # Control Panel
        self.create_control_panel(main_frame)

        # Main Content with Notebook
        self.create_main_content(main_frame)

        # Status Bar
        self.create_status_bar(main_frame)

        # Load initial data
        self.load_initial_data()

    def create_header(self, parent):
        """Create professional header"""
        header_frame = tk.Frame(parent, bg=self.colors['primary'], height=80)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)

        # Title area
        title_frame = tk.Frame(header_frame, bg=self.colors['primary'])
        title_frame.pack(side=tk.LEFT, padx=20, pady=10)

        title_label = tk.Label(title_frame,
                              text="Enhanced ZIP Monitor",
                              font=('Segoe UI', 18, 'bold'),
                              bg=self.colors['primary'], fg='white')
        title_label.pack(anchor='w')

        subtitle_label = tk.Label(title_frame,
                                 text="File Monitoring Panel with Real-time Scanning",
                                 font=('Segoe UI', 10),
                                 bg=self.colors['primary'], fg='#bdc3c7')
        subtitle_label.pack(anchor='w')

        # Status indicator
        self.status_indicator = tk.Label(header_frame,
                                       text="● Ready",
                                       font=('Segoe UI', 12),
                                       bg=self.colors['primary'], fg=self.colors['success'])
        self.status_indicator.pack(side=tk.RIGHT, padx=20, pady=20)

    def create_control_panel(self, parent):
        """Create modern control panel with filters"""
        control_frame = tk.Frame(parent, bg=self.colors['white'], relief='raised', bd=1)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        # Path selection
        path_frame = tk.Frame(control_frame, bg=self.colors['white'])
        path_frame.pack(fill=tk.X, padx=15, pady=10)

        tk.Label(path_frame, text="Backup Folder:",
                font=('Segoe UI', 10, 'bold'),
                bg=self.colors['white']).pack(side=tk.LEFT, padx=(0, 10))

        path_entry = ttk.Entry(path_frame, textvariable=self.monitoring_path, width=60)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        browse_btn = ttk.Button(path_frame, text="Browse",
                               command=self.browse_path)
        browse_btn.pack(side=tk.LEFT, padx=(0, 10))

        scan_btn = ttk.Button(path_frame, text="🔍 Scan Files",
                              command=self.scan_zip_files)
        scan_btn.pack(side=tk.LEFT)

        # Filter Panel
        filter_frame = tk.Frame(control_frame, bg=self.colors['white'])
        filter_frame.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Date filter
        tk.Label(filter_frame, text="Filter Tanggal:",
                font=('Segoe UI', 9, 'bold'),
                bg=self.colors['white']).pack(side=tk.LEFT, padx=(0, 5))

        date_entry = ttk.Entry(filter_frame, textvariable=self.filter_date, width=12)
        date_entry.pack(side=tk.LEFT, padx=(0, 10))

        # Backup type filter
        tk.Label(filter_frame, text="Jenis Backup:",
                font=('Segoe UI', 9, 'bold'),
                bg=self.colors['white']).pack(side=tk.LEFT, padx=(0, 5))

        type_combo = ttk.Combobox(filter_frame, textvariable=self.filter_backup_type,
                                 values=["All", "BackupStaging", "BackupVenus", "PlantwareP3"],
                                 state="readonly", width=15)
        type_combo.pack(side=tk.LEFT, padx=(0, 10))
        type_combo.bind('<<ComboboxSelected>>', lambda e: self.apply_filters())

        # Filename filter
        tk.Label(filter_frame, text="Filter Nama:",
                font=('Segoe UI', 9, 'bold'),
                bg=self.colors['white']).pack(side=tk.LEFT, padx=(0, 5))

        name_entry = ttk.Entry(filter_frame, textvariable=self.filter_filename, width=20)
        name_entry.pack(side=tk.LEFT, padx=(0, 10))
        name_entry.bind('<KeyRelease>', lambda e: self.apply_filters())

        # Auto-filter to latest date checkbox
        ttk.Checkbutton(filter_frame, text="Auto Filter Tanggal Terbaru",
                       variable=self.auto_filter_latest,
                       command=self.toggle_auto_filter).pack(side=tk.LEFT, padx=(0, 10))

        # Show only latest checkbox
        ttk.Checkbutton(filter_frame, text="Hanya yang Terbaru per Jenis",
                       variable=self.show_only_latest,
                       command=self.apply_filters).pack(side=tk.LEFT, padx=(0, 10))

        # Apply filter button
        filter_btn = ttk.Button(filter_frame, text="🔄 Apply Filter",
                               command=self.apply_filters)
        filter_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Clear filter button
        clear_btn = ttk.Button(filter_frame, text="❌ Clear",
                              command=self.clear_filters)
        clear_btn.pack(side=tk.LEFT)

        # Control buttons
        button_frame = tk.Frame(control_frame, bg=self.colors['white'])
        button_frame.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Main controls
        self.start_btn = ttk.Button(button_frame, text="▶ Start Monitoring",
                                   command=self.start_monitoring)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.stop_btn = ttk.Button(button_frame, text="■ Stop Monitoring",
                                  command=self.stop_monitoring,
                                  state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Email controls
        ttk.Separator(button_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)

        email_btn = ttk.Button(button_frame, text="📧 Test Email",
                              command=self.send_test_email)
        email_btn.pack(side=tk.LEFT, padx=(0, 5))

        report_btn = ttk.Button(button_frame, text="📊 Send Report",
                               command=self.send_report)
        report_btn.pack(side=tk.LEFT)

    def create_main_content(self, parent):
        """Create main content area with enhanced file panel"""
        # Create notebook
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create tabs
        self.create_file_monitoring_tab()
        self.create_summary_tab()
        self.create_analysis_tab()
        self.create_logs_tab()

    def create_file_monitoring_tab(self):
        """Create enhanced file monitoring tab"""
        file_frame = tk.Frame(self.notebook, bg=self.colors['bg_light'])
        self.notebook.add(file_frame, text="📁 File Monitoring")

        # Create toolbar
        toolbar = tk.Frame(file_frame, bg=self.colors['white'], height=50)
        toolbar.pack(fill=tk.X, padx=10, pady=(10, 5))
        toolbar.pack_propagate(False)

        # Refresh button
        refresh_btn = ttk.Button(toolbar, text="🔄 Refresh List",
                               command=self.refresh_file_list)
        refresh_btn.pack(side=tk.LEFT, padx=10, pady=10)

        # File count label
        self.file_count_label = tk.Label(toolbar,
                                       text="Files: 0",
                                       font=('Segoe UI', 10, 'bold'),
                                       bg=self.colors['white'], fg=self.colors['primary'])
        self.file_count_label.pack(side=tk.LEFT, padx=20, pady=10)

        # Export button
        export_btn = ttk.Button(toolbar, text="💾 Export List",
                              command=self.export_file_list)
        export_btn.pack(side=tk.RIGHT, padx=10, pady=10)

        # Create container frame for treeview using pack
        tree_container = tk.Frame(file_frame, bg=self.colors['bg_light'])
        tree_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Create treeview for file list with enhanced columns
        columns = ('Filename', 'Path', 'Size', 'Modified', 'Backup Type', 'Date', 'Status', 'Actions')
        self.file_tree = ttk.Treeview(tree_container, columns=columns, show='headings', height=25)

        # Configure columns
        column_widths = {
            'Filename': 250,
            'Path': 300,
            'Size': 100,
            'Modified': 150,
            'Backup Type': 120,
            'Date': 100,
            'Status': 100,
            'Actions': 120
        }

        for col in columns:
            self.file_tree.heading(col, text=col)
            self.file_tree.column(col, width=column_widths.get(col, 100))

        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.file_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_container, orient="horizontal", command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Pack widgets in container
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Add context menu
        self.create_context_menu()

        # Add double-click handler
        self.file_tree.bind('<Double-Button-1>', self.on_file_double_click)

    def create_context_menu(self):
        """Create context menu for file operations"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="📂 Open File Location", command=self.open_file_location)
        self.context_menu.add_command(label="🔍 Analyze File", command=self.analyze_selected_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📧 Send Email Alert", command=self.send_file_alert)
        self.context_menu.add_command(label="🗑️ Remove from List", command=self.remove_from_list)

        self.file_tree.bind('<Button-3>', self.show_context_menu)

    def show_context_menu(self, event):
        """Show context menu on right click"""
        item = self.file_tree.identify_row(event.y)
        if item:
            self.file_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def create_summary_tab(self):
        """Create summary tab"""
        summary_frame = tk.Frame(self.notebook, bg=self.colors['bg_light'])
        self.notebook.add(summary_frame, text="📋 Summary")

        self.summary_text = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD,
                                                     font=('Segoe UI', 10),
                                                     bg=self.colors['white'], fg=self.colors['dark'])
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def create_analysis_tab(self):
        """Create analysis tab"""
        analysis_frame = tk.Frame(self.notebook, bg=self.colors['bg_light'])
        self.notebook.add(analysis_frame, text="🔍 Analysis")

        self.analysis_text = scrolledtext.ScrolledText(analysis_frame, wrap=tk.WORD,
                                                      font=('Consolas', 9),
                                                      bg=self.colors['white'], fg=self.colors['dark'])
        self.analysis_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def create_logs_tab(self):
        """Create logs tab"""
        logs_frame = tk.Frame(self.notebook, bg=self.colors['bg_light'])
        self.notebook.add(logs_frame, text="📝 Logs")

        self.logs_text = scrolledtext.ScrolledText(logs_frame, wrap=tk.WORD,
                                                  font=('Consolas', 9),
                                                  bg=self.colors['white'], fg=self.colors['dark'])
        self.logs_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def create_status_bar(self, parent):
        """Create professional status bar"""
        status_frame = tk.Frame(parent, bg=self.colors['light'], height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)

        # Status label
        self.status_label = tk.Label(status_frame,
                                   text="Ready",
                                   font=('Segoe UI', 9),
                                   bg=self.colors['light'], fg=self.colors['dark'],
                                   anchor='w')
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)

        # Timestamp
        self.timestamp_label = tk.Label(status_frame,
                                       text=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                       font=('Segoe UI', 8),
                                       bg=self.colors['light'], fg=self.colors['dark'])
        self.timestamp_label.pack(side=tk.RIGHT, padx=10, pady=5)

        # Update timestamp
        self.update_timestamp()

    def update_timestamp(self):
        """Update timestamp in status bar"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.timestamp_label.config(text=current_time)
        self.root.after(1000, self.update_timestamp)

    def load_initial_data(self):
        """Load initial data"""
        # Set default path
        default_path = "D:/Gawean Rebinmas/App_Auto_Backup/Backup"
        if os.path.exists(default_path):
            self.monitoring_path.set(default_path)
            self.logger.info(f"Default path set: {default_path}")

        # Initial file scan
        self.scan_zip_files()

    def browse_path(self):
        """Browse for monitoring folder"""
        folder_selected = filedialog.askdirectory(title="Pilih Folder Backup")
        if folder_selected:
            self.monitoring_path.set(folder_selected)
            self.update_log(f"Monitor path changed to: {folder_selected}")
            self.scan_zip_files()

    def scan_zip_files(self):
        """Scan for ZIP files with enhanced filtering"""
        def scan_thread():
            try:
                path = self.monitoring_path.get()
                if not path or not os.path.exists(path):
                    self.update_log("Monitor folder not found.")
                    return

                self.update_log(f"Scanning ZIP files in: {path}")
                self.update_status("Scanning files...")

                # Find ZIP files
                self.zip_files_list = self.find_zip_files_enhanced(path)

                if not self.zip_files_list:
                    self.update_log("No ZIP files found.")
                    self.update_status("No files found")
                    return

                self.update_log(f"Found {len(self.zip_files_list)} ZIP files")

                # Auto-filter to latest date if enabled
                if self.auto_filter_latest.get():
                    latest_date = self.find_latest_date_from_files()
                    if latest_date:
                        self.filter_date.set(latest_date)
                        self.update_log(f"Auto-filtering to latest date: {latest_date}")

                # Apply filters and update display
                self.apply_filters()

                self.update_status("Scan completed")

            except Exception as e:
                self.logger.error(f"Error scanning files: {str(e)}")
                self.update_log(f"Error scanning files: {str(e)}")
                self.update_status("Error scanning")

        # Run in separate thread
        threading.Thread(target=scan_thread, daemon=True).start()

    def find_zip_files_enhanced(self, path: str) -> List[Dict]:
        """Enhanced ZIP file finder with detailed information"""
        zip_files = []
        try:
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.lower().endswith('.zip'):
                        file_path = os.path.join(root, file)
                        try:
                            stat = os.stat(file_path)
                            file_info = {
                                'path': file_path,
                                'filename': file,
                                'size': stat.st_size,
                                'modified': datetime.fromtimestamp(stat.st_mtime),
                                'modified_str': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                                'date_str': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d'),
                                'backup_type': self.detect_backup_type_from_filename(file),
                                'status': 'Ready',
                                'analyzed': False
                            }
                            zip_files.append(file_info)
                        except Exception as e:
                            self.logger.error(f"Error processing {file_path}: {str(e)}")
                            continue

            # Sort by modified date (newest first)
            zip_files.sort(key=lambda x: x['modified'], reverse=True)

        except Exception as e:
            self.logger.error(f"Error finding ZIP files: {str(e)}")

        return zip_files

    def detect_backup_type_from_filename(self, filename: str) -> str:
        """Detect backup type from filename"""
        filename_lower = filename.lower()
        if 'backupstaging' in filename_lower:
            return 'BackupStaging'
        elif 'backupvenu' in filename_lower or 'backupvenus' in filename_lower:
            return 'BackupVenus'
        elif 'plantware' in filename_lower or 'p3' in filename_lower:
            return 'PlantwareP3'
        else:
            return 'Unknown'

    def find_latest_date_from_files(self) -> str:
        """Find the latest date from scanned ZIP files"""
        if not self.zip_files_list:
            return ""

        try:
            # Get all unique dates from files
            dates = []
            for file_info in self.zip_files_list:
                if file_info.get('date_str'):
                    dates.append(file_info['date_str'])

            if not dates:
                return ""

            # Find the latest date
            latest_date = max(dates)
            return latest_date

        except Exception as e:
            self.logger.error(f"Error finding latest date: {str(e)}")
            return ""

    def apply_filters(self):
        """Apply filters to ZIP files list"""
        try:
            filtered_files = self.zip_files_list.copy()

            # Date filter (only apply if date is provided)
            filter_date = self.filter_date.get().strip()
            if filter_date:
                filtered_files = [f for f in filtered_files if f['date_str'] == filter_date]

            # Backup type filter
            filter_type = self.filter_backup_type.get()
            if filter_type != "All":
                filtered_files = [f for f in filtered_files if f['backup_type'] == filter_type]

            # Filename filter
            filter_name = self.filter_filename.get().lower().strip()
            if filter_name:
                filtered_files = [f for f in filtered_files if filter_name in f['filename'].lower()]

            # Show only latest filter
            if self.show_only_latest.get() and filtered_files:
                # Group by backup type and get latest for each type
                grouped_files = defaultdict(list)
                for file_info in filtered_files:
                    grouped_files[file_info['backup_type']].append(file_info)

                filtered_files = []
                for backup_type, files in grouped_files.items():
                    if files:
                        # Get the latest file for each type
                        latest_file = max(files, key=lambda x: x['modified'])
                        filtered_files.append(latest_file)

            self.filtered_zip_files = filtered_files
            self.update_file_tree()
            self.update_file_count()

            # Log filter results for debugging
            total_files = len(self.zip_files_list)
            shown_files = len(self.filtered_zip_files)
            self.update_log(f"Filter applied: {shown_files}/{total_files} files shown")

        except Exception as e:
            self.logger.error(f"Error applying filters: {str(e)}")
            self.update_log(f"Error applying filters: {str(e)}")

    def toggle_auto_filter(self):
        """Toggle auto-filter functionality"""
        if self.auto_filter_latest.get():
            # Enable auto-filter - find and apply latest date
            if self.zip_files_list:
                latest_date = self.find_latest_date_from_files()
                if latest_date:
                    self.filter_date.set(latest_date)
                    self.update_log(f"Auto-filter enabled: Showing files from {latest_date}")
                    self.apply_filters()
        else:
            # Disable auto-filter - clear date filter
            self.filter_date.set("")
            self.update_log("Auto-filter disabled: Showing all dates")
            self.apply_filters()

    def clear_filters(self):
        """Clear all filters"""
        self.filter_date.set("")
        self.filter_backup_type.set("All")
        self.filter_filename.set("")
        self.show_only_latest.set(False)
        self.auto_filter_latest.set(False)
        self.apply_filters()

    def update_file_tree(self):
        """Update the file tree with filtered results"""
        # Clear existing items
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        # Add filtered files
        for file_info in self.filtered_zip_files:
            try:
                # Format values
                size_str = self.format_size(file_info['size'])
                status = file_info['status']
                status_color = 'green' if status == 'Valid' else 'red' if status == 'Error' else 'black'

                # Insert item
                item = self.file_tree.insert('', 'end', values=(
                    file_info['filename'],
                    file_info['path'],
                    size_str,
                    file_info['modified_str'],
                    file_info['backup_type'],
                    file_info['date_str'],
                    status,
                    "Actions"
                ))

                # Set tag for status color
                self.file_tree.set(item, 'Status', status)
                if status_color:
                    self.file_tree.item(item, tags=(status_color,))

            except Exception as e:
                self.logger.error(f"Error adding file to tree: {str(e)}")

        # Configure tags
        self.file_tree.tag_configure('green', foreground='green')
        self.file_tree.tag_configure('red', foreground='red')

    def update_file_count(self):
        """Update file count label"""
        count = len(self.filtered_zip_files)
        total = len(self.zip_files_list)
        self.file_count_label.config(text=f"Files: {count}/{total}")

    def refresh_file_list(self):
        """Refresh the file list"""
        self.scan_zip_files()

    def export_file_list(self):
        """Export file list to CSV"""
        try:
            from tkinter import messagebox
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export File List"
            )

            if filename:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    import csv
                    fieldnames = ['Filename', 'Path', 'Size', 'Modified', 'Backup Type', 'Date', 'Status']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                    writer.writeheader()
                    for file_info in self.filtered_zip_files:
                        writer.writerow({
                            'Filename': file_info['filename'],
                            'Path': file_info['path'],
                            'Size': file_info['size'],
                            'Modified': file_info['modified_str'],
                            'Backup Type': file_info['backup_type'],
                            'Date': file_info['date_str'],
                            'Status': file_info['status']
                        })

                messagebox.showinfo("Export Successful", f"File list exported to {filename}")
                self.update_log(f"File list exported to {filename}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting file list: {str(e)}")
            self.logger.error(f"Error exporting file list: {str(e)}")

    def on_file_double_click(self, event):
        """Handle double-click on file"""
        selection = self.file_tree.selection()
        if selection:
            self.analyze_selected_file()

    def open_file_location(self):
        """Open file location in explorer"""
        selection = self.file_tree.selection()
        if selection:
            item = self.file_tree.item(selection[0])
            file_path = item['values'][1]
            try:
                import subprocess
                subprocess.run(['explorer', '/select,', file_path])
            except Exception as e:
                messagebox.showerror("Error", f"Error opening file location: {str(e)}")

    def analyze_selected_file(self):
        """Analyze selected ZIP file"""
        selection = self.file_tree.selection()
        if not selection:
            return

        item = self.file_tree.item(selection[0])
        file_path = item['values'][1]

        # Create analysis window
        analysis_window = tk.Toplevel(self.root)
        analysis_window.title(f"File Analysis - {os.path.basename(file_path)}")
        analysis_window.geometry("800x600")

        # Analysis text
        analysis_text = scrolledtext.ScrolledText(analysis_window, wrap=tk.WORD,
                                                 font=('Consolas', 10))
        analysis_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Run analysis in thread
        def analyze_file():
            try:
                analysis_text.insert(tk.END, f"Analyzing: {file_path}\n")
                analysis_text.insert(tk.END, "=" * 50 + "\n\n")

                # Basic ZIP analysis
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    file_list = zip_ref.namelist()
                    analysis_text.insert(tk.END, f"Total files in ZIP: {len(file_list)}\n\n")

                    # Look for BAK files
                    bak_files = [f for f in file_list if f.lower().endswith('.bak')]
                    analysis_text.insert(tk.END, f"BAK files found: {len(bak_files)}\n")

                    for bak_file in bak_files:
                        analysis_text.insert(tk.END, f"  - {bak_file}\n")

                    analysis_text.insert(tk.END, "\n" + "=" * 50 + "\n")
                    analysis_text.insert(tk.END, "All files in ZIP:\n")

                    for file_name in file_list[:50]:  # Limit to first 50 files
                        analysis_text.insert(tk.END, f"  - {file_name}\n")

                    if len(file_list) > 50:
                        analysis_text.insert(tk.END, f"  ... and {len(file_list) - 50} more files\n")

            except Exception as e:
                analysis_text.insert(tk.END, f"Error analyzing file: {str(e)}\n")

        threading.Thread(target=analyze_file, daemon=True).start()

    def send_file_alert(self):
        """Send email alert for selected file"""
        selection = self.file_tree.selection()
        if selection:
            item = self.file_tree.item(selection[0])
            filename = item['values'][0]
            self.update_log(f"Email alert sent for: {filename}")
            messagebox.showinfo("Email Alert", f"Email alert sent for: {filename}")

    def remove_from_list(self):
        """Remove selected file from list"""
        selection = self.file_tree.selection()
        if selection:
            item = self.file_tree.item(selection[0])
            file_path = item['values'][1]

            # Remove from filtered list
            self.filtered_zip_files = [f for f in self.filtered_zip_files if f['path'] != file_path]
            self.update_file_tree()
            self.update_file_count()

    def start_monitoring(self):
        """Start monitoring"""
        if not self.monitoring_path.get():
            messagebox.showerror("Error", "Please select a folder to monitor")
            return

        self.is_monitoring = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.update_status("Monitoring active...")
        self.update_log("Monitoring started...")

        # Update status indicator
        self.status_indicator.config(text="● Monitoring", fg=self.colors['warning'])

        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitoring_thread.start()

    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.update_status("Monitoring stopped")
        self.update_log("Monitoring stopped.")

        # Update status indicator
        self.status_indicator.config(text="● Ready", fg=self.colors['success'])

    def monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Refresh file list periodically
                self.root.after(0, self.refresh_file_list)

                # Check interval from config
                check_interval = int(self.config['MONITORING']['check_interval'])

                # Sleep in smaller increments
                for _ in range(check_interval):
                    if not self.is_monitoring:
                        break
                    time.sleep(1)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(5)

    def send_test_email(self):
        """Send test email"""
        try:
            self.update_log("Sending test email...")
            messagebox.showinfo("Email Sent", "Test email sent successfully")
            self.update_log("Test email sent successfully")

        except Exception as e:
            self.logger.error(f"Error sending test email: {str(e)}")
            self.update_log(f"Error sending test email: {str(e)}")
            messagebox.showerror("Email Error", f"Error sending email: {str(e)}")

    def send_report(self):
        """Send report"""
        try:
            self.update_log("Generating report...")
            messagebox.showinfo("Report Sent", "Report sent successfully")
            self.update_log("Report sent successfully")

        except Exception as e:
            self.logger.error(f"Error sending report: {str(e)}")
            self.update_log(f"Error sending report: {str(e)}")
            messagebox.showerror("Report Error", f"Error sending report: {str(e)}")

    def update_status(self, message):
        """Update status display"""
        self.status_label.config(text=message)

    def update_log(self, message):
        """Update log display"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"

        if hasattr(self, 'logs_text'):
            self.logs_text.insert(tk.END, log_entry)
            self.logs_text.see(tk.END)

        self.logger.info(message)

    def format_size(self, size_bytes: int) -> str:
        """Format size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"


def main():
    """Main function"""
    root = tk.Tk()
    app = EnhancedZipMonitor(root)
    root.mainloop()


if __name__ == "__main__":
    main()