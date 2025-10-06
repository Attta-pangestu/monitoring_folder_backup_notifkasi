#!/usr/bin/env python3
"""
SQL Server Direct Query Analysis
Query langsung ke database yang sudah di-restore
"""

import sys
import os
import subprocess

def explore_database():
    """Jelajahi database yang sudah di-restore"""
    print("=" * 80)
    print("EXPLORING RESTORED DATABASE")
    print("=" * 80)
    print()

    db_name = "Staging_Restored"

    print(f"Database: {db_name}")

    # Coba cara berbeda untuk list tables
    print("\nTrying different methods to list tables...")

    methods = [
        # Method 1: sys.tables
        f"SELECT name as TableName FROM {db_name}.sys.tables ORDER BY name",
        # Method 2: sys.objects
        f"SELECT name as ObjectName FROM {db_name}.sys.objects WHERE type = 'U' ORDER BY name",
        # Method 3: INFORMATION_SCHEMA with different syntax
        f"USE {db_name}; SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'",
    ]

    for i, method in enumerate(methods, 1):
        print(f"\nMethod {i}:")
        try:
            result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', method, '-h', '-1', '-s', ','],
                                  capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                lines = [line.strip() for line in result.stdout.split('\n') if line.strip() and not line.startswith('-')]
                if lines and len(lines) > 1:
                    print(f"  Success! Found {len(lines)} potential tables:")
                    for j, line in enumerate(lines[:10]):
                        print(f"    {j+1}. {line}")
                    if len(lines) > 10:
                        print(f"    ... and {len(lines) - 10} more")

                    # Look for GWSCANNER in results
                    scanner_tables = []
                    for line in lines:
                        if 'GWSCANNER' in line.upper() or 'SCANNER' in line.upper():
                            scanner_tables.append(line)

                    if scanner_tables:
                        print(f"\n  Scanner tables found: {scanner_tables}")
                        return scanner_tables
                else:
                    print("  No results found")
            else:
                print(f"  Failed: {result.stderr}")
        except Exception as e:
            print(f"  Error: {e}")

    return []

def explore_table_structure(table_name):
    """Explore structure of specific table"""
    print(f"\n{'='*80}")
    print(f"EXPLORING TABLE: {table_name}")
    print('='*80)

    db_name = "Staging_Restored"

    # Get columns using sys.columns
    print("\nTable columns:")
    try:
        query = f"SELECT c.name as ColumnName, t.name as DataType, c.max_length, c.is_nullable FROM {db_name}.sys.columns c JOIN {db_name}.sys.types t ON c.user_type_id = t.user_type_id WHERE c.object_id = OBJECT_ID('{db_name}.dbo.{table_name}') ORDER BY c.column_id"
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
                            print(f"  {parts[0]:25} {parts[1]:15} {parts[2]:10} {parts[3] if len(parts) > 3 else ''}")
    except Exception as e:
        print(f"Error getting columns: {e}")

    # Get row count
    print(f"\nRow count:")
    try:
        query = f"SELECT COUNT(*) as RowCount FROM {db_name}.dbo.{table_name}"
        result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1'],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.strip().isdigit():
                    print(f"  Total rows: {int(line.strip()):,}")
                    break
    except Exception as e:
        print(f"Error getting row count: {e}")

    # Look for data
    print(f"\nSample data:")
    try:
        # Get some sample data
        query = f"SELECT TOP 10 * FROM {db_name}.dbo.{table_name}"
        result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1', '-s', ' | '],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            lines = [line.strip() for line in result.stdout.split('\n') if line.strip() and not line.startswith('-')]
            if lines:
                print("Sample rows:")
                for i, line in enumerate(lines[:5]):
                    print(f"  {i+1}. {line}")
    except Exception as e:
        print(f"Error getting sample data: {e}")

