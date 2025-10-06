#!/usr/bin/env python3
"""
Extract GWSCANNER Data from Staging Backup
Mengekstrak data GWSCANNER dari backup Staging database
"""

import sys
import os
import re
import zipfile
import sqlite3
from datetime import datetime

def extract_staging_gwscanner():
    """Ekstrak GWSCANNER dari backup Staging"""
    print("=" * 80)
    print("EXTRACTING GWSCANNER FROM STAGING BACKUP")
    print("=" * 80)
    print()

    # Path ke backup Staging
    staging_zip = r"D:/Gawean Rebinmas/App_Auto_Backup/Backup/BackupStaging 2025-10-04 09;16;30.zip"

    if not os.path.exists(staging_zip):
        print(f"Staging backup not found: {staging_zip}")
        return None

    print(f"Staging backup: {staging_zip}")
    print(f"Size: {os.path.getsize(staging_zip) / (1024*1024):.2f} MB")

    # Ekstrak ZIP
    extracted_files = []
    try:
        with zipfile.ZipFile(staging_zip, 'r') as zip_ref:
            # List isi ZIP
            print(f"\nFiles in ZIP:")
            for file_info in zip_ref.filelist:
                print(f"  - {file_info.filename}")

            # Ekstrak semua file
            extract_path = r"D:/Gawean Rebinmas/App_Auto_Backup/Backup/staging_extracted"
            os.makedirs(extract_path, exist_ok=True)
            zip_ref.extractall(extract_path)

            # Dapatkan daftar file yang diekstrak
            for root, dirs, files in os.walk(extract_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    extracted_files.append(file_path)

            print(f"\nExtracted {len(extracted_files)} files to: {extract_path}")

    except Exception as e:
        print(f"Error extracting ZIP: {e}")
        return None

    # Cari file database di hasil ekstrak
    database_files = []
    for file_path in extracted_files:
        if file_path.endswith(('.bak', '.db', '.sqlite', '.sqlite3')):
            database_files.append(file_path)

    print(f"\nFound {len(database_files)} database files:")
    for db_file in database_files:
        print(f"  - {db_file}")

    # Analisis setiap database file
    all_dates = []
    for db_file in database_files:
        print(f"\n{'='*50}")
        print(f"ANALYZING: {os.path.basename(db_file)}")
        print('='*50)

        try:
            # Coba baca sebagai SQLite
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            # Cek tabel yang ada
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Tables found: {[t[0] for t in tables]}")

            # Cari GWSCANNER table
            gwscanner_tables = [t[0] for t in tables if 'GWSCANNER' in t[0].upper()]

            if gwscanner_tables:
                print(f"GWSCANNER tables found: {gwscanner_tables}")

                for table_name in gwscanner_tables:
                    print(f"\nAnalyzing table: {table_name}")

                    # Cek struktur tabel
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    print(f"Columns: {[col[1] for col in columns]}")

                    # Cari kolom tanggal
                    date_columns = []
                    for col in columns:
                        col_name = col[1].upper()
                        if 'DATE' in col_name or 'TIME' in col_name:
                            date_columns.append(col[1])

                    if date_columns:
                        print(f"Date columns: {date_columns}")

                        # Ambil data terbaru dari setiap kolom tanggal
                        for date_col in date_columns:
                            try:
                                cursor.execute(f"SELECT DISTINCT {date_col} FROM {table_name} WHERE {date_col} IS NOT NULL ORDER BY {date_col} DESC LIMIT 10")
                                dates = cursor.fetchall()
                                if dates:
                                    print(f"Latest {date_col}: {[d[0] for d in dates[:5]]}")
                                    all_dates.extend([d[0] for d in dates])
                            except Exception as e:
                                print(f"Error querying {date_col}: {e}")

                    # Ambil sample data
                    try:
                        cursor.execute(f"SELECT * FROM {table_name} ORDER BY 1 DESC LIMIT 5")
                        sample_data = cursor.fetchall()
                        print(f"Sample data: {sample_data}")
                    except Exception as e:
                        print(f"Error getting sample data: {e}")
            else:
                print("No GWSCANNER tables found")

            conn.close()

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            # Coba baca sebagai file biner jika gagal
            try:
                print("Trying binary analysis...")
                with open(db_file, 'rb') as f:
                    content = f.read(1024 * 1024)  # Baca 1MB
                    text_content = content.decode('utf-8', errors='ignore')

                    # Cari GWSCANNER dalam text
                    gwscanner_positions = []
                    start = 0
                    while True:
                        pos = text_content.find('GWSCANNER', start)
                        if pos == -1:
                            break
                        gwscanner_positions.append(pos)
                        start = pos + 1

                    if gwscanner_positions:
                        print(f"Found GWSCANNER at {len(gwscanner_positions)} positions")

                        # Cari tanggal di sekitar GWSCANNER
                        for pos in gwscanner_positions[:10]:
                            context_start = max(0, pos - 200)
                            context_end = min(len(text_content), pos + 300)
                            context = text_content[context_start:context_end]

                            # Cari pattern tanggal
                            date_patterns = [
                                r'\d{4}-\d{2}-\d{2}',
                                r'\d{2}/\d{2}/\d{4}',
                                r'\d{4}\d{2}\d{2}',
                            ]

                            for pattern in date_patterns:
                                matches = re.findall(pattern, context)
                                if matches:
                                    print(f"Dates near GWSCANNER: {matches}")
                                    all_dates.extend(matches)
                                    break
                    else:
                        print("No GWSCANNER found in text content")

            except Exception as e2:
                print(f"Binary analysis also failed: {e2}")

    # Analisis tanggal yang ditemukan
    if all_dates:
        print(f"\n{'='*50}")
        print("DATE ANALYSIS")
        print('='*50)

        # Parse tanggal
        parsed_dates = []
        for date_str in all_dates:
            if isinstance(date_str, str):
                clean_date = re.sub(r'[\'"\\]', '', date_str.strip())

                date_formats = [
                    '%Y-%m-%d',
                    '%d/%m/%Y',
                    '%Y%m%d',
                    '%m/%d/%Y',
                    '%Y-%m-%d %H:%M:%S',
                    '%d/%m/%Y %H:%M:%S'
                ]

                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(clean_date, fmt)
                        parsed_dates.append(parsed_date)
                        break
                    except:
                        continue

        if parsed_dates:
            parsed_dates.sort(reverse=True)

            print(f"\n{'='*40}")
            print("LATEST DATES FROM STAGING GWSCANNER")
            print('='*40)

            for i, date in enumerate(parsed_dates[:10]):
                print(f"{i+1}. {date.strftime('%Y-%m-%d %H:%M:%S') if date.hour > 0 else date.strftime('%Y-%m-%d')}")

            latest_date = parsed_dates[0]
            print(f"\nLatest date: {latest_date.strftime('%Y-%m-%d %H:%M:%S') if latest_date.hour > 0 else latest_date.strftime('%Y-%m-%d')}")

            return latest_date.strftime('%Y-%m-%d')
        else:
            print("Could not parse any dates")
    else:
        print("No dates found")

    return None

if __name__ == "__main__":
    latest_date = extract_staging_gwscanner()
    if latest_date:
        print(f"\nFINAL RESULT: Latest GWSCANNER date from Staging is {latest_date}")
    else:
        print("\nNo GWSCANNER dates found in Staging backup")