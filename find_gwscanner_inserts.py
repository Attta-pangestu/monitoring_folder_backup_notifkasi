#!/usr/bin/env python3
"""
Find GWSCANNER INSERT Statements
Fokus mencari INSERT INTO GWSCANNER dengan data aktual
"""

import sys
import os
import re
import mmap
from datetime import datetime

def find_gwscanner_inserts():
    """Cari INSERT statements untuk GWSCANNER dengan data aktual"""
    print("=" * 80)
    print("FINDING GWSCANNER INSERT STATEMENTS")
    print("=" * 80)
    print()

    # Coba di PlantwareP3 dulu
    bak_path = r"D:/Gawean Rebinmas/App_Auto_Backup/Backup/PlantwareP3"

    if not os.path.exists(bak_path):
        print(f"File not found: {bak_path}")
        return None

    print(f"Analyzing: {bak_path}")
    print(f"Size: {os.path.getsize(bak_path) / (1024*1024*1024):.2f} GB")

    insert_dates = []
    insert_statements = []

    try:
        with open(bak_path, 'rb') as f:
            # Gunakan memory mapping dengan batasan
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

            print("Searching for INSERT statements...")

            # Cari pattern INSERT yang berisi GWSCANNER
            search_patterns = [
                rb'INSERT\s+INTO\s+GWSCANNER',
                rb'INSERT\s+INTO\s+#?GWSCANNER#?',
                rb'INSERT\s+INTO\s+[^\s]+\s+GWSCANNER',
                rb'INSERT\s+INTO\s+[^\s]+\s+GWSCANNER#?'
            ]

            # Batasi pencarian ke 100MB pertama untuk performa
            search_limit = 100 * 1024 * 1024  # 100MB
            search_pos = 0

            while search_pos < search_limit:
                found_insert = False

                for pattern in search_patterns:
                    pos = mm.find(pattern, search_pos, min(search_pos + 1000, search_limit))
                    if pos != -1:
                        # Ekstrak INSERT statement lengkap
                        insert_start = pos
                        insert_end = mm.find(b');', insert_start)

                        if insert_end != -1 and insert_end - insert_start < 5000:  # Batasi panjang
                            insert_statement = mm[insert_start:insert_end + 2]

                            try:
                                insert_text = insert_statement.decode('utf-8', errors='ignore')

                                # Cari tanggal dalam INSERT statement
                                date_matches = re.findall(r'\d{4}-\d{2}-\d{2}', insert_text)
                                if date_matches:
                                    insert_dates.extend(date_matches)
                                    insert_statements.append({
                                        'position': insert_start,
                                        'statement': insert_text[:500] + '...' if len(insert_text) > 500 else insert_text,
                                        'dates': date_matches
                                    })

                                    print(f"Found INSERT at {insert_start} with dates: {date_matches}")

                            except Exception as e:
                                pass

                            search_pos = insert_end + 2
                            found_insert = True
                            break

                if not found_insert:
                    search_pos += 1000

                if search_pos >= search_limit:
                    break

            # Cari juga di Staging backup
            print(f"\nChecking Staging backup...")
            staging_zip = r"D:/Gawean Rebinmas/App_Auto_Backup/Backup/BackupStaging 2025-10-04 09;16;30.zip"

            if os.path.exists(staging_zip):
                import zipfile
                import tempfile

                with zipfile.ZipFile(staging_zip, 'r') as zip_ref:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        zip_ref.extractall(temp_dir)

                        for file in os.listdir(temp_dir):
                            if file.endswith('.bak'):
                                bak_file = os.path.join(temp_dir, file)
                                print(f"Analyzing extracted: {file}")

                                with open(bak_file, 'rb') as staging_f:
                                    staging_mm = mmap.mmap(staging_f.fileno(), 0, access=mmap.ACCESS_READ)

                                    # Cari INSERT statements di staging
                                    for pattern in search_patterns:
                                        pos = staging_mm.find(pattern)
                                        if pos != -1:
                                            insert_start = pos
                                            insert_end = staging_mm.find(b');', insert_start)

                                            if insert_end != -1 and insert_end - insert_start < 5000:
                                                insert_statement = staging_mm[insert_start:insert_end + 2]

                                                try:
                                                    insert_text = insert_statement.decode('utf-8', errors='ignore')

                                                    date_matches = re.findall(r'\d{4}-\d{2}-\d{2}', insert_text)
                                                    if date_matches:
                                                        insert_dates.extend(date_matches)
                                                        insert_statements.append({
                                                            'position': insert_start,
                                                            'file': file,
                                                            'statement': insert_text[:300] + '...',
                                                            'dates': date_matches
                                                        })

                                                        print(f"Found INSERT in {file} with dates: {date_matches}")

                                                except Exception as e:
                                                    pass

                                    staging_mm.close()

            mm.close()

    except Exception as e:
        print(f"Error: {e}")
        return None

    # Analisis hasil
    print(f"\n{'='*50}")
    print("INSERT STATEMENT ANALYSIS")
    print('='*50)

    print(f"Found {len(insert_statements)} GWSCANNER INSERT statements")
    print(f"Total date strings found: {len(insert_dates)}")

    if insert_statements:
        print(f"\n{'='*40}")
        print("SAMPLE INSERT STATEMENTS")
        print('='*40)

        for i, insert in enumerate(insert_statements[:3]):
            print(f"\n{i+1}. Position: {insert.get('position', 'N/A')}")
            if 'file' in insert:
                print(f"   File: {insert['file']}")
            print(f"   Dates: {insert['dates']}")
            print(f"   Statement: {insert['statement']}")

    # Parse tanggal untuk menemukan yang terbaru
    if insert_dates:
        print(f"\n{'='*40}")
        print("DATE ANALYSIS")
        print('='*40)

        parsed_dates = []
        for date_str in insert_dates:
            clean_date = re.sub(r'[\'"\\]', '', date_str.strip())

            date_formats = [
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%Y%m%d',
                '%m/%d/%Y'
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
            print("LATEST DATES FROM GWSCANNER INSERTS")
            print('='*40)

            for i, date in enumerate(parsed_dates[:10]):
                print(f"{i+1}. {date.strftime('%Y-%m-%d')}")

            latest_date = parsed_dates[0]
            print(f"\nLatest date: {latest_date.strftime('%Y-%m-%d')}")

            # Filter tanggal yang masuk akal (bukan 1900-01-01)
            valid_dates = [d for d in parsed_dates if d.year > 2000]
            if valid_dates:
                latest_valid = valid_dates[0]
                print(f"Latest valid date: {latest_valid.strftime('%Y-%m-%d')}")
                return latest_valid.strftime('%Y-%m-%d')

            return latest_date.strftime('%Y-%m-%d')
        else:
            print("Could not parse dates")
    else:
        print("No dates found in INSERT statements")

    return None

if __name__ == "__main__":
    latest_date = find_gwscanner_inserts()
    if latest_date:
        print(f"\nFINAL RESULT: Latest GWSCANNER date from INSERT statements is {latest_date}")
    else:
        print("\nNo GWSCANNER INSERT statements with dates found")