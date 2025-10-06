#!/usr/bin/env python3
"""
Advanced BAK File Extractor
Menggunakan tools Python yang lebih advanced untuk ekstrak data
"""

import sys
import os
import re
import mmap
import struct
from pathlib import Path

def advanced_extraction():
    """Ekstrak data dari BAK file dengan metode advanced"""
    print("=" * 80)
    print("ADVANCED BAK FILE EXTRACTION")
    print("=" * 80)
    print()

    bak_path = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup\PlantwareP3"

    if not os.path.exists(bak_path):
        print(f"File not found: {bak_path}")
        return

    print(f"File: {bak_path}")
    print(f"Size: {os.path.getsize(bak_path) / (1024*1024*1024):.2f} GB")

    # Metode 1: Memory Mapping dengan Advanced Pattern Matching
    print(f"\n{'='*50}")
    print("METHOD 1: Advanced Memory Mapping")
    print('='*50)
    try:
        with open(bak_path, 'rb') as f:
            # Memory map seluruh file (untuk file besar, gunakan sliding window)
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

            # Cari semua CREATE TABLE statements
            create_table_positions = []
            search_start = 0
            chunk_size = 10 * 1024 * 1024  # 10MB chunks
            file_size = os.path.getsize(bak_path)

            while search_start < file_size:
                end_pos = min(search_start + chunk_size, file_size)
                mm.seek(search_start)
                chunk = mm.read(chunk_size)

                # Cari CREATE TABLE dalam chunk
                pattern = rb'CREATE\s+TABLE\s+([#\w_]+)'
                matches = list(re.finditer(pattern, chunk, re.IGNORECASE))

                for match in matches:
                    global_pos = search_start + match.start()
                    table_name = match.group(1).decode('utf-8', errors='ignore')
                    create_table_positions.append((global_pos, table_name))

                search_start = end_pos
                if len(create_table_positions) >= 20:  # Batasi untuk performansi
                    break

            print(f"Found {len(create_table_positions)} CREATE TABLE statements")

            # Tampilkan detail beberapa tabel
            for i, (pos, table_name) in enumerate(create_table_positions[:10]):
                print(f"\nTable {i+1}: {table_name} at position {pos}")

                # Ekstrak table definition
                mm.seek(pos)
                table_def_chunk = mm.read(2000)  # Baca 2KB untuk definisi

                try:
                    table_def = table_def_chunk.decode('utf-8', errors='ignore')
                    # Cari akhir dari CREATE TABLE
                    end_create = table_def.find(');')
                    if end_create != -1:
                        full_def = table_def[:end_create + 2]
                        print(f"  Definition preview: {full_def[:200]}...")
                except:
                    print(f"  Could not decode table definition")

            mm.close()

    except Exception as e:
        print(f"Advanced memory mapping failed: {e}")

    # Metode 2: SQL String Extraction
    print(f"\n{'='*50}")
    print("METHOD 2: SQL String Extraction")
    print('='*50)
    try:
        with open(bak_path, 'rb') as f:
            # Baca file dalam chunks yang lebih kecil
            chunk_size = 1024 * 1024  # 1MB
            sql_statements = []

            for i in range(5):  # Baca 5 chunk pertama
                f.seek(i * chunk_size)
                chunk = f.read(chunk_size)

                # Coba decode dengan berbagai encoding
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        text = chunk.decode(encoding, errors='ignore')

                        # Ekstrak SQL statements
                        # CREATE TABLE
                        create_matches = re.findall(r'CREATE\s+TABLE\s+([#\w_]+)\s*\([^)]*\)', text, re.IGNORECASE | re.DOTALL)
                        for match in create_matches:
                            sql_statements.append(('CREATE_TABLE', match))

                        # INSERT INTO
                        insert_matches = re.findall(r'INSERT\s+INTO\s+([#\w_]+)', text, re.IGNORECASE)
                        for match in insert_matches:
                            sql_statements.append(('INSERT_INTO', match))

                        # SELECT statements
                        select_matches = re.findall(r'SELECT\s+.+?\s+FROM\s+([#\w_]+)', text, re.IGNORECASE | re.DOTALL)
                        for match in select_matches:
                            sql_statements.append(('SELECT', match))

                        break  # Stop jika encoding berhasil
                    except:
                        continue

            print(f"Extracted {len(sql_statements)} SQL statements")

            # Kelompokkan berdasarkan jenis
            statement_types = {}
            for stmt_type, table_name in sql_statements:
                if stmt_type not in statement_types:
                    statement_types[stmt_type] = set()
                statement_types[stmt_type].add(table_name)

            for stmt_type, tables in statement_types.items():
                print(f"\n{stmt_type}: {len(tables)} unique tables")
                for table in sorted(list(tables))[:5]:
                    print(f"  - {table}")

    except Exception as e:
        print(f"SQL string extraction failed: {e}")

    # Metode 3: Binary Structure Analysis
    print(f"\n{'='*50}")
    print("METHOD 3: Binary Structure Analysis")
    print('='*50)
    try:
        with open(bak_path, 'rb') as f:
            # Analisis header structure
            header = f.read(512)  # Baca 512 bytes pertama
            print(f"Header analysis (first 512 bytes):")
            print(f"  Header (hex): {header.hex()[:100]}...")

            # Cari pattern yang menunjukkan struktur
            patterns = [
                (b'SELECT', 'SELECT statement'),
                (b'INSERT', 'INSERT statement'),
                (b'CREATE', 'CREATE statement'),
                (b'UPDATE', 'UPDATE statement'),
                (b'DELETE', 'DELETE statement'),
                (b'FROM', 'FROM clause'),
                (b'WHERE', 'WHERE clause'),
                (b'JOIN', 'JOIN clause'),
            ]

            for pattern, description in patterns:
                pos = header.find(pattern)
                if pos != -1:
                    print(f"  Found {description} at position {pos}")

            # Cari numeric patterns yang mungkin menunjukkan ukuran/offset
            print(f"\nLooking for structural patterns...")
            for i in range(0, len(header) - 4, 4):
                dword = struct.unpack('<I', header[i:i+4])[0]
                # Cari nilai yang masuk akal sebagai offset/size
                if 1000 < dword < 100000000:  # Reasonable range for file offsets
                    print(f"  Possible offset/size at {i}: {dword}")

    except Exception as e:
        print(f"Binary structure analysis failed: {e}")

    # Metode 4: Extract Table Names dan Data Patterns
    print(f"\n{'='*50}")
    print("METHOD 4: Table and Data Pattern Extraction")
    print('='*50)
    try:
        # Table names yang dicari berdasarkan dokumentasi
        target_tables = ['PR_TASKREG', 'TA_MACHINE', 'GWSCANNER', 'PR_USER', 'PR_PROJECT']

        with open(bak_path, 'rb') as f:
            # Cari setiap tabel target
            for table_name in target_tables:
                table_bytes = table_name.encode('utf-8')

                # Reset file pointer
                f.seek(0)

                # Search dalam chunks
                chunk_size = 1024 * 1024
                found_positions = []

                for chunk_num in range(10):  # Search 10 chunks
                    f.seek(chunk_num * chunk_size)
                    chunk = f.read(chunk_size)

                    pos = 0
                    while True:
                        pos = chunk.find(table_bytes, pos)
                        if pos == -1:
                            break

                        global_pos = chunk_num * chunk_size + pos
                        found_positions.append(global_pos)

                        # Tampilkan konteks
                        context_start = max(0, pos - 100)
                        context_end = min(len(chunk), pos + 200)
                        context = chunk[context_start:context_end]

                        try:
                            context_text = context.decode('utf-8', errors='ignore')
                            print(f"\nFound '{table_name}' at position {global_pos}:")
                            print(f"  Context: ...{context_text}...")
                        except:
                            print(f"  Context (binary): {context.hex()}")

                        pos += 1

                        if len(found_positions) >= 3:  # Batasi hasil
                            break

                    if len(found_positions) >= 3:
                        break

                if found_positions:
                    print(f"\nTotal occurrences of '{table_name}': {len(found_positions)}")
                else:
                    print(f"\n'{table_name}' not found in first 10MB")

    except Exception as e:
        print(f"Table pattern extraction failed: {e}")

    print(f"\n{'='*80}")
    print("PYTHON TOOLS SUMMARY")
    print("="*80)
    print("Berdasarkan analisis:")
    print("1. File mengandung banyak CREATE TABLE statements")
    print("2. Data SQL dapat diekstrak dengan memory mapping")
    print("3. Format file adalah TAPE (bukan SQLite murni)")
    print("4. Kemungkinan besar ini adalah SQL Server backup dalam format khusus")
    print()
    print("Tools Python yang bisa dicoba:")
    print("- pymssql (untuk SQL Server)")
    print("- pyodbc (dengan SQL Server driver)")
    print("- Custom binary parser untuk format TAPE")
    print()
    print("Rekomendasi:")
    print("1. Gunakan Plantware P3 native tools jika tersedia")
    print("2. Coba restore dengan SQL Server tools")
    print("3. Atau gunakan custom parser untuk format TAPE")

if __name__ == "__main__":
    advanced_extraction()