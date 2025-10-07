#!/usr/bin/env python3
"""
Test script untuk backup history functionality
"""

import tkinter as tk
from tkinter import ttk
import os
import json

class BackupHistoryTest:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Backup History Test")
        self.root.geometry("800x600")

        # Create test button
        test_button = ttk.Button(self.root, text="Test Load Backup History", command=self.test_load_history)
        test_button.pack(pady=10)

        # Create text widget for output
        self.output_text = tk.Text(self.root, height=20, width=80)
        self.output_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.output_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.config(yscrollcommand=scrollbar.set)

    def test_load_history(self):
        """Test loading backup history from JSON file"""
        try:
            self.output_text.insert(tk.END, "Testing backup history load...\n\n")

            json_file = "backup_summary_enhanced.json"

            if not os.path.exists(json_file):
                self.output_text.insert(tk.END, f"ERROR: File {json_file} not found!\n")
                return

            self.output_text.insert(tk.END, f"Loading data from {json_file}...\n")

            with open(json_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            self.output_text.insert(tk.END, f"Successfully loaded {len(backup_data)} backup files!\n\n")

            # Show summary
            self.output_text.insert(tk.END, "=== BACKUP SUMMARY ===\n")
            for file_path, file_info in backup_data.items():
                self.output_text.insert(tk.END, f"\nFile: {os.path.basename(file_path)}\n")
                self.output_text.insert(tk.END, f"Status: {file_info.get('status', 'Unknown')}\n")
                self.output_text.insert(tk.END, f"Size: {file_info.get('size', 0) / (1024*1024):.2f} MB\n")
                self.output_text.insert(tk.END, f"Modified: {file_info.get('modified', 'N/A')}\n")

                bak_files = file_info.get('bak_files', [])
                if bak_files:
                    self.output_text.insert(tk.END, f"BAK Files: {len(bak_files)}\n")
                    for bak in bak_files:
                        self.output_text.insert(tk.END, f"  - {bak.get('filename', 'Unknown')}\n")

            self.output_text.insert(tk.END, "\n=== TEST COMPLETED SUCCESSFULLY ===\n")

        except Exception as e:
            self.output_text.insert(tk.END, f"ERROR: {str(e)}\n")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    test_app = BackupHistoryTest()
    test_app.run()