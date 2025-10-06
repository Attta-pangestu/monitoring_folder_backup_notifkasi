#!/usr/bin/env python3
"""
Explore Restored Plantware Database
Menjelajahi database Plantware yang sudah di-restore
"""

import sys
import os
import subprocess
from datetime import datetime

def explore_plantware_database():
    """Jelajahi database Plantware yang sudah di-restore"""
    print("=" * 80)
    print("EXPLORING RESTORED PLANTWARE DATABASE")
    print("=" * 80)
    print()

    db_name = "Plantware_Restored"

    print(f"Database: {db_name}")

    # List tables using sys.tables
    print("\nListing all tables...")
    try:
        query = f"USE {db_name}; SELECT name as TableName FROM sys.tables ORDER BY name"
        result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1', '-s', ','],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            lines = [line.strip() for line in result.stdout.split('\n') if line.strip() and not line.startswith('-')]
            if lines:
                print(f"Found {len(lines)} tables:")

                # Look for tables of interest
                tables_of_interest = []
                for table in lines:
                    table_upper = table.upper()
                    if ('TASK' in table_upper or 'GWSCANNER' in table_upper or
                        'SCANNER' in table_upper or 'GATEWAY' in table_upper or
                        'PR_' in table_upper):
                        tables_of_interest.append(table)

                if tables_of_interest:
                    print(f"\nTables of interest:")
                    for table in tables_of_interest:
                        print(f"  - {table}")
                else:
                    print(f"\nFirst 20 tables:")
                    for i, table in enumerate(lines[:20]):
                        print(f"  {i+1}. {table}")
        else:
            print(f"Error listing tables: {result.stderr}")
    except Exception as e:
        print(f"Error: {e}")

    # Cari PR_TASKREG sesuai dokumentasi
    print(f"\n{'='*60}")
    print("LOOKING FOR PR_TASKREG TABLE")
    print('='*60)

    try:
        # Cek jika PR_TASKREG ada
        query = f"USE {db_name}; SELECT COUNT(*) as TableExists FROM sys.tables WHERE name = 'PR_TASKREG'"
        result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1'],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.strip().isdigit() and int(line.strip()) > 0:
                    print("[FOUND] PR_TASKREG table exists!")
                    explore_pr_taskreg(db_name)
                    break
            else:
                print("[NOT FOUND] PR_TASKREG table does not exist")

                # Cari tabel yang mirip
                similar_query = f"USE {db_name}; SELECT name as TableName FROM sys.tables WHERE name LIKE '%TASK%' OR name LIKE '%PR_%' ORDER BY name"
                result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', similar_query, '-h', '-1', '-s', ','],
                                      capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    similar_tables = [line.strip() for line in result.stdout.split('\n') if line.strip() and not line.startswith('-')]
                    if similar_tables:
                        print("Similar tables found:")
                        for table in similar_tables:
                            print(f"  - {table}")
    except Exception as e:
        print(f"Error checking PR_TASKREG: {e}")

    # Cari tabel GWSCANNER
    print(f"\n{'='*60}")
    print("LOOKING FOR GWSCANNER TABLES")
    print('='*60)

    try:
        scanner_query = f"USE {db_name}; SELECT name as TableName FROM sys.tables WHERE name LIKE '%GWSCANNER%' OR name LIKE '%SCANNER%' OR name LIKE '%GATEWAY%' ORDER BY name"
        result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', scanner_query, '-h', '-1', '-s', ','],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            scanner_tables = [line.strip() for line in result.stdout.split('\n') if line.strip() and not line.startswith('-')]
            if scanner_tables:
                print("Scanner-related tables found:")
                for table in scanner_tables:
                    print(f"  - {table}")

                # Explore the first scanner table
                if scanner_tables:
                    explore_scanner_table(db_name, scanner_tables[0])
            else:
                print("No scanner-related tables found")
    except Exception as e:
        print(f"Error looking for scanner tables: {e}")

def explore_pr_taskreg(db_name):
    """Explore PR_TASKREG table structure and data"""
    print(f"\n{'='*80}")
    print("EXPLORING PR_TASKREG TABLE")
    print('='*80)

    # Get table structure
    print("Table structure:")
    try:
        query = f"USE {db_name}; SELECT c.name as ColumnName, t.name as DataType, c.max_length, c.is_nullable FROM sys.columns c JOIN sys.types t ON c.user_type_id = t.user_type_id WHERE c.object_id = OBJECT_ID('PR_TASKREG') ORDER BY c.column_id"
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

                # Look for date columns specifically
                date_columns = []
                for line in lines:
                    if '|' in line:
                        parts = [p.strip() for p in line.split('|')]
                        if len(parts) >= 2 and ('DATE' in parts[1].upper() or 'TIME' in parts[1].upper()):
                            date_columns.append(parts[0])

                if date_columns:
                    print(f"\nDate columns found: {date_columns}")
                    explore_date_columns(db_name, "PR_TASKREG", date_columns)
    except Exception as e:
        print(f"Error getting table structure: {e}")

    # Get row count
    print(f"\nRow count:")
    try:
        query = f"USE {db_name}; SELECT COUNT(*) as RowCount FROM PR_TASKREG"
        result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1'],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.strip().isdigit():
                    print(f"  Total rows: {int(line.strip()):,}")
                    break
    except Exception as e:
        print(f"Error getting row count: {e}")

    # Get sample data
    print(f"\nSample data (first 5 rows):")
    try:
        query = f"USE {db_name}; SELECT TOP 5 * FROM PR_TASKREG ORDER BY 1 DESC"
        result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1', '-s', ' | '],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            lines = [line.strip() for line in result.stdout.split('\n') if line.strip() and not line.startswith('-')]
            if lines:
                print("Sample rows:")
                for i, line in enumerate(lines):
                    print(f"  {i+1}. {line}")
    except Exception as e:
        print(f"Error getting sample data: {e}")

