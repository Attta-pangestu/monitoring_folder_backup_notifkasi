#!/usr/bin/env python3
"""
Database Structure Analyzer
Menganalisis struktur database backup sesuai dokumentasi README_MONITORING.md
"""

import sys
import os
sys.path.append('src')

from bak_file_reader import BAKFileReader

def analyze_database_structure():
    """Analisis struktur database backup"""
    print("=" * 80)
    print("DATABASE STRUCTURE ANALYZER")
    print("=" * 80)
    print()

    # Database configuration berdasarkan dokumentasi
    db_config = {
        'plantware': {
            'main_table': 'PR_TASKREG',
            'date_columns': ['TGLREG', 'TGLUPDATE', 'TGLKIRIM'],
            'description': 'Database Plantware P3'
        },
        'venus': {
            'main_table': 'TA_MACHINE',
            'date_columns': ['TANGGAL', 'WAKTU_UPDATE', 'CREATED_DATE'],
            'description': 'Database Venus'
        },
        'staging': {
            'main_table': 'GWSCANNER',
            'date_columns': ['SCAN_DATE', 'UPDATE_DATE', 'CREATED_AT'],
            'description': 'Database Staging'
        }
    }

    # Cari file backup
    backup_dir = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup"
    backup_files = []

    if os.path.exists(backup_dir):
        for file in os.listdir(backup_dir):
            if file.endswith('.zip'):
                backup_files.append(os.path.join(backup_dir, file))

    if not backup_files:
        print("Tidak ditemukan file backup ZIP")
        return

    reader = BAKFileReader()

    for backup_file in backup_files:
        print(f"\n{'='*60}")
        print(f"ANALYZING: {os.path.basename(backup_file)}")
        print('='*60)

        try:
            # Deteksi tipe database berdasarkan nama file
            db_type = None
            if 'plantware' in backup_file.lower():
                db_type = 'plantware'
            elif 'venus' in backup_file.lower():
                db_type = 'venus'
            elif 'staging' in backup_file.lower():
                db_type = 'staging'

            if not db_type:
                print("Unknown database type - skipping")
                continue

            config = db_config[db_type]
            print(f"Database Type: {db_type.upper()}")
            print(f"Description: {config['description']}")
            print(f"Main Table: {config['main_table']}")
            print(f"Date Columns: {', '.join(config['date_columns'])}")

            # Baca file backup
            print(f"\nReading backup file...")
            result = reader.read_bak_file(backup_file, extract_to_same_folder=True)

            if not result['success']:
                print(f"Failed to read backup: {result.get('errors', ['Unknown error'])}")
                continue

            # Analisis struktur database
            if result.get('tables'):
                tables = result['tables']
                print(f"\nDatabase Structure:")
                print(f"Total Tables: {len(tables)}")

                # Cari main table
                main_table = config['main_table']
                if main_table in tables:
                    print(f"\n✅ Found main table: {main_table}")
                    table_info = tables[main_table]
                    print(f"   Records: {table_info.get('record_count', 0):,}")

                    # Analisis kolom
                    columns = table_info.get('columns', [])
                    print(f"   Total Columns: {len(columns)}")

                    # Cari kolom tanggal
                    date_columns_found = []
                    for col in columns:
                        col_name = col[1]  # column name
                        if col_name in config['date_columns']:
                            date_columns_found.append(col_name)

                    if date_columns_found:
                        print(f"   Date Columns Found: {', '.join(date_columns_found)}")

                        # Dapatkan tanggal terbaru
                        latest_dates = table_info.get('latest_dates', {})
                        if latest_dates:
                            print(f"   Latest Dates:")
                            for col, date in latest_dates.items():
                                print(f"     {col}: {date}")
                    else:
                        print(f"   ⚠️  No date columns found from: {config['date_columns']}")

                    # Tampilkan sample data
                    sample_data = table_info.get('sample_data', [])
                    if sample_data:
                        print(f"   Sample Data (first 3 rows):")
                        for i, row in enumerate(sample_data[:3]):
                            print(f"     Row {i+1}: {row}")
                else:
                    print(f"\n❌ Main table {main_table} not found")
                    print(f"Available tables: {list(tables.keys())}")

                # Tampilkan semua tabel
                print(f"\nAll Tables in Database:")
                for table_name, table_info in tables.items():
                    record_count = table_info.get('record_count', 0)
                    print(f"   - {table_name}: {record_count:,} records")

            else:
                print("No tables found in database")

        except Exception as e:
            print(f"Error analyzing {backup_file}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETED")
    print("="*80)

    # Cleanup
    reader.cleanup()

if __name__ == "__main__":
    analyze_database_structure()