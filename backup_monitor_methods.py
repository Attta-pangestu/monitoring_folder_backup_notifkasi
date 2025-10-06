"""
Additional methods for BackupMonitorWindow class
These methods handle the new extract all and analyze BAK functionality
"""

import os
import zipfile
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import QTimer, QThreadPool

def extract_all_and_analyze_bak(self):
    """Extract all ZIP files and analyze BAK files with user confirmation"""
    if not hasattr(self, 'current_zip_files') or len(self.current_zip_files) == 0:
        self.append_terminal_output("❌ ERROR: Tidak ada file ZIP yang ditemukan!")
        QMessageBox.warning(self, "Warning", "Tidak ada file ZIP yang ditemukan. Silakan refresh files terlebih dahulu.")
        return

    # Confirm extraction
    reply = QMessageBox.question(
        self, 
        "Konfirmasi Ekstraksi Massal",
        f"Akan mengekstrak {len(self.current_zip_files)} file ZIP ke:\n"
        f"D:\\Gawean Rebinmas\\App_Auto_Backup\\Backup\n\n"
        f"⚠️ PERINGATAN: Ekstraksi akan menimpa file yang sudah ada!\n"
        f"Semua file akan di-extract langsung ke folder backup tanpa subfolder.\n\n"
        f"Lanjutkan?",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )
    
    if reply != QMessageBox.Yes:
        self.append_terminal_output("❌ Ekstraksi dibatalkan oleh user.")
        return

    self.append_terminal_output("🚀 Memulai ekstraksi massal...")
    self.append_terminal_output(f"📁 Target direktori: D:\\Gawean Rebinmas\\App_Auto_Backup\\Backup")
    self.append_terminal_output(f"📦 Total file ZIP: {len(self.current_zip_files)}")
    self.append_terminal_output("=" * 60)

    # Start extraction process
    self.show_progress("Mengekstrak file ZIP...")
    self.extraction_results = []
    self.current_extraction_index = 0
    self.extract_next_zip()

def extract_next_zip(self):
    """Extract next ZIP file in sequence"""
    if self.current_extraction_index >= len(self.current_zip_files):
        # All files extracted, now ask for BAK analysis
        self.hide_progress()
        self.ask_for_bak_analysis()
        return

    zip_path = self.current_zip_files[self.current_extraction_index]
    zip_name = os.path.basename(zip_path)
    
    self.append_terminal_output(f"📦 Mengekstrak: {zip_name}")
    
    # Extract to backup directory
    extraction_dir = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup"
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extract all files directly to backup directory (overwrite mode)
            zip_ref.extractall(extraction_dir)
            
        self.append_terminal_output(f"✅ Berhasil: {zip_name}")
        self.extraction_results.append({'zip_path': zip_path, 'status': 'success'})
        
    except Exception as e:
        self.append_terminal_output(f"❌ Gagal: {zip_name} - {str(e)}")
        self.extraction_results.append({'zip_path': zip_path, 'status': 'error', 'error': str(e)})

    # Move to next file
    self.current_extraction_index += 1
    
    # Use QTimer to prevent UI freezing
    QTimer.singleShot(100, self.extract_next_zip)

def ask_for_bak_analysis(self):
    """Ask user confirmation for BAK file analysis"""
    successful_extractions = [r for r in self.extraction_results if r['status'] == 'success']
    failed_extractions = [r for r in self.extraction_results if r['status'] == 'error']
    
    self.append_terminal_output("=" * 60)
    self.append_terminal_output(f"📊 RINGKASAN EKSTRAKSI:")
    self.append_terminal_output(f"✅ Berhasil: {len(successful_extractions)} file")
    self.append_terminal_output(f"❌ Gagal: {len(failed_extractions)} file")
    self.append_terminal_output("=" * 60)

    if len(successful_extractions) == 0:
        self.append_terminal_output("❌ Tidak ada file yang berhasil diekstrak. Analisis BAK dibatalkan.")
        return

    # Ask for BAK analysis
    reply = QMessageBox.question(
        self, 
        "Konfirmasi Analisis BAK",
        f"Ekstraksi selesai!\n\n"
        f"✅ {len(successful_extractions)} file berhasil diekstrak\n"
        f"❌ {len(failed_extractions)} file gagal\n\n"
        f"Lanjutkan dengan analisis file BAK?",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.Yes
    )
    
    if reply == QMessageBox.Yes:
        self.start_bak_analysis()
    else:
        self.append_terminal_output("ℹ️ Analisis BAK dibatalkan oleh user.")

