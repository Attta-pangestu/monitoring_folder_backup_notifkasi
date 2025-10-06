#!/usr/bin/env python3
"""
Extract GWSCANNER Dates from SQL Server
Ekstrak tanggal terbaru dari tabel GWSCANNER di SQL Server
"""

import subprocess
from datetime import datetime

def extract_gwscanner_dates():
    """Ekstrak tanggal dari tabel Gwscannerdata"""
    print("=" * 80)
    print("EXTRACTING GWSCANNER DATES FROM SQL SERVER")
    print("=" * 80)
    print()

    db_name = "staging_PTRJ_iFES_Plantware"

    print(f"Database: {db_name}")
    print(f"Tables: Ffbscannerdata, Gwscannerdata, Scanner_User")

    all_latest_dates = {}

    # Explore Gwscannerdata table
    print(f"\n{'='*60}")
    print("EXPLORING: Gwscannerdata")
    print('='*60)

    table_name = "Gwscannerdata"
    date_columns = ['TRANSDATE', 'DATECREATED', 'INTEGRATETIME', 'SCANOUTDATETIME']

    for col in date_columns:
        print(f"\nExtracting dates from {col}...")

        # Get row count first
        try:
            query = f"SELECT COUNT(*) FROM {db_name}.dbo.{table_name} WHERE {col} IS NOT NULL"
            result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1'],
                                  capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.strip().isdigit():
                        count = int(line.strip())
                        print(f"  Non-null rows: {count:,}")
                        break
        except Exception as e:
            print(f"  Error getting count: {e}")

        # Get latest date
        try:
            query = f"SELECT MAX({col}) as MaxDate FROM {db_name}.dbo.{table_name} WHERE {col} IS NOT NULL"
            result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1'],
                                  capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.strip() and not line.startswith('-') and not line.strip().startswith('(') and not line.strip().startswith('MaxDate'):
                        date_str = line.strip()
                        print(f"  Latest {col}: {date_str}")
                        all_latest_dates[f"{table_name}_{col}"] = date_str
                        break
        except Exception as e:
            print(f"  Error getting max date: {e}")

        # Get date range
        try:
            query = f"SELECT MIN({col}) as MinDate, MAX({col}) as MaxDate FROM {db_name}.dbo.{table_name} WHERE {col} IS NOT NULL"
            result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1', '-s', '|'],
                                  capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                lines = [line.strip() for line in result.stdout.split('\n') if line.strip() and not line.startswith('-')]
                if lines and '|' in lines[0]:
                    parts = [p.strip() for p in lines[0].split('|')]
                    if len(parts) >= 2:
                        print(f"  Date range: {parts[0]} to {parts[1]}")
        except Exception as e:
            print(f"  Error getting date range: {e}")

    # Explore Ffbscannerdata table
    print(f"\n{'='*60}")
    print("EXPLORING: Ffbscannerdata")
    print('='*60)

    table_name = "Ffbscannerdata"
    date_columns = ['TRANSDATE', 'DATECREATED', 'INTEGRATETIME']

    for col in date_columns:
        print(f"\nExtracting dates from {col}...")

        # Get latest date
        try:
            query = f"SELECT MAX({col}) as MaxDate FROM {db_name}.dbo.{table_name} WHERE {col} IS NOT NULL"
            result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1'],
                                  capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.strip() and not line.startswith('-') and not line.strip().startswith('(') and not line.strip().startswith('MaxDate'):
                        date_str = line.strip()
                        print(f"  Latest {col}: {date_str}")
                        all_latest_dates[f"{table_name}_{col}"] = date_str
                        break
        except Exception as e:
            print(f"  Error getting max date: {e}")

    # Get sample data with dates
    print(f"\n{'='*60}")
    print("SAMPLE SCANNER DATA")
    print('='*60)

    tables_to_sample = [
        ("Gwscannerdata", "TRANSDATE"),
        ("Ffbscannerdata", "TRANSDATE")
    ]

    for table_name, date_col in tables_to_sample:
        print(f"\n{table_name} - Latest 5 records by {date_col}:")
        try:
            query = f"SELECT TOP 5 SCANNERUSERCODE, WORKERCODE, FIELDNO, {date_col} FROM {db_name}.dbo.{table_name} WHERE {date_col} IS NOT NULL ORDER BY {date_col} DESC"
            result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1', '-s', ' | '],
                                  capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                lines = [line.strip() for line in result.stdout.split('\n') if line.strip() and not line.startswith('-')]
                if lines:
                    print("  ScannerUser | WorkerCode | FieldNo | Date")
                    print("  -------------|------------|---------|-------------")
                    for line in lines:
                        print(f"  {line}")
        except Exception as e:
            print(f"  Error getting sample data: {e}")

    # Summary of latest dates
    print(f"\n{'='*80}")
    print("LATEST DATES SUMMARY")
    print('='*80)

    if all_latest_dates:
        parsed_dates = []

        print("All latest dates found:")
        for key, date_str in all_latest_dates.items():
            print(f"  {key}: {date_str}")

            # Parse date for comparison
            try:
                # Handle different SQL Server datetime formats
                date_clean = date_str.split('.')[0]  # Remove milliseconds
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                    try:
                        parsed_date = datetime.strptime(date_clean, fmt)
                        parsed_dates.append((key, parsed_date, date_str))
                        break
                    except:
                        continue
            except:
                pass

        if parsed_dates:
            # Sort by date
            parsed_dates.sort(key=lambda x: x[1], reverse=True)

            print(f"\n{'='*60}")
            print("SORTED LATEST DATES")
            print('='*60)

            for i, (key, parsed_date, original_str) in enumerate(parsed_dates):
                print(f"{i+1}. {key}: {original_str}")
                if i == 0:  # Highlight the latest
                    print(f"    *** LATEST OVERALL: {parsed_date.strftime('%Y-%m-%d %H:%M:%S')} ***")

            latest_overall = parsed_dates[0]
            print(f"\nFINAL RESULT:")
            print(f"Latest scanner date: {latest_overall[2]}")
            print(f"From table/column: {latest_overall[0]}")
            print(f"Formatted: {latest_overall[1].strftime('%Y-%m-%d %H:%M:%S')}")

            return latest_overall[1].strftime('%Y-%m-%d')
    else:
        print("No dates found")

    return None

