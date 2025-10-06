#!/usr/bin/env python3
"""
Simulate Database Check Results
Simulasi hasil check database dengan sample data
"""

import sys
import os
sys.path.append('src')

from bak_file_reader import BAKFileReader
import sqlite3
import tempfile

def create_sample_databases():
    """Buat sample database untuk simulasi"""
    print("Creating sample databases for simulation...")

    # Plantware sample
    plantware_db = 'sample_plantware.db'
    conn = sqlite3.connect(plantware_db)
    cursor = conn.cursor()

    # PR_TASKREG table
    cursor.execute('''
        CREATE TABLE PR_TASKREG (
            ID INTEGER PRIMARY KEY,
            TASK_CODE TEXT,
            TGLREG TEXT,
            TGLUPDATE TEXT,
            TGLKIRIM TEXT,
            STATUS TEXT,
            DESCRIPTION TEXT,
            PRIORITY INTEGER,
            ASSIGNED_TO TEXT
        )
    ''')

    # Insert sample data
    sample_data = [
        (1, 'TASK001', '2025-10-01', '2025-10-02', '2025-10-03', 'COMPLETED', 'Sample task 1', 1, 'USER1'),
        (2, 'TASK002', '2025-10-02', '2025-10-03', '2025-10-04', 'PENDING', 'Sample task 2', 2, 'USER2'),
        (3, 'TASK003', '2025-10-03', '2025-10-04', '2025-10-05', 'PROCESSING', 'Sample task 3', 3, 'USER3'),
    ]

    cursor.executemany('INSERT INTO PR_TASKREG VALUES (?,?,?,?,?,?,?,?,?)', sample_data)

    # Additional tables
    cursor.execute('CREATE TABLE PR_USER (ID INTEGER PRIMARY KEY, NAME TEXT, DEPARTMENT TEXT)')
    cursor.execute('CREATE TABLE PR_PROJECT (ID INTEGER PRIMARY KEY, PROJECT_NAME TEXT, START_DATE TEXT)')
    cursor.execute('CREATE TABLE PR_DEPARTMENT (ID INTEGER PRIMARY KEY, DEPT_NAME TEXT, MANAGER TEXT)')

    conn.commit()
    conn.close()

    # Venus sample
    venus_db = 'sample_venus.db'
    conn = sqlite3.connect(venus_db)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE TA_MACHINE (
            MACHINE_ID INTEGER PRIMARY KEY,
            MACHINE_NAME TEXT,
            TANGGAL TEXT,
            WAKTU_UPDATE TEXT,
            CREATED_DATE TEXT,
            STATUS TEXT,
            LOCATION TEXT,
            MODEL TEXT
        )
    ''')

    venus_data = [
        (1, 'MACHINE001', '2025-10-01', '2025-10-02 10:00:00', '2025-09-30', 'ACTIVE', 'FLOOR A', 'MODEL-X1'),
        (2, 'MACHINE002', '2025-10-02', '2025-10-03 11:00:00', '2025-10-01', 'INACTIVE', 'FLOOR B', 'MODEL-Y2'),
    ]

    cursor.executemany('INSERT INTO TA_MACHINE VALUES (?,?,?,?,?,?,?,?)', venus_data)
    cursor.execute('CREATE TABLE TA_OPERATOR (ID INTEGER PRIMARY KEY, NAME TEXT, SHIFT TEXT)')
    cursor.execute('CREATE TABLE TA_MAINTENANCE (ID INTEGER PRIMARY KEY, MACHINE_ID INTEGER, MAINT_DATE TEXT)')

    conn.commit()
    conn.close()

    # Staging sample
    staging_db = 'sample_staging.db'
    conn = sqlite3.connect(staging_db)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE GWSCANNER (
            SCANNER_ID INTEGER PRIMARY KEY,
            SCANNER_NAME TEXT,
            SCAN_DATE TEXT,
            UPDATE_DATE TEXT,
            CREATED_AT TEXT,
            LOCATION TEXT,
            TYPE TEXT
        )
    ''')

    staging_data = [
        (1, 'SCANNER001', '2025-10-01', '2025-10-02 09:00:00', '2025-09-30 08:00:00', 'LOCATION A', 'TYPE1'),
        (2, 'SCANNER002', '2025-10-02', '2025-10-03 10:00:00', '2025-10-01 09:00:00', 'LOCATION B', 'TYPE2'),
    ]

    cursor.executemany('INSERT INTO GWSCANNER VALUES (?,?,?,?,?,?,?)', staging_data)
    cursor.execute('CREATE TABLE GW_LOG (ID INTEGER PRIMARY KEY, LOG_DATE TEXT, ACTIVITY TEXT)')
    cursor.execute('CREATE TABLE GW_CONFIG (ID INTEGER PRIMARY KEY, PARAM_NAME TEXT, PARAM_VALUE TEXT)')

    conn.commit()
    conn.close()

    return [plantware_db, venus_db, staging_db]

