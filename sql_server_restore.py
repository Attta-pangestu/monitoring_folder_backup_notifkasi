#!/usr/bin/env python3
"""
SQL Server Database Restore and Analysis
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
        print(f"❌ Error checking SQL Server service: {e}")

    # Cek sqlcmd availability
    print("\nChecking sqlcmd availability...")
    try:
        result = subprocess.run(['sqlcmd', '-?',], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ sqlcmd is available")
            return True
        else:
            print("❌ sqlcmd not found")
    except FileNotFoundError:
        print("❌ sqlcmd not found in PATH")
    except Exception as e:
        print(f"❌ Error checking sqlcmd: {e}")

    # Cek PowerShell SQL Server module
    print("\nChecking PowerShell SQL Server module...")
    try:
        result = subprocess.run(['powershell', '-Command', 'Get-Module -Name SqlServer -ListAvailable'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            print("✅ SQL Server PowerShell module is available")
            return True
        else:
            print("⚠️  SQL Server PowerShell module not found (install with: Install-Module SqlServer)")
    except Exception as e:
        print(f"❌ Error checking PowerShell module: {e}")

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
            print("✅ Connected to SQL Server with Windows Authentication")
            # Extract version info
            lines = result.stdout.split('\n')
            for line in lines:
                if 'SQL Server' in line and 'Version' not in line:
                    print(f"   Version: {line.strip()}")
                    break
            return True
        else:
            print(f"❌ Connection failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Error testing connection: {e}")

    # Try dengan instance name
    print("\nTrying with instance name...")
    try:
        result = subprocess.run(['sqlcmd', '-S', 'localhost\\SQLEXPRESS', '-Q', test_query],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print("✅ Connected to SQL Server Express")
            return True
        else:
            print(f"❌ SQL Server Express connection failed")
    except Exception as e:
        print(f"❌ Error testing SQL Express: {e}")

    return False

def restore_database():
    """Coba restore database PlantwareP3"""
    print("\n" + "=" * 80)
    print("RESTORING PLANTWARE DATABASE")
    print("=" * 80)
    print()

    bak_path = r"D:/Gawean Rebinmas/App_Auto_Backup/Backup/PlantwareP3"
    db_name = "Plantware_Restored"

    if not os.path.exists(bak_path):
        print(f"❌ Backup file not found: {bak_path}")
        return False

    print(f"Backup file: {bak_path}")
    print(f"Target database: {db_name}")

    # Check logical file names in backup
    print("\nChecking backup file contents...")
    try:
        cmd = f'sqlcmd -S localhost -Q "RESTORE FILELISTONLY FROM DISK = \'{bak_path}\'"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            print("✅ Backup file is readable")
            print("Backup contains:")
            lines = result.stdout.split('\n')
            for line in lines:
                if 'LogicalName' in line or 'PhysicalName' in line or 'Type' in line:
                    print(f"  {line.strip()}")

            # Extract logical names
            logical_names = []
            for line in lines:
                if len(line.strip()) > 10 and not line.startswith('-') and not line.startswith('LogicalName'):
                    parts = line.split()
                    if len(parts) >= 2:
                        logical_names.append(parts[0])

            if len(logical_names) >= 2:
                data_file = logical_names[0]
                log_file = logical_names[1]
                print(f"\nUsing logical names: Data={data_file}, Log={log_file}")

                # Restore database
                print(f"\nRestoring database {db_name}...")
                restore_cmd = f'''
                sqlcmd -S localhost -Q "
                RESTORE DATABASE [{db_name}]
                FROM DISK = '{bak_path}'
                WITH MOVE '{data_file}' TO 'C:\\SQLData\\{db_name}_Data.mdf',
                MOVE '{log_file}' TO 'C:\\SQLData\\{db_name}_Log.ldf',
                REPLACE"
                '''

                result = subprocess.run(restore_cmd, shell=True, capture_output=True, text=True, timeout=300)

                if result.returncode == 0:
                    print("✅ Database restored successfully!")
                    return db_name
                else:
                    print(f"❌ Restore failed: {result.stderr}")
                    print("Trying alternative restore method...")

                    # Try simple restore
                    simple_restore = f'sqlcmd -S localhost -Q "RESTORE DATABASE [{db_name}] FROM DISK = \'{bak_path}\' WITH REPLACE"'
                    result = subprocess.run(simple_restore, shell=True, capture_output=True, text=True, timeout=300)

                    if result.returncode == 0:
                        print("✅ Database restored with simple method!")
                        return db_name
                    else:
                        print(f"❌ Simple restore also failed: {result.stderr}")
            else:
                print("❌ Could not extract logical file names")
        else:
            print(f"❌ Could not read backup file: {result.stderr}")
    except Exception as e:
        print(f"❌ Error during restore: {e}")

    return False

def examine_database(db_name):
    """Examine restored database"""
    print("\n" + "=" * 80)
    print(f"EXAMINING DATABASE: {db_name}")
    print("=" * 80)
    print()

    # List tables
    print("Listing tables...")
    try:
        query = f"SELECT TABLE_NAME FROM {db_name}.INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME"
        result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1', '-s', ','],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            tables = [line.strip() for line in result.stdout.split('\n') if line.strip() and not line.startswith('-')]
            print(f"Found {len(tables)} tables:")
            for i, table in enumerate(tables[:20]):  # Show first 20
                print(f"  {i+1}. {table}")
            if len(tables) > 20:
                print(f"  ... and {len(tables) - 20} more tables")

            # Look for GWSCANNER tables
            gwscanner_tables = [t for t in tables if 'GWSCANNER' in t.upper()]
            if gwscanner_tables:
                print(f"\n✅ GWSCANNER tables found: {gwscanner_tables}")
                return gwscanner_tables
            else:
                print("\n❌ No GWSCANNER tables found")
                return []
        else:
            print(f"❌ Error listing tables: {result.stderr}")
    except Exception as e:
        print(f"❌ Error examining database: {e}")

    return []

def examine_gwscanner_table(db_name, table_name):
    """Examine GWSCANNER table structure and data"""
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
                            print(f"  {parts[0]:20} {parts[1]:15} {parts[2]}")
    except Exception as e:
        print(f"❌ Error getting table structure: {e}")

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
        print(f"❌ Error getting row count: {e}")

    # Get sample data
    print(f"\nSample data (first 10 rows):")
    try:
        query = f"SELECT TOP 10 * FROM {db_name}.dbo.{table_name} ORDER BY 1 DESC"
        result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1', '-s', '|', '-W'],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            lines = [line.strip() for line in result.stdout.split('\n') if line.strip() and not line.startswith('-')]
            if lines:
                print("Data:")
                for i, line in enumerate(lines[:10]):
                    print(f"  {i+1}. {line}")
    except Exception as e:
        print(f"❌ Error getting sample data: {e}")

    # Look for date columns specifically
    print(f"\nLatest dates:")
    date_columns = []
    try:
        query = f"SELECT COLUMN_NAME FROM {db_name}.INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}' AND DATA_TYPE IN ('datetime', 'date', 'datetime2', 'smalldatetime')"
        result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1'],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.strip() and not line.startswith('-'):
                    date_columns.append(line.strip())

        if date_columns:
            print(f"Date columns found: {date_columns}")
            for col in date_columns:
                query = f"SELECT DISTINCT TOP 5 {col} FROM {db_name}.dbo.{table_name} WHERE {col} IS NOT NULL ORDER BY {col} DESC"
                result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1'],
                                      capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    dates = []
                    for line in result.stdout.split('\n'):
                        if line.strip() and not line.startswith('-'):
                            dates.append(line.strip())
                    if dates:
                        print(f"  Latest {col}: {dates[0]}")
        else:
            print("No date columns found")
    except Exception as e:
        print(f"❌ Error finding date columns: {e}")

def main():
    """Main function"""
    print("SQL SERVER DATABASE RESTORE AND ANALYSIS")
    print("=" * 80)

    # Step 1: Check SQL Server
    if not check_sql_server():
        print("\n❌ SQL Server is not properly installed or accessible")
        print("Please ensure SQL Server is installed and running")
        return

    # Step 2: Test connection
    if not test_sql_connection():
        print("\n❌ Cannot connect to SQL Server")
        print("Please check SQL Server service and authentication")
        return

    # Step 3: Restore database
    db_name = restore_database()
    if not db_name:
        print("\n❌ Failed to restore database")
        return

    # Step 4: Examine database
    gwscanner_tables = examine_database(db_name)
    if gwscanner_tables:
        for table_name in gwscanner_tables:
            examine_gwscanner_table(db_name, table_name)
    else:
        print("\nNo GWSCANNER tables found to examine")

    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()