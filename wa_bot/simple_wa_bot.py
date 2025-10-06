#!/usr/bin/env python3
"""
Simple WhatsApp Bot for Database Backup Monitoring
Mengikuti pendekatan dari tutorial medium.com
"""

import json
import time
from datetime import datetime
import random
import requests

class SimpleWhatsAppNotifier:
    def __init__(self):
        """
        Inisialisasi bot dengan data dummy
        """
        self.base_url = "https://api.whatsapp.com/send"  # Ini hanya placeholder
        self.phone_number = "6281234567890"  # Ganti dengan nomor tujuan
        self.backup_data = self.generate_dummy_backup_data()
    
    def generate_dummy_backup_data(self):
        """
        Generate data backup dummy yang realistis berdasarkan konteks yang diketahui
        """
        # Kita gunakan data yang mirip dengan struktur database yang telah diketahui
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "backup_file": f"staging_PTRJ_iFES_Plantware_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak",
            "size_mb": round(random.uniform(100, 1500), 2),  # UKuran realistic antara 100-1500 MB
            "tables_count": random.randint(20, 50),  # Jumlah tabel
            "gwscandata_records": random.randint(1000, 10000),  # Record GWScanner
            "ffb_records": random.randint(1000, 8000),  # Record FFBScanner
            "status": random.choice(["Success", "Warning", "Error"]),
            "last_scanned": (datetime.now() - 
                           timedelta(hours=random.randint(1, 24))).strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def format_backup_message(self, data):
        """
        Format pesan backup dalam format yang mudah dibaca
        """
        status_symbol = {
            "Success": "✅",
            "Warning": "⚠️",
            "Error": "❌"
        }
        
        # Kita ganti simbol emoji dengan teks biasa untuk menghindari masalah encoding
        status_text = {
            "Success": "[SUCCESS]",
            "Warning": "[WARNING]", 
            "Error": "[ERROR]"
        }
        
        status_display = status_text[data['status']]
        
        message = f"DATABASE BACKUP STATUS REPORT\n\n"
        message += f"Status: {status_display} {data['status']}\n"
        message += f"Timestamp: {data['timestamp']}\n"
        message += f"File: {data['backup_file']}\n"
        message += f"Size: {data['size_mb']} MB\n"
        message += f"Tables: {data['tables_count']} tables\n"
        message += f"GWScanner Records: {data['gwscandata_records']}\n"
        message += f"FFBScanner Records: {data['ffb_records']}\n"
        message += f"Last Scanned: {data['last_scanned']}\n\n"
        
        # Tambahkan pesan tambahan berdasarkan status
        if data['status'] == 'Success':
            message += "✅ Backup completed successfully!\n"
            message += "All systems are operational."
        elif data['status'] == 'Warning':
            message += "⚠️ Backup completed with warnings\n"
            message += "Please check backup integrity."
        else:  # Error
            message += "❌ Backup failed!\n"
            message += "Immediate attention required!"
        
        return message
    
    def send_dummy_message(self, message):
        """
        Kirim pesan dummy (tanpa API sebenarnya)
        """
        print("="*50)
        print("DUMMY WHATSAPP NOTIFICATION")
        print(f"To: {self.phone_number}")
        print("-"*50)
        print(message)
        print("-"*50)
        print(f"Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)
        return True
    
    def simulate_api_message(self, message):
        """
        Simulasikan kirim pesan via API
        """
        # Dalam implementasi nyata, Anda akan menggunakan API seperti:
        # 1. Twilio
        # 2. WhatsApp Business API
        # 3. Atau layanan pihak ketiga
        
        print("\nSimulating API call to send message...")
        print("In a real implementation, this would connect to a WhatsApp API service.")
        print("For now, showing dummy message:\n")
        
        success = self.send_dummy_message(message)
        return success
    
    def check_backup_status(self):
        """
        Periksa status backup dan kirim notifikasi
        """
        print("Checking backup status...")
        
        # Generate data baru untuk cek saat ini
        current_data = self.generate_dummy_backup_data()
        
        # Format pesan
        message = self.format_backup_message(current_data)
        
        # Kirim notifikasi
        success = self.simulate_api_message(message)
        
        if success:
            print("\n✅ Notification sent successfully!")
        else:
            print("\n❌ Failed to send notification!")
        
        return current_data

    def run_periodic_check(self, interval_minutes=30):
        """
        Jalankan pengecekan berkala
        """
        print(f"Starting periodic backup checks every {interval_minutes} minutes...")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.check_backup_status()
                print(f"\nNext check in {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)  # Convert to seconds
        except KeyboardInterrupt:
            print("\n\nStopping periodic checks...")

def main():
    print("Starting Simple WhatsApp Bot for Database Backup Monitoring")
    print("This bot simulates notifications about database backup status")
    print("Based on data structures from: staging_PTRJ_iFES_Plantware database\n")
    
    # Buat instance bot
    bot = SimpleWhatsAppNotifier()
    
    # Lakukan satu kali pengecekan
    print("Performing initial backup status check:\n")
    bot.check_backup_status()
    
    # Contoh data yang dihasilkan
    print("\n" + "="*50)
    print("SAMPLE DUMMY DATA STRUCTURE:")
    print(json.dumps(bot.backup_data, indent=2))
    print("="*50)
    
    # Jika ingin menjalankan pengecekan berkala, uncomment baris berikut:
    # bot.run_periodic_check(5)  # Cek setiap 5 menit untuk testing

if __name__ == "__main__":
    from datetime import timedelta  # Import tambahan
    main()