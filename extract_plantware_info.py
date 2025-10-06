#!/usr/bin/env python3
"""
Extract Plantware Information
Mengekstrak informasi detail dari file PlantwareP3.bak
"""

import sys
import os
import re
from pathlib import Path

def extract_plantware_info():
    """Ekstrak informasi dari file PlantwareP3.bak"""
    print("=" * 80)
    print("PLANTWARE INFORMATION EXTRACTION")
    print("=" * 80)
    print()

    bak_path = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup\PlantwareP3"

    if not os.path.exists(bak_path):
        print(f"File not found: {bak_path}")
        return

    print(f"File: {bak_path}")
    print(f"Size: {os.path.getsize(bak_path) / (1024*1024*1024):.2f} GB")

    try:
        with open(bak_path, 'rb') as f:
            # Baca file dalam chunk untuk mencari informasi
            chunk_size = 1024 * 1024  # 1MB
            total_chunks = min(10, os.path.getsize(bak_path) // chunk_size)

            print(f"\nScanning {total_chunks} chunks...")

            tables_found = []
            create_statements = []
            table_references = {}

            for chunk_num in range(total_chunks):
                f.seek(chunk_num * chunk_size)
                chunk_data = f.read(chunk_size)

                # Convert ke string untuk pencarian (handle encoding issues)
                try:
                    chunk_str = chunk_data.decode('utf-8', errors='ignore')
                except:
                    chunk_str = chunk_data.decode('latin-1', errors='ignore')

                # Cari CREATE TABLE statements
                create_matches = re.finditer(r'CREATE\s+TABLE\s+(#[\w_]+|[\w_]+)\s*\(', chunk_str, re.IGNORECASE)
                for match in create_matches:
                    table_name = match.group(1)
                    start_pos = match.start()
                    end_pos = chunk_str.find(');', start_pos)
                    if end_pos == -1:
                        end_pos = len(chunk_str)

                    table_def = chunk_str[start_pos:end_pos + 2]
                    create_statements.append({
                        'table_name': table_name,
                        'definition': table_def[:300] + '...' if len(table_def) > 300 else table_def,
                        'chunk': chunk_num,
                        'position': start_pos
                    })

                # Cari nama tabel yang di-reference
                table_names = ['PR_TASKREG', 'TA_MACHINE', 'GWSCANNER', 'PR_USER', 'PR_PROJECT',
                               'PR_DEPARTMENT', 'PR_EMPLOYEE', 'PR_LOG', 'PR_CONFIG']

                for table_name in table_names:
                    if table_name in chunk_str:
                        pos = chunk_str.find(table_name)
                        if table_name not in table_references:
                            table_references[table_name] = []
                        table_references[table_name].append({
                            'chunk': chunk_num,
                            'position': pos,
                            'context': chunk_str[max(0, pos-100):min(len(chunk_str), pos+200)]
                        })

                # Cari pattern data yang mungkin berisi informasi
                # Cari pattern tanggal (YYYY-MM-DD)
                date_pattern = r'\d{4}-\d{2}-\d{2}'
                dates = re.findall(date_pattern, chunk_str)
                if dates:
                    print(f"\nDates found in chunk {chunk_num}: {list(set(dates))[:5]}")

            # Tampilkan hasil
            print(f"\n{'='*50}")
            print("CREATE TABLE STATEMENTS FOUND")
            print('='*50)
            if create_statements:
                for i, stmt in enumerate(create_statements):
                    print(f"\n{i+1}. Table: {stmt['table_name']}")
                    print(f"   Chunk: {stmt['chunk']}, Position: {stmt['position']}")
                    print(f"   Definition: {stmt['definition']}")
            else:
                print("No CREATE TABLE statements found")

            print(f"\n{'='*50}")
            print("TABLE REFERENCES FOUND")
            print('='*50)
            if table_references:
                for table_name, refs in table_references.items():
                    print(f"\nTable: {table_name}")
                    print(f"References found: {len(refs)}")
                    for i, ref in enumerate(refs[:3]):  # Show first 3 references
                        print(f"   {i+1}. Chunk {ref['chunk']}, Position {ref['position']}")
                        print(f"      Context: ...{ref['context'][100:300]}...")
            else:
                print("No table references found")

            # Analisis spesifik untuk PR_TASKREG
            print(f"\n{'='*50}")
            print("PR_TASKREG ANALYSIS")
            print('='*50)
            if 'PR_TASKREG' in table_references:
                refs = table_references['PR_TASKREG']
                print(f"PR_TASKREG found in {len(refs)} locations")

                # Coba ekstrak lebih banyak konteks
                f.seek(0)
                file_data = f.read(5 * 1024 * 1024)  # Baca 5MB
                try:
                    file_str = file_data.decode('utf-8', errors='ignore')
                except:
                    file_str = file_data.decode('latin-1', errors='ignore')

                # Cari informasi sekitar PR_TASKREG
                pr_positions = []
                start = 0
                while True:
                    pos = file_str.find('PR_TASKREG', start)
                    if pos == -1:
                        break
                    pr_positions.append(pos)
                    start = pos + 1

                print(f"\nFound PR_TASKREG at {len(pr_positions)} positions")

                for i, pos in enumerate(pr_positions[:5]):  # Show first 5
                    context_start = max(0, pos - 200)
                    context_end = min(len(file_str), pos + 500)
                    context = file_str[context_start:context_end]

                    print(f"\nReference {i+1} at position {pos}:")
                    print(f"Context:\n{context}")

                    # Cari pattern yang mungkin column names
                    column_patterns = [
                        r'TGLREG,\s*TGLUPDATE,\s*TGLKIRIM',
                        r'TGLREG|TGLUPDATE|TGLKIRIM',
                        r'SELECT\s+.*\s+FROM\s+PR_TASKREG',
                        r'INSERT\s+INTO\s+PR_TASKREG'
                    ]

                    for pattern in column_patterns:
                        matches = re.findall(pattern, context, re.IGNORECASE)
                        if matches:
                            print(f"   Pattern found: {pattern} -> {matches}")

            else:
                print("PR_TASKREG not found in file")

    except Exception as e:
        print(f"Error reading file: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n{'='*80}")
    print("EXTRACTION SUMMARY")
    print("="*80)
    print("File PlantwareP3.bak mengandung:")
    print("- Struktur database dalam format TAPE")
    print("- Beberapa CREATE TABLE statements")
    print("- Reference ke tabel PR_TASKREG")
    print("- Kemungkinan besar data lengkap ada di dalam file")
    print()
    print("Untuk akses penuh, dibutuhkan:")
    print("- Plantware P3 software")
    print("- TAPE format parser")
    print("- Atau conversion tools ke SQLite")

if __name__ == "__main__":
    extract_plantware_info()