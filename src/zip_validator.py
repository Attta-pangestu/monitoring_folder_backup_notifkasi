#!/usr/bin/env python3
"""
ZIP Validator Module
Modul untuk validasi file ZIP backup database
"""

import os
import zipfile
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import sqlite3
import re

class ZipValidator:
    def __init__(self):
        self.temp_dir = None
        self.validation_results = {}
    
    def validate_zip_file(self, zip_path: str) -> Dict:
        """
        Validasi komprehensif file ZIP
        Returns: Dictionary dengan hasil validasi
        """
        result = {
            'filename': os.path.basename(zip_path),
            'filepath': zip_path,
            'is_valid': False,
            'is_readable': False,
            'has_bak_files': False,
            'file_size_mb': 0,
            'creation_date': None,
            'modification_date': None,
            'extracted_date': None,
            'bak_files': [],
            'database_info': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # Check if file exists
            if not os.path.exists(zip_path):
                result['errors'].append("File tidak ditemukan")
                return result
            
            # Get file info
            stat_info = os.stat(zip_path)
            result['file_size_mb'] = round(stat_info.st_size / (1024 * 1024), 2)
            result['creation_date'] = datetime.fromtimestamp(stat_info.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
            result['modification_date'] = datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            # Extract date from filename
            result['extracted_date'] = self._extract_date_from_filename(os.path.basename(zip_path))
            
            # Test ZIP file integrity
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Test ZIP integrity
                    bad_file = zip_ref.testzip()
                    if bad_file:
                        result['errors'].append(f"ZIP corrupted: {bad_file}")
                        return result
                    
                    result['is_readable'] = True
                    
                    # List contents
                    file_list = zip_ref.namelist()
                    
                    # Check for .bak files
                    bak_files = [f for f in file_list if f.lower().endswith('.bak')]
                    result['bak_files'] = bak_files
                    result['has_bak_files'] = len(bak_files) > 0
                    
                    if not result['has_bak_files']:
                        result['warnings'].append("Tidak ada file .bak ditemukan")
                    
                    # Extract and analyze .bak files
                    if result['has_bak_files']:
                        result['database_info'] = self._analyze_bak_files(zip_ref, bak_files)
                    
                    result['is_valid'] = True
                    
            except zipfile.BadZipFile:
                result['errors'].append("File bukan ZIP yang valid")
            except Exception as e:
                result['errors'].append(f"Error membaca ZIP: {str(e)}")
        
        except Exception as e:
            result['errors'].append(f"Error validasi: {str(e)}")
        
        return result
    
    def _extract_date_from_filename(self, filename: str) -> Optional[str]:
        """Extract date from filename using various patterns"""
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{2}-\d{2}-\d{4})',  # DD-MM-YYYY
            r'(\d{4}_\d{2}_\d{2})',  # YYYY_MM_DD
            r'(\d{2}_\d{2}_\d{4})',  # DD_MM_YYYY
            r'(\d{8})',              # YYYYMMDD
            r'(\d{6})',              # YYMMDD
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                date_str = match.group(1)
                return self._normalize_date(date_str)
        
        return None
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string to YYYY-MM-DD format"""
        date_str = date_str.replace('_', '-')
        
        formats = [
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%Y%m%d',
            '%y%m%d',
            '%m-%d-%Y'
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return date_str
    
    def _analyze_bak_files(self, zip_ref: zipfile.ZipFile, bak_files: List[str]) -> Dict:
        """Analyze .bak files in the ZIP"""
        database_info = {}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            for bak_file in bak_files:
                try:
                    # Extract .bak file
                    zip_ref.extract(bak_file, temp_dir)
                    bak_path = os.path.join(temp_dir, bak_file)
                    
                    # Analyze database
                    db_info = self._analyze_single_bak(bak_path)
                    database_info[bak_file] = db_info
                    
                except Exception as e:
                    database_info[bak_file] = {
                        'error': f"Error analyzing {bak_file}: {str(e)}"
                    }
        
        return database_info
    
    def _analyze_single_bak(self, bak_path: str) -> Dict:
        """Analyze single .bak file"""
        info = {
            'database_type': 'unknown',
            'tables_count': 0,
            'key_tables': {},
            'latest_dates': {},
            'file_size_mb': 0,
            'errors': []
        }
        
        try:
            info['file_size_mb'] = round(os.path.getsize(bak_path) / (1024 * 1024), 2)
            
            # Try to connect as SQLite database
            conn = sqlite3.connect(bak_path)
            cursor = conn.cursor()
            
            # Get table list
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            info['tables_count'] = len(tables)
            
            # Detect database type and analyze key tables
            info['database_type'] = self._detect_database_type(tables)
            
            # Analyze key tables based on database type
            if info['database_type'] == 'plantware':
                info['key_tables'] = self._analyze_plantware_tables(cursor)
            elif info['database_type'] == 'venus':
                info['key_tables'] = self._analyze_venus_tables(cursor)
            elif info['database_type'] == 'staging':
                info['key_tables'] = self._analyze_staging_tables(cursor)
            else:
                info['key_tables'] = self._analyze_generic_tables(cursor, tables[:5])  # Analyze first 5 tables
            
            conn.close()
            
        except Exception as e:
            info['errors'].append(f"Error analyzing database: {str(e)}")
        
        return info
    
    def _detect_database_type(self, tables: List[str]) -> str:
        """Detect database type based on table names"""
        table_names_upper = [t.upper() for t in tables]
        
        if 'PR_TASKREG' in table_names_upper:
            return 'plantware'
        elif 'TA_MACHINE' in table_names_upper:
            return 'venus'
        elif 'GWSCANNER' in table_names_upper:
            return 'staging'
        else:
            return 'unknown'
    
    def _analyze_plantware_tables(self, cursor) -> Dict:
        """Analyze Plantware specific tables"""
        result = {}
        
        try:
            # Analyze PR_TASKREG table
            cursor.execute("SELECT COUNT(*) FROM PR_TASKREG")
            count = cursor.fetchone()[0]
            
            # Get latest date from various date columns
            date_columns = ['TASK_DATE', 'CREATED_DATE', 'MODIFIED_DATE', 'START_DATE', 'END_DATE']
            latest_date = self._get_latest_date(cursor, 'PR_TASKREG', date_columns)
            
            result['PR_TASKREG'] = {
                'record_count': count,
                'latest_date': latest_date
            }
            
        except Exception as e:
            result['PR_TASKREG'] = {'error': str(e)}
        
        return result
    
    def _analyze_venus_tables(self, cursor) -> Dict:
        """Analyze Venus specific tables"""
        result = {}
        
        try:
            # Analyze TA_MACHINE table
            cursor.execute("SELECT COUNT(*) FROM TA_MACHINE")
            count = cursor.fetchone()[0]
            
            # Get latest date
            date_columns = ['MACHINE_DATE', 'CREATED_DATE', 'MODIFIED_DATE', 'LAST_UPDATE', 'TIMESTAMP']
            latest_date = self._get_latest_date(cursor, 'TA_MACHINE', date_columns)
            
            result['TA_MACHINE'] = {
                'record_count': count,
                'latest_date': latest_date
            }
            
        except Exception as e:
            result['TA_MACHINE'] = {'error': str(e)}
        
        return result
    
    def _analyze_staging_tables(self, cursor) -> Dict:
        """Analyze Staging specific tables"""
        result = {}
        
        try:
            # Analyze GWSCANNER table
            cursor.execute("SELECT COUNT(*) FROM GWSCANNER")
            count = cursor.fetchone()[0]
            
            # Get latest date
            date_columns = ['SCAN_DATE', 'CREATED_DATE', 'MODIFIED_DATE', 'TIMESTAMP', 'LOG_DATE']
            latest_date = self._get_latest_date(cursor, 'GWSCANNER', date_columns)
            
            result['GWSCANNER'] = {
                'record_count': count,
                'latest_date': latest_date
            }
            
        except Exception as e:
            result['GWSCANNER'] = {'error': str(e)}
        
        return result
    
    def _analyze_generic_tables(self, cursor, tables: List[str]) -> Dict:
        """Analyze generic tables"""
        result = {}
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                
                # Try common date columns
                date_columns = ['created_at', 'timestamp', 'date', 'updated_at', 'log_date', 'created_time']
                latest_date = self._get_latest_date(cursor, table, date_columns)
                
                result[table] = {
                    'record_count': count,
                    'latest_date': latest_date
                }
                
            except Exception as e:
                result[table] = {'error': str(e)}
        
        return result
    
    def _get_latest_date(self, cursor, table: str, date_columns: List[str]) -> Optional[str]:
        """Get latest date from specified columns"""
        for col in date_columns:
            try:
                cursor.execute(f"SELECT MAX({col}) FROM {table}")
                result = cursor.fetchone()
                if result and result[0]:
                    return str(result[0])
            except:
                continue
        return None
    
    def validate_multiple_zips(self, zip_paths: List[str]) -> Dict:
        """Validate multiple ZIP files"""
        results = {
            'total_files': len(zip_paths),
            'valid_files': 0,
            'invalid_files': 0,
            'files_with_bak': 0,
            'files_without_bak': 0,
            'total_size_mb': 0,
            'validation_details': [],
            'summary': {}
        }
        
        for zip_path in zip_paths:
            validation_result = self.validate_zip_file(zip_path)
            results['validation_details'].append(validation_result)
            
            if validation_result['is_valid']:
                results['valid_files'] += 1
            else:
                results['invalid_files'] += 1
            
            if validation_result['has_bak_files']:
                results['files_with_bak'] += 1
            else:
                results['files_without_bak'] += 1
            
            results['total_size_mb'] += validation_result['file_size_mb']
        
        # Generate summary
        results['summary'] = {
            'validation_rate': f"{(results['valid_files'] / results['total_files'] * 100):.1f}%" if results['total_files'] > 0 else "0%",
            'bak_files_rate': f"{(results['files_with_bak'] / results['total_files'] * 100):.1f}%" if results['total_files'] > 0 else "0%",
            'total_size_gb': round(results['total_size_mb'] / 1024, 2)
        }
        
        return results
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def __del__(self):
        """Destructor to clean up resources"""
        self.cleanup()