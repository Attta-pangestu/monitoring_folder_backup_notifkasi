#!/usr/bin/env python3
"""
Coba berbagai Python tools untuk membaca file BAK
"""

import sys
import os
import struct
import sqlite3
import pandas as pd
from pathlib import Path

def try_sqlite_alternatives():
    """Coba berbagai metode untuk membaca file BAK"""
    print("=" * 80)
    print("TRYING PYTHON TOOLS FOR BAK FILE")
    print("=" * 80)
    print()

    bak_path = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup\PlantwareP3"

    if not os.path.exists(bak_path):
        print(f"File not found: {bak_path}")
        return

    print(f"File: {bak_path}")
    print(f"Size: {os.path.getsize(bak_path) / (1024*1024*1024):.2f} GB")

    # Metode 1: Coba SQLite dengan berbagai mode
    print(f"\n{'='*50}")
    print("METHOD 1: SQLite with Different Modes")
    print('='*50)
    try:
        # Coba dengan URI mode
        import urllib.parse
        uri_path = f"file:{bak_path}?mode=ro"
        conn = sqlite3.connect(uri_path, uri=True, timeout=30.0)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"✅ URI Mode Success! Tables: {tables}")
        conn.close()
    except Exception as e:
        print(f"URI Mode Failed: {e}")

    try:
        # Coba dengan timeout lebih lama
        conn = sqlite3.connect(bak_path, timeout=60.0)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"✅ Long Timeout Success! Tables: {tables}")
        conn.close()
    except Exception as e:
        print(f"Long Timeout Failed: {e}")

    # Metode 2: Coba pandas read_sqlite
    print(f"\n{'='*50}")
    print("METHOD 2: Pandas SQLite")
    print('='*50)
    try:
        # Coba baca dengan pandas
        tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'",
                                   f"sqlite:///{bak_path}")
        print(f"✅ Pandas Success! Tables: {tables}")
    except Exception as e:
        print(f"Pandas Failed: {e}")

    # Metode 3: Coba SQLAlchemy
    print(f"\n{'='*50}")
    print("METHOD 3: SQLAlchemy")
    print('='*50)
    try:
        from sqlalchemy import create_engine, text
        # Coba dengan SQLAlchemy
        engine = create_engine(f"sqlite:///{bak_path}")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = result.fetchall()
            print(f"✅ SQLAlchemy Success! Tables: {tables}")
    except ImportError:
        print("SQLAlchemy not installed")
    except Exception as e:
        print(f"SQLAlchemy Failed: {e}")

    # Metode 4: Coba apakah ini SQL Server backup
    print(f"\n{'='*50}")
    print("METHOD 4: Check if SQL Server Backup")
    print('='*50)
    try:
        with open(bak_path, 'rb') as f:
            header = f.read(100)
            if b'Microsoft' in header or b'SQL Server' in header:
                print("✅ Detected SQL Server backup format")
            else:
                print("❌ Not SQL Server backup format")
    except Exception as e:
        print(f"SQL Server check failed: {e}")

    # Metode 5: Coba apakah ini PostgreSQL backup
    print(f"\n{'='*50}")
    print("METHOD 5: Check if PostgreSQL Backup")
    print('='*50)
    try:
        with open(bak_path, 'rb') as f:
            header = f.read(100)
            if b'PGDMP' in header:
                print("✅ Detected PostgreSQL dump format")
            else:
                print("❌ Not PostgreSQL backup format")
    except Exception as e:
        print(f"PostgreSQL check failed: {e}")

    # Metode 6: Coba apakah ini MySQL backup
    print(f"\n{'='*50}")
    print("METHOD 6: Check if MySQL Backup")
    print('='*50)
    try:
        with open(bak_path, 'rb') as f:
            header = f.read(100)
            if b'MySQL' in header or b'mysqldump' in header:
                print("✅ Detected MySQL backup format")
            else:
                print("❌ Not MySQL backup format")
    except Exception as e:
        print(f"MySQL check failed: {e}")

    # Metode 7: Coba baca sebagai text file
    print(f"\n{'='*50}")
    print("METHOD 7: Read as Text File")
    print('='*50)
    try:
        with open(bak_path, 'r', encoding='utf-8', errors='ignore') as f:
            sample = f.read(1000)
            if 'CREATE TABLE' in sample or 'INSERT INTO' in sample:
                print("✅ Detected SQL text format")
                print(f"Sample: {sample[:200]}...")
            else:
                print("❌ Not SQL text format")
    except Exception as e:
        print(f"Text read failed: {e}")

    # Metode 8: Coba baca sebagai binary dengan structural analysis
    print(f"\n{'='*50}")
    print("METHOD 8: Binary Structure Analysis")
    print('='*50)
    try:
        with open(bak_path, 'rb') as f:
            # Baca beberapa bagian untuk mencari pattern
            f.seek(0)
            data = f.read(1024 * 1024)  # 1MB pertama

            # Cari string SQL
            import re
            sql_pattern = rb'CREATE\s+TABLE\s+(\w+)'
            matches = re.findall(sql_pattern, data, re.IGNORECASE)
            if matches:
                print(f"✅ Found CREATE TABLE statements: {matches}")
            else:
                print("❌ No CREATE TABLE statements found")

            # Cari INSERT statements
            insert_pattern = rb'INSERT\s+INTO\s+(\w+)'
            matches = re.findall(insert_pattern, data, re.IGNORECASE)
            if matches:
                print(f"✅ Found INSERT statements: {matches[:10]}")

    except Exception as e:
        print(f"Binary analysis failed: {e}")

    # Metode 9: Coba dengan pyodbc (jika ada)
    print(f"\n{'='*50}")
    print("METHOD 9: Try pyodbc")
    print('='*50)
    try:
        import pyodbc
        # Coba connect sebagai database
        conn_str = f"DRIVER={{SQLite3 ODBC Driver}};DATABASE={bak_path};"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"✅ pyodbc Success! Tables: {tables}")
        conn.close()
    except ImportError:
        print("pyodbc not installed")
    except Exception as e:
        print(f"pyodbc Failed: {e}")

    # Metode 10: Coba dengan aiosqlite (jika ada)
    print(f"\n{'='*50}")
    print("METHOD 10: Try aiosqlite")
    print('='*50)
    try:
        import aiosqlite
        import asyncio

        async def test_aiosqlite():
            async with aiosqlite.connect(bak_path) as db:
                async with db.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
                    tables = await cursor.fetchall()
                    return tables

        tables = asyncio.run(test_aiosqlite())
        print(f"✅ aiosqlite Success! Tables: {tables}")
    except ImportError:
        print("aiosqlite not installed")
    except Exception as e:
        print(f"aiosqlite Failed: {e}")

    print(f"\n{'='*80}")
    print("TOOL INSTALLATION RECOMMENDATIONS")
    print("="*80)
    print("Jika beberapa tools belum terinstall, install dengan:")
    print("pip install sqlalchemy")
    print("pip install pyodbc")
    print("pip install aiosqlite")
    print()
    print("Untuk SQL Server:")
    print("pip install pyodbc")
    print("Atau gunakan mssql-tools")
    print()
    print("Untuk MySQL:")
    print("pip install mysql-connector-python")
    print()
    print("Untuk PostgreSQL:")
    print("pip install psycopg2-binary")

if __name__ == "__main__":
    try_sqlite_alternatives()