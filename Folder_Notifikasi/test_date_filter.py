#!/usr/bin/env python3
"""
Test date filtering logic
"""

import os
from datetime import datetime

def test_date_filtering():
    backup_path = "D:/Gawean Rebinmas/App_Auto_Backup/Backup"

    # Get all ZIP files
    zip_files = []
    for root, dirs, files in os.walk(backup_path):
        for file in files:
            if file.lower().endswith('.zip'):
                zip_files.append(os.path.join(root, file))

    print(f"Found {len(zip_files)} ZIP files:")
    for file in zip_files:
        mod_time = os.path.getmtime(file)
        file_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d')
        file_size = os.path.getsize(file)
        print(f"  {os.path.basename(file)} - Date: {file_date} - Size: {file_size:,} bytes")

    # Find latest date
    if zip_files:
        latest_time = 0
        latest_file = ""
        for file in zip_files:
            mod_time = os.path.getmtime(file)
            if mod_time > latest_time:
                latest_time = mod_time
                latest_file = file

        latest_date = datetime.fromtimestamp(latest_time).strftime('%Y-%m-%d')
        print(f"\nLatest date: {latest_date}")
        print(f"Latest file: {os.path.basename(latest_file)}")

        # Filter files by latest date
        filtered_files = [f for f in zip_files if datetime.fromtimestamp(os.path.getmtime(f)).strftime('%Y-%m-%d') == latest_date]
        print(f"\nFiles for latest date ({latest_date}): {len(filtered_files)}")
        for file in filtered_files:
            print(f"  {os.path.basename(file)}")
    else:
        print("No ZIP files found")

if __name__ == "__main__":
    test_date_filtering()