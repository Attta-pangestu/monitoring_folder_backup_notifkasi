#!/usr/bin/env python3
"""
Debug script to test the backup analysis functionality
"""

import os
import sys
import traceback

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zip_backup_monitor_fixed import ZipBackupMonitor

def test_backup_analysis():
    """Test backup analysis functionality"""
    print("Testing backup analysis...")

    # Test with a dummy file path
    test_file = "test_dummy.bak"

    # Create a dummy class instance
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()  # Hide the GUI

    try:
        monitor = ZipBackupMonitor(root)

        # Test method calls one by one
        print("Testing detect_backup_type_from_filename...")
        result = monitor.detect_backup_type_from_filename("BackupStaging_test.bak")
        print(f"Result: {result}")

        print("Testing generate_bak_checklist...")
        result = monitor.generate_bak_checklist(test_file, "BackupStaging", {})
        print(f"Result: {result}")

        print("Testing analyze_backup_file_header...")
        # Create a dummy file for testing
        with open(test_file, 'wb') as f:
            f.write(b"dummy backup file content")

        result = monitor.analyze_backup_file_header(test_file)
        print(f"Result: {result}")

        print("Testing analyze_staging_backup...")
        result = monitor.analyze_staging_backup(test_file, {})
        print(f"Result: {result}")

    except Exception as e:
        print(f"Error: {e}")
        print("Traceback:")
        traceback.print_exc()
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)
        root.destroy()

if __name__ == "__main__":
    test_backup_analysis()