#!/usr/bin/env python3
"""
Simple test to check ZIP files
"""

import os
import zipfile
from datetime import datetime

def test_simple():
    backup_path = "D:/Gawean Rebinmas/App_Auto_Backup/Backup"

    # Get all ZIP files
    zip_files = []
    for root, dirs, files in os.walk(backup_path):
        for file in files:
            if file.lower().endswith('.zip'):
                zip_files.append(os.path.join(root, file))

    print(f"Found {len(zip_files)} ZIP files")

    # Test each ZIP file
    for file_path in zip_files:
        print(f"\nTesting: {os.path.basename(file_path)}")

        try:
            # Basic file info
            stat_info = os.stat(file_path)
            print(f"  Size: {stat_info.st_size:,} bytes")
            print(f"  Modified: {datetime.fromtimestamp(stat_info.st_mtime)}")

            # Test ZIP file opening
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Get file list
                file_list = zip_ref.namelist()
                print(f"  Files in ZIP: {len(file_list)}")

                # Show first few files
                for i, file in enumerate(file_list[:5]):
                    print(f"    {i+1}. {file}")

                if len(file_list) > 5:
                    print(f"    ... and {len(file_list) - 5} more files")

                # Look for BAK files
                bak_files = [f for f in file_list if f.lower().endswith('.bak')]
                print(f"  BAK files: {len(bak_files)}")
                for bak_file in bak_files:
                    print(f"    - {bak_file}")

        except Exception as e:
            print(f"  ERROR: {str(e)}")

if __name__ == "__main__":
    test_simple()