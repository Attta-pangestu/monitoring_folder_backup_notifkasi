import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
from datetime import datetime
from email_notifier import EmailNotifier
from folder_monitor import FolderMonitor
from zip_validator import ZipValidator
from database_validator import DatabaseValidator
from monitoring_controller import MonitoringController

class DatabaseBackupMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Database Backup Monitor")
        self.root.geometry("800x700")
        
        # Initialize components
        self.email_notifier = EmailNotifier()
        self.folder_monitor = FolderMonitor()
        self.zip_validator = ZipValidator()
        self.database_validator = DatabaseValidator()
        self.monitoring_controller = MonitoringController()
        
        # Variables
        self.smtp_server = tk.StringVar()
        self.smtp_port = tk.StringVar(value="587")
        self.email_user = tk.StringVar()
        self.email_password = tk.StringVar()
        self.recipient_email = tk.StringVar()
        self.backup_file_path = tk.StringVar()
        self.monitoring_path = tk.StringVar()
        self.status_text = tk.StringVar(value="Ready")
        
        # Auto-monitoring variables
        self.auto_monitoring = False
        self.monitoring_thread = None
        
        self.create_widgets()

    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text="Database Backup Monitor",
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Email Configuration Section
        email_frame = ttk.LabelFrame(main_frame, text="Email Configuration", padding="10")
        email_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        email_frame.columnconfigure(1, weight=1)

        ttk.Label(email_frame, text="Sender Email:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.sender_email_var = tk.StringVar(value=self.email_notifier.sender_email)
        ttk.Entry(email_frame, textvariable=self.sender_email_var, width=40).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)

        ttk.Label(email_frame, text="Receiver Email:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.receiver_email_var = tk.StringVar(value=self.email_notifier.receiver_email)
        ttk.Entry(email_frame, textvariable=self.receiver_email_var, width=40).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)

        ttk.Label(email_frame, text="Password:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.password_var = tk.StringVar(value=self.email_notifier.sender_password)
        self.password_entry = ttk.Entry(email_frame, textvariable=self.password_var, width=40, show="*")
        self.password_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)

        # Backup File Selection
        backup_frame = ttk.LabelFrame(main_frame, text="Backup File Selection", padding="10")
        backup_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        backup_frame.columnconfigure(1, weight=1)

        ttk.Label(backup_frame, text="Backup File Path:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(backup_frame, textvariable=self.backup_file_path, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        ttk.Button(backup_frame, text="Browse", command=self.browse_file).grid(row=0, column=2, pady=2, padx=(5, 0))

        # Folder Monitoring Section
        monitor_frame = ttk.LabelFrame(main_frame, text="Folder Monitoring", padding="10")
        monitor_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        monitor_frame.columnconfigure(1, weight=1)

        ttk.Label(monitor_frame, text="Monitoring Path:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(monitor_frame, textvariable=self.monitoring_path, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        ttk.Button(monitor_frame, text="Browse Folder", command=self.browse_folder).grid(row=0, column=2, pady=2, padx=(5, 0))

        # Monitoring buttons
        button_frame = ttk.Frame(monitor_frame)
        button_frame.grid(row=1, column=0, columnspan=3, pady=(10, 0))

        ttk.Button(button_frame, text="🔍 Scan Latest Backups",
                  command=self.scan_latest_backups).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(button_frame, text="📊 Analyze & Extract",
                  command=self.analyze_extract_backups).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(button_frame, text="📋 Lihat Metadata ZIP",
                  command=self.show_zip_metadata).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(button_frame, text="✅ Validate ZIP Files",
                  command=self.validate_zip_files).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(button_frame, text="🗄️ Check Databases",
                  command=self.check_databases).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(button_frame, text="📈 Full Monitoring",
                  command=self.run_full_monitoring).grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(button_frame, text="📧 Send Report",
                  command=self.send_folder_report).grid(row=2, column=0, columnspan=3, padx=5, pady=5)

        # Auto Monitoring section
        auto_frame = ttk.Frame(monitor_frame)
        auto_frame.grid(row=2, column=0, columnspan=3, pady=(10, 0))

        self.auto_monitor_var = tk.BooleanVar()
        ttk.Checkbutton(auto_frame, text="Auto Monitoring (every 1 hour)",
                       variable=self.auto_monitor_var,
                       command=self.toggle_auto_monitoring).grid(row=0, column=0, padx=5, pady=5)

        ttk.Button(auto_frame, text="▶️ Start Auto Monitor",
                  command=self.start_auto_monitoring).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(auto_frame, text="⏹️ Stop Auto Monitor",
                  command=self.stop_auto_monitoring).grid(row=0, column=2, padx=5, pady=5)

        # Initialize auto monitoring variables
        self.auto_monitoring_active = False
        self.auto_monitor_thread = None

        # Manual Test Section
        test_frame = ttk.LabelFrame(main_frame, text="Manual Testing", padding="10")
        test_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Button(test_frame, text="Test Email Connection",
                  command=self.test_email_connection).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(test_frame, text="Send Test Notification",
                  command=self.send_test_notification).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(test_frame, text="Generate Dummy Report",
                  command=self.generate_dummy_report).grid(row=0, column=2, padx=5, pady=5)

        # Status Section
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(0, weight=1)

        self.status_label = ttk.Label(status_frame, textvariable=self.status_text,
                                     font=('Arial', 10, 'bold'))
        self.status_label.grid(row=0, column=0, sticky=tk.W)

        # Progress Bar
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

        # Log Section
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="10")
        log_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)

        # Create scrollable text widget
        self.log_text = tk.Text(log_frame, height=10, width=70)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Add context menu
        self.create_context_menu()

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Clear Log", command=self.clear_log)
        self.context_menu.add_command(label="Copy Selected", command=self.copy_selected)

        self.log_text.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def copy_selected(self):
        try:
            selected_text = self.log_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
        except:
            pass

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select Backup File",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
        )
        if filename:
            self.backup_file_path.set(filename)
            self.log_message(f"Backup file selected: {filename}")

    def log_message(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def update_status(self, status):
        self.status_text.set(status)
        self.log_message(f"Status: {status}")

    def test_email_connection(self):
        def test_connection():
            try:
                self.progress.start()
                self.update_status("Testing email connection...")

                # Update notifier with current values
                self.notifier.sender_email = self.sender_email_var.get()
                self.notifier.sender_password = self.password_var.get()
                self.notifier.receiver_email = self.receiver_email_var.get()

                success, message = self.notifier.send_notification(
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
                self.update_status("Connection test failed")
                messagebox.showerror("Error", f"Connection test failed: {str(e)}")
            finally:
                self.progress.stop()

        thread = threading.Thread(target=test_connection)
        thread.daemon = True
        thread.start()

    def send_test_notification(self):
        def send_notification():
            try:
                self.progress.start()
                self.update_status("Sending test notification...")

                backup_info = {
                    'filename': os.path.basename(self.backup_file_path.get() or "test_backup.zip"),
                    'size': 125.5,
                    'backup_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'Test Mode',
                    'query_results': {
                        'Users': '2023-10-01',
                        'Transactions': '2023-10-01',
                        'Logs': '2023-10-01'
                    },
                    'errors': []
                }

                success, message = self.notifier.send_backup_report(backup_info)

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

        thread = threading.Thread(target=send_notification)
        thread.daemon = True
        thread.start()

    def generate_dummy_report(self):
        def generate_report():
            try:
                self.progress.start()
                self.update_status("Generating dummy report...")

                # Simulate processing
                import time
                time.sleep(2)

                # Create dummy backup info
                backup_info = {
                    'filename': 'dummy_backup_20231001.zip',
                    'size': 256.8,
                    'backup_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'Success',
                    'query_results': {
                        'Users': '2023-10-01 14:30:00',
                        'Transactions': '2023-10-01 14:29:45',
                        'Logs': '2023-10-01 14:28:30'
                    },
                    'errors': []
                }

                self.log_message(f"Generated dummy report for {backup_info['filename']}")
                self.log_message(f"File size: {backup_info['size']} MB")
                self.log_message(f"Last records:")
                for table, date in backup_info['query_results'].items():
                    self.log_message(f"  - {table}: {date}")

                self.update_status("Dummy report generated")

            except Exception as e:
                self.update_status("Failed to generate report")
                messagebox.showerror("Error", f"Failed to generate report: {str(e)}")
            finally:
                self.progress.stop()

        thread = threading.Thread(target=generate_report)
        thread.daemon = True
        thread.start()

    # Folder Monitoring Methods
    def browse_folder(self):
        folder_path = filedialog.askdirectory(title="Select Folder to Monitor")
        if folder_path:
            self.monitoring_path.set(folder_path)
            self.folder_monitor.set_monitoring_path(folder_path)
            self.log_message(f"Monitoring folder set to: {folder_path}")

    def scan_latest_backups(self):
        def scan_folder():
            try:
                self.progress.start()
                self.update_status("Scanning for latest backups...")

                if not self.monitoring_path.get():
                    messagebox.showwarning("Warning", "Please select a monitoring folder first!")
                    return

                self.folder_monitor.set_monitoring_path(self.monitoring_path.get())
                zip_files, latest_date = self.folder_monitor.get_latest_zip_files_by_date()

                if zip_files:
                    self.log_message(f"Found {len(zip_files)} ZIP files for date: {latest_date}")
                    for zip_file in zip_files:
                        self.log_message(f"  - {os.path.basename(zip_file)}")
                    self.update_status(f"Found {len(zip_files)} backup files")
                else:
                    self.log_message("No ZIP files found in monitoring folder")
                    self.update_status("No backup files found")

            except Exception as e:
                self.update_status("Scan failed")
                messagebox.showerror("Error", f"Scan failed: {str(e)}")
            finally:
                self.progress.stop()

        thread = threading.Thread(target=scan_folder)
        thread.daemon = True
        thread.start()

    def analyze_extract_backups(self):
        def analyze_backups():
            try:
                self.progress.start()
                self.update_status("Analyzing and extracting backups...")

                if not self.monitoring_path.get():
                    messagebox.showwarning("Warning", "Please select a monitoring folder first!")
                    return

                # Get monitoring summary
                summary = self.folder_monitor.get_monitoring_summary()

                self.log_message(f"=== Backup Analysis Report ===")
                self.log_message(f"Monitoring Path: {summary['monitoring_path']}")
                self.log_message(f"Latest Date: {summary['latest_date']}")
                self.log_message(f"Status: {summary['status']}")

                if summary['zip_files']:
                    self.log_message(f"ZIP Files Found: {len(summary['zip_files'])}")
                    for zip_file in summary['zip_files']:
                        self.log_message(f"  - {zip_file}")

                if summary['extracted_data']:
                    self.log_message("Extraction Results:")
                    for zip_name, file_count in summary['extracted_data'].items():
                        self.log_message(f"  - {zip_name}: {file_count} files extracted")

                if summary['bak_files']:
                    self.log_message("BAK Files Found:")
                    for zip_name, bak_count in summary['bak_files'].items():
                        self.log_message(f"  - {zip_name}: {bak_count} .bak files")

                if summary['analysis_results']:
                    self.log_message("Database Analysis:")
                    for zip_name, analysis in summary['analysis_results'].items():
                        self.log_message(f"  {zip_name}:")
                        self.log_message(f"    Status: {analysis['status']}")
                        for table, info in analysis['tables'].items():
                            self.log_message(f"    - {table}: {info}")
                        if analysis['errors']:
                            self.log_message("    Errors:")
                            for error in analysis['errors']:
                                self.log_message(f"      * {error}")

                if summary['errors']:
                    self.log_message("Analysis Errors:")
                    for error in summary['errors']:
                        self.log_message(f"  - {error}")

                self.update_status("Analysis completed")

            except Exception as e:
                self.update_status("Analysis failed")
                messagebox.showerror("Error", f"Analysis failed: {str(e)}")
            finally:
                self.progress.stop()

        thread = threading.Thread(target=analyze_backups)
        thread.daemon = True
        thread.start()

    def send_folder_report(self):
        def send_report():
            try:
                self.progress.start()
                self.update_status("Sending folder monitoring report...")

                if not self.monitoring_path.get():
                    messagebox.showwarning("Warning", "Please select a monitoring folder first!")
                    return

                # Get monitoring summary
                summary = self.folder_monitor.get_monitoring_summary()

                # Create email message
                message = f"""
                <h3>Folder Monitoring Report</h3>
                <table border="1" style="border-collapse: collapse;">
                    <tr>
                        <td><strong>Monitoring Path:</strong></td>
                        <td>{summary['monitoring_path']}</td>
                    </tr>
                    <tr>
                        <td><strong>Latest Date:</strong></td>
                        <td>{summary['latest_date']}</td>
                    </tr>
                    <tr>
                        <td><strong>Status:</strong></td>
                        <td>{summary['status']}</td>
                    </tr>
                    <tr>
                        <td><strong>ZIP Files Found:</strong></td>
                        <td>{len(summary['zip_files'])}</td>
                    </tr>
                </table>

                <h4>ZIP Files:</h4>
                <ul>
                """

                for zip_file in summary['zip_files']:
                    message += f"<li>{zip_file}</li>"

                message += "</ul>"

                if summary['analysis_results']:
                    message += "<h4>Database Analysis:</h4>"
                    for zip_name, analysis in summary['analysis_results'].items():
                        message += f"""
                        <h5>{zip_name}:</h5>
                        <p><strong>Status:</strong> {analysis['status']}</p>
                        <table border="1" style="border-collapse: collapse;">
                        """
                        for table, info in analysis['tables'].items():
                            message += f"""
                            <tr>
                                <td><strong>{table}:</strong></td>
                                <td>{info}</td>
                            </tr>
                            """
                        message += "</table>"

                if summary['errors']:
                    message += """
                    <h4 style="color: red;">Errors Found:</h4>
                    <ul>
                    """
                    for error in summary['errors']:
                        message += f"<li>{error}</li>"
                    message += "</ul>"

                # Send email
                success, email_message = self.notifier.send_notification(
                    subject=f"Folder Monitoring Report - {summary['latest_date']}",
                    message=message
                )

                if success:
                    self.update_status("Folder report sent successfully")
                    messagebox.showinfo("Success", "Folder monitoring report sent successfully!")
                else:
                    self.update_status("Failed to send folder report")
                    messagebox.showerror("Error", f"Failed to send report: {email_message}")

            except Exception as e:
                self.update_status("Failed to send folder report")
                messagebox.showerror("Error", f"Failed to send report: {str(e)}")
            finally:
                self.progress.stop()

        thread = threading.Thread(target=send_report)
        thread.daemon = True
        thread.start()

    # Auto Monitoring Methods
    def toggle_auto_monitoring(self):
        """Toggle auto monitoring checkbox"""
        if self.auto_monitor_var.get():
            self.log_message("Auto monitoring enabled - will check every hour")
        else:
            self.log_message("Auto monitoring disabled")

    def start_auto_monitoring(self):
        """Start auto monitoring background thread"""
        if self.auto_monitoring_active:
            messagebox.showinfo("Info", "Auto monitoring is already running!")
            return

        if not self.monitoring_path.get():
            messagebox.showwarning("Warning", "Please select a monitoring folder first!")
            return

        self.auto_monitoring_active = True
        self.auto_monitor_var.set(True)
        self.log_message("Starting auto monitoring...")

        # Start background thread
        self.auto_monitor_thread = threading.Thread(target=self._auto_monitor_loop, daemon=True)
        self.auto_monitor_thread.start()

        self.update_status("Auto monitoring active")

    def stop_auto_monitoring(self):
        """Stop auto monitoring"""
        self.auto_monitoring_active = False
        self.auto_monitor_var.set(False)
        self.log_message("Auto monitoring stopped")
        self.update_status("Auto monitoring stopped")

    def _auto_monitor_loop(self):
        """Background loop for auto monitoring"""
        import time

        self.log_message("Auto monitoring loop started")
        check_interval = 3600  # 1 hour

        while self.auto_monitoring_active:
            try:
                self.log_message("Running scheduled backup check...")

                # Get monitoring summary
                summary = self.folder_monitor.get_monitoring_summary()

                # Log results
                self.log_message(f"Auto-check completed for {summary['latest_date']}")
                self.log_message(f"Found {len(summary['zip_files'])} ZIP files")

                # Check for issues
                has_issues = (
                    summary['status'] not in ['Success', 'Ready'] or
                    summary['errors'] or
                    any('errors' in result and result['errors']
                        for result in summary['analysis_results'].values())
                )

                if has_issues:
                    self.log_message("Issues found - sending alert email...")
                    # Send alert email
                    self._send_auto_alert(summary)

                # Wait for next check
                for _ in range(check_interval):
                    if not self.auto_monitoring_active:
                        break
                    time.sleep(1)

            except Exception as e:
                self.log_message(f"Auto monitoring error: {str(e)}")

        self.log_message("Auto monitoring loop stopped")

    def _send_auto_alert(self, summary):
        """Send auto monitoring alert email"""
        try:
            message = f"""
            <h3>🚨 Auto Monitoring Alert</h3>
            <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;">
                <h4>Monitoring Summary</h4>
                <table border="1" style="border-collapse: collapse;">
                    <tr>
                        <td><strong>Path:</strong></td>
                        <td>{summary['monitoring_path']}</td>
                    </tr>
                    <tr>
                        <td><strong>Date:</strong></td>
                        <td>{summary['latest_date']}</td>
                    </tr>
                    <tr>
                        <td><strong>Status:</strong></td>
                        <td>{summary['status']}</td>
                    </tr>
                    <tr>
                        <td><strong>ZIP Files:</strong></td>
                        <td>{len(summary['zip_files'])}</td>
                    </tr>
                </table>
            </div>

            <h4>Issues Found:</h4>
            <ul>
            """

            # Add status issues
            if summary['status'] not in ['Success', 'Ready']:
                message += f"<li>Overall status: {summary['status']}</li>"

            # Add errors
            for error in summary['errors']:
                message += f"<li>{error}</li>"

            # Add analysis errors
            for zip_name, analysis in summary['analysis_results'].items():
                if analysis['errors']:
                    message += f"<li>{zip_name}: {', '.join(analysis['errors'])}</li>"

            message += """
            </ul>
            <p><em>This alert was generated automatically by the monitoring system.</em></p>
            """

            success, email_message = self.notifier.send_notification(
                subject=f"🚨 Auto Monitoring Alert - {summary['latest_date']}",
                message=message
            )

            if success:
                self.log_message("Alert email sent successfully")
            else:
                self.log_message(f"Failed to send alert: {email_message}")

        except Exception as e:
            self.log_message(f"Error sending auto alert: {str(e)}")

    def validate_zip_files(self):
        """Validate ZIP files in the monitoring folder"""
        def validate_files():
            try:
                self.progress.start()
                self.update_status("Validating ZIP files...")

                if not self.monitoring_path.get():
                    messagebox.showwarning("Warning", "Please select a monitoring folder first!")
                    return

                # Use ZIP validator
                validation_results = self.zip_validator.validate_folder(self.monitoring_path.get())

                self.log_message("=== ZIP Validation Report ===")
                self.log_message(f"Folder: {self.monitoring_path.get()}")
                self.log_message(f"Total ZIP files found: {validation_results['total_files']}")
                self.log_message(f"Valid ZIP files: {validation_results['valid_files']}")
                self.log_message(f"Invalid ZIP files: {validation_results['invalid_files']}")

                if validation_results['file_results']:
                    self.log_message("\nFile Details:")
                    for file_path, result in validation_results['file_results'].items():
                        filename = os.path.basename(file_path)
                        status = "✅ VALID" if result['is_valid'] else "❌ INVALID"
                        self.log_message(f"  {filename}: {status}")
                        
                        if result['size_mb']:
                            self.log_message(f"    Size: {result['size_mb']:.2f} MB")
                        if result['date_from_filename']:
                            self.log_message(f"    Date from filename: {result['date_from_filename']}")
                        if result['errors']:
                            for error in result['errors']:
                                self.log_message(f"    Error: {error}")

                self.update_status(f"Validation completed - {validation_results['valid_files']}/{validation_results['total_files']} valid")

            except Exception as e:
                self.update_status("Validation failed")
                messagebox.showerror("Error", f"ZIP validation failed: {str(e)}")
            finally:
                self.progress.stop()

        thread = threading.Thread(target=validate_files)
        thread.daemon = True
        thread.start()

    def show_zip_metadata(self):
        """Show ZIP metadata in a simple, step-by-step manner"""
        def show_metadata():
            try:
                self.progress.start()
                self.update_status("Loading ZIP metadata...")

                if not self.monitoring_path.get():
                    messagebox.showwarning("Warning", "Please select a monitoring folder first!")
                    return

                # Import and use the metadata viewer
                from zip_metadata_viewer import ZipMetadataViewer
                viewer = ZipMetadataViewer()

                # Find latest ZIP files
                zip_files = viewer.find_latest_zip_files(self.monitoring_path.get())

                if not zip_files:
                    self.log_message("❌ Tidak ada file ZIP ditemukan di folder tersebut.")
                    self.update_status("No ZIP files found")
                    return

                # Display metadata in log
                self.log_message("=" * 80)
                self.log_message("📋 METADATA FILE ZIP TERBARU")
                self.log_message("=" * 80)

                for i, zip_info in enumerate(zip_files, 1):
                    self.log_message(f"\n{i}. {zip_info['filename']}")
                    self.log_message(f"   📁 Ukuran: {zip_info['size_mb']} MB ({zip_info['size_bytes']:,} bytes)")
                    self.log_message(f"   📅 Dibuat: {zip_info['created_str']}")
                    self.log_message(f"   🔄 Dimodifikasi: {zip_info['modified_str']}")

                    # Get ZIP contents
                    contents = viewer.get_zip_contents_detailed(zip_info['full_path'])
                    if contents['success']:
                        self.log_message(f"   📦 Berisi {contents['total_files']} file")
                        if contents['bak_files']:
                            self.log_message(f"   💾 File database (.bak): {len(contents['bak_files'])}")
                            for bak_file in contents['bak_files']:
                                self.log_message(f"      • {bak_file['filename']} ({bak_file['size_mb']} MB)")
                    else:
                        self.log_message(f"   ❌ Error membaca ZIP: {contents['error']}")

                self.log_message("\n" + "=" * 80)
                self.log_message("💡 Tip: Gunakan tombol 'Check Databases' untuk analisis database lebih detail")
                self.update_status(f"Metadata loaded - {len(zip_files)} ZIP files found")

            except Exception as e:
                self.update_status("Failed to load metadata")
                messagebox.showerror("Error", f"Failed to load ZIP metadata: {str(e)}")
            finally:
                self.progress.stop()

        thread = threading.Thread(target=show_metadata)
        thread.start()

    def check_databases(self):
        """Check databases in ZIP files"""
        def check_db():
            try:
                self.progress.start()
                self.update_status("Checking databases...")

                if not self.monitoring_path.get():
                    messagebox.showwarning("Warning", "Please select a monitoring folder first!")
                    return

                # Use database validator
                db_results = self.database_validator.validate_databases_in_folder(self.monitoring_path.get())

                self.log_message("=== Database Check Report ===")
                self.log_message(f"Folder: {self.monitoring_path.get()}")
                self.log_message(f"ZIP files processed: {len(db_results['zip_results'])}")

                for zip_file, result in db_results['zip_results'].items():
                    filename = os.path.basename(zip_file)
                    self.log_message(f"\n📁 {filename}:")
                    self.log_message(f"  Status: {result['status']}")
                    self.log_message(f"  Database type: {result['database_type']}")
                    
                    if result['analysis']:
                        analysis = result['analysis']
                        if 'record_count' in analysis:
                            self.log_message(f"  Records: {analysis['record_count']}")
                        if 'latest_date' in analysis:
                            self.log_message(f"  Latest date: {analysis['latest_date']}")
                        if 'recent_records' in analysis:
                            self.log_message(f"  Recent records (7 days): {analysis['recent_records']}")
                    
                    if result['errors']:
                        for error in result['errors']:
                            self.log_message(f"  ❌ Error: {error}")

                self.update_status("Database check completed")

            except Exception as e:
                self.update_status("Database check failed")
                messagebox.showerror("Error", f"Database check failed: {str(e)}")
            finally:
                self.progress.stop()

        thread = threading.Thread(target=check_db)
        thread.daemon = True
        thread.start()

    def run_full_monitoring(self):
        """Run comprehensive monitoring with ZIP validation and database checking"""
        def full_monitor():
            try:
                self.progress.start()
                self.update_status("Running full monitoring...")

                if not self.monitoring_path.get():
                    messagebox.showwarning("Warning", "Please select a monitoring folder first!")
                    return

                # Use monitoring controller for comprehensive analysis
                monitoring_results = self.monitoring_controller.monitor_backup_folder(self.monitoring_path.get())

                self.log_message("=== COMPREHENSIVE MONITORING REPORT ===")
                self.log_message(f"Monitoring Path: {monitoring_results['folder_path']}")
                self.log_message(f"Scan Time: {monitoring_results['scan_time']}")
                self.log_message(f"Overall Status: {monitoring_results['overall_status']}")

                # ZIP File Summary
                zip_summary = monitoring_results['zip_validation_summary']
                self.log_message(f"\n📦 ZIP FILES SUMMARY:")
                self.log_message(f"  Total files: {zip_summary['total_files']}")
                self.log_message(f"  Valid files: {zip_summary['valid_files']}")
                self.log_message(f"  Invalid files: {zip_summary['invalid_files']}")

                # Database Summary
                db_summary = monitoring_results['database_summary']
                self.log_message(f"\n🗄️ DATABASE SUMMARY:")
                self.log_message(f"  Plantware databases: {db_summary['plantware_count']}")
                self.log_message(f"  Venus databases: {db_summary['venus_count']}")
                self.log_message(f"  Staging databases: {db_summary['staging_count']}")

                # Date Comparison
                date_comparison = monitoring_results['date_comparison']
                self.log_message(f"\n📅 DATE ANALYSIS:")
                self.log_message(f"  ZIP file dates range: {date_comparison['zip_date_range']}")
                self.log_message(f"  Database dates range: {date_comparison['db_date_range']}")
                self.log_message(f"  Synchronization status: {date_comparison['sync_status']}")

                # Detailed Results
                if monitoring_results['detailed_results']:
                    self.log_message(f"\n📋 DETAILED RESULTS:")
                    for zip_file, details in monitoring_results['detailed_results'].items():
                        filename = os.path.basename(zip_file)
                        self.log_message(f"\n  📁 {filename}:")
                        self.log_message(f"    ZIP Status: {'✅ Valid' if details['zip_valid'] else '❌ Invalid'}")
                        self.log_message(f"    Database Type: {details['database_type']}")
                        
                        if details['database_analysis']:
                            db_analysis = details['database_analysis']
                            self.log_message(f"    Records: {db_analysis.get('record_count', 'N/A')}")
                            self.log_message(f"    Latest Date: {db_analysis.get('latest_date', 'N/A')}")
                            self.log_message(f"    Recent Records: {db_analysis.get('recent_records', 'N/A')}")

                        if details['errors']:
                            for error in details['errors']:
                                self.log_message(f"    ❌ {error}")

                # Recommendations
                if monitoring_results['recommendations']:
                    self.log_message(f"\n💡 RECOMMENDATIONS:")
                    for recommendation in monitoring_results['recommendations']:
                        self.log_message(f"  • {recommendation}")

                self.update_status(f"Full monitoring completed - Status: {monitoring_results['overall_status']}")

            except Exception as e:
                self.update_status("Full monitoring failed")
                messagebox.showerror("Error", f"Full monitoring failed: {str(e)}")
            finally:
                self.progress.stop()

        thread = threading.Thread(target=full_monitor)
        thread.daemon = True
        thread.start()

def main():
    root = tk.Tk()
    app = DatabaseBackupMonitorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()