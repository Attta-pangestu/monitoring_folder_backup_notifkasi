#!/usr/bin/env python3
"""
Test script untuk analisis BAK file menggunakan BAKMetadataAnalyzer
"""

import os
import sys
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bak_metadata_analyzer import BAKMetadataAnalyzer

def test_bak_analysis():
    """Test analisis BAK file"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    # Path ke file BAK yang sudah diekstrak
    bak_file_path = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup\BackupStaging.bak"
    
    if not os.path.exists(bak_file_path):
        logger.error(f"File BAK tidak ditemukan: {bak_file_path}")
        return
    
    logger.info(f"Menganalisis file BAK: {bak_file_path}")
    logger.info(f"Ukuran file: {os.path.getsize(bak_file_path):,} bytes")
    
    # Inisialisasi analyzer
    analyzer = BAKMetadataAnalyzer()
    
    try:
        # Analisis file BAK
        result = analyzer.analyze_bak_file(bak_file_path)
        
        logger.info("=== HASIL ANALISIS BAK FILE ===")
        logger.info(f"File: {result.get('file_path', 'N/A')}")
        logger.info(f"Ukuran: {result.get('file_size', 0):,} bytes")
        logger.info(f"Status Analisis: {result.get('analysis_status', 'N/A')}")
        logger.info(f"Valid BAK File: {result.get('is_valid_bak', False)}")
        
        # Informasi struktur file
        if 'file_structure' in result:
            structure = result['file_structure']
            logger.info("\n=== STRUKTUR FILE ===")
            logger.info(f"Header Size: {structure.get('header_size', 0)} bytes")
            logger.info(f"Data Blocks: {structure.get('data_blocks', 0)}")
            logger.info(f"Page Count: {structure.get('page_count', 0)}")
            logger.info(f"Estimated Backup Sets: {structure.get('estimated_backup_sets', 0)}")
        
        # Informasi validasi
        if 'validation' in result:
            validation = result['validation']
            logger.info("\n=== VALIDASI ===")
            logger.info(f"Has SQL Server Signature: {validation.get('has_sql_server_signature', False)}")
            logger.info(f"Has Backup Header: {validation.get('has_backup_header', False)}")
            logger.info(f"Corruption Detected: {validation.get('corruption_detected', False)}")
        
        # Informasi database (jika tersedia)
        if 'database_info' in result:
            db_info = result['database_info']
            logger.info("\n=== INFORMASI DATABASE ===")
            logger.info(f"Database Name: {db_info.get('database_name', 'N/A')}")
            logger.info(f"Server Name: {db_info.get('server_name', 'N/A')}")
            logger.info(f"Backup Date: {db_info.get('backup_date', 'N/A')}")
            logger.info(f"Backup Type: {db_info.get('backup_type', 'N/A')}")
        
        # Error jika ada
        if 'error' in result:
            logger.error(f"Error: {result['error']}")
            
    except Exception as e:
        logger.error(f"Error saat menganalisis file BAK: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    test_bak_analysis()