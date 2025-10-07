#!/usr/bin/env python3
"""
Test email sederhana dan generate backup summary
"""

import smtplib
import configparser
import json
import os
from datetime import datetime
from email.mime.text import MIMEText

def test_email_connection():
    """Test koneksi SMTP server"""
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        print("=== Email Configuration Test ===")
        print(f"SMTP Server: {config['EMAIL']['smtp_server']}")
        print(f"SMTP Port: {config['EMAIL']['smtp_port']}")
        print(f"Sender Email: {config['EMAIL']['sender_email']}")
        print(f"Recipient Email: {config['EMAIL']['recipient_email']}")
        print(f"Password: {'*' * len(config['EMAIL']['sender_password'])}")

        print("\n=== Testing SMTP Connection ===")

        # Test connection ke server
        server = smtplib.SMTP(config['EMAIL']['smtp_server'], int(config['EMAIL']['smtp_port']))
        print("[OK] Connected to SMTP server")

        # Test STARTTLS
        server.starttls()
        print("[OK] STARTTLS successful")

        # Test login
        server.login(
            config['EMAIL']['sender_email'],
            config['EMAIL']['sender_password']
        )
        print("[OK] Login successful")

        # Test sending email
        msg = MIMEText("Test email dari monitoring backup system")
        msg['Subject'] = 'Test Email Connection'
        msg['From'] = config['EMAIL']['sender_email']
        msg['To'] = config['EMAIL']['recipient_email']

        server.sendmail(
            config['EMAIL']['sender_email'],
            config['EMAIL']['recipient_email'],
            msg.as_string()
        )
        print("[OK] Test email sent successfully")

        server.quit()
        print("\n[SUCCESS] All tests passed! Email configuration is working.")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"\n[ERROR] Authentication Error: {e}")
        print("\nPossible causes:")
        print("1. 2-Factor Authentication tidak aktif di Google Account")
        print("2. App Password tidak valid atau expired")
        print("3. Email/password salah")
        print("\nSolusi:")
        print("1. Pastikan 2FA aktif: https://myaccount.google.com/security")
        print("2. Generate App Password baru: https://myaccount.google.com/apppasswords")
        print("3. Pilih app: 'Mail', device: 'Windows Computer'")
        return False

    except smtplib.SMTPException as e:
        print(f"\n[ERROR] SMTP Error: {e}")
        print("Check koneksi internet dan firewall settings")
        return False

    except Exception as e:
        print(f"\n[ERROR] General Error: {e}")
        return False

def generate_backup_summary_json():
    """Generate backup summary JSON dari data yang ada"""
    backup_path = "D:/Gawean Rebinmas/App_Auto_Backup/Backup"

    # Create summary data structure
    summary_data = {
        "generated_at": datetime.now().isoformat(),
        "backup_path": backup_path,
        "scan_results": {
            "total_zip_files": 0,
            "valid_zip_files": 0,
            "extracted_files": 0,
            "total_bak_files": 0,
            "valid_bak_files": 0
        },
        "files": [],
        "by_type": {
            "BackupStaging": {"count": 0, "valid": 0, "excluded": False},
            "BackupVenus": {"count": 0, "valid": 0, "excluded": False},
            "PlantwareP3": {"count": 0, "valid": 0, "excluded": True},  # Exclude PlantwareP3
            "Unknown": {"count": 0, "valid": 0, "excluded": False}
        },
        "checklist_results": [],
        "configuration": {
            "exclude_plantware": True,
            "extract_files": True
        }
    }

    try:
        # Scan for ZIP files
        zip_files = []
        for root, dirs, files in os.walk(backup_path):
            for file in files:
                if file.lower().endswith('.zip'):
                    zip_files.append(os.path.join(root, file))

        summary_data["scan_results"]["total_zip_files"] = len(zip_files)

        for file_path in zip_files:
            filename = os.path.basename(file_path)
            backup_type = detect_backup_type_from_filename(filename)

            # Skip PlantwareP3 if excluded
            if backup_type == "PlantwareP3":
                print(f"[INFO] Excluding PlantwareP3: {filename}")
                continue

            file_info = {
                "filename": filename,
                "path": file_path,
                "size": os.path.getsize(file_path),
                "size_formatted": format_size(os.path.getsize(file_path)),
                "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                "backup_type": backup_type,
                "status": "Valid",
                "bak_files": []
            }

            summary_data["scan_results"]["valid_zip_files"] += 1

            # Update by_type statistics
            if backup_type in summary_data["by_type"]:
                summary_data["by_type"][backup_type]["count"] += 1
                summary_data["by_type"][backup_type]["valid"] += 1

            summary_data["files"].append(file_info)

        # Save to JSON
        with open('backup_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"[SUCCESS] Backup summary saved to backup_summary.json")
        print(f"  - Total ZIP files found: {summary_data['scan_results']['total_zip_files']}")
        print(f"  - Valid ZIP files (non-PlantwareP3): {summary_data['scan_results']['valid_zip_files']}")
        print(f"  - PlantwareP3 excluded: {summary_data['by_type']['PlantwareP3']['excluded']}")
        print(f"  - Generated at: {summary_data['generated_at']}")

        return True

    except Exception as e:
        print(f"[ERROR] Error generating backup summary: {e}")
        return False

def detect_backup_type_from_filename(filename: str) -> str:
    """Deteksi jenis backup dari nama file"""
    filename_lower = filename.lower()

    if filename_lower.startswith('backupstaging'):
        return 'BackupStaging'
    elif filename_lower.startswith('backupvenu'):
        return 'BackupVenus'
    elif filename_lower.startswith('plantwarep3'):
        return 'PlantwareP3'
    else:
        return 'Unknown'

def format_size(size_bytes: int) -> str:
    """Format size dalam format yang mudah dibaca"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

if __name__ == "__main__":
    print("=== Backup Monitor Email & Summary Test ===\n")

    # Generate backup summary
    print("1. Generating backup summary JSON (PlantwareP3 excluded)...")
    generate_backup_summary_json()

    print("\n" + "="*60 + "\n")

    # Test email connection
    print("2. Testing email connection...")
    email_success = test_email_connection()

    print("\n" + "="*60 + "\n")

    if email_success:
        print("[COMPLETE] Both backup summary and email test successful!")
    else:
        print("[PARTIAL] Backup summary generated, but email test failed.")
        print("Check email configuration and try again.")