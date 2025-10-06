"""
PDF Report Generator for Backup Analysis
Generates comprehensive PDF reports for ZIP backup files
"""

import os
import sys
import json
import zipfile
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# PDF generation libraries
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
except ImportError:
    print("ReportLab not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Import our analyzers
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.bak_metadata_analyzer import BAKMetadataAnalyzer


class ZipAnalyzer:
    """Comprehensive ZIP file analyzer for backup reports"""
    
    def __init__(self, zip_path: Optional[str] = None):
        self.zip_path = zip_path
        self.zip_name = os.path.basename(zip_path) if zip_path else None
        
    def analyze_zip_metadata(self, zip_path: Optional[str] = None) -> Dict[str, Any]:
        """Analyze ZIP file metadata"""
        target_path = zip_path or self.zip_path
        if not target_path:
            return {}
            
        try:
            stat = os.stat(target_path)
            
            with zipfile.ZipFile(target_path, 'r') as zf:
                file_list = zf.infolist()
                
                # Basic metadata
                metadata = {
                    'file_name': os.path.basename(target_path),
                    'file_path': target_path,
                    'file_size_bytes': stat.st_size,
                    'file_size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'created_date': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    'modified_date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'total_files': len(file_list),
                    'compressed_size': sum(f.compress_size for f in file_list),
                    'uncompressed_size': sum(f.file_size for f in file_list),
                    'compression_ratio': 0,
                    'files_info': []
                }
                
                # Calculate compression ratio
                if metadata['uncompressed_size'] > 0:
                    metadata['compression_ratio'] = round(
                        (1 - metadata['compressed_size'] / metadata['uncompressed_size']) * 100, 2
                    )
                
                # File details
                for file_info in file_list:
                    metadata['files_info'].append({
                        'filename': file_info.filename,
                        'file_size': file_info.file_size,
                        'compress_size': file_info.compress_size,
                        'date_time': datetime(*file_info.date_time).strftime('%Y-%m-%d %H:%M:%S'),
                        'is_dir': file_info.is_dir(),
                        'crc': file_info.CRC
                    })
                
                return metadata
                
        except Exception as e:
            return {
                'error': f"Failed to analyze ZIP metadata: {str(e)}",
                'file_name': os.path.basename(target_path) if target_path else 'Unknown',
                'file_path': target_path or 'Unknown'
            }
    
    def check_extraction_capability(self, zip_path: Optional[str] = None) -> Dict[str, Any]:
        """Test ZIP extraction capability"""
        target_path = zip_path or self.zip_path
        if not target_path:
            return {'error': 'No ZIP path provided'}
            
        try:
            with zipfile.ZipFile(target_path, 'r') as zf:
                # Test if ZIP can be opened and read
                file_list = zf.infolist()
                
                # Try to read a small file to test extraction
                test_results = {
                    'can_open': True,
                    'can_list_files': True,
                    'total_files': len(file_list),
                    'extractable_files': 0,
                    'corrupted_files': [],
                    'extraction_errors': []
                }
                
                # Test extraction of first few files
                for i, file_info in enumerate(file_list[:5]):  # Test first 5 files
                    if not file_info.is_dir():
                        try:
                            with zf.open(file_info) as f:
                                # Try to read first 1KB
                                f.read(1024)
                            test_results['extractable_files'] += 1
                        except Exception as e:
                            test_results['corrupted_files'].append(file_info.filename)
                            test_results['extraction_errors'].append(str(e))
                
                return test_results
                
        except Exception as e:
            return {
                'can_open': False,
                'error': str(e),
                'extraction_capability': 'Failed'
            }
    
    def check_corruption(self, zip_path: Optional[str] = None) -> Dict[str, Any]:
        """Check ZIP file for corruption"""
        target_path = zip_path or self.zip_path
        if not target_path:
            return {'error': 'No ZIP path provided'}
            
        try:
            with zipfile.ZipFile(target_path, 'r') as zf:
                # Test ZIP integrity
                bad_files = zf.testzip()
                
                corruption_status = {
                    'is_corrupted': bad_files is not None,
                    'corrupted_file': bad_files if bad_files else None,
                    'integrity_check': 'Passed' if bad_files is None else 'Failed',
                    'test_method': 'zipfile.testzip()'
                }
                
                return corruption_status
                
        except Exception as e:
            return {
                'is_corrupted': True,
                'error': str(e),
                'integrity_check': 'Failed',
                'test_method': 'Exception during test'
            }
    
    def analyze_bak_files(self, zip_path: Optional[str] = None) -> Dict[str, Any]:
        """Analyze BAK files within the ZIP"""
        target_path = zip_path or self.zip_path
        if not target_path:
            return {'error': 'No ZIP path provided'}
            
        bak_analysis = {
            'bak_files_found': [],
            'total_bak_files': 0,
            'bak_analyses': {},
            'restore_capability': 'Unknown'
        }
        
        try:
            with zipfile.ZipFile(target_path, 'r') as zf:
                # Find BAK files
                for file_info in zf.infolist():
                    if file_info.filename.lower().endswith('.bak') and not file_info.is_dir():
                        bak_analysis['bak_files_found'].append(file_info.filename)
                
                bak_analysis['total_bak_files'] = len(bak_analysis['bak_files_found'])
                
                # Analyze each BAK file
                with tempfile.TemporaryDirectory() as temp_dir:
                    for bak_file in bak_analysis['bak_files_found'][:3]:  # Analyze first 3 BAK files
                        try:
                            # Extract BAK file to temp directory
                            zf.extract(bak_file, temp_dir)
                            bak_path = os.path.join(temp_dir, bak_file)
                            
                            # Analyze with BAKMetadataAnalyzer
                            analyzer = BAKMetadataAnalyzer(bak_path)
                            analysis = analyzer.analyze()
                            
                            bak_analysis['bak_analyses'][bak_file] = analysis
                            
                        except Exception as e:
                            bak_analysis['bak_analyses'][bak_file] = {
                                'error': f"Failed to analyze {bak_file}: {str(e)}"
                            }
                
                # Determine overall restore capability
                if bak_analysis['total_bak_files'] > 0:
                    valid_baks = sum(1 for analysis in bak_analysis['bak_analyses'].values() 
                                   if analysis.get('is_valid_backup', False))
                    if valid_baks > 0:
                        bak_analysis['restore_capability'] = f"Possible ({valid_baks}/{bak_analysis['total_bak_files']} valid BAK files)"
                    else:
                        bak_analysis['restore_capability'] = "Unlikely (No valid BAK files found)"
                else:
                    bak_analysis['restore_capability'] = "No BAK files found"
                
                return bak_analysis
                
        except Exception as e:
            bak_analysis['error'] = str(e)
            return bak_analysis


class PDFReportGenerator:
    """Generate comprehensive PDF reports for backup analysis"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkgreen
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.darkred
        ))
    
    def generate_report(self, zip_files: List[str], output_path: str) -> bool:
        """Generate comprehensive PDF report for selected ZIP files"""
        try:
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            story = []
            
            # Title page
            story.append(Paragraph("Laporan Analisis Backup Database", self.styles['CustomTitle']))
            story.append(Spacer(1, 20))
            story.append(Paragraph(f"Tanggal: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles['Normal']))
            story.append(Paragraph(f"Total File: {len(zip_files)}", self.styles['Normal']))
            story.append(PageBreak())
            
            # Process each ZIP file
            for i, zip_path in enumerate(zip_files, 1):
                story.extend(self._generate_zip_report(zip_path, i))
                if i < len(zip_files):
                    story.append(PageBreak())
            
            # Build PDF
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"Error generating PDF report: {str(e)}")
            return False
    
    def _generate_zip_report(self, zip_path: str, file_number: int) -> List:
        """Generate report section for a single ZIP file"""
        story = []
        analyzer = ZipAnalyzer(zip_path)
        
        # Section title
        story.append(Paragraph(f"{file_number}. Analisis File: {os.path.basename(zip_path)}", 
                              self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # 1. ZIP Metadata Summary
        story.append(Paragraph("1. Summary Metadata File ZIP", self.styles['SectionHeader']))
        metadata = analyzer.analyze_zip_metadata()
        story.extend(self._create_metadata_section(metadata))
        
        # 2. ZIP Backup Analysis Summary
        story.append(Paragraph("2. Analisis Detail File ZIP Backup", self.styles['SectionHeader']))
        
        # Extraction capability
        story.append(Paragraph("2.1 Kemampuan Ekstraksi", self.styles['SubHeader']))
        extraction = analyzer.check_extraction_capability()
        story.extend(self._create_extraction_section(extraction))
        
        # Corruption status
        story.append(Paragraph("2.2 Status Corrupt", self.styles['SubHeader']))
        corruption = analyzer.check_corruption()
        story.extend(self._create_corruption_section(corruption))
        
        # BAK validity and restore capability
        story.append(Paragraph("2.3 Kemampuan Restore & Validitas BAK", self.styles['SubHeader']))
        bak_analysis = analyzer.analyze_bak_files()
        story.extend(self._create_bak_validity_section(bak_analysis))
        
        # 3. Detailed BAK Analysis
        story.append(Paragraph("3. Analisis BAK Detail", self.styles['SectionHeader']))
        story.extend(self._create_detailed_bak_section(bak_analysis))
        
        return story
    
    def _create_metadata_section(self, metadata: Dict[str, Any]) -> List:
        """Create metadata section"""
        story = []
        
        if 'error' in metadata:
            story.append(Paragraph(f"Error: {metadata['error']}", self.styles['Normal']))
            return story
        
        # Create metadata table
        data = [
            ['Properti', 'Nilai'],
            ['Nama File', metadata.get('file_name', 'N/A')],
            ['Ukuran File', f"{metadata.get('file_size_mb', 0)} MB ({metadata.get('file_size_bytes', 0):,} bytes)"],
            ['Tanggal Dibuat', metadata.get('created_date', 'N/A')],
            ['Tanggal Dimodifikasi', metadata.get('modified_date', 'N/A')],
            ['Total File dalam ZIP', str(metadata.get('total_files', 0))],
            ['Ukuran Terkompresi', f"{metadata.get('compressed_size', 0):,} bytes"],
            ['Ukuran Tidak Terkompresi', f"{metadata.get('uncompressed_size', 0):,} bytes"],
            ['Rasio Kompresi', f"{metadata.get('compression_ratio', 0)}%"]
        ]
        
        table = Table(data, colWidths=[2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 12))
        
        return story
    
    def _create_extraction_section(self, extraction: Dict[str, Any]) -> List:
        """Create extraction capability section"""
        story = []
        
        if 'error' in extraction:
            story.append(Paragraph(f"Status: <b>Gagal</b> - {extraction['error']}", self.styles['Normal']))
        else:
            can_open = extraction.get('can_open', False)
            extractable = extraction.get('extractable_files', 0)
            total = extraction.get('total_files', 0)
            
            status = "Berhasil" if can_open and extractable > 0 else "Gagal"
            story.append(Paragraph(f"Status Ekstraksi: <b>{status}</b>", self.styles['Normal']))
            story.append(Paragraph(f"File yang dapat diekstrak: {extractable}/{total}", self.styles['Normal']))
            
            if extraction.get('corrupted_files'):
                story.append(Paragraph("File yang rusak:", self.styles['Normal']))
                for corrupted in extraction['corrupted_files']:
                    story.append(Paragraph(f"• {corrupted}", self.styles['Normal']))
        
        story.append(Spacer(1, 8))
        return story
    
    def _create_corruption_section(self, corruption: Dict[str, Any]) -> List:
        """Create corruption status section"""
        story = []
        
        if 'error' in corruption:
            story.append(Paragraph(f"Status: <b>Error</b> - {corruption['error']}", self.styles['Normal']))
        else:
            is_corrupted = corruption.get('is_corrupted', True)
            status = "Rusak" if is_corrupted else "Baik"
            story.append(Paragraph(f"Status Integritas: <b>{status}</b>", self.styles['Normal']))
            story.append(Paragraph(f"Hasil Test: {corruption.get('integrity_check', 'N/A')}", self.styles['Normal']))
            
            if corruption.get('corrupted_file'):
                story.append(Paragraph(f"File rusak: {corruption['corrupted_file']}", self.styles['Normal']))
        
        story.append(Spacer(1, 8))
        return story
    
    def _create_bak_validity_section(self, bak_analysis: Dict[str, Any]) -> List:
        """Create BAK validity section"""
        story = []
        
        total_bak = bak_analysis.get('total_bak_files', 0)
        story.append(Paragraph(f"Total File BAK: <b>{total_bak}</b>", self.styles['Normal']))
        story.append(Paragraph(f"Kemampuan Restore: <b>{bak_analysis.get('restore_capability', 'Unknown')}</b>", self.styles['Normal']))
        
        if bak_analysis.get('bak_files_found'):
            story.append(Paragraph("File BAK yang ditemukan:", self.styles['Normal']))
            for bak_file in bak_analysis['bak_files_found']:
                story.append(Paragraph(f"• {bak_file}", self.styles['Normal']))
        
        story.append(Spacer(1, 8))
        return story
    
    def _create_detailed_bak_section(self, bak_analysis: Dict[str, Any]) -> List:
        """Create detailed BAK analysis section"""
        story = []
        
        if not bak_analysis.get('bak_analyses'):
            story.append(Paragraph("Tidak ada file BAK untuk dianalisis.", self.styles['Normal']))
            return story
        
        for bak_file, analysis in bak_analysis.get('bak_analyses', {}).items():
            story.append(Paragraph(f"3.{list(bak_analysis['bak_analyses'].keys()).index(bak_file) + 1} Analisis {bak_file}", self.styles['SubHeader']))
            
            if 'error' in analysis:
                story.append(Paragraph(f"Error: {analysis['error']}", self.styles['Normal']))
                continue
            
            # Create BAK analysis table
            data = [
                ['Properti', 'Nilai'],
                ['Validitas BAK', 'Valid' if analysis.get('is_valid_backup', False) else 'Tidak Valid'],
                ['Kemampuan Restore', 'Mungkin' if analysis.get('is_valid_backup', False) else 'Tidak Mungkin'],
                ['Ukuran File', f"{analysis.get('file_size_mb', 0)} MB"],
                ['Signature', analysis.get('signature', 'N/A')],
                ['Header Size', f"{analysis.get('header_size', 0)} bytes"],
                ['Data Blocks', str(analysis.get('data_blocks', 0))],
                ['Page Count', str(analysis.get('page_count', 0))],
                ['Estimated Backup Sets', str(analysis.get('estimated_backup_sets', 0))],
                ['Corruption Check', analysis.get('corruption_check', 'N/A')]
            ]
            
            table = Table(data, colWidths=[2*inch, 3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            story.append(Spacer(1, 12))
        
        return story


def main():
    """Test the PDF report generator"""
    # Test with sample ZIP files
    test_zip_files = [
        r"D:\Gawean Rebinmas\App_Auto_Backup\Notiikasi_Database\BackupStaging.zip"
    ]
    
    generator = PDFReportGenerator()
    output_path = "test_backup_report.pdf"
    
    success = generator.generate_report(test_zip_files, output_path)
    if success:
        print(f"PDF report generated successfully: {output_path}")
    else:
        print("Failed to generate PDF report")


if __name__ == "__main__":
    main()