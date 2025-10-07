#!/usr/bin/env python3
"""
Test script untuk memverifikasi email dengan tanggal backup yang benar
"""

import tkinter as tk
import json
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zip_backup_monitor_enhanced import ZipBackupMonitorEnhanced

def test_email_with_corrected_dates():
    """Test pengiriman email dengan tanggal backup yang sudah diperbaiki"""
    
    print("=== Test Email dengan Tanggal Backup yang Diperbaiki ===")
    
    # Create tkinter root (hidden)
    root = tk.Tk()
    root.withdraw()
    
    try:
        # Initialize monitor
        monitor = ZipBackupMonitorEnhanced(root)
        monitor.monitoring_path.set('D:/Gawean Rebinmas/App_Auto_Backup/Backup')
        
        # Load existing summary data
        summary_file = 'backup_summary_enhanced.json'
        if os.path.exists(summary_file):
            with open(summary_file, 'r') as f:
                monitor.summary_data = json.load(f)
            print(f"✓ Summary data loaded: {len(monitor.summary_data)} backup files")
            
            # Display backup dates for verification
            print("\n=== Verifikasi Tanggal Backup ===")
            for file_path, file_info in monitor.summary_data.items():
                filename = os.path.basename(file_path)
                zip_modified = file_info.get('modified', 'N/A')
                print(f"File: {filename}")
                print(f"  ZIP Modified Date: {zip_modified}")
                
                # Check BAK files
                bak_files = file_info.get('bak_files', [])
                for bak_file in bak_files:
                    bak_name = bak_file.get('filename', 'Unknown')
                    is_outdated = bak_file.get('is_outdated', False)
                    days_since = bak_file.get('days_since_backup', 0)
                    print(f"  BAK: {bak_name} - Outdated: {is_outdated}, Days: {days_since}")
                print()
        else:
            print(f"❌ Summary file not found: {summary_file}")
            return False
        
        # Get overall status
        overall_status = monitor.get_overall_backup_status()
        print(f"Overall Backup Status: {overall_status}")
        
        # Test email generation (without actually sending)
        print("\n=== Test Email Generation ===")
        try:
            email_body = monitor.generate_deep_analysis_email_template()
            print("✓ Email template generated successfully")
            
            # Check if email contains correct date information
            if "Tanggal Backup (ZIP)" in email_body:
                print("✓ Email contains corrected ZIP file date labels")
            else:
                print("⚠ Email may not contain corrected date labels")
                
            # Save email template for inspection
            with open('test_email_template.html', 'w', encoding='utf-8') as f:
                f.write(email_body)
            print("✓ Email template saved to test_email_template.html")
            
        except Exception as e:
            print(f"❌ Error generating email template: {e}")
            return False
        
        # Optionally send actual email (uncomment if needed)
        # try:
        #     monitor.send_deep_analysis_email()
        #     print("✓ Test email sent successfully!")
        # except Exception as e:
        #     print(f"❌ Error sending email: {e}")
        
        print("\n=== Test Completed Successfully ===")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        root.destroy()

if __name__ == "__main__":
    success = test_email_with_corrected_dates()
    sys.exit(0 if success else 1)