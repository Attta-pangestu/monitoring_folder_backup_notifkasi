#!/usr/bin/env python3
"""
Enhanced BAK File Analyzer
Analyzer untuk SQL Server backup files dengan kemampuan deteksi yang lebih baik
"""

import os
import struct
import zipfile
import tempfile
import subprocess
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import sqlite3

class EnhancedBAKAnalyzer:
    def __init__(self):
        self.sql_server_available = self._check_sql_server()

    def _check_sql_server(self) -> bool:
        """Check if SQL Server is available"""
        try:
            result = subprocess.run(['sqlcmd', '-?', '-h', '-1'],
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False

    def analyze_bak_file_comprehensive(self, bak_path: str, zip_file: Optional[zipfile.ZipFile] = None) -> Dict[str, Any]:
        """
        Analisis komprehensif BAK file dengan deteksi database yang lebih baik
        """
        try:
            # Extract file if needed
            if zip_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.bak') as temp_file:
                    with zip_file.open(bak_path) as source:
                        temp_file.write(source.read())
                    temp_bak_path = temp_file.name
            else:
                temp_bak_path = bak_path

            # Comprehensive analysis
            result = {
                'filename': os.path.basename(bak_path),
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'file_size': 0,
                'file_size_mb': 0,
                'analysis_status': 'success',
                'backup_metadata': {},
                'database_info': {},
                'restore_info': {},
                'table_info': {},
                'validation': {},
                'recommendations': []
            }

            # Get file size
            file_size = os.path.getsize(temp_bak_path)
            result['file_size'] = file_size
            result['file_size_mb'] = round(file_size / (1024 * 1024), 2)

            # Step 1: Basic BAK file analysis
            basic_info = self._analyze_bak_basic(temp_bak_path)
            result['backup_metadata'] = basic_info

            # Step 2: Try to restore and analyze if SQL Server available
            if self.sql_server_available:
                restore_info = self._try_restore_and_analyze(temp_bak_path, bak_path)
                result['restore_info'] = restore_info
                result['table_info'] = restore_info.get('table_info', {})
                result['database_info'] = restore_info.get('database_info', {})
            else:
                # Fallback to header analysis
                header_info = self._analyze_bak_header_enhanced(temp_bak_path)
                result['database_info'] = header_info
                result['recommendations'].append("SQL Server tidak tersedia - menggunakan analisis header saja")

            # Step 3: Validation
            validation = self._validate_bak_file(temp_bak_path, result)
            result['validation'] = validation

            # Step 4: Generate recommendations
            result['recommendations'].extend(self._generate_recommendations(result))

            # Clean up temp file
            if zip_file and os.path.exists(temp_bak_path):
                os.unlink(temp_bak_path)

            return result

        except Exception as e:
            return {
                'filename': os.path.basename(bak_path),
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'analysis_status': 'failed',
                'error': str(e),
                'recommendations': [f'Analisis gagal: {str(e)}']
            }

    def _analyze_bak_basic(self, bak_path: str) -> Dict[str, Any]:
        """Analisis dasar BAK file dengan metadata file system"""
        try:
            # Get file metadata
            file_stat = os.stat(bak_path)
            modified_time = datetime.fromtimestamp(file_stat.st_mtime)
            created_time = datetime.fromtimestamp(file_stat.st_ctime)

            with open(bak_path, 'rb') as f:
                # Read header
                header = f.read(8192)

                basic_info = {
                    'file_signature': header[:20].hex(),
                    'is_sql_backup': False,
                    'backup_type': 'Unknown',
                    'sql_version': 'Unknown',
                    'backup_date': modified_time.strftime('%Y-%m-%d %H:%M:%S'),  # Use file modification time
                    'backup_date_source': 'file_metadata',  # Indicate source
                    'database_name': self._extract_db_name_from_filename(bak_path),
                    'compression_ratio': 0.0,
                    'estimated_size_mb': os.path.getsize(bak_path) / (1024 * 1024),
                    'file_created': created_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'file_modified': modified_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'file_size_bytes': file_stat.st_size,
                    'file_health': 'unknown'
                }

                # Check SQL Server signatures
                sql_signatures = [
                    b'Microsoft SQL Server Backup',
                    b'TAPE',
                    b'Microsoft SQL Server',
                    b'\x01\x00\x00\x00'
                ]

                for sig in sql_signatures:
                    if sig in header:
                        basic_info['is_sql_backup'] = True
                        break

                # Extract text information
                try:
                    header_text = header.decode('utf-8', errors='ignore')

                    # Extract database name from header
                    db_match = re.search(r'Database[\"\'\s]*[:=]\s*([^\s\n\r\x00]+)', header_text, re.IGNORECASE)
                    if db_match:
                        basic_info['database_name'] = db_match.group(1).strip()

                    # Extract backup type
                    if 'FULL' in header_text.upper():
                        basic_info['backup_type'] = 'FULL'
                    elif 'DIFFERENTIAL' in header_text.upper():
                        basic_info['backup_type'] = 'DIFFERENTIAL'
                    elif 'LOG' in header_text.upper():
                        basic_info['backup_type'] = 'TRANSACTION LOG'

                    # Extract date
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', header_text)
                    if date_match:
                        basic_info['backup_date'] = date_match.group(1)

                    # Extract SQL version
                    version_match = re.search(r'SQL Server\s+(\d{4}|\d+\.\d+)', header_text)
                    if version_match:
                        basic_info['sql_version'] = version_match.group(1)

                except:
                    pass

                return basic_info

        except Exception as e:
            return {'error': str(e)}

    def _extract_db_name_from_filename(self, filepath: str) -> str:
        """Extract database name from filename"""
        filename = os.path.basename(filepath).lower()

        # Check for known patterns
        if 'backupstaging' in filename:
            return 'BackupStaging'
        elif 'backupvenus' in filename:
            return 'BackupVenuz'
        elif 'staging' in filename:
            return 'staging_PTRJ_iFES_Plantware'
        elif 'venus' in filename:
            return 'VenusHR14'
        elif 'ptrj' in filename:
            return 'db_ptrj'
        else:
            # Extract from filename
            name_parts = re.findall(r'[a-zA-Z_]+', filename)
            if name_parts:
                return name_parts[0].capitalize()
            return 'Unknown'

    def _try_restore_and_analyze(self, bak_path: str, original_name: str) -> Dict[str, Any]:
        """Coba restore database dan analisis"""
        result = {
            'restore_success': False,
            'database_info': {},
            'table_info': {},
            'error': None
        }

        try:
            # Generate unique database name
            db_name = f"temp_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Restore command
            restore_cmd = f'sqlcmd -S localhost -U sa -P windows0819 -Q "RESTORE DATABASE [{db_name}] FROM DISK = \'{bak_path}\' WITH REPLACE, MOVE \'{db_name}\' TO \'C:\\Program Files\\Microsoft SQL Server\\MSSQL15.MSSQLSERVER\\MSSQL\\DATA\\{db_name}.mdf\', MOVE \'{db_name}_log\' TO \'C:\\Program Files\\Microsoft SQL Server\\MSSQL15.MSSQLSERVER\\MSSQL\\DATA\\{db_name}_log.ldf\'" -h -1'

            # Execute restore
            restore_result = subprocess.run(restore_cmd, shell=True, capture_output=True, text=True, timeout=300)

            if restore_result.returncode == 0:
                result['restore_success'] = True

                # Get database info
                db_info = self._get_sql_database_info(db_name, original_name)
                result['database_info'] = db_info

                # Get table info
                table_info = self._get_sql_table_info(db_name)
                result['table_info'] = table_info

                # Clean up - drop database
                cleanup_cmd = f'sqlcmd -S localhost -U sa -P windows0819 -Q "DROP DATABASE [{db_name}]" -h -1'
                subprocess.run(cleanup_cmd, shell=True, capture_output=True, timeout=30)
            else:
                result['error'] = restore_result.stderr

        except Exception as e:
            result['error'] = str(e)

        return result

    def _get_sql_database_info(self, db_name: str, original_name: str) -> Dict[str, Any]:
        """Get database information from SQL Server"""
        db_info = {
            'database_name': original_name,
            'create_date': 'Unknown',
            'size_mb': 0,
            'status': 'Online',
            'recovery_model': 'Unknown',
            'compatibility_level': 'Unknown'
        }

        try:
            # Get database properties
            query = f"""
            SELECT
                create_date,
                size * 8.0 / 1024 as size_mb,
                state_desc,
                recovery_model_desc,
                compatibility_level
            FROM sys.databases
            WHERE name = '{db_name}'
            """

            cmd = f'sqlcmd -S localhost -U sa -P windows0819 -Q "{query}" -h -1 -W'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 1 and lines[0].strip():
                    values = lines[0].split()
                    if len(values) >= 5:
                        db_info.update({
                            'create_date': values[0],
                            'size_mb': round(float(values[1]), 2),
                            'status': values[2],
                            'recovery_model': values[3],
                            'compatibility_level': values[4]
                        })
        except:
            pass

        return db_info

    def _get_sql_table_info(self, db_name: str) -> Dict[str, Any]:
        """Get table information from SQL Server"""
        table_info = {
            'tables': [],
            'total_tables': 0,
            'total_records': 0,
            'largest_table': None,
            'table_details': {}
        }

        try:
            # Get table list and record counts
            query = f"""
            USE [{db_name}]
            SELECT
                t.name as table_name,
                s.row_count,
                SUM(s.used_page_count) * 8.0 / 1024 as size_mb
            FROM sys.tables t
            LEFT JOIN (
                SELECT
                    object_id,
                    SUM(row_count) as row_count,
                    SUM(used_page_count) as used_page_count
                FROM sys.dm_db_partition_stats
                GROUP BY object_id
            ) s ON t.object_id = s.object_id
            WHERE t.is_ms_shipped = 0
            GROUP BY t.name, s.row_count
            ORDER BY s.row_count DESC
            """

            cmd = f'sqlcmd -S localhost -U sa -P windows0819 -Q "{query}" -h -1 -W'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                tables = []
                total_records = 0
                largest_table = None
                max_size = 0

                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 3:
                            table_name = parts[0]
                            record_count = int(parts[1]) if parts[1].isdigit() else 0
                            size_mb = float(parts[2]) if len(parts) > 2 and parts[2].replace('.', '').isdigit() else 0

                            tables.append({
                                'name': table_name,
                                'record_count': record_count,
                                'size_mb': size_mb
                            })

                            total_records += record_count

                            if size_mb > max_size:
                                max_size = size_mb
                                largest_table = table_name

                table_info['tables'] = [t['name'] for t in tables[:10]]  # Show top 10
                table_info['total_tables'] = len(tables)
                table_info['total_records'] = total_records
                table_info['largest_table'] = largest_table
                table_info['table_details'] = {t['name']: t for t in tables}

        except Exception as e:
            table_info['error'] = str(e)

        return table_info

    def _analyze_bak_header_enhanced(self, bak_path: str) -> Dict[str, Any]:
        """Analisis header BAK file yang ditingkatkan"""
        try:
            with open(bak_path, 'rb') as f:
                # Read more header data
                header = f.read(65536)  # 64KB

                db_info = {
                    'database_name': self._extract_db_name_from_filename(bak_path),
                    'backup_type': 'Unknown',
                    'backup_date': 'Unknown',
                    'sql_version': 'Unknown',
                    'estimated_tables': 0,
                    'estimated_records': 0,
                    'size_mb': os.path.getsize(bak_path) / (1024 * 1024),
                    'recovery_model': 'Unknown',
                    'compatibility_level': 'Unknown'
                }

                # Enhanced header analysis
                try:
                    header_text = header.decode('utf-8', errors='ignore')

                    # More comprehensive pattern matching
                    patterns = {
                        'database_name': [r'Database[\"\'\s]*[:=]\s*([^\s\n\r\x00]+)', r'LogicalName[\"\'\s]*[:=]\s*([^\s\n\r\x00]+)'],
                        'backup_type': [r'(FULL|DIFFERENTIAL|TRANSACTION\s+LOG)\s+BACKUP', r'BackupType[\"\'\s]*[:=]\s*([^\s\n\r\x00]+)'],
                        'backup_date': [r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', r'(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})'],
                        'sql_version': [r'SQL\s+Server\s+(\d{4}|\d+\.\d+)', r'Version[\"\'\s]*[:=]\s*(\d+\.\d+)'],
                        'recovery_model': [r'Recovery\s+Model[\"\'\s]*[:=]\s*([^\s\n\r\x00]+)']
                    }

                    for field, pattern_list in patterns.items():
                        for pattern in pattern_list:
                            match = re.search(pattern, header_text, re.IGNORECASE)
                            if match:
                                db_info[field] = match.group(1).strip()
                                break

                    # Estimate based on file size and database name
                    db_info.update(self._estimate_database_stats(db_info['database_name'], db_info['size_mb']))

                except:
                    pass

                return db_info

        except Exception as e:
            return {'error': str(e)}

    def _estimate_database_stats(self, db_name: str, size_mb: float) -> Dict[str, Any]:
        """Estimate database statistics based on name and size"""
        stats = {
            'estimated_tables': 0,
            'estimated_records': 0,
            'estimated_table_size_mb': 0
        }

        # Base estimates on database type
        if 'staging' in db_name.lower():
            # Staging database - typically moderate size
            stats['estimated_tables'] = 45
            stats['estimated_records'] = int(size_mb * 5000)
            stats['estimated_table_size_mb'] = size_mb / 45
        elif 'venus' in db_name.lower():
            # Venus/HR database - typically larger
            stats['estimated_tables'] = 170
            stats['estimated_records'] = int(size_mb * 10000)
            stats['estimated_table_size_mb'] = size_mb / 170
        elif 'ptrj' in db_name.lower():
            # PTRJ database
            stats['estimated_tables'] = 25
            stats['estimated_records'] = int(size_mb * 3000)
            stats['estimated_table_size_mb'] = size_mb / 25
        else:
            # Generic database
            stats['estimated_tables'] = max(10, int(size_mb / 10))
            stats['estimated_records'] = int(size_mb * 2000)
            stats['estimated_table_size_mb'] = size_mb / max(10, int(size_mb / 10))

        return stats

    def _validate_bak_file(self, bak_path: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate BAK file integrity"""
        validation = {
            'is_valid_bak': True,
            'can_be_restored': True,
            'corruption_detected': False,
            'warnings': [],
            'file_integrity': 'Good'
        }

        try:
            # Basic file checks
            file_size = os.path.getsize(bak_path)

            if file_size < 1024 * 1024:  # Less than 1MB
                validation['warnings'].append("File size unusually small")
                validation['can_be_restored'] = False

            # Check file readability
            with open(bak_path, 'rb') as f:
                # Try to read different parts of the file
                test_positions = [0, file_size // 4, file_size // 2, file_size - 1024]

                for pos in test_positions:
                    try:
                        f.seek(pos)
                        f.read(1024)
                    except Exception as e:
                        validation['corruption_detected'] = True
                        validation['warnings'].append(f"Cannot read file at position {pos}: {str(e)}")
                        break

            # Check backup header
            with open(bak_path, 'rb') as f:
                header = f.read(1024)
                if not any(sig in header for sig in [b'Microsoft SQL Server', b'TAPE', b'\x01\x00\x00\x00']):
                    validation['warnings'].append("No valid SQL Server backup signature found")
                    validation['is_valid_bak'] = False

            # Determine overall integrity
            if validation['corruption_detected']:
                validation['file_integrity'] = 'Corrupted'
                validation['can_be_restored'] = False
            elif validation['warnings']:
                validation['file_integrity'] = 'Warnings'
            else:
                validation['file_integrity'] = 'Good'

        except Exception as e:
            validation['corruption_detected'] = True
            validation['warnings'].append(f"Validation error: {str(e)}")
            validation['file_integrity'] = 'Error'
            validation['can_be_restored'] = False

        return validation

    def generate_health_summary(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate health summary untuk multiple BAK files"""
        summary = {
            'total_files': len(analysis_results),
            'healthy_files': 0,
            'warning_files': 0,
            'corrupted_files': 0,
            'total_size_mb': 0,
            'database_types': set(),
            'backup_date_range': {'earliest': None, 'latest': None},
            'health_status': 'Unknown',
            'recommendations': []
        }

        for result in analysis_results:
            if result.get('analysis_status') == 'success':
                validation = result.get('validation', {})

                # Count health status
                if validation.get('file_integrity') == 'Good':
                    summary['healthy_files'] += 1
                elif validation.get('corruption_detected'):
                    summary['corrupted_files'] += 1
                else:
                    summary['warning_files'] += 1

                # Add to total size
                summary['total_size_mb'] += result.get('file_size_mb', 0)

                # Track database types
                db_name = result.get('backup_metadata', {}).get('database_name', 'Unknown')
                summary['database_types'].add(db_name)

                # Track backup dates
                backup_date = result.get('backup_metadata', {}).get('backup_date')
                if backup_date and backup_date != 'Unknown':
                    try:
                        dt = datetime.strptime(backup_date, '%Y-%m-%d %H:%M:%S')
                        if not summary['backup_date_range']['earliest'] or dt < summary['backup_date_range']['earliest']:
                            summary['backup_date_range']['earliest'] = dt
                        if not summary['backup_date_range']['latest'] or dt > summary['backup_date_range']['latest']:
                            summary['backup_date_range']['latest'] = dt
                    except:
                        pass

        # Convert set to list for JSON serialization
        summary['database_types'] = list(summary['database_types'])

        # Determine overall health status
        if summary['corrupted_files'] > 0:
            summary['health_status'] = 'Critical'
            summary['recommendations'].append(f"⚠️ {summary['corrupted_files']} file backup korupti ditemukan")
        elif summary['warning_files'] > 0:
            summary['health_status'] = 'Warning'
            summary['recommendations'].append(f"⚠️ {summary['warning_files']} file backup memiliki peringatan")
        else:
            summary['health_status'] = 'Healthy'
            summary['recommendations'].append("✅ Semua file backup dalam kondisi baik")

        # Add general recommendations
        if summary['total_size_mb'] > 20000:  # > 20GB
            summary['recommendations'].append("ℹ️ Total backup size besar - pertimbangkan retention policy")

        if summary['total_files'] == 0:
            summary['recommendations'].append("⚠️ Tidak ada file backup valid ditemukan")

        return summary

    def format_analysis_output(self, analysis_results: List[Dict[str, Any]]) -> str:
        """Format analysis results untuk tampilan user-friendly"""
        output = []

        # Health summary
        health_summary = self.generate_health_summary(analysis_results)

        output.append("=" * 60)
        output.append("🏥 HEALTH SUMMARY")
        output.append("=" * 60)
        output.append(f"📊 Total Files: {health_summary['total_files']}")
        output.append(f"✅ Healthy: {health_summary['healthy_files']}")
        output.append(f"⚠️  Warnings: {health_summary['warning_files']}")
        output.append(f"❌ Corrupted: {health_summary['corrupted_files']}")
        output.append(f"📏 Total Size: {health_summary['total_size_mb']:.1f} MB")
        output.append(f"🏥 Overall Status: {health_summary['health_status']}")
        output.append("")

        if health_summary['backup_date_range']['earliest']:
            earliest = health_summary['backup_date_range']['earliest'].strftime('%Y-%m-%d %H:%M:%S')
            latest = health_summary['backup_date_range']['latest'].strftime('%Y-%m-%d %H:%M:%S')
            output.append(f"📅 Backup Date Range: {earliest} - {latest}")

        output.append("")

        # Detailed analysis
        output.append("=" * 60)
        output.append("🔍 DETAILED ANALYSIS")
        output.append("=" * 60)

        for result in analysis_results:
            if result.get('analysis_status') == 'success':
                metadata = result.get('backup_metadata', {})
                validation = result.get('validation', {})

                # Status emoji
                if validation.get('file_integrity') == 'Good':
                    status_emoji = "✅"
                elif validation.get('corruption_detected'):
                    status_emoji = "❌"
                else:
                    status_emoji = "⚠️"

                output.append(f"{status_emoji} File: {result.get('filename', 'Unknown')}")
                output.append(f"   📅 Backup Date: {metadata.get('backup_date', 'Unknown')}")
                output.append(f"   💾 Database: {metadata.get('database_name', 'Unknown')}")
                output.append(f"   📏 Size: {result.get('file_size_mb', 0):.1f} MB")
                output.append(f"   🏥 Health: {validation.get('file_integrity', 'Unknown')}")

                if validation.get('warnings'):
                    output.append(f"   ⚠️  Warnings: {len(validation['warnings'])}")

                output.append("")

        # Recommendations
        if health_summary['recommendations']:
            output.append("=" * 60)
            output.append("💡 RECOMMENDATIONS")
            output.append("=" * 60)
            for rec in health_summary['recommendations']:
                output.append(rec)
            output.append("")

        return "\n".join(output)

    def _generate_recommendations(self, analysis_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []

        # Check validation results
        validation = analysis_result.get('validation', {})
        if validation.get('corruption_detected'):
            recommendations.append("⚠️ Korupsi file terdeteksi - file mungkin tidak bisa di-restore")

        if not validation.get('is_valid_bak', True):
            recommendations.append("⚠️ File bukan backup SQL Server yang valid")

        if validation.get('warnings'):
            recommendations.append(f"⚠️ {len(validation['warnings'])} peringatan terdeteksi")

        # Check restore results
        restore_info = analysis_result.get('restore_info', {})
        if not restore_info.get('restore_success', False):
            if restore_info.get('error'):
                recommendations.append(f"⚠️ Restore gagal: {restore_info['error']}")
            else:
                recommendations.append("ℹ️ SQL Server tidak tersedia - analisis terbatas pada header file")

        # Check database info
        db_info = analysis_result.get('database_info', {})
        table_info = analysis_result.get('table_info', {})

        if db_info.get('size_mb', 0) > 10000:  # > 10GB
            recommendations.append("ℹ️ Database besar - pastikan ruang disk cukup untuk restore")

        if table_info.get('total_tables', 0) == 0:
            recommendations.append("ℹ️ Tidak dapat mengambil informasi tabel - cek manual dengan SQL Server")

        # Positive recommendations
        if validation.get('file_integrity') == 'Good':
            recommendations.append("✅ File backup dalam kondisi baik")

        if restore_info.get('restore_success'):
            recommendations.append("✅ Restore sukses - database dapat diakses")

        return recommendations

    def generate_comprehensive_report(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive report for multiple BAK files"""
        report = {
            'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_files': len(analysis_results),
            'successful_analyses': len([r for r in analysis_results if r.get('analysis_status') == 'success']),
            'failed_analyses': len([r for r in analysis_results if r.get('analysis_status') == 'failed']),
            'summary': {
                'total_size_mb': 0,
                'valid_files': 0,
                'corrupted_files': 0,
                'databases_found': []
            },
            'file_details': analysis_results,
            'recommendations': []
        }

        # Calculate summary
        for result in analysis_results:
            if result.get('analysis_status') == 'success':
                report['summary']['total_size_mb'] += result.get('file_size_mb', 0)

                validation = result.get('validation', {})
                if validation.get('is_valid_bak'):
                    report['summary']['valid_files'] += 1
                if validation.get('corruption_detected'):
                    report['summary']['corrupted_files'] += 1

                db_name = result.get('database_info', {}).get('database_name', 'Unknown')
                if db_name not in report['summary']['databases_found']:
                    report['summary']['databases_found'].append(db_name)

        # Generate overall recommendations
        if report['summary']['corrupted_files'] > 0:
            report['recommendations'].append(f"⚠️ {report['summary']['corrupted_files']} file koruptsi ditemukan")

        if report['failed_analyses'] > 0:
            report['recommendations'].append(f"⚠️ {report['failed_analyses']} file gagal dianalisis")

        if report['summary']['valid_files'] == report['total_files']:
            report['recommendations'].append("✅ Semua file backup valid dan dalam kondisi baik")

        return report