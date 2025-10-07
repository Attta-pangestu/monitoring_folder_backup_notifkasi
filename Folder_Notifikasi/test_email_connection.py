#!/usr/bin/env python3
"""
Test koneksi email dan troubleshooting
"""

import smtplib
import configparser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback

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
        print("✓ Connected to SMTP server")

        # Test STARTTLS
        server.starttls()
        print("✓ STARTTLS successful")

        # Test login
        server.login(
            config['EMAIL']['sender_email'],
            config['EMAIL']['sender_password']
        )
        print("✓ Login successful")

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
        print("✓ Test email sent successfully")

        server.quit()
        print("\n✓ All tests passed! Email configuration is working.")

    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ Authentication Error: {e}")
        print("\nPossible causes:")
        print("1. 2-Factor Authentication tidak aktif")
        print("2. App Password tidak valid atau expired")
        print("3. Email/password salah")

    except smtplib.SMTPException as e:
        print(f"\n❌ SMTP Error: {e}")
        print("Check koneksi internet dan firewall settings")

    except Exception as e:
        print(f"\n❌ General Error: {e}")
        print("Full traceback:")
        traceback.print_exc()

def generate_backup_summary_json():
    """Generate backup summary JSON dari data yang ada"""
    import os
    import json
    from datetime import datetime

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
            "BackupStaging": {"count": 0, "valid": 0},
            "BackupVenus": {"count": 0, "valid": 0},
            "PlantwareP3": {"count": 0, "valid": 0},
            "Unknown": {"count": 0, "valid": 0}
        },
        "checklist_results": []
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
            file_info = {
                "filename": os.path.basename(file_path),
                "path": file_path,
                "size": os.path.getsize(file_path),
                "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                "backup_type": detect_backup_type_from_filename(os.path.basename(file_path)),
                "status": "Valid",
                "bak_files": []
            }

            summary_data["scan_results"]["valid_zip_files"] += 1

            # Update by_type statistics
            btype = file_info["backup_type"]
            if btype in summary_data["by_type"]:
                summary_data["by_type"][btype]["count"] += 1
                summary_data["by_type"][btype]["valid"] += 1

            summary_data["files"].append(file_info)

        # Save to JSON
        with open('backup_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"✓ Backup summary saved to backup_summary.json")
        print(f"  - Total ZIP files: {summary_data['scan_results']['total_zip_files']}")
        print(f"  - Valid ZIP files: {summary_data['scan_results']['valid_zip_files']}")
        print(f"  - Generated at: {summary_data['generated_at']}")

        return True

    except Exception as e:
        print(f"❌ Error generating backup summary: {e}")
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

if __name__ == "__main__":
    print("=== Backup Monitor Email & Summary Test ===\n")

    # Test email connection
    print("1. Testing email connection...")
    test_email_connection()

    print("\n" + "="*50 + "\n")

    # Generate backup summary
    print("2. Generating backup summary JSON...")
    generate_backup_summary_json()

    print("\n" + "="*50 + "\n")
    print("Test selesai!")