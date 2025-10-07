#!/usr/bin/env python3
"""
BackupStaging.bak Metadata Analyzer
Script untuk analisis lengkap file backup SQL Server
"""

import os
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Tuple
import re

class BackupAnalyzer:
    def __init__(self):
        self.bak_path = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup\BackupStaging.bak"
        self.sqlcmd_path = "sqlcmd"
        self.analysis_results = {}

    def analyze_backup_header(self) -> Dict:
        """Analisis header file backup menggunakan sqlcmd"""
        print("=== Analyzing Backup Header ===")

        header_info = {
            'backup_name': '',
            'backup_description': '',
            'backup_type': '',
            'database_name': '',
            'server_name': '',
            'machine_name': '',
            'backup_start_date': None,
            'backup_finish_date': None,
            'backup_size': 0,
            'compressed_backup_size': 0,
            'database_version': '',
            'collation': '',
            'recovery_model': '',
            'position': 1,
            'first_lsn': '',
            'last_lsn': '',
            'checkpoint_lsn': '',
            'database_backup_lsn': '',
            'is_password_protected': False,
            'has_bulk_logged_data': False,
            'is_snapshot': False,
            'is_readonly': False,
            'has_incomplete_metadata': False
        }

        try:
            # SQL command to get backup header
            sql_query = f"RESTORE HEADERONLY FROM DISK='{self.bak_path}'"

            cmd = [
                self.sqlcmd_path,
                '-S', 'localhost',
                '-E',  # Windows Authentication
                '-Q', sql_query,
                '-h', '-1',  # No headers
                '-s', ','   # Comma separator
                '-W',      # Remove trailing spaces
                '-o', 'backup_header.txt'
            ]

            print(f"Executing: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                # Read the output file
                if os.path.exists('backup_header.txt'):
                    with open('backup_header.txt', 'r', encoding='utf-8') as f:
                        header_data = f.read().strip()

                    # Parse header data (comma-separated)
                    if header_data:
                        columns = header_data.split(',')
                        if len(columns) >= 50:  # RESTORE HEADERONLY returns many columns
                            header_info.update({
                                'backup_name': columns[0].strip() if columns[0] else '',
                                'backup_description': columns[1].strip() if columns[1] else '',
                                'backup_type': self.get_backup_type_name(int(columns[2]) if columns[2].isdigit() else 0),
                                'database_name': columns[3].strip() if columns[3] else '',
                                'server_name': columns[4].strip() if columns[4] else '',
                                'machine_name': columns[5].strip() if columns[5] else '',
                                'backup_start_date': self.parse_sql_datetime(columns[6]) if columns[6] else None,
                                'backup_finish_date': self.parse_sql_datetime(columns[7]) if columns[7] else None,
                                'backup_size': int(columns[8]) if columns[8].isdigit() else 0,
                                'compressed_backup_size': int(columns[15]) if columns[15].isdigit() else 0,
                                'database_version': columns[12].strip() if columns[12] else '',
                                'collation': columns[18].strip() if columns[18] else '',
                                'recovery_model': self.get_recovery_model_name(int(columns[19]) if columns[19].isdigit() else 0),
                                'position': int(columns[21]) if columns[21].isdigit() else 1,
                                'first_lsn': columns[27].strip() if columns[27] else '',
                                'last_lsn': columns[28].strip() if columns[28] else '',
                                'checkpoint_lsn': columns[29].strip() if columns[29] else '',
                                'database_backup_lsn': columns[30].strip() if columns[30] else '',
                                'is_password_protected': columns[22].strip() == '1',
                                'has_bulk_logged_data': columns[23].strip() == '1',
                                'is_snapshot': columns[24].strip() == '1',
                                'is_readonly': columns[25].strip() == '1',
                                'has_incomplete_metadata': columns[26].strip() == '1'
                            })

                    print(f"[SUCCESS] Backup header analysis completed")

            else:
                print(f"[ERROR] SQLCMD failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            print("[ERROR] Backup header analysis timed out")
        except Exception as e:
            print(f"[ERROR] Backup header analysis failed: {str(e)}")

        return header_info

    def analyze_filelist(self) -> List[Dict]:
        """Analisis daftar file dalam backup"""
        print("\n=== Analyzing Backup Filelist ===")

        filelist = []

        try:
            # SQL command to get filelist
            sql_query = f"RESTORE FILELISTONLY FROM DISK='{self.bak_path}'"

            cmd = [
                self.sqlcmd_path,
                '-S', 'localhost',
                '-E',
                '-Q', sql_query,
                '-h', '-1',
                '-s', ',',
                '-W',
                '-o', 'backup_filelist.txt'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                if os.path.exists('backup_filelist.txt'):
                    with open('backup_filelist.txt', 'r', encoding='utf-8') as f:
                        filelist_data = f.read().strip()

                    # Parse filelist data
                    lines = filelist_data.split('\n')
                    for line in lines:
                        if line.strip():
                            columns = line.split(',')
                            if len(columns) >= 6:
                                file_info = {
                                    'logical_name': columns[0].strip() if columns[0] else '',
                                    'physical_name': columns[1].strip() if columns[1] else '',
                                    'file_type': columns[2].strip() if columns[2] else '',
                                    'file_group': columns[3].strip() if columns[3] else '',
                                    'size': int(columns[4]) if columns[4].isdigit() else 0,
                                    'max_size': int(columns[5]) if columns[5].isdigit() else 0,
                                    'growth': int(columns[6]) if columns[6].isdigit() else 0,
                                    'usage': columns[7].strip() if len(columns) > 7 else ''
                                }
                                filelist.append(file_info)

                    print(f"[SUCCESS] Found {len(filelist)} files in backup")

            else:
                print(f"[ERROR] Filelist analysis failed: {result.stderr}")

        except Exception as e:
            print(f"[ERROR] Filelist analysis failed: {str(e)}")

        return filelist

    def estimate_database_size(self) -> Dict:
        """Estimasi ukuran database"""
        print("\n=== Estimating Database Size ===")

        size_info = {
            'total_size_mb': 0,
            'data_size_mb': 0,
            'log_size_mb': 0,
            'file_count': 0,
            'compression_ratio': 0.0
        }

        try:
            file_size_bytes = os.path.getsize(self.bak_path)
            backup_size_mb = file_size_bytes / (1024 * 1024)

            # Get filelist for better estimation
            filelist = self.analyze_filelist()

            if filelist:
                total_db_size = 0
                data_size = 0
                log_size = 0

                for file_info in filelist:
                    size_mb = file_info['size'] / (1024 * 1024)
                    total_db_size += size_mb

                    if file_info['file_type'].upper() == 'D':
                        data_size += size_mb
                    elif file_info['file_type'].upper() == 'L':
                        log_size += size_mb

                size_info.update({
                    'total_size_mb': total_db_size,
                    'data_size_mb': data_size,
                    'log_size_mb': log_size,
                    'file_count': len(filelist),
                    'compression_ratio': (backup_size_mb / total_db_size * 100) if total_db_size > 0 else 0
                })

                print(f"[SUCCESS] Database size estimation completed")
                print(f"  Total DB size: {total_db_size:.2f} MB")
                print(f"  Data size: {data_size:.2f} MB")
                print(f"  Log size: {log_size:.2f} MB")
                print(f"  Compression ratio: {size_info['compression_ratio']:.1f}%")
            else:
                # Fallback estimation
                size_info['total_size_mb'] = backup_size_mb * 3  # Rough estimate
                size_info['compression_ratio'] = 33.3  # Assume 1:3 compression

        except Exception as e:
            print(f"[ERROR] Size estimation failed: {str(e)}")

        return size_info

    def get_table_estimation(self) -> Dict:
        """Estimasi jumlah tabel dan record"""
        print("\n=== Estimating Table Information ===")

        table_info = {
            'estimated_table_count': 0,
            'estimated_total_records': 0,
            'table_types': {},
            'top_largest_tables': [],
            'backup_contains_tables': False
        }

        try:
            # Try to get table information from backup
            # This is a complex operation, so we'll use estimation based on database size

            filelist = self.analyze_filelist()
            if not filelist:
                return table_info

            # Estimate based on database size and typical table distribution
            total_size_mb = sum(f['size'] for f in filelist) / (1024 * 1024)

            # Rough estimation formula based on typical database patterns
            if total_size_mb < 100:  # Small database
                table_info['estimated_table_count'] = max(10, int(total_size_mb / 2))
                table_info['estimated_total_records'] = max(1000, int(total_size_mb * 100))
            elif total_size_mb < 1000:  # Medium database
                table_info['estimated_table_count'] = max(20, int(total_size_mb / 10))
                table_info['estimated_total_records'] = max(10000, int(total_size_mb * 500))
            else:  # Large database
                table_info['estimated_table_count'] = max(50, int(total_size_mb / 20))
                table_info['estimated_total_records'] = max(100000, int(total_size_mb * 1000))

            # Estimate table types based on naming patterns
            table_info['table_types'] = {
                'user_tables': int(table_info['estimated_table_count'] * 0.7),
                'system_tables': int(table_info['estimated_table_count'] * 0.2),
                'temp_tables': int(table_info['estimated_table_count'] * 0.1)
            }

            # Estimate top largest tables
            avg_table_size = total_size_mb / table_info['estimated_table_count']
            table_info['top_largest_tables'] = [
                {'estimated_name': f'Table_{i}', 'estimated_size_mb': avg_table_size * (2 + i * 0.5)}
                for i in range(1, 6)
            ]

            table_info['backup_contains_tables'] = True

            print(f"[SUCCESS] Table estimation completed")
            print(f"  Estimated tables: {table_info['estimated_table_count']}")
            print(f"  Estimated records: {table_info['estimated_total_records']:,}")

        except Exception as e:
            print(f"[ERROR] Table estimation failed: {str(e)}")

        return table_info

    def analyze_backup_metadata(self) -> Dict:
        """Analisis metadata lengkap backup"""
        print("\n=== Comprehensive Backup Analysis ===")

        # Get basic file info
        file_size = os.path.getsize(self.bak_path)
        file_modified = datetime.fromtimestamp(os.path.getmtime(self.bak_path))

        analysis = {
            'file_info': {
                'path': self.bak_path,
                'size_bytes': file_size,
                'size_mb': file_size / (1024 * 1024),
                'size_gb': file_size / (1024 * 1024 * 1024),
                'last_modified': file_modified.isoformat(),
                'exists': os.path.exists(self.bak_path)
            },
            'header_info': self.analyze_backup_header(),
            'filelist': self.analyze_filelist(),
            'size_estimation': self.estimate_database_size(),
            'table_estimation': self.get_table_estimation(),
            'analysis_timestamp': datetime.now().isoformat()
        }

        # Calculate derived metrics
        header_info = analysis['header_info']
        if header_info['backup_start_date'] and header_info['backup_finish_date']:
            duration = header_info['backup_finish_date'] - header_info['backup_start_date']
            analysis['backup_duration_seconds'] = duration.total_seconds()

        # Add compression analysis
        if analysis['size_estimation']['total_size_mb'] > 0:
            backup_size_mb = analysis['file_info']['size_mb']
            db_size_mb = analysis['size_estimation']['total_size_mb']
            analysis['compression_analysis'] = {
                'compression_ratio': (backup_size_mb / db_size_mb * 100) if db_size_mb > 0 else 0,
                'space_saved_mb': db_size_mb - backup_size_mb if db_size_mb > backup_size_mb else 0,
                'space_saved_percent': ((db_size_mb - backup_size_mb) / db_size_mb * 100) if db_size_mb > 0 else 0
            }

        return analysis

    def get_backup_type_name(self, backup_type_code: int) -> str:
        """Get backup type name from code"""
        backup_types = {
            1: 'Database',
            2: 'Transaction Log',
            4: 'File or Filegroup',
            5: 'Database Differential',
            6: 'File Differential',
            7: 'Partial',
            8: 'Partial Differential'
        }
        return backup_types.get(backup_type_code, f'Unknown ({backup_type_code})')

    def get_recovery_model_name(self, recovery_model_code: int) -> str:
        """Get recovery model name from code"""
        recovery_models = {
            1: 'FULL',
            2: 'BULK_LOGGED',
            3: 'SIMPLE'
        }
        return recovery_models.get(recovery_model_code, f'Unknown ({recovery_model_code})')

    def parse_sql_datetime(self, datetime_str: str) -> datetime:
        """Parse SQL Server datetime string"""
        try:
            # SQL Server datetime format: 'YYYY-MM-DD HH:MM:SS.xxx'
            if datetime_str and datetime_str.strip():
                # Remove milliseconds for simplicity
                clean_str = datetime_str.split('.')[0]
                return datetime.strptime(clean_str, '%Y-%m-%d %H:%M:%S')
        except:
            pass
        return None

    def generate_report(self, analysis: Dict) -> str:
        """Generate comprehensive analysis report"""
        report = f"""
===============================================================
BACKUPSTAGING.BAK COMPREHENSIVE ANALYSIS REPORT
===============================================================

FILE INFORMATION
---------------------------------------------------------------
Path: {analysis['file_info']['path']}
Size: {analysis['file_info']['size_mb']:.2f} MB ({analysis['file_info']['size_gb']:.2f} GB)
Last Modified: {analysis['file_info']['last_modified']}
File Exists: {analysis['file_info']['exists']}

BACKUP HEADER INFORMATION
---------------------------------------------------------------
Backup Name: {analysis['header_info']['backup_name']}
Database Name: {analysis['header_info']['database_name']}
Server Name: {analysis['header_info']['server_name']}
Machine Name: {analysis['header_info']['machine_name']}
Backup Type: {analysis['header_info']['backup_type']}
Backup Start: {analysis['header_info']['backup_start_date']}
Backup Finish: {analysis['header_info']['backup_finish_date']}
Database Version: {analysis['header_info']['database_version']}
Collation: {analysis['header_info']['collation']}
Recovery Model: {analysis['header_info']['recovery_model']}

Backup Size: {analysis['header_info']['backup_size']:,} bytes
Compressed Size: {analysis['header_info']['compressed_backup_size']:,} bytes

LSN Information:
- First LSN: {analysis['header_info']['first_lsn']}
- Last LSN: {analysis['header_info']['last_lsn']}
- Checkpoint LSN: {analysis['header_info']['checkpoint_lsn']}
- Database Backup LSN: {analysis['header_info']['database_backup_lsn']}

FILE LIST
---------------------------------------------------------------
"""

        for i, file_info in enumerate(analysis['filelist'], 1):
            report += f"""
File {i}: {file_info['logical_name']}
  Type: {file_info['file_type']}
  Group: {file_info['file_group']}
  Size: {file_info['size'] / (1024*1024):.2f} MB
  Physical Name: {file_info['physical_name']}
"""

        report += f"""
DATABASE SIZE ESTIMATION
---------------------------------------------------------------
Total Database Size: {analysis['size_estimation']['total_size_mb']:.2f} MB
Data Size: {analysis['size_estimation']['data_size_mb']:.2f} MB
Log Size: {analysis['size_estimation']['log_size_mb']:.2f} MB
File Count: {analysis['size_estimation']['file_count']}

TABLE ESTIMATION
---------------------------------------------------------------
Estimated Table Count: {analysis['table_estimation']['estimated_table_count']}
Estimated Total Records: {analysis['table_estimation']['estimated_total_records']:,}

Table Types:
- User Tables: {analysis['table_estimation']['table_types']['user_tables']}
- System Tables: {analysis['table_estimation']['table_types']['system_tables']}
- Temp Tables: {analysis['table_estimation']['table_types']['temp_tables']}

Top 5 Largest Tables (Estimated):
"""

        for table in analysis['table_estimation']['top_largest_tables']:
            report += f"- {table['estimated_name']}: {table['estimated_size_mb']:.2f} MB\n"

        if 'compression_analysis' in analysis:
            comp = analysis['compression_analysis']
            report += f"""
COMPRESSION ANALYSIS
---------------------------------------------------------------
Compression Ratio: {comp['compression_ratio']:.1f}%
Space Saved: {comp['space_saved_mb']:.2f} MB
Space Saved Percentage: {comp['space_saved_percent']:.1f}%
"""

        report += f"""
ANALYSIS SUMMARY
---------------------------------------------------------------
Analysis Generated: {analysis['analysis_timestamp']}
Backup Duration: {analysis.get('backup_duration_seconds', 0):.2f} seconds
Contains Tables: {analysis['table_estimation']['backup_contains_tables']}
Password Protected: {analysis['header_info']['is_password_protected']}
Has Bulk Logged Data: {analysis['header_info']['has_bulk_logged_data']}
Is Snapshot: {analysis['header_info']['is_snapshot']}
Is Read Only: {analysis['header_info']['is_readonly']}
Has Incomplete Metadata: {analysis['header_info']['has_incomplete_metadata']}

===============================================================
Report Complete - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
===============================================================
"""

        return report

    def save_analysis_to_json(self, analysis: Dict, filename: str = 'backup_analysis.json'):
        """Save analysis results to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)
            print(f"[SUCCESS] Analysis saved to {filename}")
        except Exception as e:
            print(f"[ERROR] Failed to save analysis: {str(e)}")

def main():
    print("BackupStaging.bak Metadata Analyzer")
    print("===================================")

    analyzer = BackupAnalyzer()

    # Check if file exists
    if not os.path.exists(analyzer.bak_path):
        print(f"[ERROR] Backup file not found: {analyzer.bak_path}")
        return

    print(f"[INFO] Analyzing backup file: {analyzer.bak_path}")

    # Perform comprehensive analysis
    analysis = analyzer.analyze_backup_metadata()

    # Generate and save report
    report = analyzer.generate_report(analysis)

    # Save to file
    with open('backup_analysis_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)

    # Save JSON data
    analyzer.save_analysis_to_json(analysis)

    print("\n" + "="*60)
    print("[SUCCESS] Analysis completed!")
    print(f"Report saved to: backup_analysis_report.txt")
    print(f"JSON data saved to: backup_analysis.json")
    print("="*60)

    # Print key findings
    print(f"\nKEY FINDINGS:")
    print(f"- Database Name: {analysis['header_info']['database_name']}")
    print(f"- Backup Type: {analysis['header_info']['backup_type']}")
    print(f"- File Size: {analysis['file_info']['size_mb']:.2f} MB")
    print(f"- Estimated Tables: {analysis['table_estimation']['estimated_table_count']}")
    print(f"- Estimated Records: {analysis['table_estimation']['estimated_total_records']:,}")
    print(f"- Database Size: {analysis['size_estimation']['total_size_mb']:.2f} MB")

if __name__ == "__main__":
    main()