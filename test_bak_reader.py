#!/usr/bin/env python3
"""
Test BAK File Reader - Demonstration Script
Menunjukkan kemampuan BAK file reader yang telah dibuat
"""

import sys
import os
sys.path.append('src')

from bak_file_reader import BAKFileReader

def test_bak_reader():
    """Test BAK file reader dengan backup files yang tersedia"""
    print("=" * 80)
    print("BAK FILE READER - DEMONSTRATION")
    print("=" * 80)

    # Cari file backup yang tersedia
    backup_dir = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup"
    test_files = []

    if os.path.exists(backup_dir):
        for file in os.listdir(backup_dir):
            if file.endswith('.zip'):
                test_files.append(os.path.join(backup_dir, file))

    if not test_files:
        print("Tidak ditemukan file backup ZIP untuk diuji")
        return

    reader = BAKFileReader()

    for i, test_file in enumerate(test_files[:3], 1):  # Test max 3 files
        print(f"\n{'='*60}")
        print(f"TEST #{i}: {os.path.basename(test_file)}")
        print('='*60)

        try:
            # Test file size
            file_size_mb = os.path.getsize(test_file) / (1024 * 1024)
            print(f"File size: {file_size_mb:.2f} MB")

            # Baca file BAK
            print("\nReading BAK file...")
            result = reader.read_bak_file(test_file, extract_to_same_folder=True)

            # Tampilkan hasil
            print(f"\nResults:")
            print(f"  Success: {'YES' if result['success'] else 'NO'}")
            print(f"  File Type: {result['file_type']}")

            if result.get('zip_info'):
                print(f"  ZIP Info:")
                print(f"    BAK File: {result['zip_info'].get('bak_file', 'N/A')}")
                print(f"    Total Files: {result['zip_info'].get('total_files', 0)}")
                if result.get('cleanup_note'):
                    print(f"    Cleanup: {result['cleanup_note']}")

            if result.get('database_info'):
                db_info = result['database_info']
                print(f"  Database Info:")
                print(f"    Detected Type: {db_info.get('detected_type', 'Unknown')}")
                print(f"    Tables: {db_info.get('table_count', 0)}")

                if 'page_size' in db_info:
                    print(f"    Page Size: {db_info['page_size']:,} bytes")
                    print(f"    Total Size: {db_info['total_size']:,} bytes")

            if result.get('tables'):
                print(f"  Tables Found:")
                for table_name, table_info in result['tables'].items():
                    print(f"    - {table_name}: {table_info.get('record_count', 0):,} records")

            if result.get('errors'):
                print(f"  Errors:")
                for error in result['errors'][:3]:  # Show first 3 errors
                    print(f"    * {error}")

            if result.get('warnings'):
                print(f"  Warnings:")
                for warning in result['warnings'][:3]:  # Show first 3 warnings
                    print(f"    * {warning}")

        except Exception as e:
            print(f"Error testing {test_file}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*80}")
    print("TEST COMPLETED")
    print("="*80)

    # Cleanup
    reader.cleanup()

if __name__ == "__main__":
    test_bak_reader()