def simulate_database_check():
    """Simulasi check database dengan sample data"""
    print("=" * 80)
    print("SIMULATED DATABASE CHECK RESULTS")
    print("=" * 80)
    print("NOTE: This is a simulation using sample SQLite databases")
    print("Real backup files use TAPE format and cannot be read directly")
    print()

    # Buat sample databases
    sample_files = create_sample_databases()

    reader = BAKFileReader()
    total_databases = 0

    # Simulasi file names
    simulation_files = [
        ('sample_plantware.db', 'PlantwareP3 2025-10-04 11;33;53.zip'),
        ('sample_venus.db', 'BackupVenuz 2025-10-04 10;17;35.zip'),
        ('sample_staging.db', 'BackupStaging 2025-10-04 09;16;30.zip')
    ]

    for db_file, zip_name in simulation_files:
        if os.path.exists(db_file):
            print(f"\n{'='*60}")
            print(f"DATABASE CHECK: {zip_name}")
            print('='*60)

            try:
                # Deteksi tipe database
                if 'plantware' in zip_name.lower():
                    db_type = "Plantware"
                elif 'venus' in zip_name.lower():
                    db_type = "Venus"
                elif 'staging' in zip_name.lower():
                    db_type = "Staging"
                else:
                    db_type = "Unknown"

                print(f"Database Type: {db_type}")
                print(f"File: {zip_name}")

                # Baca database
                result = reader.read_bak_file(db_file)

                if result['success']:
                    total_databases += 1
                    print(f"Status: SUCCESS - Database readable")

                    # Informasi database
                    db_info = result.get('database_info', {})
                    if db_info:
                        print(f"\nDatabase Information:")
                        print(f"   Format: {result.get('file_type', 'Unknown')}")
                        print(f"   Detected Type: {db_info.get('detected_type', 'Unknown')}")
                        print(f"   Total Tables: {db_info.get('table_count', 0)}")

                    # Daftar tabel
                    tables = result.get('tables', {})
                    if tables:
                        print(f"\nTables Found ({len(tables)} tables):")
                        for table_name, table_info in tables.items():
                            record_count = table_info.get('record_count', 0)
                            column_count = len(table_info.get('columns', []))

                            print(f"\n   Table: {table_name}")
                            print(f"      Records: {record_count:,}")
                            print(f"      Columns: {column_count}")

                            # Tampilkan nama kolom
                            columns = table_info.get('columns', [])
                            if columns:
                                column_names = [col[1] for col in columns]
                                print(f"      Column Names: {column_names}")

                            # Tampilkan tanggal terbaru
                            latest_dates = table_info.get('latest_dates', {})
                            if latest_dates:
                                print(f"      Latest Dates: {latest_dates}")

                else:
                    print(f"Status: FAILED - Cannot read database")

            except Exception as e:
                print(f"Error processing {db_file}: {e}")

    # Cleanup
    for db_file in sample_files:
        if os.path.exists(db_file):
            os.remove(db_file)

    reader.cleanup()

    print(f"\n{'='*80}")
    print("REAL SITUATION SUMMARY")
    print("="*80)
    print("Your actual backup files:")
    print("- Use TAPE format (proprietary)")
    print("- Cannot be read directly with SQLite tools")
    print("- Need specialized parser for content extraction")
    print()
    print("This simulation shows what the information would look like")
    print("if your backup files were in SQLite format.")

if __name__ == "__main__":
    simulate_database_check()