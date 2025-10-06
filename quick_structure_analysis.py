#!/usr/bin/env python3
"""
Quick Database Structure Analysis
Analisis cepat struktur database dengan partial reading
"""

import sys
import os
sys.path.append('src')

from bak_file_reader import BAKFileReader
import zipfile
import tempfile

def quick_analysis():
    """Analisis cepat struktur database"""
    print("=" * 80)
    print("QUICK DATABASE STRUCTURE ANALYSIS")
    print("=" * 80)
    print()

    # Database configuration
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

    backup_dir = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup"

    # Fokus pada file yang lebih kecil dulu
    backup_files = []
    if os.path.exists(backup_dir):
        for file in os.listdir(backup_dir):
            if file.endswith('.zip'):
                file_path = os.path.join(backup_dir, file)
                file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                if file_size_mb < 500:  # Fokus pada file < 500MB
                    backup_files.append((file_path, file_size_mb))

    if not backup_files:
        print("Tidak ditemukan file backup < 500MB")
        return

    # Sort by size
    backup_files.sort(key=lambda x: x[1])

    for backup_file, size_mb in backup_files[:2]:  # Analisis 2 file terkecil
        print(f"\n{'='*60}")
        print(f"ANALYZING: {os.path.basename(backup_file)}")
        print(f"Size: {size_mb:.1f} MB")
        print('='*60)

        try:
            # Deteksi tipe database
            db_type = None
            filename = os.path.basename(backup_file).lower()
            if 'plantware' in filename:
                db_type = 'plantware'
            elif 'venus' in filename:
                db_type = 'venus'
            elif 'staging' in filename:
                db_type = 'staging'

            if not db_type:
                print("Unknown database type")
                continue

            config = db_config[db_type]
            print(f"Database Type: {db_type.upper()}")
            print(f"Main Table: {config['main_table']}")

            # Analisis langsung dari ZIP (tanpa ekstrak penuh)
            with zipfile.ZipFile(backup_file, 'r') as zip_ref:
                # Cari file database
                db_files = [f for f in zip_ref.namelist() if not f.endswith('/')]
                if not db_files:
                    print("No database files found in ZIP")
                    continue

                db_file = db_files[0]
                print(f"Database file: {db_file}")

                # Ekstrak ke temporary file untuk analisis
                with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
                    with zip_ref.open(db_file) as source:
                        # Hanya baca 10MB pertama untuk analisis cepat
                        temp_file.write(source.read(10 * 1024 * 1024))
                    temp_path = temp_file.name

                try:
                    # Analisis dengan SQLite
                    import sqlite3
                    conn = sqlite3.connect(temp_path)
                    cursor = conn.cursor()

                    # Get all tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                    tables = [row[0] for row in cursor.fetchall()]

                    print(f"\nTables found: {len(tables)}")
                    for table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        print(f"  - {table}: {count:,} records")

                    # Analisis main table
                    main_table = config['main_table']
                    if main_table in tables:
                        print(f"\n✅ Main table {main_table} found!")

                        # Get table structure
                        cursor.execute(f"PRAGMA table_info({main_table})")
                        columns = cursor.fetchall()
                        print(f"Columns in {main_table}:")
                        for col in columns:
                            print(f"  - {col[1]} ({col[2]})")

                        # Cari kolom tanggal
                        date_columns_found = []
                        for col in columns:
                            col_name = col[1]
                            if col_name in config['date_columns']:
                                date_columns_found.append(col_name)

                        if date_columns_found:
                            print(f"\nDate columns found: {', '.join(date_columns_found)}")

                            # Get sample data untuk kolom tanggal
                            for date_col in date_columns_found:
                                try:
                                    cursor.execute(f"SELECT DISTINCT {date_col} FROM {main_table} WHERE {date_col} IS NOT NULL ORDER BY {date_col} DESC LIMIT 5")
                                    dates = cursor.fetchall()
                                    if dates:
                                        print(f"Sample {date_col}: {[d[0] for d in dates]}")
                                except:
                                    print(f"Could not query {date_col}")

                        # Get sample data
                        cursor.execute(f"SELECT * FROM {main_table} LIMIT 3")
                        sample_data = cursor.fetchall()
                        if sample_data:
                            print(f"\nSample data from {main_table}:")
                            for i, row in enumerate(sample_data):
                                print(f"  Row {i+1}: {row}")
                    else:
                        print(f"\n❌ Main table {main_table} not found!")

                    conn.close()

                except sqlite3.Error as e:
                    print(f"SQLite error: {e}")
                finally:
                    # Cleanup temp file
                    os.unlink(temp_path)

        except Exception as e:
            print(f"Error: {e}")

    print(f"\n{'='*80}")
    print("QUICK ANALYSIS COMPLETED")
    print("="*80)

if __name__ == "__main__":
    quick_analysis()