#!/usr/bin/env python3
"""
Quick Database Check
Cek cepat informasi database backup
"""

import sys
import os
sys.path.append('src')

from bak_file_reader import BAKFileReader
import zipfile

def quick_database_check():
    """Cek cepat database backup"""
    print("=" * 80)
    print("QUICK DATABASE CHECK")
    print("=" * 80)
    print()

    backup_dir = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup"
    backup_files = []

    if os.path.exists(backup_dir):
        for file in os.listdir(backup_dir):
            if file.endswith('.zip'):
                backup_files.append((os.path.join(backup_dir, file), file))

    if not backup_files:
        print("No backup ZIP files found")
        return

    total_files = 0
    total_databases = 0

    for backup_file, filename in backup_files:
        print(f"\n{'='*60}")
        print(f"DATABASE CHECK: {filename}")
        print('='*60)

        total_files += 1

        try:
            # Deteksi tipe database
            db_type = "Unknown"
            if 'plantware' in filename.lower():
                db_type = "Plantware"
            elif 'venus' in filename.lower():
                db_type = "Venus"
            elif 'staging' in filename.lower():
                db_type = "Staging"

            print(f"Database Type: {db_type}")

            # Cek file di ZIP
            with zipfile.ZipFile(backup_file, 'r') as zip_ref:
                files = zip_ref.namelist()
                print(f"Files in ZIP: {files}")

                for file_in_zip in files:
                    print(f"\nAnalyzing: {file_in_zip}")

                    # Cek header
                    with zip_ref.open(file_in_zip) as f:
                        header = f.read(32)
                        print(f"Header: {header.hex()[:32]}...")

                    if header.startswith(b'SQLite format 3'):
                        print("Format: SQLite")
                        total_databases += 1
                        print("Status: Can be read with BAK File Reader")
                    elif header.startswith(b'TAPE'):
                        print("Format: TAPE (proprietary)")
                        print("Status: Format detected but cannot read content")
                    else:
                        print("Format: Unknown")
                        print("Status: Cannot read")

        except Exception as e:
            print(f"Error: {e}")

    print(f"\n{'='*80}")
    print("SUMMARY")
    print("="*80)
    print(f"Total ZIP files: {total_files}")
    print(f"Readable databases (SQLite): {total_databases}")
    print(f"TAPE format files: {total_files - total_databases}")

    print(f"\nRecommendations:")
    if total_databases > 0:
        print("- Use BAK File Reader GUI to read SQLite databases")
        print("- Browse tables and run SQL queries")
    if total_files - total_databases > 0:
        print("- TAPE format files need special parser")
        print("- Cannot read content directly")

if __name__ == "__main__":
    quick_database_check()