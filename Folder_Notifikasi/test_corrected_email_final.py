#!/usr/bin/env python3
"""
Test script untuk memverifikasi perbaikan tanggal backup dan subject email
"""

import json
import os
from datetime import datetime
from zip_backup_monitor_enhanced import ZipBackupMonitorEnhanced
import tkinter as tk

def test_corrected_email():
    print("=== Testing Corrected Email Display ===")
    
    # Initialize monitor
    root = tk.Tk()
    root.withdraw()  # Hide the GUI
    monitor = ZipBackupMonitorEnhanced(root)
    
    # Set monitoring path
    monitor.monitoring_path.set("D:/Gawean Rebinmas/App_Auto_Backup/Backup")
    
    # Load summary data
    summary_file = "backup_summary_enhanced.json"
    if os.path.exists(summary_file):
        with open(summary_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            monitor.summary_data = data.get('zip_files', {})
            monitor.bak_summary = data.get('bak_analysis', {})
    
    print("\n1. Checking ZIP file dates:")
    for file_path, file_info in monitor.summary_data.items():
        filename = os.path.basename(file_path)
        modified_time = file_info.get('modified_time', 'Unknown')
        days_since = file_info.get('days_since_backup', 0)
        is_outdated = file_info.get('is_outdated', False)
        print(f"   {filename}: Modified={modified_time}, Days={days_since}, Outdated={is_outdated}")
    
    print("\n2. Checking BAK file dates:")
    for bak_file in monitor.bak_summary.get('bak_files', []):
        filename = bak_file.get('filename', 'Unknown')
        backup_date = bak_file.get('backup_date', 'Unknown')
        days_since = bak_file.get('days_since_backup', 0)
        is_outdated = bak_file.get('is_outdated', False)
        print(f"   {filename}: BackupDate={backup_date}, Days={days_since}, Outdated={is_outdated}")
    
    print("\n3. Testing email subject:")
    backup_status = monitor.get_overall_backup_status()
    print(f"   Overall backup status: {backup_status}")
    
    # Test subject generation logic
    if backup_status == "OUTDATED":
        status_label = "OUTDATED"
    elif backup_status == "UPDATE":
        status_label = "UPDATE"
    else:
        status_label = "VALID"
    
    subject = f"[{status_label}] Deep Analysis Report - {datetime.now().strftime('%Y-%m-%d')}"
    print(f"   Email subject: {subject}")
    
    print("\n4. Generating email template:")
    try:
        email_template = monitor.generate_deep_analysis_email_template()
        
        # Save template for inspection
        with open("test_corrected_email_template.html", "w", encoding="utf-8") as f:
            f.write(email_template)
        
        print("   ✓ Email template generated and saved to test_corrected_email_template.html")
        
        # Check for corrected date labels in template
        if "Tanggal Backup" in email_template:
            print("   ✓ Email contains backup date information")
        else:
            print("   ✗ Email might not contain corrected date labels")
            
        # Check for proper status display
        if status_label in email_template or backup_status in email_template:
            print("   ✓ Email contains status information")
        else:
            print("   ✗ Email might not contain status information")
            
    except Exception as e:
        print(f"   ✗ Error generating email template: {e}")
    
    print("\n=== Test Completed ===")
    root.destroy()

if __name__ == "__main__":
    test_corrected_email()