#!/usr/bin/env python3
"""
Database Validator Module

This module provides enhanced database validation capabilities for ZIP files
containing database backups. It can analyze Plantware, Venus, and Staging databases.
"""

import os
import sqlite3
import zipfile
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

from zip_validator import ZipValidator

class DatabaseValidator:
    def __init__(self):
        self.supported_databases = ['plantware', 'venus', 'staging']
        self.temp_connections = {}
    
    def validate_backup_databases(self, zip_files: List[str]) -> Dict:
        """
        Validasi database dari multiple ZIP files
        Returns: Dictionary dengan hasil validasi lengkap
        """
        results = {
            'validation_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_zip_files': len(zip_files),
            'databases_found': {},
            'latest_dates': {},
            'validation_summary': {},
            'errors': [],
            'warnings': []
        }
        
        for zip_file in zip_files:
            try:
                zip_result = self._validate_single_zip(zip_file)
                
                # Merge results
                for db_type, db_info in zip_result.get('databases', {}).items():
                    if db_type not in results['databases_found']:
                        results['databases_found'][db_type] = []
                    results['databases_found'][db_type].append({
                        'zip_file': os.path.basename(zip_file),
                        'zip_path': zip_file,
                        'database_info': db_info
                    })
                
                # Track latest dates
                for db_type, latest_date in zip_result.get('latest_dates', {}).items():
                    if db_type not in results['latest_dates'] or latest_date > results['latest_dates'].get(db_type, ''):
                        results['latest_dates'][db_type] = latest_date
                
                # Collect errors and warnings
                results['errors'].extend(zip_result.get('errors', []))
                results['warnings'].extend(zip_result.get('warnings', []))
                
            except Exception as e:
                results['errors'].append(f"Error processing {zip_file}: {str(e)}")
        
        # Generate validation summary
        results['validation_summary'] = self._generate_validation_summary(results)
        
        return results
    
    def _validate_single_zip(self, zip_path: str) -> Dict:
        """Validasi single ZIP file"""
        result = {
            'zip_file': os.path.basename(zip_path),
            'databases': {},
            'latest_dates': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Find .bak files
                bak_files = [f for f in zip_ref.namelist() if f.lower().endswith('.bak')]
                
                if not bak_files:
                    result['warnings'].append(f"No .bak files found in {zip_path}")
                    return result
                
                # Analyze each .bak file
                with tempfile.TemporaryDirectory() as temp_dir:
                    for bak_file in bak_files:
                        try:
                            # Extract .bak file
                            zip_ref.extract(bak_file, temp_dir)
                            bak_path = os.path.join(temp_dir, bak_file)
                            
                            # Analyze database
                            db_analysis = self._analyze_database(bak_path)
                            
                            if db_analysis['database_type'] != 'unknown':
                                result['databases'][db_analysis['database_type']] = db_analysis
                                
                                # Track latest date for this database type
                                latest_date = self._get_database_latest_date(db_analysis)
                                if latest_date:
                                    result['latest_dates'][db_analysis['database_type']] = latest_date
                            
                        except Exception as e:
                            result['errors'].append(f"Error analyzing {bak_file}: {str(e)}")
        
        except Exception as e:
            result['errors'].append(f"Error processing ZIP {zip_path}: {str(e)}")
        
        return result
    
    def _analyze_database(self, bak_path: str) -> Dict:
        """Analyze database file"""
        analysis = {
            'database_type': 'unknown',
            'file_path': bak_path,
            'file_size_mb': round(os.path.getsize(bak_path) / (1024 * 1024), 2),
            'tables': [],
            'key_tables_info': {},
            'latest_dates': {},
            'record_counts': {},
            'errors': []
        }
        
        try:
            conn = sqlite3.connect(bak_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            analysis['tables'] = tables
            
            # Detect database type
            analysis['database_type'] = self._detect_database_type(tables)
            
            # Analyze based on database type
            if analysis['database_type'] == 'plantware':
                analysis['key_tables_info'] = self._analyze_plantware_database(cursor)
            elif analysis['database_type'] == 'venus':
                analysis['key_tables_info'] = self._analyze_venus_database(cursor)
            elif analysis['database_type'] == 'staging':
                analysis['key_tables_info'] = self._analyze_staging_database(cursor)
            
            conn.close()
            
        except Exception as e:
            analysis['errors'].append(f"Database analysis error: {str(e)}")
        
        return analysis
    
    def _detect_database_type(self, tables: List[str]) -> str:
        """Detect database type based on table names"""
        table_names_upper = [t.upper() for t in tables]
        
        # Check for Plantware specific tables
        plantware_indicators = ['PR_TASKREG', 'PR_TASK', 'PR_PROJECT']
        if any(indicator in table_names_upper for indicator in plantware_indicators):
            return 'plantware'
        
        # Check for Venus specific tables
        venus_indicators = ['TA_MACHINE', 'TA_TRANSACTION', 'TA_LOG']
        if any(indicator in table_names_upper for indicator in venus_indicators):
            return 'venus'
        
        # Check for Staging specific tables
        staging_indicators = ['GWSCANNER', 'GW_LOG', 'SCANNER_DATA']
        if any(indicator in table_names_upper for indicator in staging_indicators):
            return 'staging'
        
        return 'unknown'
    
    def _analyze_plantware_database(self, cursor) -> Dict:
        """Analyze Plantware database specifically"""
        info = {}
        
        # Analyze PR_TASKREG table
        try:
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='PR_TASKREG'")
            if cursor.fetchone():
                # Get record count
                cursor.execute("SELECT COUNT(*) FROM PR_TASKREG")
                count = cursor.fetchone()[0]
                
                # Get latest dates from various columns
                date_info = self._get_table_date_info(cursor, 'PR_TASKREG', 
                    ['TASK_DATE', 'CREATED_DATE', 'MODIFIED_DATE', 'START_DATE', 'END_DATE'])
                
                # Get recent records (last 7 days)
                recent_count = self._get_recent_records_count(cursor, 'PR_TASKREG', 
                    ['TASK_DATE', 'CREATED_DATE'], days=7)
                
                info['PR_TASKREG'] = {
                    'total_records': count,
                    'latest_dates': date_info,
                    'recent_records_7days': recent_count,
                    'status': 'active' if recent_count > 0 else 'inactive'
                }
            else:
                info['PR_TASKREG'] = {'error': 'Table not found'}
        
        except Exception as e:
            info['PR_TASKREG'] = {'error': str(e)}
        
        # Analyze other Plantware tables if they exist
        other_tables = ['PR_PROJECT', 'PR_TASK', 'PR_USER']
        for table in other_tables:
            try:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if cursor.fetchone():
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    info[table] = {'total_records': count}
            except:
                pass
        
        return info
    
    def _analyze_venus_database(self, cursor) -> Dict:
        """Analyze Venus database specifically"""
        info = {}
        
        # Analyze TA_MACHINE table
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='TA_MACHINE'")
            if cursor.fetchone():
                # Get record count
                cursor.execute("SELECT COUNT(*) FROM TA_MACHINE")
                count = cursor.fetchone()[0]
                
                # Get latest dates
                date_info = self._get_table_date_info(cursor, 'TA_MACHINE', 
                    ['MACHINE_DATE', 'CREATED_DATE', 'MODIFIED_DATE', 'LAST_UPDATE', 'TIMESTAMP'])
                
                # Get recent records
                recent_count = self._get_recent_records_count(cursor, 'TA_MACHINE', 
                    ['MACHINE_DATE', 'TIMESTAMP'], days=7)
                
                info['TA_MACHINE'] = {
                    'total_records': count,
                    'latest_dates': date_info,
                    'recent_records_7days': recent_count,
                    'status': 'active' if recent_count > 0 else 'inactive'
                }
            else:
                info['TA_MACHINE'] = {'error': 'Table not found'}
        
        except Exception as e:
            info['TA_MACHINE'] = {'error': str(e)}
        
        # Analyze other Venus tables
        other_tables = ['TA_TRANSACTION', 'TA_LOG', 'TA_USER']
        for table in other_tables:
            try:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if cursor.fetchone():
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    info[table] = {'total_records': count}
            except:
                pass
        
        return info
    
    def _analyze_staging_database(self, cursor) -> Dict:
        """Analyze Staging database specifically"""
        info = {}
        
        # Analyze GWSCANNER table
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='GWSCANNER'")
            if cursor.fetchone():
                # Get record count
                cursor.execute("SELECT COUNT(*) FROM GWSCANNER")
                count = cursor.fetchone()[0]
                
                # Get latest dates
                date_info = self._get_table_date_info(cursor, 'GWSCANNER', 
                    ['SCAN_DATE', 'CREATED_DATE', 'MODIFIED_DATE', 'TIMESTAMP', 'LOG_DATE'])
                
                # Get recent records
                recent_count = self._get_recent_records_count(cursor, 'GWSCANNER', 
                    ['SCAN_DATE', 'TIMESTAMP'], days=7)
                
                info['GWSCANNER'] = {
                    'total_records': count,
                    'latest_dates': date_info,
                    'recent_records_7days': recent_count,
                    'status': 'active' if recent_count > 0 else 'inactive'
                }
            else:
                info['GWSCANNER'] = {'error': 'Table not found'}
        
        except Exception as e:
            info['GWSCANNER'] = {'error': str(e)}
        
        # Analyze other Staging tables
        other_tables = ['GW_LOG', 'SCANNER_DATA', 'GW_CONFIG']
        for table in other_tables:
            try:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if cursor.fetchone():
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    info[table] = {'total_records': count}
            except:
                pass
        
        return info
    
    def _get_table_date_info(self, cursor, table: str, date_columns: List[str]) -> Dict:
        """Get date information from table"""
        date_info = {}
        
        for col in date_columns:
            try:
                # Check if column exists
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                
                if col in columns:
                    cursor.execute(f"SELECT MAX({col}) FROM {table}")
                    result = cursor.fetchone()
                    if result and result[0]:
                        date_info[col] = str(result[0])
            except:
                continue
        
        return date_info
    
    def _get_recent_records_count(self, cursor, table: str, date_columns: List[str], days: int = 7) -> int:
        """Get count of recent records within specified days"""
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        for col in date_columns:
            try:
                # Check if column exists
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                
                if col in columns:
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} >= ?", (cutoff_date,))
                    result = cursor.fetchone()
                    if result:
                        return result[0]
            except:
                continue
        
        return 0
    
    def _get_database_latest_date(self, db_analysis: Dict) -> Optional[str]:
        """Get the latest date from database analysis"""
        latest_date = None
        
        for table_info in db_analysis.get('key_tables_info', {}).values():
            if isinstance(table_info, dict) and 'latest_dates' in table_info:
                for date_val in table_info['latest_dates'].values():
                    if date_val and (not latest_date or date_val > latest_date):
                        latest_date = date_val
        
        return latest_date
    
    def _generate_validation_summary(self, results: Dict) -> Dict:
        """Generate validation summary"""
        summary = {
            'databases_detected': list(results['databases_found'].keys()),
            'total_databases': len(results['databases_found']),
            'validation_status': 'success' if not results['errors'] else 'warning',
            'latest_backup_dates': {},
            'database_health': {},
            'recommendations': []
        }
        
        # Analyze each database type
        for db_type, db_entries in results['databases_found'].items():
            # Get latest backup date for this database type
            latest_date = results['latest_dates'].get(db_type)
            if latest_date:
                summary['latest_backup_dates'][db_type] = latest_date
                
                # Check if backup is recent (within 2 days)
                try:
                    backup_date = datetime.strptime(latest_date[:10], '%Y-%m-%d')
                    days_old = (datetime.now() - backup_date).days
                    
                    if days_old <= 1:
                        health = 'excellent'
                    elif days_old <= 3:
                        health = 'good'
                    elif days_old <= 7:
                        health = 'warning'
                    else:
                        health = 'critical'
                    
                    summary['database_health'][db_type] = {
                        'status': health,
                        'days_old': days_old,
                        'backup_count': len(db_entries)
                    }
                    
                    # Add recommendations
                    if health == 'critical':
                        summary['recommendations'].append(f"{db_type.upper()}: Backup sangat lama ({days_old} hari), perlu backup segera!")
                    elif health == 'warning':
                        summary['recommendations'].append(f"{db_type.upper()}: Backup agak lama ({days_old} hari), pertimbangkan backup baru")
                
                except:
                    summary['database_health'][db_type] = {'status': 'unknown', 'error': 'Cannot parse date'}
        
        # General recommendations
        if results['errors']:
            summary['recommendations'].append(f"Ditemukan {len(results['errors'])} error yang perlu diperbaiki")
        
        if results['warnings']:
            summary['recommendations'].append(f"Ditemukan {len(results['warnings'])} warning yang perlu diperhatikan")
        
        return summary
    
    def generate_detailed_report(self, validation_results: Dict) -> str:
        """Generate detailed text report"""
        report = []
        report.append("=" * 60)
        report.append("DATABASE BACKUP VALIDATION REPORT")
        report.append("=" * 60)
        report.append(f"Validation Time: {validation_results['validation_timestamp']}")
        report.append(f"Total ZIP Files Processed: {validation_results['total_zip_files']}")
        report.append("")
        
        # Summary section
        summary = validation_results['validation_summary']
        report.append("VALIDATION SUMMARY")
        report.append("-" * 30)
        report.append(f"Databases Detected: {', '.join(summary['databases_detected'])}")
        report.append(f"Total Database Types: {summary['total_databases']}")
        report.append(f"Overall Status: {summary['validation_status'].upper()}")
        report.append("")
        
        # Database health
        if summary['database_health']:
            report.append("DATABASE HEALTH STATUS")
            report.append("-" * 30)
            for db_type, health_info in summary['database_health'].items():
                status = health_info['status'].upper()
                days_old = health_info.get('days_old', 'N/A')
                backup_count = health_info.get('backup_count', 0)
                report.append(f"{db_type.upper()}: {status} ({days_old} days old, {backup_count} backups)")
            report.append("")
        
        # Latest backup dates
        if summary['latest_backup_dates']:
            report.append("LATEST BACKUP DATES")
            report.append("-" * 30)
            for db_type, latest_date in summary['latest_backup_dates'].items():
                report.append(f"{db_type.upper()}: {latest_date}")
            report.append("")
        
        # Recommendations
        if summary['recommendations']:
            report.append("RECOMMENDATIONS")
            report.append("-" * 30)
            for i, rec in enumerate(summary['recommendations'], 1):
                report.append(f"{i}. {rec}")
            report.append("")
        
        # Errors and warnings
        if validation_results['errors']:
            report.append("ERRORS")
            report.append("-" * 30)
            for error in validation_results['errors']:
                report.append(f"• {error}")
            report.append("")
        
        if validation_results['warnings']:
            report.append("WARNINGS")
            report.append("-" * 30)
            for warning in validation_results['warnings']:
                report.append(f"• {warning}")
            report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)