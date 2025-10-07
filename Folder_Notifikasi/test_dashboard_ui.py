#!/usr/bin/env python3
"""
Test script untuk dashboard UI card display
"""

import tkinter as tk
from tkinter import ttk
import json
import os
from datetime import datetime

class DashboardTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dashboard UI Test")
        self.root.geometry("1200x800")

        # Load test data
        self.load_test_data()

        # Create dashboard UI
        self.create_dashboard_ui()

        # Update display
        self.update_dashboard_display()

    def load_test_data(self):
        """Load test data from JSON file"""
        try:
            with open('backup_summary_enhanced.json', 'r', encoding='utf-8') as f:
                self.test_data = json.load(f)
            print(f"Loaded {len(self.test_data)} test records")
        except Exception as e:
            print(f"Error loading test data: {e}")
            self.test_data = {}

    def create_dashboard_ui(self):
        """Create dashboard UI similar to the main app"""
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = tk.Label(main_frame, text="DASHBOARD MONITORING BACKUP",
                              font=('Arial', 16, 'bold'), fg='#2c3e50')
        title_label.pack(pady=10)

        # Control buttons
        control_frame = tk.Frame(main_frame, bg='#f8f9fa')
        control_frame.pack(fill='x', padx=10, pady=5)

        refresh_btn = ttk.Button(control_frame, text="Refresh Dashboard", command=self.update_dashboard_display)
        refresh_btn.pack(side='left', padx=5)

        # Create scrollable canvas
        canvas = tk.Canvas(main_frame, bg='#f8f9fa')
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Store reference
        self.dashboard_frame = scrollable_frame

        # Create dashboard sections
        self.create_critical_info_section(scrollable_frame)
        self.create_executive_summary_section(scrollable_frame)
        self.create_backup_cards_section(scrollable_frame)

    def create_critical_info_section(self, parent):
        """Create critical information section"""
        # Critical Info Card
        critical_frame = tk.Frame(parent, bg='#fff3cd', relief='solid', borderwidth=2)
        critical_frame.pack(fill='x', padx=10, pady=5)

        # Header
        header_label = tk.Label(critical_frame, text="INFORMASI KRITIS BACKUP",
                              font=('Arial', 14, 'bold'), bg='#fff3cd', fg='#856404')
        header_label.pack(pady=10)

        # Content frame
        content_frame = tk.Frame(critical_frame, bg='#fff3cd')
        content_frame.pack(fill='x', padx=10, pady=5)

        # Left column - Backup Info
        left_frame = tk.Frame(content_frame, bg='#fff3cd')
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        tk.Label(left_frame, text="Informasi Backup", font=('Arial', 12, 'bold'),
                bg='#fff3cd', fg='#856404').pack(anchor='w')

        self.critical_info_labels = {
            'report_date': tk.Label(left_frame, text="Laporan Dibuat: -", bg='#fff3cd', fg='#856404'),
            'latest_backup': tk.Label(left_frame, text="Backup Terbaru: -", bg='#fff3cd', fg='#856404'),
            'oldest_backup': tk.Label(left_frame, text="Backup Terlama: -", bg='#fff3cd', fg='#856404'),
            'total_files': tk.Label(left_frame, text="Total File Backup: -", bg='#fff3cd', fg='#856404')
        }

        for label in self.critical_info_labels.values():
            label.pack(anchor='w', pady=2)

        # Right column - Status Info
        right_frame = tk.Frame(content_frame, bg='#fff3cd')
        right_frame.pack(side='right', fill='both', expand=True)

        tk.Label(right_frame, text="Status Kritis", font=('Arial', 12, 'bold'),
                bg='#fff3cd', fg='#856404').pack(anchor='w')

        self.critical_status_labels = {
            'attention_items': tk.Label(right_frame, text="Item Perlu Perhatian: -", bg='#fff3cd', fg='#856404'),
            'system_status': tk.Label(right_frame, text="Status Sistem: -", bg='#fff3cd', fg='#856404')
        }

        for label in self.critical_status_labels.values():
            label.pack(anchor='w', pady=2)

    def create_executive_summary_section(self, parent):
        """Create executive summary section with statistics"""
        summary_frame = tk.Frame(parent, bg='#f8f9fa', relief='solid', borderwidth=1)
        summary_frame.pack(fill='x', padx=10, pady=5)

        # Header
        header_label = tk.Label(summary_frame, text="Ringkasan Eksekutif",
                              font=('Arial', 14, 'bold'), bg='#f8f9fa', fg='#2c3e50')
        header_label.pack(pady=10)

        # Stats grid
        stats_frame = tk.Frame(summary_frame, bg='#f8f9fa')
        stats_frame.pack(fill='x', padx=10, pady=5)

        # Create stat cards
        self.stat_cards = {}
        stats_data = [
            ('total_zip', 'Total Arsip ZIP', '-'),
            ('valid_zip', 'File ZIP Valid', '-'),
            ('success_rate', 'Tingkat Keberhasilan', '-'),
            ('backup_date', 'Tanggal Backup', '-'),
            ('total_bak', 'Total File BAK', '-'),
            ('system_status', 'Status Sistem', '-')
        ]

        for i, (key, label, default_value) in enumerate(stats_data):
            card_frame = tk.Frame(stats_frame, bg='white', relief='solid', borderwidth=1, width=120)
            card_frame.grid(row=i//3, column=i%3, padx=5, pady=5)
            card_frame.grid_propagate(False)

            # Value label
            value_label = tk.Label(card_frame, text=default_value, font=('Arial', 12, 'bold'),
                                 bg='white', fg='#007bff')
            value_label.pack(pady=(10, 2))

            # Label
            label_widget = tk.Label(card_frame, text=label, font=('Arial', 9),
                                   bg='white', fg='#6c757d')
            label_widget.pack(pady=(2, 10))

            self.stat_cards[key] = {'frame': card_frame, 'value': value_label, 'label': label_widget}

    def create_backup_cards_section(self, parent):
        """Create backup file cards section"""
        cards_frame = tk.Frame(parent, bg='#f8f9fa')
        cards_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Header
        header_label = tk.Label(cards_frame, text="Detail Analisis File Backup",
                              font=('Arial', 14, 'bold'), bg='#f8f9fa', fg='#2c3e50')
        header_label.pack(anchor='w', pady=(10, 5))

        # Container for backup cards
        self.backup_cards_container = tk.Frame(cards_frame, bg='#f8f9fa')
        self.backup_cards_container.pack(fill='both', expand=True)

    def update_dashboard_display(self):
        """Update dashboard display with test data"""
        if not self.test_data:
            return

        # Update critical info
        self.update_critical_info()

        # Update executive summary
        self.update_executive_summary()

        # Update backup cards
        self.update_backup_cards()

    def update_critical_info(self):
        """Update critical information section"""
        total_files = len(self.test_data)
        valid_files = sum(1 for f in self.test_data.values() if f.get('status') == 'Valid')
        latest_date = max((f.get('modified', '') for f in self.test_data.values()), default='')
        oldest_date = min((f.get('modified', '') for f in self.test_data.values()), default='')

        # Count issues
        attention_items = 0
        for file_info in self.test_data.values():
            if file_info.get('status') != 'Valid':
                attention_items += 1
            if file_info.get('is_outdated', False):
                attention_items += 1

        # Update labels
        self.critical_info_labels['report_date'].config(text=f"Laporan Dibuat: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.critical_info_labels['latest_backup'].config(text=f"Backup Terbaru: {latest_date[:16] if latest_date else '-'}")
        self.critical_info_labels['oldest_backup'].config(text=f"Backup Terlama: {oldest_date[:16] if oldest_date else '-'}")
        self.critical_info_labels['total_files'].config(text=f"Total File Backup: {total_files}")

        self.critical_status_labels['attention_items'].config(text=f"Item Perlu Perhatian: {attention_items}")
        system_status = "AKTIF" if valid_files == total_files else "PERLU PERHATIAN"
        self.critical_status_labels['system_status'].config(text=f"Status Sistem: {system_status}")

    def update_executive_summary(self):
        """Update executive summary statistics"""
        total_files = len(self.test_data)
        valid_files = sum(1 for f in self.test_data.values() if f.get('status') == 'Valid')
        success_rate = f"{(valid_files/total_files*100):.1f}%" if total_files > 0 else "0%"

        # Count BAK files
        total_bak = sum(len(f.get('bak_files', [])) for f in self.test_data.values())

        # Get latest backup date
        latest_date = max((f.get('modified', '') for f in self.test_data.values()), default='')
        backup_date = latest_date[:10] if latest_date else '-'

        # Update stat cards
        self.stat_cards['total_zip']['value'].config(text=str(total_files))
        self.stat_cards['valid_zip']['value'].config(text=str(valid_files))
        self.stat_cards['success_rate']['value'].config(text=success_rate)
        self.stat_cards['backup_date']['value'].config(text=backup_date)
        self.stat_cards['total_bak']['value'].config(text=str(total_bak))
        self.stat_cards['system_status']['value'].config(text="AKTIF")

    def update_backup_cards(self):
        """Update backup file cards"""
        # Clear existing cards
        for widget in self.backup_cards_container.winfo_children():
            widget.destroy()

        for file_path, file_info in self.test_data.items():
            self.create_backup_card(file_path, file_info)

    def create_backup_card(self, file_path, file_info):
        """Create individual backup file card"""
        card_frame = tk.Frame(self.backup_cards_container, bg='white', relief='solid', borderwidth=1)
        card_frame.pack(fill='x', padx=5, pady=5)

        # File name
        filename = os.path.basename(file_path)
        name_label = tk.Label(card_frame, text=filename, font=('Arial', 12, 'bold'),
                             bg='white', fg='#2c3e50')
        name_label.pack(anchor='w', padx=10, pady=(10, 5))

        # Details frame
        details_frame = tk.Frame(card_frame, bg='white')
        details_frame.pack(fill='x', padx=10, pady=5)

        # File information
        size_mb = file_info.get('size', 0) / (1024 * 1024)
        modified = file_info.get('modified', 'N/A')[:16] if file_info.get('modified') != 'N/A' else 'N/A'
        status = file_info.get('status', 'Unknown')
        backup_type = file_info.get('backup_type', 'Unknown')

        # Calculate age
        try:
            mod_date = datetime.fromisoformat(file_info.get('modified', '2025-01-01'))
            age_days = (datetime.now() - mod_date).days
        except:
            age_days = 0

        details = [
            ("Tipe Backup:", backup_type),
            ("Ukuran File:", f"{size_mb:.1f} MB"),
            ("Status:", status),
            ("Terakhir Dimodifikasi:", modified),
            ("Usia:", f"{age_days} hari")
        ]

        for i, (label, value) in enumerate(details):
            label_widget = tk.Label(details_frame, text=label, bg='white', fg='#6c757d', font=('Arial', 9))
            label_widget.grid(row=i//3, column=(i%3)*2, sticky='w', padx=(0, 5), pady=2)

            value_widget = tk.Label(details_frame, text=value, bg='white', fg='#2c3e50', font=('Arial', 9, 'bold'))
            value_widget.grid(row=i//3, column=(i%3)*2+1, sticky='w', padx=(0, 20), pady=2)

        # Status badge
        status_color = "#28a745" if status == "Valid" else "#dc3545"
        status_badge = tk.Label(card_frame, text=status, bg=status_color, fg='white',
                               font=('Arial', 8, 'bold'), relief='solid', borderwidth=1)
        status_badge.pack(anchor='e', padx=10, pady=(0, 10))

if __name__ == "__main__":
    root = tk.Tk()
    app = DashboardTestApp(root)
    root.mainloop()