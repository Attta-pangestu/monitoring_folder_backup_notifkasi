#!/usr/bin/env python3
"""
Database Backup Monitor Application
Aplikasi untuk monitoring dan notifikasi backup database
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gui import DatabaseBackupMonitorGUI
from email_notifier import EmailNotifier
from backup_monitor import BackupMonitor
from folder_monitor import FolderMonitor

def main():
    try:
        # Create main window
        root = tk.Tk()

        # Set application icon (if available)
        try:
            root.iconbitmap('assets/icon.ico')
        except:
            pass

        # Create application
        app = DatabaseBackupMonitorGUI(root)

        # Start the GUI
        root.mainloop()

    except Exception as e:
        messagebox.showerror("Error", f"Failed to start application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()