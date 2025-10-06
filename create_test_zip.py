#!/usr/bin/env python3
"""
Create a test ZIP file for testing the PDF report system
"""

import zipfile
import os
import tempfile
from datetime import datetime

def create_test_zip():
    """Create a test ZIP file with sample content"""
    zip_filename = "TestBackup.zip"
    
    # Create temporary files to add to ZIP
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create sample files
        files_to_add = []
        
        # Create a sample text file
        txt_file = os.path.join(temp_dir, "sample.txt")
        with open(txt_file, 'w') as f:
            f.write("This is a sample text file for testing.\n")
            f.write(f"Created on: {datetime.now()}\n")
        files_to_add.append(("sample.txt", txt_file))
        
        # Create a sample BAK file (simulated)
        bak_file = os.path.join(temp_dir, "database_backup.bak")
        with open(bak_file, 'wb') as f:
            # Write a simple header that looks like a BAK file
            f.write(b"TAPE\x00\x00\x00\x00")  # Simple BAK header simulation
            f.write(b"Sample database backup content for testing purposes.\n" * 100)
        files_to_add.append(("database_backup.bak", bak_file))
        
        # Create another sample file
        log_file = os.path.join(temp_dir, "backup.log")
        with open(log_file, 'w') as f:
            f.write("Backup Log\n")
            f.write("==========\n")
            f.write(f"Backup started: {datetime.now()}\n")
            f.write("Status: Completed successfully\n")
        files_to_add.append(("backup.log", log_file))
        
        # Create the ZIP file
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zf:
            for arc_name, file_path in files_to_add:
                zf.write(file_path, arc_name)
                print(f"Added {arc_name} to ZIP")
    
    # Verify the ZIP file
    if os.path.exists(zip_filename):
        size = os.path.getsize(zip_filename)
        print(f"\nTest ZIP file created successfully!")
        print(f"File: {zip_filename}")
        print(f"Size: {size} bytes")
        
        # List contents
        with zipfile.ZipFile(zip_filename, 'r') as zf:
            print(f"Contents: {len(zf.infolist())} files")
            for info in zf.infolist():
                print(f"  - {info.filename} ({info.file_size} bytes)")
        
        return zip_filename
    else:
        print("Failed to create test ZIP file")
        return None

if __name__ == "__main__":
    create_test_zip()