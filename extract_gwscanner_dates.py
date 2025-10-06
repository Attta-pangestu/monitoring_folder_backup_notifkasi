#!/usr/bin/env python3
"""
Extract Dates from GWSCANNER Table
Mengekstrak informasi tanggal dari tabel GWSCANNER di file BAK
"""

import sys
import os
import re
import mmap
from datetime import datetime

def extract_gwscanner_dates():
    """Ekstrak tanggal dari tabel GWSCANNER"""
    print("=" * 80)
    print("EXTRACTING DATES FROM GWSCANNER TABLE")
    print("=" * 80)
    print()

    bak_path = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup\PlantwareP3"

    if not os.path.exists(bak_path):
        print(f"File not found: {bak_path}")
        return

    print(f"File: {bak_path}")
    print(f"Size: {os.path.getsize(bak_path) / (1024*1024*1024):.2f} GB")

    # Metode 1: Cari semua referensi GWSCANNER dan ekstrak konteks tanggal
    print(f"\n{'='*50}")
    print("METHOD 1: GWSCANNER Date Context Extraction")
    print('='*50)

    gwscanner_dates = []
    gwscanner_contexts = []

    try:
        with open(bak_path, 'rb') as f:
            # Memory mapping untuk pencarian efisien
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

            # Search pattern untuk GWSCANNER
            gwscanner_pattern = b'GWSCANNER'
            pos = 0

            while True:
                pos = mm.find(gwscanner_pattern, pos)
                if pos == -1:
                    break

                # Ekstrak konteks di sekitar GWSCANNER
                context_start = max(0, pos - 500)
                context_end = min(len(mm), pos + 1000)
                context = mm[context_start:context_end]

                try:
                    context_text = context.decode('utf-8', errors='ignore')
                    gwscanner_contexts.append({
                        'position': pos,
                        'context': context_text
                    })

                    # Cari pattern tanggal dalam konteks
                    date_patterns = [
                        r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
                        r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
                        r'\d{4}\d{2}\d{2}',    # YYYYMMDD
                        r'TRANSDATE\s*=\s*[\'"]?\d{4}-\d{2}-\d{2}',  # TRANSDATE = 'YYYY-MM-DD'
                        r'MONTH\(TRANSDATE\)\s*=\s*(\d+)',  # MONTH(TRANSDATE) = X
                        r'YEAR\(TRANSDATE\)\s*=\s*(\d{4})',  # YEAR(TRANSDATE) = YYYY
                    ]

                    for pattern in date_patterns:
                        matches = re.findall(pattern, context_text, re.IGNORECASE)
                        if matches:
                            gwscanner_dates.extend(matches)

                except:
                    pass

                pos += 1

                # Batasi pencarian untuk performansi
                if len(gwscanner_contexts) >= 20:
                    break

            mm.close()

        print(f"Found {len(gwscanner_contexts)} GWSCANNER references")
        print(f"Extracted {len(gwscanner_dates)} date-related values")

        # Tampilkan tanggal-tanggal yang ditemukan
        if gwscanner_dates:
            print(f"\nDate values found:")
            unique_dates = list(set(gwscanner_dates))
            for date in sorted(unique_dates)[:20]:  # Show first 20 unique dates
                print(f"  - {date}")

    except Exception as e:
        print(f"GWSCANNER context extraction failed: {e}")

    # Metode 2: Cari CREATE TABLE GWSCANNER jika ada
    print(f"\n{'='*50}")
    print("METHOD 2: Find GWSCANNER Table Definition")
    print('='*50)

    try:
        with open(bak_path, 'rb') as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

            # Cari CREATE TABLE GWSCANNER
            create_pattern = rb'CREATE\s+TABLE\s+([#\w_]*GWSCANNER[#\w_]*)'
            matches = list(re.finditer(create_pattern, mm, re.IGNORECASE))

            if matches:
                print(f"Found {len(matches)} GWSCANNER table definitions:")
                for i, match in enumerate(matches):
                    table_name = match.group(1).decode('utf-8', errors='ignore')
                    print(f"\nTable {i+1}: {table_name} at position {match.start()}")

                    # Ekstrak definisi tabel lengkap
                    start_pos = match.start()
                    mm.seek(start_pos)
                    table_def = mm.read(5000)  # Baca 5KB untuk definisi

                    try:
                        table_def_text = table_def.decode('utf-8', errors='ignore')
                        # Cari akhir definisi
                        end_create = table_def_text.find(');')
                        if end_create != -1:
                            full_def = table_def_text[:end_create + 2]
                            print(f"  Definition preview: {full_def[:300]}...")

                            # Cari kolom tanggal dalam definisi
                            date_columns = []
                            if 'SCAN_DATE' in full_def:
                                date_columns.append('SCAN_DATE')
                            if 'UPDATE_DATE' in full_def:
                                date_columns.append('UPDATE_DATE')
                            if 'CREATED_AT' in full_def:
                                date_columns.append('CREATED_AT')
                            if 'TRANSDATE' in full_def:
                                date_columns.append('TRANSDATE')

                            if date_columns:
                                print(f"  Date columns found: {date_columns}")
                    except:
                        print(f"  Could not decode table definition")
            else:
                print("No CREATE TABLE GWSCANNER found")

            mm.close()

    except Exception as e:
        print(f"GWSCANNER table definition search failed: {e}")

    # Metode 3: Cari INSERT INTO GWSCANNER untuk sample data
    print(f"\n{'='*50}")
    print("METHOD 3: Find GWSCANNER INSERT Statements")
    print('='*50)

    try:
        with open(bak_path, 'rb') as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

            # Cari INSERT INTO GWSCANNER
            insert_pattern = rb'INSERT\s+INTO\s+([#\w_]*GWSCANNER[#\w_]*)'
            matches = list(re.finditer(insert_pattern, mm, re.IGNORECASE))

            print(f"Found {len(matches)} GWSCANNER INSERT statements")

            for i, match in enumerate(matches[:5]):  # Show first 5
                table_name = match.group(1).decode('utf-8', errors='ignore')
                pos = match.start()

                print(f"\nINSERT {i+1}: {table_name} at position {pos}")

                # Ekstrak INSERT statement
                mm.seek(pos)
                insert_statement = mm.read(2000)  # Baca 2KB

                try:
                    insert_text = insert_statement.decode('utf-8', errors='ignore')
                    # Cari akhir statement
                    end_insert = insert_text.find(');')
                    if end_insert != -1:
                        full_insert = insert_text[:end_insert + 2]
                        print(f"  Statement preview: {full_insert[:300]}...")

                        # Cari nilai tanggal dalam INSERT
                        date_values = re.findall(r'(\'\d{4}-\d{2}-\d{2}[^\'\"]*\'|\d{4}-\d{2}-\d{2})', full_insert)
                        if date_values:
                            print(f"  Date values in INSERT: {date_values}")
                except:
                    print(f"  Could not decode INSERT statement")

            mm.close()

    except Exception as e:
        print(f"GWSCANNER INSERT search failed: {e}")

    # Metode 4: Cari UPDATE GWSCANNER dengan tanggal
    print(f"\n{'='*50}")
    print("METHOD 4: Find GWSCANNER UPDATE with Dates")
    print('='*50)

    update_dates = []

    try:
        with open(bak_path, 'rb') as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

            # Cari UPDATE ... GWSCANNER dengan tanggal
            update_pattern = rb'UPDATE\s+[^\s]+\s+SET\s+[^=]*=\s*[\'"]?\d{4}-\d{2}-\d{2}[^\'"]*?[^W]*WHERE[^G]*GWSCANNER'
            matches = list(re.finditer(update_pattern, mm, re.IGNORECASE | re.DOTALL))

            print(f"Found {len(matches)} GWSCANNER UPDATE statements with dates")

            for i, match in enumerate(matches):
                update_text = match.group().decode('utf-8', errors='ignore')
                print(f"\nUPDATE {i+1}:")
                print(f"  {update_text[:200]}...")

                # Ekstrak tanggal dari UPDATE
                date_matches = re.findall(r'\d{4}-\d{2}-\d{2}', update_text)
                if date_matches:
                    update_dates.extend(date_matches)
                    print(f"  Dates: {date_matches}")

            mm.close()

    except Exception as e:
        print(f"GWSCANNER UPDATE search failed: {e}")

    # Metode 5: Analisis tanggal yang ditemukan
    print(f"\n{'='*50}")
    print("METHOD 5: Date Analysis")
    print('='*50)

    all_dates = gwscanner_dates + update_dates

    if all_dates:
        print(f"Total date values found: {len(all_dates)}")

        # Clean dan normalisasi tanggal
        clean_dates = []
        for date in all_dates:
            # Remove quote dan karakter lain
            clean_date = re.sub(r'[\'"\\]', '', date.strip())

            # Coba parse sebagai tanggal
            date_formats = [
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%Y%m%d',
                '%m/%d/%Y'
            ]

            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(clean_date, fmt)
                    clean_dates.append(parsed_date)
                    break
                except:
                    continue

        if clean_dates:
            print(f"Successfully parsed {len(clean_dates)} dates")

            # Tampilkan range tanggal
            if clean_dates:
                min_date = min(clean_dates)
                max_date = max(clean_dates)
                print(f"Date range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")

                # Tampilkan tanggal terbaru
                sorted_dates = sorted(clean_dates, reverse=True)
                print(f"\nLatest dates:")
                for i, date in enumerate(sorted_dates[:10]):
                    print(f"  {i+1}. {date.strftime('%Y-%m-%d')}")

                # Group by year
                years = {}
                for date in clean_dates:
                    year = date.year
                    if year not in years:
                        years[year] = []
                    years[year].append(date)

                print(f"\nDates by year:")
                for year in sorted(years.keys(), reverse=True):
                    count = len(years[year])
                    print(f"  {year}: {count} dates")

        else:
            print("Could not parse any dates")

    else:
        print("No date values found")

    # Metode 6: Cari parameter tanggal di stored procedure/function
    print(f"\n{'='*50}")
    print("METHOD 6: Date Parameters in GWSCANNER Operations")
    print('='*50)

    try:
        with open(bak_path, 'rb') as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

            # Cari parameter tanggal yang terkait GWSCANNER
            param_patterns = [
                rb'@DelPhyMonth\s*=\s*(\d+)',
                rb'@DelPhyYear\s*=\s*(\d{4})',
                rb'MONTH\(TRANSDATE\)\s*=\s*@(\w+)',
                rb'YEAR\(TRANSDATE\)\s*=\s*@(\w+)',
                rb'GWSCANNER.*?WHERE.*?(\d{4}-\d{2}-\d{2})'
            ]

            for pattern in param_patterns:
                matches = list(re.finditer(pattern, mm, re.IGNORECASE | re.DOTALL))
                for match in matches:
                    if len(match.groups()) > 0:
                        param_value = match.group(1).decode('utf-8', errors='ignore')
                        print(f"Found date parameter: {param_value}")

            mm.close()

    except Exception as e:
        print(f"Date parameter search failed: {e}")

    print(f"\n{'='*80}")
    print("GWSCANNER DATE EXTRACTION SUMMARY")
    print("="*80)
    print("Hasil ekstraksi tanggal dari GWSCANNER:")
    print(f"- Total references found: {len(gwscanner_contexts)}")
    print(f"- Date values extracted: {len(all_dates)}")
    print(f"- Successfully parsed dates: {len(clean_dates) if clean_dates else 0}")

    if clean_dates:
        print(f"- Date range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
        print("- Data mencakup beberapa tahun operasi")

    print("\nRekomendasi:")
    print("- Gunakan tanggal terbaru untuk monitoring")
    print("- Fokus pada data dari tahun terakhir untuk analisis")
    print("- Pertimbangkan untuk membuat parser lengkap untuk ekstrak data GWSCANNER")

if __name__ == "__main__":
    extract_gwscanner_dates()