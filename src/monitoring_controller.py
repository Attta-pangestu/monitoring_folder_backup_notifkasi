#!/usr/bin/env python3
"""
Monitoring Controller Module
Modul pengontrol untuk koordinasi monitoring backup dan validasi database
"""

import os
import glob
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import re
from pathlib import Path

from zip_validator import ZipValidator
from database_validator import DatabaseValidator

class MonitoringController:
    def __init__(self):
        self.zip_validator = ZipValidator()
        self.database_validator = DatabaseValidator()
        self.monitoring_results = {}
    
    def monitor_backup_folder(self, folder_path: str, days_to_check: int = 7) -> Dict:
        """
        Monitor backup folder untuk validasi ZIP files dan database
        
        Args:
            folder_path: Path ke folder yang berisi ZIP files
            days_to_check: Jumlah hari ke belakang untuk mencari ZIP files terbaru
        
        Returns:
            Dictionary dengan hasil monitoring lengkap
        """
        monitoring_result = {
            'monitoring_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'folder_path': folder_path,
            'days_checked': days_to_check,
            'zip_files_found': [],
            'zip_validation_results': {},
            'database_validation_results': {},
            'date_comparison_results': {},
            'overall_summary': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # Step 1: Find recent ZIP files
            recent_zip_files = self._find_recent_zip_files(folder_path, days_to_check)
            monitoring_result['zip_files_found'] = recent_zip_files
            
            if not recent_zip_files:
                monitoring_result['warnings'].append(f"Tidak ditemukan ZIP files dalam {days_to_check} hari terakhir di folder {folder_path}")
                return monitoring_result
            
            # Step 2: Validate ZIP files
            zip_validation = self.zip_validator.validate_multiple_zip_files(recent_zip_files)
            monitoring_result['zip_validation_results'] = zip_validation
            
            # Step 3: Validate databases within ZIP files
            database_validation = self.database_validator.validate_backup_databases(recent_zip_files)
            monitoring_result['database_validation_results'] = database_validation
            
            # Step 4: Compare dates between ZIP files and database records
            date_comparison = self._compare_zip_and_database_dates(
                zip_validation, database_validation
            )
            monitoring_result['date_comparison_results'] = date_comparison
            
            # Step 5: Generate overall summary
            overall_summary = self._generate_overall_summary(
                monitoring_result
            )
            monitoring_result['overall_summary'] = overall_summary
            
            # Collect errors and warnings
            monitoring_result['errors'].extend(zip_validation.get('errors', []))
            monitoring_result['errors'].extend(database_validation.get('errors', []))
            monitoring_result['warnings'].extend(zip_validation.get('warnings', []))
            monitoring_result['warnings'].extend(database_validation.get('warnings', []))
            
        except Exception as e:
            monitoring_result['errors'].append(f"Error dalam monitoring folder: {str(e)}")
        
        # Store results for later reference
        self.monitoring_results[folder_path] = monitoring_result
        
        return monitoring_result
    
    def _find_recent_zip_files(self, folder_path: str, days: int) -> List[str]:
        """Find ZIP files from recent days"""
        if not os.path.exists(folder_path):
            return []
        
        zip_files = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Find all ZIP files in folder
        zip_pattern = os.path.join(folder_path, "*.zip")
        all_zip_files = glob.glob(zip_pattern)
        
        for zip_file in all_zip_files:
            try:
                # Check modification time
                mod_time = datetime.fromtimestamp(os.path.getmtime(zip_file))
                
                # Also try to extract date from filename
                filename_date = self._extract_date_from_filename(os.path.basename(zip_file))
                
                # Use the more recent date
                file_date = max(mod_time, filename_date) if filename_date else mod_time
                
                if file_date >= cutoff_date:
                    zip_files.append(zip_file)
            
            except Exception as e:
                continue
        
        # Sort by date (newest first)
        zip_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        return zip_files
    
    def _extract_date_from_filename(self, filename: str) -> Optional[datetime]:
        """Extract date from filename using various patterns"""
        # Common date patterns in filenames
        patterns = [
            r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
            r'(\d{4})(\d{2})(\d{2})',    # YYYYMMDD
            r'(\d{2})-(\d{2})-(\d{4})',  # DD-MM-YYYY
            r'(\d{2})(\d{2})(\d{4})',    # DDMMYYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-M-D
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 3:
                        # Determine if it's YYYY-MM-DD or DD-MM-YYYY format
                        if len(groups[0]) == 4:  # YYYY-MM-DD
                            year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                        else:  # DD-MM-YYYY
                            day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                        
                        return datetime(year, month, day)
                except ValueError:
                    continue
        
        return None
    
    def _compare_zip_and_database_dates(self, zip_validation: Dict, database_validation: Dict) -> Dict:
        """Compare dates between ZIP files and database records"""
        comparison_result = {
            'comparison_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'database_comparisons': {},
            'sync_status': {},
            'date_gaps': {},
            'recommendations': []
        }
        
        # Get latest dates from database validation
        db_latest_dates = database_validation.get('latest_dates', {})
        
        # Get ZIP file dates
        zip_file_dates = {}
        for zip_info in zip_validation.get('validation_results', []):
            zip_file = zip_info.get('zip_file', '')
            zip_date = zip_info.get('file_date', '')
            if zip_file and zip_date:
                zip_file_dates[zip_file] = zip_date
        
        # Compare each database type
        for db_type, db_latest_date in db_latest_dates.items():
            comparison_result['database_comparisons'][db_type] = {
                'database_latest_date': db_latest_date,
                'zip_files_with_this_db': [],
                'date_analysis': {}
            }
            
            # Find ZIP files containing this database type
            db_entries = database_validation.get('databases_found', {}).get(db_type, [])
            
            for db_entry in db_entries:
                zip_file = db_entry.get('zip_file', '')
                zip_path = db_entry.get('zip_path', '')
                
                if zip_file:
                    # Get ZIP file date
                    zip_date = None
                    for zip_info in zip_validation.get('validation_results', []):
                        if zip_info.get('zip_file') == zip_file:
                            zip_date = zip_info.get('file_date')
                            break
                    
                    zip_entry = {
                        'zip_file': zip_file,
                        'zip_date': zip_date,
                        'database_info': db_entry.get('database_info', {})
                    }
                    
                    comparison_result['database_comparisons'][db_type]['zip_files_with_this_db'].append(zip_entry)
            
            # Analyze date synchronization
            sync_analysis = self._analyze_date_synchronization(db_type, db_latest_date, 
                comparison_result['database_comparisons'][db_type]['zip_files_with_this_db'])
            
            comparison_result['sync_status'][db_type] = sync_analysis['sync_status']
            comparison_result['date_gaps'][db_type] = sync_analysis['date_gap_days']
            comparison_result['database_comparisons'][db_type]['date_analysis'] = sync_analysis
            
            # Add recommendations
            if sync_analysis['recommendations']:
                comparison_result['recommendations'].extend(sync_analysis['recommendations'])
        
        return comparison_result
    
    def _analyze_date_synchronization(self, db_type: str, db_latest_date: str, zip_entries: List[Dict]) -> Dict:
        """Analyze synchronization between database dates and ZIP file dates"""
        analysis = {
            'sync_status': 'unknown',
            'date_gap_days': None,
            'latest_zip_date': None,
            'database_date': db_latest_date,
            'recommendations': []
        }
        
        try:
            # Parse database date
            db_date = datetime.strptime(db_latest_date[:10], '%Y-%m-%d')
            
            # Find latest ZIP date for this database type
            latest_zip_date = None
            for zip_entry in zip_entries:
                zip_date_str = zip_entry.get('zip_date')
                if zip_date_str:
                    try:
                        zip_date = datetime.strptime(zip_date_str[:10], '%Y-%m-%d')
                        if not latest_zip_date or zip_date > latest_zip_date:
                            latest_zip_date = zip_date
                    except:
                        continue
            
            if latest_zip_date:
                analysis['latest_zip_date'] = latest_zip_date.strftime('%Y-%m-%d')
                
                # Calculate date gap
                date_gap = (latest_zip_date - db_date).days
                analysis['date_gap_days'] = date_gap
                
                # Determine sync status
                if abs(date_gap) <= 1:
                    analysis['sync_status'] = 'excellent'
                elif abs(date_gap) <= 3:
                    analysis['sync_status'] = 'good'
                elif abs(date_gap) <= 7:
                    analysis['sync_status'] = 'warning'
                else:
                    analysis['sync_status'] = 'critical'
                
                # Generate recommendations
                if date_gap > 7:
                    analysis['recommendations'].append(
                        f"{db_type.upper()}: ZIP backup lebih baru {date_gap} hari dari data database terakhir"
                    )
                elif date_gap < -7:
                    analysis['recommendations'].append(
                        f"{db_type.upper()}: Data database lebih baru {abs(date_gap)} hari dari ZIP backup terakhir"
                    )
                elif analysis['sync_status'] == 'warning':
                    analysis['recommendations'].append(
                        f"{db_type.upper()}: Selisih tanggal {abs(date_gap)} hari, pertimbangkan backup yang lebih sering"
                    )
            else:
                analysis['sync_status'] = 'no_zip_date'
                analysis['recommendations'].append(
                    f"{db_type.upper()}: Tidak dapat menentukan tanggal ZIP file untuk perbandingan"
                )
        
        except Exception as e:
            analysis['sync_status'] = 'error'
            analysis['recommendations'].append(
                f"{db_type.upper()}: Error dalam analisis tanggal: {str(e)}"
            )
        
        return analysis
    
    def _generate_overall_summary(self, monitoring_result: Dict) -> Dict:
        """Generate overall monitoring summary"""
        summary = {
            'monitoring_status': 'success',
            'total_zip_files': len(monitoring_result['zip_files_found']),
            'databases_found': [],
            'overall_health': 'unknown',
            'critical_issues': [],
            'warnings': [],
            'recommendations': [],
            'next_actions': []
        }
        
        # Get database types found
        db_validation = monitoring_result.get('database_validation_results', {})
        summary['databases_found'] = list(db_validation.get('databases_found', {}).keys())
        
        # Analyze overall health
        date_comparison = monitoring_result.get('date_comparison_results', {})
        sync_statuses = date_comparison.get('sync_status', {})
        
        if sync_statuses:
            # Determine overall health based on sync statuses
            status_priority = {'excellent': 4, 'good': 3, 'warning': 2, 'critical': 1, 'unknown': 0}
            min_status = min(sync_statuses.values(), key=lambda x: status_priority.get(x, 0))
            summary['overall_health'] = min_status
        
        # Collect critical issues
        for db_type, status in sync_statuses.items():
            if status == 'critical':
                summary['critical_issues'].append(f"Database {db_type.upper()} memiliki masalah sinkronisasi kritis")
        
        # Collect all errors as critical issues
        all_errors = monitoring_result.get('errors', [])
        summary['critical_issues'].extend(all_errors)
        
        # Collect warnings
        all_warnings = monitoring_result.get('warnings', [])
        summary['warnings'].extend(all_warnings)
        
        # Collect recommendations
        zip_validation = monitoring_result.get('zip_validation_results', {})
        db_validation = monitoring_result.get('database_validation_results', {})
        date_comparison = monitoring_result.get('date_comparison_results', {})
        
        # From validation summaries
        if 'validation_summary' in zip_validation:
            summary['recommendations'].extend(zip_validation['validation_summary'].get('recommendations', []))
        
        if 'validation_summary' in db_validation:
            summary['recommendations'].extend(db_validation['validation_summary'].get('recommendations', []))
        
        # From date comparison
        summary['recommendations'].extend(date_comparison.get('recommendations', []))
        
        # Generate next actions
        if summary['critical_issues']:
            summary['next_actions'].append("Segera perbaiki masalah kritis yang ditemukan")
        
        if summary['overall_health'] in ['warning', 'critical']:
            summary['next_actions'].append("Periksa dan perbaiki sinkronisasi backup database")
        
        if not summary['databases_found']:
            summary['next_actions'].append("Periksa kembali folder backup, tidak ditemukan database yang valid")
        
        # Set monitoring status
        if summary['critical_issues']:
            summary['monitoring_status'] = 'critical'
        elif summary['warnings'] or summary['overall_health'] == 'warning':
            summary['monitoring_status'] = 'warning'
        else:
            summary['monitoring_status'] = 'success'
        
        return summary
    
    def generate_monitoring_report(self, monitoring_result: Dict) -> str:
        """Generate detailed monitoring report"""
        report = []
        report.append("=" * 70)
        report.append("BACKUP FOLDER MONITORING REPORT")
        report.append("=" * 70)
        report.append(f"Monitoring Time: {monitoring_result['monitoring_timestamp']}")
        report.append(f"Folder Path: {monitoring_result['folder_path']}")
        report.append(f"Days Checked: {monitoring_result['days_checked']}")
        report.append("")
        
        # Overall Summary
        overall_summary = monitoring_result.get('overall_summary', {})
        report.append("OVERALL SUMMARY")
        report.append("-" * 40)
        report.append(f"Monitoring Status: {overall_summary.get('monitoring_status', 'unknown').upper()}")
        report.append(f"Overall Health: {overall_summary.get('overall_health', 'unknown').upper()}")
        report.append(f"ZIP Files Found: {overall_summary.get('total_zip_files', 0)}")
        report.append(f"Databases Found: {', '.join(overall_summary.get('databases_found', []))}")
        report.append("")
        
        # ZIP Files Found
        zip_files = monitoring_result.get('zip_files_found', [])
        if zip_files:
            report.append("ZIP FILES FOUND")
            report.append("-" * 40)
            for i, zip_file in enumerate(zip_files, 1):
                report.append(f"{i}. {os.path.basename(zip_file)}")
            report.append("")
        
        # Database Validation Summary
        db_validation = monitoring_result.get('database_validation_results', {})
        if db_validation.get('validation_summary'):
            db_summary = db_validation['validation_summary']
            report.append("DATABASE VALIDATION SUMMARY")
            report.append("-" * 40)
            
            if db_summary.get('database_health'):
                for db_type, health_info in db_summary['database_health'].items():
                    status = health_info.get('status', 'unknown').upper()
                    days_old = health_info.get('days_old', 'N/A')
                    report.append(f"{db_type.upper()}: {status} ({days_old} days old)")
            report.append("")
        
        # Date Synchronization Status
        date_comparison = monitoring_result.get('date_comparison_results', {})
        if date_comparison.get('sync_status'):
            report.append("DATE SYNCHRONIZATION STATUS")
            report.append("-" * 40)
            for db_type, sync_status in date_comparison['sync_status'].items():
                gap_days = date_comparison.get('date_gaps', {}).get(db_type, 'N/A')
                report.append(f"{db_type.upper()}: {sync_status.upper()} (Gap: {gap_days} days)")
            report.append("")
        
        # Critical Issues
        if overall_summary.get('critical_issues'):
            report.append("CRITICAL ISSUES")
            report.append("-" * 40)
            for i, issue in enumerate(overall_summary['critical_issues'], 1):
                report.append(f"{i}. {issue}")
            report.append("")
        
        # Warnings
        if overall_summary.get('warnings'):
            report.append("WARNINGS")
            report.append("-" * 40)
            for i, warning in enumerate(overall_summary['warnings'], 1):
                report.append(f"{i}. {warning}")
            report.append("")
        
        # Recommendations
        if overall_summary.get('recommendations'):
            report.append("RECOMMENDATIONS")
            report.append("-" * 40)
            for i, rec in enumerate(overall_summary['recommendations'], 1):
                report.append(f"{i}. {rec}")
            report.append("")
        
        # Next Actions
        if overall_summary.get('next_actions'):
            report.append("NEXT ACTIONS")
            report.append("-" * 40)
            for i, action in enumerate(overall_summary['next_actions'], 1):
                report.append(f"{i}. {action}")
            report.append("")
        
        report.append("=" * 70)
        
        return "\n".join(report)
    
    def get_monitoring_status_summary(self, folder_path: str) -> Dict:
        """Get quick status summary for a monitored folder"""
        if folder_path not in self.monitoring_results:
            return {'status': 'not_monitored', 'message': 'Folder belum dimonitor'}
        
        result = self.monitoring_results[folder_path]
        overall_summary = result.get('overall_summary', {})
        
        return {
            'status': overall_summary.get('monitoring_status', 'unknown'),
            'health': overall_summary.get('overall_health', 'unknown'),
            'zip_count': overall_summary.get('total_zip_files', 0),
            'databases': overall_summary.get('databases_found', []),
            'last_check': result.get('monitoring_timestamp', ''),
            'critical_count': len(overall_summary.get('critical_issues', [])),
            'warning_count': len(overall_summary.get('warnings', []))
        }