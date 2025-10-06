#!/usr/bin/env python3
"""
Comprehensive Backup Analyzer
Aplikasi analisis backup database yang komprehensif dengan GUI
"""

import sys
import os
import json
import threading
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# PyQt5 imports
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_zip_analyzer import EnhancedZIPAnalyzer
from enhanced_email_notifier import EnhancedEmailNotifier
from pdf_report_generator import PDFReportGenerator

class WorkerSignals(QObject):
    """Signals for worker threads"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    status = pyqtSignal(str)
    log = pyqtSignal(str)

class AnalysisWorker(QRunnable):
    """Worker thread for comprehensive analysis"""
    def __init__(self, zip_files: List[str], analysis_type: str, window=None):
        super().__init__()
        self.zip_files = zip_files
        self.analysis_type = analysis_type
        self.window = window
        self.signals = WorkerSignals()

    def run(self):
        """Run the analysis task"""
        try:
            if self.analysis_type == "comprehensive":
                result = self._comprehensive_analysis()
            elif self.analysis_type == "zip_only":
                result = self._zip_analysis_only()
            elif self.analysis_type == "auto_extract_analyze":
                result = self._auto_extract_and_analyze()
            else:
                raise ValueError(f"Unknown analysis type: {self.analysis_type}")

            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))

    def _comprehensive_analysis(self):
        """Comprehensive analysis of ZIP files"""
        signals = self.signals
        signals.progress.emit("Memulai analisis komprehensif...")

        zip_analyzer = EnhancedZIPAnalyzer()
        email_notifier = EnhancedEmailNotifier()
        pdf_generator = PDFReportGenerator()

        results = []
        total_files = len(self.zip_files)

        for i, zip_file in enumerate(self.zip_files):
            try:
                signals.progress.emit(f"Analisis file {i+1}/{total_files}: {os.path.basename(zip_file)}")
                signals.log.emit(f"🔍 Menganalisis: {os.path.basename(zip_file)}")

                # Analyze ZIP file
                zip_analysis = zip_analyzer.analyze_zip_comprehensive(zip_file)
                zip_analysis['file_path'] = zip_file
                results.append(zip_analysis)

                signals.log.emit(f"✅ Selesai: {os.path.basename(zip_file)}")

            except Exception as e:
                signals.log.emit(f"❌ Error: {os.path.basename(zip_file)} - {str(e)}")
                results.append({
                    'file_path': zip_file,
                    'error': str(e),
                    'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

        # Generate summary report
        signals.progress.emit("Membuat ringkasan laporan...")
        summary_report = self._generate_summary_report(results)

        # Generate PDF report
        signals.progress.emit("Membuat PDF report...")
        pdf_path = None
        try:
            pdf_path = pdf_generator.generate_comprehensive_pdf_report(results)
            if pdf_path:
                signals.log.emit(f"📄 PDF report dibuat: {os.path.basename(pdf_path)}")
        except Exception as e:
            signals.log.emit(f"❌ Gagal membuat PDF: {str(e)}")

        # Send email report
        signals.progress.emit("Mengirim email laporan...")
        try:
            email_success, email_msg = email_notifier.send_auto_analysis_report(results, pdf_path)
            if email_success:
                signals.log.emit(f"📧 Email laporan berhasil dikirim")
            else:
                signals.log.emit(f"❌ Gagal kirim email: {email_msg}")
        except Exception as e:
            signals.log.emit(f"❌ Error kirim email: {str(e)}")

        return {
            'type': 'comprehensive',
            'analysis_results': results,
            'summary': summary_report,
            'pdf_path': pdf_path,
            'total_files': total_files,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def _zip_analysis_only(self):
        """ZIP file analysis only"""
        signals = self.signals
        signals.progress.emit("Analisis ZIP file metadata...")

        zip_analyzer = EnhancedZIPAnalyzer()
        results = []

        for i, zip_file in enumerate(self.zip_files):
            try:
                signals.progress.emit(f"Analisis ZIP {i+1}/{len(self.zip_files)}")
                signals.log.emit(f"📦 Analisis ZIP: {os.path.basename(zip_file)}")

                # Analyze ZIP metadata
                zip_info = zip_analyzer.analyze_zip_comprehensive(zip_file)
                results.append(zip_info)

                # Show ZIP summary
                summary = zip_analyzer.generate_zip_summary_report(zip_info)
                self._display_zip_summary(summary, signals)

            except Exception as e:
                signals.log.emit(f"❌ Error analisis ZIP: {str(e)}")

        return {
            'type': 'zip_only',
            'analysis_results': results,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def _auto_extract_and_analyze(self):
        """Auto extract and analyze BAK files"""
        signals = self.signals
        signals.progress.emit("Ekstrak dan analisis BAK files...")

        zip_analyzer = EnhancedZIPAnalyzer()
        email_notifier = EnhancedEmailNotifier()
        results = []

        for zip_file in self.zip_files:
            try:
                signals.progress.emit(f"Proses: {os.path.basename(zip_file)}")
                signals.log.emit(f"🔄 Ekstrak & Analisis: {os.path.basename(zip_file)}")

                # Comprehensive analysis includes BAK analysis
                analysis = zip_analyzer.analyze_zip_comprehensive(zip_file)
                results.append(analysis)

                # Show detailed BAK information
                self._display_bak_analysis_details(analysis, signals)

            except Exception as e:
                signals.log.emit(f"❌ Error: {str(e)}")

        # Send detailed report for BackupStaging and BackupVenuz
        signals.progress.emit("Mengirim laporan detail...")
        try:
            filtered_results = self._filter_target_databases(results)
            if filtered_results:
                email_success, email_msg = email_notifier.send_auto_analysis_report(filtered_results)
                if email_success:
                    signals.log.emit(f"📧 Laporan detail database berhasil dikirim")
                else:
                    signals.log.emit(f"❌ Gagal kirim laporan: {email_msg}")
        except Exception as e:
            signals.log.emit(f"❌ Error kirim laporan: {str(e)}")

        return {
            'type': 'auto_extract_analyze',
            'analysis_results': results,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def _display_zip_summary(self, summary: Dict[str, Any], signals):
        """Display ZIP summary in log"""
        signals.log.emit("=" * 60)
        signals.log.emit("📊 ZIP FILE SUMMARY")
        signals.log.emit("=" * 60)
        signals.log.emit(f"Filename: {summary.get('filename', 'Unknown')}")
        signals.log.emit(f"Size: {summary.get('file_size_mb', 0):.2f} MB")
        signals.log.emit(f"Backup Date: {summary.get('backup_date', 'Unknown')}")
        signals.log.emit(f"ZIP Status: {summary.get('zip_status', 'Unknown')}")
        signals.log.emit(f"Can Be Extracted: {'Yes' if summary.get('can_be_extracted') else 'No'}")
        signals.log.emit(f"BAK Files: {summary.get('bak_files_count', 0)}")
        signals.log.emit(f"Databases: {', '.join(summary.get('databases_found', []))}")
        signals.log.emit("=" * 60)

    def _display_bak_analysis_details(self, analysis: Dict[str, Any], signals):
        """Display detailed BAK analysis dengan format yang lebih baik"""
        bak_analysis = analysis.get('bak_analysis', {})
        bak_files = bak_analysis.get('bak_analyses', [])

        if not bak_files:
            return

        # Import EnhancedBAKAnalyzer untuk formatting
        from enhanced_bak_analyzer import EnhancedBAKAnalyzer
        bak_analyzer = EnhancedBAKAnalyzer()

        # Format output yang lebih user-friendly
        formatted_output = bak_analyzer.format_analysis_output(bak_files)
        signals.log.emit(formatted_output)

    def _filter_target_databases(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter results for BackupStaging and BackupVenuz"""
        filtered = []
        target_databases = ['BackupStaging', 'BackupVenuz', 'staging', 'venus']

        for result in results:
            zip_info = result.get('zip_info', {})
            db_type = zip_info.get('database_type_from_filename', '')

            if any(target.lower() in db_type.lower() for target in target_databases):
                filtered.append(result)

        return filtered

    def _generate_summary_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary report"""
        total_files = len(results)
        successful_analyses = len([r for r in results if r.get('analysis_status', '').lower() != 'failed'])
        total_size_mb = sum(r.get('zip_info', {}).get('file_size_mb', 0) for r in results)

        valid_zips = 0
        corrupted_files = 0
        total_bak_files = 0
        valid_bak_files = 0

        for result in results:
            validation = result.get('validation', {})
            if validation.get('is_valid_zip'):
                valid_zips += 1
            if validation.get('corruption_detected'):
                corrupted_files += 1

            bak_analysis = result.get('bak_analysis', {})
            total_bak_files += bak_analysis.get('total_bak_files', 0)
            valid_bak_files += bak_analysis.get('summary', {}).get('valid_bak_files', 0)

        return {
            'total_files': total_files,
            'successful_analyses': successful_analyses,
            'failed_analyses': total_files - successful_analyses,
            'total_size_mb': total_size_mb,
            'valid_zip_files': valid_zips,
            'corrupted_files': corrupted_files,
            'total_bak_files': total_bak_files,
            'valid_bak_files': valid_bak_files,
            'databases_found': list(set(
                db for result in results
                for db in result.get('bak_analysis', {}).get('summary', {}).get('databases_found', [])
            ))
        }

class ComprehensiveBackupAnalyzerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Comprehensive Backup Database Analyzer")
        self.setGeometry(100, 100, 1200, 800)
        self.thread_pool = QThreadPool()
        self.current_analysis = None

        self.init_ui()

    def init_ui(self):
        """Initialize user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Header
        header_label = QLabel("📊 Comprehensive Backup Database Analyzer")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(header_label)

        # Control Panel
        control_group = QGroupBox("Analysis Controls")
        control_layout = QHBoxLayout()

        self.browse_btn = QPushButton("📁 Browse Backup Folder")
        self.browse_btn.clicked.connect(self.browse_folder)
        control_layout.addWidget(self.browse_btn)

        self.folder_path = QLineEdit()
        self.folder_path.setPlaceholderText("Select backup folder containing ZIP files...")
        control_layout.addWidget(self.folder_path)

        self.refresh_btn = QPushButton("🔄 Refresh Files")
        self.refresh_btn.clicked.connect(self.refresh_files)
        control_layout.addWidget(self.refresh_btn)

        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        # File List
        file_group = QGroupBox("ZIP Files Found")
        file_layout = QVBoxLayout()

        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QAbstractItemView.MultiSelection)
        file_layout.addWidget(self.file_list)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Analysis Buttons
        button_group = QGroupBox("Analysis Options")
        button_layout = QGridLayout()

        self.zip_meta_btn = QPushButton("1️⃣ ZIP Metadata Analysis")
        self.zip_meta_btn.clicked.connect(lambda: self.run_analysis("zip_only"))
        button_layout.addWidget(self.zip_meta_btn, 0, 0)

        self.comprehensive_btn = QPushButton("2️⃣ Comprehensive Analysis")
        self.comprehensive_btn.clicked.connect(lambda: self.run_analysis("comprehensive"))
        button_layout.addWidget(self.comprehensive_btn, 0, 1)

        self.auto_extract_btn = QPushButton("3️⃣ Auto Extract & Analyze")
        self.auto_extract_btn.clicked.connect(lambda: self.run_analysis("auto_extract_analyze"))
        button_layout.addWidget(self.auto_extract_btn, 1, 0)

        self.send_report_btn = QPushButton("📧 Send Email Report")
        self.send_report_btn.clicked.connect(self.send_email_report)
        button_layout.addWidget(self.send_report_btn, 1, 1)

        button_group.setLayout(button_layout)
        layout.addWidget(button_group)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Tab Widget for Analysis Results
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Log Tab
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)

        log_group = QGroupBox("Analysis Log")
        log_inner_layout = QVBoxLayout()

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        log_inner_layout.addWidget(self.log_display)

        log_group.setLayout(log_inner_layout)
        log_layout.addWidget(log_group)

        self.tab_widget.addTab(log_widget, "📋 Analysis Log")

        # BAK Analysis Tab
        bak_widget = QWidget()
        bak_layout = QVBoxLayout(bak_widget)

        bak_group = QGroupBox("BAK Analysis Summary")
        bak_inner_layout = QVBoxLayout()

        # Create BAK Summary Table
        self.bak_table = QTableWidget()
        self.bak_table.setColumnCount(8)
        self.bak_table.setHorizontalHeaderLabels([
            "File Name", "Database", "Backup Date", "Size (MB)",
            "Health Status", "Tables", "Records", "Can Restore"
        ])
        self.bak_table.setSortingEnabled(True)
        self.bak_table.horizontalHeader().setStretchLastSection(True)

        # Make table read-only
        self.bak_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Set column widths
        self.bak_table.setColumnWidth(0, 200)  # File Name
        self.bak_table.setColumnWidth(1, 150)  # Database
        self.bak_table.setColumnWidth(2, 150)  # Backup Date
        self.bak_table.setColumnWidth(3, 100)  # Size
        self.bak_table.setColumnWidth(4, 120)  # Health Status
        self.bak_table.setColumnWidth(5, 80)   # Tables
        self.bak_table.setColumnWidth(6, 100)  # Records
        self.bak_table.setColumnWidth(7, 100)  # Can Restore

        bak_inner_layout.addWidget(self.bak_table)
        bak_group.setLayout(bak_inner_layout)
        bak_layout.addWidget(bak_group)

        # BAK Health Summary
        health_group = QGroupBox("BAK Health Summary")
        health_layout = QHBoxLayout()

        self.health_labels = {}
        health_info = [
            ("total_files", "Total Files", "📊"),
            ("healthy_files", "Healthy", "✅"),
            ("warning_files", "Warnings", "⚠️"),
            ("corrupted_files", "Corrupted", "❌"),
            ("total_size", "Total Size", "📏"),
            ("overall_status", "Overall Status", "🏥")
        ]

        for key, label, emoji in health_info:
            frame = QFrame()
            frame.setFrameStyle(QFrame.Box)
            frame_layout = QVBoxLayout(frame)

            title_label = QLabel(f"{emoji} {label}")
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet("font-weight: bold;")

            value_label = QLabel("-")
            value_label.setAlignment(Qt.AlignCenter)
            value_label.setStyleSheet("font-size: 14px;")

            frame_layout.addWidget(title_label)
            frame_layout.addWidget(value_label)

            health_layout.addWidget(frame)
            self.health_labels[key] = value_label

        health_group.setLayout(health_layout)
        bak_layout.addWidget(health_group)

        self.tab_widget.addTab(bak_widget, "💾 BAK Analysis")

        # Status Bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        # Set default backup folder
        default_folder = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup"
        if os.path.exists(default_folder):
            self.folder_path.setText(default_folder)
            self.refresh_files()

    def browse_folder(self):
        """Browse for backup folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Backup Folder")
        if folder:
            self.folder_path.setText(folder)
            self.refresh_files()

    def refresh_files(self):
        """Refresh ZIP files list"""
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

        self.log(f"Found {len(zip_files)} ZIP files in {folder}")
        self.status_bar.showMessage(f"Found {len(zip_files)} ZIP files")

    def run_analysis(self, analysis_type: str):
        """Run analysis on selected files"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select ZIP files to analyze.")
            return

        folder = self.folder_path.text()
        zip_files = [os.path.join(folder, item.text()) for item in selected_items]

        # Clear log and show progress
        self.log_display.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress

        # Create and run worker
        worker = AnalysisWorker(zip_files, analysis_type, self)
        worker.signals.progress.connect(self.update_progress)
        worker.signals.log.connect(self.log)
        worker.signals.finished.connect(self.analysis_finished)
        worker.signals.error.connect(self.analysis_error)

        self.thread_pool.start(worker)
        self.current_analysis = worker
        self.log(f"🚀 Starting {analysis_type} analysis...")

    def update_progress(self, message: str):
        """Update progress bar and status"""
        self.status_bar.showMessage(message)

    def log(self, message: str):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_display.append(f"[{timestamp}] {message}")

    def analysis_finished(self, result: Dict[str, Any]):
        """Handle analysis completion"""
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Analysis completed")

        analysis_type = result.get('type', 'unknown')
        if analysis_type == 'comprehensive':
            summary = result.get('summary', {})
            self.log(f"✅ Comprehensive analysis completed!")
            self.log(f"📊 Summary: {summary['successful_analyses']}/{summary['total_files']} successful")
            if result.get('pdf_path'):
                self.log(f"📄 PDF report saved: {result['pdf_path']}")

            # Update BAK analysis tab
            self.update_bak_analysis_table(result.get('analysis_results', []))

        elif analysis_type == 'auto_extract_analyze':
            self.log(f"✅ Auto extract & analyze completed!")
            # Update BAK analysis tab
            self.update_bak_analysis_table(result.get('analysis_results', []))

        elif analysis_type == 'zip_only':
            self.log(f"✅ ZIP metadata analysis completed!")

        QMessageBox.information(self, "Analysis Complete",
                              f"{analysis_type.title()} analysis completed successfully!")

        # Switch to BAK Analysis tab if we have BAK results
        if analysis_type in ['comprehensive', 'auto_extract_analyze']:
            self.tab_widget.setCurrentIndex(1)  # Switch to BAK Analysis tab

    def analysis_error(self, error_message: str):
        """Handle analysis error"""
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Analysis failed")
        self.log(f"❌ Analysis error: {error_message}")
        QMessageBox.critical(self, "Analysis Error", f"Analysis failed: {error_message}")

    def update_bak_analysis_table(self, analysis_results: List[Dict[str, Any]]):
        """Update BAK analysis table dengan hasil analisis"""
        # Import EnhancedBAKAnalyzer for health summary
        from enhanced_bak_analyzer import EnhancedBAKAnalyzer
        bak_analyzer = EnhancedBAKAnalyzer()

        # Clear existing table data
        self.bak_table.setRowCount(0)

        # Collect all BAK analyses
        all_bak_analyses = []
        for result in analysis_results:
            bak_analysis = result.get('bak_analysis', {})
            bak_analyses = bak_analysis.get('bak_analyses', [])
            all_bak_analyses.extend(bak_analyses)

        # Populate table
        for i, bak_result in enumerate(all_bak_analyses):
            if bak_result.get('analysis_status') != 'success':
                continue

            self.bak_table.insertRow(i)

            # Extract information
            filename = bak_result.get('original_filename', bak_result.get('filename', 'Unknown'))
            metadata = bak_result.get('backup_metadata', {})
            db_info = bak_result.get('database_info', {})
            validation = bak_result.get('validation', {})
            table_info = bak_result.get('table_info', {})

            # File Name
            self.bak_table.setItem(i, 0, QTableWidgetItem(filename))

            # Database
            db_name = metadata.get('database_name', db_info.get('database_name', 'Unknown'))
            self.bak_table.setItem(i, 1, QTableWidgetItem(db_name))

            # Backup Date
            backup_date = metadata.get('backup_date', 'Unknown')
            self.bak_table.setItem(i, 2, QTableWidgetItem(backup_date))

            # Size (MB)
            size_mb = bak_result.get('file_size_mb', 0)
            self.bak_table.setItem(i, 3, QTableWidgetItem(f"{size_mb:.1f}"))

            # Health Status
            health_status = validation.get('file_integrity', 'Unknown')
            status_item = QTableWidgetItem(health_status)

            # Color coding for health status
            if health_status == 'Good':
                status_item.setBackground(QColor(144, 238, 144))  # Light green
            elif health_status == 'Warnings':
                status_item.setBackground(QColor(255, 255, 224))  # Light yellow
            elif health_status in ['Corrupted', 'Error']:
                status_item.setBackground(QColor(255, 182, 193))  # Light red

            self.bak_table.setItem(i, 4, status_item)

            # Tables
            tables_count = table_info.get('total_tables', db_info.get('estimated_tables', 0))
            self.bak_table.setItem(i, 5, QTableWidgetItem(str(tables_count)))

            # Records
            records_count = table_info.get('total_records', db_info.get('estimated_records', 0))
            self.bak_table.setItem(i, 6, QTableWidgetItem(f"{records_count:,}" if records_count > 0 else "N/A"))

            # Can Restore
            can_restore = validation.get('can_be_restored', False)
            restore_item = QTableWidgetItem("Yes" if can_restore else "No")
            if can_restore:
                restore_item.setBackground(QColor(144, 238, 144))  # Light green
            else:
                restore_item.setBackground(QColor(255, 182, 193))  # Light red

            self.bak_table.setItem(i, 7, restore_item)

        # Update health summary
        self.update_health_summary(all_bak_analyses)

    def update_health_summary(self, bak_analyses: List[Dict[str, Any]]):
        """Update health summary labels"""
        # Import EnhancedBAKAnalyzer for health summary
        from enhanced_bak_analyzer import EnhancedBAKAnalyzer
        bak_analyzer = EnhancedBAKAnalyzer()

        # Generate health summary
        health_summary = bak_analyzer.generate_health_summary(bak_analyses)

        # Update labels
        self.health_labels['total_files'].setText(str(health_summary['total_files']))
        self.health_labels['healthy_files'].setText(str(health_summary['healthy_files']))
        self.health_labels['warning_files'].setText(str(health_summary['warning_files']))
        self.health_labels['corrupted_files'].setText(str(health_summary['corrupted_files']))
        self.health_labels['total_size'].setText(f"{health_summary['total_size_mb']:.1f} MB")
        self.health_labels['overall_status'].setText(health_summary['health_status'])

        # Color coding for overall status
        status_color = {
            'Healthy': QColor(144, 238, 144),    # Light green
            'Warning': QColor(255, 255, 224),    # Light yellow
            'Critical': QColor(255, 182, 193)    # Light red
        }

        if health_summary['health_status'] in status_color:
            self.health_labels['overall_status'].setBackground(status_color[health_summary['health_status']])

    def send_email_report(self):
        """Send email report of last analysis"""
        if not self.current_analysis:
            QMessageBox.warning(self, "No Analysis", "Please run analysis first.")
            return

        self.log("📧 Sending email report...")
        # Email sending is handled within the analysis worker
        self.log("✅ Email report functionality included in analysis types")

def main():
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Create and show main window
    window = ComprehensiveBackupAnalyzerGUI()
    window.show()

    # Run application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()