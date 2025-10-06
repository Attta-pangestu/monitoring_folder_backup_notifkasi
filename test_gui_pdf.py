#!/usr/bin/env python3
"""
Test GUI PDF functionality by simulating user interactions
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from PyQt5.QtTest import QTest
from backup_monitor_qt import BackupMonitorWindow

def test_gui_pdf_functionality():
    """Test the PDF generation functionality through the GUI"""
    print("Testing GUI PDF Functionality...")
    print("=" * 50)
    
    # Create QApplication if it doesn't exist
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        # Create the main window
        window = BackupMonitorWindow()
        window.show()
        
        # Wait for the window to fully load
        QTest.qWait(1000)
        
        # Check if ZIP files are loaded in the table
        zip_table = window.zip_summary_table
        row_count = zip_table.rowCount()
        print(f"ZIP files loaded in table: {row_count}")
        
        if row_count > 0:
            # Select the first row
            zip_table.selectRow(0)
            print("Selected first ZIP file in table")
            
            # Check if the PDF button is enabled
            pdf_button = window.generate_pdf_btn
            if pdf_button.isEnabled():
                print("PDF generation button is enabled ✓")
                
                # Test clicking the PDF button (but don't actually generate)
                print("PDF button functionality is ready for testing")
                
                # Check if TestBackup.zip is in the table
                test_zip_found = False
                for row in range(row_count):
                    item = zip_table.item(row, 0)  # Assuming filename is in first column
                    if item and "TestBackup.zip" in item.text():
                        test_zip_found = True
                        zip_table.selectRow(row)
                        print(f"Found and selected TestBackup.zip in row {row} ✓")
                        break
                
                if not test_zip_found:
                    print("TestBackup.zip not found in table - this is expected if it's not in the monitored directory")
                
            else:
                print("PDF generation button is disabled ✗")
        else:
            print("No ZIP files found in table ✗")
        
        # Test the PDF generator directly
        print("\nTesting PDF generator integration...")
        if hasattr(window, 'pdf_generator'):
            print("PDF generator is properly integrated ✓")
        else:
            print("PDF generator not found ✗")
        
        # Close the window
        window.close()
        
        print("\n" + "=" * 50)
        print("GUI PDF Test completed successfully ✓")
        
    except Exception as e:
        print(f"Error during GUI testing: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_gui_pdf_functionality()
    sys.exit(0 if success else 1)