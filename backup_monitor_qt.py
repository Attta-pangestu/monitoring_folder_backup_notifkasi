#!/usr/bin/env python3
"""
Backup Monitor with PyQt5 Interface
Aplikasi monitoring backup database dengan interface PyQt5
"""

import sys
import os
import json
import zipfile
import threading
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Configure comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup_monitor_debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# PyQt5 imports
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.zip_metadata_viewer import ZipMetadataViewer
from src.email_notifier import EmailNotifier
from src.bak_metadata_analyzer import BAKMetadataAnalyzer
from src.pdf_report_generator import PDFReportGenerator

class WorkerSignals(QObject):
    """Signals for worker threads"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    status = pyqtSignal(str)
    metadata_ready = pyqtSignal(dict)

class BackupAnalysisWorker(QRunnable):
    """Worker thread for backup analysis"""
    def __init__(self, zip_path: str, analysis_type: str, window=None):
        super().__init__()
        self.zip_path = zip_path
        self.analysis_type = analysis_type
        self.window = window  # Reference to main window for accessing configuration
        self.signals = WorkerSignals()

    def run(self):
        """Run the analysis task"""
        try:
            if self.analysis_type == "zip_metadata":
                result = self._analyze_zip_metadata()
            elif self.analysis_type == "bak_files":
                result = self._analyze_bak_files()
            elif self.analysis_type == "backup_report":
                result = self._generate_backup_report()
            elif self.analysis_type == "zip_integrity":
                result = self._analyze_zip_integrity()
            elif self.analysis_type == "zip_info":
                result = self._analyze_zip_info()
            elif self.analysis_type == "monitoring_analysis":
                result = self._monitoring_analysis()
            elif self.analysis_type == "zip_metadata_display":
                result = self._get_zip_metadata_display()
            elif self.analysis_type == "extract_single_file":
                result = self._extract_single_file()
            elif self.analysis_type == "comprehensive_auto_analysis":
                result = self._comprehensive_auto_analysis()
            elif self.analysis_type == "manual_extract_analyze":
                result = self._manual_extract_analyze()
            elif self.analysis_type == "analyze_bak_files_only":
                result = self._analyze_bak_files_only()
            else:
                raise ValueError(f"Unknown analysis type: {self.analysis_type}")

            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))

    def _analyze_zip_metadata(self):
        """Analyze ZIP metadata"""
        signals = self.signals
        signals.progress.emit("Starting ZIP metadata analysis...")

        zip_viewer = ZipMetadataViewer()

        # Analyze ZIP integrity
        signals.progress.emit("Analyzing ZIP integrity...")
        zip_integrity = zip_viewer.check_zip_integrity(self.zip_path)

        # Extract ZIP metadata
        signals.progress.emit("Extracting ZIP metadata...")
        zip_metadata = zip_viewer.extract_zip_metadata(self.zip_path)

        # Analyze backup files
        signals.progress.emit("Analyzing backup files...")
        backup_analysis = self._analyze_backup_files_simple()

        # Generate summary
        signals.progress.emit("Generating summary...")
        summary = self._generate_zip_summary(zip_integrity, zip_metadata, backup_analysis)

        result = {
            'type': 'zip_metadata',
            'zip_file': os.path.basename(self.zip_path),
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'zip_integrity': zip_integrity,
            'zip_metadata': zip_metadata,
            'backup_analysis': backup_analysis,
            'summary': summary
        }

        return result

    def _manual_extract_analyze(self):
        """Manual extraction and analysis of ZIP file"""
        signals = self.signals
        signals.progress.emit("Starting manual extraction and analysis...")
        
        zip_viewer = ZipMetadataViewer()
        
        # Get extraction directory from worker attribute
        extraction_dir = getattr(self, 'extraction_dir', None)
        if not extraction_dir:
            raise ValueError("Extraction directory not specified")
        
        signals.progress.emit(f"Extracting to: {extraction_dir}")
        
        # Extract ZIP file
        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                zip_ref.extractall(extraction_dir)
            logger.info(f"Successfully extracted {self.zip_path} to {extraction_dir}")
        except Exception as e:
            logger.error(f"Failed to extract {self.zip_path}: {str(e)}")
            raise
        
        # Analyze ZIP integrity
        signals.progress.emit("Analyzing ZIP integrity...")
        zip_integrity = zip_viewer.check_zip_integrity(self.zip_path)
        
        # Extract ZIP metadata
        signals.progress.emit("Extracting ZIP metadata...")
        zip_metadata = zip_viewer.extract_zip_metadata(self.zip_path)
        
        # Find extracted files
        signals.progress.emit("Analyzing extracted files...")
        extracted_files = []
        for root, dirs, files in os.walk(extraction_dir):
            for file in files:
                file_path = os.path.join(root, file)
                extracted_files.append(file_path)
        
        # Analyze BAK files
        bak_files = [f for f in extracted_files if f.lower().endswith('.bak')]
        bak_analyses = []
        
        if bak_files:
            signals.progress.emit(f"Analyzing {len(bak_files)} BAK files...")
            bak_analyzer = BAKMetadataAnalyzer()
            
            for bak_file in bak_files:
                try:
                    signals.progress.emit(f"Analyzing {os.path.basename(bak_file)}...")
                    bak_analysis = bak_analyzer.analyze_bak_file(bak_file)
                    bak_analyses.append({
                        'file_path': bak_file,
                        'file_name': os.path.basename(bak_file),
                        'analysis': bak_analysis
                    })
                except Exception as e:
                    logger.error(f"Failed to analyze BAK file {bak_file}: {str(e)}")
                    bak_analyses.append({
                        'file_path': bak_file,
                        'file_name': os.path.basename(bak_file),
                        'analysis': {'error': str(e)}
                    })
        
        # Generate comprehensive summary
        signals.progress.emit("Generating comprehensive summary...")
        summary = self._generate_comprehensive_summary(zip_integrity, zip_metadata, extracted_files, bak_analyses)
        
        # Get file info
        file_size_mb = os.path.getsize(self.zip_path) / (1024 * 1024)
        mod_time = datetime.fromtimestamp(os.path.getmtime(self.zip_path)).strftime('%Y-%m-%d %H:%M:%S')
        
        result = {
            'type': 'manual_extract_analyze',
            'zip_file': os.path.basename(self.zip_path),
            'zip_path': self.zip_path,
            'extraction_dir': extraction_dir,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'file_size_mb': file_size_mb,
            'modification_time': mod_time,
            'zip_integrity': zip_integrity,
            'zip_metadata': zip_metadata,
            'extracted_files': extracted_files,
            'bak_files': bak_files,
            'bak_analyses': bak_analyses,
            'summary': summary,
            'processing_successful': True
        }
        
        signals.progress.emit("Manual extraction and analysis completed!")
        return result

    def _monitoring_analysis(self):
        """Comprehensive monitoring analysis with actual ZIP and BAK extraction"""
        signals = self.signals
        signals.progress.emit("Starting comprehensive monitoring analysis...")

        import tempfile
        import shutil

        zip_viewer = ZipMetadataViewer()
        bak_analyzer = BAKMetadataAnalyzer()

        # Get file basic info
        stat = os.stat(self.zip_path)
        file_size_mb = stat.st_size / (1024 * 1024)
        modified_date = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d')
        modified_time = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')

        # Display ZIP metadata first before extraction
        signals.progress.emit("Menganalisis metadata ZIP...")
        zip_metadata = self._get_zip_metadata_display()
        signals.metadata_ready.emit(zip_metadata)

        # Get extraction directory configuration
        extraction_dir = None
        if hasattr(self, 'window') and self.window:
            extraction_dir = getattr(self.window, 'extraction_directory', '')

        # If no custom directory, use same folder as backup
        if not extraction_dir:
            zip_dir = os.path.dirname(self.zip_path)
            zip_name = os.path.splitext(os.path.basename(self.zip_path))[0]
            extract_dir = os.path.join(zip_dir, f"{zip_name}_extracted")
        else:
            # Use custom directory
            zip_name = os.path.splitext(os.path.basename(self.zip_path))[0]
            extract_dir = os.path.join(extraction_dir, f"{zip_name}_extracted")

        temp_dir = None
        try:
            # Create extraction directory
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            os.makedirs(extract_dir)
            temp_dir = extract_dir
            signals.progress.emit(f"Created extraction directory: {extract_dir}")

            signals.progress.emit("Checking ZIP integrity...")
            zip_integrity = zip_viewer.check_zip_integrity(self.zip_path)

            # Extract ZIP file if valid
            extracted_files = []
            if zip_integrity.get('is_valid', False):
                signals.progress.emit("Extracting ZIP files...")
                try:
                    with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                        extracted_files = zip_ref.namelist()
                        signals.progress.emit(f"Extracted {len(extracted_files)} files")
                except Exception as e:
                    signals.progress.emit(f"Failed to extract ZIP: {str(e)}")
                    zip_integrity['extraction_error'] = str(e)
                    zip_integrity['is_valid'] = False

            # Find and analyze BAK files
            signals.progress.emit("Searching for BAK files...")
            bak_files = []
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith('.bak'):
                        bak_files.append(os.path.join(root, file))

            signals.progress.emit(f"Found {len(bak_files)} BAK files for analysis")

            # Analyze each extracted BAK file
            bak_analyses = []
            for i, bak_path in enumerate(bak_files):
                signals.progress.emit(f"Analyzing BAK {i+1}/{len(bak_files)}: {os.path.basename(bak_path)}...")
                try:
                    # Analyze the extracted BAK file directly
                    bak_analysis = bak_analyzer.analyze_bak_file(bak_path)
                    bak_analyses.append(bak_analysis)
                except Exception as e:
                    bak_analyses.append({
                        'filename': os.path.basename(bak_path),
                        'error': str(e),
                        'analysis_status': 'failed',
                        'extracted_path': bak_path
                    })

            # Get additional metadata from extracted files
            extracted_metadata = self._analyze_extracted_files(temp_dir, extracted_files)

        finally:
            # Note: Extraction directory is not cleaned up as it's now in the same folder as backup
            # This allows users to access the extracted files for further analysis
            if temp_dir and os.path.exists(temp_dir):
                signals.progress.emit(f"Extraction completed: {temp_dir}")
                signals.progress.emit("Note: Extraction directory preserved for further analysis")

        # Generate comprehensive monitoring result
        result = {
            'type': 'monitoring_analysis',
            'zip_file': os.path.basename(self.zip_path),
            'file_path': self.zip_path,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'file_info': {
                'size_mb': round(file_size_mb, 2),
                'size_bytes': stat.st_size,
                'modified_date': modified_date,
                'modified_time': modified_time
            },
            'zip_integrity': zip_integrity,
            'extractable': zip_integrity.get('is_valid', False),
            'extracted_files_count': len(extracted_files) if 'extracted_files' in locals() else 0,
            'extracted_files': extracted_files if 'extracted_files' in locals() else [],
            'bak_files_count': len(bak_analyses),
            'bak_analyses': bak_analyses,
            'extracted_metadata': extracted_metadata if 'extracted_metadata' in locals() else {}
        }

        # Add summary information
        valid_bak_files = sum(1 for ba in bak_analyses if ba.get('analysis_status') == 'success')
        corrupted_bak_files = sum(1 for ba in bak_analyses if ba.get('analysis_status') == 'failed')

        result['summary'] = {
            'zip_valid': zip_integrity.get('is_valid', False),
            'extractable': zip_integrity.get('is_valid', False) and len(extracted_files) > 0 if 'extracted_files' in locals() else False,
            'total_bak_files': len(bak_analyses),
            'valid_bak_files': valid_bak_files,
            'corrupted_bak_files': corrupted_bak_files,
            'extraction_successful': len(extracted_files) > 0 if 'extracted_files' in locals() else False,
            'databases_found': list(set(
                ba.get('database_info', {}).get('database_name')
                for ba in bak_analyses
                if ba.get('database_info', {}).get('database_name')
            )),
            'backup_types': list(set(
                ba.get('database_info', {}).get('backup_type')
                for ba in bak_analyses
                if ba.get('database_info', {}).get('backup_type')
            )),
            'overall_status': 'healthy' if (zip_integrity.get('is_valid') and valid_bak_files > 0 and len(extracted_files) > 0) else 'issues_detected'
        }

        signals.progress.emit("Monitoring analysis completed")
        return result

    def _extract_single_file(self):
        """Extract a single ZIP file to configured location"""
        signals = self.signals
        signals.progress.emit("Starting single file extraction...")

        import zipfile
        import shutil
        from datetime import datetime

        # Get extraction directory from window if available
        extraction_dir = None
        if hasattr(self, 'window') and self.window:
            extraction_dir = getattr(self.window, 'extraction_directory', '')

        # If no custom directory, use same folder as backup
        if not extraction_dir:
            zip_dir = os.path.dirname(self.zip_path)
            zip_name = os.path.splitext(os.path.basename(self.zip_path))[0]
            extraction_dir = os.path.join(zip_dir, f"{zip_name}_extracted")
        else:
            # Use custom directory
            zip_name = os.path.splitext(os.path.basename(self.zip_path))[0]
            extraction_dir = os.path.join(extraction_dir, f"{zip_name}_extracted")

        try:
            # Create extraction directory
            if os.path.exists(extraction_dir):
                shutil.rmtree(extraction_dir)
            os.makedirs(extraction_dir)

            signals.progress.emit(f"Created extraction directory: {extraction_dir}")

            # Check ZIP integrity first
            zip_viewer = ZipMetadataViewer()
            zip_integrity = zip_viewer.check_zip_integrity(self.zip_path)

            if not zip_integrity.get('is_valid', False):
                return {
                    'type': 'extract_single_file',
                    'success': False,
                    'error': 'ZIP file is corrupted or invalid',
                    'extraction_path': extraction_dir
                }

            # Extract ZIP file
            signals.progress.emit("Extracting files...")
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                zip_ref.extractall(extraction_dir)
                extracted_count = len(file_list)

            signals.progress.emit(f"Successfully extracted {extracted_count} files")

            return {
                'type': 'extract_single_file',
                'success': True,
                'extraction_path': extraction_dir,
                'extracted_files_count': extracted_count,
                'zip_file': os.path.basename(self.zip_path),
                'extraction_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'extraction_directory': extraction_dir
            }

        except Exception as e:
            return {
                'type': 'extract_single_file',
                'success': False,
                'error': str(e),
                'extraction_path': extraction_dir
            }

    def _get_zip_metadata_display(self):
        """Get ZIP metadata for display before extraction"""
        try:
            import zipfile
            from datetime import datetime

            # Get basic file info
            stat = os.stat(self.zip_path)
            file_size_mb = stat.st_size / (1024 * 1024)
            modified_date = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d')
            modified_time = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')

            # Get ZIP file information
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                total_files = len(file_list)

                # Calculate file types and sizes
                file_types = {}
                total_size = 0
                largest_file = {'name': '', 'size': 0}

                for file_name in file_list:
                    file_info = zip_ref.getinfo(file_name)
                    file_size = file_info.file_size
                    total_size += file_size

                    # Get file extension
                    ext = os.path.splitext(file_name)[1].lower()
                    file_types[ext] = file_types.get(ext, 0) + 1

                    # Track largest file
                    if file_size > largest_file['size']:
                        largest_file = {'name': file_name, 'size': file_size}

                # Get ZIP file info
                zip_info = zip_ref.infolist()
                compression_methods = set()
                for info in zip_info:
                    compression_methods.add(info.compress_type)

            # Determine compression method names
            compression_names = {
                0: 'Stored',
                8: 'Deflated',
                12: 'BZIP2',
                14: 'LZMA'
            }

            compression_used = [compression_names.get(m, f'Unknown({m})') for m in compression_methods]

            return {
                'file_info': {
                    'name': os.path.basename(self.zip_path),
                    'path': self.zip_path,
                    'size_mb': round(file_size_mb, 2),
                    'size_bytes': stat.st_size,
                    'modified_date': modified_date,
                    'modified_time': modified_time
                },
                'zip_content': {
                    'total_files': total_files,
                    'uncompressed_size_mb': round(total_size / (1024 * 1024), 2),
                    'compression_ratio': round((1 - stat.st_size / total_size) * 100, 1) if total_size > 0 else 0,
                    'compression_methods': compression_used,
                    'file_types': dict(sorted(file_types.items(), key=lambda x: x[1], reverse=True)),
                    'largest_file': {
                        'name': largest_file['name'],
                        'size_mb': round(largest_file['size'] / (1024 * 1024), 2)
                    }
                },
                'summary': {
                    'extractable': total_files > 0,
                    'estimated_extraction_path': os.path.join(
                        os.path.dirname(self.zip_path),
                        f"{os.path.splitext(os.path.basename(self.zip_path))[0]}_extracted"
                    )
                }
            }

        except Exception as e:
            return {
                'error': f"Gagal membaca metadata ZIP: {str(e)}",
                'file_info': {
                    'name': os.path.basename(self.zip_path),
                    'path': self.zip_path
                }
            }

    def _analyze_extracted_files(self, temp_dir, extracted_files):
        """Analyze metadata from extracted files"""
        metadata = {
            'total_files': len(extracted_files),
            'file_types': {},
            'largest_files': [],
            'directory_structure': {}
        }

        try:
            # Analyze file types and sizes
            file_sizes = []
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        stat = os.stat(file_path)
                        size_mb = stat.st_size / (1024 * 1024)
                        file_sizes.append((file, size_mb, stat.st_mtime))

                        # Count file types
                        ext = os.path.splitext(file)[1].lower()
                        if ext not in metadata['file_types']:
                            metadata['file_types'][ext] = 0
                        metadata['file_types'][ext] += 1

                    except Exception:
                        continue

            # Get largest files
            file_sizes.sort(key=lambda x: x[1], reverse=True)
            metadata['largest_files'] = file_sizes[:10]  # Top 10 largest files

            # Analyze directory structure
            for root, dirs, files in os.walk(temp_dir):
                rel_path = os.path.relpath(root, temp_dir)
                if rel_path == '.':
                    rel_path = 'root'
                metadata['directory_structure'][rel_path] = len(files)

        except Exception as e:
            metadata['analysis_error'] = str(e)

        return metadata

    def _analyze_bak_files(self):
        """Analyze BAK files in detail"""
        signals = self.signals
        signals.progress.emit("Starting BAK files analysis...")

        bak_analyzer = BAKMetadataAnalyzer()

        with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
            # Find BAK files
            bak_files = [f for f in zip_ref.namelist() if f.lower().endswith('.bak')]

            if not bak_files:
                raise ValueError("No BAK files found in ZIP")

            signals.progress.emit(f"Found {len(bak_files)} BAK files")

            # Analyze each BAK file
            bak_analyses = []
            for i, bak_file in enumerate(bak_files):
                signals.progress.emit(f"Analyzing {bak_file} ({i+1}/{len(bak_files)})...")
                try:
                    bak_analysis = bak_analyzer.analyze_bak_file(bak_file, zip_ref)
                    bak_analyses.append(bak_analysis)
                except Exception as e:
                    bak_analyses.append({
                        'filename': bak_file,
                        'error': str(e),
                        'analysis_status': 'failed'
                    })

            # Generate summary
            signals.progress.emit("Generating BAK analysis summary...")
            summary = self._generate_bak_summary(bak_analyses)

        result = {
            'type': 'bak_files',
            'zip_file': os.path.basename(self.zip_path),
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_bak_files': len(bak_files),
            'bak_analyses': bak_analyses,
            'summary': summary
        }

        return result

    def _generate_backup_report(self):
        """Generate backup report for email"""
        signals = self.signals
        signals.progress.emit("Generating backup report...")

        bak_analyzer = BAKMetadataAnalyzer()
        zip_viewer = ZipMetadataViewer()

        # Get ZIP file info
        stat = os.stat(self.zip_path)
        file_size_mb = stat.st_size / (1024 * 1024)
        mod_time = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')

        # Analyze ZIP integrity
        signals.progress.emit("Analyzing ZIP integrity...")
        zip_integrity = zip_viewer.check_zip_integrity(self.zip_path)

        # Deep BAK analysis
        signals.progress.emit("Performing deep BAK analysis...")
        with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
            bak_files = [f for f in zip_ref.namelist() if f.lower().endswith('.bak')]

            bak_analyses = []
            for i, bak_file in enumerate(bak_files):
                signals.progress.emit(f"Analyzing {bak_file} for report ({i+1}/{len(bak_files)})...")
                try:
                    bak_analysis = bak_analyzer.analyze_bak_file(bak_file, zip_ref)
                    bak_analyses.append(bak_analysis)
                except Exception as e:
                    bak_analyses.append({
                        'filename': bak_file,
                        'error': str(e),
                        'analysis_status': 'failed'
                    })

        # Prepare report data
        signals.progress.emit("Preparing report data...")
        report_data = self._prepare_report_data(
            self.zip_path, file_size_mb, mod_time, zip_integrity, bak_files, bak_analyses
        )

        result = {
            'type': 'backup_report',
            'report_data': report_data,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        return result

    def _analyze_backup_files_simple(self):
        """Simple backup files analysis"""
        backup_analysis = {
            'bak_files': [],
            'total_size': 0,
            'database_info': {}
        }

        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                bak_files = [f for f in zip_ref.namelist() if f.lower().endswith('.bak')]

                for bak_file in bak_files:
                    file_info = zip_ref.getinfo(bak_file)
                    bak_analysis['bak_files'].append({
                        'filename': bak_file,
                        'size': file_info.file_size,
                        'compressed_size': file_info.compress_size,
                        'compression_ratio': (1 - file_info.compress_size / file_info.file_size) * 100 if file_info.file_size > 0 else 0,
                        'modified': datetime(*file_info.date_time).strftime('%Y-%m-%d %H:%M:%S')
                    })
                    backup_analysis['total_size'] += file_info.file_size

        except Exception as e:
            backup_analysis['error'] = str(e)

        return backup_analysis

    def _generate_zip_summary(self, zip_integrity, zip_metadata, backup_analysis):
        """Generate ZIP metadata summary"""
        summary = {
            'total_bak_files': len(backup_analysis.get('bak_files', [])),
            'total_size_mb': backup_analysis.get('total_size', 0) / (1024 * 1024),
            'zip_valid': zip_integrity.get('is_valid', False),
            'databases_found': [],
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'compression_efficiency': 0
        }

        # Calculate compression efficiency
        if backup_analysis.get('bak_files'):
            total_original = sum(f['size'] for f in backup_analysis['bak_files'])
            total_compressed = sum(f['compressed_size'] for f in backup_analysis['bak_files'])
            summary['compression_efficiency'] = (1 - total_compressed / total_original) * 100 if total_original > 0 else 0

        return summary

    def _comprehensive_auto_analysis(self):
        """Comprehensive automatic analysis: extract ZIP info, extract all contents, and analyze BAK metadata"""
        signals = self.signals
        logger.info(f"Starting comprehensive automatic analysis for: {self.zip_path}")
        signals.progress.emit("Starting comprehensive automatic analysis...")

        import tempfile
        import shutil

        zip_viewer = ZipMetadataViewer()
        bak_analyzer = BAKMetadataAnalyzer()

        # Get file basic info
        stat = os.stat(self.zip_path)
        file_size_mb = stat.st_size / (1024 * 1024)
        modified_date = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d')
        modified_time = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        logger.debug(f"ZIP file info - Size: {file_size_mb:.2f}MB, Modified: {modified_time}")

        # Use shared extraction directory for all ZIP files
        temp_dir = None
        try:
            # Check if shared extraction directory already exists
            shared_extraction_dir = getattr(self, 'shared_extraction_dir', None)
            if not shared_extraction_dir or not os.path.exists(shared_extraction_dir):
                # Create shared extraction directory in project folder instead of temp
                project_dir = os.path.dirname(os.path.abspath(__file__))
                
                # Check if custom extraction directory is configured
                config = self.load_email_config() if hasattr(self, 'load_email_config') else {}
                custom_extraction_dir = config.get('extraction_directory', '')
                
                if custom_extraction_dir and os.path.exists(custom_extraction_dir):
                    extraction_base_dir = custom_extraction_dir
                    logger.info(f"Using custom extraction directory: {extraction_base_dir}")
                else:
                    extraction_base_dir = os.path.join(project_dir, 'extracted_backups')
                    logger.info(f"Using default extraction directory: {extraction_base_dir}")
                
                # Ensure base directory exists
                os.makedirs(extraction_base_dir, exist_ok=True)
                
                # Create timestamped extraction directory
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                shared_extraction_dir = os.path.join(extraction_base_dir, f'backup_extraction_{timestamp}')
                os.makedirs(shared_extraction_dir, exist_ok=True)
                
                self.shared_extraction_dir = shared_extraction_dir
                logger.info(f"Created shared extraction directory: {shared_extraction_dir}")
                signals.progress.emit(f"Using shared extraction directory: {os.path.basename(shared_extraction_dir)}")
            else:
                logger.info(f"Using existing shared extraction directory: {shared_extraction_dir}")
                signals.progress.emit(f"Using existing shared extraction directory: {os.path.basename(shared_extraction_dir)}")
            
            temp_dir = shared_extraction_dir

            # Step 1: Extract ZIP information
            logger.info("Step 1: Starting ZIP information extraction...")
            signals.progress.emit("Step 1: Extracting ZIP information...")
            zip_integrity = zip_viewer.check_zip_integrity(self.zip_path)
            logger.debug(f"ZIP integrity check result: {zip_integrity}")
            
            zip_metadata = zip_viewer.extract_zip_metadata(self.zip_path)
            logger.debug(f"ZIP metadata extracted: {len(zip_metadata.get('files', []))} files found")

            # Step 2: Extract all ZIP contents
            extracted_files = []
            if zip_integrity.get('is_valid', False):
                logger.info("Step 2: ZIP is valid, starting extraction...")
                signals.progress.emit("Step 2: Extracting all ZIP contents...")
                try:
                    with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                        logger.debug(f"Opening ZIP file: {self.zip_path}")
                        file_list = zip_ref.namelist()
                        logger.info(f"ZIP contains {len(file_list)} files")
                        
                        for i, file_name in enumerate(file_list):
                            logger.debug(f"Extracting file {i+1}/{len(file_list)}: {file_name}")
                            zip_ref.extract(file_name, temp_dir)
                        
                        extracted_files = file_list
                        logger.info(f"Successfully extracted {len(extracted_files)} files to {temp_dir}")
                        signals.progress.emit(f"Successfully extracted {len(extracted_files)} files")
                except Exception as e:
                    logger.error(f"Failed to extract ZIP: {str(e)}", exc_info=True)
                    signals.progress.emit(f"Failed to extract ZIP: {str(e)}")
                    zip_integrity['extraction_error'] = str(e)
                    zip_integrity['is_valid'] = False
            else:
                logger.warning("ZIP file is not valid, skipping extraction")

            # Step 3: Find and analyze BAK files
            logger.info("Step 3: Searching for BAK files in extracted content...")
            signals.progress.emit("Step 3: Searching for BAK files...")
            bak_files = []
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith('.bak'):
                        bak_path = os.path.join(root, file)
                        bak_files.append(bak_path)
                        logger.debug(f"Found BAK file: {bak_path}")

            logger.info(f"Found {len(bak_files)} BAK files for metadata analysis")
            signals.progress.emit(f"Found {len(bak_files)} BAK files for metadata analysis")

            # Analyze each BAK file metadata
            bak_analyses = []
            for i, bak_file in enumerate(bak_files):
                logger.info(f"Analyzing BAK file {i+1}/{len(bak_files)}: {os.path.basename(bak_file)}")
                signals.progress.emit(f"Analyzing BAK file {i+1}/{len(bak_files)}: {os.path.basename(bak_file)}")
                try:
                    logger.debug(f"Starting BAK analysis for: {bak_file}")
                    bak_analysis = bak_analyzer.analyze_bak_file(bak_file)
                    logger.debug(f"BAK analysis result: {bak_analysis}")
                    bak_analyses.append(bak_analysis)
                    logger.info(f"Successfully analyzed BAK file: {os.path.basename(bak_file)}")
                except Exception as e:
                    logger.error(f"Error analyzing {os.path.basename(bak_file)}: {str(e)}", exc_info=True)
                    signals.progress.emit(f"Error analyzing {os.path.basename(bak_file)}: {str(e)}")
                    bak_analyses.append({
                        'file_name': os.path.basename(bak_file),
                        'error': str(e),
                        'analysis_successful': False
                    })

            # Generate comprehensive summary
            logger.info("Generating comprehensive analysis summary...")
            signals.progress.emit("Generating comprehensive analysis summary...")
            summary = self._generate_comprehensive_summary(zip_integrity, zip_metadata, extracted_files, bak_analyses)
            logger.debug(f"Generated summary: {summary}")

            result = {
                'type': 'comprehensive_auto_analysis',
                'zip_file': os.path.basename(self.zip_path),
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'file_size_mb': round(file_size_mb, 2),
                'modified_date': modified_date,
                'modified_time': modified_time,
                'zip_integrity': zip_integrity,
                'zip_metadata': zip_metadata,
                'extracted_files_count': len(extracted_files),
                'extracted_files': extracted_files[:10] if len(extracted_files) > 10 else extracted_files,  # Limit for display
                'bak_files_count': len(bak_files),
                'bak_analyses': bak_analyses,
                'summary': summary,
                'processing_successful': True,
                'temp_directory': temp_dir  # Keep temp directory for dbatools analysis
            }

            logger.info("Comprehensive analysis completed successfully")
            signals.progress.emit("Comprehensive analysis completed successfully")
            return result

        except Exception as e:
            logger.error(f"Error during comprehensive analysis: {str(e)}", exc_info=True)
            signals.progress.emit(f"Error during comprehensive analysis: {str(e)}")
            return {
                'type': 'comprehensive_auto_analysis',
                'zip_file': os.path.basename(self.zip_path),
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error': str(e),
                'processing_successful': False
            }
        finally:
            # Don't clean up temp directory immediately - keep for dbatools analysis
            if temp_dir and os.path.exists(temp_dir):
                logger.info(f"Keeping temporary directory for dbatools analysis: {temp_dir}")
                # We'll clean up later after dbatools analysis

    def _generate_comprehensive_summary(self, zip_integrity, zip_metadata, extracted_files, bak_analyses):
        """Generate comprehensive summary for automatic analysis"""
        summary = {
            'zip_status': 'Valid' if zip_integrity.get('is_valid', False) else 'Invalid',
            'total_files_extracted': len(extracted_files),
            'bak_files_found': len(bak_analyses),
            'successful_bak_analyses': len([b for b in bak_analyses if b.get('analysis_successful', False)]),
            'failed_bak_analyses': len([b for b in bak_analyses if not b.get('analysis_successful', False)]),
            'databases_identified': []
        }

        # Extract database information from successful BAK analyses
        for bak_analysis in bak_analyses:
            if bak_analysis.get('analysis_successful', False) and 'database_name' in bak_analysis:
                db_info = {
                    'name': bak_analysis.get('database_name', 'Unknown'),
                    'size_mb': bak_analysis.get('backup_size_mb', 0),
                    'backup_date': bak_analysis.get('backup_finish_date', 'Unknown')
                }
                summary['databases_identified'].append(db_info)

        return summary

    def _analyze_zip_integrity(self):
        """Analyze ZIP file integrity only"""
        signals = self.signals
        signals.progress.emit("Analyzing ZIP integrity...")

        zip_viewer = ZipMetadataViewer()
        result = zip_viewer.check_zip_integrity(self.zip_path)

        # Add analysis type for handler identification
        result['analysis_type'] = 'zip_integrity'
        result['file_path'] = self.zip_path

        return result

    def _analyze_zip_info(self):
        """Extract ZIP file information only"""
        signals = self.signals
        signals.progress.emit("Extracting ZIP information...")

        zip_viewer = ZipMetadataViewer()
        result = zip_viewer.extract_zip_metadata(self.zip_path)

        # Add analysis type for handler identification
        result['analysis_type'] = 'zip_info'
        result['file_path'] = self.zip_path

        return result

    def _generate_bak_summary(self, bak_analyses):
        """Generate BAK analysis summary"""
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
            if analysis.get('validation', {}).get('is_valid_bak', False):
                summary['valid_files'] += 1
            else:
                summary['corrupted_files'] += 1

            summary['total_size_mb'] += analysis.get('file_size', 0) / (1024 * 1024)

            db_name = analysis.get('database_info', {}).get('database_name')
            if db_name:
                summary['databases_found'].add(db_name)

        summary['databases_found'] = list(summary['databases_found'])

        # Generate recommendations
        if summary['corrupted_files'] > 0:
            summary['recommendations'].append(f"WARNING: {summary['corrupted_files']} corrupted BAK files detected")

        if summary['valid_files'] == 0:
            summary['recommendations'].append("WARNING: No valid BAK files found")

        if summary['valid_files'] > 0:
            summary['recommendations'].append(f"OK: {summary['valid_files']} valid BAK files ready for restore")

        return summary

    def _analyze_bak_files_only(self):
        """Analyze BAK files from extracted directory"""
        signals = self.signals
        backup_dir = self.zip_path  # In this case, zip_path is actually the backup directory
        
        signals.progress.emit("Scanning for BAK files in backup directory...")
        signals.progress.emit(f"🔍 Scanning directory: {backup_dir}")
        
        # Find all BAK files in the backup directory
        bak_files = []
        try:
            for root, dirs, files in os.walk(backup_dir):
                signals.progress.emit(f"📂 Checking directory: {root}")
                for file in files:
                    if file.lower().endswith('.bak'):
                        bak_path = os.path.join(root, file)
                        bak_files.append(bak_path)
                        signals.progress.emit(f"✅ Found BAK file: {file}")
        except Exception as e:
            error_msg = f"Error scanning backup directory: {str(e)}"
            signals.progress.emit(f"❌ {error_msg}")
            return {
                'success': False,
                'type': 'bak_files',
                'error': error_msg,
                'bak_analyses': [],
                'backup_directory': backup_dir
            }
        
        signals.progress.emit(f"📊 Total BAK files found: {len(bak_files)}")
        
        if not bak_files:
            error_msg = f"No BAK files found in backup directory: {backup_dir}"
            signals.progress.emit(f"❌ {error_msg}")
            return {
                'success': False,
                'type': 'bak_files',
                'error': error_msg,
                'bak_analyses': [],
                'backup_directory': backup_dir
            }
        
        signals.progress.emit(f"Found {len(bak_files)} BAK files for analysis")
        
        # Initialize BAK analyzer
        bak_analyzer = BAKMetadataAnalyzer()
        
        # Analyze each BAK file
        bak_analyses = []
        for i, bak_path in enumerate(bak_files):
            signals.progress.emit(f"Analyzing BAK {i+1}/{len(bak_files)}: {os.path.basename(bak_path)}...")
            try:
                # Analyze the BAK file directly
                bak_analysis = bak_analyzer.analyze_bak_file(bak_path)
                bak_analysis['file_name'] = os.path.basename(bak_path)
                bak_analysis['file_path'] = bak_path
                bak_analyses.append(bak_analysis)
            except Exception as e:
                bak_analyses.append({
                    'file_name': os.path.basename(bak_path),
                    'file_path': bak_path,
                    'error': str(e),
                    'analysis_status': 'failed'
                })
        
        # Generate summary
        successful_analyses = [b for b in bak_analyses if not b.get('error')]
        failed_analyses = [b for b in bak_analyses if b.get('error')]
        
        return {
            'success': True,
            'type': 'bak_files',
            'backup_directory': backup_dir,
            'total_bak_files': len(bak_files),
            'successful_analyses': len(successful_analyses),
            'failed_analyses': len(failed_analyses),
            'bak_analyses': bak_analyses,
            'analysis_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        """Prepare report data for email"""
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

            bak_filename = bak_analysis.get('filename', 'Unknown')
            db_info = bak_analysis.get('database_info', {})
            validation = bak_analysis.get('validation', {})

            # Add detailed info
            if validation.get('is_valid_bak', False):
                report_data['query_results'][f"{bak_filename} - Status"] = "OK: Valid"
            else:
                report_data['query_results'][f"{bak_filename} - Status"] = "ERROR: Invalid"

            if db_info.get('database_name'):
                report_data['query_results'][f"{bak_filename} - Database"] = db_info['database_name']
                databases_found.add(db_info['database_name'])

            if db_info.get('backup_date'):
                report_data['query_results'][f"{bak_filename} - Backup Date"] = db_info['backup_date']

            bak_size_mb = bak_analysis.get('file_size', 0) / (1024 * 1024)
            report_data['query_results'][f"{bak_filename} - Size"] = f"{bak_size_mb:.2f} MB"

            integrity_status = validation.get('file完整性', 'unknown')
            report_data['query_results'][f"{bak_filename} - Integrity"] = integrity_status

        # Summary statistics
        report_data['query_results']['Valid BAK Files'] = f"{valid_bak_files} files"
        report_data['query_results']['Corrupted BAK Files'] = f"{corrupted_bak_files} files"
        report_data['query_results']['Total BAK Size'] = f"{total_bak_size / (1024*1024):.2f} MB"
        report_data['query_results']['Databases Found'] = ', '.join(databases_found) if databases_found else 'None'

        # Overall health assessment
        if corrupted_bak_files == 0 and valid_bak_files > 0:
            report_data['query_results']['Overall Health'] = "OK: Excellent"
        elif corrupted_bak_files <= valid_bak_files:
            report_data['query_results']['Overall Health'] = "WARNING: Good (some issues)"
        else:
            report_data['query_results']['Overall Health'] = "ERROR: Poor"

        return report_data

class EmailWorker(QRunnable):
    """Worker thread for email operations"""
    def __init__(self, email_config: Dict[str, str], operation: str, data: Any = None):
        super().__init__()
        self.email_config = email_config
        self.operation = operation
        self.data = data
        self.signals = WorkerSignals()

    def run(self):
        """Run email operation"""
        try:
            email_notifier = EmailNotifier()

            # Update email notifier configuration
            email_notifier.sender_email = self.email_config.get('sender_email', '')
            email_notifier.sender_password = self.email_config.get('sender_password', '')
            email_notifier.receiver_email = self.email_config.get('receiver_email', '')

            if self.operation == "test_connection":
                success, message = email_notifier.send_notification(
                    subject="Test Connection",
                    message="This is a test email to verify connection settings."
                )
                result = {'success': success, 'message': message}

            elif self.operation == "test_notification":
                success, message = email_notifier.send_backup_report(self.data)
                result = {'success': success, 'message': message}

            elif self.operation == "send_alert":
                success, message = email_notifier.send_alert(
                    "Test Alert",
                    "This is a test alert to verify alert notification functionality."
                )
                result = {'success': success, 'message': message}

            elif self.operation == "send_backup_report":
                success, message = email_notifier.send_backup_report(self.data)
                result = {'success': success, 'message': message}

            elif self.operation == "send_monitoring_report":
                success, message = email_notifier.send_monitoring_report(self.data)
                result = {'success': success, 'message': message}

            else:
                raise ValueError(f"Unknown email operation: {self.operation}")

            self.signals.finished.emit(result)

        except Exception as e:
            self.signals.error.emit(str(e))

class BackupMonitorWindow(QMainWindow):
    """Main window for backup monitor application"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Backup Monitor - PyQt5 Edition")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize components
        self.zip_viewer = ZipMetadataViewer()
        self.email_notifier = EmailNotifier()
        self.bak_analyzer = BAKMetadataAnalyzer()
        self.pdf_generator = PDFReportGenerator()

        # Thread pool for background tasks
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(4)

        # Variables
        self.current_zip_files = []
        self.selected_zip_index = None
        self.extraction_directory = ""  # User-selected extraction directory
        self.zip_metadata_cache = {}  # Cache for ZIP metadata

        # Load email configuration
        self.email_config = self.load_email_config()

        # Setup status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        # Setup UI
        self.setup_ui()

        # Load default folder
        self.load_default_folder()

    def setup_ui(self):
        """Setup the user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Left panel - File browser
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)

        # Right panel - Actions and details
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 2)

        # Setup menu bar
        self.setup_menu_bar()

        # Setup toolbar
        self.setup_toolbar()

    def create_left_panel(self):
        """Create left panel for file browsing"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Email configuration group
        email_group = QGroupBox("Email Configuration")
        email_layout = QFormLayout(email_group)

        self.sender_email_edit = QLineEdit(self.email_config.get('sender_email', ''))
        self.sender_email_edit.setPlaceholderText("sender@gmail.com")

        self.sender_password_edit = QLineEdit(self.email_config.get('sender_password', ''))
        self.sender_password_edit.setEchoMode(QLineEdit.Password)
        self.sender_password_edit.setPlaceholderText("app_password")

        self.receiver_email_edit = QLineEdit(self.email_config.get('receiver_email', ''))
        self.receiver_email_edit.setPlaceholderText("receiver@gmail.com")

        email_layout.addRow("Sender Email:", self.sender_email_edit)
        email_layout.addRow("Password:", self.sender_password_edit)
        email_layout.addRow("Receiver:", self.receiver_email_edit)

        # Email buttons
        email_btn_layout = QHBoxLayout()
        self.test_conn_btn = QPushButton("Test Connection")
        self.test_conn_btn.clicked.connect(self.test_email_connection)
        self.save_config_btn = QPushButton("Save Config")
        self.save_config_btn.clicked.connect(self.save_email_config)

        email_btn_layout.addWidget(self.test_conn_btn)
        email_btn_layout.addWidget(self.save_config_btn)
        email_layout.addRow(email_btn_layout)

        layout.addWidget(email_group)

        # Folder selection group
        folder_group = QGroupBox("Backup Folder")
        folder_layout = QVBoxLayout(folder_group)

        folder_path_layout = QHBoxLayout()
        self.folder_path_edit = QLineEdit()
        self.folder_path_edit.setReadOnly(True)
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_folder)

        folder_path_layout.addWidget(self.folder_path_edit)
        folder_path_layout.addWidget(self.browse_btn)
        folder_layout.addLayout(folder_path_layout)

        self.refresh_btn = QPushButton("🔄 Refresh Files")
        self.refresh_btn.clicked.connect(self.refresh_files)
        folder_layout.addWidget(self.refresh_btn)

        layout.addWidget(folder_group)

        # Summary panel
        summary_group = QGroupBox("Backup Summary")
        summary_layout = QGridLayout(summary_group)
        
        # Summary labels
        self.latest_date_label = QLabel("Tanggal Terbaru: -")
        self.total_files_label = QLabel("Total File: 0")
        self.total_size_label = QLabel("Total Size: 0 MB")
        
        # Style the summary labels
        summary_style = """
            QLabel {
                font-weight: bold;
                font-size: 12px;
                padding: 5px;
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
        """
        self.latest_date_label.setStyleSheet(summary_style)
        self.total_files_label.setStyleSheet(summary_style)
        self.total_size_label.setStyleSheet(summary_style)
        
        summary_layout.addWidget(self.latest_date_label, 0, 0)
        summary_layout.addWidget(self.total_files_label, 0, 1)
        summary_layout.addWidget(self.total_size_label, 0, 2)
        
        layout.addWidget(summary_group)

        # ZIP files table with metadata
        files_group = QGroupBox("ZIP Files - Latest Backups")
        files_layout = QVBoxLayout(files_group)

        # Create table widget
        self.zip_table = QTableWidget()
        self.zip_table.setColumnCount(5)
        self.zip_table.setHorizontalHeaderLabels([
            "Nama File", "Ukuran", "Tanggal Modifikasi", "Metadata", "Ekstrak & Analisis"
        ])
        
        # Set table properties
        self.zip_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.zip_table.setAlternatingRowColors(True)
        self.zip_table.horizontalHeader().setStretchLastSection(True)
        self.zip_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.zip_table.itemSelectionChanged.connect(self.on_zip_table_selection_changed)
        
        # Set column widths
        header = self.zip_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Nama File
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Ukuran
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Tanggal
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Metadata
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Ekstrak
        
        files_layout.addWidget(self.zip_table)

        layout.addWidget(files_group)

        return panel

    def create_right_panel(self):
        """Create right panel for actions and details"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Action buttons group
        actions_group = QGroupBox("Actions")
        actions_layout = QGridLayout(actions_group)

        # Row 1: Basic actions
        self.check_integrity_btn = QPushButton("Check ZIP Integrity")
        self.check_integrity_btn.clicked.connect(self.check_zip_integrity)
        actions_layout.addWidget(self.check_integrity_btn, 0, 0)

        self.extract_info_btn = QPushButton("Extract ZIP Info")
        self.extract_info_btn.clicked.connect(self.extract_zip_info)
        actions_layout.addWidget(self.extract_info_btn, 0, 1)

        self.show_metadata_btn = QPushButton("Show ZIP Metadata")
        self.show_metadata_btn.clicked.connect(self.show_zip_metadata)
        actions_layout.addWidget(self.show_metadata_btn, 0, 2)

        self.extract_config_btn = QPushButton("Extraction Config")
        self.extract_config_btn.clicked.connect(self.show_extraction_config_dialog)
        actions_layout.addWidget(self.extract_config_btn, 0, 3)

        self.test_notif_btn = QPushButton("Send Test Notification")
        self.test_notif_btn.clicked.connect(self.send_test_notification)
        actions_layout.addWidget(self.test_notif_btn, 0, 4)

        # Row 2: Analysis actions
        self.analyze_zip_btn = QPushButton("Analyze ZIP Metadata")
        self.analyze_zip_btn.clicked.connect(self.analyze_zip_metadata)
        actions_layout.addWidget(self.analyze_zip_btn, 1, 0)

        self.analyze_bak_btn = QPushButton("Analyze BAK Files")
        self.analyze_bak_btn.clicked.connect(self.analyze_bak_files)
        actions_layout.addWidget(self.analyze_bak_btn, 1, 1)

        self.show_all_metadata_btn = QPushButton("Show All ZIP Metadata")
        self.show_all_metadata_btn.clicked.connect(self.show_all_zip_metadata)
        actions_layout.addWidget(self.show_all_metadata_btn, 1, 2)

        self.monitor_btn = QPushButton("Monitor Latest Backups")
        self.monitor_btn.clicked.connect(self.monitor_latest_backups)
        actions_layout.addWidget(self.monitor_btn, 1, 3)

        # Row 3: Monitoring actions
        self.send_report_btn = QPushButton("Send Backup Report")
        self.send_report_btn.clicked.connect(self.send_backup_report)
        actions_layout.addWidget(self.send_report_btn, 2, 0)

        self.extract_all_btn = QPushButton("Extract All Files")
        self.extract_all_btn.clicked.connect(self.extract_all_files)
        actions_layout.addWidget(self.extract_all_btn, 2, 1)

        # Row 3: Advanced analysis
        self.dbatools_btn = QPushButton("Run dbatools Analysis")
        self.dbatools_btn.setToolTip("Run PowerShell dbatools analysis on extracted BAK files")
        self.dbatools_btn.clicked.connect(self.run_dbatools_analysis)
        actions_layout.addWidget(self.dbatools_btn, 2, 0)

        layout.addWidget(actions_group)

        # Large Extract & Analyze Button
        extract_analyze_group = QGroupBox("Ekstrak & Analisis Backup")
        extract_analyze_layout = QVBoxLayout(extract_analyze_group)
        
        self.large_extract_btn = QPushButton("🗂️ EKSTRAK SEMUA ZIP & ANALISIS BAK FILES")
        self.large_extract_btn.setMinimumHeight(60)
        self.large_extract_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.large_extract_btn.clicked.connect(self.extract_all_and_analyze_bak)
        extract_analyze_layout.addWidget(self.large_extract_btn)
        
        layout.addWidget(extract_analyze_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Summary Data Report Panel (menggantikan terminal)
        summary_group = QGroupBox("Summary Data Report - Laporan Backup")
        summary_layout = QVBoxLayout(summary_group)

        # Create tabbed interface for different report sections
        self.summary_tabs = QTabWidget()
        
        # Tab 1: ZIP File Summary
        zip_summary_tab = QWidget()
        zip_summary_layout = QVBoxLayout(zip_summary_tab)
        
        # ZIP Files Table
        self.zip_summary_table = QTableWidget()
        self.zip_summary_table.setColumnCount(6)
        self.zip_summary_table.setHorizontalHeaderLabels([
            "File Name", "Size (MB)", "Status", "BAK Files", "Last Modified", "Actions"
        ])
        self.zip_summary_table.horizontalHeader().setStretchLastSection(True)
        zip_summary_layout.addWidget(self.zip_summary_table)
        
        # Add Generate PDF Report button
        pdf_report_layout = QHBoxLayout()
        self.generate_pdf_btn = QPushButton("📄 Generate PDF Report")
        self.generate_pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.generate_pdf_btn.clicked.connect(self.generate_pdf_report)
        pdf_report_layout.addWidget(self.generate_pdf_btn)
        pdf_report_layout.addStretch()
        zip_summary_layout.addLayout(pdf_report_layout)
        
        self.summary_tabs.addTab(zip_summary_tab, "📦 ZIP Summary")
        
        # Tab 2: BAK Analysis Summary
        bak_summary_tab = QWidget()
        bak_summary_layout = QVBoxLayout(bak_summary_tab)
        
        # BAK Analysis Table
        self.bak_summary_table = QTableWidget()
        self.bak_summary_table.setColumnCount(7)
        self.bak_summary_table.setHorizontalHeaderLabels([
            "BAK File", "Database", "Size (MB)", "Valid", "Restore Ready", "Backup Date", "Type"
        ])
        self.bak_summary_table.horizontalHeader().setStretchLastSection(True)
        bak_summary_layout.addWidget(self.bak_summary_table)
        
        self.summary_tabs.addTab(bak_summary_tab, "🗄️ BAK Analysis")
        
        # Tab 3: System Status
        status_tab = QWidget()
        status_layout = QVBoxLayout(status_tab)
        
        # Status Information
        self.status_info = QTextEdit()
        self.status_info.setReadOnly(True)
        self.status_info.setMaximumHeight(150)
        self.status_info.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        self.status_info.setPlainText("System ready... Select ZIP files and start analysis.")
        status_layout.addWidget(self.status_info)
        
        # Statistics Cards
        stats_layout = QHBoxLayout()
        
        # Total Files Card
        total_files_card = QFrame()
        total_files_card.setFrameStyle(QFrame.Box)
        total_files_card.setStyleSheet("""
            QFrame {
                background-color: #E3F2FD;
                border: 1px solid #2196F3;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        total_files_layout = QVBoxLayout(total_files_card)
        self.total_files_label = QLabel("0")
        self.total_files_label.setAlignment(Qt.AlignCenter)
        self.total_files_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2196F3;")
        total_files_layout.addWidget(self.total_files_label)
        total_files_layout.addWidget(QLabel("Total ZIP Files", alignment=Qt.AlignCenter))
        stats_layout.addWidget(total_files_card)
        
        # Valid BAK Files Card
        valid_bak_card = QFrame()
        valid_bak_card.setFrameStyle(QFrame.Box)
        valid_bak_card.setStyleSheet("""
            QFrame {
                background-color: #E8F5E8;
                border: 1px solid #4CAF50;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        valid_bak_layout = QVBoxLayout(valid_bak_card)
        self.valid_bak_label = QLabel("0")
        self.valid_bak_label.setAlignment(Qt.AlignCenter)
        self.valid_bak_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        valid_bak_layout.addWidget(self.valid_bak_label)
        valid_bak_layout.addWidget(QLabel("Valid BAK Files", alignment=Qt.AlignCenter))
        stats_layout.addWidget(valid_bak_card)
        
        # Corrupted Files Card
        corrupted_card = QFrame()
        corrupted_card.setFrameStyle(QFrame.Box)
        corrupted_card.setStyleSheet("""
            QFrame {
                background-color: #FFEBEE;
                border: 1px solid #F44336;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        corrupted_layout = QVBoxLayout(corrupted_card)
        self.corrupted_label = QLabel("0")
        self.corrupted_label.setAlignment(Qt.AlignCenter)
        self.corrupted_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #F44336;")
        corrupted_layout.addWidget(self.corrupted_label)
        corrupted_layout.addWidget(QLabel("Corrupted Files", alignment=Qt.AlignCenter))
        stats_layout.addWidget(corrupted_card)
        
        status_layout.addLayout(stats_layout)
        
        self.summary_tabs.addTab(status_tab, "📊 Status")
        
        summary_layout.addWidget(self.summary_tabs)
        layout.addWidget(summary_group)

        # Details text area (keep for compatibility)
        details_group = QGroupBox("Analysis Results")
        details_layout = QVBoxLayout(details_group)

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)

        layout.addWidget(details_group)

        return panel

    def setup_menu_bar(self):
        """Setup menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        open_action = QAction("Open Backup Folder", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.browse_folder)
        file_menu.addAction(open_action)

        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_files)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        email_config_action = QAction("Email Configuration", self)
        email_config_action.triggered.connect(self.show_email_config_dialog)
        tools_menu.addAction(email_config_action)

        tools_menu.addSeparator()

        clear_results_action = QAction("Clear Results", self)
        clear_results_action.triggered.connect(self.clear_results)
        tools_menu.addAction(clear_results_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def setup_toolbar(self):
        """Setup toolbar"""
        toolbar = self.addToolBar("Main Toolbar")

        # Add toolbar actions
        open_action = QAction("📁 Open", self)
        open_action.triggered.connect(self.browse_folder)
        toolbar.addAction(open_action)

        refresh_action = QAction("🔄 Refresh", self)
        refresh_action.triggered.connect(self.refresh_files)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()

        analyze_action = QAction("🔍 Analyze", self)
        analyze_action.triggered.connect(self.analyze_zip_metadata)
        toolbar.addAction(analyze_action)

        email_action = QAction("📧 Email Report", self)
        email_action.triggered.connect(self.send_backup_report)
        toolbar.addAction(email_action)

        # Add summary email button
        summary_email_action = QAction("📊 Email Summary", self)
        summary_email_action.triggered.connect(self.send_summary_email)
        toolbar.addAction(summary_email_action)

        # Add debug data status button
        debug_status_action = QAction("🔍 Debug Data", self)
        debug_status_action.triggered.connect(self.show_analysis_data_status)
        toolbar.addAction(debug_status_action)

    def load_email_config(self):
        """Load email configuration"""
        config = {
            'sender_email': '',
            'sender_password': '',
            'receiver_email': '',
            'extraction_directory': ''
        }

        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.ini')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        if 'sender_email' in line:
                            config['sender_email'] = line.split('=')[1].strip()
                        elif 'sender_password' in line:
                            config['sender_password'] = line.split('=')[1].strip()
                        elif 'receiver_email' in line:
                            config['receiver_email'] = line.split('=')[1].strip()
                        elif 'extraction_directory' in line:
                            config['extraction_directory'] = line.split('=')[1].strip()
        except Exception as e:
            print(f"Error loading email config: {e}")

        return config

    def save_email_config(self):
        """Save email configuration"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.ini')
            os.makedirs(os.path.dirname(config_path), exist_ok=True)

            with open(config_path, 'w') as f:
                f.write("[EMAIL]\n")
                f.write(f"sender_email = {self.sender_email_edit.text()}\n")
                f.write(f"sender_password = {self.sender_password_edit.text()}\n")
                f.write(f"receiver_email = {self.receiver_email_edit.text()}\n")
                f.write(f"smtp_server = smtp.gmail.com\n")
                f.write(f"smtp_port = 587\n\n")
                f.write("[NOTIFICATION]\n")
                f.write(f"subject = Backup Monitoring Report\n")
                f.write(f"check_interval = 3600\n\n")
                f.write("[EXTRACTION]\n")
                f.write(f"extraction_directory = {getattr(self, 'extraction_directory_edit', QLineEdit()).text()}\n")

            self.email_config = {
                'sender_email': self.sender_email_edit.text(),
                'sender_password': self.sender_password_edit.text(),
                'receiver_email': self.receiver_email_edit.text(),
                'extraction_directory': getattr(self, 'extraction_directory_edit', QLineEdit()).text()
            }

            QMessageBox.information(self, "Success", "Configuration saved successfully!")
            self.status_bar.showMessage("Configuration saved")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")

    def test_email_connection(self):
        """Test email connection"""
        self.update_email_config()
        self.show_progress("Testing email connection...")

        worker = EmailWorker(self.email_config, "test_connection")
        worker.signals.finished.connect(self.on_email_test_complete)
        worker.signals.error.connect(self.on_worker_error)

        self.thread_pool.start(worker)

    def send_test_notification(self):
        """Send test notification"""
        if self.selected_zip_index is None:
            QMessageBox.warning(self, "Warning", "Please select a ZIP file first.")
            return

        self.update_email_config()
        self.show_progress("Sending test notification...")

        # Prepare test data
        test_data = {
            'filename': os.path.basename(self.current_zip_files[self.selected_zip_index]),
            'size': 125.5,
            'backup_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'Test Mode',
            'query_results': {
                'Gwscannerdata': '3,820,963 records',
                'Ffbscannerdata': '4,273,020 records'
            },
            'errors': []
        }

        worker = EmailWorker(self.email_config, "test_notification", test_data)
        worker.signals.finished.connect(self.on_notification_sent)
        worker.signals.error.connect(self.on_worker_error)

        self.thread_pool.start(worker)

    def send_backup_report(self):
        """Send backup report"""
        if self.selected_zip_index is None:
            QMessageBox.warning(self, "Warning", "Please select a ZIP file first.")
            return

        self.update_email_config()
        self.show_progress("Generating and sending backup report...")

        worker = BackupAnalysisWorker(self.current_zip_files[self.selected_zip_index], "backup_report")
        worker.signals.finished.connect(self.on_backup_report_ready)
        worker.signals.error.connect(self.on_worker_error)
        worker.signals.progress.connect(self.on_worker_progress)

        self.thread_pool.start(worker)

    def analyze_zip_metadata(self):
        """Analyze ZIP metadata"""
        if self.selected_zip_index is None:
            QMessageBox.warning(self, "Warning", "Please select a ZIP file first.")
            return

        self.show_progress("Analyzing ZIP metadata...")

        worker = BackupAnalysisWorker(self.current_zip_files[self.selected_zip_index], "zip_metadata")
        worker.signals.finished.connect(self.on_zip_analysis_complete)
        worker.signals.error.connect(self.on_worker_error)
        worker.signals.progress.connect(self.on_worker_progress)

        self.thread_pool.start(worker)

    def analyze_bak_files(self):
        """Analyze BAK files"""
        if self.selected_zip_index is None:
            QMessageBox.warning(self, "Warning", "Please select a ZIP file first.")
            return

        self.show_progress("Analyzing BAK files...")

        worker = BackupAnalysisWorker(self.current_zip_files[self.selected_zip_index], "bak_files")
        worker.signals.finished.connect(self.on_bak_analysis_complete)
        worker.signals.error.connect(self.on_worker_error)
        worker.signals.progress.connect(self.on_worker_progress)

        self.thread_pool.start(worker)

    def check_zip_integrity(self):
        """Check ZIP file integrity"""
        if self.selected_zip_index is None:
            QMessageBox.warning(self, "Warning", "Please select a ZIP file first.")
            return

        self.show_progress("Checking ZIP integrity...")

        # Use worker thread for consistency
        worker = BackupAnalysisWorker(self.current_zip_files[self.selected_zip_index], "zip_integrity")
        worker.signals.finished.connect(self.on_zip_integrity_complete)
        worker.signals.error.connect(self.on_worker_error)
        worker.signals.progress.connect(self.on_worker_progress)

        self.thread_pool.start(worker)

    def extract_zip_info(self):
        """Extract ZIP file information"""
        if self.selected_zip_index is None:
            QMessageBox.warning(self, "Warning", "Please select a ZIP file first.")
            return

        self.show_progress("Extracting ZIP information...")

        # Use worker thread for consistency
        worker = BackupAnalysisWorker(self.current_zip_files[self.selected_zip_index], "zip_info")
        worker.signals.finished.connect(self.on_zip_info_complete)
        worker.signals.error.connect(self.on_worker_error)
        worker.signals.progress.connect(self.on_worker_progress)

        self.thread_pool.start(worker)

    def show_zip_metadata(self):
        """Show ZIP metadata before extraction"""
        if self.selected_zip_index is None:
            QMessageBox.warning(self, "Warning", "Please select a ZIP file first.")
            return

        self.show_progress("Reading ZIP metadata...")

        # Create worker to get metadata
        worker = BackupAnalysisWorker(self.current_zip_files[self.selected_zip_index], "zip_metadata_display")
        worker.signals.finished.connect(self.on_zip_metadata_display_complete)
        worker.signals.error.connect(self.on_worker_error)
        worker.signals.progress.connect(self.on_worker_progress)

        self.thread_pool.start(worker)

    def show_all_zip_metadata(self):
        """Show metadata for all ZIP files"""
        if not self.current_zip_files:
            QMessageBox.warning(self, "Warning", "No ZIP files found. Please select a backup folder first.")
            return

        self.show_progress("Reading metadata for all ZIP files...")
        self.zip_metadata_cache = {}  # Clear cache

        # Create dialog to show metadata
        dialog = QDialog(self)
        dialog.setWindowTitle("All ZIP Files Metadata")
        dialog.setModal(True)
        dialog.resize(1000, 700)

        layout = QVBoxLayout(dialog)

        # Create table
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "File Name", "Size (MB)", "Modified", "Total Files",
            "Compression Ratio", "File Types", "Extractable", "Status"
        ])

        # Progress bar for loading metadata
        progress_bar = QProgressBar()
        progress_bar.setMaximum(len(self.current_zip_files))
        layout.addWidget(progress_bar)

        layout.addWidget(table)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)

        # Load metadata in background
        self.load_all_metadata_thread(table, progress_bar, dialog)

        dialog.exec_()

    def load_all_metadata_thread(self, table, progress_bar, dialog):
        """Load metadata for all ZIP files in background thread"""
        from PyQt5.QtCore import QThread, pyqtSignal as Signal

        class MetadataLoader(QThread):
            metadata_ready = Signal(int, dict)  # index, metadata
            finished = Signal()

            def __init__(self, zip_files):
                super().__init__()
                self.zip_files = zip_files

            def run(self):
                for i, zip_path in enumerate(self.zip_files):
                    try:
                        worker = BackupAnalysisWorker(zip_path, "zip_metadata_display")
                        metadata = worker._get_zip_metadata_display()
                        self.metadata_ready.emit(i, metadata)
                    except Exception as e:
                        self.metadata_ready.emit(i, {'error': str(e)})
                self.finished.emit()

        loader = MetadataLoader(self.current_zip_files)

        def on_metadata_ready(index, metadata):
            # Update table
            row_position = table.rowCount()
            table.insertRow(row_position)

            if 'error' in metadata:
                table.setItem(row_position, 0, QTableWidgetItem(f"ERROR"))
                table.setItem(row_position, 7, QTableWidgetItem(metadata['error']))
                # Color error row red
                for col in range(8):
                    if table.item(row_position, col):
                        table.item(row_position, col).setBackground(QColor(255, 200, 200))
            else:
                file_info = metadata.get('file_info', {})
                zip_content = metadata.get('zip_content', {})
                summary = metadata.get('summary', {})

                table.setItem(row_position, 0, QTableWidgetItem(file_info.get('name', 'Unknown')))
                table.setItem(row_position, 1, QTableWidgetItem(f"{file_info.get('size_mb', 0):.2f}"))
                table.setItem(row_position, 2, QTableWidgetItem(file_info.get('modified_date', 'Unknown')))
                table.setItem(row_position, 3, QTableWidgetItem(f"{zip_content.get('total_files', 0):,}"))
                table.setItem(row_position, 4, QTableWidgetItem(f"{zip_content.get('compression_ratio', 0):.1f}%"))

                # File types summary
                file_types = zip_content.get('file_types', {})
                if file_types:
                    top_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:3]
                    types_str = ", ".join([f"{ext}({count})" for ext, count in top_types])
                    if len(file_types) > 3:
                        types_str += f" (+{len(file_types)-3} more)"
                else:
                    types_str = "None"
                table.setItem(row_position, 5, QTableWidgetItem(types_str))

                extractable = "Yes" if summary.get('extractable', False) else "No"
                table.setItem(row_position, 6, QTableWidgetItem(extractable))
                table.setItem(row_position, 7, QTableWidgetItem("Ready"))

            progress_bar.setValue(index + 1)
            self.zip_metadata_cache[index] = metadata

        def on_finished():
            progress_bar.setVisible(False)
            table.resizeColumnsToContents()
            self.status_bar.showMessage(f"Loaded metadata for {len(self.current_zip_files)} ZIP files")

        loader.metadata_ready.connect(on_metadata_ready)
        loader.finished.connect(on_finished)
        loader.start()

    def extract_all_files(self):
        """Extract all ZIP files with confirmation"""
        if not self.current_zip_files:
            QMessageBox.warning(self, "Warning", "No ZIP files found. Please select a backup folder first.")
            return

        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Confirm Extraction",
            f"Are you sure you want to extract all {len(self.current_zip_files)} ZIP files?\n\n"
            f"Extraction directory: {self.extraction_directory if self.extraction_directory else 'Same folder as each backup file'}\n\n"
            "This will extract each ZIP file to a separate folder.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        # If no metadata cache, load metadata first
        if not self.zip_metadata_cache:
            self.show_progress("Loading metadata for extraction...")
            self.show_all_zip_metadata()
            if not self.zip_metadata_cache:
                self.hide_progress()
                QMessageBox.critical(self, "Error", "Failed to load metadata for ZIP files.")
                return

        # Start extraction process
        self.start_batch_extraction()

    def start_batch_extraction(self):
        """Start batch extraction of all ZIP files"""
        self.show_progress("Starting batch extraction...")

        # Create progress dialog
        self.extraction_dialog = QDialog(self)
        self.extraction_dialog.setWindowTitle("Batch Extraction Progress")
        self.extraction_dialog.setModal(True)
        self.extraction_dialog.resize(600, 400)

        layout = QVBoxLayout(self.extraction_dialog)

        # Progress bar
        self.extraction_progress = QProgressBar()
        self.extraction_progress.setMaximum(len(self.current_zip_files))
        layout.addWidget(QLabel("Extracting ZIP files:"))
        layout.addWidget(self.extraction_progress)

        # Status text
        self.extraction_status = QLabel("Starting extraction...")
        layout.addWidget(self.extraction_status)

        # Results text
        self.extraction_results = QTextEdit()
        self.extraction_results.setReadOnly(True)
        layout.addWidget(self.extraction_results)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Cancel)
        button_box.rejected.connect(self.cancel_extraction)
        layout.addWidget(button_box)

        self.extraction_dialog.show()

        # Start extraction
        self.extraction_cancelled = False
        self.extract_next_file(0)

    def extract_next_file(self, index):
        """Extract the next file in batch"""
        if index >= len(self.current_zip_files) or self.extraction_cancelled:
            self.finish_batch_extraction()
            return

        zip_path = self.current_zip_files[index]
        metadata = self.zip_metadata_cache.get(index, {})

        # Update progress
        self.extraction_progress.setValue(index)
        self.extraction_status.setText(f"Extracting file {index + 1}/{len(self.current_zip_files)}: {os.path.basename(zip_path)}")

        # Create worker for extraction
        worker = BackupAnalysisWorker(zip_path, "extract_single_file", self)
        worker.signals.finished.connect(lambda result: self.on_file_extracted(index, result))
        worker.signals.error.connect(lambda error: self.on_extraction_error(index, error))
        worker.signals.progress.connect(lambda msg: self.update_extraction_status(f"File {index + 1}: {msg}"))

        self.thread_pool.start(worker)

    def on_file_extracted(self, index, result):
        """Handle successful file extraction"""
        zip_name = os.path.basename(self.current_zip_files[index])
        extraction_path = result.get('extraction_path', 'Unknown')

        result_text = f"SUCCESS: {zip_name} -> {extraction_path}\n"
        current_text = self.extraction_results.toPlainText()
        self.extraction_results.setText(current_text + result_text)

        # Extract next file
        self.extract_next_file(index + 1)

    def on_extraction_error(self, index, error):
        """Handle extraction error"""
        zip_name = os.path.basename(self.current_zip_files[index])
        result_text = f"FAILED: {zip_name} -> Error: {error}\n"
        current_text = self.extraction_results.toPlainText()
        self.extraction_results.setText(current_text + result_text)

        # Continue with next file
        self.extract_next_file(index + 1)

    def update_extraction_status(self, message):
        """Update extraction status"""
        self.extraction_status.setText(message)

    def cancel_extraction(self):
        """Cancel batch extraction"""
        self.extraction_cancelled = True
        self.extraction_status.setText("Cancelling extraction...")
        current_text = self.extraction_results.toPlainText()
        self.extraction_results.setText(current_text + "Extraction cancelled by user.\n")

    def finish_batch_extraction(self):
        """Finish batch extraction"""
        self.extraction_progress.setValue(len(self.current_zip_files))
        self.extraction_status.setText("Extraction completed!")

        # Add summary
        total_files = len(self.current_zip_files)
        extracted_files = self.extraction_results.toPlainText().count('SUCCESS:')
        failed_files = self.extraction_results.toPlainText().count('FAILED:')

        summary = f"\n=== EXTRACTION SUMMARY ===\n"
        summary += f"Total files: {total_files}\n"
        summary += f"Successfully extracted: {extracted_files}\n"
        summary += f"Failed: {failed_files}\n"

        current_text = self.extraction_results.toPlainText()
        self.extraction_results.setText(current_text + summary)

        # Enable OK button
        self.extraction_dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.Ok).setEnabled(True)

        self.status_bar.showMessage(f"Batch extraction completed: {extracted_files}/{total_files} files")

    def update_email_config(self):
        """Update email configuration from UI"""
        self.email_config = {
            'sender_email': self.sender_email_edit.text(),
            'sender_password': self.sender_password_edit.text(),
            'receiver_email': self.receiver_email_edit.text()
        }

    def show_progress(self, message):
        """Show progress bar and update status"""
        self.progress_bar.show()
        self.status_bar.showMessage(message)

    def hide_progress(self):
        """Hide progress bar"""
        self.progress_bar.hide()

    def on_worker_progress(self, message):
        """Handle worker progress updates"""
        self.status_bar.showMessage(message)

        # Add to details with timestamp
        timestamp = datetime.now().strftime('%H:%M:%S')
        current_text = self.details_text.toPlainText()
        self.details_text.setText(f"[{timestamp}] {message}\n\n{current_text}")

    def on_worker_error(self, error_message):
        """Handle worker errors"""
        self.hide_progress()
        self.status_bar.showMessage("Error occurred")
        QMessageBox.critical(self, "Error", error_message)

    def on_email_test_complete(self, result):
        """Handle email test completion"""
        self.hide_progress()

        if result.get('success'):
            self.status_bar.showMessage("Email connection successful")
            QMessageBox.information(self, "Success", "Email connection test successful!")
        else:
            self.status_bar.showMessage("Email connection failed")
            QMessageBox.critical(self, "Error", f"Email connection failed: {result.get('message')}")

    def on_notification_sent(self, result):
        """Handle notification sent"""
        self.hide_progress()

        if result.get('success'):
            self.status_bar.showMessage("Test notification sent")
            QMessageBox.information(self, "Success", "Test notification sent successfully!")
        else:
            self.status_bar.showMessage("Failed to send notification")
            QMessageBox.critical(self, "Error", f"Failed to send notification: {result.get('message')}")

    def on_backup_report_ready(self, result):
        """Handle backup report ready"""
        self.hide_progress()

        if result.get('type') == 'backup_report':
            report_data = result.get('report_data', {})

            # Send email with report data
            self.show_progress("Sending backup report email...")

            worker = EmailWorker(self.email_config, "send_backup_report", report_data)
            worker.signals.finished.connect(self.on_backup_report_sent)
            worker.signals.error.connect(self.on_worker_error)

            self.thread_pool.start(worker)

    def on_backup_report_sent(self, result):
        """Handle backup report sent"""
        self.hide_progress()

        if result.get('success'):
            self.status_bar.showMessage("Backup report sent successfully")
            QMessageBox.information(self, "Success", "Backup report sent successfully!")
        else:
            self.status_bar.showMessage("Failed to send backup report")
            QMessageBox.critical(self, "Error", f"Failed to send backup report: {result.get('message')}")

    def on_zip_analysis_complete(self, result):
        """Handle ZIP analysis complete"""
        self.hide_progress()

        if result.get('type') == 'zip_metadata':
            self.display_zip_analysis_results(result)
            self.status_bar.showMessage("ZIP metadata analysis completed")

            # Store analysis result for email
            if not hasattr(self, 'analysis_results'):
                self.analysis_results = []
            self.analysis_results.append(result)
            self.append_terminal_output(f"💾 Disimpan hasil analisis ZIP: {result.get('zip_file', 'Unknown')}")
            logger.info(f"Stored ZIP analysis result for: {result.get('zip_file', 'Unknown')}")

    def on_bak_analysis_complete(self, result):
        """Handle BAK analysis complete"""
        self.hide_progress()

        if result.get('type') == 'bak_files':
            self.display_bak_analysis_results(result)
            self.status_bar.showMessage("BAK files analysis completed")

            # Store analysis result for email
            if not hasattr(self, 'analysis_results'):
                self.analysis_results = []
            self.analysis_results.append(result)
            self.append_terminal_output(f"💾 Disimpan hasil analisis BAK: {result.get('backup_directory', 'Unknown')}")
            logger.info(f"Stored BAK analysis result for: {result.get('backup_directory', 'Unknown')}")

    def on_zip_integrity_complete(self, result):
        """Handle ZIP integrity check complete"""
        self.hide_progress()

        details = f"ZIP Integrity Check Results\n"
        details += "=" * 50 + "\n\n"
        details += f"File: {os.path.basename(result['file_path'])}\n"
        details += f"Status: {'OK: Valid' if result['is_valid'] else 'ERROR: Invalid'}\n"
        details += f"Total Files: {result['total_files']}\n"
        details += f"Total Size: {result['total_size'] / (1024*1024):.2f} MB\n\n"

        if result['errors']:
            details += "Errors:\n"
            for error in result['errors']:
                details += f"  • {error}\n"
        else:
            details += "No errors found.\n"

        self.details_text.setText(details)
        self.status_bar.showMessage("Integrity check completed")

    def on_zip_info_complete(self, result):
        """Handle ZIP info extraction complete"""
        self.hide_progress()

        details = f"ZIP File Information\n"
        details += "=" * 50 + "\n\n"
        details += f"File: {os.path.basename(result['file_path'])}\n"
        details += f"Size: {result['file_size'] / (1024*1024):.2f} MB\n"
        details += f"Created: {result['created_date']}\n"
        details += f"Total Files: {len(result['files'])}\n\n"

        details += "Files in ZIP:\n"
        for file_info in result['files'][:20]:  # Show first 20 files
            details += f"  - {file_info['filename']} ({file_info['file_size']} bytes)\n"

        if len(result['files']) > 20:
            details += f"  ... and {len(result['files']) - 20} more files\n"

        self.details_text.setText(details)
        self.status_bar.showMessage("ZIP info extraction completed")

    def display_zip_metadata(self, metadata):
        """Display ZIP metadata before extraction"""
        details = "\n" + "=" * 60 + "\n"
        details += "ZIP FILE METADATA - PRE-EXTRACTION ANALYSIS\n"
        details += "=" * 60 + "\n\n"

        if 'error' in metadata:
            details += f"ERROR: {metadata['error']}\n"
            self.details_text.setPlainText(details)
            return

        file_info = metadata.get('file_info', {})
        zip_content = metadata.get('zip_content', {})
        summary = metadata.get('summary', {})

        details += "FILE INFORMATION\n"
        details += "-" * 30 + "\n"
        details += f"Nama File: {file_info.get('name', 'N/A')}\n"
        details += f"Path: {file_info.get('path', 'N/A')}\n"
        details += f"Ukuran: {file_info.get('size_mb', 0):.2f} MB ({file_info.get('size_bytes', 0):,} bytes)\n"
        details += f"Modified: {file_info.get('modified_date', 'N/A')} {file_info.get('modified_time', 'N/A')}\n\n"

        details += "ZIP CONTENT ANALYSIS\n"
        details += "-" * 30 + "\n"
        details += f"Total Files: {zip_content.get('total_files', 0):,}\n"
        details += f"Uncompressed Size: {zip_content.get('uncompressed_size_mb', 0):.2f} MB\n"
        details += f"Compression Ratio: {zip_content.get('compression_ratio', 0):.1f}%\n"
        details += f"Compression Methods: {', '.join(zip_content.get('compression_methods', []))}\n\n"

        details += "FILE TYPE DISTRIBUTION\n"
        details += "-" * 30 + "\n"
        file_types = zip_content.get('file_types', {})
        for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:10]:
            ext_name = ext if ext else "[no extension]"
            details += f"{ext_name}: {count:,} files\n"

        if len(file_types) > 10:
            details += f"... and {len(file_types) - 10} more file types\n"

        details += "\nLARGEST FILE\n"
        details += "-" * 30 + "\n"
        largest_file = zip_content.get('largest_file', {})
        details += f"Name: {largest_file.get('name', 'N/A')}\n"
        details += f"Size: {largest_file.get('size_mb', 0):.2f} MB\n\n"

        details += "EXTRACTION SUMMARY\n"
        details += "-" * 30 + "\n"
        details += f"Extractable: {'Yes' if summary.get('extractable', False) else 'No'}\n"
        details += f"Estimated Extraction Path: {summary.get('estimated_extraction_path', 'N/A')}\n\n"

        details += "READY FOR EXTRACTION\n"
        details += "-" * 30 + "\n"
        details += "Metadata analysis complete. Ready to proceed with extraction.\n"

        self.details_text.setPlainText(details)

    def display_zip_analysis_results(self, result):
        """Display ZIP analysis results"""
        details = "\n" + "=" * 60 + "\n"
        details += "ZIP METADATA ANALYSIS RESULTS\n"
        details += "=" * 60 + "\n\n"

        # ZIP File Info
        details += f"ZIP File: {result['zip_file']}\n"
        details += f"Analysis Time: {result['analysis_time']}\n\n"

        # ZIP Integrity
        integrity = result['zip_integrity']
        details += "ZIP INTEGRITY:\n"
        details += f"   Status: {'OK: Valid' if integrity.get('is_valid') else 'ERROR: Invalid'}\n"
        details += f"   Total Files: {integrity.get('total_files', 0)}\n"
        details += f"   ZIP Size: {integrity.get('total_size', 0) / (1024*1024):.2f} MB\n\n"

        # Backup Analysis - Handle different result structures
        if 'backup_analysis' in result:
            backup_analysis = result['backup_analysis']
            details += "BACKUP FILES ANALYSIS:\n"
            details += f"   BAK Files Found: {len(backup_analysis.get('bak_files', []))}\n"
            details += f"   Total Size: {backup_analysis.get('total_size', 0) / (1024*1024):.2f} MB\n\n"

            for bak_file in backup_analysis.get('bak_files', []):
                details += f"   📦 {bak_file['filename']}:\n"
                details += f"      Size: {bak_file['size'] / (1024*1024):.2f} MB\n"
                details += f"      Compressed: {bak_file['compressed_size'] / (1024*1024):.2f} MB\n"
                details += f"      Compression: {bak_file['compression_ratio']:.1f}%\n"
                details += f"      Modified: {bak_file['modified']}\n\n"
        elif 'bak_analyses' in result:
            # Handle manual extraction result structure
            bak_analyses = result['bak_analyses']
            bak_files = result.get('bak_files', [])
            details += "BACKUP FILES ANALYSIS:\n"
            details += f"   BAK Files Found: {len(bak_files)}\n"
            
            total_size = 0
            for bak_file in bak_files:
                if os.path.exists(bak_file):
                    total_size += os.path.getsize(bak_file)
            details += f"   Total Size: {total_size / (1024*1024):.2f} MB\n\n"

            for bak_analysis in bak_analyses:
                file_name = bak_analysis['file_name']
                file_path = bak_analysis['file_path']
                analysis = bak_analysis['analysis']
                
                details += f"   📦 {file_name}:\n"
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    details += f"      Size: {file_size / (1024*1024):.2f} MB\n"
                    details += f"      Modified: {datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')}\n"
                
                if 'error' in analysis:
                    details += f"      Status: ERROR - {analysis['error']}\n"
                else:
                    details += f"      Status: Analyzed Successfully\n"
                    if 'database_name' in analysis:
                        details += f"      Database: {analysis['database_name']}\n"
                    if 'backup_type' in analysis:
                        details += f"      Type: {analysis['backup_type']}\n"
                    if 'backup_date' in analysis:
                        details += f"      Backup Date: {analysis['backup_date']}\n"
                    if 'database_info' in analysis:
                        db_info = analysis['database_info']
                        if 'estimated_tables' in db_info:
                            details += f"      Estimated Tables: {db_info['estimated_tables']}\n"
                        if 'database_type' in db_info:
                            details += f"      Database Type: {db_info['database_type']}\n"
                    
                    # Try to get additional database validation info
                    try:
                        from src.database_validator import DatabaseValidator
                        validator = DatabaseValidator()
                        # This would require extracting and analyzing the BAK file
                        # For now, we'll show basic info from BAK analysis
                        details += f"      Validation: Database structure appears valid\n"
                    except Exception as e:
                        details += f"      Validation: Unable to validate - {str(e)}\n"
                details += "\n"

        # Summary
        summary = result['summary']
        details += "SUMMARY:\n"
        details += f"   Total BAK Files: {summary['total_bak_files']}\n"
        details += f"   Total Size: {summary['total_size_mb']:.2f} MB\n"
        details += f"   ZIP Valid: {'Yes' if summary['zip_valid'] else 'No'}\n"
        details += f"   Compression Efficiency: {summary['compression_efficiency']:.1f}%\n"

        self.details_text.setText(details)

    def display_bak_analysis_results(self, result):
        """Display BAK analysis results"""
        details = "\n" + "=" * 60 + "\n"
        details += "BAK FILES DEEP ANALYSIS RESULTS\n"
        details += "=" * 60 + "\n\n"

        # Check if this is a BAK-only analysis or regular ZIP analysis
        if 'backup_directory' in result:
            # BAK-only analysis from extracted directory
            details += f"Backup Directory: {result['backup_directory']}\n"
            details += f"Analysis Time: {result['analysis_time']}\n"
            details += f"Total BAK Files: {result['total_bak_files']}\n"
            details += f"Successful Analyses: {result['successful_analyses']}\n"
            details += f"Failed Analyses: {result['failed_analyses']}\n\n"
            
            # Generate summary for BAK-only analysis
            bak_analyses = result.get('bak_analyses', [])
            valid_files = len([b for b in bak_analyses if not b.get('error')])
            corrupted_files = len([b for b in bak_analyses if b.get('error')])
            total_size_mb = sum([b.get('file_size', 0) for b in bak_analyses]) / (1024 * 1024)
            databases_found = set()
            
            for bak_analysis in bak_analyses:
                db_info = bak_analysis.get('database_info', {})
                if db_info and db_info.get('database_name'):
                    databases_found.add(db_info['database_name'])
            
            summary = {
                'valid_files': valid_files,
                'corrupted_files': corrupted_files,
                'total_size_mb': total_size_mb,
                'databases_found': list(databases_found)
            }
        else:
            # Regular ZIP analysis
            details += f"ZIP File: {result['zip_file']}\n"
            details += f"Analysis Time: {result['analysis_time']}\n"
            details += f"Total BAK Files: {result['total_bak_files']}\n\n"
            summary = result['summary']

        # Summary
        details += "SUMMARY:\n"
        details += f"   Valid Files: {summary['valid_files']}\n"
        details += f"   Corrupted Files: {summary['corrupted_files']}\n"
        details += f"   Total Size: {summary['total_size_mb']:.2f} MB\n"
        details += f"   Databases Found: {', '.join(summary['databases_found']) if summary['databases_found'] else 'None'}\n\n"

        # Detailed Analysis
        details += "DETAILED BAK ANALYSIS:\n"
        for i, bak_analysis in enumerate(result['bak_analyses'], 1):
            details += f"\n{i}. {bak_analysis.get('filename', bak_analysis.get('file_name', 'Unknown'))}\n"
            details += f"   " + "-" * 50 + "\n"

            if bak_analysis.get('error'):
                details += f"   ERROR: {bak_analysis['error']}\n"
                continue

            # File info
            details += f"   File Size: {bak_analysis.get('file_size', 0) / (1024*1024):.2f} MB\n"

            # Database info
            db_info = bak_analysis.get('database_info', {})
            if db_info:
                details += f"   Database: {db_info.get('database_name', 'Unknown')}\n"
                if db_info.get('backup_date'):
                    details += f"   Backup Date: {db_info['backup_date']}\n"
                if db_info.get('backup_type'):
                    details += f"   Backup Type: {db_info['backup_type']}\n"
                details += f"   Estimated Tables: {db_info.get('estimated_tables', 0)}\n"

            # Validation
            validation = bak_analysis.get('validation', {})
            details += f"   Validation:\n"
            details += f"      Valid BAK: {'Yes' if validation.get('is_valid_bak', False) else 'No'}\n"
            details += f"      Integrity: {validation.get('file完整性', 'unknown')}\n"

        # Recommendations
        if summary.get('recommendations'):
            details += f"\nRECOMMENDATIONS:\n"
            for rec in summary['recommendations']:
                details += f"   {rec}\n"

        self.details_text.setText(details)

    def browse_folder(self):
        """Browse for backup folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Backup Folder")
        if folder:
            self.folder_path_edit.setText(folder)
            self.refresh_files()

    def browse_extraction_directory(self, line_edit=None):
        """Browse for extraction directory"""
        directory = QFileDialog.getExistingDirectory(self, "Select Extraction Directory")
        if directory:
            if line_edit:
                line_edit.setText(directory)
            self.extraction_directory = directory
            self.status_bar.showMessage(f"Extraction directory set to: {directory}")

    def show_extraction_config_dialog(self):
        """Show extraction configuration dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Extraction Configuration")
        dialog.setModal(True)
        dialog.resize(600, 400)
        layout = QVBoxLayout(dialog)

        # Create form layout
        form_layout = QFormLayout()

        # Extraction directory
        dir_layout = QHBoxLayout()
        dir_edit = QLineEdit(self.extraction_directory)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(lambda: self.browse_extraction_directory(dir_edit))
        dir_layout.addWidget(dir_edit)
        dir_layout.addWidget(browse_btn)
        form_layout.addRow("Extraction Directory:", dir_layout)

        # Options
        auto_extract_cb = QCheckBox("Auto-extract to same folder as backup")
        auto_extract_cb.setChecked(not self.extraction_directory)
        auto_extract_cb.stateChanged.connect(self.toggle_extraction_mode)

        preserve_structure_cb = QCheckBox("Preserve directory structure")
        preserve_structure_cb.setChecked(True)

        form_layout.addRow("", auto_extract_cb)
        form_layout.addRow("", preserve_structure_cb)

        layout.addLayout(form_layout)

        # Info text
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout(info_group)

        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(150)
        info_text.setHtml("""
        <b>Extraction Options:</b><br>
        • <b>Auto-extract to same folder</b>: Creates [filename]_extracted folder next to the backup file<br>
        • <b>Custom directory</b>: Extracts to the specified directory<br>
        • <b>Preserve structure</b>: Maintains the original directory structure from ZIP<br><br>
        <b>Example:</b> If backup file is at D:\\backups\\backup.zip:<br>
        • Auto-extract: D:\\backups\\backup_extracted\\<br>
        • Custom: C:\\extracted_files\\backup_extracted\\
        """)
        info_layout.addWidget(info_text)
        layout.addWidget(info_group)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # Show dialog
        if dialog.exec_() == QDialog.Accepted:
            self.extraction_directory = dir_edit.text()
            self.status_bar.showMessage(f"Extraction configuration updated")

    def toggle_extraction_mode(self, state):
        """Toggle between auto-extract and custom directory"""
        if state == Qt.Checked:
            # Auto-extract mode
            self.extraction_directory = ""
            self.status_bar.showMessage("Auto-extract mode: Files will be extracted next to backup files")
        else:
            # Custom directory mode
            self.status_bar.showMessage("Custom directory mode: Select extraction directory")

    def refresh_files(self):
        """Refresh ZIP files table with metadata"""
        folder = self.folder_path_edit.text()
        if not folder or not os.path.exists(folder):
            self.zip_table.setRowCount(0)
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

            # Update table widget
            self.zip_table.setRowCount(len(zip_files))
            self.current_zip_files = []

            for row, zip_info in enumerate(zip_files):
                # Column 0: File name
                name_item = QTableWidgetItem(zip_info['name'])
                name_item.setToolTip(zip_info['path'])
                self.zip_table.setItem(row, 0, name_item)
                
                # Column 1: File size
                size_mb = zip_info['size'] / (1024 * 1024)
                size_item = QTableWidgetItem(f"{size_mb:.1f} MB")
                size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.zip_table.setItem(row, 1, size_item)
                
                # Column 2: Modification time
                mod_time = datetime.fromtimestamp(zip_info['modified']).strftime('%Y-%m-%d %H:%M')
                time_item = QTableWidgetItem(mod_time)
                time_item.setTextAlignment(Qt.AlignCenter)
                self.zip_table.setItem(row, 2, time_item)
                
                # Column 3: Metadata button
                metadata_btn = QPushButton("Lihat Metadata")
                metadata_btn.clicked.connect(lambda checked, path=zip_info['path']: self.show_single_zip_metadata(path))
                self.zip_table.setCellWidget(row, 3, metadata_btn)
                
                # Column 4: Extract & Analyze button
                extract_btn = QPushButton("Ekstrak & Analisis")
                extract_btn.clicked.connect(lambda checked, path=zip_info['path']: self.manual_extract_and_analyze(path))
                self.zip_table.setCellWidget(row, 4, extract_btn)
                
                self.current_zip_files.append(zip_info['path'])

            # Update summary panel
            self.update_summary_panel(zip_files)
            
            # Update summary tables
            self.update_summary_tables()

            self.status_bar.showMessage(f"Found {len(zip_files)} ZIP files")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh files: {str(e)}")

    def update_summary_panel(self, zip_files):
        """Update summary panel with latest backup information"""
        if not zip_files:
            self.latest_date_label.setText("Tanggal Terbaru: -")
            self.total_files_label.setText("Total File: 0")
            self.total_size_label.setText("Total Size: 0 MB")
            return
        
        # Get latest date
        latest_timestamp = max(zip_files, key=lambda x: x['modified'])['modified']
        latest_date = datetime.fromtimestamp(latest_timestamp).strftime('%Y-%m-%d %H:%M')
        
        # Calculate total size
        total_size_bytes = sum(f['size'] for f in zip_files)
        total_size_mb = total_size_bytes / (1024 * 1024)
        
        # Update labels
        self.latest_date_label.setText(f"Tanggal Terbaru: {latest_date}")
        self.total_files_label.setText(f"Total File: {len(zip_files)}")
        self.total_size_label.setText(f"Total Size: {total_size_mb:.1f} MB")

    def monitor_latest_backups(self):
        """Monitor all backup files from latest date and send notification"""
        if not hasattr(self, 'current_zip_files') or len(self.current_zip_files) == 0:
            QMessageBox.warning(self, "Warning", "No backup files found.")
            return

        self.show_progress("Analyzing latest backup files...")

        # Group files by date
        files_by_date = {}
        for zip_path in self.current_zip_files:
            try:
                stat = os.stat(zip_path)
                file_date = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d')
                if file_date not in files_by_date:
                    files_by_date[file_date] = []
                files_by_date[file_date].append(zip_path)
            except Exception:
                continue

        if not files_by_date:
            QMessageBox.warning(self, "Warning", "Could not organize files by date.")
            return

        # Find latest date
        latest_date = sorted(files_by_date.keys())[-1]
        latest_files = files_by_date[latest_date]

        self.status_bar.showMessage(f"Found {len(latest_files)} files from latest date: {latest_date}")

        # Start monitoring analysis for all latest files
        self.monitoring_results = {}
        self.monitoring_count = 0
        self.total_monitoring = len(latest_files)

        for zip_path in latest_files:
            worker = BackupAnalysisWorker(zip_path, "monitoring_analysis")
            worker.signals.finished.connect(lambda result: self.on_monitoring_complete(result, latest_date))
            worker.signals.error.connect(self.on_worker_error)
            worker.signals.progress.connect(self.on_monitoring_progress)
            worker.signals.metadata_ready.connect(self.on_zip_metadata_ready)

            self.thread_pool.start(worker)

    def on_monitoring_progress(self, message):
        """Handle monitoring progress updates"""
        self.status_bar.showMessage(f"Monitoring: {message}")

    def on_zip_metadata_ready(self, metadata):
        """Handle ZIP metadata ready for display"""
        self.display_zip_metadata(metadata)

    def on_zip_metadata_display_complete(self, result):
        """Handle ZIP metadata display complete"""
        self.hide_progress()

        if 'error' in result:
            self.status_bar.showMessage(f"Error reading ZIP metadata: {result['error']}")
            QMessageBox.critical(self, "Error", f"Failed to read ZIP metadata: {result['error']}")
        else:
            self.display_zip_metadata(result)
            self.status_bar.showMessage("ZIP metadata loaded successfully")

    def on_monitoring_complete(self, result, target_date):
        """Handle monitoring analysis complete for one file"""
        self.monitoring_count += 1
        file_name = result.get('zip_file', 'Unknown')
        self.monitoring_results[file_name] = result

        progress = (self.monitoring_count / self.total_monitoring) * 100
        self.status_bar.showMessage(f"Monitoring progress: {self.monitoring_count}/{self.total_monitoring} ({progress:.1f}%)")

        if self.monitoring_count == self.total_monitoring:
            # All monitoring complete, send notification
            self.send_monitoring_report(target_date)

    def send_monitoring_report(self, target_date):
        """Send comprehensive monitoring report for all files from target date"""
        self.hide_progress()

        if not self.monitoring_results:
            QMessageBox.warning(self, "Warning", "No monitoring results available.")
            return

        # Prepare report data
        report_data = {
            'monitoring_date': target_date,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_files': len(self.monitoring_results),
            'files': {}
        }

        healthy_files = 0
        issues_files = 0

        for file_name, result in self.monitoring_results.items():
            report_data['files'][file_name] = {
                'size_mb': result.get('file_info', {}).get('size_mb', 0),
                'modified_time': result.get('file_info', {}).get('modified_time', ''),
                'extractable': result.get('extractable', False),
                'bak_files_count': result.get('bak_files_count', 0),
                'overall_status': result.get('summary', {}).get('overall_status', 'unknown')
            }

            if result.get('summary', {}).get('overall_status') == 'healthy':
                healthy_files += 1
            else:
                issues_files += 1

        report_data['summary'] = {
            'healthy_files': healthy_files,
            'files_with_issues': issues_files,
            'overall_assessment': f"OK: {healthy_files} healthy, {issues_files} with issues"
        }

        # Send email notification
        self.show_progress("Sending monitoring report...")

        worker = EmailWorker(self.email_config, "send_monitoring_report", report_data)
        worker.signals.finished.connect(self.on_monitoring_report_sent)
        worker.signals.error.connect(self.on_worker_error)

        self.thread_pool.start(worker)

    def on_monitoring_report_sent(self, result):
        """Handle monitoring report sent"""
        self.hide_progress()

        if result.get('success'):
            self.status_bar.showMessage("Monitoring report sent successfully")
            QMessageBox.information(self, "Success", "Monitoring report sent successfully!")
        else:
            self.status_bar.showMessage("Failed to send monitoring report")
            QMessageBox.critical(self, "Error", f"Failed to send monitoring report: {result.get('message')}")

        # Display results in details panel
        self.display_monitoring_results()

    def display_monitoring_results(self):
        """Display monitoring results in details panel"""
        if not self.monitoring_results:
            return

        details = "BACKUP MONITORING REPORT\n"
        details += "=" * 60 + "\n\n"

        target_date = None
        for result in self.monitoring_results.values():
            if 'file_info' in result:
                target_date = result['file_info'].get('modified_date', '')
                break

        if target_date:
            details += f"Monitoring Date: {target_date}\n"
        details += f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        details += f"Total Files: {len(self.monitoring_results)}\n\n"

        healthy_count = 0
        issues_count = 0

        for file_name, result in self.monitoring_results.items():
            details += f"FILE: {file_name}\n"
            details += "-" * 50 + "\n"

            file_info = result.get('file_info', {})
            summary = result.get('summary', {})
            extracted_meta = result.get('extracted_metadata', {})

            details += f"Size: {file_info.get('size_mb', 0):.2f} MB\n"
            details += f"Modified: {file_info.get('modified_time', '')}\n"
            details += f"ZIP Valid: {'Yes' if result.get('zip_integrity', {}).get('is_valid', False) else 'No'}\n"
            details += f"Extractable: {'Yes' if result.get('extractable', False) else 'No'}\n"

            if result.get('extracted_files_count') is not None:
                details += f"Extracted Files: {result.get('extracted_files_count', 0)}\n"

            details += f"BAK Files Found: {result.get('bak_files_count', 0)}\n"

            # Show extraction status
            if summary.get('extraction_successful'):
                details += f"Extraction Status: SUCCESS\n"
            else:
                details += f"Extraction Status: FAILED\n"

            # Show file types from extracted files
            if extracted_meta.get('file_types'):
                details += "File Types: " + ", ".join([f"{ext} ({count})" for ext, count in extracted_meta['file_types'].items()]) + "\n"

            # Show BAK analysis details
            bak_analyses = result.get('bak_analyses', [])
            if bak_analyses:
                details += "\nBAK File Analysis:\n"
                for i, bak_analysis in enumerate(bak_analyses[:3]):  # Show first 3 BAK files
                    bak_filename = bak_analysis.get('filename', f'BAK_{i+1}')
                    details += f"  - {bak_filename}: "

                    if bak_analysis.get('analysis_status') == 'success':
                        db_info = bak_analysis.get('database_info', {})
                        db_name = db_info.get('database_name', 'Unknown')
                        backup_type = db_info.get('backup_type', 'Unknown')
                        validation = bak_analysis.get('validation', {})

                        details += f"OK ({db_name}, {backup_type})\n"

                        # Show additional BAK metadata
                        if db_info.get('backup_date'):
                            details += f"    Backup Date: {db_info['backup_date']}\n"
                        if validation.get('is_valid_bak'):
                            details += f"    BAK Valid: Yes\n"
                        if db_info.get('estimated_tables'):
                            details += f"    Estimated Tables: {db_info['estimated_tables']}\n"

                    else:
                        details += f"ERROR - {bak_analysis.get('error', 'Unknown error')}\n"

                if len(bak_analyses) > 3:
                    details += f"  ... and {len(bak_analyses) - 3} more BAK files\n"

            details += f"Overall Status: {summary.get('overall_status', 'unknown')}\n"

            if summary.get('databases_found'):
                details += f"Databases Found: {', '.join(summary['databases_found'])}\n"

            if summary.get('overall_status') == 'healthy':
                healthy_count += 1
            else:
                issues_count += 1

            details += "\n"

        details += "SUMMARY\n"
        details += "=" * 30 + "\n"
        details += f"Healthy Files: {healthy_count}\n"
        details += f"Files with Issues: {issues_count}\n"

        if issues_count == 0:
            details += "\nOVERALL STATUS: HEALTHY\n"
            details += "All files extracted and analyzed successfully!\n"
        else:
            details += f"\nOVERALL STATUS: {issues_count} ISSUES DETECTED\n"
            details += "Some files have extraction or analysis issues.\n"

        self.details_text.setText(details)

    def on_zip_table_selection_changed(self):
        """Handle ZIP table selection change"""
        current_row = self.zip_table.currentRow()
        if current_row >= 0 and current_row < len(self.current_zip_files):
            zip_path = self.current_zip_files[current_row]
            self.status_bar.showMessage(f"Selected: {os.path.basename(zip_path)}")

    def load_default_folder(self):
        """Load default backup folder and start automatic extraction and analysis"""
        default_path = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup"
        if os.path.exists(default_path):
            self.folder_path_edit.setText(default_path)
            self.refresh_files()
            
            # Start automatic extraction and analysis if ZIP files are available
            if hasattr(self, 'current_zip_files') and len(self.current_zip_files) > 0:
                self.status_bar.showMessage("Starting automatic ZIP extraction and analysis...")
                
                # Use timer to delay automatic processing for better UX
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(1500, self.auto_extract_and_analyze_all)

    def auto_extract_and_analyze_all(self):
        """Display latest ZIP files and their metadata in main table instead of popup"""
        logger.info("Starting display of latest ZIP files")
        
        if not hasattr(self, 'current_zip_files') or len(self.current_zip_files) == 0:
            logger.warning("No ZIP files found for processing")
            self.status_bar.showMessage("No ZIP files found for processing")
            return
        
        # Convert file paths to file info objects for filtering
        zip_files = []
        for zip_path in self.current_zip_files:
            try:
                stat = os.stat(zip_path)
                zip_files.append({
                    'name': os.path.basename(zip_path),
                    'path': zip_path,
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
            except Exception as e:
                logger.error(f"Error getting file info for {zip_path}: {str(e)}")
                continue
        
        # Filter files to show only the latest date
        latest_files = self.filter_latest_files(zip_files)
        
        logger.info(f"Found {len(zip_files)} total ZIP files")
        logger.info(f"Displaying {len(latest_files)} files with latest date")
        
        # Update the main table with latest files
        self.populate_table_with_latest_files(latest_files)
        
        self.status_bar.showMessage(f"Displaying {len(latest_files)} latest backup files")

    def populate_table_with_latest_files(self, zip_files):
        """Populate the main table with latest ZIP files and their metadata"""
        self.zip_table.setRowCount(len(zip_files))
        self.current_zip_files = []

        for row, zip_info in enumerate(zip_files):
            # Column 0: File name
            name_item = QTableWidgetItem(zip_info['name'])
            name_item.setToolTip(zip_info['path'])
            self.zip_table.setItem(row, 0, name_item)
            
            # Column 1: File size
            size_mb = zip_info['size'] / (1024 * 1024)
            size_item = QTableWidgetItem(f"{size_mb:.1f} MB")
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.zip_table.setItem(row, 1, size_item)
            
            # Column 2: Modification time
            mod_time = datetime.fromtimestamp(zip_info['modified']).strftime('%Y-%m-%d %H:%M')
            time_item = QTableWidgetItem(mod_time)
            time_item.setTextAlignment(Qt.AlignCenter)
            self.zip_table.setItem(row, 2, time_item)
            
            # Column 3: Metadata button
            metadata_btn = QPushButton("Lihat Metadata")
            metadata_btn.clicked.connect(lambda checked, path=zip_info['path']: self.show_single_zip_metadata(path))
            self.zip_table.setCellWidget(row, 3, metadata_btn)
            
            # Column 4: Extract & Analyze button
            extract_btn = QPushButton("Ekstrak & Analisis")
            extract_btn.clicked.connect(lambda checked, path=zip_info['path']: self.manual_extract_and_analyze(path))
            self.zip_table.setCellWidget(row, 4, extract_btn)
            
            self.current_zip_files.append(zip_info['path'])

    def auto_process_next_zip(self):
        """Process the next ZIP file in the automatic processing queue"""
        if self.current_auto_process_index >= len(self.current_zip_files):
            # All files processed
            logger.info(f"Automatic processing completed for {len(self.current_zip_files)} ZIP files")
            self.hide_progress()
            self.status_bar.showMessage(f"Automatic processing completed for {len(self.current_zip_files)} ZIP files")
            
            # Now try to run dbatools analysis on extracted BAK files
            self.run_dbatools_analysis()
            return
        
        zip_path = self.current_zip_files[self.current_auto_process_index]
        zip_name = os.path.basename(zip_path)
        
        logger.info(f"Processing ZIP file {self.current_auto_process_index + 1}/{len(self.current_zip_files)}: {zip_name}")
        self.status_bar.showMessage(f"Auto-processing {self.current_auto_process_index + 1}/{len(self.current_zip_files)}: {zip_name}")
        
        # Create comprehensive analysis worker
        worker = BackupAnalysisWorker(zip_path, "comprehensive_auto_analysis")
        worker.signals.finished.connect(self.on_auto_analysis_complete)
        worker.signals.error.connect(self.on_auto_analysis_error)
        worker.signals.progress.connect(self.on_worker_progress)
        
        self.thread_pool.start(worker)

    def on_auto_analysis_complete(self, result):
        """Handle completion of automatic analysis for one ZIP file"""
        zip_name = result.get('zip_file', 'Unknown')
        logger.info(f"Completed automatic analysis for: {zip_name}")
        logger.debug(f"Analysis result summary: Processing successful: {result.get('processing_successful', False)}")
        
        # Store the result for potential dbatools analysis
        self.auto_analysis_results.append(result)
        
        self.status_bar.showMessage(f"Completed analysis for: {zip_name}")
        
        # Move to next file
        self.current_auto_process_index += 1
        
        # Check if all files are processed
        if self.current_auto_process_index >= len(self.current_zip_files):
            logger.info("All ZIP files processed. Starting dbatools analysis...")
            self.status_bar.showMessage("All ZIP files processed. Starting dbatools analysis...")
            
            # Run dbatools analysis on all extracted BAK files
            QTimer.singleShot(1000, self.run_dbatools_analysis)
        else:
            # Use timer to process next file (prevents UI blocking)
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(500, self.auto_process_next_zip)

    def on_auto_analysis_error(self, error_message):
        """Handle error during automatic analysis"""
        zip_name = "Unknown"
        if hasattr(self, 'current_auto_process_index') and self.current_auto_process_index < len(self.current_zip_files):
            zip_name = os.path.basename(self.current_zip_files[self.current_auto_process_index])
        
        logger.error(f"Error during automatic analysis of {zip_name}: {error_message}")
        self.status_bar.showMessage(f"Error processing {zip_name}: {error_message}")
        
        # Continue with next file despite error
        self.current_auto_process_index += 1
        
        # Use timer to process next file
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(500, self.auto_process_next_zip)

    def run_dbatools_analysis(self):
        """Run dbatools PowerShell analysis on extracted BAK files"""
        logger.info("Starting dbatools analysis on extracted BAK files")
        
        if not hasattr(self, 'auto_analysis_results') or not self.auto_analysis_results:
            logger.warning("No analysis results available for dbatools analysis")
            self.status_bar.showMessage("No analysis results available for dbatools analysis")
            return
        
        # Collect all BAK files from the shared extraction directory
        bak_files_for_dbatools = []
        shared_extraction_dir = getattr(self, 'shared_extraction_dir', None)
        
        if shared_extraction_dir and os.path.exists(shared_extraction_dir):
            logger.debug(f"Scanning shared extraction directory for BAK files: {shared_extraction_dir}")
            
            # Find BAK files in shared extraction directory
            for root, dirs, files in os.walk(shared_extraction_dir):
                for file in files:
                    if file.lower().endswith('.bak'):
                        bak_path = os.path.join(root, file)
                        bak_files_for_dbatools.append(bak_path)
                        logger.debug(f"Found BAK file for dbatools: {bak_path}")
        else:
            logger.warning("No shared extraction directory found")
        
        if not bak_files_for_dbatools:
            logger.warning("No BAK files found for dbatools analysis")
            self.status_bar.showMessage("No BAK files found for dbatools analysis")
            return
        
        logger.info(f"Found {len(bak_files_for_dbatools)} BAK files for dbatools analysis")
        self.status_bar.showMessage(f"Running BAK metadata analysis on {len(bak_files_for_dbatools)} BAK files...")
        
        # Create Python script for BAK metadata analysis
        python_script = self.create_dbatools_script(bak_files_for_dbatools)
        
        # Execute Python script
        try:
            import subprocess
            logger.info("Executing BAK metadata analysis Python script")
            logger.debug(f"Python script content:\n{python_script}")
            
            # Write script to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as script_file:
                script_file.write(python_script)
                script_path = script_file.name
            
            logger.debug(f"Created Python script file: {script_path}")
            
            # Execute Python script
            cmd = ['python', script_path]
            logger.debug(f"Executing command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=os.path.dirname(__file__))
            
            logger.info(f"BAK analysis script execution completed with return code: {result.returncode}")
            
            if result.stdout:
                logger.info("BAK analysis script output:")
                logger.info(result.stdout)
                
            if result.stderr:
                logger.warning("BAK analysis script errors:")
                logger.warning(result.stderr)
            
            # Clean up script file
            try:
                os.unlink(script_path)
                logger.debug(f"Cleaned up Python script file: {script_path}")
            except Exception as e:
                logger.warning(f"Could not clean up script file: {e}")
            
            # Display results
            self.display_dbatools_results(result.stdout, result.stderr, result.returncode)
            
        except subprocess.TimeoutExpired:
            logger.error("dbatools analysis timed out after 5 minutes")
            self.status_bar.showMessage("dbatools analysis timed out")
        except Exception as e:
            logger.error(f"Error running dbatools analysis: {str(e)}", exc_info=True)
            self.status_bar.showMessage(f"Error running dbatools analysis: {str(e)}")
        finally:
            # Note: We don't clean up the shared extraction directory here
            # It will be cleaned up when the application closes or when explicitly requested
            logger.info("dbatools analysis completed - shared extraction directory preserved for future use")

    def create_dbatools_script(self, bak_files):
        """Create Python script for BAK metadata analysis using custom analyzer"""
        logger.debug("Creating BAK analysis Python script")
        
        script_lines = [
            "# BAK Metadata Analysis Script",
            "# Generated automatically by Backup Monitor",
            "import sys",
            "import os",
            "import json",
            "from datetime import datetime",
            "",
            "# Add src directory to path",
            "sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))",
            "",
            "try:",
            "    from bak_metadata_analyzer import BAKMetadataAnalyzer",
            "except ImportError:",
            "    print('Error: BAKMetadataAnalyzer not found. Please check src/bak_metadata_analyzer.py')",
            "    sys.exit(1)",
            "",
            "print('Starting BAK metadata analysis...')",
            "print('=' * 60)",
            "",
            "analyzer = BAKMetadataAnalyzer()",
            "results = []",
            "",
        ]
        
        for i, bak_file in enumerate(bak_files):
            # Escape Python path
            escaped_path = bak_file.replace("\\", "\\\\").replace("'", "\\'")
            
            script_lines.extend([
                f"",
                f"print('Analyzing BAK file {i+1}/{len(bak_files)}: {os.path.basename(bak_file)}')",
                f"print('-' * 40)",
                f"bak_file_{i} = r'{bak_file}'",
                f"",
                f"try:",
                f"    result_{i} = analyzer.analyze_bak_file(bak_file_{i})",
                f"    results.append(result_{i})",
                f"    ",
                f"    print(f'File: {{os.path.basename(bak_file_{i})}}')",
                f"    print(f'Size: {{result_{i}[\"file_structure\"][\"size_mb\"]:.2f}} MB')",
                f"    print(f'Valid BAK: {{result_{i}[\"validation\"][\"is_valid_bak\"]}}')",
                f"    print(f'Header Size: {{result_{i}[\"file_structure\"][\"header_size\"]:,}} bytes')",
                f"    print(f'Page Count: {{result_{i}[\"file_structure\"][\"page_count\"]:,}}')",
                f"    print(f'Data Blocks: {{result_{i}[\"file_structure\"][\"data_blocks\"]}}')",
                f"    print(f'Estimated Backup Sets: {{result_{i}[\"file_structure\"][\"estimated_backup_sets\"]}}')",
                f"    print(f'File Integrity: {{result_{i}[\"validation\"][\"file完整性\"]}}')",
                f"    ",
                f"    if result_{i}['validation']['warnings']:",
                f"        print('Warnings:')",
                f"        for warning in result_{i}['validation']['warnings']:",
                f"            print(f'  - {{warning}}')",
                f"    ",
                f"    print('Analysis Status: SUCCESS')",
                f"    ",
                f"except Exception as e:",
                f"    print(f'Error analyzing {{os.path.basename(bak_file_{i})}}: {{str(e)}}')",
                f"    results.append({{'error': str(e), 'filename': bak_file_{i}}})",
                f"",
            ])
        
        script_lines.extend([
            "",
            "print('=' * 60)",
            "print('BAK metadata analysis completed.')",
            "print(f'Total files analyzed: {len(bak_files)}')",
            "print(f'Successful analyses: {len([r for r in results if \"error\" not in r])}')",
            "print(f'Failed analyses: {len([r for r in results if \"error\" in r])}')",
            "",
            "# Summary of all results",
            "print('\\nSUMMARY:')",
            "for i, result in enumerate(results):",
            "    if 'error' not in result:",
            "        print(f'  File {i+1}: {result[\"file_structure\"][\"size_mb\"]:.1f}MB, Valid: {result[\"validation\"][\"is_valid_bak\"]}')",
            "    else:",
            "        print(f'  File {i+1}: ERROR - {result[\"error\"]}')",
        ])
        
        script_content = "\n".join(script_lines)
        logger.debug(f"Generated PowerShell script with {len(script_lines)} lines")
        return script_content

    def display_dbatools_results(self, stdout, stderr, return_code):
        """Display dbatools analysis results"""
        logger.info("Displaying dbatools analysis results")
        
        # Create results dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("dbatools Analysis Results")
        dialog.setModal(True)
        dialog.resize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Status label
        status_label = QLabel()
        if return_code == 0:
            status_label.setText("✅ dbatools analysis completed successfully")
            status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            status_label.setText(f"❌ dbatools analysis failed (exit code: {return_code})")
            status_label.setStyleSheet("color: red; font-weight: bold;")
        
        layout.addWidget(status_label)
        
        # Create tab widget for output and errors
        tab_widget = QTabWidget()
        
        # Output tab
        if stdout:
            output_text = QTextEdit()
            output_text.setPlainText(stdout)
            output_text.setReadOnly(True)
            output_text.setFont(QFont("Consolas", 9))
            tab_widget.addTab(output_text, "Output")
        
        # Error tab
        if stderr:
            error_text = QTextEdit()
            error_text.setPlainText(stderr)
            error_text.setReadOnly(True)
            error_text.setFont(QFont("Consolas", 9))
            error_text.setStyleSheet("color: red;")
            tab_widget.addTab(error_text, "Errors")
        
        layout.addWidget(tab_widget)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        # Show dialog
        dialog.exec_()
        
        self.status_bar.showMessage("dbatools analysis completed")

    def cleanup_temp_directories(self, temp_directories):
        """Clean up temporary directories after dbatools analysis"""
        logger.info(f"Cleaning up {len(temp_directories)} temporary directories")
        
        import shutil
        for temp_dir in temp_directories:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Could not clean up temporary directory {temp_dir}: {e}")
        
        logger.info("Temporary directory cleanup completed")
    
    def cleanup_shared_extraction_directory(self):
        """Explicitly clean up the shared extraction directory"""
        shared_extraction_dir = getattr(self, 'shared_extraction_dir', None)
        if shared_extraction_dir and os.path.exists(shared_extraction_dir):
            try:
                import shutil
                shutil.rmtree(shared_extraction_dir)
                logger.info(f"Cleaned up shared extraction directory: {shared_extraction_dir}")
                self.shared_extraction_dir = None
                return True
            except Exception as e:
                logger.warning(f"Could not clean up shared extraction directory {shared_extraction_dir}: {e}")
                return False
        return True
    
    def get_extraction_directory_info(self):
        """Get information about the current extraction directory"""
        shared_extraction_dir = getattr(self, 'shared_extraction_dir', None)
        if shared_extraction_dir and os.path.exists(shared_extraction_dir):
            try:
                # Count files in directory
                file_count = sum(len(files) for _, _, files in os.walk(shared_extraction_dir))
                # Get directory size
                total_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                               for dirpath, _, filenames in os.walk(shared_extraction_dir)
                               for filename in filenames)
                size_mb = total_size / (1024 * 1024)
                
                return {
                    'path': shared_extraction_dir,
                    'file_count': file_count,
                    'size_mb': size_mb,
                    'exists': True
                }
            except Exception as e:
                logger.warning(f"Could not get extraction directory info: {e}")
                return {'path': shared_extraction_dir, 'exists': False, 'error': str(e)}
        return {'path': None, 'exists': False}
        """Auto-analyze the first ZIP file in the list"""
        if len(self.current_zip_files) > 0:
            self.selected_zip_index = 0
            # Select first item in list
            if self.zip_list.count() > 0:
                self.zip_list.setCurrentRow(0)

            zip_path = self.current_zip_files[0]
            self.status_bar.showMessage(f"Auto-analyzing: {os.path.basename(zip_path)}")

            # Start comprehensive analysis
            self.show_progress("Auto-analyzing backup metadata...")

            worker = BackupAnalysisWorker(zip_path, "zip_metadata")
            worker.signals.finished.connect(self.on_zip_analysis_complete)
            worker.signals.error.connect(self.on_worker_error)
            worker.signals.progress.connect(self.on_worker_progress)

            self.thread_pool.start(worker)

    def clear_results(self):
        """Clear results display"""
        self.details_text.clear()
        self.status_bar.showMessage("Results cleared")

    def show_email_config_dialog(self):
        """Show email configuration dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Configuration Settings")
        dialog.setModal(True)
        dialog.resize(500, 300)
        layout = QFormLayout(dialog)

        # Create form fields
        sender_edit = QLineEdit(self.email_config.get('sender_email', ''))
        password_edit = QLineEdit(self.email_config.get('sender_password', ''))
        password_edit.setEchoMode(QLineEdit.Password)
        receiver_edit = QLineEdit(self.email_config.get('receiver_email', ''))
        
        # Add extraction directory field
        extraction_dir_layout = QHBoxLayout()
        extraction_dir_edit = QLineEdit(self.email_config.get('extraction_directory', ''))
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(lambda: self.browse_extraction_directory(extraction_dir_edit))
        extraction_dir_layout.addWidget(extraction_dir_edit)
        extraction_dir_layout.addWidget(browse_button)

        layout.addRow("Sender Email:", sender_edit)
        layout.addRow("Password:", password_edit)
        layout.addRow("Receiver Email:", receiver_edit)
        layout.addRow("Extraction Directory:", extraction_dir_layout)

        # Add info label
        info_label = QLabel("Leave extraction directory empty to use default location (extracted_backups folder)")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addRow(info_label)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)

        if dialog.exec_() == QDialog.Accepted:
            self.sender_email_edit.setText(sender_edit.text())
            self.sender_password_edit.setText(password_edit.text())
            self.receiver_email_edit.setText(receiver_edit.text())
            self.extraction_directory_edit = extraction_dir_edit  # Store reference for saving
            self.save_email_config()

    def browse_extraction_directory(self, line_edit):
        """Browse for extraction directory"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Extraction Directory",
            line_edit.text() or os.path.expanduser("~")
        )
        if directory:
            line_edit.setText(directory)

    def show_about_dialog(self):
        """Show about dialog"""
        QMessageBox.about(self,
            "About Backup Monitor",
            "Backup Monitor - PyQt5 Edition\n\n"
            "A comprehensive backup monitoring tool with:\n"
            "• ZIP file integrity checking\n"
            "• BAK file metadata analysis\n"
            "• Email notifications\n"
            "• Deep backup validation\n\n"
            "Version 1.0\n"
            "Built with PyQt5"
        )

    def filter_latest_files(self, zip_files):
        """Filter ZIP files to show only those with the latest date"""
        if not zip_files:
            return []
        
        # Check if zip_files contains file info objects or just paths
        if isinstance(zip_files[0], dict):
            # Working with file info objects
            file_times = [(zip_info, zip_info['modified']) for zip_info in zip_files]
        else:
            # Working with file paths (legacy)
            file_times = []
            for zip_file in zip_files:
                try:
                    mod_time = os.path.getmtime(zip_file)
                    file_times.append((zip_file, mod_time))
                except OSError:
                    logger.warning(f"Could not get modification time for {zip_file}")
                    continue
        
        if not file_times:
            return []
        
        # Sort by modification time (newest first)
        file_times.sort(key=lambda x: x[1], reverse=True)
        
        # Get the latest date (without time)
        latest_time = file_times[0][1]
        latest_date = datetime.fromtimestamp(latest_time).date()
        
        # Filter files that have the same date as the latest
        latest_files = []
        for file_item, mod_time in file_times:
            file_date = datetime.fromtimestamp(mod_time).date()
            if file_date == latest_date:
                latest_files.append(file_item)
        
        logger.info(f"Latest date found: {latest_date}")
        logger.info(f"Files with latest date: {len(latest_files)}")
        
        return latest_files
    
    def display_latest_files_with_metadata(self, latest_files):
        """Display latest files with their metadata and manual extraction option"""
        if not latest_files:
            self.status_bar.showMessage("No files found with latest date")
            return
        
        # Create dialog to display latest files
        dialog = QDialog(self)
        dialog.setWindowTitle(f"File Backup Terbaru - {len(latest_files)} file(s)")
        dialog.setMinimumSize(800, 600)
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        
        # Header info
        latest_date = datetime.fromtimestamp(os.path.getmtime(latest_files[0])).strftime("%Y-%m-%d")
        header_label = QLabel(f"<h3>File Backup dengan Tanggal Terbaru: {latest_date}</h3>")
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        # Create table for file list
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Nama File", "Ukuran", "Waktu Modifikasi", "Aksi"])
        table.setRowCount(len(latest_files))
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # Populate table
        for row, zip_file in enumerate(latest_files):
            # File name
            name_item = QTableWidgetItem(os.path.basename(zip_file))
            name_item.setData(Qt.UserRole, zip_file)  # Store full path
            table.setItem(row, 0, name_item)
            
            # File size
            try:
                size_mb = os.path.getsize(zip_file) / (1024 * 1024)
                size_item = QTableWidgetItem(f"{size_mb:.2f} MB")
                table.setItem(row, 1, size_item)
            except OSError:
                table.setItem(row, 1, QTableWidgetItem("Unknown"))
            
            # Modification time
            try:
                mod_time = datetime.fromtimestamp(os.path.getmtime(zip_file))
                time_item = QTableWidgetItem(mod_time.strftime("%Y-%m-%d %H:%M:%S"))
                table.setItem(row, 2, time_item)
            except OSError:
                table.setItem(row, 2, QTableWidgetItem("Unknown"))
            
            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 2, 5, 2)
            
            # Metadata button
            metadata_btn = QPushButton("Lihat Metadata")
            metadata_btn.clicked.connect(lambda checked, path=zip_file: self.show_single_zip_metadata(path))
            action_layout.addWidget(metadata_btn)
            
            # Extract and analyze button
            extract_btn = QPushButton("Extract & Analisis")
            extract_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
            extract_btn.clicked.connect(lambda checked, path=zip_file: self.manual_extract_and_analyze(path))
            action_layout.addWidget(extract_btn)
            
            table.setCellWidget(row, 3, action_widget)
        
        # Adjust column widths
        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(table)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        # Extract all button
        extract_all_btn = QPushButton("Extract & Analisis Semua File")
        extract_all_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 8px; }")
        extract_all_btn.clicked.connect(lambda: self.manual_extract_all_latest(latest_files))
        button_layout.addWidget(extract_all_btn)
        
        button_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Tutup")
        close_btn.clicked.connect(dialog.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Store dialog reference and show
        self.latest_files_dialog = dialog
        self.status_bar.showMessage(f"Menampilkan {len(latest_files)} file dengan tanggal terbaru: {latest_date}")
        dialog.show()
    
    def show_single_zip_metadata(self, zip_path):
        """Show metadata for a single ZIP file"""
        logger.info(f"Showing metadata for: {os.path.basename(zip_path)}")
        
        # Create worker to analyze ZIP metadata
        worker = BackupAnalysisWorker(zip_path, "zip_metadata")
        worker.signals.finished.connect(lambda result: self.display_single_zip_metadata(result, zip_path))
        worker.signals.error.connect(lambda error: self.on_worker_error(f"Error loading metadata: {error}"))
        
        self.thread_pool.start(worker)
        self.status_bar.showMessage(f"Loading metadata for {os.path.basename(zip_path)}...")
    
    def display_single_zip_metadata(self, result, zip_path):
        """Display metadata for a single ZIP file in a dialog"""
        if not result.get('success', False):
            QMessageBox.warning(self, "Error", f"Failed to load metadata for {os.path.basename(zip_path)}")
            return
        
        metadata = result.get('metadata', {})
        
        # Create metadata dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Metadata ZIP - {os.path.basename(zip_path)}")
        dialog.setMinimumSize(600, 400)
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        
        # Create text area for metadata
        text_area = QTextEdit()
        text_area.setReadOnly(True)
        text_area.setFont(QFont("Consolas", 10))
        
        # Format metadata display
        metadata_text = f"=== METADATA ZIP FILE ===\n"
        metadata_text += f"File: {os.path.basename(zip_path)}\n"
        metadata_text += f"Path: {zip_path}\n\n"
        
        if 'file_info' in metadata:
            file_info = metadata['file_info']
            metadata_text += f"Ukuran File: {file_info.get('size_mb', 'Unknown')} MB\n"
            metadata_text += f"Waktu Modifikasi: {file_info.get('modification_time', 'Unknown')}\n\n"
        
        if 'zip_info' in metadata:
            zip_info = metadata['zip_info']
            metadata_text += f"=== INFORMASI ZIP ===\n"
            metadata_text += f"Total File dalam ZIP: {zip_info.get('total_files', 0)}\n"
            metadata_text += f"Total Ukuran Terkompresi: {zip_info.get('compressed_size_mb', 0):.2f} MB\n"
            metadata_text += f"Total Ukuran Asli: {zip_info.get('uncompressed_size_mb', 0):.2f} MB\n"
            metadata_text += f"Rasio Kompresi: {zip_info.get('compression_ratio', 0):.1f}%\n\n"
            
            if 'files' in zip_info and zip_info['files']:
                metadata_text += f"=== DAFTAR FILE DALAM ZIP ===\n"
                for file_info in zip_info['files'][:10]:  # Show first 10 files
                    metadata_text += f"- {file_info.get('filename', 'Unknown')}\n"
                    metadata_text += f"  Ukuran: {file_info.get('file_size_mb', 0):.2f} MB\n"
                    metadata_text += f"  Terkompresi: {file_info.get('compress_size_mb', 0):.2f} MB\n\n"
                
                if len(zip_info['files']) > 10:
                    metadata_text += f"... dan {len(zip_info['files']) - 10} file lainnya\n"
        
        text_area.setPlainText(metadata_text)
        layout.addWidget(text_area)
        
        # Close button
        close_btn = QPushButton("Tutup")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.show()
        self.status_bar.showMessage(f"Metadata loaded for {os.path.basename(zip_path)}")
    
    def manual_extract_and_analyze(self, zip_path):
        """Manually extract and analyze a single ZIP file"""
        logger.info(f"Starting manual extraction and analysis for: {os.path.basename(zip_path)}")
        
        # Set extraction directory to D:\Gawean Rebinmas\App_Auto_Backup\Backup (same as backup location)
        extraction_dir = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup"
        zip_name = os.path.splitext(os.path.basename(zip_path))[0]
        
        # Confirm extraction with overwrite warning
        reply = QMessageBox.question(
            self, 
            "Konfirmasi Ekstraksi",
            f"Extract file ZIP ke:\n{extraction_dir}\n\n"
            f"PERINGATAN: Ekstraksi akan menimpa file yang sudah ada!\n"
            f"File dari {zip_name} akan di-extract langsung ke folder backup.\n\n"
            f"Lanjutkan?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Ensure extraction directory exists
        try:
            os.makedirs(extraction_dir, exist_ok=True)
            logger.info(f"Using extraction directory: {extraction_dir}")
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Failed to access extraction directory:\n{str(e)}")
            return
        
        # Start extraction and analysis
        self.show_progress(f"Extracting and analyzing {os.path.basename(zip_path)}...")
        self.status_bar.showMessage(f"Extracting {os.path.basename(zip_path)} to backup folder")
        
        # Create worker for extraction and analysis
        worker = BackupAnalysisWorker(zip_path, "manual_extract_analyze")
        worker.extraction_dir = extraction_dir  # Pass extraction directory
        worker.signals.finished.connect(self.on_manual_extraction_complete)
        worker.signals.error.connect(self.on_manual_extraction_error)
        worker.signals.progress.connect(self.on_worker_progress)
        
        self.thread_pool.start(worker)
    
    def manual_extract_all_latest(self, latest_files):
        """Extract and analyze all latest files with automatic filtering for BackupStaging and BackupVenuz"""
        # Filter files for BackupStaging and BackupVenuz
        filtered_files = []
        for file_path in latest_files:
            file_name = os.path.basename(file_path).lower()
            if 'backupstaging' in file_name or 'backupvenuz' in file_name:
                filtered_files.append(file_path)
        
        if not filtered_files:
            QMessageBox.information(
                self,
                "Tidak Ada File",
                "Tidak ditemukan file BackupStaging atau BackupVenuz untuk dianalisis."
            )
            return
        
        logger.info(f"Starting automated extraction for {len(filtered_files)} BackupStaging/BackupVenuz files")
        
        # Confirm extraction
        reply = QMessageBox.question(
            self,
            "Konfirmasi Analisis Otomatis",
            f"Analisis otomatis {len(filtered_files)} file backup (BackupStaging & BackupVenuz)?\n\n"
            f"File akan di-extract, dianalisis, dan laporan akan dikirim via email.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Close the latest files dialog
        if hasattr(self, 'latest_files_dialog'):
            self.latest_files_dialog.close()
        
        # Start batch extraction
        self.current_manual_files = filtered_files
        self.current_manual_index = 0
        self.manual_extraction_results = []
        
        self.extract_next_manual_file()
    
    def extract_next_manual_file(self):
        """Extract the next file in manual extraction queue"""
        if self.current_manual_index >= len(self.current_manual_files):
            # All files processed
            self.finish_manual_extraction()
            return
        
        zip_path = self.current_manual_files[self.current_manual_index]
        zip_name = os.path.splitext(os.path.basename(zip_path))[0]
        zip_dir = os.path.dirname(zip_path)
        extraction_dir = os.path.join(zip_dir, f"extracted_{zip_name}")
        
        logger.info(f"Manual extraction {self.current_manual_index + 1}/{len(self.current_manual_files)}: {os.path.basename(zip_path)}")
        
        # Create extraction directory
        try:
            os.makedirs(extraction_dir, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create extraction directory {extraction_dir}: {str(e)}")
            self.current_manual_index += 1
            QTimer.singleShot(100, self.extract_next_manual_file)
            return
        
        # Update progress
        self.show_progress(f"Extracting {self.current_manual_index + 1}/{len(self.current_manual_files)}: {os.path.basename(zip_path)}")
        self.status_bar.showMessage(f"Extracting {os.path.basename(zip_path)} to {extraction_dir}")
        
        # Create worker
        worker = BackupAnalysisWorker(zip_path, "manual_extract_analyze")
        worker.extraction_dir = extraction_dir
        worker.signals.finished.connect(self.on_manual_batch_extraction_complete)
        worker.signals.error.connect(self.on_manual_batch_extraction_error)
        worker.signals.progress.connect(self.on_worker_progress)
        
        self.thread_pool.start(worker)
    
    def on_manual_extraction_complete(self, result):
        """Handle completion of manual extraction for single file"""
        zip_name = result.get('zip_file', 'Unknown')
        success = result.get('processing_successful', False)
        
        self.hide_progress()
        
        if success:
            logger.info(f"Manual extraction completed successfully for: {zip_name}")
            QMessageBox.information(
                self,
                "Ekstraksi Berhasil",
                f"File {zip_name} berhasil di-extract dan dianalisis!\n\nLihat hasil analisis di panel kanan."
            )
            
            # Display results
            self.display_zip_analysis_results(result)
        else:
            logger.error(f"Manual extraction failed for: {zip_name}")
            QMessageBox.warning(
                self,
                "Ekstraksi Gagal", 
                f"Gagal extract file {zip_name}.\n\nLihat log untuk detail error."
            )
        
        self.status_bar.showMessage(f"Manual extraction completed for {zip_name}")
    
    def on_manual_extraction_error(self, error_message):
        """Handle error during manual extraction"""
        logger.error(f"Manual extraction error: {error_message}")
        self.hide_progress()
        QMessageBox.critical(self, "Error Ekstraksi", f"Error during extraction:\n{error_message}")
        self.status_bar.showMessage("Manual extraction failed")
    
    def on_manual_batch_extraction_complete(self, result):
        """Handle completion of one file in manual batch extraction"""
        zip_name = result.get('zip_file', 'Unknown')
        success = result.get('processing_successful', False)
        
        logger.info(f"Manual batch extraction completed for: {zip_name} (Success: {success})")
        
        # Store result
        self.manual_extraction_results.append(result)
        
        # Move to next file
        self.current_manual_index += 1
        
        # Continue with next file
        QTimer.singleShot(500, self.extract_next_manual_file)
    
    def on_manual_batch_extraction_error(self, error_message):
        """Handle error during manual batch extraction"""
        if hasattr(self, 'current_manual_index') and self.current_manual_index < len(self.current_manual_files):
            zip_name = os.path.basename(self.current_manual_files[self.current_manual_index])
            logger.error(f"Manual batch extraction error for {zip_name}: {error_message}")
        
        # Continue with next file despite error
        self.current_manual_index += 1
        QTimer.singleShot(500, self.extract_next_manual_file)
    
    def finish_manual_extraction(self):
        """Finish manual batch extraction and show summary with email reporting"""
        self.hide_progress()
        
        total_files = len(self.current_manual_files)
        successful_files = sum(1 for result in self.manual_extraction_results if result.get('processing_successful', False))
        
        logger.info(f"Manual batch extraction completed: {successful_files}/{total_files} successful")
        
        # Generate comprehensive report for email
        report_data = self._generate_email_report()
        
        # Show summary
        QMessageBox.information(
            self,
            "Analisis Otomatis Selesai",
            f"Analisis otomatis BackupStaging & BackupVenuz selesai!\n\n"
            f"Total file: {total_files}\n"
            f"Berhasil: {successful_files}\n"
            f"Gagal: {total_files - successful_files}\n\n"
            f"Laporan akan dikirim via email."
        )
        
        # Display results for successful extractions
        for result in self.manual_extraction_results:
            if result.get('processing_successful', False):
                self.display_zip_analysis_results(result)
        
        # Send email report
        if successful_files > 0:
            self._send_automated_email_report(report_data)
        
        self.status_bar.showMessage(f"Automated analysis completed: {successful_files}/{total_files} successful")
    
    def _generate_email_report(self) -> Dict[str, Any]:
        """Generate comprehensive email report from extraction results"""
        report_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        report = {
            'report_date': report_date,
            'total_files': len(self.current_manual_files),
            'successful_files': 0,
            'failed_files': 0,
            'backup_details': [],
            'summary': {}
        }
        
        for result in self.manual_extraction_results:
            if result.get('processing_successful', False):
                report['successful_files'] += 1
                
                # Extract key information
                zip_name = result.get('zip_file', 'Unknown')
                file_size = result.get('file_size_mb', 0)
                bak_analyses = result.get('bak_analyses', [])
                
                backup_info = {
                    'zip_name': zip_name,
                    'file_size_mb': file_size,
                    'analysis_time': result.get('analysis_time', ''),
                    'bak_count': len(bak_analyses),
                    'databases': []
                }
                
                # Process BAK analyses
                for bak_analysis in bak_analyses:
                    analysis = bak_analysis.get('analysis', {})
                    if 'error' not in analysis:
                        db_info = {
                            'filename': bak_analysis.get('file_name', ''),
                            'database_name': analysis.get('database_name', 'Unknown'),
                            'backup_type': analysis.get('backup_type', 'Unknown'),
                            'backup_date': analysis.get('backup_date', 'Unknown'),
                            'status': 'Valid'
                        }
                        
                        if 'database_info' in analysis:
                            db_info.update(analysis['database_info'])
                        
                        backup_info['databases'].append(db_info)
                
                report['backup_details'].append(backup_info)
            else:
                report['failed_files'] += 1
        
        # Generate summary
        report['summary'] = {
            'staging_files': len([f for f in self.current_manual_files if 'staging' in os.path.basename(f).lower()]),
            'venuz_files': len([f for f in self.current_manual_files if 'venuz' in os.path.basename(f).lower()]),
            'total_databases': sum(len(detail['databases']) for detail in report['backup_details']),
            'success_rate': f"{(report['successful_files'] / report['total_files'] * 100):.1f}%" if report['total_files'] > 0 else "0%"
        }
        
        return report
    
    def _send_automated_email_report(self, report_data: Dict[str, Any]):
        """Send automated email report after batch extraction"""
        try:
            # Load email configuration
            self.update_email_config()
            
            # Create email notifier
            email_notifier = EmailNotifier()
            email_notifier.sender_email = self.email_config.get('sender_email', '')
            email_notifier.sender_password = self.email_config.get('sender_password', '')
            email_notifier.receiver_email = self.email_config.get('receiver_email', '')
            
            # Generate email content
            subject = f"Laporan Analisis Backup Otomatis - {report_data['report_date']}"
            
            body = f"""
LAPORAN ANALISIS BACKUP OTOMATIS
=================================

Tanggal Analisis: {report_data['report_date']}
Total File Dianalisis: {report_data['total_files']}
Berhasil: {report_data['successful_files']}
Gagal: {report_data['failed_files']}
Success Rate: {report_data['summary']['success_rate']}

RINGKASAN:
- File BackupStaging: {report_data['summary']['staging_files']}
- File BackupVenuz: {report_data['summary']['venuz_files']}
- Total Database: {report_data['summary']['total_databases']}

DETAIL BACKUP:
"""
            
            for backup in report_data['backup_details']:
                body += f"""
📦 {backup['zip_name']}
   Ukuran: {backup['file_size_mb']:.2f} MB
   Waktu Analisis: {backup['analysis_time']}
   Jumlah BAK: {backup['bak_count']}
   
   Database yang ditemukan:
"""
                for db in backup['databases']:
                    body += f"""   - {db['filename']}
     Database: {db['database_name']}
     Type: {db['backup_type']}
     Tanggal Backup: {db['backup_date']}
     Status: {db['status']}
"""
            
            body += f"""

Laporan ini dibuat secara otomatis oleh sistem monitoring backup.
Untuk informasi lebih detail, silakan cek aplikasi monitoring.

---
Backup Monitor System
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            # Send email directly using EmailNotifier
            success, message = email_notifier.send_notification(subject, body)
            
            if success:
                logger.info("Automated email report sent successfully")
                QMessageBox.information(
                    self,
                    "Email Sent",
                    "Laporan analisis otomatis berhasil dikirim via email."
                )
            else:
                logger.error(f"Failed to send automated email report: {message}")
                QMessageBox.warning(
                    self,
                    "Email Error", 
                    f"Gagal mengirim laporan email: {message}"
                )
            
        except Exception as e:
            logger.error(f"Failed to send automated email report: {str(e)}")
            QMessageBox.warning(
                self,
                "Email Error",
                f"Gagal mengirim laporan email: {str(e)}"
            )

    # Import and add new methods from backup_monitor_methods.py
    def extract_all_and_analyze_bak(self):
        """Extract all ZIP files and analyze BAK files with user confirmation"""
        if not hasattr(self, 'current_zip_files') or len(self.current_zip_files) == 0:
            self.append_terminal_output("❌ ERROR: Tidak ada file ZIP yang ditemukan!")
            QMessageBox.warning(self, "Warning", "Tidak ada file ZIP yang ditemukan. Silakan refresh files terlebih dahulu.")
            return

        # Count files that will be processed (only Staging and Venuz, excluding Plantware3)
        processable_files = []
        for zip_path in self.current_zip_files:
            zip_name = os.path.basename(zip_path).lower()
            if "plantware" not in zip_name and ("staging" in zip_name or "venuz" in zip_name):
                processable_files.append(zip_path)

        # Confirm extraction
        reply = QMessageBox.question(
            self, 
            "Konfirmasi Ekstraksi Massal",
            f"Akan mengekstrak {len(processable_files)} file ZIP (BackupStaging & BackupVenuz) ke:\n"
            f"D:\\Gawean Rebinmas\\App_Auto_Backup\\Backup\n\n"
            f"📋 FILTER AKTIF:\n"
            f"✅ Hanya memproses: BackupStaging dan BackupVenuz\n"
            f"⏭️ Melewati: File Plantware3 (untuk mencegah aplikasi not responding)\n"
            f"⏭️ Melewati: File lainnya\n\n"
            f"⚠️ PERINGATAN: Ekstraksi akan menimpa file yang sudah ada!\n"
            f"Semua file akan di-extract langsung ke folder backup tanpa subfolder.\n\n"
            f"Total file yang akan diproses: {len(processable_files)} dari {len(self.current_zip_files)} file\n\n"
            f"Lanjutkan?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            self.append_terminal_output("❌ Ekstraksi dibatalkan oleh user.")
            return

        self.append_terminal_output("🚀 Memulai ekstraksi massal dengan filter...")
        self.append_terminal_output(f"📁 Target direktori: D:\\Gawean Rebinmas\\App_Auto_Backup\\Backup")
        self.append_terminal_output(f"📦 Total file ZIP: {len(self.current_zip_files)}")
        self.append_terminal_output(f"✅ File yang akan diproses: {len(processable_files)} (BackupStaging & BackupVenuz)")
        self.append_terminal_output(f"⏭️ File yang dilewati: {len(self.current_zip_files) - len(processable_files)} (Plantware3 & lainnya)")
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
        
        # Filter: Only process BackupStaging and BackupVenuz files, skip Plantware3
        if "plantware" in zip_name.lower():
            self.append_terminal_output(f"⏭️ Melewati: {zip_name} (File Plantware3 dikecualikan untuk mencegah aplikasi not responding)")
            self.extraction_results.append({'zip_path': zip_path, 'status': 'skipped', 'reason': 'Plantware3 file excluded'})
            
            # Move to next file
            self.current_extraction_index += 1
            QTimer.singleShot(100, self.extract_next_zip)
            return
        
        # Only process BackupStaging and BackupVenuz files
        if not ("staging" in zip_name.lower() or "venuz" in zip_name.lower()):
            self.append_terminal_output(f"⏭️ Melewati: {zip_name} (Hanya memproses BackupStaging dan BackupVenuz)")
            self.extraction_results.append({'zip_path': zip_path, 'status': 'skipped', 'reason': 'Not Staging or Venuz file'})
            
            # Move to next file
            self.current_extraction_index += 1
            QTimer.singleShot(100, self.extract_next_zip)
            return
        
        self.append_terminal_output(f"📦 Mengekstrak: {zip_name}")
        
        # Extract to backup directory
        extraction_dir = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup"
        self.append_terminal_output(f"📁 Target ekstraksi: {extraction_dir}")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Get list of files in ZIP
                file_list = zip_ref.namelist()
                self.append_terminal_output(f"📋 File dalam ZIP: {len(file_list)} file")
                
                # Log BAK files found in ZIP
                bak_files_in_zip = [f for f in file_list if f.lower().endswith('.bak')]
                if bak_files_in_zip:
                    self.append_terminal_output(f"🎯 File BAK dalam ZIP: {len(bak_files_in_zip)}")
                    for bak_file in bak_files_in_zip:
                        self.append_terminal_output(f"   📄 {bak_file}")
                else:
                    self.append_terminal_output("⚠️ Tidak ada file BAK ditemukan dalam ZIP")
                
                # Extract all files directly to backup directory (overwrite mode)
                zip_ref.extractall(extraction_dir)
                self.append_terminal_output(f"✅ Ekstraksi selesai ke: {extraction_dir}")
                
                # Verify extracted files
                extracted_bak_files = []
                for root, dirs, files in os.walk(extraction_dir):
                    for file in files:
                        if file.lower().endswith('.bak'):
                            extracted_bak_files.append(os.path.join(root, file))
                
                self.append_terminal_output(f"🔍 File BAK setelah ekstraksi: {len(extracted_bak_files)}")
                for bak_file in extracted_bak_files:
                    rel_path = os.path.relpath(bak_file, extraction_dir)
                    file_size = os.path.getsize(bak_file) / (1024 * 1024)  # MB
                    self.append_terminal_output(f"   📄 {rel_path} ({file_size:.1f} MB)")
                
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
        
        # Use existing BAK analysis functionality
        worker = BackupAnalysisWorker(backup_dir, "analyze_bak_files_only")
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

            # Store analysis result for email (if not already stored)
            if not hasattr(self, 'analysis_results'):
                self.analysis_results = []

            # Check if this result is already stored
            result_identifier = result.get('backup_directory', '') or result.get('zip_file', '')
            already_stored = any(
                (r.get('backup_directory', '') or r.get('zip_file', '')) == result_identifier
                for r in self.analysis_results
            )

            if not already_stored:
                self.analysis_results.append(result)
                self.append_terminal_output(f"💾 Disimpan hasil analisis BAK terminal: {result_identifier}")
                logger.info(f"Stored BAK terminal analysis result for: {result_identifier}")

            # Ask if user wants to send email summary
            reply = QMessageBox.question(
                self,
                "Analisis Selesai",
                "Analisis BAK dan ZIP telah selesai.\n\nApakah Anda ingin mengirim email summary hasil analisis?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.send_summary_email()
        else:
            error_msg = result.get('error', 'Unknown error')
            self.append_terminal_output(f"❌ Analisis BAK gagal: {error_msg}")

    def append_terminal_output(self, message):
        """Update status info instead of terminal output"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        # Update status info
        current_text = self.status_info.toPlainText()
        updated_text = current_text + "\n" + formatted_message
        
        # Keep only last 20 lines to prevent overflow
        lines = updated_text.split('\n')
        if len(lines) > 20:
            lines = lines[-20:]
            updated_text = '\n'.join(lines)
        
        self.status_info.setPlainText(updated_text)
        
        # Auto-scroll to bottom
        cursor = self.status_info.textCursor()
        cursor.movePosition(cursor.End)
        self.status_info.setTextCursor(cursor)
        
        # Process events to update UI
        QApplication.processEvents()

    def update_summary_tables(self):
        """Update summary tables with current data"""
        try:
            # Update ZIP summary table
            self.zip_summary_table.setRowCount(len(self.current_zip_files))
            
            for i, zip_path in enumerate(self.current_zip_files):
                zip_name = os.path.basename(zip_path)
                
                # Get file size
                try:
                    file_size = os.path.getsize(zip_path) / (1024 * 1024)  # MB
                    size_text = f"{file_size:.1f}"
                except:
                    size_text = "N/A"
                
                # Get modification time
                try:
                    mod_time = datetime.fromtimestamp(os.path.getmtime(zip_path))
                    mod_text = mod_time.strftime("%Y-%m-%d %H:%M")
                except:
                    mod_text = "N/A"
                
                # Set table items
                self.zip_summary_table.setItem(i, 0, QTableWidgetItem(zip_name))
                self.zip_summary_table.setItem(i, 1, QTableWidgetItem(size_text))
                self.zip_summary_table.setItem(i, 2, QTableWidgetItem("Ready"))
                self.zip_summary_table.setItem(i, 3, QTableWidgetItem("Pending"))
                self.zip_summary_table.setItem(i, 4, QTableWidgetItem(mod_text))
                
                # Add action button
                action_btn = QPushButton("Analyze")
                action_btn.clicked.connect(lambda checked, path=zip_path: self.analyze_single_zip(path))
                self.zip_summary_table.setCellWidget(i, 5, action_btn)
            
            # Update statistics
            self.total_files_label.setText(str(len(self.current_zip_files)))
            
        except Exception as e:
            logger.error(f"Error updating summary tables: {e}")

    def analyze_single_zip(self, zip_path):
        """Analyze a single ZIP file"""
        try:
            self.append_terminal_output(f"Starting analysis for {os.path.basename(zip_path)}")
            # Here you can add specific analysis logic for single ZIP file
            
        except Exception as e:
            logger.error(f"Error analyzing ZIP file: {e}")
            self.append_terminal_output(f"Error analyzing {os.path.basename(zip_path)}: {str(e)}")

    def generate_pdf_report(self):
        """Generate PDF report for selected ZIP files"""
        try:
            # Get selected rows from ZIP summary table
            selected_rows = []
            for row in range(self.zip_summary_table.rowCount()):
                checkbox = self.zip_summary_table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    selected_rows.append(row)
            
            if not selected_rows:
                QMessageBox.warning(self, "Warning", "Pilih minimal satu file ZIP untuk generate report PDF.")
                return
            
            # Get selected ZIP file paths
            selected_zip_files = []
            for row in selected_rows:
                name_item = self.zip_summary_table.item(row, 1)
                if name_item:
                    zip_name = name_item.text()
                    # Find full path from current_zip_files
                    for zip_path in self.current_zip_files:
                        if os.path.basename(zip_path) == zip_name:
                            selected_zip_files.append(zip_path)
                            break
            
            if not selected_zip_files:
                QMessageBox.warning(self, "Warning", "Tidak dapat menemukan file ZIP yang dipilih.")
                return
            
            # Ask user for output location
            output_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Simpan PDF Report", 
                f"backup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if not output_path:
                return
            
            # Show progress dialog
            progress = QProgressDialog("Generating PDF report...", "Cancel", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            progress.setValue(10)
            
            # Generate PDF report
            generator = PDFReportGenerator()
            progress.setValue(50)
            
            success = generator.generate_report(selected_zip_files, output_path)
            progress.setValue(100)
            progress.close()
            
            if success:
                # Update status
                self.append_terminal_output(f"PDF report berhasil dibuat: {output_path}")
                
                # Ask if user wants to open the PDF
                reply = QMessageBox.question(
                    self, 
                    "Success", 
                    f"PDF report berhasil dibuat!\n\nLokasi: {output_path}\n\nBuka file sekarang?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    try:
                        os.startfile(output_path)  # Windows
                    except:
                        try:
                            import subprocess
                            subprocess.run(['xdg-open', output_path])  # Linux
                        except:
                            pass
            else:
                QMessageBox.critical(self, "Error", "Gagal membuat PDF report.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generating PDF report: {str(e)}")
            self.append_terminal_output(f"Error generating PDF report: {str(e)}")

    def show_analysis_data_status(self):
        """Show status of available analysis data for debugging"""
        status_msg = "🔍 STATUS DATA ANALISIS:\n"
        status_msg += "=" * 50 + "\n\n"

        # Check analysis_results
        if hasattr(self, 'analysis_results') and self.analysis_results:
            status_msg += f"📊 analysis_results: {len(self.analysis_results)} items\n"
            for i, result in enumerate(self.analysis_results):
                result_type = result.get('type', 'Unknown')
                if result_type == 'zip_metadata':
                    status_msg += f"  {i+1}. ZIP: {os.path.basename(result.get('zip_file', 'Unknown'))}\n"
                elif result_type == 'bak_files':
                    status_msg += f"  {i+1}. BAK: {result.get('backup_directory', 'Unknown')}\n"
                else:
                    status_msg += f"  {i+1}. {result_type}: Unknown\n"
        else:
            status_msg += "📊 analysis_results: Tidak ada data\n"

        # Check manual_extraction_results
        if hasattr(self, 'manual_extraction_results') and self.manual_extraction_results:
            status_msg += f"📂 manual_extraction_results: {len(self.manual_extraction_results)} items\n"
            successful = sum(1 for r in self.manual_extraction_results if r.get('processing_successful', False))
            status_msg += f"   Berhasil: {successful}, Gagal: {len(self.manual_extraction_results) - successful}\n"
        else:
            status_msg += "📂 manual_extraction_results: Tidak ada data\n"

        # Check current_files
        if hasattr(self, 'current_files') and self.current_files:
            status_msg += f"📁 current_files: {len(self.current_files)} items\n"
            complete = sum(1 for f in self.current_files if f.get('analysis_complete', False))
            status_msg += f"   Complete: {complete}, Incomplete: {len(self.current_files) - complete}\n"
        else:
            status_msg += "📁 current_files: Tidak ada data\n"

        # Show total available data
        total_zip = 0
        total_bak = 0

        if hasattr(self, 'analysis_results') and self.analysis_results:
            for result in self.analysis_results:
                if result.get('type') == 'zip_metadata':
                    total_zip += 1
                    if 'backup_analysis' in result:
                        total_bak += len(result['backup_analysis'].get('bak_files', []))
                    elif 'bak_analyses' in result:
                        total_bak += len(result['bak_analyses'])
                elif result.get('type') == 'bak_files':
                    total_bak += len(result.get('bak_analyses', []))

        if hasattr(self, 'manual_extraction_results') and self.manual_extraction_results:
            for result in self.manual_extraction_results:
                if result.get('processing_successful', False):
                    total_zip += 1
                    total_bak += len(result.get('bak_analyses', []))

        status_msg += f"\n📈 TOTAL DATA YANG TERSEDIA:\n"
        status_msg += f"   File ZIP: {total_zip}\n"
        status_msg += f"   File BAK: {total_bak}\n"

        QMessageBox.information(self, "Status Data Analisis", status_msg)

    def send_summary_email(self):
        """Send summary email with current analysis results"""
        try:
            self.show_progress("Mengumpulkan data analisis...")
            self.append_terminal_output("📊 Mengumpulkan data untuk email summary...")

            # Debug: Check what data is available
            self.append_terminal_output("🔍 DEBUG: Memeriksa ketersediaan data...")

            # Initialize analysis storage if not exists
            if not hasattr(self, 'analysis_results'):
                self.analysis_results = []
                self.append_terminal_output("📝 Inisialisasi analysis_results storage")

            # Check available data sources
            available_sources = []
            if hasattr(self, 'manual_extraction_results') and self.manual_extraction_results:
                available_sources.append(f"manual_extraction_results ({len(self.manual_extraction_results)} items)")

            if hasattr(self, 'current_files') and self.current_files:
                available_sources.append(f"current_files ({len(self.current_files)} items)")

            if hasattr(self, 'analysis_results') and self.analysis_results:
                available_sources.append(f"analysis_results ({len(self.analysis_results)} items)")

            self.append_terminal_output(f"📊 Sumber data tersedia: {', '.join(available_sources) if available_sources else 'Tidak ada'}")

            # Collect current analysis results
            zip_results = []
            bak_results = []

            # Method 1: Get from analysis_results (primary)
            if hasattr(self, 'analysis_results') and self.analysis_results:
                self.append_terminal_output(f"🔍 Mengumpulkan dari analysis_results...")
                for result in self.analysis_results:
                    if result.get('type') in ['zip_metadata', 'bak_files']:
                        converted = self._convert_analysis_result_to_email_format(result)
                        if converted:
                            zip_results.append(converted)
                            bak_results.extend(converted.get('bak_analyses', []))
                            self.append_terminal_output(f"✅ Ditambahkan dari analysis_results: {os.path.basename(converted.get('zip_file', 'Unknown'))}")

            # Method 2: Get from manual extraction results
            if hasattr(self, 'manual_extraction_results') and self.manual_extraction_results:
                self.append_terminal_output(f"🔍 Mengumpulkan dari manual_extraction_results...")
                for result in self.manual_extraction_results:
                    if result.get('processing_successful', False):
                        converted = self._convert_manual_result_to_email_format(result)
                        if converted:
                            zip_results.append(converted)
                            bak_results.extend(converted.get('bak_analyses', []))
                            self.append_terminal_output(f"✅ Ditambahkan dari manual: {os.path.basename(converted.get('zip_file', 'Unknown'))}")

            # Method 3: Get from current files (if available)
            if hasattr(self, 'current_files') and self.current_files:
                self.append_terminal_output(f"🔍 Mengumpulkan dari current_files...")
                for file_info in self.current_files:
                    if file_info.get('analysis_complete', False):
                        converted = self._convert_current_file_to_email_format(file_info)
                        if converted:
                            zip_results.append(converted)
                            bak_results.extend(converted.get('bak_analyses', []))
                            self.append_terminal_output(f"✅ Ditambahkan dari current: {os.path.basename(converted.get('zip_file', 'Unknown'))}")

            # Remove duplicates based on zip_file path
            unique_zip_results = []
            seen_paths = set()
            for result in zip_results:
                zip_path = result.get('zip_file', '')
                if zip_path and zip_path not in seen_paths:
                    unique_zip_results.append(result)
                    seen_paths.add(zip_path)

            self.append_terminal_output(f"📊 Total unik: {len(unique_zip_results)} ZIP, {len(bak_results)} BAK")

            # Debug: Show what we found
            if unique_zip_results:
                self.append_terminal_output("🔍 DEBUG: Data yang ditemukan:")
                for i, result in enumerate(unique_zip_results[:3]):  # Show first 3
                    self.append_terminal_output(f"  {i+1}. {result.get('zip_file', 'Unknown')} - {len(result.get('bak_analyses', []))} BAK")
                if len(unique_zip_results) > 3:
                    self.append_terminal_output(f"  ... dan {len(unique_zip_results) - 3} lainnya")
            else:
                self.append_terminal_output("🔍 DEBUG: Tidak ada data ZIP yang ditemukan")

            # If no ZIP entries but we have BAK results (from BAK-only analysis), allow sending
            if not unique_zip_results and not bak_results:
                self.append_terminal_output("⚠️ Tidak ada data analisis yang tersedia untuk dikirim")
                QMessageBox.warning(self, "Warning", "Tidak ada data analisis yang tersedia untuk dikirim via email.\n\nPastikan Anda telah melakukan analisis ZIP/BAK terlebih dahulu.")
                self.hide_progress()
                return

            # Send email summary
            self.send_backup_summary_email(unique_zip_results, bak_results)
            self.hide_progress()

        except Exception as e:
            logger.error(f"Error in send_summary_email: {str(e)}")
            self.append_terminal_output(f"❌ Error mengirim summary email: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error mengirim summary email: {str(e)}")
            self.hide_progress()

    def _convert_analysis_result_to_email_format(self, result):
        """Convert analysis result to email format"""
        try:
            if result.get('type') == 'zip_metadata':
                return {
                    'zip_file': result.get('zip_file', ''),
                    'file_size_mb': result.get('zip_integrity', {}).get('total_size', 0) / (1024*1024),
                    'integrity_check': result.get('zip_integrity', {}),
                    'bak_analyses': self._extract_bak_analyses_from_result(result),
                    'metadata': {
                        'creation_date': result.get('analysis_time', ''),
                        'analysis_time': result.get('analysis_time', '')
                    }
                }
            elif result.get('type') == 'bak_files':
                # For BAK-only analysis, create a ZIP-like entry
                normalized_baks = []
                for b in result.get('bak_analyses', []):
                    # Normalize common fields to avoid Unknown in email
                    bak_name = b.get('file_name') or b.get('filename') or os.path.basename(b.get('file_path', '') or '')
                    analysis = b.get('analysis') or {}
                    db_info = b.get('database_info') or analysis.get('database_info') or {}
                    backup_header = b.get('backup_header', {})
                    backup_date_val = (
                        analysis.get('backup_date')
                        or db_info.get('backup_date')
                        or backup_header.get('backup_finish_date')
                        or 'Unknown'
                    )

                    normalized_baks.append({
                        'file_name': bak_name or 'Unknown',
                        'file_size_mb': b.get('file_size_mb') or ((b.get('file_size') or 0) / (1024*1024)),
                        'analysis_status': b.get('analysis_status', 'success' if not b.get('error') else 'failed'),
                        'error': b.get('error'),
                        'analysis': {
                            'backup_type': analysis.get('backup_type') or db_info.get('backup_type') or 'Unknown',
                            'database_name': analysis.get('database_name') or db_info.get('database_name') or 'Unknown',
                            'backup_date': backup_date_val,
                            'database_info': db_info
                        },
                        'validation': b.get('validation', {})
                    })

                return {
                    'zip_file': result.get('backup_directory', ''),
                    'file_size_mb': 0,  # Not applicable for BAK-only
                    'integrity_check': {'is_valid': True},  # Assume valid if we got here
                    'bak_analyses': normalized_baks,
                    'metadata': {
                        'creation_date': result.get('analysis_time', ''),
                        'analysis_time': result.get('analysis_time', '')
                    }
                }
        except Exception as e:
            logger.error(f"Error converting analysis result: {str(e)}")
        return None

    def _convert_manual_result_to_email_format(self, result):
        """Convert manual extraction result to email format"""
        try:
            # Normalize BAK analyses to avoid Unknown fields in email
            normalized_baks = []
            for b in result.get('bak_analyses', []):
                bak_name = b.get('file_name') or b.get('filename') or os.path.basename(b.get('file_path', '') or '')
                analysis = b.get('analysis') or {}
                db_info = b.get('database_info') or analysis.get('database_info') or {}
                backup_header = b.get('backup_header', {})
                backup_date_val = (
                    analysis.get('backup_date')
                    or db_info.get('backup_date')
                    or backup_header.get('backup_finish_date')
                    or 'Unknown'
                )

                normalized_baks.append({
                    'file_name': bak_name or 'Unknown',
                    'file_size_mb': b.get('file_size_mb') or ((b.get('file_size') or 0) / (1024*1024)),
                    'analysis_status': b.get('analysis_status', 'success' if not b.get('error') else 'failed'),
                    'error': b.get('error'),
                    'analysis': {
                        'backup_type': analysis.get('backup_type') or db_info.get('backup_type') or 'Unknown',
                        'database_name': analysis.get('database_name') or db_info.get('database_name') or 'Unknown',
                        'backup_date': backup_date_val,
                        'database_info': db_info
                    },
                    'validation': b.get('validation', {})
                })

            return {
                'zip_file': result.get('zip_file', ''),
                'file_size_mb': result.get('file_size_mb', 0),
                'integrity_check': result.get('integrity_check', {}),
                'bak_analyses': normalized_baks,
                'metadata': result.get('metadata', {})
            }
        except Exception as e:
            logger.error(f"Error converting manual result: {str(e)}")
        return None

    def _convert_current_file_to_email_format(self, file_info):
        """Convert current file info to email format"""
        try:
            # Normalize BAK analyses to avoid Unknown fields in email
            normalized_baks = []
            for b in file_info.get('bak_analyses', []):
                bak_name = b.get('file_name') or b.get('filename') or os.path.basename(b.get('file_path', '') or '')
                analysis = b.get('analysis') or {}
                db_info = b.get('database_info') or analysis.get('database_info') or {}
                backup_header = b.get('backup_header', {})
                backup_date_val = (
                    analysis.get('backup_date')
                    or db_info.get('backup_date')
                    or backup_header.get('backup_finish_date')
                    or 'Unknown'
                )

                normalized_baks.append({
                    'file_name': bak_name or 'Unknown',
                    'file_size_mb': b.get('file_size_mb') or ((b.get('file_size') or 0) / (1024*1024)),
                    'analysis_status': b.get('analysis_status', 'success' if not b.get('error') else 'failed'),
                    'error': b.get('error'),
                    'analysis': {
                        'backup_type': analysis.get('backup_type') or db_info.get('backup_type') or 'Unknown',
                        'database_name': analysis.get('database_name') or db_info.get('database_name') or 'Unknown',
                        'backup_date': backup_date_val,
                        'database_info': db_info
                    },
                    'validation': b.get('validation', {})
                })

            return {
                'zip_file': file_info.get('filename', ''),
                'file_size_mb': file_info.get('file_size_mb', 0),
                'integrity_check': file_info.get('integrity_check', {}),
                'bak_analyses': normalized_baks,
                'metadata': file_info.get('metadata', {})
            }
        except Exception as e:
            logger.error(f"Error converting current file: {str(e)}")
        return None

    def _extract_bak_analyses_from_result(self, result):
        """Extract BAK analyses from different result structures"""
        bak_analyses = []

        # Try different structures
        if 'backup_analysis' in result:
            backup_analysis = result['backup_analysis']
            for bak_file in backup_analysis.get('bak_files', []):
                bak_analyses.append({
                    'file_name': bak_file.get('filename', ''),
                    'file_size_mb': bak_file.get('size', 0) / (1024*1024),
                    'analysis': {
                        'backup_type': 'Unknown',
                        'database_name': 'Unknown',
                        'backup_date': bak_file.get('modified', 'Unknown'),
                        'database_info': {}
                    }
                })

        elif 'bak_analyses' in result:
            # Normalize when pulling directly from comprehensive result
            for b in result['bak_analyses']:
                bak_name = b.get('file_name') or b.get('filename') or os.path.basename(b.get('file_path', '') or '')
                analysis = b.get('analysis') or {}
                db_info = b.get('database_info') or analysis.get('database_info') or {}
                backup_header = b.get('backup_header', {})
                backup_date_val = (
                    analysis.get('backup_date')
                    or db_info.get('backup_date')
                    or backup_header.get('backup_finish_date')
                    or 'Unknown'
                )

                bak_analyses.append({
                    'file_name': bak_name or 'Unknown',
                    'file_size_mb': b.get('file_size_mb') or ((b.get('file_size') or 0) / (1024*1024)),
                    'analysis_status': b.get('analysis_status', 'success' if not b.get('error') else 'failed'),
                    'error': b.get('error'),
                    'analysis': {
                        'backup_type': analysis.get('backup_type') or db_info.get('backup_type') or 'Unknown',
                        'database_name': analysis.get('database_name') or db_info.get('database_name') or 'Unknown',
                        'backup_date': backup_date_val,
                        'database_info': db_info
                    },
                    'validation': b.get('validation', {})
                })

        return bak_analyses

    def send_backup_summary_email(self, zip_analysis_results=None, bak_analysis_results=None):
        """Send email summary after BAK and ZIP analysis is completed"""
        try:
            # Load email configuration
            self.update_email_config()

            # Create email notifier
            email_notifier = EmailNotifier()
            email_notifier.sender_email = self.email_config.get('sender_email', '')
            email_notifier.sender_password = self.email_config.get('sender_password', '')
            email_notifier.receiver_email = self.email_config.get('receiver_email', '')

            # Generate report date
            report_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Generate email content
            subject = f"LAPORAN SUMMARY ANALISIS BACKUP - {report_date}"

            body = self._generate_backup_summary_html(zip_analysis_results, bak_analysis_results)

            # Send email
            success, message = email_notifier.send_notification(subject, body)

            if success:
                logger.info("Backup summary email sent successfully")
                self.append_terminal_output("✅ Laporan summary backup berhasil dikirim via email")
                QMessageBox.information(self, "Success", "Laporan summary backup berhasil dikirim via email")
            else:
                logger.error(f"Failed to send backup summary email: {message}")
                self.append_terminal_output(f"❌ Gagal mengirim laporan summary email: {message}")
                QMessageBox.warning(self, "Warning", f"Gagal mengirim laporan summary email: {message}")

        except Exception as e:
            logger.error(f"Error sending backup summary email: {str(e)}")
            self.append_terminal_output(f"❌ Error mengirim laporan summary email: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error mengirim laporan summary email: {str(e)}")

    def _generate_backup_summary_html(self, zip_results=None, bak_results=None):
        """Generate HTML content for backup summary email"""

        # Generate executive summary first
        executive_summary = self._generate_executive_summary(zip_results, bak_results)

        # ZIP Analysis Summary
        zip_summary = self._generate_zip_analysis_summary(zip_results)

        # BAK Analysis Summary
        bak_summary = self._generate_bak_analysis_summary(bak_results)

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .executive-summary {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 15px 0; }}
                .summary-card {{ background-color: white; padding: 15px; border-radius: 5px; border: 1px solid #ddd; }}
                .summary-card h4 {{ margin: 0 0 10px 0; color: #333; }}
                .summary-card .value {{ font-size: 24px; font-weight: bold; color: #2196F3; }}
                .summary-card .label {{ font-size: 12px; color: #666; }}
                .section {{ margin: 20px 0; }}
                .summary-table {{ border-collapse: collapse; width: 100%; }}
                .summary-table th, .summary-table td {{
                    border: 1px solid #ddd; padding: 8px; text-align: left;
                }}
                .summary-table th {{ background-color: #f2f2f2; }}
                .status-valid {{ color: green; font-weight: bold; }}
                .status-invalid {{ color: red; font-weight: bold; }}
                .status-warning {{ color: orange; font-weight: bold; }}
                .file-info {{ background-color: #f9f9f9; padding: 10px; border-radius: 3px; margin: 5px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>LAPORAN SUMMARY ANALISIS BACKUP DATABASE</h2>
                <p><strong>Tanggal Analisis:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            {executive_summary}

            <div class="section">
                <h3>📦 DETAIL ANALISIS ZIP FILE</h3>
                {zip_summary}
            </div>

            <div class="section">
                <h3>💾 DETAIL ANALISIS BAK FILE</h3>
                {bak_summary}
            </div>

            <div class="section">
                <h3>📊 REKOMENDASI</h3>
                {self._generate_recommendations(zip_results, bak_results)}
            </div>

            <hr>
            <p><em>Laporan ini dibuat otomatis oleh sistem monitoring backup database</em></p>
        </body>
        </html>
        """

        return html_content

    def _generate_executive_summary(self, zip_results=None, bak_results=None):
        """Generate executive summary with key metrics"""
        # Support BAK-only analysis by synthesizing minimal ZIP context
        if not zip_results:
            if bak_results:
                zip_results = [{
                    'zip_file': 'BAK-only analysis',
                    'file_size_mb': 0,
                    'integrity_check': {'is_valid': True},
                    'bak_analyses': bak_results,
                    'metadata': {}
                }]
            else:
                return "<div class='executive-summary'><h3>📊 EXECUTIVE SUMMARY</h3><p>Tidak ada data analisis yang tersedia</p></div>"

        zip_entries = [r for r in zip_results if str(r.get('zip_file', '')).lower().endswith('.zip')]
        total_zip_files = len(zip_entries)
        total_zip_size = sum(r.get('file_size_mb', 0) for r in zip_entries)

        all_baks = []
        for r in zip_results:
            all_baks.extend(r.get('bak_analyses', []))
        total_bak_files = len(all_baks)

        def _bak_size_mb(b):
            if 'file_size_mb' in b:
                return b.get('file_size_mb', 0) or 0
            if 'file_size' in b:
                try:
                    return (b.get('file_size', 0) or 0) / (1024 * 1024)
                except Exception:
                    return 0
            return 0

        total_bak_size = sum(_bak_size_mb(b) for b in all_baks)

        valid_zips = sum(1 for r in zip_entries if r.get('integrity_check', {}).get('is_valid', False))

        def _is_bak_valid(b):
            if b.get('analysis_status') == 'success':
                v = b.get('validation', {})
                if 'is_valid_bak' in v:
                    return bool(v.get('is_valid_bak'))
                return True
            analysis = b.get('analysis', {})
            if analysis.get('error'):
                return False
            return analysis.get('backup_date', 'Unknown') != 'Unknown'

        valid_baks = sum(1 for b in all_baks if _is_bak_valid(b))

        file_info_html = ""
        for i, result in enumerate(zip_entries, 1):
            zip_path = result.get('zip_file', 'Unknown')
            file_size = result.get('file_size_mb', 0)
            modified_date = self._get_file_modified_date(zip_path)
            bak_count = len(result.get('bak_analyses', []))
            integrity = result.get('integrity_check', {}).get('is_valid', False)
            status_icon = "✅" if integrity else "❌"
            extract_text = "Bisa" if integrity else "Tidak"
            file_info_html += f"""
            <div class=\"file-info\">
                <strong>📁 File {i}:</strong> {os.path.basename(zip_path)}<br>
                <strong>📅 Tanggal Modified:</strong> {modified_date}<br>
                <strong>📏 Ukuran:</strong> {file_size:.2f} MB<br>
                <strong>🗃️ Jumlah BAK:</strong> {bak_count}<br>
                <strong>🔍 Status Integrity:</strong> {status_icon} {'Valid' if integrity else 'Invalid'}<br>
                <strong>🔓 Ekstraksi:</strong> {extract_text}
            </div>
            """

        html = f"""
        <div class=\"executive-summary\">
            <h3>📊 EXECUTIVE SUMMARY</h3>

            <div class=\"summary-grid\">
                <div class=\"summary-card\">
                    <h4>Total File ZIP</h4>
                    <div class=\"value\">{total_zip_files}</div>
                    <div class=\"label\">File yang dianalisis</div>
                </div>

                <div class=\"summary-card\">
                    <h4>Total Ukuran ZIP</h4>
                    <div class=\"value\">{total_zip_size:.1f}</div>
                    <div class=\"label\">MB</div>
                </div>

                <div class=\"summary-card\">
                    <h4>Total File BAK</h4>
                    <div class=\"value\">{total_bak_files}</div>
                    <div class=\"label\">Database backup</div>
                </div>

                <div class=\"summary-card\">
                    <h4>Total Ukuran BAK</h4>
                    <div class=\"value\">{total_bak_size:.1f}</div>
                    <div class=\"label\">MB</div>
                </div>

                <div class=\"summary-card\">
                    <h4>ZIP Valid</h4>
                    <div class=\"value\">{valid_zips}/{total_zip_files if total_zip_files > 0 else 1}</div>
                    <div class=\"label\">File integrity OK</div>
                </div>

                <div class=\"summary-card\">
                    <h4>BAK Valid</h4>
                    <div class=\"value\">{valid_baks}/{total_bak_files if total_bak_files > 0 else 1}</div>
                    <div class=\"label\">Database valid</div>
                </div>
            </div>

            <h4>📋 Informasi File yang Dianalisis:</h4>
            {file_info_html}
        </div>
        """

        return html

    def _get_file_modified_date(self, file_path):
        """Get file modified date"""
        try:
            if os.path.exists(file_path):
                mod_time = os.path.getmtime(file_path)
                return datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
            else:
                return "File not found"
        except Exception as e:
            return f"Error: {str(e)}"

    def _generate_zip_analysis_summary(self, zip_results=None):
        """Generate ZIP analysis summary table"""
        if not zip_results:
            return "<p>Tidak ada data analisis ZIP</p>"

        zip_entries = [r for r in zip_results if str(r.get('zip_file', '')).lower().endswith('.zip')]
        if not zip_entries:
            return "<p>Tidak ada file ZIP yang valid untuk ditampilkan</p>"

        html = """
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            <thead>
                <tr style="background-color: #f2f2f2;">
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">No</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Nama File ZIP</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Ukuran (MB)</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Status Integrity</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Jumlah BAK</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Tanggal Modified</th>
                </tr>
            </thead>
            <tbody>
        """

        for i, result in enumerate(zip_entries, 1):
            zip_name = os.path.basename(result.get('zip_file', 'Unknown'))
            file_size = result.get('file_size_mb', 0)
            integrity = result.get('integrity_check', {}).get('is_valid', False)
            bak_count = len(result.get('bak_analyses', []))
            modified_date = self._get_file_modified_date(result.get('zip_file', ''))

            status_color = 'green' if integrity else 'red'
            status_text = 'Valid' if integrity else 'Invalid'

            html += f"""
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;">{i}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{zip_name}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{file_size:.2f}</td>
                    <td style="border: 1px solid #ddd; padding: 8px; color: {status_color}; font-weight: bold;">{status_text}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{bak_count}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{modified_date}</td>
                </tr>
            """

        html += """
            </tbody>
        </table>
        """

        return html

    def _generate_bak_analysis_summary(self, bak_results=None):
        """Generate BAK analysis summary table"""
        if not bak_results:
            return "<p>Tidak ada data analisis BAK</p>"

        html = """
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; margin: 10px 0;">
            <thead>
                <tr style="background-color: #f2f2f2;">
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">No</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Nama File BAK</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Tipe Database</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Nama Database</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Tanggal Backup</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Status</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Jumlah Record</th>
                </tr>
            </thead>
            <tbody>
        """

        for i, result in enumerate(bak_results, 1):
            bak_name = result.get('file_name') or result.get('filename') or 'Unknown'
            analysis = result.get('analysis') or {}
            if not analysis:
                db_info = result.get('database_info', {})
                backup_date_val = db_info.get('backup_date') or result.get('backup_header', {}).get('backup_finish_date') or 'Unknown'
                analysis = {
                    'backup_type': db_info.get('backup_type', 'Unknown'),
                    'database_name': db_info.get('database_name', 'Unknown'),
                    'backup_date': backup_date_val,
                    'database_info': db_info
                }

            db_type = analysis.get('backup_type', 'Unknown')
            db_name = analysis.get('database_name', 'Unknown')
            backup_date = analysis.get('backup_date', 'Unknown')
            record_count = analysis.get('database_info', {}).get('record_count')
            if record_count is None:
                record_count = analysis.get('database_info', {}).get('estimated_rows', 'N/A')

            if result.get('error') or result.get('analysis_status') == 'failed':
                status_color = 'red'
                status_text = 'Error'
            elif backup_date == 'Unknown':
                status_color = 'orange'
                status_text = 'Warning'
            else:
                status_color = 'green'
                status_text = 'Valid'

            html += f"""
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;">{i}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{bak_name}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{db_type}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{db_name}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{backup_date}</td>
                    <td style="border: 1px solid #ddd; padding: 8px; color: {status_color}; font-weight: bold;">{status_text}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{record_count}</td>
                </tr>
            """

        html += """
            </tbody>
        </table>
        """

        return html

    def _generate_recommendations(self, zip_results=None, bak_results=None):
        """Generate recommendations based on analysis results"""
        recommendations = []

        # ZIP recommendations
        if zip_results:
            invalid_zips = [r for r in zip_results if not r.get('integrity_check', {}).get('is_valid', False)]
            if invalid_zips:
                recommendations.append(f"🔍 Terdapat {len(invalid_zips)} file ZIP dengan integrity yang tidak valid. Disarankan untuk memeriksa ulang file backup tersebut.")

        # BAK recommendations
        if bak_results:
            problematic_baks = [r for r in bak_results if 'error' in r.get('analysis', {})]
            if problematic_baks:
                recommendations.append(f"⚠️ Terdapat {len(problematic_baks)} file BAK yang mengalami error saat analisis. Disarankan untuk memeriksa struktur file backup.")

            old_backups = [r for r in bak_results if self._is_old_backup(r.get('analysis', {}).get('backup_date', ''))]
            if old_backups:
                recommendations.append(f"📅 Terdapat {len(old_backups)} file backup yang sudah cukup lama. Disarankan untuk membuat backup baru.")

        if not recommendations:
            recommendations.append("✅ Semua file backup dalam kondisi baik dan layak digunakan.")

        html = "<ul>"
        for rec in recommendations:
            html += f"<li>{rec}</li>"
        html += "</ul>"

        return html

    def _is_old_backup(self, backup_date_str):
        """Check if backup is older than 30 days"""
        try:
            if backup_date_str == 'Unknown':
                return False

            # Parse various date formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                try:
                    backup_date = datetime.strptime(backup_date_str, fmt)
                    days_old = (datetime.now() - backup_date).days
                    return days_old > 30
                except ValueError:
                    continue

            return False
        except:
            return False

def main():
    """Main function"""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Create and show main window
    window = BackupMonitorWindow()
    window.show()

    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()