def start_bak_analysis(self):
    """Start BAK file analysis"""
    self.append_terminal_output("🔍 Memulai analisis file BAK...")
    
    backup_dir = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup"
    
    # Find all BAK files
    bak_files = []
    try:
        for root, dirs, files in os.walk(backup_dir):
            for file in files:
                if file.lower().endswith('.bak'):
                    bak_files.append(os.path.join(root, file))
    except Exception as e:
        self.append_terminal_output(f"❌ Error scanning BAK files: {str(e)}")
        return

    if not bak_files:
        self.append_terminal_output("⚠️ Tidak ada file BAK ditemukan di direktori backup.")
        return

    self.append_terminal_output(f"📋 Ditemukan {len(bak_files)} file BAK:")
    for bak_file in bak_files:
        rel_path = os.path.relpath(bak_file, backup_dir)
        file_size = os.path.getsize(bak_file) / (1024 * 1024)  # MB
        self.append_terminal_output(f"  📄 {rel_path} ({file_size:.1f} MB)")

    self.append_terminal_output("=" * 60)
    self.append_terminal_output("🔬 Memulai analisis metadata BAK...")

    # Start BAK analysis worker
    self.show_progress("Menganalisis file BAK...")
    
    # Create BAK analysis worker with proper parameters
    # Use backup directory as the "zip_path" since we're analyzing extracted BAK files
    worker = self.BackupAnalysisWorker(backup_dir, "analyze_bak_files_only")
    worker.signals.finished.connect(self.on_bak_analysis_complete_terminal)
    worker.signals.error.connect(self.on_worker_error)
    worker.signals.progress.connect(self.on_worker_progress)
    
    QThreadPool.globalInstance().start(worker)

def on_bak_analysis_complete_terminal(self, result):
    """Handle BAK analysis completion for terminal output"""
    self.hide_progress()
    
    if result.get('success', False):
        self.append_terminal_output("✅ Analisis BAK selesai!")
        
        # Display results in terminal format
        if 'bak_analyses' in result:
            self.append_terminal_output("📊 HASIL ANALISIS BAK:")
            self.append_terminal_output("=" * 60)
            
            for analysis in result['bak_analyses']:
                self.append_terminal_output(f"📄 File: {analysis.get('file_name', 'Unknown')}")
                self.append_terminal_output(f"   💾 Database: {analysis.get('database_name', 'N/A')}")
                self.append_terminal_output(f"   📅 Backup Date: {analysis.get('backup_date', 'N/A')}")
                self.append_terminal_output(f"   📏 Size: {analysis.get('file_size_mb', 0):.1f} MB")
                self.append_terminal_output(f"   🔧 Type: {analysis.get('backup_type', 'N/A')}")
                self.append_terminal_output("")
            
        # Also display in regular details area for compatibility
        self.display_bak_analysis_results(result)
    else:
        error_msg = result.get('error', 'Unknown error')
        self.append_terminal_output(f"❌ Analisis BAK gagal: {error_msg}")

def append_terminal_output(self, message):
    """Append message to terminal output with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    
    # Append to terminal
    self.terminal_output.append(formatted_message)
    
    # Auto-scroll to bottom
    cursor = self.terminal_output.textCursor()
    cursor.movePosition(cursor.End)
    self.terminal_output.setTextCursor(cursor)
    
    # Process events to update UI
    QApplication.processEvents()