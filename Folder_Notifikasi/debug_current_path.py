#!/usr/bin/env python3
"""
Debug current path issue
"""

import os
from datetime import datetime

def debug_path():
    # Test the exact path the user mentioned
    test_path = "D:/Gawean Rebinmas/App_Auto_Backup/Backup"

    print(f"Testing path: {test_path}")
    print(f"Path exists: {os.path.exists(test_path)}")

    if os.path.exists(test_path):
        print(f"Path is directory: {os.path.isdir(test_path)}")

        # List all files
        all_files = []
        for root, dirs, files in os.walk(test_path):
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append(file_path)

        print(f"Total files found: {len(all_files)}")

        # Filter ZIP files
        zip_files = [f for f in all_files if f.lower().endswith('.zip')]
        print(f"ZIP files found: {len(zip_files)}")

        if zip_files:
            print("\nZIP files details:")
            for zip_file in zip_files:
                mod_time = os.path.getmtime(zip_file)
                mod_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d')
                size = os.path.getsize(zip_file)
                print(f"  {os.path.basename(zip_file)}")
                print(f"    Date: {mod_date}")
                print(f"    Size: {size:,} bytes")

            # Find latest date
            latest_time = max(os.path.getmtime(f) for f in zip_files)
            latest_date = datetime.fromtimestamp(latest_time).strftime('%Y-%m-%d')
            print(f"\nLatest date among ZIPs: {latest_date}")

            # Filter by latest date
            latest_files = [f for f in zip_files
                           if datetime.fromtimestamp(os.path.getmtime(f)).strftime('%Y-%m-%d') == latest_date]
            print(f"Files for latest date: {len(latest_files)}")
        else:
            print("No ZIP files found in the directory")

        # Show all file types
        file_types = {}
        for file in all_files:
            ext = os.path.splitext(file)[1].lower()
            file_types[ext] = file_types.get(ext, 0) + 1

        print(f"\nFile types found: {file_types}")

    else:
        print("Path does not exist!")

if __name__ == "__main__":
    debug_path()