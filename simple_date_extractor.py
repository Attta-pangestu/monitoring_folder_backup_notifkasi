#!/usr/bin/env python3
"""
Simple Date Extractor - Testing Version
Purpose: Quick test of date extraction functionality
"""

import pyodbc
import json
import zipfile
import os
from datetime import datetime

class SimpleDateExtractor:
    def __init__(self):
        self.server = 'localhost'
        self.username = 'sa'
        self.password = 'windows0819'
        self.output_dir = 'date_extraction_output'

    def create_directory_structure(self):
        """Create necessary directory structure"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Created directory: {self.output_dir}")

    def get_database_connection(self):
        """Establish database connection"""
        try:
            conn_str = f'DRIVER={{SQL Server}};SERVER={self.server};UID={self.username};PWD={self.password}'
            conn = pyodbc.connect(conn_str)
            return conn
        except Exception as e:
            print(f"Database connection error: {e}")
            return None

    def test_single_table(self):
        """Test extraction from one table only"""
        print("Testing single table extraction...")

        conn = self.get_database_connection()
        if not conn:
            return False

        cursor = conn.cursor()
        self.create_directory_structure()

        try:
            # Test with Gwscannerdata only
            cursor.execute('USE staging_PTRJ_iFES_Plantware')

            # Get basic date info from TRANSDATE
            cursor.execute("""
                SELECT
                    MIN(TRANSDATE) as min_date,
                    MAX(TRANSDATE) as max_date,
                    COUNT(TRANSDATE) as record_count,
                    COUNT(DISTINCT CONVERT(date, TRANSDATE)) as unique_days
                FROM Gwscannerdata
                WHERE TRANSDATE IS NOT NULL
            """)

            result = cursor.fetchone()
            min_date, max_date, record_count, unique_days = result

            test_result = {
                'test_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'table_tested': 'staging_PTRJ_iFES_Plantware.Gwscannerdata',
                    'column_tested': 'TRANSDATE'
                },
                'results': {
                    'min_date': str(min_date),
                    'max_date': str(max_date),
                    'total_records': record_count,
                    'unique_days': unique_days,
                    'avg_records_per_day': round(record_count / unique_days, 2) if unique_days > 0 else 0
                }
            }

            # Save test result
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(self.output_dir, f'test_extraction_{timestamp}.json')

            with open(output_file, 'w') as f:
                json.dump(test_result, f, indent=2)

            print(f"Test completed successfully!")
            print(f"Results saved to: {output_file}")
            print(f"Date range: {min_date} to {max_date}")
            print(f"Total records: {record_count:,}")
            print(f"Unique days: {unique_days}")
            print(f"Avg records/day: {test_result['results']['avg_records_per_day']:,.2f}")

            return True

        except Exception as e:
            print(f"Error during test: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def test_backup_functionality(self):
        """Test backup creation"""
        print("\nTesting backup functionality...")

        # Find existing JSON file
        if not os.path.exists(self.output_dir):
            print("No output directory found")
            return False

        json_files = [f for f in os.listdir(self.output_dir) if f.endswith('.json')]
        if not json_files:
            print("No JSON files found to backup")
            return False

        # Use the most recent file
        latest_file = max(json_files, key=lambda f: os.path.getmtime(os.path.join(self.output_dir, f)))
        file_path = os.path.join(self.output_dir, latest_file)

        print(f"Creating backup of: {latest_file}")

        # Create backup
        backup_dir = 'date_extraction_backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'test_backup_{timestamp}.zip')

        try:
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(file_path, latest_file)

                # Add backup info
                backup_info = {
                    'backup_timestamp': timestamp,
                    'original_file': latest_file,
                    'test_type': 'simple_date_extraction_test'
                }
                zipf.writestr('backup_info.json', json.dumps(backup_info, indent=2))

            print(f"Backup created successfully: {backup_file}")
            return True

        except Exception as e:
            print(f"Backup creation failed: {e}")
            return False

    def test_restore_functionality(self):
        """Test restore from backup"""
        print("\nTesting restore functionality...")

        backup_dir = 'date_extraction_backups'
        if not os.path.exists(backup_dir):
            print("No backup directory found")
            return False

        zip_files = [f for f in os.listdir(backup_dir) if f.endswith('.zip')]
        if not zip_files:
            print("No backup files found")
            return False

        # Use the most recent backup
        latest_backup = max(zip_files, key=lambda f: os.path.getmtime(os.path.join(backup_dir, f)))
        backup_path = os.path.join(backup_dir, latest_backup)

        print(f"Testing restore from: {latest_backup}")

        try:
            # Extract backup info
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                with zipf.open('backup_info.json') as f:
                    backup_info = json.load(f)

                print(f"Backup info:")
                print(f"  Created: {backup_info['backup_timestamp']}")
                print(f"  Original file: {backup_info['original_file']}")
                print(f"  Test type: {backup_info['test_type']}")

            return True

        except Exception as e:
            print(f"Restore test failed: {e}")
            return False

    def run_complete_test(self):
        """Run complete test workflow"""
        print("=== SIMPLE DATE EXTRACTOR TEST ===")
        print("Testing: EXTRACT -> BACKUP -> RESTORE")
        print("=" * 40)

        # Step 1: Extract
        print("\n1. EXTRACTING data...")
        if not self.test_single_table():
            print("FAILED: Extract failed")
            return False

        # Step 2: Backup
        print("\n2. CREATING backup...")
        if not self.test_backup_functionality():
            print("FAILED: Backup failed")
            return False

        # Step 3: Restore
        print("\n3. TESTING restore...")
        if not self.test_restore_functionality():
            print("FAILED: Restore test failed")
            return False

        print("\nSUCCESS: COMPLETE TEST SUCCESSFUL!")
        print("All components working correctly.")
        return True

if __name__ == "__main__":
    extractor = SimpleDateExtractor()
    extractor.run_complete_test()