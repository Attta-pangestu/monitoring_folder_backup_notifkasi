#!/usr/bin/env python3
"""
Test the full process: scan, filter, and analyze files
"""

import os
import sys
import zipfile
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_zip_analysis():
    backup_path = "D:/Gawean Rebinmas/App_Auto_Backup/Backup"

    # Step 1: Find ZIP files
    zip_files = []
    for root, dirs, files in os.walk(backup_path):
        for file in files:
            if file.lower().endswith('.zip'):
                zip_files.append(os.path.join(root, file))

    print(f"Found {len(zip_files)} ZIP files")

    # Step 2: Get latest date
    latest_time = 0
    for file in zip_files:
        mod_time = os.path.getmtime(file)
        if mod_time > latest_time:
            latest_time = mod_time

    latest_date = datetime.fromtimestamp(latest_time).strftime('%Y-%m-%d')
    print(f"Latest date: {latest_date}")

    # Step 3: Filter files by latest date
    filtered_files = [f for f in zip_files if datetime.fromtimestamp(os.path.getmtime(f)).strftime('%Y-%m-%d') == latest_date]
    print(f"Files for latest date: {len(filtered_files)}")

    # Step 4: Analyze each file
    for i, file_path in enumerate(filtered_files):
        print(f"\nAnalyzing ({i+1}/{len(filtered_files)}): {os.path.basename(file_path)}")

        try:
            # Basic file info
            stat_info = os.stat(file_path)
            file_info = {
                'path': file_path,
                'size': stat_info.st_size,
                'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                'status': 'Menunggu',
                'extractable': False,
                'corrupt': False
            }

            print(f"  Size: {file_info['size']:,} bytes")
            print(f"  Modified: {file_info['modified']}")

            # Analyze ZIP file
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Test integrity
                bad_file = zip_ref.testzip()
                if bad_file:
                    file_info['corrupt'] = True
                    file_info['status'] = 'Corrupt'
                    print(f"  Status: CORRUPT - {bad_file}")
                    continue

                # Get file list
                file_list = zip_ref.namelist()
                print(f"  Files in ZIP: {len(file_list)}")

                # Look for BAK files
                bak_files = []
                for file in file_list:
                    if file.lower().endswith('.bak'):
                        bak_files.append(file)

                print(f"  BAK files found: {len(bak_files)}")
                for bak_file in bak_files:
                    print(f"    - {bak_file}")

                file_info['extractable'] = True
                file_info['status'] = 'Valid'
                print(f"  Status: Valid")

        except Exception as e:
            file_info['corrupt'] = True
            file_info['status'] = f'Error: {str(e)}'
            print(f"  Status: ERROR - {str(e)}")

if __name__ == "__main__":
    test_zip_analysis()