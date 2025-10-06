#!/usr/bin/env python3
"""
Enhanced ZIP Analyzer for Database Backups
Analyzer untuk file ZIP backup dengan kemampuan analisis mendalam
"""

import os
import zipfile
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import hashlib
import json

from enhanced_bak_analyzer import EnhancedBAKAnalyzer

class EnhancedZIPAnalyzer:
    def __init__(self):
        self.bak_analyzer = EnhancedBAKAnalyzer()

    def analyze_zip_comprehensive(self, zip_path: str) -> Dict[str, Any]:
        """
        Analisis komprehensif file ZIP backup database
        """
        try:
            result = {
                'zip_info': {},
                'file_analysis': {},
                'bak_analysis': {},
                'validation': {},
                'recommendations': [],
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # Step 1: ZIP Metadata Analysis
            zip_info = self._analyze_zip_metadata(zip_path)
            result['zip_info'] = zip_info

            # Step 2: ZIP Integrity Validation
            validation = self._validate_zip_integrity(zip_path)
            result['validation'] = validation

            # Step 3: File Content Analysis
            file_analysis = self._analyze_zip_contents(zip_path)
            result['file_analysis'] = file_analysis

            # Step 4: BAK File Analysis
            if file_analysis.get('bak_files'):
                bak_analysis = self._analyze_bak_files_in_zip(zip_path, file_analysis['bak_files'])
                result['bak_analysis'] = bak_analysis

            # Step 5: Generate Recommendations
            result['recommendations'] = self._generate_zip_recommendations(result)

            return result

        except Exception as e:
            return {
                'error': str(e),
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'recommendations': [f'Analisis gagal: {str(e)}']
            }

    def _analyze_zip_metadata(self, zip_path: str) -> Dict[str, Any]:
        """Analisis metadata file ZIP"""
        try:
            stat = os.stat(zip_path)
            filename = os.path.basename(zip_path)

            zip_info = {
                'filename': filename,
                'full_path': zip_path,
                'file_size': stat.st_size,
                'file_size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created_time': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                'modified_time': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'file_hash': self._calculate_file_hash(zip_path),
                'backup_date_from_filename': self._extract_date_from_filename(filename),
                'database_type_from_filename': self._extract_database_type_from_filename(filename)
            }

            # Analyze ZIP structure
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_file_list = zip_ref.namelist()

                zip_info.update({
                    'total_files': len(zip_file_list),
                    'total_compressed_size': sum(zinfo.compress_size for zinfo in zip_ref.infolist()),
                    'total_uncompressed_size': sum(zinfo.file_size for zinfo in zip_ref.infolist()),
                    'compression_ratio': self._calculate_compression_ratio(zip_ref),
                    'file_types': self._analyze_file_types(zip_file_list),
                    'directory_structure': self._analyze_directory_structure(zip_file_list)
                })

            return zip_info

        except Exception as e:
            return {'error': str(e)}

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return "Hash calculation failed"

    def _extract_date_from_filename(self, filename: str) -> str:
        """Extract date from filename"""
        import re

        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{4}\d{2}\d{2})',
            r'(\d{2}-\d{2}-\d{4})',
            r'(\d{2}/\d{2}/\d{4})'
        ]

        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                date_str = match.group(1)
                # Normalize date format
                if len(date_str) == 8 and date_str.isdigit():  # YYYYMMDD
                    date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                return date_str

        return "Unknown"

    def _extract_database_type_from_filename(self, filename: str) -> str:
        """Extract database type from filename"""
        filename_lower = filename.lower()

        if 'backupstaging' in filename_lower:
            return 'BackupStaging'
        elif 'backupvenus' in filename_lower:
            return 'BackupVenuz'
        elif 'staging' in filename_lower:
            return 'Staging'
        elif 'venus' in filename_lower or 'hr' in filename_lower:
            return 'Venus'
        elif 'plantware' in filename_lower or 'ptrj' in filename_lower:
            return 'Plantware'
        else:
            return 'Unknown'

    def _calculate_compression_ratio(self, zip_ref: zipfile.ZipFile) -> float:
        """Calculate ZIP compression ratio"""
        try:
            total_compressed = sum(zinfo.compress_size for zinfo in zip_ref.infolist())
            total_uncompressed = sum(zinfo.file_size for zinfo in zip_ref.infolist())

            if total_uncompressed > 0:
                return round((1 - total_compressed / total_uncompressed) * 100, 2)
            return 0.0
        except:
            return 0.0

    def _analyze_file_types(self, file_list: List[str]) -> Dict[str, int]:
        """Analyze file types in ZIP"""
        file_types = {}

        for file_path in file_list:
            if not file_path.endswith('/'):  # Skip directories
                ext = os.path.splitext(file_path)[1].lower()
                if ext:
                    file_types[ext] = file_types.get(ext, 0) + 1
                else:
                    file_types['no_extension'] = file_types.get('no_extension', 0) + 1

        return file_types

    def _analyze_directory_structure(self, file_list: List[str]) -> Dict[str, Any]:
        """Analyze directory structure in ZIP"""
        directories = set()
        max_depth = 0

        for file_path in file_list:
            depth = file_path.count('/')
            max_depth = max(max_depth, depth)

            # Extract directories
            path_parts = file_path.split('/')
            for i in range(len(path_parts) - 1):
                dir_path = '/'.join(path_parts[:i+1]) + '/'
                directories.add(dir_path)

        return {
            'total_directories': len(directories),
            'max_depth': max_depth,
            'directory_list': sorted(list(directories))[:20]  # Show first 20
        }

    def _validate_zip_integrity(self, zip_path: str) -> Dict[str, Any]:
        """Validate ZIP file integrity"""
        validation = {
            'is_valid_zip': False,
            'can_be_extracted': True,
            'corruption_detected': False,
            'warnings': [],
            'file_integrity': 'Good'
        }

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Test ZIP integrity
                try:
                    test_result = zip_ref.testzip()
                    if test_result is not None:
                        validation['corruption_detected'] = True
                        validation['warnings'].append(f"Corrupted file: {test_result}")
                        validation['can_be_extracted'] = False
                    else:
                        validation['is_valid_zip'] = True
                except Exception as e:
                    validation['corruption_detected'] = True
                    validation['warnings'].append(f"ZIP test failed: {str(e)}")
                    validation['can_be_extracted'] = False

                # Check all files can be read
                try:
                    for zinfo in zip_ref.infolist():
                        with zip_ref.open(zinfo.filename) as f:
                            f.read(1024)  # Try to read first 1KB
                except Exception as e:
                    validation['warnings'].append(f"Cannot read some files: {str(e)}")
                    validation['can_be_extracted'] = False

            # Determine overall integrity
            if validation['corruption_detected']:
                validation['file_integrity'] = 'Corrupted'
            elif validation['warnings']:
                validation['file_integrity'] = 'Warnings'
            else:
                validation['file_integrity'] = 'Good'

        except zipfile.BadZipFile:
            validation['is_valid_zip'] = False
            validation['corruption_detected'] = True
            validation['warnings'].append("Not a valid ZIP file")
            validation['file_integrity'] = 'Invalid'
        except Exception as e:
            validation['warnings'].append(f"Validation error: {str(e)}")
            validation['file_integrity'] = 'Error'

        return validation

    def _analyze_zip_contents(self, zip_path: str) -> Dict[str, Any]:
        """Analyze ZIP file contents"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()

                analysis = {
                    'total_files': len(file_list),
                    'bak_files': [],
                    'database_files': [],
                    'log_files': [],
                    'other_files': [],
                    'largest_files': [],
                    'file_details': {}
                }

                # Categorize files
                for zinfo in zip_ref.infolist():
                    if zinfo.filename.endswith('/'):
                        continue  # Skip directories

                    file_detail = {
                        'filename': zinfo.filename,
                        'size_bytes': zinfo.file_size,
                        'size_mb': round(zinfo.file_size / (1024 * 1024), 2),
                        'compressed_size': zinfo.compress_size,
                        'compression_ratio': round((1 - zinfo.compress_size / zinfo.file_size) * 100, 2) if zinfo.file_size > 0 else 0,
                        'date_time': datetime(*zinfo.date_time).strftime('%Y-%m-%d %H:%M:%S'),
                        'file_type': 'unknown'
                    }

                    # Determine file type
                    ext = os.path.splitext(zinfo.filename)[1].lower()
                    if ext == '.bak':
                        file_detail['file_type'] = 'database_backup'
                        analysis['bak_files'].append(file_detail)
                    elif ext in ['.mdf', '.ndf', '.ldf']:
                        file_detail['file_type'] = 'database_file'
                        analysis['database_files'].append(file_detail)
                    elif ext in ['.log', '.txt']:
                        file_detail['file_type'] = 'log_file'
                        analysis['log_files'].append(file_detail)
                    else:
                        analysis['other_files'].append(file_detail)

                    analysis['file_details'][zinfo.filename] = file_detail

                # Find largest files
                all_files = analysis['bak_files'] + analysis['database_files'] + analysis['other_files']
                analysis['largest_files'] = sorted(all_files, key=lambda x: x['size_bytes'], reverse=True)[:10]

                return analysis

        except Exception as e:
            return {'error': str(e)}

    def _analyze_bak_files_in_zip(self, zip_path: str, bak_files: List[Dict]) -> Dict[str, Any]:
        """Analyze BAK files within ZIP"""
        bak_analysis = {
            'total_bak_files': len(bak_files),
            'bak_analyses': [],
            'summary': {
                'total_size_mb': sum(bf['size_mb'] for bf in bak_files),
                'databases_found': [],
                'valid_bak_files': 0,
                'corrupted_bak_files': 0
            }
        }

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for bak_file in bak_files:
                    try:
                        # Analyze each BAK file
                        analysis = self.bak_analyzer.analyze_bak_file_comprehensive(
                            bak_file['filename'], zip_ref
                        )
                        analysis['original_filename'] = bak_file['filename']
                        bak_analysis['bak_analyses'].append(analysis)

                        # Update summary
                        if analysis.get('analysis_status') == 'success':
                            bak_analysis['summary']['valid_bak_files'] += 1

                            db_name = analysis.get('database_info', {}).get('database_name', 'Unknown')
                            if db_name not in bak_analysis['summary']['databases_found']:
                                bak_analysis['summary']['databases_found'].append(db_name)
                        else:
                            bak_analysis['summary']['corrupted_bak_files'] += 1

                    except Exception as e:
                        bak_analysis['bak_analyses'].append({
                            'filename': bak_file['filename'],
                            'analysis_status': 'failed',
                            'error': str(e)
                        })
                        bak_analysis['summary']['corrupted_bak_files'] += 1

        except Exception as e:
            bak_analysis['error'] = str(e)

        return bak_analysis

    def _generate_zip_recommendations(self, analysis_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on ZIP analysis"""
        recommendations = []

        # Check validation results
        validation = analysis_result.get('validation', {})
        if not validation.get('is_valid_zip', False):
            recommendations.append("⚠️ File ZIP tidak valid - mungkin korupsi")

        if validation.get('corruption_detected'):
            recommendations.append("⚠️ Korupsi file ZIP terdeteksi - beberapa file mungkin tidak bisa diekstrak")

        if not validation.get('can_be_extracted', True):
            recommendations.append("⚠️ File ZIP tidak dapat diekstrak sepenuhnya")

        # Check BAK analysis
        bak_analysis = analysis_result.get('bak_analysis', {})
        if bak_analysis.get('total_bak_files', 0) == 0:
            recommendations.append("ℹ️ Tidak ada file BAK ditemukan dalam ZIP")
        else:
            summary = bak_analysis.get('summary', {})
            if summary.get('corrupted_bak_files', 0) > 0:
                recommendations.append(f"⚠️ {summary['corrupted_bak_files']} file BAK korupti ditemukan")

            if summary.get('valid_bak_files', 0) == 0:
                recommendations.append("⚠️ Tidak ada file BAK valid yang dapat dianalisis")

        # Check file size
        zip_info = analysis_result.get('zip_info', {})
        if zip_info.get('file_size_mb', 0) > 1000:  # > 1GB
            recommendations.append("ℹ️ File ZIP besar - pastikan ruang disk cukup untuk ekstraksi")

        # Check compression
        zip_info = analysis_result.get('zip_info', {})
        compression_ratio = zip_info.get('compression_ratio', 0)
        if compression_ratio < 10:
            recommendations.append("ℹ️ Rasio kompresi rendah - backup mungkin tidak terkompresi dengan baik")
        elif compression_ratio > 80:
            recommendations.append("✅ Rasio kompresi sangat baik")

        # Check backup date
        backup_date = zip_info.get('backup_date_from_filename')
        if backup_date != "Unknown":
            try:
                backup_dt = datetime.strptime(backup_date, '%Y-%m-%d')
                age_days = (datetime.now() - backup_dt).days
                if age_days > 30:
                    recommendations.append(f"ℹ️ Backup sudah {age_days} hari - pertimbangkan backup yang lebih baru")
            except:
                pass

        # Positive recommendations
        if validation.get('file_integrity') == 'Good':
            recommendations.append("✅ File ZIP dalam kondisi baik dan lengkap")

        if bak_analysis.get('summary', {}).get('valid_bak_files', 0) > 0:
            recommendations.append("✅ File BAK valid ditemukan dan siap untuk restore")

        return recommendations

    def generate_zip_summary_report(self, zip_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary report for ZIP analysis"""
        zip_info = zip_analysis.get('zip_info', {})
        validation = zip_analysis.get('validation', {})
        bak_analysis = zip_analysis.get('bak_analysis', {})

        report = {
            'filename': zip_info.get('filename', 'Unknown'),
            'file_size_mb': zip_info.get('file_size_mb', 0),
            'backup_date': zip_info.get('backup_date_from_filename', 'Unknown'),
            'analysis_time': zip_analysis.get('analysis_time', 'Unknown'),
            'zip_status': validation.get('file_integrity', 'Unknown'),
            'can_be_extracted': validation.get('can_be_extracted', False),
            'bak_files_count': bak_analysis.get('total_bak_files', 0),
            'databases_found': bak_analysis.get('summary', {}).get('databases_found', []),
            'recommendations': zip_analysis.get('recommendations', [])
        }

        return report