#!/usr/bin/env python3
"""
Script khusus untuk membaca isi tabel dari file PlantwareP3.bak
Path: D:\Gawean Rebinmas\App_Auto_Backup\Backup\PlantwareP3
"""

import sys
import os
import struct
import sqlite3
import tempfile
from pathlib import Path

sys.path.append('src')
from bak_file_reader import BAKFileReader

def read_plantware_bak():
    """Membaca file PlantwareP3.bak dengan berbagai metode"""
    print("=" * 80)
    print("READING PLANTWAREP3.BAK")
    print("=" * 80)
    print()

    bak_path = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup\PlantwareP3"

    if not os.path.exists(bak_path):
        print(f"❌ File not found: {bak_path}")
        return

    print(f"📁 File: {bak_path}")
    print(f"📏 Size: {os.path.getsize(bak_path) / (1024*1024*1024):.2f} GB")

    # Metode 1: Coba sebagai SQLite langsung
    print(f"\n{'='*50}")
    print("METHOD 1: Direct SQLite Access")
    print('='*50)
    try:
        conn = sqlite3.connect(bak_path)
        cursor = conn.cursor()

        # Get table list
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()

        if tables:
            print(f"✅ Success! Found {len(tables)} tables:")
            for table in tables:
                table_name = table[0]
                print(f"\n📋 Table: {table_name}")

                # Get table structure
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                print(f"   Columns: {[col[1] for col in columns]}")

                # Get record count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   Records: {count:,}")

                # Get sample data
                if count > 0:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                    sample_data = cursor.fetchall()
                    print(f"   Sample Data:")
                    for i, row in enumerate(sample_data):
                        print(f"      Row {i+1}: {row}")
        else:
            print("❌ No tables found")

        conn.close()

    except sqlite3.Error as e:
        print(f"❌ SQLite Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Metode 2: Coba dengan BAK File Reader
    print(f"\n{'='*50}")
    print("METHOD 2: BAK File Reader")
    print('='*50)
    try:
        reader = BAKFileReader()
        result = reader.read_bak_file(bak_path)

        if result['success']:
            print("✅ BAK File Reader Success!")
            print(f"File Type: {result['file_type']}")

            if result.get('tables'):
                print(f"\n📊 Tables Found: {len(result['tables'])}")
                for table_name, table_info in result['tables'].items():
                    print(f"\n📋 Table: {table_name}")
                    print(f"   Records: {table_info.get('record_count', 0):,}")
                    print(f"   Columns: {len(table_info.get('columns', []))}")

                    if table_info.get('columns'):
                        col_names = [col[1] for col in table_info['columns'][:10]]
                        print(f"   Column Names: {col_names}")

                    if table_info.get('sample_data'):
                        print(f"   Sample: {table_info['sample_data'][0] if table_info['sample_data'] else 'None'}")
            else:
                print("❌ No tables found")
        else:
            print("❌ BAK File Reader Failed")
            if result.get('errors'):
                for error in result['errors']:
                    print(f"   Error: {error}")

        reader.cleanup()

    except Exception as e:
        print(f"❌ BAK File Reader Error: {e}")

    # Metode 3: Analisis header dan structure
    print(f"\n{'='*50}")
    print("METHOD 3: Header Analysis")
    print('='*50)
    try:
        with open(bak_path, 'rb') as f:
            # Baca header
            header = f.read(64)
            print(f"Header (hex): {header.hex()}")
            print(f"Header (text): {header}")

            # Cek signature
            if header.startswith(b'SQLite format 3'):
                print("✅ SQLite format detected")
            elif header.startswith(b'TAPE'):
                print("📼 TAPE format detected")

                # Coba parse TAPE header
                if len(header) >= 16:
                    print(f"TAPE Version: {header[4:8].hex()}")
                    print(f"Flags: {header[8:12].hex()}")
                    print(f"Timestamp: {header[12:16].hex()}")

            else:
                print("❓ Unknown format")

            # Cari string yang mungkin nama tabel
            print(f"\n🔍 Searching for table names...")
            f.seek(0)
            data = f.read(1024 * 1024)  # Baca 1MB pertama

            # String yang mungkin nama tabel (berdasarkan dokumentasi)
            possible_tables = ['PR_TASKREG', 'TA_MACHINE', 'GWSCANNER', 'PR_USER', 'PR_PROJECT']

            for table in possible_tables:
                if table.encode('utf-8') in data:
                    pos = data.find(table.encode('utf-8'))
                    print(f"✅ Found '{table}' at position {pos}")

                    # Tampilkan konteks sekitar
                    start = max(0, pos - 50)
                    end = min(len(data), pos + 100)
                    context = data[start:end]
                    print(f"   Context: {context}")

    except Exception as e:
        print(f"❌ Header analysis error: {e}")

    # Metode 4: Coba cari struktur database dengan pendekatan berbeda
    print(f"\n{'='*50}")
    print("METHOD 4: Binary Structure Analysis")
    print('='*50)
    try:
        # Coba cari pattern yang menunjukkan struktur tabel
        with open(bak_path, 'rb') as f:
            # Baca beberapa bagian file untuk mencari pattern
            chunk_size = 1024 * 1024  # 1MB
            chunks_to_read = 5

            for i in range(chunks_to_read):
                f.seek(i * chunk_size)
                chunk = f.read(chunk_size)

                # Cari pattern CREATE TABLE
                create_table_pos = chunk.find(b'CREATE TABLE')
                if create_table_pos != -1:
                    print(f"✅ Found CREATE TABLE at chunk {i}, position {create_table_pos}")

                    # Ekstrak beberapa karakter setelah CREATE TABLE
                    table_def_start = create_table_pos
                    table_def_end = chunk.find(b';', table_def_start)
                    if table_def_end != -1:
                        table_def = chunk[table_def_start:table_def_end + 1]
                        print(f"   Table definition: {table_def[:200]}...")

                # Cari nama tabel spesifik
                table_names = [b'PR_TASKREG', b'TA_MACHINE', b'GWSCANNER']
                for table_name in table_names:
                    pos = chunk.find(table_name)
                    if pos != -1:
                        print(f"✅ Found {table_name.decode()} at chunk {i}, position {pos}")

    except Exception as e:
        print(f"❌ Binary analysis error: {e}")

    print(f"\n{'='*80}")
    print("SUMMARY")
    print("="*80)
    print("Jika file menggunakan TAPE format:")
    print("- Tidak bisa dibaca langsung dengan SQLite")
    print("- Butuh parser khusus untuk format Plantware P3")
    print("- Informasi tabel mungkin ada tapi terenkripsi/dikompresi")
    print()
    print("Jika Anda punya akses ke:")
    print("- Plantware P3 software")
    print("- Database restore tools")
    print("- Conversion utilities")
    print("...mungkin bisa convert ke SQLite untuk dibaca")

if __name__ == "__main__":
    read_plantware_bak()