#!/usr/bin/env python3
"""
Demo BAK File Reader - Simple Demonstration
Demonstrasi singkat kemampuan BAK file reader
"""

import sys
import os
sys.path.append('src')

from bak_file_reader import BAKFileReader

def demo_bak_reader():
    """Demo singkat BAK file reader"""
    print("=" * 80)
    print("BAK FILE READER - DEMONSTRATION")
    print("=" * 80)
    print()

    print("Fitur-fitur BAK File Reader:")
    print("[OK] Membaca file .bak langsung atau dari dalam ZIP")
    print("[OK] Ekstrak ke folder yang sama dengan file ZIP")
    print("[OK] Hapus otomatis file hasil ekstrak setelah dibaca")
    print("[OK] Deteksi berbagai format database (SQLite, TAPE, dll)")
    print("[OK] GUI dengan 3 tab: Summary, Tables, Query")
    print("[OK] Drag and drop support")
    print("[OK] SQL query execution langsung dari backup")
    print()

    # Test dengan file kecil
    backup_dir = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup"
    test_files = []

    if os.path.exists(backup_dir):
        for file in os.listdir(backup_dir):
            if file.endswith('.zip'):
                file_path = os.path.join(backup_dir, file)
                file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                test_files.append((file_path, file_size_mb))

    if test_files:
        print("File backup yang tersedia:")
        for file_path, size_mb in test_files:
            print(f"  - {os.path.basename(file_path)}: {size_mb:.1f} MB")

        # Test dengan file terkecil
        smallest_file = min(test_files, key=lambda x: x[1])
        test_file, size_mb = smallest_file

        print(f"\nTesting dengan file terkecil: {os.path.basename(test_file)}")
        print(f"Size: {size_mb:.1f} MB")

        reader = BAKFileReader()
        try:
            result = reader.read_bak_file(test_file, extract_to_same_folder=True)

            print(f"\nHasil:")
            print(f"  Success: {'YES' if result['success'] else 'NO'}")
            print(f"  File Type: {result['file_type']}")

            if result.get('zip_info'):
                print(f"  File dalam ZIP: {result['zip_info'].get('bak_file', 'N/A')}")

            if result.get('cleanup_note'):
                print(f"  Cleanup: {result['cleanup_note']}")

            # Verifikasi cleanup
            extracted_files = []
            for file in os.listdir(backup_dir):
                full_path = os.path.join(backup_dir, file)
                if os.path.isfile(full_path) and not file.endswith('.zip'):
                    extracted_files.append(file)

            if extracted_files:
                print(f"  Warning: File ekstrak tersisa: {extracted_files}")
            else:
                print(f"  [OK] Cleanup berhasil: tidak ada file tersisa")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            reader.cleanup()
    else:
        print("Tidak ditemukan file backup untuk diuji")

    print()
    print("=" * 80)
    print("Cara menggunakan BAK File Reader:")
    print("1. GUI: python bak_file_reader_gui.py")
    print("2. Command line: python demo_bak_reader.py")
    print("3. Di integrated GUI: akan segera tersedia")
    print("=" * 80)

if __name__ == "__main__":
    demo_bak_reader()