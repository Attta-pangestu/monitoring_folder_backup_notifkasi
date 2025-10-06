#!/usr/bin/env python3
"""
Find All Scanner Related Data
Mencari semua data terkait scanner di backup files
"""

import sys
import os
import re
import mmap
from datetime import datetime

def find_scanner_data():
    """Cari semua data scanner di semua backup files"""
    print("=" * 80)
    print("FINDING ALL SCANNER RELATED DATA")
    print("=" * 80)
    print()

    backup_folder = r"D:/Gawean Rebinmas/App_Auto_Backup/Backup"

    # File yang akan di scan
    files_to_scan = [
        "PlantwareP3",
        "BackupStaging 2025-10-04 09;16;30.zip",
        "BackupVenuz 2025-10-04 10;17;35.zip"
    ]

    all_dates = []
    scanner_references = []

    for filename in files_to_scan:
        filepath = os.path.join(backup_folder, filename)
        if not os.path.exists(filepath):
            continue

        print(f"\n{'='*50}")
        print(f"SCANNING: {filename}")
        print('='*50)

        if filename.endswith('.zip'):
            # Handle ZIP file
            import zipfile
            import tempfile

            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)

                    for file in os.listdir(temp_dir):
                        if file.endswith('.bak'):
                            bak_path = os.path.join(temp_dir, file)
                            print(f"  Extracted: {file}")

                            dates, refs = scan_binary_file(bak_path, f"{filename}/{file}")
                            all_dates.extend(dates)
                            scanner_references.extend(refs)
        else:
            # Handle direct .bak file
            dates, refs = scan_binary_file(filepath, filename)
            all_dates.extend(dates)
            scanner_references.extend(refs)

    # Analisis hasil
    print(f"\n{'='*60}")
    print("SCANNER DATA ANALYSIS RESULTS")
    print('='*60)

    print(f"Total scanner references: {len(scanner_references)}")
    print(f"Total date strings found: {len(all_dates)}")

    # Tampilkan sample references
    if scanner_references:
        print(f"\n{'='*40}")
        print("SAMPLE SCANNER REFERENCES")
        print('='*40)

        for i, ref in enumerate(scanner_references[:10]):
            print(f"\n{i+1}. File: {ref['file']}")
            print(f"   Type: {ref['type']}")
            print(f"   Position: {ref['position']}")
            if 'context' in ref:
                print(f"   Context: ...{ref['context'][200:400]}...")

    # Analisis tanggal
    if all_dates:
        print(f"\n{'='*40}")
        print("DATE ANALYSIS")
        print('='*40)

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

            print(f"Successfully parsed {len(parsed_dates)} dates")

            print(f"\n{'='*40}")
            print("LATEST DATES FOUND")
            print('='*40)

            for i, date in enumerate(parsed_dates[:15]):
                print(f"{i+1}. {date.strftime('%Y-%m-%d')}")

            latest_date = parsed_dates[0]
            print(f"\nLatest date: {latest_date.strftime('%Y-%m-%d')}")

            # Filter tanggal valid
            valid_dates = [d for d in parsed_dates if d.year > 2000]
            if valid_dates:
                latest_valid = valid_dates[0]
                print(f"Latest valid date: {latest_valid.strftime('%Y-%m-%d')}")

                # Statistik per tahun
                years = {}
                for date in valid_dates:
                    year = date.year
                    years[year] = years.get(year, 0) + 1

                print(f"\n{'='*40}")
                print("VALID DATES BY YEAR")
                print('='*40)
                for year in sorted(years.keys(), reverse=True):
                    print(f"{year}: {years[year]} dates")

                return latest_valid.strftime('%Y-%m-%d')

            return latest_date.strftime('%Y-%m-%d')
        else:
            print("Could not parse dates")
    else:
        print("No dates found")

    return None

def scan_binary_file(file_path, filename):
    """Scan file binary untuk mencari scanner data"""
    print(f"  Size: {os.path.getsize(file_path) / (1024*1024):.2f} MB")

    all_dates = []
    scanner_references = []

    try:
        with open(file_path, 'rb') as f:
            file_size = os.path.getsize(file_path)

            # Batasi scan untuk performa
            if file_size > 200 * 1024 * 1024:  # > 200MB
                scan_limit = 150 * 1024 * 1024  # 150MB
            else:
                scan_limit = file_size

            mm = mmap.mmap(f.fileno(), scan_limit, access=mmap.ACCESS_READ)

            # Pattern untuk mencari scanner
            scanner_patterns = [
                (b'GWSCANNER', 'GWSCANNER'),
                (b'GATEWAY', 'GATEWAY'),
                (b'SCANNER', 'SCANNER'),
                (b'SCAN_DATA', 'SCAN_DATA'),
                (b'SCAN_RESULT', 'SCAN_RESULT'),
                (b'TRANSDATE', 'TRANSDATE'),
                (b'SCAN_DATE', 'SCAN_DATE'),
            ]

            # Cari semua kemunculan pattern
            for pattern, pattern_type in scanner_patterns:
                pos = 0
                while pos < scan_limit:
                    found_pos = mm.find(pattern, pos)
                    if found_pos == -1:
                        break

                    # Ekstrak konteks
                    context_start = max(0, found_pos - 200)
                    context_end = min(scan_limit, found_pos + 400)
                    context = mm[context_start:context_end]

                    try:
                        context_text = context.decode('utf-8', errors='ignore')

                        scanner_references.append({
                            'file': filename,
                            'type': pattern_type,
                            'position': found_pos,
                            'context': context_text
                        })

                        # Cari tanggal dalam konteks
                        date_patterns = [
                            r'\d{4}-\d{2}-\d{2}',
                            r'\d{2}/\d{2}/\d{4}',
                            r'\d{4}\d{2}\d{2}',
                            r'TRANSDATE\s*=\s*[\'"]?(\d{4}-\d{2}-\d{2})',
                            r'SCAN_DATE\s*=\s*[\'"]?(\d{4}-\d{2}-\d{2})',
                            r'UPDATE_DATE\s*=\s*[\'"]?(\d{4}-\d{2}-\d{2})',
                            r'CREATED_DATE\s*=\s*[\'"]?(\d{4}-\d{2}-\d{2})',
                        ]

                        for date_pattern in date_patterns:
                            matches = re.findall(date_pattern, context_text, re.IGNORECASE)
                            if matches:
                                all_dates.extend(matches)
                                break

                    except Exception as e:
                        pass

                    pos = found_pos + 1

            mm.close()

    except Exception as e:
        print(f"  Error scanning {filename}: {e}")

    return all_dates, scanner_references

if __name__ == "__main__":
    latest_date = find_scanner_data()
    if latest_date:
        print(f"\nFINAL RESULT: Latest scanner date is {latest_date}")
    else:
        print("\nNo scanner dates found")