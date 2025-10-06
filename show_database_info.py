#!/usr/bin/env python3
"""
Show Database Information
Menampilkan informasi database backup dan daftar tabel
"""

import sys
import os
sys.path.append('src')

from bak_file_reader import BAKFileReader

def show_database_info():
    """Tampilkan informasi database dari backup files"""
    print("=" * 80)
    print("DATABASE INFORMATION - CHECK DATABASE RESULTS")
    print("=" * 80)
    print()

    # Cari backup files
    backup_dir = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup"
    backup_files = []

    if os.path.exists(backup_dir):
        for file in os.listdir(backup_dir):
            if file.endswith('.zip'):
                backup_files.append(os.path.join(backup_dir, file))

    if not backup_files:
        print("❌ Tidak ditemukan file backup ZIP di folder:")
        print(f"   {backup_dir}")
        return

    # Sort files by name
    backup_files.sort()

    reader = BAKFileReader()
    total_databases = 0

    for i, backup_file in enumerate(backup_files, 1):
        print(f"\n{'='*60}")
        print(f"DATABASE CHECK: {os.path.basename(backup_file)}")
        print('='*60)

        try:
            # Deteksi tipe database dari filename
            filename = os.path.basename(backup_file).lower()
            db_type = "Unknown"
            if 'plantware' in filename:
                db_type = "Plantware"
            elif 'venus' in filename:
                db_type = "Venus"
            elif 'staging' in filename:
                db_type = "Staging"

            print(f"📊 Database Type: {db_type}")
            print(f"📁 File: {backup_file}")

            # Baca file backup
            print(f"\n🔍 Reading database...")
            result = reader.read_bak_file(backup_file, extract_to_same_folder=True)

            if result['success']:
                total_databases += 1
                print(f"✅ Status: SUCCESS - Database readable")

                # Tampilkan informasi database
                db_info = result.get('database_info', {})
                if db_info:
                    print(f"\n📋 Database Information:")
                    print(f"   Format: {result.get('file_type', 'Unknown')}")
                    print(f"   Detected Type: {db_info.get('detected_type', 'Unknown')}")
                    print(f"   Total Tables: {db_info.get('table_count', 0)}")

                    if 'page_size' in db_info:
                        print(f"   Page Size: {db_info['page_size']:,} bytes")
                        print(f"   Total Size: {db_info['total_size']:,} bytes")

                # Tampilkan ZIP info jika ada
                if result.get('zip_info'):
                    zip_info = result['zip_info']
                    print(f"\n📦 Archive Information:")
                    print(f"   Files in ZIP: {zip_info.get('total_files', 0)}")
                    print(f"   Database File: {zip_info.get('bak_file', 'N/A')}")
                    if result.get('cleanup_note'):
                        print(f"   Cleanup: {result['cleanup_note']}")

                # Tampilkan daftar tabel
                tables = result.get('tables', {})
                if tables:
                    print(f"\n📊 Tables Found ({len(tables)} tables):")
                    for table_name, table_info in tables.items():
                        record_count = table_info.get('record_count', 0)
                        column_count = len(table_info.get('columns', []))

                        print(f"\n   📋 Table: {table_name}")
                        print(f"      📈 Records: {record_count:,}")
                        print(f"      📋 Columns: {column_count}")

                        # Tampilkan nama kolom
                        columns = table_info.get('columns', [])
                        if columns:
                            print(f"      📝 Column Names: {[col[1] for col in columns[:5]]}")
                            if len(columns) > 5:
                                print(f"                      ... (+{len(columns)-5} more columns)")

                        # Tampilkan kolom tanggal jika ada
                        date_columns = table_info.get('date_columns', [])
                        if date_columns:
                            print(f"      📅 Date Columns: {date_columns}")

                        # Tampilkan tanggal terbaru
                        latest_dates = table_info.get('latest_dates', {})
                        if latest_dates:
                            print(f"      ⏰ Latest Dates:")
                            for col, date in latest_dates.items():
                                print(f"         {col}: {date}")

                        # Tampilkan sample data jika ada
                        sample_data = table_info.get('sample_data', [])
                        if sample_data and record_count > 0:
                            print(f"      👀 Sample Data (first row): {sample_data[0]}")

                else:
                    print(f"\n⚠️  No tables found in database")

            else:
                print(f"❌ Status: FAILED - Cannot read database")
                if result.get('errors'):
                    print(f"\n❌ Errors:")
                    for error in result['errors']:
                        print(f"      • {error}")

        except Exception as e:
            print(f"❌ Error processing {backup_file}: {e}")

    print(f"\n{'='*80}")
    print("SUMMARY")
    print("="*80)
    print(f"📁 Total ZIP files processed: {len(backup_files)}")
    print(f"🗄️  Databases found: {total_databases}")
    print(f"❌ Failed to read: {len(backup_files) - total_databases}")

    if total_databases > 0:
        print(f"\n✅ Successfully analyzed {total_databases} database(s)")
        print("📋 Use BAK File Reader GUI for detailed table browsing and SQL queries")
    else:
        print(f"\n⚠️  No readable databases found")
        print("🔧 Check if backup files use supported format (SQLite/TAPE)")

    # Cleanup
    reader.cleanup()

if __name__ == "__main__":
    show_database_info()