def find_scanner_data():
    """Cari data scanner di database"""
    print("\n" + "=" * 80)
    print("SEARCHING FOR SCANNER DATA")
    print("=" * 80)

    db_name = "Staging_Restored"

    # Cari semua stored procedure dan view yang mengandung scanner
    print("\nSearching for scanner-related objects...")

    search_queries = [
        # Tables
        f"SELECT name as ObjectName, type as ObjectType FROM {db_name}.sys.objects WHERE name LIKE '%GWSCANNER%' OR name LIKE '%SCANNER%' OR name LIKE '%GATEWAY%'",
        # Stored procedures
        f"SELECT name as ProcedureName FROM {db_name}.sys.procedures WHERE name LIKE '%GWSCANNER%' OR name LIKE '%SCANNER%' OR name LIKE '%GATEWAY%'",
        # Views
        f"SELECT name as ViewName FROM {db_name}.sys.views WHERE name LIKE '%GWSCANNER%' OR name LIKE '%SCANNER%' OR name LIKE '%GATEWAY%'",
    ]

    for query_desc, query in [
        ("Tables with scanner names", search_queries[0]),
        ("Procedures with scanner names", search_queries[1]),
        ("Views with scanner names", search_queries[2]),
    ]:
        print(f"\n{query_desc}:")
        try:
            result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1', '-s', ','],
                                  capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                lines = [line.strip() for line in result.stdout.split('\n') if line.strip() and not line.startswith('-')]
                if lines:
                    for line in lines:
                        print(f"  - {line}")
                else:
                    print("  No results found")
            else:
                print(f"  Query failed: {result.stderr}")
        except Exception as e:
            print(f"  Error: {e}")

    # Coba query langsung ke tabel yang mungkin
    print(f"\nTrying direct table access...")

    possible_tables = [
        "GWSCANNER",
        "GWSCANNERDATA",
        "SCANNER_DATA",
        "GATEWAY_DATA",
        "TBL_SCANNER",
        "TBL_GATEWAY"
    ]

    for table in possible_tables:
        print(f"\nTrying table: {table}")
        try:
            # Test jika table exists
            test_query = f"SELECT TOP 1 * FROM {db_name}.dbo.{table}"
            result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', test_query, '-h', '-1'],
                                  capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                print(f"  [SUCCESS] Table {table} exists!")
                explore_table_structure(table)
            else:
                error_msg = result.stderr
                if "Invalid object name" not in error_msg:
                    print(f"  Other error: {error_msg}")
        except Exception as e:
            pass

def try_plantware_restore():
    """Coba restore PlantwareP3"""
    print("\n" + "=" * 80)
    print("TRYING PLANTWARE RESTORE")
    print("=" * 80)

    bak_path = r"D:/Gawean Rebinmas/App_Auto_Backup/Backup/PlantwareP3"
    db_name = "Plantware_Restored"

    print(f"Attempting to restore: {bak_path}")
    print(f"Target database: {db_name}")

    # Check if file exists
    if not os.path.exists(bak_path):
        print(f"[ERROR] File not found: {bak_path}")
        return False

    # Try restore
    try:
        print("Checking backup file...")
        check_cmd = f'sqlcmd -S localhost -Q "RESTORE FILELISTONLY FROM DISK = \'{bak_path}\'"'
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True, timeout=120)

        if result.returncode == 0:
            print("[OK] Plantware backup is readable")

            # Extract logical names
            lines = result.stdout.split('\n')
            logical_names = []
            for line in lines:
                if len(line.strip()) > 10 and not line.startswith('LogicalName'):
                    parts = line.split()
                    if len(parts) >= 2:
                        logical_names.append(parts[0])

            if len(logical_names) >= 2:
                data_file = logical_names[0]
                log_file = logical_names[1]
                print(f"Logical files: Data={data_file}, Log={log_file}")

                # Restore with move
                print("Restoring database...")
                restore_cmd = f'''
                sqlcmd -S localhost -Q "
                RESTORE DATABASE [{db_name}]
                FROM DISK = '{bak_path}'
                WITH MOVE '{data_file}' TO 'C:\\SQLData\\{db_name}_Data.mdf',
                MOVE '{log_file}' TO 'C:\\SQLData\\{db_name}_Log.ldf',
                REPLACE"
                '''

                result = subprocess.run(restore_cmd, shell=True, capture_output=True, text=True, timeout=600)

                if result.returncode == 0:
                    print(f"[OK] Plantware database restored as {db_name}!")
                    return db_name
                else:
                    print(f"[ERROR] Restore failed: {result.stderr}")
            else:
                print("[ERROR] Could not extract logical file names")
        else:
            print(f"[ERROR] Cannot read backup: {result.stderr}")
    except Exception as e:
        print(f"[ERROR] Error: {e}")

    return False

def main():
    """Main function"""
    print("SQL SERVER DATABASE EXPLORATION")
    print("=" * 80)

    # Explore the restored Staging database
    scanner_tables = explore_database()

    if scanner_tables:
        print(f"\nFound scanner tables: {scanner_tables}")
        for table in scanner_tables:
            explore_table_structure(table)
    else:
        print("\nNo scanner tables found with standard methods")
        find_scanner_data()

    # Try to restore Plantware
    print(f"\n{'='*80}")
    print("ATTEMPTING PLANTWARE RESTORE")
    print('='*80)

    plantware_db = try_plantware_restore()
    if plantware_db:
        print(f"\nPlantware database {plantware_db} restored successfully!")
        # Explore Plantware database
        # (Add exploration code here if needed)

    print(f"\n{'='*80}")
    print("EXPLORATION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()