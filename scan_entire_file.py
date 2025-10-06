#!/usr/bin/env python3
"""
Scan Entire File for GWSCANNER
Mencari GWSCANNER di seluruh file dengan strategi berbeda
"""

import sys
import os
import re
import mmap
from datetime import datetime

def scan_entire_file():
    """Scan seluruh file untuk mencari GWSCANNER"""
    print("=" * 80)
    print("COMPREHENSIVE GWSCANNER SCAN")
    print("=" * 80)
    print()

    bak_path = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup\PlantwareP3"

    if not os.path.exists(bak_path):
        print(f"File not found: {bak_path}")
        return

    print(f"File: {bak_path}")
    print(f"Size: {os.path.getsize(bak_path) / (1024*1024*1024):.2f} GB")

    # Coba cari semua tabel yang ada dulu
    try:
        with open(bak_path, 'rb') as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

            print(f"Scanning for all table names...")

            # Cari CREATE TABLE statements
            create_pattern = rb'CREATE\s+TABLE\s+([#\w_]+)'
            matches = list(re.finditer(create_pattern, mm, re.IGNORECASE))

            print(f"Found {len(matches)} CREATE TABLE statements")

            # Tampilkan beberapa tabel
            tables_found = []
            for i, match in enumerate(matches[:20]):
                table_name = match.group(1).decode('utf-8', errors='ignore')
                tables_found.append(table_name)
                print(f"{i+1}. {table_name}")

            # Cari khusus GWSCANNER
            gwscanner_tables = []
            for match in matches:
                table_name = match.group(1).decode('utf-8', errors='ignore')
                if 'GWSCANNER' in table_name.upper():
                    gwscanner_tables.append(table_name)

            if gwscanner_tables:
                print(f"\nGWSCANNER tables found: {gwscanner_tables}")
            else:
                print(f"\nNo GWSCANNER tables found in CREATE TABLE statements")

            # Cari semua kemunculan kata GWSCANNER
            print(f"\nSearching for all GWSCANNER references...")
            mm.seek(0)

            gwscanner_bytes = b'GWSCANNER'
            positions = []
            search_pos = 0

            while search_pos < len(mm):
                pos = mm.find(gwscanner_bytes, search_pos)
                if pos == -1:
                    break

                positions.append(pos)
                search_pos = pos + 1

                # Batasi hasil
                if len(positions) > 100:
                    break

            print(f"Found {len(positions)} GWSCANNER references")

            if positions:
                print(f"\nFirst 10 GWSCANNER positions:")
                for i, pos in enumerate(positions[:10]):
                    # Tampilkan konteks
                    context_start = max(0, pos - 100)
                    context_end = min(len(mm), pos + 100)
                    context = mm[context_start:context_end]

                    try:
                        context_text = context.decode('utf-8', errors='ignore')
                        print(f"{i+1}. Position {pos}: ...{context_text}...")
                    except:
                        print(f"{i+1}. Position {pos}: [binary data]")

                # Cari tanggal di sekitar GWSCANNER
                print(f"\nExtracting dates from GWSCANNER contexts...")
                all_dates = []

                for pos in positions[:50]:  # Batasi untuk performa
                    context_start = max(0, pos - 500)
                    context_end = min(len(mm), pos + 1000)
                    context = mm[context_start:context_end]

                    try:
                        context_text = context.decode('utf-8', errors='ignore')

                        # Cari pattern tanggal
                        date_patterns = [
                            r'\d{4}-\d{2}-\d{2}',
                            r'\d{2}/\d{2}/\d{4}',
                            r'\d{4}\d{2}\d{2}',
                            r'TRANSDATE\s*=\s*[\'"]?(\d{4}-\d{2}-\d{2})',
                            r'SCAN_DATE\s*=\s*[\'"]?(\d{4}-\d{2}-\d{2})',
                            r'UPDATE_DATE\s*=\s*[\'"]?(\d{4}-\d{2}-\d{2})',
                        ]

                        for pattern in date_patterns:
                            matches = re.findall(pattern, context_text, re.IGNORECASE)
                            if matches:
                                all_dates.extend(matches)
                                break

                    except:
                        continue

                # Analisis tanggal
                if all_dates:
                    print(f"\nFound {len(all_dates)} date strings")

                    # Parse tanggal
                    parsed_dates = []
                    for date_str in all_dates:
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
                        print("LATEST DATES FROM GWSCANNER")
                        print('='*40)

                        for i, date in enumerate(parsed_dates[:10]):
                            print(f"{i+1}. {date.strftime('%Y-%m-%d')}")

                        print(f"\nLatest date: {parsed_dates[0].strftime('%Y-%m-%d')}")
                        return parsed_dates[0].strftime('%Y-%m-%d')
                else:
                    print("\nNo dates found in GWSCANNER contexts")
            else:
                print("\nNo GWSCANNER references found in entire file")

            mm.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    return None

if __name__ == "__main__":
    latest_date = scan_entire_file()
    if latest_date:
        print(f"\nFINAL RESULT: Latest GWSCANNER date is {latest_date}")
    else:
        print("\nNo GWSCANNER dates found")