#!/usr/bin/env python3
"""
Tape File Analyzer Module
Untuk menganalisis file backup format TAPE yang bukan SQLite database
"""

import os
import struct
from datetime import datetime
from typing import Dict, List, Optional, Any
import zipfile

class TapeFileAnalyzer:
    def __init__(self):
        self.supported_formats = ['TAPE', 'PLANTWARE_BACKUP']

    def analyze_tape_file(self, file_path: str, original_filename: str = None) -> Dict:
        """
        Analisis file format TAPE
        """
        analysis = {
            'file_format': 'unknown',
            'filename': original_filename or os.path.basename(file_path),
            'file_size_mb': round(os.path.getsize(file_path) / (1024 * 1024), 2),
            'signature': None,
            'header_info': {},
            'estimated_records': 0,
            'date_info': {},
            'warnings': [],
            'errors': [],
            'analysis_notes': []
        }

        try:
            with open(file_path, 'rb') as f:
                # Baca header untuk analisis
                header = f.read(1024)  # Baca 1KB pertama

                if len(header) < 16:
                    analysis['errors'].append("File too small for analysis")
                    return analysis

                analysis['signature'] = header[:16].hex()

                # Deteksi format berdasarkan signature
                if header.startswith(b'TAPE'):
                    analysis['file_format'] = 'TAPE'
                    analysis = self._analyze_tape_header(analysis, header)
                else:
                    analysis['warnings'].append("Unknown file format detected")

                # Coba ekstrak informasi tanggal dari filename
                if original_filename:
                    date_info = self._extract_date_from_filename(original_filename)
                    if date_info:
                        analysis['date_info']['filename_date'] = date_info

                # Estimasi jumlah record berdasarkan ukuran file
                analysis['estimated_records'] = self._estimate_record_count(file_path, analysis['file_format'])

        except Exception as e:
            analysis['errors'].append(f"Error analyzing file: {str(e)}")

        return analysis

    def _analyze_tape_header(self, analysis: Dict, header: bytes) -> Dict:
        """Analisis header TAPE format"""
        try:
            # Header structure (berdasarkan analisis sebelumnya):
            # TAPE [4 bytes] + version [4 bytes] + flags [4 bytes] + timestamp [8 bytes]

            analysis['header_info']['format_signature'] = header[:4].decode('ascii', errors='ignore')

            # Version info (bytes 4-7)
            if len(header) >= 8:
                version = struct.unpack('<I', header[4:8])[0]
                analysis['header_info']['version'] = version

            # Flags/parameters (bytes 8-11)
            if len(header) >= 12:
                flags = struct.unpack('<I', header[8:12])[0]
                analysis['header_info']['flags'] = flags

            # Timestamp (bytes 12-19) - jika ada
            if len(header) >= 20:
                timestamp_bytes = header[12:20]
                # Coba interpret sebagai timestamp
                try:
                    timestamp = struct.unpack('<Q', timestamp_bytes)[0]
                    if timestamp > 0:
                        # Konversi ke datetime (asumsi Unix timestamp)
                        try:
                            dt = datetime.fromtimestamp(timestamp)
                            analysis['date_info']['header_timestamp'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            analysis['warnings'].append("Could not convert header timestamp")
                except:
                    analysis['warnings'].append("Could not parse header timestamp")

            # Additional header analysis
            if len(header) >= 32:
                analysis['header_info']['additional_data'] = header[20:32].hex()

            analysis['analysis_notes'].append("TAPE format detected - proprietary backup format")
            analysis['analysis_notes'].append("This appears to be a Plantware P3 backup file")

        except Exception as e:
            analysis['errors'].append(f"Error analyzing TAPE header: {str(e)}")

        return analysis

    def _extract_date_from_filename(self, filename: str) -> Optional[str]:
        """Ekstrak tanggal dari nama file"""
        import re

        # Pattern untuk tanggal dalam format: YYYY-MM-DD HH;MM;SS
        patterns = [
            r'(\d{4}-\d{2}-\d{2}\s+\d{2};\d{2};\d{2})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{4}\d{2}\d{2})'
        ]

        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                date_str = match.group(1)
                # Normalisasi format
                date_str = date_str.replace(';', ':')
                return date_str

        return None

    def _estimate_record_count(self, file_path: str, file_format: str) -> int:
        """Estimasi jumlah record berdasarkan ukuran file"""
        try:
            file_size = os.path.getsize(file_path)

            if file_format == 'TAPE':
                # Untuk Plantware backup, asumsi rata-rata record size ~500 bytes
                avg_record_size = 500
                estimated = file_size // avg_record_size
                return max(estimated, 0)
            else:
                # Default estimation
                return file_size // 1000  # Asumsi 1KB per record

        except:
            return 0

    def get_tape_file_summary(self, analysis: Dict) -> str:
        """Generate human-readable summary"""
        summary = []

        summary.append("TAPE FILE ANALYSIS")
        summary.append("=" * 50)
        summary.append(f"File: {analysis['filename']}")
        summary.append(f"Format: {analysis['file_format']}")
        summary.append(f"Size: {analysis['file_size_mb']:.2f} MB")
        summary.append("")

        if analysis.get('signature'):
            summary.append(f"Signature: {analysis['signature']}")

        if analysis.get('header_info'):
            summary.append("\nHEADER INFORMATION:")
            for key, value in analysis['header_info'].items():
                if isinstance(value, int):
                    summary.append(f"  {key}: {value} (0x{value:08X})")
                else:
                    summary.append(f"  {key}: {value}")

        if analysis.get('date_info'):
            summary.append("\nDATE INFORMATION:")
            for key, value in analysis['date_info'].items():
                summary.append(f"  {key}: {value}")

        summary.append(f"\nESTIMATED RECORDS: {analysis['estimated_records']:,}")

        if analysis.get('analysis_notes'):
            summary.append("\nANALYSIS NOTES:")
            for note in analysis['analysis_notes']:
                summary.append(f"  * {note}")

        if analysis.get('warnings'):
            summary.append("\nWARNINGS:")
            for warning in analysis['warnings']:
                summary.append(f"  * {warning}")

        if analysis.get('errors'):
            summary.append("\nERRORS:")
            for error in analysis['errors']:
                summary.append(f"  * {error}")

        return "\n".join(summary)

    def can_analyze_format(self, file_signature: bytes) -> bool:
        """Cek apakah format bisa dianalisis"""
        return file_signature.startswith(b'TAPE')

# Test function
def test_tape_analyzer():
    """Test the tape analyzer"""
    analyzer = TapeFileAnalyzer()

    # Test with the actual file
    test_file = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup\PlantwareP3 2025-10-04 11;33;53.zip"

    if os.path.exists(test_file):
        print(f"Testing with: {test_file}")

        try:
            with zipfile.ZipFile(test_file, 'r') as zip_ref:
                files = zip_ref.namelist()
                print(f"Files in ZIP: {files}")

                for filename in files:
                    print(f"\nAnalyzing: {filename}")

                    # Extract to temp file
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                        with zip_ref.open(filename) as source:
                            temp_file.write(source.read())
                        temp_file_path = temp_file.name

                    try:
                        analysis = analyzer.analyze_tape_file(temp_file_path, filename)
                        print(analyzer.get_tape_file_summary(analysis))
                    finally:
                        os.unlink(temp_file_path)

        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"Test file not found: {test_file}")

if __name__ == "__main__":
    test_tape_analyzer()