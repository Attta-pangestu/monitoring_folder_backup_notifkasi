#!/usr/bin/env python3
"""
Direct ZIP Scanner
Scan ZIP files tanpa mengekstrak ke disk
"""

import sys
import os
import re
import zipfile
from datetime import datetime

def scan_zip_directly(zip_path, filename):
    """Scan ZIP file tanpa ekstraksi"""
    print(f"  Size: {os.path.getsize(zip_path) / (1024*1024):.2f} MB")

    all_dates = []
    scanner_references = []

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Cari file .bak di ZIP
            bak_files = [f for f in zip_ref.namelist() if f.endswith('.bak')]
            print(f"  BAK files in ZIP: {bak_files}")

            for bak_file in bak_files:
                print(f"  Scanning: {bak_file}")

                # Baca file dari ZIP tanpa ekstraksi
                with zip_ref.open(bak_file) as file_in_zip:
                    # Baca dalam chunks untuk menghemat memory
                    chunk_size = 1024 * 1024  # 1MB
                    chunks_to_scan = 50  # Batasi chunks

                    for chunk_num in range(chunks_to_scan):
                        chunk = file_in_zip.read(chunk_size)
                        if not chunk:
                            break

                        try:
                            chunk_text = chunk.decode('utf-8', errors='ignore')

                            # Cari scanner patterns
                            scanner_patterns = [
                                'GWSCANNER',
                                'GATEWAY',
                                'SCANNER',
                                'SCAN_DATA',
                                'SCAN_RESULT',
                                'TRANSDATE',
                                'SCAN_DATE',
                            ]

                            for pattern in scanner_patterns:
                                positions = []
                                start = 0
                                while True:
                                    pos = chunk_text.find(pattern, start)
                                    if pos == -1:
                                        break
                                    positions.append(pos)
                                    start = pos + 1

                                if positions:
                                    global_pos = chunk_num * chunk_size + pos

                                    for pos in positions[:5]:  # Batasi hasil
                                        context_start = max(0, pos - 150)
                                        context_end = min(len(chunk_text), pos + 300)
                                        context = chunk_text[context_start:context_end]

                                        scanner_references.append({
                                            'file': f"{filename}/{bak_file}",
                                            'type': pattern,
                                            'position': global_pos,
                                            'context': context
                                        })

                                        # Cari tanggal
                                        date_patterns = [
                                            r'\d{4}-\d{2}-\d{2}',
                                            r'\d{2}/\d{2}/\d{4}',
                                            r'\d{4}\d{2}\d{2}',
                                            r'TRANSDATE\s*=\s*[\'"]?(\d{4}-\d{2}-\d{2})',
                                            r'SCAN_DATE\s*=\s*[\'"]?(\d{4}-\d{2}-\d{2})',
                                        ]

                                        for date_pattern in date_patterns:
                                            matches = re.findall(date_pattern, context, re.IGNORECASE)
                                            if matches:
                                                all_dates.extend(matches)
                                                break

                        except Exception as e:
                            pass

    except Exception as e:
        print(f"  Error scanning {filename}: {e}")

    return all_dates, scanner_references

def final_scanner_search():
    """Pencarian akhir untuk data scanner"""
    print("=" * 80)
    print("FINAL SCANNER DATA SEARCH")
    print("=" * 80)
    print()

    backup_folder = r"D:/Gawean Rebinmas/App_Auto_Backup/Backup"

    # File yang akan di scan
    files_to_scan = [
        "BackupStaging 2025-10-04 09;16;30.zip",
        "BackupVenuz 2025-10-04 10;17;35.zip"
    ]

    all_dates = []
    all_references = []

    for filename in files_to_scan:
        filepath = os.path.join(backup_folder, filename)
        if not os.path.exists(filepath):
            continue

        print(f"\n{'='*50}")
        print(f"SCANNING: {filename}")
        print('='*50)

        dates, refs = scan_zip_directly(filepath, filename)
        all_dates.extend(dates)
        all_references.extend(refs)

    # Scan Plantware juga (hanya sebagian)
    print(f"\n{'='*50}")
    print("SCANNING: PlantwareP3 (partial)")
    print('='*50)

    plantware_path = os.path.join(backup_folder, "PlantwareP3")
    if os.path.exists(plantware_path):
        # Batasi scan ke 50MB pertama
        with open(plantware_path, 'rb') as f:
            limited_data = f.read(50 * 1024 * 1024)  # 50MB
            try:
                text_data = limited_data.decode('utf-8', errors='ignore')

                # Cari tanggal terbaru
                date_matches = re.findall(r'\d{4}-\d{2}-\d{2}', text_data)
                if date_matches:
                    print(f"Found {len(date_matches)} date strings in first 50MB")
                    all_dates.extend(date_matches[:50])  # Batasi

                    # Cari beberapa pattern spesifik
                    for i, date in enumerate(date_matches[:10]):
                        print(f"  Date {i+1}: {date}")

            except Exception as e:
                print(f"Error reading Plantware: {e}")

    # Analisis final
    print(f"\n{'='*60}")
    print("FINAL ANALYSIS RESULTS")
    print('='*60)

    print(f"Total references found: {len(all_references)}")
    print(f"Total date strings found: {len(all_dates)}")

    if all_references:
        print(f"\n{'='*40}")
        print("SAMPLE REFERENCES")
        print('='*40)

        for i, ref in enumerate(all_references[:5]):
            print(f"\n{i+1}. {ref['file']}")
            print(f"   Type: {ref['type']}")
            print(f"   Context: ...{ref['context'][100:250]}...")

    # Parse dan analisis tanggal
    if all_dates:
        print(f"\n{'='*40}")
        print("DATE ANALYSIS")
        print('='*40)

        parsed_dates = []
        for date_str in list(set(all_dates)):  # Remove duplicates
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
                    # Filter tanggal yang masuk akal
                    if 2000 < parsed_date.year <= 2030:
                        parsed_dates.append(parsed_date)
                    break
                except:
                    continue

        if parsed_dates:
            parsed_dates.sort(reverse=True)

            print(f"Successfully parsed {len(parsed_dates)} valid dates")

            print(f"\n{'='*40}")
            print("LATEST DATES FOUND")
            print('='*40)

            for i, date in enumerate(parsed_dates[:15]):
                print(f"{i+1}. {date.strftime('%Y-%m-%d')}")

            latest_date = parsed_dates[0]
            print(f"\nLatest date: {latest_date.strftime('%Y-%m-%d')}")

            return latest_date.strftime('%Y-%m-%d')
        else:
            print("No valid dates found")
    else:
        print("No dates found")

    return None

if __name__ == "__main__":
    latest_date = final_scanner_search()
    if latest_date:
        print(f"\nFINAL RESULT: Latest scanner date is {latest_date}")
    else:
        print("\nNo scanner dates found in any backup files")