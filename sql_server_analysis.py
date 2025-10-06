#!/usr/bin/env python3
"""
SQL Server Database Analysis (no emoji version)
Menggunakan SQL Server untuk restore dan analisis database
"""

import sys
import os
import subprocess
from datetime import datetime

def check_sql_server():
    """Cek instalasi SQL Server"""
    print("=" * 80)
    print("CHECKING SQL SERVER INSTALLATION")
    print("=" * 80)
    print()

    # Cek SQL Server service
    print("Checking SQL Server services...")
    try:
        result = subprocess.run(['sc', 'query', 'MSSQLSERVER'], capture_output=True, text=True, timeout=10)
        if 'RUNNING' in result.stdout:
            print("[OK] SQL Server (MSSQLSERVER) service is running")
        else:
            print("[ERROR] SQL Server (MSSQLSERVER) service not found or not running")
            print("Available services:")
            result_all = subprocess.run(['sc', 'query', 'state=', 'all'], capture_output=True, text=True, timeout=30)
            sql_services = [line for line in result_all.stdout.split('\n') if 'SQL' in line and 'SERVICE_NAME' in line]
            for service in sql_services:
                print(f"  - {service.strip()}")
    except Exception as e:
        print(f"[ERROR] Error checking SQL Server service: {e}")

    # Cek sqlcmd availability
    print("\nChecking sqlcmd availability...")
    try:
        result = subprocess.run(['sqlcmd', '-?',], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("[OK] sqlcmd is available")
            return True
        else:
            print("[ERROR] sqlcmd not found")
    except FileNotFoundError:
        print("[ERROR] sqlcmd not found in PATH")
    except Exception as e:
        print(f"[ERROR] Error checking sqlcmd: {e}")

    return False

def test_sql_connection():
    """Test koneksi SQL Server"""
    print("\n" + "=" * 80)
    print("TESTING SQL SERVER CONNECTION")
    print("=" * 80)
    print()

    # Try Windows Authentication
    print("Testing Windows Authentication...")
    try:
        # Test dengan sqlcmd
        test_query = "SELECT @@VERSION as SQL_Server_Version"
        result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', test_query],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print("[OK] Connected to SQL Server with Windows Authentication")
            # Extract version info
            lines = result.stdout.split('\n')
            for line in lines:
                if 'SQL Server' in line and 'Version' not in line:
                    print(f"   Version: {line.strip()}")
                    break
            return True
        else:
            print(f"[ERROR] Connection failed: {result.stderr}")
    except Exception as e:
        print(f"[ERROR] Error testing connection: {e}")

    return False

def try_staging_restore():
    """Coba restore database Staging"""
    print("\n" + "=" * 80)
    print("TRYING STAGING DATABASE RESTORE")
    print("=" * 80)
    print()

    staging_zip = r"D:/Gawean Rebinmas/App_Auto_Backup/Backup/BackupStaging 2025-10-04 09;16;30.zip"

    if not os.path.exists(staging_zip):
        print(f"[ERROR] Staging backup not found: {staging_zip}")
        return False

    print(f"Staging backup: {staging_zip}")

    # Extract ZIP first
    import zipfile
    import tempfile

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Extracting to temporary directory...")
            with zipfile.ZipFile(staging_zip, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Find BAK file
            bak_files = [f for f in os.listdir(temp_dir) if f.endswith('.bak')]
            if not bak_files:
                print("[ERROR] No BAK file found in ZIP")
                return False

            bak_path = os.path.join(temp_dir, bak_files[0])
            print(f"Found BAK file: {bak_files[0]}")

            # Try to restore
            db_name = "Staging_Restored"
            print(f"Attempting to restore as database: {db_name}")

            # Check backup first
            print("Checking backup file...")
            check_cmd = f'sqlcmd -S localhost -Q "RESTORE FILELISTONLY FROM DISK = \'{bak_path}\'"'
            result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                print("[OK] Backup file is readable by SQL Server")

                # Try restore
                restore_cmd = f'sqlcmd -S localhost -Q "RESTORE DATABASE [{db_name}] FROM DISK = \'{bak_path}\' WITH REPLACE"'
                result = subprocess.run(restore_cmd, shell=True, capture_output=True, text=True, timeout=300)

                if result.returncode == 0:
                    print(f"[OK] Database {db_name} restored successfully!")
                    return db_name
                else:
                    print(f"[ERROR] Restore failed: {result.stderr}")
            else:
                print(f"[ERROR] Cannot read backup file: {result.stderr}")

    except Exception as e:
        print(f"[ERROR] Error during staging restore: {e}")

    return False

def examine_staging_database(db_name):
    """Examine restored Staging database"""
    print(f"\n{'='*80}")
    print(f"EXAMINING STAGING DATABASE: {db_name}")
    print('='*80)

    # List all tables
    print("Listing all tables...")
    try:
        query = f"SELECT TABLE_NAME FROM {db_name}.INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME"
        result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1', '-s', ','],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            tables = [line.strip() for line in result.stdout.split('\n') if line.strip() and not line.startswith('-')]
            print(f"Found {len(tables)} tables:")

            # Look for GWSCANNER related tables
            scanner_tables = []
            for i, table in enumerate(tables):
                table_upper = table.upper()
                if 'GWSCANNER' in table_upper or 'SCANNER' in table_upper or 'GATEWAY' in table_upper:
                    scanner_tables.append(table)

            if scanner_tables:
                print(f"\nScanner-related tables found:")
                for table in scanner_tables:
                    print(f"  - {table}")
                return scanner_tables
            else:
                print("\nNo scanner-related tables found")
                print("First 10 tables:")
                for i, table in enumerate(tables[:10]):
                    print(f"  {i+1}. {table}")
        else:
            print(f"[ERROR] Error listing tables: {result.stderr}")
    except Exception as e:
        print(f"[ERROR] Error examining database: {e}")

    return []

def examine_table_details(db_name, table_name):
    """Examine table structure and data"""
    print(f"\n{'='*80}")
    print(f"EXAMINING TABLE: {table_name}")
    print('='*80)

    # Get table structure
    print("Table structure:")
    try:
        query = f"SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE FROM {db_name}.INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}' ORDER BY ORDINAL_POSITION"
        result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1', '-s', '|'],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            lines = [line.strip() for line in result.stdout.split('\n') if line.strip() and not line.startswith('-')]
            if lines:
                print("Columns:")
                for line in lines:
                    if '|' in line:
                        parts = [p.strip() for p in line.split('|')]
                        if len(parts) >= 3:
                            print(f"  {parts[0]:25} {parts[1]:15} {parts[2]}")
    except Exception as e:
        print(f"[ERROR] Error getting table structure: {e}")

    # Get row count
    print(f"\nRow count:")
    try:
        query = f"SELECT COUNT(*) as Row_Count FROM {db_name}.dbo.{table_name}"
        result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1'],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.strip().isdigit():
                    print(f"  Total rows: {int(line.strip()):,}")
                    break
    except Exception as e:
        print(f"[ERROR] Error getting row count: {e}")

    # Look for date columns and get latest dates
    print(f"\nLooking for date columns...")
    date_columns = []
    try:
        query = f"SELECT COLUMN_NAME FROM {db_name}.INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}' AND (DATA_TYPE LIKE '%date%' OR DATA_TYPE LIKE '%time%')"
        result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1'],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.strip() and not line.startswith('-'):
                    date_columns.append(line.strip())

        if date_columns:
            print(f"Date/Time columns found: {date_columns}")
            print("\nLatest dates:")

            for col in date_columns:
                try:
                    query = f"SELECT TOP 1 {col} FROM {db_name}.dbo.{table_name} WHERE {col} IS NOT NULL ORDER BY {col} DESC"
                    result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1'],
                                          capture_output=True, text=True, timeout=30)

                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if line.strip() and not line.startswith('-') and not line.strip().startswith('('):
                                print(f"  Latest {col}: {line.strip()}")
                                break
                except Exception as e:
                    print(f"  Error getting latest {col}: {e}")
        else:
            print("No date/time columns found")
    except Exception as e:
        print(f"[ERROR] Error finding date columns: {e}")

    # Get sample data
    print(f"\nSample data (first 5 rows):")
    try:
        # First get column names
        query = f"SELECT COLUMN_NAME FROM {db_name}.INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}' ORDER BY ORDINAL_POSITION"
        result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1'],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            columns = [line.strip() for line in result.stdout.split('\n') if line.strip() and not line.startswith('-')]
            if columns:
                # Select first 5 columns to avoid overflow
                selected_cols = ', '.join(columns[:5])
                query = f"SELECT TOP 5 {selected_cols} FROM {db_name}.dbo.{table_name} ORDER BY 1 DESC"
                result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1', '-s', ' | '],
                                      capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    lines = [line.strip() for line in result.stdout.split('\n') if line.strip() and not line.startswith('-')]
                    if lines:
                        print("Data:")
                        for i, line in enumerate(lines):
                            print(f"  {i+1}. {line}")
    except Exception as e:
        print(f"[ERROR] Error getting sample data: {e}")

def main():
    """Main function"""
    print("SQL SERVER DATABASE RESTORE AND ANALYSIS")
    print("=" * 80)

    # Step 1: Check SQL Server
    if not check_sql_server():
        print("\n[ERROR] SQL Server is not properly installed or accessible")
        print("Please ensure SQL Server is installed and running")
        return

    # Step 2: Test connection
    if not test_sql_connection():
        print("\n[ERROR] Cannot connect to SQL Server")
        print("Please check SQL Server service and authentication")
        return

    # Step 3: Try restore Staging database (smaller file)
    print("\nTrying to restore Staging database first (smaller file)...")
    db_name = try_staging_restore()
    if not db_name:
        print("\n[ERROR] Failed to restore Staging database")
        return

    # Step 4: Examine database
    scanner_tables = examine_staging_database(db_name)
    if scanner_tables:
        for table_name in scanner_tables:
            examine_table_details(db_name, table_name)
    else:
        print("\nNo scanner tables found, showing all tables for manual inspection")
        examine_staging_database(db_name)

    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()