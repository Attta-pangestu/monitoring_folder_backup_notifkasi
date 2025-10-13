#!/usr/bin/env python3
"""
Refactoring Script for Enhanced Backup Monitor UI
- Professional UI dengan harmonis desain
- Integrasi dashboard monitoring yang sync proper
- Optimized layout dan user experience
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
import shutil

class ProfessionalBackupMonitorUI:
    """
    Professional UI untuk Backup Monitor dengan design yang harmonis
    dan integrasi dashboard monitoring yang proper
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Professional Backup Monitor v4.0 - Dashboard Monitoring")
        self.root.geometry("1600x1000")
        self.root.minsize(1200, 800)

        # Initialize variables
        self.monitoring_path = tk.StringVar()
        self.is_monitoring = False
        self.summary_data = {}
        self.config_file = "config.ini"
        
        # Target files for scheduler analysis
        self.target_files_for_analysis = []
        self.latest_backup_date = None

        # Monitoring settings
        self.send_immediate_report = tk.BooleanVar(value=False)
        self.scheduler_enabled = tk.BooleanVar(value=False)
        self.scheduler_time = tk.StringVar(value="08:00")
        self.scheduler_thread = None
        self.scheduler_running = False
        self.scheduler_countdown = tk.StringVar(value="Countdown: --:--:--")
        self.next_run_time = None
        
        # Email settings
        self.recipient_email = tk.StringVar(value="atharizki.developer@gmail.com")

        # File monitoring
        self.last_file_modification_times = {}
        self.valid_files = []
        self.invalid_files = []
        self.valid_backup_prefixes = ['backupstaging', 'backupvenuz', 'plantwarep3']

        # UI Theme colors (Professional color scheme)
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
            'critical_bg': '#fff3cd',
            'critical_fg': '#856404',
            'card_bg': '#ffffff',
            'bg_light': '#f8f9fa'
        }

        # Initialize
        self.setup_logging()
        self.load_config()
        self.create_professional_gui()

        # Start monitoring thread
        self.monitoring_thread = None
        
        # Start scheduler thread in background (always running, but only executes when enabled)
        self.start_scheduler_thread()

    def setup_logging(self):
        """Setup professional logging configuration"""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'professional_monitor.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ProfessionalBackupMonitor')

    def load_config(self):
        """Load configuration with enhanced defaults"""
        self.config = configparser.ConfigParser()

        # Enhanced default configuration
        self.config['EMAIL'] = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': '587',
            'sender_email': 'ifesptrj@gmail.com',
            'sender_password': 'ugaowlrdcuhpdafu',
            'recipient_email': 'atharizki.developer@gmail.com'
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

        self.config['ANALYSIS'] = {
            'dbatools_timeout': '60',
            'extraction_timeout': '300',
            'enable_sql_analysis': 'true'
        }

        self.config['SCHEDULER'] = {
            'enabled': 'false',
            'execution_time': '08:00'
        }

        self.config['UI'] = {
            'theme': 'professional',
            'auto_refresh': 'true',
            'refresh_interval': '300'  # 5 minutes
        }

        # Load from file if exists
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
            # Load email settings from config
            self.recipient_email.set(self.config.get('EMAIL', 'recipient_email', fallback='atharizki.developer@gmail.com'))

    def create_professional_gui(self):
        """Create professional GUI layout"""
        # Main container with modern styling
        main_frame = tk.Frame(self.root, bg=self.colors['bg_light'])
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header with professional design
        self.create_header(main_frame)

        # Control Panel
        self.create_control_panel(main_frame)

        # Status Bar
        self.create_status_bar(main_frame)

        # Main Content Area with Notebook
        self.create_main_content(main_frame)

        # Load default path and initial data
        self.load_initial_data()

    def create_header(self, parent):
        """Create professional header"""
        header_frame = tk.Frame(parent, bg=self.colors['primary'], height=80)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)

        # Logo/Title area
        title_frame = tk.Frame(header_frame, bg=self.colors['primary'])
        title_frame.pack(side=tk.LEFT, padx=20, pady=10)

        # Main title
        title_label = tk.Label(title_frame,
                              text="Professional Backup Monitor",
                              font=('Segoe UI', 18, 'bold'),
                              bg=self.colors['primary'], fg='white')
        title_label.pack(anchor='w')

        # Subtitle
        subtitle_label = tk.Label(title_frame,
                                 text="v4.0 - Dashboard Monitoring & Analysis",
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
        """Create modern control panel"""
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
                               command=self.browse_path,
                               style='Modern.TButton')
        browse_btn.pack(side=tk.LEFT, padx=(0, 10))

        scan_btn = ttk.Button(path_frame, text="Deep Scan",
                              command=self.deep_scan_files,
                              style='Accent.TButton')
        scan_btn.pack(side=tk.LEFT)

        # Control buttons
        button_frame = tk.Frame(control_frame, bg=self.colors['white'])
        button_frame.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Monitoring controls
        self.start_btn = ttk.Button(button_frame, text="▶ Start Monitoring",
                                   command=self.start_monitoring,
                                   style='Success.TButton')
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.stop_btn = ttk.Button(button_frame, text="■ Stop Monitoring",
                                  command=self.stop_monitoring,
                                  state=tk.DISABLED,
                                  style='Danger.TButton')
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Email controls
        ttk.Separator(button_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)

        email_btn = ttk.Button(button_frame, text="📧 Test Email",
                              command=self.send_test_email,
                              style='Modern.TButton')
        email_btn.pack(side=tk.LEFT, padx=(0, 5))

        report_btn = ttk.Button(button_frame, text="📊 Send Report",
                               command=self.send_deep_analysis_email,
                               style='Modern.TButton')
        report_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Options
        ttk.Separator(button_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)

        ttk.Checkbutton(button_frame, text="Send immediate report",
                       variable=self.send_immediate_report,
                       style='Modern.TCheckbutton').pack(side=tk.LEFT, padx=(0, 10))

        ttk.Checkbutton(button_frame, text="Enable Scheduler",
                       variable=self.scheduler_enabled,
                       command=self.toggle_scheduler,
                       style='Modern.TCheckbutton').pack(side=tk.LEFT, padx=(0, 10))

        # Scheduler time
        tk.Label(button_frame, text="Schedule:",
                font=('Segoe UI', 9),
                bg=self.colors['white']).pack(side=tk.LEFT, padx=(10, 5))

        time_entry = ttk.Entry(button_frame, textvariable=self.scheduler_time, width=8)
        time_entry.pack(side=tk.LEFT, padx=(0, 5))
        time_entry.bind('<FocusOut>', lambda e: self.save_scheduler_settings())

        # Set Scheduler Time Button
        set_scheduler_btn = ttk.Button(button_frame, text="Set Time",
                                     command=self.set_scheduler_time,
                                     style='Modern.TButton')
        set_scheduler_btn.pack(side=tk.LEFT, padx=(5, 5))

        # Run Now Button
        run_now_btn = ttk.Button(button_frame, text="Run Now",
                               command=self.run_scheduler_now,
                               style='Accent.TButton')
        run_now_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Refresh Target Files Button
        refresh_target_btn = ttk.Button(button_frame, text="Refresh Target",
                                       command=self.refresh_target_files,
                                       style='Modern.TButton')
        refresh_target_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Refresh Files Tab Button
        refresh_files_btn = ttk.Button(button_frame, text="Refresh Files",
                                      command=self.refresh_files_display,
                                      style='Modern.TButton')
        refresh_files_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Scheduler status label
        self.scheduler_status_label = ttk.Label(button_frame, text="Scheduler: Non-aktif",
                                               foreground="gray", font=('Segoe UI', 9))
        self.scheduler_status_label.pack(side=tk.LEFT, padx=(10, 5))

        # Email settings section
        email_frame = tk.Frame(control_frame, bg=self.colors['white'])
        email_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        # Email recipient input
        tk.Label(email_frame, text="Email Tujuan:",
                font=('Segoe UI', 10, 'bold'),
                bg=self.colors['white']).pack(side=tk.LEFT, padx=(0, 10))
        
        email_entry = ttk.Entry(email_frame, textvariable=self.recipient_email, width=40)
        email_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        save_email_btn = ttk.Button(email_frame, text="Simpan Email",
                                   command=self.save_email_settings,
                                   style='Modern.TButton')
        save_email_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Countdown label
        self.countdown_label = ttk.Label(button_frame, textvariable=self.scheduler_countdown,
                                        foreground="blue", font=('Segoe UI', 9, 'bold'))
        self.countdown_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Target files info label
        self.target_info_label = ttk.Label(button_frame, text="Target: Not set",
                                         foreground="green", font=('Segoe UI', 9))
        self.target_info_label.pack(side=tk.LEFT, padx=(10, 0))

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

        # Separator
        ttk.Separator(status_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, pady=5)

        # Config info
        config_info = f"Plantware: {'Excluded' if self.config.getboolean('MONITORING', 'exclude_plantware', fallback=True) else 'Included'} | SQL Analysis: {'Enabled' if self.config.getboolean('ANALYSIS', 'enable_sql_analysis', fallback=True) else 'Disabled'}"
        config_label = tk.Label(status_frame,
                               text=config_info,
                               font=('Segoe UI', 8),
                               bg=self.colors['light'], fg=self.colors['dark'])
        config_label.pack(side=tk.LEFT, padx=10, pady=5)

        # Timestamp
        self.timestamp_label = tk.Label(status_frame,
                                       text=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                       font=('Segoe UI', 8),
                                       bg=self.colors['light'], fg=self.colors['dark'])
        self.timestamp_label.pack(side=tk.RIGHT, padx=10, pady=5)

        # Update timestamp every second
        self.update_timestamp()

    def create_main_content(self, parent):
        """Create main content area with professional notebook"""
        # Create notebook with modern styling
        self.notebook = ttk.Notebook(parent, style='Modern.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Configure styles
        self.configure_styles()

        # Create tabs
        self.create_summary_tab()  # Create summary tab first
        self.create_logs_tab()     # Create logs tab second
        # Create other tabs with delay for faster startup
        self.root.after(200, self.create_remaining_tabs)
        
    def create_remaining_tabs(self):
        """Create remaining tabs after initial UI is shown"""
        self.create_dashboard_tab()
        self.create_files_tab()
        self.create_analysis_tab()
        self.create_history_tab()
        
        # Refresh dashboard after all components are created
        self.root.after(100, self.safe_refresh_dashboard)
        
        # Notify user that application is ready
        self.root.after(200, self.notify_application_ready)
    
    def notify_application_ready(self):
        """Notify user that application is ready"""
        self.update_log("Application ready! All tabs loaded successfully.")
        self.update_status("Application ready")

    def configure_styles(self):
        """Configure modern UI styles"""
        style = ttk.Style()

        # Configure notebook style
        style.configure('Modern.TNotebook', background=self.colors['bg_light'])
        style.configure('Modern.TNotebook.Tab',
                       background=self.colors['light'],
                       foreground=self.colors['dark'],
                       padding=[12, 8],
                       font=('Segoe UI', 10))
        style.map('Modern.TNotebook.Tab',
                 background=[('selected', self.colors['white']),
                           ('active', self.colors['accent'])])

        # Configure button styles
        style.configure('Modern.TButton',
                       font=('Segoe UI', 9),
                       padding=[8, 4])

        style.configure('Success.TButton',
                       font=('Segoe UI', 9, 'bold'),
                       padding=[8, 4],
                       background=self.colors['success'])

        style.configure('Danger.TButton',
                       font=('Segoe UI', 9, 'bold'),
                       padding=[8, 4],
                       background=self.colors['danger'])

        style.configure('Accent.TButton',
                       font=('Segoe UI', 9, 'bold'),
                       padding=[8, 4],
                       background=self.colors['accent'])

        # Configure checkbutton style
        style.configure('Modern.TCheckbutton',
                       font=('Segoe UI', 9),
                       background=self.colors['white'])

    def create_dashboard_tab(self):
        """Create professional dashboard tab"""
        dashboard_frame = tk.Frame(self.notebook, bg=self.colors['bg_light'])
        self.notebook.add(dashboard_frame, text="📊 Dashboard")

        # Create dashboard UI
        self.create_professional_dashboard(dashboard_frame)

    def create_professional_dashboard(self, parent):
        """Create professional dashboard layout"""
        # Control toolbar
        toolbar = tk.Frame(parent, bg=self.colors['white'], height=50)
        toolbar.pack(fill=tk.X, padx=10, pady=(10, 5))
        toolbar.pack_propagate(False)

        # Refresh controls
        refresh_btn = ttk.Button(toolbar, text="🔄 Refresh",
                               command=self.refresh_dashboard,
                               style='Modern.TButton')
        refresh_btn.pack(side=tk.LEFT, padx=10, pady=10)

        load_btn = ttk.Button(toolbar, text="📂 Load JSON",
                            command=self.load_backup_history_on_startup,
                            style='Modern.TButton')
        load_btn.pack(side=tk.LEFT, padx=5, pady=10)

        export_btn = ttk.Button(toolbar, text="💾 Export",
                               command=self.export_dashboard_data,
                               style='Modern.TButton')
        export_btn.pack(side=tk.LEFT, padx=5, pady=10)

        # Last update info
        self.last_update_label = tk.Label(toolbar,
                                        text="Last Update: Never",
                                        font=('Segoe UI', 9),
                                        bg=self.colors['white'], fg=self.colors['dark'])
        self.last_update_label.pack(side=tk.RIGHT, padx=10, pady=10)

        # Create scrollable main area
        canvas = tk.Canvas(parent, bg=self.colors['bg_light'])
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg_light'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Store references
        self.dashboard_canvas = canvas
        self.dashboard_frame = scrollable_frame

        # Create dashboard sections
        self.create_critical_alerts_section(scrollable_frame)
        self.create_metrics_section(scrollable_frame)
        self.create_backup_status_section(scrollable_frame)
        self.create_recent_activity_section(scrollable_frame)

    def create_critical_alerts_section(self, parent):
        """Create critical alerts section"""
        alerts_frame = tk.Frame(parent, bg=self.colors['critical_bg'], relief='raised', bd=2)
        alerts_frame.pack(fill=tk.X, padx=10, pady=5)

        # Header
        header_frame = tk.Frame(alerts_frame, bg=self.colors['critical_bg'])
        header_frame.pack(fill=tk.X, padx=15, pady=(10, 5))

        tk.Label(header_frame, text="⚠ CRITICAL ALERTS",
                font=('Segoe UI', 14, 'bold'),
                bg=self.colors['critical_bg'], fg=self.colors['critical_fg']).pack(side=tk.LEFT)

        self.alert_count_label = tk.Label(header_frame,
                                         text="0 Items Need Attention",
                                         font=('Segoe UI', 12, 'bold'),
                                         bg=self.colors['critical_bg'], fg=self.colors['critical_fg'])
        self.alert_count_label.pack(side=tk.RIGHT)

        # Content frame
        content_frame = tk.Frame(alerts_frame, bg=self.colors['critical_bg'])
        content_frame.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Critical info grid
        self.critical_info_frame = tk.Frame(content_frame, bg=self.colors['critical_bg'])
        self.critical_info_frame.pack(fill=tk.X)

        # Placeholder for critical info
        self.create_critical_info_placeholders()

    def create_metrics_section(self, parent):
        """Create metrics overview section"""
        metrics_frame = tk.Frame(parent, bg=self.colors['white'], relief='raised', bd=1)
        metrics_frame.pack(fill=tk.X, padx=10, pady=5)

        # Header
        header_frame = tk.Frame(metrics_frame, bg=self.colors['white'])
        header_frame.pack(fill=tk.X, padx=15, pady=(10, 5))

        tk.Label(header_frame, text="📈 SYSTEM METRICS",
                font=('Segoe UI', 14, 'bold'),
                bg=self.colors['white'], fg=self.colors['primary']).pack(side=tk.LEFT)

        # Metrics grid
        self.metrics_grid = tk.Frame(metrics_frame, bg=self.colors['white'])
        self.metrics_grid.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Create metric cards
        self.create_metric_cards()

    def create_backup_status_section(self, parent):
        """Create backup status overview section"""
        status_frame = tk.Frame(parent, bg=self.colors['white'], relief='raised', bd=1)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Header
        header_frame = tk.Frame(status_frame, bg=self.colors['white'])
        header_frame.pack(fill=tk.X, padx=15, pady=(10, 5))

        tk.Label(header_frame, text="💾 BACKUP STATUS OVERVIEW",
                font=('Segoe UI', 14, 'bold'),
                bg=self.colors['white'], fg=self.colors['primary']).pack(side=tk.LEFT)

        self.backup_status_filter = ttk.Combobox(header_frame,
                                                values=["All", "Valid", "Warning", "Error"],
                                                state="readonly",
                                                width=10)
        self.backup_status_filter.set("All")
        self.backup_status_filter.pack(side=tk.RIGHT)
        self.backup_status_filter.bind('<<ComboboxSelected>>', lambda e: self.filter_backup_status())

        # Backup cards container
        self.backup_cards_container = tk.Frame(status_frame, bg=self.colors['bg_light'])
        self.backup_cards_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        # Create scrollable area for backup cards
        backup_canvas = tk.Canvas(self.backup_cards_container, bg=self.colors['bg_light'])
        backup_scrollbar = ttk.Scrollbar(self.backup_cards_container, orient="vertical", command=backup_canvas.yview)
        self.backup_cards_scrollable = tk.Frame(backup_canvas, bg=self.colors['bg_light'])

        self.backup_cards_scrollable.bind(
            "<Configure>",
            lambda e: backup_canvas.configure(scrollregion=backup_canvas.bbox("all"))
        )

        backup_canvas.create_window((0, 0), window=self.backup_cards_scrollable, anchor="nw")
        backup_canvas.configure(yscrollcommand=backup_scrollbar.set)

        backup_canvas.pack(side="left", fill="both", expand=True)
        backup_scrollbar.pack(side="right", fill="y")

    def create_recent_activity_section(self, parent):
        """Create recent activity section"""
        activity_frame = tk.Frame(parent, bg=self.colors['white'], relief='raised', bd=1)
        activity_frame.pack(fill=tk.X, padx=10, pady=5)

        # Header
        header_frame = tk.Frame(activity_frame, bg=self.colors['white'])
        header_frame.pack(fill=tk.X, padx=15, pady=(10, 5))

        tk.Label(header_frame, text="🕒 RECENT ACTIVITY",
                font=('Segoe UI', 14, 'bold'),
                bg=self.colors['white'], fg=self.colors['primary']).pack(side=tk.LEFT)

        # Activity log
        self.activity_text = tk.Text(activity_frame, height=6, wrap=tk.WORD,
                                   font=('Consolas', 9),
                                   bg=self.colors['bg_light'], fg=self.colors['dark'])
        self.activity_text.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Add scrollbar
        activity_scrollbar = ttk.Scrollbar(self.activity_text, command=self.activity_text.yview)
        activity_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.activity_text.config(yscrollcommand=activity_scrollbar.set)

    def create_critical_info_placeholders(self):
        """Create placeholder widgets for critical info"""
        # Clear existing
        for widget in self.critical_info_frame.winfo_children():
            widget.destroy()

        # Create grid layout
        for i in range(2):
            for j in range(3):
                frame = tk.Frame(self.critical_info_frame, bg=self.colors['critical_bg'])
                frame.grid(row=i, column=j, padx=10, pady=5, sticky='ew')

                label = tk.Label(frame, text="Loading...",
                               font=('Segoe UI', 9),
                               bg=self.colors['critical_bg'], fg=self.colors['critical_fg'])
                label.pack(anchor='w')

        # Configure grid weights
        self.critical_info_frame.columnconfigure(0, weight=1)
        self.critical_info_frame.columnconfigure(1, weight=1)
        self.critical_info_frame.columnconfigure(2, weight=1)

    def create_metric_cards(self):
        """Create metric cards for dashboard"""
        # Clear existing
        for widget in self.metrics_grid.winfo_children():
            widget.destroy()

        metrics = [
            ("Total Backups", "0", self.colors['primary']),
            ("Valid Files", "0", self.colors['success']),
            ("Warnings", "0", self.colors['warning']),
            ("Errors", "0", self.colors['danger']),
            ("Last Backup", "Never", self.colors['dark']),
            ("System Status", "Ready", self.colors['success'])
        ]

        self.metric_widgets = {}

        for i, (title, value, color) in enumerate(metrics):
            card_frame = tk.Frame(self.metrics_grid, bg=self.colors['white'], relief='raised', bd=1)
            card_frame.grid(row=i//3, column=i%3, padx=5, pady=5, sticky='ew')

            # Title
            title_label = tk.Label(card_frame, text=title,
                                 font=('Segoe UI', 9, 'bold'),
                                 bg=self.colors['white'], fg=self.colors['dark'])
            title_label.pack(anchor='w', padx=10, pady=(10, 5))

            # Value
            value_label = tk.Label(card_frame, text=value,
                                 font=('Segoe UI', 16, 'bold'),
                                 bg=self.colors['white'], fg=color)
            value_label.pack(anchor='w', padx=10, pady=(0, 10))

            self.metric_widgets[title] = value_label

        # Configure grid weights
        for i in range(3):
            self.metrics_grid.columnconfigure(i, weight=1)

    def create_summary_tab(self):
        """Create summary tab"""
        summary_frame = tk.Frame(self.notebook, bg=self.colors['bg_light'])
        self.notebook.add(summary_frame, text="📋 Summary")

        # Summary text widget
        self.summary_text = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD,
                                                     font=('Segoe UI', 10),
                                                     bg=self.colors['white'], fg=self.colors['dark'])
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def create_files_tab(self):
        """Create files tab"""
        files_frame = tk.Frame(self.notebook, bg=self.colors['bg_light'])
        self.notebook.add(files_frame, text="📁 Files")

        # Control panel for Files tab
        control_frame = tk.Frame(files_frame, bg=self.colors['white'])
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Scan button
        scan_btn = ttk.Button(control_frame, text="🔍 Scan Backup Files",
                             command=self.scan_files_for_tab,
                             style='Accent.TButton')
        scan_btn.pack(side=tk.LEFT, padx=5)
        
        # Refresh button
        refresh_btn = ttk.Button(control_frame, text="🔄 Refresh Display",
                               command=self.refresh_files_display,
                               style='Modern.TButton')
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.files_status_label = tk.Label(control_frame,
                                          text="Ready to scan backup files",
                                          font=('Segoe UI', 9),
                                          bg=self.colors['white'], fg=self.colors['dark'])
        self.files_status_label.pack(side=tk.LEFT, padx=20)

        # Files text widget
        self.files_text = scrolledtext.ScrolledText(files_frame, wrap=tk.WORD,
                                                   font=('Consolas', 9),
                                                   bg=self.colors['white'], fg=self.colors['dark'])
        self.files_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    def create_analysis_tab(self):
        """Create analysis tab"""
        analysis_frame = tk.Frame(self.notebook, bg=self.colors['bg_light'])
        self.notebook.add(analysis_frame, text="🔍 Analysis")

        # Analysis text widget
        self.analysis_text = scrolledtext.ScrolledText(analysis_frame, wrap=tk.WORD,
                                                      font=('Consolas', 9),
                                                      bg=self.colors['white'], fg=self.colors['dark'])
        self.analysis_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def create_history_tab(self):
        """Create history tab"""
        history_frame = tk.Frame(self.notebook, bg=self.colors['bg_light'])
        self.notebook.add(history_frame, text="📜 History")

        # Control buttons
        control_frame = tk.Frame(history_frame, bg=self.colors['white'])
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(control_frame, text="🔄 Refresh",
                  command=self.refresh_backup_history,
                  style='Modern.TButton').pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="📂 Load JSON",
                  command=self.load_backup_history_on_startup,
                  style='Modern.TButton').pack(side=tk.LEFT, padx=5)

        # History text widget
        self.history_text = scrolledtext.ScrolledText(history_frame, wrap=tk.WORD,
                                                     font=('Segoe UI', 10),
                                                     bg=self.colors['white'], fg=self.colors['dark'])
        self.history_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    def create_logs_tab(self):
        """Create logs tab"""
        logs_frame = tk.Frame(self.notebook, bg=self.colors['bg_light'])
        self.notebook.add(logs_frame, text="📝 Logs")

        # Logs text widget
        self.logs_text = scrolledtext.ScrolledText(logs_frame, wrap=tk.WORD,
                                                  font=('Consolas', 9),
                                                  bg=self.colors['white'], fg=self.colors['dark'])
        self.logs_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def load_initial_data(self):
        """Load initial data and setup"""
        # Set default path
        default_path = "D:/Gawean Rebinmas/App_Auto_Backup/Backup"
        if os.path.exists(default_path):
            self.monitoring_path.set(default_path)
            self.logger.info(f"Default monitoring path set: {default_path}")

        # Load scheduler settings
        self.load_scheduler_settings()

        # Load backup history in background thread for faster startup
        self.root.after(100, self.load_data_in_background)
        
    def load_data_in_background(self):
        """Load data in background thread for faster startup"""
        try:
            # Load backup history without blocking UI
            self.load_backup_history_on_startup()
            # Update dashboard after data is loaded and components are created
            # Use a longer delay to ensure all components are created
            self.root.after(500, self.safe_refresh_dashboard)
            
            # Update Files tab after a short delay to ensure it's created
            self.root.after(700, self.update_files_tab_on_startup)
        except Exception as e:
            self.logger.error(f"Error loading backup history: {str(e)}")
            
    def update_files_tab_on_startup(self):
        """Update Files tab with initial data after startup"""
        try:
            if hasattr(self, 'files_text'):
                # Always scan for files on startup to ensure we have the latest
                if self.monitoring_path.get() and os.path.exists(self.monitoring_path.get()):
                    self.update_log("Scanning for files on startup...")
                    if hasattr(self, 'files_status_label'):
                        self.files_status_label.config(text="Scanning for files...", fg=self.colors['warning'])
                    self.scan_and_set_target_files()
                else:
                    # Show initial message if no monitoring path
                    self.files_text.delete(1.0, tk.END)
                    
                    message = f"MONITORING PATH: {self.monitoring_path.get()}\n"
                    message += "="*80 + "\n"
                    message += "FILES TAB - READY\n"
                    message += "="*80 + "\n\n"
                    message += "This tab displays filtered backup files from the monitoring folder.\n\n"
                    message += "To get started:\n"
                    message += "1. Select a backup folder using the 'Browse' button\n"
                    message += "2. Click '🔍 Scan Backup Files' to find the latest backup files\n"
                    message += "3. Or click '▶ Start Monitoring' to begin monitoring\n"
                    message += "4. Use 'Refresh Target' button to update the target files\n\n"
                    message += "The files will be filtered by the latest backup date found in the folder."
                    
                    self.files_text.insert(tk.END, message)
                    
                    # Update status label
                    if hasattr(self, 'files_status_label'):
                        self.files_status_label.config(text="Ready to scan", fg=self.colors['dark'])
                    
        except Exception as e:
            self.logger.error(f"Error updating files tab on startup: {str(e)}")
    
    def safe_refresh_dashboard(self):
        """Safely refresh dashboard after all components are created"""
        try:
            self.refresh_dashboard()
        except Exception as e:
            self.logger.error(f"Error in safe refresh dashboard: {str(e)}")

    def update_timestamp(self):
        """Update timestamp in status bar"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.timestamp_label.config(text=current_time)
        self.root.after(1000, self.update_timestamp)

    def refresh_dashboard(self):
        """Refresh dashboard data and display"""
        try:
            # Check if we're already refreshing to prevent multiple simultaneous refreshes
            if hasattr(self, '_refreshing') and self._refreshing:
                return
                
            self._refreshing = True
            self.update_log("Refreshing dashboard...")

            # Refresh backup history
            self.refresh_backup_history()

            # Update dashboard display only if dashboard components exist
            if hasattr(self, 'alert_count_label') and hasattr(self, 'last_update_label'):
                self.update_dashboard_display()
                # Update last update time
                self.last_update_label.config(text=f"Last Update: {datetime.now().strftime('%H:%M:%S')}")
                self.update_log("Dashboard refreshed successfully")
            else:
                self.update_log("Dashboard components not yet initialized, skipping refresh")

        except Exception as e:
            self.logger.error(f"Error refreshing dashboard: {str(e)}")
            self.update_log(f"Dashboard refresh error: {str(e)}")
        finally:
            self._refreshing = False

    def update_dashboard_display(self):
        """Update dashboard display with current data"""
        if not hasattr(self, 'summary_data') or not self.summary_data:
            return

        try:
            # Update critical alerts only if components exist
            if hasattr(self, 'alert_count_label'):
                self.update_critical_alerts()

            # Update metrics only if components exist
            if hasattr(self, 'metric_widgets'):
                self.update_metrics()

            # Update backup status cards only if components exist
            if hasattr(self, 'backup_cards_scrollable'):
                self.update_backup_status_cards()

            # Update recent activity only if components exist
            if hasattr(self, 'activity_text'):
                self.update_recent_activity()

        except Exception as e:
            self.logger.error(f"Error updating dashboard display: {str(e)}")

    def update_critical_alerts(self):
        """Update critical alerts section"""
        if not self.summary_data:
            return

        # Calculate critical metrics
        total_files = len(self.summary_data)
        valid_files = sum(1 for f in self.summary_data.values() if f.get('status') == 'Valid')
        invalid_files = total_files - valid_files
        outdated_files = sum(1 for f in self.summary_data.values() if f.get('is_outdated', False))

        # Count attention items
        attention_items = invalid_files + outdated_files

        # Update alert count
        self.alert_count_label.config(text=f"{attention_items} Items Need Attention")

        # Update critical info
        self.update_critical_info_cards()

    def update_critical_info_cards(self):
        """Update critical info cards"""
        if not self.summary_data:
            return

        # Clear existing
        for widget in self.critical_info_frame.winfo_children():
            widget.destroy()

        # Calculate metrics
        total_files = len(self.summary_data)
        valid_files = sum(1 for f in self.summary_data.values() if f.get('status') == 'Valid')
        outdated_files = sum(1 for f in self.summary_data.values() if f.get('is_outdated', False))

        # Get dates
        dates = [f.get('modified', '') for f in self.summary_data.values() if f.get('modified')]
        latest_date = max(dates) if dates else 'N/A'
        oldest_date = min(dates) if dates else 'N/A'

        # Critical info data
        critical_data = [
            ("Total Files", str(total_files)),
            ("Valid Files", str(valid_files)),
            ("Invalid Files", str(total_files - valid_files)),
            ("Outdated Files", str(outdated_files)),
            ("Latest Backup", latest_date[:16] if latest_date != 'N/A' else 'N/A'),
            ("Oldest Backup", oldest_date[:16] if oldest_date != 'N/A' else 'N/A')
        ]

        # Create cards
        for i, (label, value) in enumerate(critical_data):
            row, col = i // 3, i % 3

            frame = tk.Frame(self.critical_info_frame, bg=self.colors['critical_bg'])
            frame.grid(row=row, column=col, padx=10, pady=5, sticky='ew')

            label_widget = tk.Label(frame, text=label,
                                  font=('Segoe UI', 9, 'bold'),
                                  bg=self.colors['critical_bg'], fg=self.colors['critical_fg'])
            label_widget.pack(anchor='w')

            value_widget = tk.Label(frame, text=value,
                                  font=('Segoe UI', 11, 'bold'),
                                  bg=self.colors['critical_bg'], fg=self.colors['critical_fg'])
            value_widget.pack(anchor='w')

    def update_metrics(self):
        """Update metrics section"""
        if not self.summary_data:
            return

        # Calculate metrics
        total_files = len(self.summary_data)
        valid_files = sum(1 for f in self.summary_data.values() if f.get('status') == 'Valid')
        warning_files = sum(1 for f in self.summary_data.values() if 'warning' in str(f.get('status', '')).lower())
        error_files = total_files - valid_files - warning_files

        # Get latest backup date
        dates = [f.get('modified', '') for f in self.summary_data.values() if f.get('modified')]
        latest_backup = max(dates)[:10] if dates else 'Never'

        # System status
        if error_files > 0:
            system_status = "Error"
            status_color = self.colors['danger']
        elif warning_files > 0:
            system_status = "Warning"
            status_color = self.colors['warning']
        elif valid_files == total_files:
            system_status = "Healthy"
            status_color = self.colors['success']
        else:
            system_status = "Unknown"
            status_color = self.colors['dark']

        # Update metric cards
        self.metric_widgets["Total Backups"].config(text=str(total_files))
        self.metric_widgets["Valid Files"].config(text=str(valid_files))
        self.metric_widgets["Warnings"].config(text=str(warning_files))
        self.metric_widgets["Errors"].config(text=str(error_files))
        self.metric_widgets["Last Backup"].config(text=latest_backup)
        self.metric_widgets["System Status"].config(text=system_status, fg=status_color)

    def update_backup_status_cards(self):
        """Update backup status cards"""
        if not self.summary_data:
            return

        # Clear existing cards
        for widget in self.backup_cards_scrollable.winfo_children():
            widget.destroy()

        # Get filter
        filter_value = self.backup_status_filter.get()

        # Create cards for each backup file
        for file_path, file_info in self.summary_data.items():
            status = file_info.get('status', 'Unknown')

            # Apply filter
            if filter_value != "All":
                if filter_value == "Valid" and status != "Valid":
                    continue
                elif filter_value == "Warning" and 'warning' not in status.lower():
                    continue
                elif filter_value == "Error" and status == "Valid":
                    continue

            self.create_backup_card(file_path, file_info)

    def create_backup_card(self, file_path, file_info):
        """Create individual backup status card"""
        card_frame = tk.Frame(self.backup_cards_scrollable, bg=self.colors['white'], relief='raised', bd=1)
        card_frame.pack(fill=tk.X, padx=5, pady=5)

        # Header
        header_frame = tk.Frame(card_frame, bg=self.colors['white'])
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        # File name
        filename = os.path.basename(file_path)
        name_label = tk.Label(header_frame, text=filename,
                             font=('Segoe UI', 12, 'bold'),
                             bg=self.colors['white'], fg=self.colors['primary'])
        name_label.pack(side=tk.LEFT, anchor='w')

        # Status badge
        status = file_info.get('status', 'Unknown')
        status_color = self.colors['success'] if status == "Valid" else self.colors['danger']
        if 'warning' in status.lower():
            status_color = self.colors['warning']

        status_badge = tk.Label(header_frame, text=status,
                               bg=status_color, fg='white',
                               font=('Segoe UI', 8, 'bold'),
                               relief='raised', bd=1)
        status_badge.pack(side=tk.RIGHT, padx=5)

        # Details
        details_frame = tk.Frame(card_frame, bg=self.colors['white'])
        details_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # File information
        size_mb = file_info.get('size', 0) / (1024 * 1024)
        modified = file_info.get('modified', 'N/A')
        backup_type = file_info.get('backup_type', 'Unknown')

        # Calculate age
        try:
            mod_date = datetime.fromisoformat(modified.replace('Z', '+00:00'))
            age_days = (datetime.now() - mod_date).days
        except:
            age_days = 0

        # Create detail grid
        details = [
            ("Type", backup_type),
            ("Size", f"{size_mb:.1f} MB"),
            ("Modified", modified[:16] if modified != 'N/A' else 'N/A'),
            ("Age", f"{age_days} days")
        ]

        for i, (label, value) in enumerate(details):
            row, col = i // 2, i % 2

            label_widget = tk.Label(details_frame, text=f"{label}:",
                                  font=('Segoe UI', 9),
                                  bg=self.colors['white'], fg=self.colors['dark'])
            label_widget.grid(row=row, column=col*2, sticky='w', padx=(0, 5), pady=2)

            value_widget = tk.Label(details_frame, text=value,
                                  font=('Segoe UI', 9, 'bold'),
                                  bg=self.colors['white'], fg=self.colors['primary'])
            value_widget.grid(row=row, column=col*2+1, sticky='w', padx=(0, 20), pady=2)

    def update_recent_activity(self):
        """Update recent activity section"""
        if not hasattr(self, 'activity_text'):
            return

        # Clear existing
        self.activity_text.delete(1.0, tk.END)

        # Add recent activities
        activities = [
            f"{datetime.now().strftime('%H:%M:%S')} - Dashboard refreshed",
            f"{datetime.now().strftime('%H:%M:%S')} - Loaded {len(self.summary_data)} backup files"
        ]

        for activity in activities:
            self.activity_text.insert(tk.END, activity + "\n")

        self.activity_text.see(tk.END)

    def export_dashboard_data(self):
        """Export dashboard data to file"""
        try:
            if not self.summary_data:
                messagebox.showwarning("No Data", "No dashboard data to export")
                return

            # Create export data
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'total_files': len(self.summary_data),
                'summary_data': self.summary_data
            }

            # Save to file
            filename = f"dashboard_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

            messagebox.showinfo("Export Successful", f"Dashboard data exported to {filename}")
            self.update_log(f"Dashboard exported to {filename}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting dashboard: {str(e)}")
            self.logger.error(f"Error exporting dashboard: {str(e)}")

    def filter_backup_status(self):
        """Filter backup status cards"""
        self.update_backup_status_cards()

    # ============= CORE FUNCTIONALITY METHODS =============
    # These methods integrate with existing functionality

    def browse_path(self):
        """Browse for monitoring folder"""
        folder_selected = filedialog.askdirectory(title="Pilih Folder Backup")
        if folder_selected:
            self.monitoring_path.set(folder_selected)
            self.update_log(f"Monitor path changed to: {folder_selected}")

    def start_monitoring(self):
        """Start monitoring"""
        if not self.monitoring_path.get():
            messagebox.showerror("Error", "Silakan pilih folder untuk dimonitor")
            return

        self.is_monitoring = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.update_status("Monitoring aktif...")
        self.update_log("Monitoring dimulai...")

        # Update status indicator
        self.status_indicator.config(text="● Monitoring", fg=self.colors['warning'])

        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitoring_thread.start()

        # Always scan for latest files when monitoring starts
        self.update_log("Melakukan scan awal untuk file terbaru...")
        self.scan_and_set_target_files()
        self.update_log("Scan file terbaru selesai. File target telah disimpan untuk scheduler.")

    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.update_status("Monitoring dihentikan")
        self.update_log("Monitoring dihentikan.")

        # Update status indicator
        self.status_indicator.config(text="● Ready", fg=self.colors['success'])

    def monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Update displays
                self.update_monitored_files_display()

                # Auto-refresh dashboard if enabled (reduced frequency)
                if self.config.getboolean('UI', 'auto_refresh', fallback=True):
                    refresh_interval = self.config.getint('UI', 'refresh_interval', fallback=300)  # 5 minutes
                    current_time = int(time.time())
                    if not hasattr(self, 'last_refresh_time'):
                        self.last_refresh_time = 0
                    
                    # Only refresh if the interval has passed AND dashboard components exist
                    if (current_time - self.last_refresh_time >= refresh_interval and
                        hasattr(self, 'alert_count_label') and
                        hasattr(self, 'last_update_label')):
                        self.root.after(0, self.safe_refresh_dashboard)
                        self.last_refresh_time = current_time

                time.sleep(1)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(5)

    def scan_and_set_target_files(self):
        """Scan for latest backup files and set them as targets for scheduler"""
        scan_thread = threading.Thread(target=self._scan_and_set_target_files_thread, daemon=True)
        scan_thread.start()
        
    def _scan_and_set_target_files_thread(self):
        """Thread to scan and set target files for scheduler"""
        try:
            path = self.monitoring_path.get()
            if not path or not os.path.exists(path):
                self.update_log("Folder monitor tidak ditemukan.")
                self.update_status("Folder tidak ada")
                return

            self.update_log(f"Memindai file ZIP terbaru di: {path}")
            self.update_status("Scanning file terbaru...")

            # Find all ZIP files
            zip_files = self.find_zip_files(path)

            if not zip_files:
                self.update_log("Tidak ada file ZIP ditemukan.")
                self.update_status("Tidak ada file")
                return

            # Get latest date from ZIP files
            latest_date = self.get_latest_date(zip_files)
            self.latest_backup_date = latest_date
            
            # Get ALL files with the latest date using our new method
            filtered_files = self.get_all_files_by_date(path, latest_date)
            
            # Store target files for scheduler
            self.target_files_for_analysis = filtered_files
            
            self.update_log(f"Ditemukan {len(filtered_files)} file ZIP terbaru dengan tanggal {latest_date}")
            self.update_log(f"File-file ini telah disimpan sebagai target untuk scheduler")
            self.update_status(f"Found {len(filtered_files)} latest files")
            
            # Update target info label
            if hasattr(self, 'target_info_label'):
                self.root.after(0, lambda: self.target_info_label.config(
                    text=f"Target: {len(filtered_files)} files ({latest_date})"
                ))
            
            # Update Files tab with filtered files
            self.root.after(0, lambda: self.update_files_display_with_filtered(filtered_files, latest_date))

        except Exception as e:
            self.logger.error(f"Error scanning target files: {str(e)}")
            self.update_log(f"Error scanning target files: {str(e)}")
            self.update_status("Error scanning files")

    def refresh_target_files(self):
        """Manually refresh target files for scheduler"""
        self.update_log("Memperbarui file target secara manual...")
        self.scan_and_set_target_files()
        self.update_log("File target telah diperbarui. Lihat tab Files untuk detailnya.")

    def deep_scan_files(self):
        """Deep scan files (threaded)"""
        scan_thread = threading.Thread(target=self._deep_scan_thread, daemon=True)
        scan_thread.start()

    def _deep_scan_thread(self):
        """Deep scan thread implementation"""
        try:
            path = self.monitoring_path.get()
            if not path or not os.path.exists(path):
                self.update_log("Folder monitor tidak ditemukan.")
                self.update_status("Folder tidak ada")
                return

            self.update_log(f"Memulai DEEP SCAN: {path}")
            self.update_status("Deep scanning file...")

            # Scan logic (similar to original)
            zip_files = self.find_zip_files(path)

            if not zip_files:
                self.update_log("Tidak ada file ZIP ditemukan.")
                self.update_status("Tidak ada file")
                return

            # Filter and analyze files
            latest_date = self.get_latest_date(zip_files)
            # Get ALL files with the latest date using our new method
            filtered_files = self.get_all_files_by_date(path, latest_date)

            self.update_log(f"Ditemukan {len(filtered_files)} file ZIP untuk deep analysis")

            # Analyze files
            self.deep_analyze_files_threaded(filtered_files)

            # Update displays
            self.update_summary()
            self.refresh_dashboard()

            self.update_status("Deep scan selesai")

        except Exception as e:
            self.logger.error(f"Error deep scanning: {str(e)}")
            self.update_log(f"Error deep scanning: {str(e)}")
            self.update_status("Error deep scanning")

    def find_zip_files(self, path):
        """Find ZIP files in directory"""
        zip_files = []
        try:
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.lower().endswith('.zip'):
                        zip_files.append(os.path.join(root, file))
        except Exception as e:
            self.logger.error(f"Error finding ZIP files: {str(e)}")
        return zip_files

    def get_latest_date(self, zip_files):
        """Get latest date from ZIP files"""
        dates = []
        for zip_file in zip_files:
            try:
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.basename(zip_file))
                if date_match:
                    dates.append(date_match.group(1))
            except:
                pass
        return max(dates) if dates else datetime.now().strftime('%Y-%m-%d')

    def is_file_date(self, file_path, target_date):
        """Check if file matches target date"""
        try:
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.basename(file_path))
            return date_match and date_match.group(1) == target_date
        except:
            return False
            
    def get_all_files_by_date(self, path, target_date):
        """Get all files with the specified date from the backup folder"""
        try:
            # Find all ZIP files
            zip_files = self.find_zip_files(path)
            
            # Filter files based on target date
            filtered_files = [f for f in zip_files if self.is_file_date(f, target_date)]
            
            self.update_log(f"Found {len(filtered_files)} files with date {target_date}")
            return filtered_files
            
        except Exception as e:
            self.logger.error(f"Error getting files by date: {str(e)}")
            return []

    def deep_analyze_files_threaded(self, files):
        """Analyze files in threaded manner"""
        # This is a placeholder - implement the actual analysis logic
        # from the original application
        for file_path in files:
            try:
                # Basic file analysis
                file_info = {
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                    'status': 'Valid' if os.path.exists(file_path) else 'Invalid'
                }

                self.summary_data[file_path] = file_info

            except Exception as e:
                self.logger.error(f"Error analyzing {file_path}: {str(e)}")

    def update_summary(self):
        """Update summary display"""
        if hasattr(self, 'summary_text'):
            self.summary_text.delete(1.0, tk.END)

            # Generate summary text
            summary_lines = [
                "=" * 80,
                "BACKUP SUMMARY REPORT",
                "=" * 80,
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Total Files: {len(self.summary_data)}",
                "",
                "FILES ANALYZED:",
                "-" * 40
            ]

            for file_path, file_info in self.summary_data.items():
                filename = os.path.basename(file_path)
                status = file_info.get('status', 'Unknown')
                size_mb = file_info.get('size', 0) / (1024 * 1024)

                summary_lines.append(f"📁 {filename}")
                summary_lines.append(f"   Status: {status}")
                summary_lines.append(f"   Size: {size_mb:.1f} MB")
                summary_lines.append("")

            self.summary_text.insert(tk.END, "\n".join(summary_lines))

    def update_monitored_files_display(self):
        """Update monitored files display"""
        if hasattr(self, 'files_text'):
            self.files_text.delete(1.0, tk.END)

            if self.is_monitoring:
                # Display filtered files if available, otherwise show basic monitoring info
                if self.target_files_for_analysis and self.latest_backup_date:
                    self.update_files_display_with_filtered(self.target_files_for_analysis, self.latest_backup_date)
                else:
                    # If monitoring is active but no target files, scan for them
                    self.update_log("Monitoring is active but no target files. Scanning for files...")
                    self.scan_and_set_target_files()
    
    def update_files_display_with_filtered(self, filtered_files, latest_date):
        """Update Files tab with filtered files information"""
        if hasattr(self, 'files_text'):
            self.files_text.delete(1.0, tk.END)
            
            # Header information
            header_text = f"MONITORING PATH: {self.monitoring_path.get()}\n"
            header_text += f"Status: {'● Active' if self.is_monitoring else '● Inactive'}\n"
            header_text += f"Latest Backup Date: {latest_date}\n"
            header_text += f"Total Files with Date {latest_date}: {len(filtered_files)}\n"
            header_text += "=" * 80 + "\n\n"
            
            self.files_text.insert(tk.END, header_text)
            
            # Display filtered files
            if filtered_files:
                self.files_text.insert(tk.END, f"ALL BACKUP FILES WITH DATE {latest_date}:\n")
                self.files_text.insert(tk.END, "-" * 50 + "\n")
                self.files_text.insert(tk.END, "Note: These are ALL files with the latest date found in the backup folder.\n")
                self.files_text.insert(tk.END, "They will be used as targets for monitoring and scheduled analysis.\n\n")
                
                for i, file_path in enumerate(filtered_files, 1):
                    try:
                        filename = os.path.basename(file_path)
                        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
                        mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        mod_time_str = mod_time.strftime('%Y-%m-%d %H:%M:%S')
                        
                        # Determine backup type from filename
                        backup_type = "Unknown"
                        if "backupstaging" in filename.lower():
                            backup_type = "BackupStaging"
                        elif "backupvenuz" in filename.lower():
                            backup_type = "BackupVenus"
                        elif "plantwarep3" in filename.lower():
                            backup_type = "PlantwareP3"
                        
                        file_info = f"{i}. {filename}\n"
                        file_info += f"   Type: {backup_type}\n"
                        file_info += f"   Size: {file_size:.1f} MB\n"
                        file_info += f"   Modified: {mod_time_str}\n"
                        file_info += f"   Path: {file_path}\n"
                        file_info += "\n"
                        
                        self.files_text.insert(tk.END, file_info)
                    except Exception as e:
                        self.files_text.insert(tk.END, f"{i}. Error reading file: {file_path} - {str(e)}\n\n")
            else:
                self.files_text.insert(tk.END, "No files found with the latest date.\n")
                self.files_text.insert(tk.END, "Please check if the backup folder contains files with date patterns.\n")
            
            # Add footer information
            footer_text = "\n" + "=" * 80 + "\n"
            footer_text += f"Total Target Files: {len(filtered_files)}\n"
            footer_text += f"Latest Date: {latest_date}\n"
            footer_text += f"These files will be used for scheduled analysis.\n"
            footer_text += f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            self.files_text.insert(tk.END, footer_text)
            self.files_text.see(tk.END)

    def scan_files_for_tab(self):
        """Scan backup files specifically for Files tab"""
        if not self.monitoring_path.get():
            messagebox.showerror("Error", "Silakan pilih folder backup terlebih dahulu")
            return
            
        if not os.path.exists(self.monitoring_path.get()):
            messagebox.showerror("Error", "Folder backup tidak ditemukan")
            return
            
        # Update status
        if hasattr(self, 'files_status_label'):
            self.files_status_label.config(text="Scanning files...", fg=self.colors['warning'])
            
        self.update_log("Scanning backup files for Files tab...")
        
        # Run scan in background thread
        scan_thread = threading.Thread(target=self._scan_files_for_tab_thread, daemon=True)
        scan_thread.start()
        
    def _scan_files_for_tab_thread(self):
        """Background thread for scanning files for Files tab"""
        try:
            path = self.monitoring_path.get()
            self.update_log(f"Scanning path: {path}")
            
            # Find all ZIP files
            zip_files = self.find_zip_files(path)
            
            if not zip_files:
                self.root.after(0, lambda: self._show_no_files_message())
                return
                
            # Get latest date and filter files
            latest_date = self.get_latest_date(zip_files)
            # Get ALL files with the latest date using our new method
            filtered_files = self.get_all_files_by_date(path, latest_date)
            
            # Store target files
            self.target_files_for_analysis = filtered_files
            self.latest_backup_date = latest_date
            
            self.update_log(f"Found {len(filtered_files)} files with latest date: {latest_date}")
            
            # Update UI in main thread
            self.root.after(0, lambda: self.update_files_display_with_filtered(filtered_files, latest_date))
            
            # Update status
            if hasattr(self, 'files_status_label'):
                self.root.after(0, lambda: self.files_status_label.config(
                    text=f"Found {len(filtered_files)} files ({latest_date})",
                    fg=self.colors['success']
                ))
                
        except Exception as e:
            self.logger.error(f"Error scanning files for tab: {str(e)}")
            self.update_log(f"Error scanning files: {str(e)}")
            
            # Update status with error
            if hasattr(self, 'files_status_label'):
                self.root.after(0, lambda: self.files_status_label.config(
                    text="Error scanning files",
                    fg=self.colors['danger']
                ))
                
    def _show_no_files_message(self):
        """Show message when no files are found"""
        if hasattr(self, 'files_text'):
            self.files_text.delete(1.0, tk.END)
            
            message = f"MONITORING PATH: {self.monitoring_path.get()}\n"
            message += "="*80 + "\n"
            message += "NO BACKUP FILES FOUND\n"
            message += "="*80 + "\n\n"
            message += "No ZIP files found in the specified folder.\n"
            message += "Please check:\n"
            message += "1. The folder path is correct\n"
            message += "2. The folder contains backup files with .zip extension\n"
            message += "3. The backup files follow the naming convention (e.g., backupstaging_YYYY-MM-DD.zip)\n\n"
            message += "Use the 'Browse' button to select a different folder if needed."
            
            self.files_text.insert(tk.END, message)
            
        # Update status
        if hasattr(self, 'files_status_label'):
            self.files_status_label.config(text="No files found", fg=self.colors['warning'])
            
    def refresh_files_display(self):
        """Refresh the Files tab display"""
        if self.target_files_for_analysis and self.latest_backup_date:
            self.update_files_display_with_filtered(self.target_files_for_analysis, self.latest_backup_date)
            self.update_log("Files display refreshed")
        else:
            # If no target files, scan for them
            self.update_log("No target files available. Scanning for backup files...")
            if hasattr(self, 'files_status_label'):
                self.files_status_label.config(text="Scanning for files...", fg=self.colors['warning'])
            self.scan_and_set_target_files()

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

    # ============= SCHEDULER FUNCTIONALITY =============

    def toggle_scheduler(self):
        """Toggle scheduler with proper validation and feedback"""
        if self.scheduler_enabled.get():
            if self.validate_time_format(self.scheduler_time.get()):
                self.start_scheduler()
                # Initialize countdown immediately
                current_time = datetime.now()
                scheduled_time = self.scheduler_time.get()
                scheduled_datetime = current_time.replace(
                    hour=int(scheduled_time.split(':')[0]),
                    minute=int(scheduled_time.split(':')[1]),
                    second=0,
                    microsecond=0
                )
                
                # If scheduled time has passed today, schedule for tomorrow
                if scheduled_datetime <= current_time:
                    scheduled_datetime += timedelta(days=1)
                
                self.next_run_time = scheduled_datetime
                self.update_countdown()
            else:
                messagebox.showerror("Error", "Format waktu tidak valid. Gunakan format HH:MM (contoh: 08:00)")
                self.scheduler_enabled.set(False)
        else:
            self.stop_scheduler()
            # Clear countdown when disabled
            self.scheduler_countdown.set("Countdown: --:--:--")

    def start_scheduler_thread(self):
        """Start scheduler thread in background (always running)"""
        # Only start the scheduler thread if it's not already running
        if not hasattr(self, 'scheduler_thread') or self.scheduler_thread is None or not self.scheduler_thread.is_alive():
            self.scheduler_thread = threading.Thread(target=self.scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            self.logger.info("Scheduler thread started in background")

    def start_scheduler(self):
        """Start scheduler with proper status update"""
        # Ensure scheduler thread is running
        self.start_scheduler_thread()
        
        self.scheduler_running = True
        self.update_log("Scheduler harian diaktifkan")
        self.update_status("Scheduler aktif")
        # Update status label if exists
        if hasattr(self, 'scheduler_status_label'):
            self.scheduler_status_label.config(text="Scheduler: Aktif", foreground="green")
        self.save_scheduler_settings()
        self.update_log("Scheduler started")
        
        # Initialize countdown immediately
        current_time = datetime.now()
        scheduled_time = self.scheduler_time.get()
        if self.validate_time_format(scheduled_time):
            scheduled_datetime = current_time.replace(
                hour=int(scheduled_time.split(':')[0]),
                minute=int(scheduled_time.split(':')[1]),
                second=0,
                microsecond=0
            )
            
            # If scheduled time has passed today, schedule for tomorrow
            if scheduled_datetime <= current_time:
                scheduled_datetime += timedelta(days=1)
            
            self.next_run_time = scheduled_datetime
            self.update_countdown()

    def stop_scheduler(self):
        """Stop scheduler with proper status update"""
        self.scheduler_running = False
        self.scheduler_enabled.set(False)
        self.update_log("Scheduler harian dinonaktifkan")
        self.update_status("Scheduler non-aktif")
        # Update status label if exists
        if hasattr(self, 'scheduler_status_label'):
            self.scheduler_status_label.config(text="Scheduler: Non-aktif", foreground="gray")
        self.save_scheduler_settings()
        self.update_log("Scheduler stopped")

    def scheduler_loop(self):
        """Main scheduler loop with real-time countdown and execution"""
        last_execution_date = None  # Track last execution date to prevent multiple runs
        debug_counter = 0  # Debug counter to log every 60 seconds
        
        self.logger.info("Scheduler loop started")
        
        while True:
            try:
                debug_counter += 1
                
                # Only process if scheduler is enabled
                if not self.scheduler_enabled.get():
                    if debug_counter % 60 == 0:  # Log every 60 seconds when disabled
                        self.logger.debug("Scheduler is disabled")
                    time.sleep(1)
                    continue
                
                current_time = datetime.now()
                current_time_str = current_time.strftime("%H:%M:%S")
                current_date_str = current_time.strftime("%Y-%m-%d")
                scheduled_time = self.scheduler_time.get()

                # Debug logging every 60 seconds
                if debug_counter % 60 == 0:
                    self.logger.debug(f"Scheduler check - Current: {current_time_str}, Scheduled: {scheduled_time}, Last execution: {last_execution_date}")

                # Validate time format
                if not self.validate_time_format(scheduled_time):
                    self.logger.error(f"Invalid time format: {scheduled_time}")
                    time.sleep(1)
                    continue

                # Get scheduled hour and minute
                scheduled_hour = int(scheduled_time.split(':')[0])
                scheduled_minute = int(scheduled_time.split(':')[1])

                # Check if current time matches scheduled time (within the same minute)
                if (current_time.hour == scheduled_hour and
                    current_time.minute == scheduled_minute and
                    current_time.second < 10 and  # Only execute in first 10 seconds of the minute
                    last_execution_date != current_date_str):  # Prevent multiple executions in same day
                    
                    self.logger.info(f"*** EXECUTING SCHEDULED ANALYSIS at {current_time_str} ***")
                    self.update_log(f"*** Menjalankan scheduled analysis pada {current_time_str} ***")

                    # Mark as running to prevent multiple executions
                    self.scheduler_running = True
                    last_execution_date = current_date_str

                    # Execute comprehensive analysis in a separate thread to avoid blocking
                    analysis_thread = threading.Thread(
                        target=self.execute_comprehensive_scheduled_analysis,
                        daemon=True
                    )
                    analysis_thread.start()

                    # Wait for 60 seconds to prevent multiple executions
                    time.sleep(60)
                    
                    # Mark as not running after execution
                    self.scheduler_running = False
                else:
                    # Calculate next run time for countdown
                    scheduled_datetime = current_time.replace(
                        hour=scheduled_hour,
                        minute=scheduled_minute,
                        second=0,
                        microsecond=0
                    )
                    
                    # If scheduled time has passed today, schedule for tomorrow
                    if scheduled_datetime <= current_time:
                        scheduled_datetime += timedelta(days=1)
                    
                    self.next_run_time = scheduled_datetime

                    # Update countdown every second
                    self.update_countdown()

                # Check every 1 second for real-time updates
                time.sleep(1)

            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {str(e)}")
                self.update_log(f"Error scheduler: {str(e)}")
                time.sleep(5)  # Wait before retrying

    def execute_comprehensive_scheduled_analysis(self):
        """Execute comprehensive scheduled analysis with proper monitoring"""
        try:
            self.logger.info("=== Starting Scheduled Analysis ===")
            self.update_log("=== Memulai Scheduled Analysis ===")
            self.update_status("Scheduled analysis berjalan...")

            # Check if monitoring path is set
            if not self.monitoring_path.get():
                error_msg = "Error: Folder monitoring belum dipilih untuk scheduled analysis"
                self.logger.error(error_msg)
                self.update_log(error_msg)
                self.update_status("Error: Path tidak ada")
                return

            # Step 1: Initialize monitoring state
            was_monitoring = self.is_monitoring
            self.is_monitoring = True
            
            # Update UI buttons if they exist
            if hasattr(self, 'start_btn') and hasattr(self, 'stop_btn'):
                self.root.after(0, lambda: self.start_btn.config(state=tk.DISABLED))
                self.root.after(0, lambda: self.stop_btn.config(state=tk.NORMAL))

            # Step 2: Update monitored files display
            self.root.after(0, self.update_monitored_files_display)

            # Step 3: Use target files if available, otherwise scan for new files
            if self.target_files_for_analysis:
                # Use previously scanned target files
                filtered_files = self.target_files_for_analysis
                latest_date = self.latest_backup_date
                self.update_log(f"Menggunakan {len(filtered_files)} file target yang sudah di-scan sebelumnya ({latest_date})")
            else:
                # Scan for new files if no target files available
                self.update_log("Tidak ada file target, melakukan scan baru...")
                path = self.monitoring_path.get()
                self.logger.info(f"Scanning path: {path}")
                self.update_log(f"Memindai path: {path}")
                
                zip_files = self.find_zip_files(path)

                if not zip_files:
                    error_msg = "Tidak ada file backup ditemukan untuk scheduled analysis"
                    self.logger.error(error_msg)
                    self.update_log(error_msg)
                    # Reset monitoring state
                    self.is_monitoring = was_monitoring
                    if hasattr(self, 'start_btn') and hasattr(self, 'stop_btn'):
                        self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
                        self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
                    return

                # Get latest date and filter files
                latest_date = self.get_latest_date(zip_files)
                # Get ALL files with the latest date using our new method
                filtered_files = self.get_all_files_by_date(path, latest_date)
                self.target_files_for_analysis = filtered_files
                self.latest_backup_date = latest_date

                self.update_log(f"Ditemukan {len(filtered_files)} file terbaru ({latest_date})")

            # Step 4: Perform deep analysis
            self.logger.info("Starting deep analysis of files")
            self.update_log(f"Menganalisis {len(filtered_files)} file backup...")
            self.deep_analyze_files_threaded(filtered_files)

            # Step 5: Update summary
            self.root.after(0, self.update_summary)

            # Step 6: Update dashboard
            self.root.after(0, self.refresh_dashboard)

            # Step 7: Send email report
            self.logger.info("Preparing to send email report")
            self.update_log("Mempersiapkan pengiriman email laporan...")
            self.root.after(1000, self.send_deep_analysis_email)  # Delay to ensure UI updates

            # Step 8: Generate PDF report if available
            if hasattr(self, 'generate_pdf_report'):
                self.root.after(2000, self.generate_pdf_report)

            self.update_log("=== Scheduled Analysis Selesai ===")
            self.update_status("Scheduled analysis selesai")
            self.logger.info("=== Scheduled Analysis Completed ===")

            # Reset monitoring state
            self.is_monitoring = was_monitoring
            if hasattr(self, 'start_btn') and hasattr(self, 'stop_btn'):
                self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))

        except Exception as e:
            error_msg = f"Error in comprehensive scheduled analysis: {str(e)}"
            self.logger.error(error_msg)
            self.update_log(f"Error scheduled analysis: {str(e)}")
            self.update_status("Error scheduled analysis")
            
            # Reset monitoring state on error
            self.is_monitoring = False
            if hasattr(self, 'start_btn') and hasattr(self, 'stop_btn'):
                self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))

    def save_scheduler_settings(self):
        """Save scheduler settings"""
        try:
            self.config.set('SCHEDULER', 'enabled', str(self.scheduler_enabled.get()).lower())
            self.config.set('SCHEDULER', 'execution_time', self.scheduler_time.get())

            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)

        except Exception as e:
            self.logger.error(f"Error saving scheduler settings: {str(e)}")

    def load_scheduler_settings(self):
        """Load scheduler settings"""
        try:
            scheduler_enabled = self.config.getboolean('SCHEDULER', 'enabled', fallback=False)
            scheduler_time = self.config.get('SCHEDULER', 'execution_time', fallback='08:00')

            self.scheduler_enabled.set(scheduler_enabled)
            self.scheduler_time.set(scheduler_time)

            self.logger.info(f"Scheduler settings loaded - Enabled: {scheduler_enabled}, Time: {scheduler_time}")

            # Start scheduler thread if enabled, but it will only run when scheduler_enabled is True
            if scheduler_enabled:
                self.logger.info("Scheduler is enabled, starting background thread")
                self.start_scheduler()
            else:
                self.scheduler_running = False

        except Exception as e:
            self.logger.error(f"Error loading scheduler settings: {str(e)}")

    def validate_time_format(self, time_str):
        """Validate time format HH:MM"""
        try:
            time_parts = time_str.split(':')
            if len(time_parts) != 2:
                return False

            hour = int(time_parts[0])
            minute = int(time_parts[1])

            return 0 <= hour <= 23 and 0 <= minute <= 59
        except:
            return False

    def set_scheduler_time(self):
        """Set scheduler time with validation"""
        time_str = self.scheduler_time.get()
        
        if not self.validate_time_format(time_str):
            messagebox.showerror("Error", "Format waktu tidak valid. Gunakan format HH:MM (contoh: 08:00)")
            return
        
        # Save the settings
        self.save_scheduler_settings()
        
        # Force update countdown immediately
        if self.scheduler_enabled.get():
            # Calculate new next run time
            current_time = datetime.now()
            scheduled_datetime = current_time.replace(
                hour=int(time_str.split(':')[0]),
                minute=int(time_str.split(':')[1]),
                second=0,
                microsecond=0
            )
            
            # If scheduled time has passed today, schedule for tomorrow
            if scheduled_datetime <= current_time:
                scheduled_datetime += timedelta(days=1)
            
            self.next_run_time = scheduled_datetime
            self.update_countdown()
        
        self.update_log(f"Scheduler time set to: {time_str}")
        messagebox.showinfo("Success", f"Scheduler time berhasil diatur ke: {time_str}")

    def update_countdown(self):
        """Update countdown display"""
        if not self.scheduler_enabled.get() or not self.next_run_time:
            self.scheduler_countdown.set("Countdown: --:--:--")
            return
        
        try:
            now = datetime.now()
            time_diff = self.next_run_time - now
            
            if time_diff.total_seconds() <= 0:
                self.scheduler_countdown.set("Countdown: Menjalankan...")
                return
            
            # Calculate hours, minutes, seconds
            total_seconds = int(time_diff.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            countdown_str = f"Countdown: {hours:02d}:{minutes:02d}:{seconds:02d}"
            
            # Update UI in main thread
            self.root.after(0, lambda: self.scheduler_countdown.set(countdown_str))
            
        except Exception as e:
            self.logger.error(f"Error updating countdown: {str(e)}")
            self.root.after(0, lambda: self.scheduler_countdown.set("Countdown: Error"))

    def run_scheduler_now(self):
        """Run scheduler task immediately"""
        try:
            self.update_log("Menjalankan scheduler task secara manual...")
            
            # Show confirmation dialog
            result = messagebox.askyesno(
                "Konfirmasi",
                "Apakah Anda ingin menjalankan scheduled analysis sekarang?"
            )
            
            if result:
                # Execute the comprehensive analysis in a separate thread
                analysis_thread = threading.Thread(
                    target=self.execute_comprehensive_scheduled_analysis,
                    daemon=True
                )
                analysis_thread.start()
                
                self.update_log("Scheduled analysis dimulai secara manual")
            else:
                self.update_log("Scheduled analysis dibatalkan")
                
        except Exception as e:
            self.logger.error(f"Error running scheduler now: {str(e)}")
            self.update_log(f"Error menjalankan scheduler: {str(e)}")
            messagebox.showerror("Error", f"Gagal menjalankan scheduler: {str(e)}")

    def save_email_settings(self):
        """Save email recipient settings"""
        try:
            email = self.recipient_email.get().strip()
            if not email:
                messagebox.showerror("Error", "Alamat email tidak boleh kosong")
                return
            
            # Basic email validation
            if '@' not in email or '.' not in email.split('@')[-1]:
                messagebox.showerror("Error", "Format email tidak valid")
                return
            
            # Save to config
            self.config.set('EMAIL', 'recipient_email', email)
            
            # Write to file
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
            
            self.update_log(f"Email tujuan disimpan: {email}")
            messagebox.showinfo("Success", f"Email tujuan berhasil disimpan: {email}")
            
        except Exception as e:
            self.logger.error(f"Error saving email settings: {str(e)}")
            messagebox.showerror("Error", f"Gagal menyimpan pengaturan email: {str(e)}")

    # ============= EMAIL FUNCTIONALITY =============

    def send_test_email(self):
        """Send test email with proper SMTP configuration"""
        try:
            self.update_log("Sending test email...")

            # Create test message with multipart/alternative
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config.get('EMAIL', 'sender_email')
            msg['To'] = self.config.get('EMAIL', 'recipient_email')
            msg['Subject'] = "Test Email - Professional Backup Monitor"

            # Create HTML version
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .info {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Test Email - Professional Backup Monitor</h1>
    </div>
    <div class="content">
        <p>Ini adalah email tes untuk memverifikasi konfigurasi email sistem Professional Backup Monitor.</p>
        
        <div class="info">
            <h3>Informasi Sistem:</h3>
            <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Status:</strong> <span style="color: green;">✓ Sistem Operasional</span></p>
            <p><strong>Monitor Path:</strong> {self.monitoring_path.get()}</p>
            <p><strong>Jumlah File Aktif:</strong> {len(self.summary_data)}</p>
        </div>
        
        <p>Email ini dikirim menggunakan konfigurasi SMTP yang telah diatur dalam sistem.</p>
        <p>Jika Anda menerima email ini, berarti konfigurasi email sudah benar.</p>
        
        <hr>
        <p><em>Professional Backup Monitor v4.0 - Sistem Monitoring Backup Database</em></p>
    </div>
</body>
</html>
            """

            # Create plain text version
            text_body = f"""
TEST EMAIL - PROFESSIONAL BACKUP MONITOR
======================================

Ini adalah email tes untuk memverifikasi konfigurasi email sistem Professional Backup Monitor.

Informasi Sistem:
- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Status: Sistem Operasional
- Monitor Path: {self.monitoring_path.get()}
- Jumlah File Aktif: {len(self.summary_data)}

Email ini dikirim menggunakan konfigurasi SMTP yang telah diatur dalam sistem.
Jika Anda menerima email ini, berarti konfigurasi email sudah benar.

---
Professional Backup Monitor v4.0 - Sistem Monitoring Backup Database
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """

            # Attach both versions
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))

            # Send email with actual SMTP logic
            if self.send_email_smtp(msg):
                self.update_log("Test email sent successfully")
                messagebox.showinfo("Email Sent", "Email tes berhasil dikirim!")
            else:
                self.update_log("Failed to send test email")
                messagebox.showerror("Email Failed", "Gagal mengirim email tes")

        except Exception as e:
            self.logger.error(f"Error sending test email: {str(e)}")
            self.update_log(f"Error sending test email: {str(e)}")
            messagebox.showerror("Email Error", f"Error sending email: {str(e)}")

    def send_deep_analysis_email(self):
        """Send deep analysis email with HTML and plain text versions"""
        try:
            self.update_log("Generating deep analysis email...")

            # Create comprehensive email report with multipart/alternative
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config.get('EMAIL', 'sender_email')
            msg['To'] = self.config.get('EMAIL', 'recipient_email')
            msg['Subject'] = f"Laporan Analisis Backup - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            # Generate HTML report
            html_report = self.generate_html_report()
            
            # Generate plain text version
            plain_text_report = self.generate_plain_text_version(html_report)

            # Attach both versions
            msg.attach(MIMEText(plain_text_report, 'plain'))
            msg.attach(MIMEText(html_report, 'html'))

            # Send email with actual SMTP logic
            if self.send_email_smtp(msg):
                self.update_log("Deep analysis email sent successfully")
                messagebox.showinfo("Report Sent", "Laporan analisis backup berhasil dikirim")
            else:
                self.update_log("Failed to send deep analysis email")
                messagebox.showerror("Report Failed", "Gagal mengirim laporan analisis")

        except Exception as e:
            self.logger.error(f"Error sending deep analysis email: {str(e)}")
            self.update_log(f"Error sending deep analysis email: {str(e)}")
            messagebox.showerror("Email Error", f"Error sending email: {str(e)}")

    def generate_html_report(self):
        """Generate template email deep analysis profesional dalam format HTML Bahasa Indonesia"""
        if not self.summary_data:
            return "<html><body><p>Tidak ada data deep analysis untuk ditampilkan</p></body></html>"

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
            .detail-item {{
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
            modified_time = file_info.get('modified', 'Unknown')
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
            size = file_info.get('size', 0) / (1024 * 1024)  # Convert to MB
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
                        <span class="detail-value">{size:.1f} MB</span>
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
                    <div class="stat-number">Professional Backup Monitor v4.0</div>
                    <div class="stat-label">Versi Sistem</div>
                </div>
            </div>
        </div>
    </div>

    <div class="footer">
        <p><strong>Sistem Monitoring Backup Database</strong></p>
        <p>Dibuat: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Professional Backup Monitor v4.0 - Analisis Real-time dengan 12 Parameter Validasi</p>
    </div>
</body>
</html>
"""

        return body

    def generate_zip_summary(self, scan_results):
        """Generate ZIP Summary dengan analisis komprehensif (from enhanced version)"""
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
                    'filename': os.path.basename(file_info.get('path', '')),
                    'size': size,
                    'size_formatted': self.format_size(size)
                }

            if zip_summary['smallest_file'] is None or size < zip_summary['smallest_file']['size']:
                zip_summary['smallest_file'] = {
                    'filename': os.path.basename(file_info.get('path', '')),
                    'size': size,
                    'size_formatted': self.format_size(size)
                }

            # Age analysis
            try:
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
                        'filename': os.path.basename(file_info.get('path', '')),
                        'modified': file_info.get('modified'),
                        'days_ago': days_diff
                    }

                if zip_summary['age_analysis']['newest_file'] is None or days_diff < zip_summary['age_analysis']['newest_file']['days_ago']:
                    zip_summary['age_analysis']['newest_file'] = {
                        'filename': os.path.basename(file_info.get('path', '')),
                        'modified': file_info.get('modified'),
                        'days_ago': days_diff
                    }
            except:
                pass

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

    def generate_bak_summary(self, scan_results):
        """Generate BAK Summary dengan analisis mendalam (from enhanced version)"""
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
            'bak_files': []  # Add list to store all BAK file details
        }

        # Analyze BAK files from deep analysis
        files = scan_results.get('files', [])

        for file_info in files:
            deep_analysis = file_info.get('deep_analysis', {})
            extracted_files = deep_analysis.get('extracted_files', [])

            for bak_file in extracted_files:
                bak_summary['total_bak_files'] += 1

                size = bak_file.get('size', 0)
                backup_type = bak_file.get('backup_type', 'Unknown')

                # Store BAK file details for email template
                bak_summary['bak_files'].append({
                    'filename': bak_file.get('filename', 'Unknown'),
                    'backup_type': backup_type,
                    'size': size,
                    'size_warning': bak_file.get('size_warning', False),
                    'is_outdated': bak_file.get('is_outdated', False),
                    'days_since_backup': bak_file.get('days_since_backup', 0),
                    'backup_date': file_info.get('modified', 'Unknown'),  # Use ZIP file date as backup date
                    'extraction_failed': bak_file.get('extraction_failed', False),
                    'dbatools_analysis': bak_file.get('dbatools_analysis', {}),
                    'file_date_one_day_different': bak_file.get('file_date_one_day_different', False),
                    'excluded': bak_file.get('excluded', False)
                })

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

        return bak_summary

    def format_size(self, size_bytes):
        """Format size dalam format yang mudah dibaca"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    def send_email_smtp(self, msg):
        """Send email using SMTP with proper configuration and error handling"""
        try:
            # Get email configuration
            smtp_server = self.config.get('EMAIL', 'smtp_server')
            smtp_port = int(self.config.get('EMAIL', 'smtp_port'))
            sender_email = self.config.get('EMAIL', 'sender_email')
            sender_password = self.config.get('EMAIL', 'sender_password')
            recipient_email = self.config.get('EMAIL', 'recipient_email')

            # Create SMTP session with timeout
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
            server.starttls()  # Secure the connection
            
            # Login with sender's email and password
            server.login(sender_email, sender_password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(sender_email, recipient_email, text)
            server.quit()
            
            self.logger.info(f"Email sent successfully to {recipient_email}")
            self.update_log(f"Email berhasil dikirim ke {recipient_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP Authentication Error: {str(e)}"
            self.logger.error(error_msg)
            self.update_log(f"Error autentikasi email: Periksa username/password")
            messagebox.showerror("Email Error", "Gagal login ke email server. Periksa username dan password.")
            return False
            
        except smtplib.SMTPRecipientsRefused as e:
            error_msg = f"SMTP Recipients Refused: {str(e)}"
            self.logger.error(error_msg)
            self.update_log(f"Error penerima email: {recipient_email} ditolak")
            messagebox.showerror("Email Error", f"Email penerima {recipient_email} ditolak server.")
            return False
            
        except smtplib.SMTPServerDisconnected as e:
            error_msg = f"SMTP Server Disconnected: {str(e)}"
            self.logger.error(error_msg)
            self.update_log(f"Koneksi ke server email terputus")
            messagebox.showerror("Email Error", "Koneksi ke server email terputus. Coba lagi.")
            return False
            
        except smtplib.SMTPException as e:
            error_msg = f"SMTP Error: {str(e)}"
            self.logger.error(error_msg)
            self.update_log(f"Error SMTP: {str(e)}")
            messagebox.showerror("Email Error", f"Terjadi error SMTP: {str(e)}")
            return False
            
        except Exception as e:
            error_msg = f"General Email Error: {str(e)}"
            self.logger.error(error_msg)
            self.update_log(f"Error pengiriman email: {str(e)}")
            messagebox.showerror("Email Error", f"Gagal mengirim email: {str(e)}")
            return False

    def generate_plain_text_version(self, html_content):
        """Generate plain text version from HTML content"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Get text and clean it up
            text = soup.get_text()
            
            # Break into lines and remove leading/trailing space on each
            lines = (line.strip() for line in text.splitlines())
            
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Add proper header
            plain_text = f"""
LAPORAN ANALISIS BACKUP DATABASE
================================

{text}

---
Generated by Professional Backup Monitor v4.0
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            return plain_text
            
        except ImportError:
            # Fallback if BeautifulSoup is not available
            import re
            
            # Remove HTML tags
            text = re.sub('<[^<]+?>', '', html_content)
            
            # Clean up whitespace
            text = re.sub('\s+', ' ', text).strip()
            
            # Add header
            plain_text = f"""
LAPORAN ANALISIS BACKUP DATABASE
================================

{text}

---
Generated by Professional Backup Monitor v4.0
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            return plain_text

    # ============= BACKUP HISTORY FUNCTIONALITY =============

    def load_backup_history_on_startup(self):
        """Load backup history on startup"""
        try:
            self.refresh_backup_history()
        except Exception as e:
            self.logger.error(f"Error loading backup history: {str(e)}")

    def refresh_backup_history(self):
        """Refresh backup history from JSON"""
        try:
            json_file = "backup_summary_enhanced.json"

            if not os.path.exists(json_file):
                self.update_log(f"Backup history file not found: {json_file}")
                return

            with open(json_file, 'r', encoding='utf-8') as f:
                self.summary_data = json.load(f)

            self.update_log(f"Loaded {len(self.summary_data)} backup files from JSON")

            # Extract target files from summary data for Files tab
            if self.summary_data:
                # Get all file paths from summary data
                all_files = list(self.summary_data.keys())
                
                # Find latest date from files
                dates = []
                for file_path in all_files:
                    try:
                        filename = os.path.basename(file_path)
                        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
                        if date_match:
                            dates.append(date_match.group(1))
                    except:
                        pass
                
                if dates:
                    latest_date = max(dates)
                    # Get ALL files with the latest date using our new method
                    # We need to get the monitoring path to use our new method
                    monitoring_path = self.monitoring_path.get()
                    if monitoring_path and os.path.exists(monitoring_path):
                        filtered_files = self.get_all_files_by_date(monitoring_path, latest_date)
                    else:
                        # Fallback to original method if path is not available
                        filtered_files = [f for f in all_files if self.is_file_date(f, latest_date)]
                    
                    self.target_files_for_analysis = filtered_files
                    self.latest_backup_date = latest_date
                    
                    self.update_log(f"Extracted {len(filtered_files)} target files with date {latest_date}")

            # Update all displays
            self.update_summary()
            if hasattr(self, 'history_text'):
                self.update_history_display()
            self.refresh_dashboard()

        except Exception as e:
            self.logger.error(f"Error refreshing backup history: {str(e)}")
            self.update_log(f"Error refreshing backup history: {str(e)}")

    def update_history_display(self):
        """Update history display"""
        if not hasattr(self, 'history_text') or not self.summary_data:
            return

        self.history_text.delete(1.0, tk.END)

        # Header
        self.history_text.insert(tk.END, "=" * 80 + "\n")
        self.history_text.insert(tk.END, "BACKUP HISTORY - OVERVIEW\n")
        self.history_text.insert(tk.END, "=" * 80 + "\n\n")

        # Summary statistics
        total_files = len(self.summary_data)
        valid_files = sum(1 for f in self.summary_data.values() if f.get('status') == 'Valid')

        self.history_text.insert(tk.END, f"Total Files: {total_files}\n")
        self.history_text.insert(tk.END, f"Valid Files: {valid_files}\n")
        self.history_text.insert(tk.END, f"Invalid Files: {total_files - valid_files}\n")
        self.history_text.insert(tk.END, "-" * 40 + "\n\n")

        # File details
        for file_path, file_info in self.summary_data.items():
            filename = os.path.basename(file_path)
            status = file_info.get('status', 'Unknown')
            size_mb = file_info.get('size', 0) / (1024 * 1024)

            self.history_text.insert(tk.END, f"📁 {filename}\n")
            self.history_text.insert(tk.END, f"   Status: {status}\n")
            self.history_text.insert(tk.END, f"   Size: {size_mb:.1f} MB\n")
            self.history_text.insert(tk.END, f"   Modified: {file_info.get('modified', 'N/A')[:16]}\n")
            self.history_text.insert(tk.END, "\n")


def main():
    """Main function to run the professional backup monitor"""
    root = tk.Tk()
    app = ProfessionalBackupMonitorUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()