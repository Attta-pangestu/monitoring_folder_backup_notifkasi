#!/usr/bin/env python3
"""
Test script for PDF report generation system
"""

from src.pdf_report_generator import PDFReportGenerator, ZipAnalyzer
import os

def test_pdf_system():
    """Test the complete PDF report system"""
    print("Testing PDF Report System...")
    print("=" * 50)
    
    # Test ZipAnalyzer with TestBackup.zip
    print("1. Testing ZipAnalyzer...")
    analyzer = ZipAnalyzer()
    
    # Test metadata analysis
    metadata = analyzer.analyze_zip_metadata('TestBackup.zip')
    metadata_success = bool(metadata and "error" not in metadata)
    print(f"   Metadata analysis: {'✓ PASS' if metadata_success else '✗ FAIL'}")
    
    if metadata_success:
        print(f"   - File: {metadata.get('file_name', 'N/A')}")
        print(f"   - Size: {metadata.get('file_size_mb', 0)} MB")
        print(f"   - Files: {metadata.get('total_files', 0)}")
    
    # Test extraction capability
    extraction_result = analyzer.check_extraction_capability('TestBackup.zip')
    extraction_success = bool(extraction_result and "error" not in extraction_result)
    print(f"   Extraction check: {'✓ PASS' if extraction_success else '✗ FAIL'}")
    
    if extraction_success:
        print(f"   - Can open: {extraction_result.get('can_open', False)}")
        print(f"   - Extractable files: {extraction_result.get('extractable_files', 0)}")
    
    # Test corruption check
    corruption_result = analyzer.check_corruption('TestBackup.zip')
    corruption_success = bool(corruption_result and "error" not in corruption_result)
    print(f"   Corruption check: {'✓ PASS' if corruption_success else '✗ FAIL'}")
    
    if corruption_success:
        print(f"   - Is corrupted: {corruption_result.get('is_corrupted', 'Unknown')}")
        print(f"   - Integrity: {corruption_result.get('integrity_check', 'Unknown')}")
    
    print("\n2. Testing PDF generation...")
    generator = PDFReportGenerator()
    result = generator.generate_report(['TestBackup.zip'], 'test_complete_report.pdf')
    pdf_success = bool(result)
    print(f"   PDF generation: {'✓ PASS' if pdf_success else '✗ FAIL'}")
    
    if pdf_success and os.path.exists('test_complete_report.pdf'):
        size = os.path.getsize('test_complete_report.pdf')
        print(f"   - Generated PDF size: {size} bytes")
        print(f"   - File location: test_complete_report.pdf")
    
    print("\n" + "=" * 50)
    overall_success = metadata_success and extraction_success and corruption_success and pdf_success
    print(f"Overall Test Result: {'✓ ALL TESTS PASSED' if overall_success else '✗ SOME TESTS FAILED'}")
    
    return overall_success

if __name__ == "__main__":
    test_pdf_system()