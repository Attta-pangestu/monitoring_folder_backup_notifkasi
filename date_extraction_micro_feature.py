#!/usr/bin/env python3
"""
Date Extraction Micro-Feature
Alur: ZIP => EXTRACT => RESTORE
Purpose: Extract and analyze date/time data from specified database tables
"""

import pyodbc
import json
import zipfile
import os
import shutil
from datetime import datetime, timedelta
import numpy as np
from decimal import Decimal
import argparse
import sys

class DateExtractionMicroFeature:
    def __init__(self, database_name=None, server='localhost', username='sa', password='windows0819'):
        self.server = server
        self.username = username
        self.password = password
        self.database_name = database_name  # Specific database to connect to
        self.output_dir = 'date_extraction_output'
        self.backup_dir = 'date_extraction_backups'

        # Table configurations based on analysis
        self.table_configs = {
            'staging_PTRJ_iFES_Plantware': {
                'Gwscannerdata': {
                    'date_columns': ['TRANSDATE', 'DATECREATED', 'INTEGRATETIME', 'SCANOUTDATETIME'],
                    'primary_date': 'TRANSDATE',
                    'description': 'Worker movement scanner data'
                },
                'Ffbscannerdata': {
                    'date_columns': ['TRANSDATE', 'DATECREATED', 'INTEGRATETIME'],
                    'primary_date': 'TRANSDATE',
                    'description': 'FFB quality scanner data'
                }
            },
            'db_ptrj': {
                'PR_Taskreg': {
                    'date_columns': ['DocDate', 'CreatedDate', 'UpdatedDate'],
                    'primary_date': 'DocDate',
                    'description': 'Payroll task registration'
                },
                'IN_FUELISSUE': {
                    'date_columns': ['CreateDate', 'UpdateDate', 'PrintDate', 'PostDate', 'FuelIssueRefDate'],
                    'primary_date': 'CreateDate',
                    'description': 'Fuel issue management'
                }
            },
            'VenusHR14': {
                'HR_T_TAMachine': {
                    'date_columns': ['TADate'],
                    'primary_date': 'TADate',
                    'description': 'Time attendance machine data'
                }
            }
        }

    def create_directory_structure(self):
        """Create necessary directory structure"""
        for dir_path in [self.output_dir, self.backup_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                print(f"Created directory: {dir_path}")

    def get_database_connection(self):
        """Establish database connection"""
        try:
            if self.database_name:
                # Connect to specific database using ODBC Driver 17
                conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.server};DATABASE={self.database_name};UID={self.username};PWD={self.password};Trusted_Connection=no'
            else:
                # Connect to server without specific database
                conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.server};UID={self.username};PWD={self.password};Trusted_Connection=no'
            conn = pyodbc.connect(conn_str)
            return conn
        except Exception as e:
            print(f"Database connection error: {e}")
            return None

    def extract_date_data(self, cursor, db_name, table_name, config, progress_callback=None):
        """Extract date data from specific table"""
        print(f"Extracting date data from {db_name}.{table_name}")

        date_data = {
            'database': db_name,
            'table': table_name,
            'description': config['description'],
            'extraction_timestamp': datetime.now().isoformat(),
            'date_columns': {},
            'summary_statistics': {}
        }

        for date_column in config['date_columns']:
            print(f"  Processing column: {date_column}")
            if progress_callback:
                progress_callback(f"  [ANALYZE] Processing column: {date_column}")

            try:
                # Basic statistics
                cursor.execute(f"""
                    SELECT
                        MIN({date_column}) as min_date,
                        MAX({date_column}) as max_date,
                        COUNT({date_column}) as non_null_count,
                        COUNT(*) as total_count,
                        COUNT(DISTINCT {date_column}) as distinct_count
                    FROM {table_name}
                    WHERE {date_column} IS NOT NULL
                """)

                stats = cursor.fetchone()
                min_date, max_date, non_null_count, total_count, distinct_count = stats

                if min_date is not None:
                    column_stats = {
                        'min_date': min_date,
                        'max_date': max_date,
                        'non_null_count': non_null_count,
                        'total_count': total_count,
                        'distinct_count': distinct_count,
                        'null_percentage': round(((total_count - non_null_count) / total_count) * 100, 2) if total_count > 0 else 0,
                        'data_span_days': (max_date - min_date).days if max_date and min_date else 0
                    }

                    # Year distribution
                    cursor.execute(f"""
                        SELECT
                            YEAR({date_column}) as year_val,
                            COUNT(*) as count
                        FROM {table_name}
                        WHERE {date_column} IS NOT NULL
                        GROUP BY YEAR({date_column})
                        ORDER BY year_val
                    """)

                    year_dist = cursor.fetchall()
                    column_stats['year_distribution'] = {str(row[0]): row[1] for row in year_dist}

                    # Recent monthly distribution (last 24 months)
                    cursor.execute(f"""
                        SELECT TOP 24
                            FORMAT({date_column}, 'yyyy-MM') as month_val,
                            COUNT(*) as count
                        FROM {table_name}
                        WHERE {date_column} IS NOT NULL
                        GROUP BY FORMAT({date_column}, 'yyyy-MM')
                        ORDER BY FORMAT({date_column}, 'yyyy-MM') DESC
                    """)

                    month_dist = cursor.fetchall()
                    column_stats['monthly_distribution'] = {row[0]: row[1] for row in month_dist}

                    # Sample recent records (last 10)
                    cursor.execute(f"""
                        SELECT TOP 10 *
                        FROM {table_name}
                        WHERE {date_column} IS NOT NULL
                        ORDER BY {date_column} DESC
                    """)

                    sample_records = cursor.fetchall()
                    column_names = [desc[0] for desc in cursor.description]

                    column_stats['recent_samples'] = []
                    for record in sample_records:
                        record_dict = dict(zip(column_names, record))
                        column_stats['recent_samples'].append(record_dict)

                    date_data['date_columns'][date_column] = column_stats

            except Exception as e:
                print(f"    Error processing {date_column}: {e}")
                date_data['date_columns'][date_column] = {'error': str(e)}

        # Calculate summary statistics
        if date_data['date_columns']:
            primary_col = config['primary_date']
            if primary_col in date_data['date_columns'] and 'error' not in date_data['date_columns'][primary_col]:
                primary_stats = date_data['date_columns'][primary_col]
                date_data['summary_statistics'] = {
                    'data_period_start': primary_stats['min_date'],
                    'data_period_end': primary_stats['max_date'],
                    'total_days_span': primary_stats['data_span_days'],
                    'total_records': primary_stats['total_count'],
                    'records_per_day': round(primary_stats['total_count'] / max(primary_stats['data_span_days'], 1), 2),
                    'data_completeness': f"{(primary_stats['non_null_count'] / primary_stats['total_count'] * 100):.1f}%"
                }

        return date_data

    def extract_all_date_data(self, progress_callback=None):
        """Extract date data from all configured tables"""
        print("Starting date data extraction...")
        self.create_directory_structure()

        conn = self.get_database_connection()
        if not conn:
            return False

        cursor = conn.cursor()
        extraction_results = {
            'extraction_metadata': {
                'timestamp': datetime.now().isoformat(),
                'server': self.server,
                'databases_processed': [],
                'total_tables': 0
            },
            'database_results': {}
        }

        total_tables = 0
        for db_name, tables in self.table_configs.items():
            print(f"\nProcessing database: {db_name}")
            if progress_callback:
                progress_callback(f"[PROCESS] Processing database: {db_name}")

            extraction_results['extraction_metadata']['databases_processed'].append(db_name)

            try:
                cursor.execute(f'USE {db_name}')
                extraction_results['database_results'][db_name] = {}

                for table_name, config in tables.items():
                    total_tables += 1
                    print(f"  Extracting from table: {table_name}")
                    if progress_callback:
                        progress_callback(f"[EXTRACT] Processing table: {table_name}")

                    table_data = self.extract_date_data(cursor, db_name, table_name, config, progress_callback)
                    extraction_results['database_results'][db_name][table_name] = table_data

                    # Show latest date info for this table
                    if 'error' not in table_data and 'summary_statistics' in table_data:
                        stats = table_data['summary_statistics']
                        latest_date = stats.get('data_period_end', 'N/A')
                        record_count = stats.get('total_records', 0)
                        print(f"  [OK] {table_name}: {record_count:,} records, latest: {latest_date}")
                        if progress_callback:
                            progress_callback(f"[OK] {table_name}: {record_count:,} records, latest: {latest_date}")

            except Exception as e:
                print(f"Error processing database {db_name}: {e}")
                extraction_results['database_results'][db_name] = {'error': str(e)}
                if progress_callback:
                    progress_callback(f"[ERROR] Processing {db_name}: {e}")

        extraction_results['extraction_metadata']['total_tables'] = total_tables

        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(self.output_dir, f'date_extraction_{timestamp}.json')

        with open(output_file, 'w') as f:
            json.dump(extraction_results, f, indent=2, cls=DateTimeEncoder)

        print(f"\nExtraction completed. Results saved to: {output_file}")
        print(f"Total databases processed: {len(extraction_results['extraction_metadata']['databases_processed'])}")
        print(f"Total tables processed: {total_tables}")

        cursor.close()
        conn.close()

        return output_file

    def create_backup(self, file_to_backup):
        """Create backup of extracted data"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'date_extraction_backup_{timestamp}.zip'
        backup_path = os.path.join(self.backup_dir, backup_filename)

        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if os.path.isfile(file_to_backup):
                zipf.write(file_to_backup, os.path.basename(file_to_backup))
                print(f"Added to backup: {os.path.basename(file_to_backup)}")

            # Add configuration info
            config_info = {
                'backup_timestamp': timestamp,
                'original_file': file_to_backup,
                'table_configs': self.table_configs
            }
            zipf.writestr('backup_info.json', json.dumps(config_info, indent=2))

        print(f"Backup created: {backup_path}")
        return backup_path

    def extract_backup(self, backup_file):
        """Extract data from backup zip file"""
        extract_dir = os.path.join(self.output_dir, f'extracted_{datetime.now().strftime("%Y%m%d_%H%M%S")}')

        if not os.path.exists(extract_dir):
            os.makedirs(extract_dir)

        try:
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(extract_dir)
                print(f"Backup extracted to: {extract_dir}")

                # List extracted files
                extracted_files = []
                for file_info in zipf.filelist:
                    extracted_files.append(file_info.filename)

                return extract_dir, extracted_files

        except Exception as e:
            print(f"Error extracting backup: {e}")
            return None, []

    def restore_from_backup(self, backup_file):
        """Restore and analyze data from backup"""
        print(f"Restoring from backup: {backup_file}")

        extract_dir, extracted_files = self.extract_backup(backup_file)
        if not extract_dir:
            return False

        # Find the JSON data file
        json_file = None
        for file in extracted_files:
            if file.endswith('.json') and file != 'backup_info.json':
                json_file = os.path.join(extract_dir, file)
                break

        if json_file and os.path.exists(json_file):
            print(f"Found data file: {json_file}")
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                self.analyze_extracted_data(data)
                return True
            except Exception as e:
                print(f"Error reading data file: {e}")
                return False
        else:
            print("No valid data file found in backup")
            return False

    def analyze_extracted_data(self, data):
        """Analyze extracted data for insights"""
        print("\n" + "="*50)
        print("DATE DATA ANALYSIS REPORT")
        print("="*50)

        if 'database_results' not in data:
            print("Invalid data format")
            return

        for db_name, db_data in data['database_results'].items():
            if 'error' in db_data:
                print(f"\nERROR: Database {db_name}: Error - {db_data['error']}")
                continue

            print(f"\nDATABASE: {db_name}")
            print("-" * 30)

            for table_name, table_data in db_data.items():
                if 'error' in table_data:
                    print(f"  ERROR: Table {table_name}: Error - {table_data['error']}")
                    continue

                print(f"  TABLE: {table_name} ({table_data.get('description', 'N/A')})")

                if 'summary_statistics' in table_data:
                    stats = table_data['summary_statistics']
                    print(f"     PERIOD: {stats.get('data_period_start', 'N/A')} to {stats.get('data_period_end', 'N/A')}")
                    print(f"     SPAN: {stats.get('total_days_span', 0)} days")
                    print(f"     RECORDS: {stats.get('total_records', 0):,}")
                    print(f"     DAILY AVG: {stats.get('records_per_day', 0):.1f} records/day")
                    print(f"     COMPLETENESS: {stats.get('data_completeness', 'N/A')}")

                # Show date columns found
                for col_name, col_data in table_data.get('date_columns', {}).items():
                    if 'error' not in col_data:
                        print(f"     DATE COLUMN: {col_name}: {col_data.get('non_null_count', 0):,} records")

    def run_zip_extract_restore(self):
        """Run complete zip -> extract -> restore workflow"""
        print("Running ZIP -> EXTRACT -> RESTORE workflow")
        print("=" * 50)

        # Step 1: Extract data
        print("\nStep 1: EXTRACT - Getting data from database")
        extracted_file = self.extract_all_date_data()

        if not extracted_file:
            print("FAILED: Extraction failed")
            return False

        # Step 2: Create backup (ZIP)
        print("\nStep 2: ZIP - Creating backup")
        backup_file = self.create_backup(extracted_file)

        # Step 3: Extract from backup
        print("\nStep 3: EXTRACT FROM BACKUP - Restoring data")
        success = self.restore_from_backup(backup_file)

        if success:
            print("\nSUCCESS: ZIP -> EXTRACT -> RESTORE workflow completed successfully!")
            return True
        else:
            print("\nFAILED: RESTORE step failed")
            return False

    def interactive_mode(self):
        """Interactive mode for testing individual features"""
        while True:
            print("\n" + "="*50)
            print("DATE EXTRACTION MICRO-FEATURE")
            print("="*50)
            print("1. Extract date data from database")
            print("2. Create backup of existing data")
            print("3. Extract from backup")
            print("4. Run complete workflow (ZIP→EXTRACT→RESTORE)")
            print("5. View table configurations")
            print("6. Exit")
            print("="*50)

            choice = input("Select option (1-6): ").strip()

            if choice == '1':
                self.extract_all_date_data()
            elif choice == '2':
                json_files = [f for f in os.listdir(self.output_dir) if f.endswith('.json')]
                if json_files:
                    print("Available JSON files:")
                    for i, f in enumerate(json_files, 1):
                        print(f"  {i}. {f}")
                    file_choice = int(input("Select file number: ")) - 1
                    if 0 <= file_choice < len(json_files):
                        file_path = os.path.join(self.output_dir, json_files[file_choice])
                        self.create_backup(file_path)
                else:
                    print("No JSON files found to backup")
            elif choice == '3':
                zip_files = [f for f in os.listdir(self.backup_dir) if f.endswith('.zip')]
                if zip_files:
                    print("Available backup files:")
                    for i, f in enumerate(zip_files, 1):
                        print(f"  {i}. {f}")
                    file_choice = int(input("Select backup number: ")) - 1
                    if 0 <= file_choice < len(zip_files):
                        file_path = os.path.join(self.backup_dir, zip_files[file_choice])
                        self.restore_from_backup(file_path)
                else:
                    print("No backup files found")
            elif choice == '4':
                self.run_zip_extract_restore()
            elif choice == '5':
                self.show_table_configurations()
            elif choice == '6':
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")

    def show_table_configurations(self):
        """Display configured table information"""
        print("\nConfigured Tables:")
        print("="*50)

        for db_name, tables in self.table_configs.items():
            print(f"\nDATABASE: {db_name}")
            for table_name, config in tables.items():
                print(f"  TABLE: {table_name}")
                print(f"     DESCRIPTION: {config['description']}")
                print(f"     PRIMARY DATE: {config['primary_date']}")
                print(f"     DATE COLUMNS: {', '.join(config['date_columns'])}")

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def main():
    parser = argparse.ArgumentParser(description='Date Extraction Micro-Feature')
    parser.add_argument('--mode', choices=['extract', 'backup', 'restore', 'workflow', 'interactive'],
                       default='interactive', help='Operation mode')
    parser.add_argument('--input', help='Input file for backup/restore operations')
    parser.add_argument('--output', help='Output file/directory')

    args = parser.parse_args()

    feature = DateExtractionMicroFeature()

    if args.mode == 'extract':
        feature.extract_all_date_data()
    elif args.mode == 'backup' and args.input:
        feature.create_backup(args.input)
    elif args.mode == 'restore' and args.input:
        feature.restore_from_backup(args.input)
    elif args.mode == 'workflow':
        feature.run_zip_extract_restore()
    else:
        feature.interactive_mode()

if __name__ == "__main__":
    main()