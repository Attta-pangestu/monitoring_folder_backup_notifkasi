#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Test untuk Simple Backup Monitor
Menguji fungsi utama tanpa GUI
"""

import os
import sys
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_zip_analyzer import EnhancedZIPAnalyzer
from enhanced_bak_analyzer import EnhancedBAKAnalyzer
from enhanced_email_notifier import EnhancedEmailNotifier

def test_simple_backup_functionality():
    """Test simple backup functionality"""
    print("Simple Backup Monitor Test")
    print("=" * 60)

    # Initialize analyzers
    zip_analyzer = EnhancedZIPAnalyzer()
    bak_analyzer = EnhancedBAKAnalyzer()
    email_notifier = EnhancedEmailNotifier()

    # Test folder
    test_folder = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup"

    if not os.path.exists(test_folder):
        print(f"Test folder not found: {test_folder}")
        return

    # Find ZIP files
    zip_files = []
    for file in os.listdir(test_folder):
        if file.lower().endswith('.zip'):
            zip_files.append(os.path.join(test_folder, file))

    if not zip_files:
        print("No ZIP files found")
        return

    print(f"Found {len(zip_files)} ZIP files")

    # Analyze first ZIP file
    test_zip = zip_files[0]
    print(f"Testing: {os.path.basename(test_zip)}")

    try:
        # Analyze ZIP
        zip_analysis = zip_analyzer.analyze_zip_comprehensive(test_zip)
        zip_analysis['file_path'] = test_zip

        print(f"ZIP Analysis Success")
        print(f"   Backup Date: {zip_analysis.get('zip_info', {}).get('backup_date_from_filename', 'Unknown')}")
        print(f"   Size: {zip_analysis.get('zip_info', {}).get('file_size_mb', 0):.2f} MB")

        # Test email report generation
        print("\nTesting Email Report...")

        # Create test analysis results for email
        test_results = [zip_analysis]

        # Test email sending
        success, message = email_notifier.send_auto_analysis_report(test_results)

        if success:
            print("Email test successful")
            print(f"   Message: {message}")
        else:
            print("Email test failed")
            print(f"   Error: {message}")

        print("\n" + "=" * 60)
        print("Simple Backup Monitor Test Completed")

    except Exception as e:
        print(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_backup_functionality()