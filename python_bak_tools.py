#!/usr/bin/env python3
"""
Python Tools untuk BAK File Analysis (tanpa emoji)
"""

import sys
import os
import struct
import sqlite3
import pandas as pd
from pathlib import Path

def analyze_with_python_tools():
    """Analisis BAK file dengan berbagai Python tools"""
    print("=" * 80)
    print("PYTHON TOOLS FOR BAK FILE ANALYSIS")
    print("=" * 80)
    print()

    bak_path = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup\PlantwareP3"

    if not os.path.exists(bak_path):
        print(f"File not found: {bak_path}")
        return

    print(f"File: {bak_path}")
    print(f"Size: {os.path.getsize(bak_path) / (1024*1024*1024):.2f} GB")

    # Metode 1: SQLAlchemy
    print(f"\n{'='*50}")
    print("METHOD 1: SQLAlchemy")
    print('='*50)
    try:
        from sqlalchemy import create_engine, text
        # Coba dengan SQLite
        engine = create_engine(f"sqlite:///{bak_path}")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = result.fetchall()
            print(f"SUCCESS: SQLAlchemy found {len(tables)} tables")
            for table in tables[:5]:  # Show first 5
                print(f"  - {table[0]}")
            if len(tables) > 5:
                print(f"  ... and {len(tables) - 5} more tables")
    except Exception as e:
        print(f"SQLAlchemy Failed: {e}")

    # Metode 2: Pandas + SQLAlchemy
    print(f"\n{'='*50}")
    print("METHOD 2: Pandas with SQLAlchemy")
    print('='*50)
    try:
        from sqlalchemy import create_engine
        engine = create_engine(f"sqlite:///{bak_path}")
        # Coba baca tabel
        tables_df = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", engine)
        print(f"SUCCESS: Pandas found {len(tables_df)} tables")
        print(f"Tables: {tables_df['name'].tolist()[:5]}")
    except Exception as e:
        print(f"Pandas + SQLAlchemy Failed: {e}")

    # Metode 3: Coba apakah ini SQL Server backup
    print(f"\n{'='*50}")
    print("METHOD 3: SQL Server Backup Detection")
    print('='*50)
    try:
        with open(bak_path, 'rb') as f:
            header = f.read(100)
            if b'Microsoft' in header or b'SQL Server' in header:
                print("DETECTED: SQL Server backup format")
            elif header.startswith(b'TAPE'):
                print("DETECTED: TAPE format (not SQL Server)")
            else:
                print("NOT: SQL Server backup format")
    except Exception as e:
        print(f"SQL Server check failed: {e}")

    # Metode 4: Coba apakah ini PostgreSQL backup
    print(f"\n{'='*50}")
    print("METHOD 4: PostgreSQL Backup Detection")
    print('='*50)
    try:
        with open(bak_path, 'rb') as f:
            header = f.read(100)
            if b'PGDMP' in header:
                print("DETECTED: PostgreSQL dump format")
            else:
                print("NOT: PostgreSQL backup format")
    except Exception as e:
        print(f"PostgreSQL check failed: {e}")

    # Metode 5: Coba apakah ini MySQL backup
    print(f"\n{'='*50}")
    print("METHOD 5: MySQL Backup Detection")
    print('='*50)
    try:
        with open(bak_path, 'rb') as f:
            header = f.read(100)
            if b'MySQL' in header or b'mysqldump' in header:
                print("DETECTED: MySQL backup format")
            else:
                print("NOT: MySQL backup format")
    except Exception as e:
        print(f"MySQL check failed: {e}")

    # Metode 6: Coba baca sebagai text file
    print(f"\n{'='*50}")
    print("METHOD 6: Text File Analysis")
    print('='*50)
    try:
        with open(bak_path, 'r', encoding='utf-8', errors='ignore') as f:
            sample = f.read(1000)
            if 'CREATE TABLE' in sample or 'INSERT INTO' in sample:
                print("DETECTED: SQL text format")
                # Cari CREATE TABLE statements
                import re
                create_matches = re.findall(r'CREATE\s+TABLE\s+(\w+)', sample, re.IGNORECASE)
                if create_matches:
                    print(f"Found tables: {create_matches}")
            else:
                print("NOT: SQL text format")
    except Exception as e:
        print(f"Text read failed: {e}")

    # Metode 7: Binary pattern analysis
    print(f"\n{'='*50}")
    print("METHOD 7: Binary Pattern Analysis")
    print('='*50)
    try:
        with open(bak_path, 'rb') as f:
            # Baca beberapa bagian
            f.seek(0)
            data = f.read(1024 * 1024)  # 1MB pertama

            # Cari string SQL dengan encoding detection
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    text = data.decode(encoding, errors='ignore')
                    if 'CREATE TABLE' in text:
                        print(f"DETECTED: SQL data in {encoding} encoding")

                        # Cari semua CREATE TABLE
                        import re
                        create_pattern = r'CREATE\s+TABLE\s+([#\w_]+)'
                        matches = re.findall(create_pattern, text, re.IGNORECASE)
                        if matches:
                            print(f"Found {len(matches)} CREATE TABLE statements:")
                            for match in matches[:10]:
                                print(f"  - {match}")
                        break
                except:
                    continue
            else:
                print("NOT: No SQL data found in common encodings")

    except Exception as e:
        print(f"Binary analysis failed: {e}")

    # Metode 8: Coba database connection dengan timeout
    print(f"\n{'='*50}")
    print("METHOD 8: Database Connection Variations")
    print('='*50)
    try:
        # Coba dengan berbagai SQLite connection parameters
        import sqlite3

        # Standard connection
        try:
            conn = sqlite3.connect(bak_path, timeout=30.0)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"SUCCESS: Standard SQLite connection - {len(tables)} tables")
            conn.close()
        except:
            print("FAILED: Standard SQLite connection")

        # Read-only connection
        try:
            conn = sqlite3.connect(f"file:{bak_path}?mode=ro", uri=True, timeout=30.0)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"SUCCESS: Read-only connection - {len(tables)} tables")
            conn.close()
        except:
            print("FAILED: Read-only connection")

    except Exception as e:
        print(f"Connection variations failed: {e}")

    # Metode 9: Coba dengan different SQLite page size
    print(f"\n{'='*50}")
    print("METHOD 9: Alternative SQLite Parameters")
    print('='*50)
    try:
        # Coba dengan pragma settings
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        # Attach database
        cursor.execute(f"ATTACH DATABASE '{bak_path}' AS bak_db")
        try:
            cursor.execute("SELECT name FROM bak_db.sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"SUCCESS: Attached database - {len(tables)} tables")
        except:
            print("FAILED: Attached database")
        conn.close()
    except Exception as e:
        print(f"Alternative parameters failed: {e}")

    # Metode 10: Coba dengan memory mapping
    print(f"\n{'='*50}")
    print("METHOD 10: Memory Mapping Approach")
    print('='*50)
    try:
        import mmap

        with open(bak_path, 'rb') as f:
            # Memory map the file
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

            # Cari SQLite signature
            sqlite_signature = b'SQLite format 3'
            if mm.find(sqlite_signature) != -1:
                print("DETECTED: SQLite signature found in memory map")
            else:
                print("NOT: No SQLite signature found")

            # Cari CREATE TABLE
            create_table = b'CREATE TABLE'
            pos = mm.find(create_table)
            if pos != -1:
                print(f"DETECTED: CREATE TABLE found at position {pos}")
                # Tampilkan konteks
                context = mm[pos:pos+200]
                try:
                    print(f"Context: {context.decode('utf-8', errors='ignore')}")
                except:
                    print(f"Context (hex): {context.hex()}")

            mm.close()
    except Exception as e:
        print(f"Memory mapping failed: {e}")

    print(f"\n{'='*80}")
    print("ALTERNATIVE APPROACHES")
    print("="*80)
    print("Jika semua metode di atas gagal, coba:")
    print()
    print("1. Install additional tools:")
    print("   pip install mysql-connector-python")
    print("   pip install psycopg2-binary")
    print("   pip install pymssql")
    print()
    print("2. Coba database-specific tools:")
    print("   - Untuk SQL Server: sqlcmd, bcp")
    print("   - Untuk MySQL: mysql, mysqldump")
    print("   - Untuk PostgreSQL: pg_dump, psql")
    print()
    print("3. Coba file conversion tools:")
    print("   - sqlite3 command line")
    print("   - DB Browser for SQLite")
    print("   - DBeaver Universal Database Tool")
    print()
    print("4. Coba specialized backup restore tools:")
    print("   - Plantware P3 native tools")
    print("   - Third-party SQL Server restore utilities")

if __name__ == "__main__":
    analyze_with_python_tools()