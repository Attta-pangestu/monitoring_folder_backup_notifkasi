#!/usr/bin/env python3
"""
Test script untuk enhanced database validator dengan file kecil
"""

import sys
import os
sys.path.append('src')

from enhanced_database_validator import EnhancedDatabaseValidator

def test_with_tape_file():
    """Test dengan file tape format"""
    validator = EnhancedDatabaseValidator()

    # Test dengan file yang lebih kecil dulu
    test_files = [
        r"D:\Gawean Rebinmas\App_Auto_Backup\Backup\BackupVenuz 2025-10-04 10;17;35.zip",
        r"D:\Gawean Rebinmas\App_Auto_Backup\Backup\PlantwareP3 2025-10-04 11;33;53.zip"
    ]

    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n{'='*60}")
            print(f"Testing with: {test_file}")
            print(f"File size: {os.path.getsize(test_file) / (1024*1024):.2f} MB")
            print('='*60)

            try:
                # Test ZIP integrity check dulu
                integrity = validator._check_zip_integrity(test_file)
                print(f"ZIP Integrity: {'VALID' if integrity['is_valid'] else 'CORRUPTED'}")
                print(f"Files in ZIP: {integrity['file_count']}")

                # Test file detection
                import zipfile
                with zipfile.ZipFile(test_file, 'r') as zip_ref:
                    files = zip_ref.namelist()
                    print(f"Files found: {files}")

                    # Test database file detection
                    db_files = validator._find_database_files(zip_ref)
                    print(f"Database files detected: {db_files}")

                    if db_files:
                        # Test dengan file pertama (hanya baca header)
                        for db_file in db_files[:1]:  # Cuma file pertama saja
                            print(f"\nAnalyzing: {db_file}")
                            try:
                                # Ekstrak hanya header untuk testing
                                with zip_ref.open(db_file) as f:
                                    header = f.read(64)
                                    print(f"Header: {header.hex()[:32]}...")

                                    if header.startswith(b'TAPE'):
                                        print("Detected: TAPE format")
                                        # Coba tape analysis
                                        with zipfile.ZipFile(test_file, 'r') as zip_ref_test:
                                            import tempfile
                                            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                                                # Hanya baca 1MB pertama untuk testing
                                                with zip_ref_test.open(db_file) as source:
                                                    temp_file.write(source.read(1024*1024))
                                                temp_file_path = temp_file.name

                                            try:
                                                tape_analysis = validator.tape_analyzer.analyze_tape_file(temp_file_path, db_file)
                                                print(f"Tape analysis result:")
                                                print(f"  Format: {tape_analysis['file_format']}")
                                                print(f"  Size: {tape_analysis['file_size_mb']:.2f} MB")
                                                if tape_analysis.get('date_info'):
                                                    print(f"  Date info: {tape_analysis['date_info']}")
                                                if tape_analysis.get('estimated_records'):
                                                    print(f"  Estimated records: {tape_analysis['estimated_records']:,}")
                                            finally:
                                                os.unlink(temp_file_path)

                            except Exception as e:
                                print(f"Error analyzing {db_file}: {e}")

            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()

        else:
            print(f"File not found: {test_file}")

if __name__ == "__main__":
    test_with_tape_file()