#!/usr/bin/env python3
"""
Script untuk memeriksa header file BAK dan menentukan jenis file
"""

import os
import struct

def check_bak_header(file_path):
    """Memeriksa header file BAK"""
    
    if not os.path.exists(file_path):
        print(f"File tidak ditemukan: {file_path}")
        return
    
    print(f"Memeriksa file: {file_path}")
    print(f"Ukuran file: {os.path.getsize(file_path):,} bytes")
    
    with open(file_path, 'rb') as f:
        # Baca 512 bytes pertama
        header = f.read(512)
        
        print("\n=== HEADER ANALYSIS ===")
        print(f"Header length: {len(header)} bytes")
        
        # Tampilkan hex dump dari 64 bytes pertama
        print("\nHex dump (first 64 bytes):")
        for i in range(0, min(64, len(header)), 16):
            hex_part = ' '.join(f'{b:02X}' for b in header[i:i+16])
            ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in header[i:i+16])
            print(f"{i:04X}: {hex_part:<48} {ascii_part}")
        
        # Cek signature SQL Server backup
        sql_signatures = [
            b'TAPE',  # SQL Server backup signature
            b'DISK',  # SQL Server disk backup
            b'Microsoft SQL Server',
            b'BACKUP',
        ]
        
        print("\n=== SIGNATURE CHECK ===")
        found_signature = False
        for sig in sql_signatures:
            if sig in header:
                print(f"Found SQL Server signature: {sig}")
                found_signature = True
        
        if not found_signature:
            print("No SQL Server backup signature found")
        
        # Cek apakah ini file SQLite
        if header.startswith(b'SQLite format 3'):
            print("This appears to be a SQLite database file")
        
        # Cek apakah ini file ZIP
        if header.startswith(b'PK'):
            print("This appears to be a ZIP/compressed file")
        
        # Cek magic numbers lainnya
        magic_numbers = {
            b'\x4D\x53\x46\x54': 'Microsoft Tape Format',
            b'\x01\x0F\x00\x00': 'SQL Server backup header',
            b'MSFT': 'Microsoft Tape Format',
        }
        
        print("\n=== MAGIC NUMBER CHECK ===")
        for magic, description in magic_numbers.items():
            if header.startswith(magic):
                print(f"Found magic number: {description}")
        
        # Cari string yang dapat dibaca
        print("\n=== READABLE STRINGS ===")
        readable_strings = []
        current_string = ""
        
        for byte in header:
            if 32 <= byte <= 126:  # Printable ASCII
                current_string += chr(byte)
            else:
                if len(current_string) >= 4:
                    readable_strings.append(current_string)
                current_string = ""
        
        if len(current_string) >= 4:
            readable_strings.append(current_string)
        
        for string in readable_strings[:10]:  # Show first 10 strings
            print(f"  '{string}'")
        
        # Analisis lebih dalam untuk SQL Server backup
        print("\n=== SQL SERVER BACKUP ANALYSIS ===")
        try:
            # Cek pada offset yang umum untuk SQL Server backup header
            offsets_to_check = [0, 512, 1024, 4096]
            
            for offset in offsets_to_check:
                f.seek(offset)
                chunk = f.read(512)
                
                if b'Microsoft SQL Server' in chunk or b'BACKUP' in chunk:
                    print(f"Found SQL Server related content at offset {offset}")
                    
                    # Cari database name
                    if b'master' in chunk or b'model' in chunk or b'msdb' in chunk or b'tempdb' in chunk:
                        print("Found system database references")
                    
                    # Cari timestamp patterns
                    for i in range(len(chunk) - 8):
                        try:
                            # Coba decode sebagai timestamp
                            timestamp_bytes = chunk[i:i+8]
                            if len(timestamp_bytes) == 8:
                                timestamp = struct.unpack('<Q', timestamp_bytes)[0]
                                if 116444736000000000 <= timestamp <= 253402300799000000:  # Valid Windows timestamp range
                                    from datetime import datetime, timezone
                                    dt = datetime.fromtimestamp((timestamp - 116444736000000000) / 10000000, tz=timezone.utc)
                                    if 2000 <= dt.year <= 2030:  # Reasonable year range
                                        print(f"Possible timestamp found: {dt}")
                                        break
                        except:
                            continue
                            
        except Exception as e:
            print(f"Error during detailed analysis: {e}")

if __name__ == "__main__":
    bak_file = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup\BackupStaging.bak"
    check_bak_header(bak_file)