def explore_scanner_table(db_name, table_name):
    """Explore scanner table structure and data"""
    print(f"\n{'='*80}")
    print(f"EXPLORING SCANNER TABLE: {table_name}")
    print('='*80)

    # Get table structure
    print("Table structure:")
    try:
        query = f"USE {db_name}; SELECT c.name as ColumnName, t.name as DataType, c.max_length, c.is_nullable FROM sys.columns c JOIN sys.types t ON c.user_type_id = t.user_type_id WHERE c.object_id = OBJECT_ID('{table_name}') ORDER BY c.column_id"
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

                # Look for date columns
                date_columns = []
                for line in lines:
                    if '|' in line:
                        parts = [p.strip() for p in line.split('|')]
                        if len(parts) >= 2 and ('DATE' in parts[1].upper() or 'TIME' in parts[1].upper()):
                            date_columns.append(parts[0])

                if date_columns:
                    print(f"\nDate columns found: {date_columns}")
                    explore_date_columns(db_name, table_name, date_columns)
    except Exception as e:
        print(f"Error getting table structure: {e}")

    # Get row count
    print(f"\nRow count:")
    try:
        query = f"USE {db_name}; SELECT COUNT(*) as RowCount FROM {table_name}"
        result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1'],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.strip().isdigit():
                    print(f"  Total rows: {int(line.strip()):,}")
                    break
    except Exception as e:
        print(f"Error getting row count: {e}")

    # Get sample data
    print(f"\nSample data (first 5 rows):")
    try:
        query = f"USE {db_name}; SELECT TOP 5 * FROM {table_name} ORDER BY 1 DESC"
        result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1', '-s', ' | '],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            lines = [line.strip() for line in result.stdout.split('\n') if line.strip() and not line.startswith('-')]
            if lines:
                print("Sample rows:")
                for i, line in enumerate(lines):
                    print(f"  {i+1}. {line}")
    except Exception as e:
        print(f"Error getting sample data: {e}")

def explore_date_columns(db_name, table_name, date_columns):
    """Explore date columns and get latest dates"""
    print(f"\n{'='*60}")
    print("EXPLORING DATE COLUMNS")
    print('='*60)

    latest_dates = {}

    for col in date_columns:
        print(f"\nExploring column: {col}")
        try:
            # Get latest date
            query = f"USE {db_name}; SELECT TOP 1 {col} as LatestDate FROM {table_name} WHERE {col} IS NOT NULL ORDER BY {col} DESC"
            result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1'],
                                  capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.strip() and not line.startswith('-') and not line.strip().startswith('('):
                        latest_dates[col] = line.strip()
                        print(f"  Latest {col}: {line.strip()}")
                        break

            # Get date range
            query = f"USE {db_name}; SELECT MIN({col}) as MinDate, MAX({col}) as MaxDate, COUNT({col}) as NonNullCount FROM {table_name} WHERE {col} IS NOT NULL"
            result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1', '-s', '|'],
                                  capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                lines = [line.strip() for line in result.stdout.split('\n') if line.strip() and not line.startswith('-')]
                if lines and '|' in lines[0]:
                    parts = [p.strip() for p in lines[0].split('|')]
                    if len(parts) >= 3:
                        print(f"  Range: {parts[0]} to {parts[1]} (Non-null: {parts[2]})")

        except Exception as e:
            print(f"  Error exploring {col}: {e}")

    # Summary of latest dates
    if latest_dates:
        print(f"\n{'='*60}")
        print("LATEST DATES SUMMARY")
        print('='*60)

        parsed_dates = []
        for col, date_str in latest_dates.items():
            print(f"  {col}: {date_str}")
            # Try to parse date
            try:
                # Handle different SQL Server date formats
                for fmt in ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                    try:
                        parsed_date = datetime.strptime(date_str.split('.')[0], fmt)
                        parsed_dates.append((col, parsed_date))
                        break
                    except:
                        continue
            except:
                pass

        if parsed_dates:
            # Sort by date
            parsed_dates.sort(key=lambda x: x[1], reverse=True)
            latest_overall = parsed_dates[0]
            print(f"\nOverall latest date: {latest_overall[1].strftime('%Y-%m-%d %H:%M:%S')} (from {latest_overall[0]})")

def main():
    """Main function"""
    print("PLANTWARE DATABASE EXPLORATION")
    print("=" * 80)

    explore_plantware_database()

    print(f"\n{'='*80}")
    print("EXPLORATION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()