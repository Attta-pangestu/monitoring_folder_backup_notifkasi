#!/usr/bin/env python3
"""
Quick GWSCANNER Date Extraction
Fokus mencari tanggal terbaru dari GWSCANNER dengan performa optimal
"""

import sys
import os
import re
import mmap
from datetime import datetime

def quick_extract_gwscanner_dates():
    """Ekstrak tanggal terbaru dari GWSCANNER dengan cepat"""
    print("=" * 80)
    print("QUICK GWSCANNER LATEST DATES EXTRACTION")
    print("=" * 80)
    print()

    bak_path = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup\PlantwareP3"

    if not os.path.exists(bak_path):
        print(f"File not found: {bak_path}")
        return

    print(f"File: {bak_path}")
    print(f"Size: {os.path.getsize(bak_path) / (1024*1024*1024):.2f} GB")

    # Fokus pencarian: Cari GWSCANNER dengan tanggal di sekitarnya
    all_dates = []
    found_positions = []

    try:
        with open(bak_path, 'rb') as f:
            # Memory mapping untuk pencarian cepat
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

            # Strategy 1: Cari semua GWSCANNER dan ekstrak tanggal di sekitarnya
            print(f"Searching for GWSCANNER with dates...")

            gwscanner_pattern = b'GWSCANNER'
            search_pos = 0
            max_matches = 50  # Batasi untuk performa

            while len(found_positions) < max_matches:
                pos = mm.find(gwscanner_pattern, search_pos)
                if pos == -1:
                    break

                # Ekstrak konteks di sekitar GWSCANNER (lebih kecil untuk performa)
                context_start = max(0, pos - 300)
                context_end = min(len(mm), pos + 500)
                context = mm[context_start:context_end]

                try:
                    context_text = context.decode('utf-8', errors='ignore')

                    # Cari pattern tanggal dalam konteks
                    date_patterns = [
                        r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
                        r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
                        r'\d{4}\d{2}\d{2}',    # YYYYMMDD
                        r'TRANSDATE\s*=\s*[\'"]?(\d{4}-\d{2}-\d{2})',  # TRANSDATE = 'YYYY-MM-DD'
                        r'SCAN_DATE\s*=\s*[\'"]?(\d{4}-\d{2}-\d{2})',  # SCAN_DATE = 'YYYY-MM-DD'
                        r'UPDATE_DATE\s*=\s*[\'"]?(\d{4}-\d{2}-\d{2})',  # UPDATE_DATE = 'YYYY-MM-DD'
                    ]

                    for pattern in date_patterns:
                        matches = re.findall(pattern, context_text, re.IGNORECASE)
                        if matches:
                            all_dates.extend(matches)
                            found_positions.append(pos)
                            break

                except:
                    pass

                search_pos = pos + 1

                # Berhenti jika sudah terlalu jauh
                if search_pos > 50 * 1024 * 1024:  # 50MB limit
                    break

            # Strategy 2: Cari INSERT INTO GWSCANNER dengan tanggal
            print(f"Searching for GWSCANNER INSERT statements...")

            insert_pattern = rb'INSERT\s+INTO\s+[#\w_]*GWSCANNER[#\w_]*\s*\([^)]*\)\s*VALUES\s*\([^)]*(\d{4}-\d{2}-\d{2})[^)]*\)'

            search_pos = 0
            while search_pos < len(mm) - 100:
                # Cari pattern yang lebih sederhana dulu
                insert_start = mm.find(rb'INSERT', search_pos)
                if insert_start == -1:
                    break

                # Cari GWSCANNER di sekitar INSERT
                gwscanner_pos = mm.find(gwscanner_pattern, insert_start, insert_start + 200)
                if gwscanner_pos != -1:
                    # Ekstrak konteks INSERT
                    insert_context = mm[insert_start:insert_start + 1000]
                    try:
                        insert_text = insert_context.decode('utf-8', errors='ignore')

                        # Cari tanggal dalam INSERT
                        date_matches = re.findall(r'\d{4}-\d{2}-\d{2}', insert_text)
                        if date_matches:
                            all_dates.extend(date_matches)
                    except:
                        pass

                search_pos = insert_start + 1

                # Batasi pencarian
                if search_pos > 100 * 1024 * 1024:  # 100MB limit
                    break

            mm.close()

    except Exception as e:
        print(f"Search failed: {e}")
        return

    # Analisis tanggal yang ditemukan
    print(f"\n{'='*50}")
    print("DATE ANALYSIS RESULTS")
    print('='*50)

    print(f"Total date strings found: {len(all_dates)}")
    print(f"GWSCANNER references found: {len(found_positions)}")

    if all_dates:
        # Clean dan parse tanggal
        parsed_dates = []

        for date_str in all_dates:
            # Clean string
            clean_date = re.sub(r'[\'"\\]', '', date_str.strip())

            # Coba parse dengan berbagai format
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
            print(f"Successfully parsed {len(parsed_dates)} dates")

            # Tanggal terbaru
            sorted_dates = sorted(parsed_dates, reverse=True)

            print(f"\n{'='*40}")
            print("LATEST DATES FOUND")
            print('='*40)

            for i, date in enumerate(sorted_dates[:10]):
                print(f"{i+1}. {date.strftime('%Y-%m-%d')}")

            print(f"\nLatest date: {sorted_dates[0].strftime('%Y-%m-%d')}")
            print(f"Oldest date: {sorted_dates[-1].strftime('%Y-%m-%d')}")

            # Statistik per tahun
            years = {}
            for date in parsed_dates:
                year = date.year
                years[year] = years.get(year, 0) + 1

            print(f"\n{'='*40}")
            print("DATES BY YEAR")
            print('='*40)
            for year in sorted(years.keys(), reverse=True):
                print(f"{year}: {years[year]} dates")

            return sorted_dates[0].strftime('%Y-%m-%d')
        else:
            print("Could not parse any dates")
    else:
        print("No dates found")

    return None

if __name__ == "__main__":
    latest_date = quick_extract_gwscanner_dates()
    if latest_date:
        print(f"\nFINAL RESULT: Latest date from GWSCANNER is {latest_date}")