def check_database_info():
    """Check additional database information"""
    print(f"\n{'='*60}")
    print("DATABASE INFORMATION")
    print('='*60)

    db_name = "staging_PTRJ_iFES_Plantware"

    # Check database properties
    try:
        query = f"SELECT DATABASEPROPERTYEX('{db_name}', 'Status') as Status, DATABASEPROPERTYEX('{db_name}', 'Recovery') as RecoveryModel, DATABASEPROPERTYEX('{db_name}', 'Collation') as Collation"
        result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1'],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            lines = [line.strip() for line in result.stdout.split('\n') if line.strip() and not line.startswith('-')]
            if lines:
                print(f"Database properties: {lines[0]}")
    except Exception as e:
        print(f"Error getting database properties: {e}")

    # Check total tables count
    try:
        query = f"SELECT COUNT(*) FROM {db_name}.sys.tables"
        result = subprocess.run(['sqlcmd', '-S', 'localhost', '-Q', query, '-h', '-1'],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.strip().isdigit():
                    print(f"Total tables: {int(line.strip()):,}")
                    break
    except Exception as e:
        print(f"Error getting table count: {e}")

def main():
    """Main function"""
    print("GWSCANNER DATE EXTRACTION FROM SQL SERVER")
    print("=" * 80)

    # Check database info
    check_database_info()

    # Extract dates
    latest_date = extract_gwscanner_dates()

    print(f"\n{'='*80}")
    print("EXTRACTION COMPLETE")
    print("="*80)

    if latest_date:
        print(f"\nSUCCESS: Latest GWSCANNER date found: {latest_date}")
    else:
        print("\nNo valid dates found")

if __name__ == "__main__":
    main()