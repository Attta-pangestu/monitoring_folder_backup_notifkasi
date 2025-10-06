#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Backup Monitor - Entry Point Application
Versi sederhana dengan satu tombol utama untuk extract dan analisis semua BAK files
"""

import sys
import os
import json
import tempfile
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_backup_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# PyQt5 imports
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_zip_analyzer import EnhancedZIPAnalyzer
from enhanced_bak_analyzer import EnhancedBAKAnalyzer
from enhanced_email_notifier import EnhancedEmailNotifier

class WorkerSignals(QObject):
    """Signals untuk worker threads"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    status = pyqtSignal(str)
    log = pyqtSignal(str)

class SimpleAnalysisWorker(QRunnable):
    """Worker thread untuk analisis sederhana"""
    def __init__(self, zip_files: List[str]):
        super().__init__()
        self.zip_files = zip_files
        self.signals = WorkerSignals()

    def run(self):
        """Run analisis utama"""
        try:
            self.signals.progress.emit("Memulai analisis backup...")
            self.signals.log.emit("🚀 Memulai analisis backup database...")

            # Initialize analyzers
            zip_analyzer = EnhancedZIPAnalyzer()
            bak_analyzer = EnhancedBAKAnalyzer()
            email_notifier = EnhancedEmailNotifier()

            results = []
            all_bak_analyses = []

            # Process each ZIP file
            for i, zip_file in enumerate(self.zip_files):
                try:
                    self.signals.progress.emit(f"Analisis file {i+1}/{len(self.zip_files)}: {os.path.basename(zip_file)}")
                    self.signals.log.emit(f"📦 Menganalisis: {os.path.basename(zip_file)}")

                    # Analyze ZIP file
                    zip_analysis = zip_analyzer.analyze_zip_comprehensive(zip_file)
                    zip_analysis['file_path'] = zip_file
                    results.append(zip_analysis)

                    # Collect BAK analyses
                    bak_analysis = zip_analysis.get('bak_analysis', {})
                    bak_analyses = bak_analysis.get('bak_analyses', [])
                    all_bak_analyses.extend(bak_analyses)

                    self.signals.log.emit(f"✅ Selesai: {os.path.basename(zip_file)}")

                except Exception as e:
                    self.signals.log.emit(f"❌ Error: {os.path.basename(zip_file)} - {str(e)}")
                    results.append({
                        'file_path': zip_file,
                        'error': str(e),
                        'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })

            # Generate health summary
            self.signals.progress.emit("Membuat health summary...")
            health_summary = bak_analyzer.generate_health_summary(all_bak_analyses)

            # Generate formatted output
            formatted_output = bak_analyzer.format_analysis_output(all_bak_analyses)
            self.signals.log.emit(formatted_output)

            # Send email report
            self.signals.progress.emit("Mengirim email report...")
            try:
                # Filter untuk BackupStaging dan BackupVenuz
                filtered_results = self._filter_target_databases(results)

                if filtered_results:
                    email_success, email_msg = email_notifier.send_auto_analysis_report(filtered_results)
                    if email_success:
                        self.signals.log.emit(f"📧 Email report berhasil dikirim")
                    else:
                        self.signals.log.emit(f"❌ Gagal kirim email: {email_msg}")
                else:
                    self.signals.log.emit("ℹ️ Tidak ada BackupStaging/BackupVenuz ditemukan untuk email")
            except Exception as e:
                self.signals.log.emit(f"❌ Error kirim email: {str(e)}")

            result = {
                'type': 'simple_analysis',
                'analysis_results': results,
                'health_summary': health_summary,
                'total_files': len(self.zip_files),
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'bak_analyses_count': len(all_bak_analyses)
            }

            self.signals.finished.emit(result)

        except Exception as e:
            self.signals.error.emit(str(e))

    def _filter_target_databases(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter hasil untuk BackupStaging dan BackupVenuz"""
        filtered = []
        for result in results:
            bak_analysis = result.get('bak_analysis', {})
            bak_analyses = bak_analysis.get('bak_analyses', [])

            for bak in bak_analyses:
                if bak.get('analysis_status') == 'success':
                    metadata = bak.get('backup_metadata', {})
                    db_name = metadata.get('database_name', '').lower()

                    if 'backupstaging' in db_name or 'backupvenus' in db_name or 'venus' in db_name or 'staging' in db_name:
                        filtered.append(result)
                        break

        return filtered

class SimpleBackupMonitorGUI(QMainWindow):
    """GUI sederhana untuk backup monitoring"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📊 Simple Backup Monitor")
        self.setGeometry(100, 100, 1000, 700)
        self.thread_pool = QThreadPool()
        self.current_analysis = None

        self.init_ui()

    def init_ui(self):
        """Initialize user interface - SANGAT SEDERHANA"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Header
        header_label = QLabel("🗄️ Simple Backup Database Monitor")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 15px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(header_label)

        # Instructions
        instructions = QLabel(
            "Aplikasi ini akan mengekstrak semua file ZIP dan menganalisis file BAK secara otomatis.\n"
            "Setelah analisis selesai, laporan akan dikirim ke email secara otomatis."
        )
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setStyleSheet("font-size: 12px; color: #666; padding: 10px;")
        layout.addWidget(instructions)

        # Folder Selection
        folder_group = QGroupBox("📁 Folder Backup")
        folder_layout = QHBoxLayout()

        self.folder_path = QLineEdit()
        self.folder_path.setPlaceholderText("Pilih folder yang berisi file ZIP backup...")
        self.folder_path.setText(r"D:\Gawean Rebinmas\App_Auto_Backup\Backup")
        folder_layout.addWidget(self.folder_path)

        browse_btn = QPushButton("📂 Browse")
        browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(browse_btn)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_files)
        folder_layout.addWidget(refresh_btn)

        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)

        # File List
        file_group = QGroupBox("📦 File ZIP Ditemukan")
        file_layout = QVBoxLayout()

        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QAbstractItemView.MultiSelection)
        file_layout.addWidget(self.file_list)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # MAIN ACTION BUTTON - TOMBOL BESAR HIJAU
        button_group = QGroupBox("🚀 Analisis Backup")
        button_layout = QVBoxLayout()

        # Tombol utama - besar dan hijau
        self.main_action_btn = QPushButton("📊 EXTRACT SEMUA ZIP & ANALISIS BAK FILES")
        self.main_action_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.main_action_btn.clicked.connect(self.run_main_analysis)
        self.main_action_btn.setMinimumHeight(60)
        button_layout.addWidget(self.main_action_btn)

        # Tombol test email
        self.test_email_btn = QPushButton("📧 Test Email Configuration")
        self.test_email_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 8px; }")
        self.test_email_btn.clicked.connect(self.test_email)
        button_layout.addWidget(self.test_email_btn)

        button_group.setLayout(button_layout)
        layout.addWidget(button_group)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Log Display
        log_group = QGroupBox("📋 Log Analisis")
        log_layout = QVBoxLayout()

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(250)
        self.log_display.setStyleSheet("font-family: monospace; font-size: 10px;")
        log_layout.addWidget(self.log_display)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # Status Bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        # Load initial files
        self.refresh_files()

    def browse_folder(self):
        """Browse untuk folder backup"""
        folder = QFileDialog.getExistingDirectory(self, "Pilih Folder Backup")
        if folder:
            self.folder_path.setText(folder)
            self.refresh_files()

    def refresh_files(self):
        """Refresh daftar file ZIP"""
        folder = self.folder_path.text()
        if not folder or not os.path.exists(folder):
            return

        self.file_list.clear()
        zip_files = []

        for file in os.listdir(folder):
            if file.lower().endswith('.zip'):
                zip_files.append(file)

        zip_files.sort()
        self.file_list.addItems(zip_files)

        self.log(f"📁 Ditemukan {len(zip_files)} file ZIP di {folder}")
        self.status_bar.showMessage(f"Ditemukan {len(zip_files)} file ZIP")

    def run_main_analysis(self):
        """Jalankan analisis utama - SATU-SATUNYA AKSI"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            # Jika tidak ada yang dipilih, gunakan semua file
            items = self.file_list.findItems("", Qt.MatchContains)
        else:
            items = selected_items

        if not items:
            QMessageBox.warning(self, "Tidak Ada File", "Tidak ada file ZIP yang ditemukan.")
            return

        folder = self.folder_path.text()
        zip_files = [os.path.join(folder, item.text()) for item in items]

        # Clear log dan show progress
        self.log_display.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress

        # Disable tombol selama analisis
        self.main_action_btn.setEnabled(False)
        self.test_email_btn.setEnabled(False)

        # Create dan run worker
        worker = SimpleAnalysisWorker(zip_files)
        worker.signals.progress.connect(self.update_progress)
        worker.signals.log.connect(self.log)
        worker.signals.finished.connect(self.analysis_finished)
        worker.signals.error.connect(self.analysis_error)

        self.thread_pool.start(worker)
        self.current_analysis = worker
        self.log(f"🚀 Memulai analisis {len(zip_files)} file ZIP...")

    def test_email(self):
        """Test email configuration"""
        try:
            self.log("📧 Menguji konfigurasi email...")
            email_notifier = EnhancedEmailNotifier()

            # Create test report
            test_report = {
                'test': True,
                'message': 'Ini adalah email test dari Simple Backup Monitor',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            success, message = email_notifier.send_test_email(test_report)

            if success:
                self.log("✅ Email test berhasil dikirim!")
                QMessageBox.information(self, "Email Test", "Email test berhasil dikirim!")
            else:
                self.log(f"❌ Email test gagal: {message}")
                QMessageBox.warning(self, "Email Test", f"Gagal kirim email: {message}")

        except Exception as e:
            error_msg = str(e)
            self.log(f"❌ Error test email: {error_msg}")
            QMessageBox.critical(self, "Email Test Error", f"Error: {error_msg}")

    def update_progress(self, message: str):
        """Update progress bar dan status"""
        self.status_bar.showMessage(message)

    def log(self, message: str):
        """Add message ke log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_display.append(f"[{timestamp}] {message}")

    def analysis_finished(self, result: Dict[str, Any]):
        """Handle analisis selesai"""
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Analisis selesai")

        # Enable tombol kembali
        self.main_action_btn.setEnabled(True)
        self.test_email_btn.setEnabled(True)

        # Show summary
        total_files = result.get('total_files', 0)
        bak_count = result.get('bak_analyses_count', 0)
        health_summary = result.get('health_summary', {})

        self.log(f"✅ Analisis selesai!")
        self.log(f"📊 Total file ZIP: {total_files}")
        self.log(f"💾 Total file BAK: {bak_count}")

        if health_summary:
            self.log(f"🏥 Overall Health: {health_summary.get('health_status', 'Unknown')}")
            self.log(f"✅ Healthy: {health_summary.get('healthy_files', 0)}")
            self.log(f"⚠️  Warnings: {health_summary.get('warning_files', 0)}")
            self.log(f"❌ Corrupted: {health_summary.get('corrupted_files', 0)}")

        # PDF report removed for simplicity

        # Show completion message
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("Analisis Selesai")
        msg_box.setText(f"Analisis backup selesai!\n\n"
                       f"Total file: {total_files}\n"
                       f"BAK files: {bak_count}\n"
                       f"Health Status: {health_summary.get('health_status', 'Unknown')}\n"
                       f"Email report telah dikirim otomatis.")
        msg_box.exec_()

    def analysis_error(self, error_message: str):
        """Handle analisis error"""
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Analisis gagal")

        # Enable tombol kembali
        self.main_action_btn.setEnabled(True)
        self.test_email_btn.setEnabled(True)

        self.log(f"❌ Analisis error: {error_message}")
        QMessageBox.critical(self, "Analisis Error", f"Analisis gagal: {error_message}")

def main():
    """Main function"""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Set application info
    app.setApplicationName("Simple Backup Monitor")
    app.setApplicationVersion("1.0")

    # Create and show main window
    window = SimpleBackupMonitorGUI()
    window.show()

    # Run application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()