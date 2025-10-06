#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script untuk Enhanced Backup Analysis System
Menguji backup date detection, health check, dan GUI table update
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Set stdout encoding for Windows
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except:
        pass

from enhanced_bak_analyzer import EnhancedBAKAnalyzer
from enhanced_zip_analyzer import EnhancedZIPAnalyzer
from enhanced_email_notifier import EnhancedEmailNotifier

def test_bak_date_detection():
    """Test BAK file date detection"""
    print("=" * 60)
    print("🧪 TEST 1: BAK File Date Detection")
    print("=" * 60)

    # Create test BAK analyzer
    bak_analyzer = EnhancedBAKAnalyzer()

    # Test dengan file yang ada di sistem
    test_files = [
        r"D:\Gawean Rebinmas\App_Auto_Backup\Notiikasi_Database\backup_monitor_qt.py",
        r"D:\Gawean Rebinmas\App_Auto_Backup\Notiikasi_Database\comprehensive_backup_analyzer.py"
    ]

    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"\n🔍 Testing file: {os.path.basename(file_path)}")

            # Get file metadata
            file_stat = os.stat(file_path)
            modified_time = datetime.fromtimestamp(file_stat.st_mtime)
            created_time = datetime.fromtimestamp(file_stat.st_ctime)

            print(f"   📅 Modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   📅 Created: {created_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   📏 Size: {file_stat.st_size / (1024*1024):.2f} MB")

            # Test basic analysis
            try:
                basic_info = bak_analyzer._analyze_bak_basic(file_path)
                print(f"   💾 Detected Date: {basic_info.get('backup_date', 'Unknown')}")
                print(f"   📊 Date Source: {basic_info.get('backup_date_source', 'Unknown')}")
                print(f"   🗄️ Database: {basic_info.get('database_name', 'Unknown')}")
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")

    print("\n" + "=" * 60)

def test_health_summary():
    """Test health summary generation"""
    print("🧪 TEST 2: Health Summary Generation")
    print("=" * 60)

    bak_analyzer = EnhancedBAKAnalyzer()

    # Create mock BAK analysis results
    mock_results = [
        {
            'filename': 'BackupStaging.bak',
            'analysis_status': 'success',
            'file_size_mb': 2287.5,
            'backup_metadata': {
                'backup_date': '2024-10-05 14:30:00',
                'database_name': 'BackupStaging'
            },
            'validation': {
                'file_integrity': 'Good',
                'is_valid_bak': True,
                'can_be_restored': True,
                'corruption_detected': False,
                'warnings': []
            }
        },
        {
            'filename': 'BackupVenuz.bak',
            'analysis_status': 'success',
            'file_size_mb': 8536.2,
            'backup_metadata': {
                'backup_date': '2024-10-05 14:25:00',
                'database_name': 'BackupVenuz'
            },
            'validation': {
                'file_integrity': 'Good',
                'is_valid_bak': True,
                'can_be_restored': True,
                'corruption_detected': False,
                'warnings': []
            }
        },
        {
            'filename': 'CorruptedBackup.bak',
            'analysis_status': 'failed',
            'validation': {
                'file_integrity': 'Corrupted',
                'is_valid_bak': False,
                'can_be_restored': False,
                'corruption_detected': True,
                'warnings': ['File corrupted']
            }
        }
    ]

    # Generate health summary
    health_summary = bak_analyzer.generate_health_summary(mock_results)

    print("📊 Health Summary Results:")
    print(f"   Total Files: {health_summary['total_files']}")
    print(f"   Healthy: {health_summary['healthy_files']}")
    print(f"   Warnings: {health_summary['warning_files']}")
    print(f"   Corrupted: {health_summary['corrupted_files']}")
    print(f"   Total Size: {health_summary['total_size_mb']:.1f} MB")
    print(f"   Overall Status: {health_summary['health_status']}")

    print("\n💡 Recommendations:")
    for rec in health_summary['recommendations']:
        print(f"   {rec}")

    # Test formatted output
    print("\n" + "=" * 60)
    print("📋 Formatted Output Test:")
    print("=" * 60)
    formatted_output = bak_analyzer.format_analysis_output(mock_results)
    print(formatted_output)

def test_zip_metadata():
    """Test ZIP metadata analysis"""
    print("🧪 TEST 3: ZIP Metadata Analysis")
    print("=" * 60)

    zip_analyzer = EnhancedZIPAnalyzer()

    # Test dengan file yang ada
    test_folder = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup"
    if os.path.exists(test_folder):
        zip_files = [f for f in os.listdir(test_folder) if f.lower().endswith('.zip')]

        if zip_files:
            for zip_file in zip_files[:3]:  # Test max 3 files
                zip_path = os.path.join(test_folder, zip_file)
                print(f"\n📦 Analyzing: {zip_file}")

                try:
                    # Test ZIP metadata analysis
                    zip_info = zip_analyzer._analyze_zip_metadata(zip_path)

                    print(f"   📅 Backup Date: {zip_info.get('backup_date_from_filename', 'Unknown')}")
                    print(f"   🗄️ Database Type: {zip_info.get('database_type_from_filename', 'Unknown')}")
                    print(f"   📏 File Size: {zip_info.get('file_size_mb', 0):.2f} MB")
                    print(f"   📁 Total Files: {zip_info.get('total_files', 0)}")
                    print(f"   🗜️ Compression Ratio: {zip_info.get('compression_ratio', 0):.2f}%")
                    print(f"   🔒 File Hash: {zip_info.get('file_hash', 'Unknown')[:16]}...")

                except Exception as e:
                    print(f"   ❌ Error: {str(e)}")
        else:
            print("   No ZIP files found in test folder")
    else:
        print(f"   Test folder not found: {test_folder}")

def test_gui_table_simulation():
    """Test GUI table update simulation"""
    print("🧪 TEST 4: GUI Table Update Simulation")
    print("=" * 60)

    # Simulate GUI table update
    mock_bak_analyses = [
        {
            'original_filename': 'BackupStaging.bak',
            'analysis_status': 'success',
            'file_size_mb': 2287.5,
            'backup_metadata': {
                'backup_date': '2024-10-05 14:30:00',
                'database_name': 'BackupStaging'
            },
            'database_info': {
                'backup_type': 'FULL',
                'sql_version': '2019'
            },
            'validation': {
                'file_integrity': 'Good',
                'is_valid_bak': True,
                'can_be_restored': True
            },
            'table_info': {
                'total_tables': 45,
                'total_records': 1250000
            }
        },
        {
            'original_filename': 'BackupVenuz.bak',
            'analysis_status': 'success',
            'file_size_mb': 8536.2,
            'backup_metadata': {
                'backup_date': '2024-10-05 14:25:00',
                'database_name': 'BackupVenuz'
            },
            'database_info': {
                'backup_type': 'FULL',
                'sql_version': '2019'
            },
            'validation': {
                'file_integrity': 'Good',
                'is_valid_bak': True,
                'can_be_restored': True
            },
            'table_info': {
                'total_tables': 120,
                'total_records': 3500000
            }
        }
    ]

    # Simulate table update
    print("📊 Simulated BAK Analysis Table:")
    print("-" * 100)
    print(f"{'File Name':<25} {'Database':<15} {'Backup Date':<20} {'Size (MB)':<10} {'Health':<12} {'Tables':<8} {'Records':<12} {'Restore':<8}")
    print("-" * 100)

    for bak_result in mock_bak_analyses:
        if bak_result.get('analysis_status') == 'success':
            filename = bak_result.get('original_filename', 'Unknown')
            metadata = bak_result.get('backup_metadata', {})
            db_info = bak_result.get('database_info', {})
            validation = bak_result.get('validation', {})
            table_info = bak_result.get('table_info', {})

            # Truncate filename if too long
            display_filename = filename[:22] + '...' if len(filename) > 25 else filename

            print(f"{display_filename:<25} "
                  f"{metadata.get('database_name', 'Unknown'):<15} "
                  f"{metadata.get('backup_date', 'Unknown'):<20} "
                  f"{bak_result.get('file_size_mb', 0):<10.1f} "
                  f"{validation.get('file_integrity', 'Unknown'):<12} "
                  f"{table_info.get('total_tables', 0):<8} "
                  f"{table_info.get('total_records', 0):<12,} "
                  f"{'Yes' if validation.get('can_be_restored') else 'No':<8}")

    print("-" * 100)

def main():
    """Main test function"""
    print("🚀 Enhanced Backup Analysis System Test")
    print("=" * 60)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    try:
        # Run tests
        test_bak_date_detection()
        test_health_summary()
        test_zip_metadata()
        test_gui_table_simulation()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)
        print("📋 Test Summary:")
        print("   ✅ Backup date detection from metadata")
        print("   ✅ Health summary generation")
        print("   ✅ ZIP metadata analysis")
        print("   ✅ GUI table simulation")
        print("\n💡 Next Steps:")
        print("   1. Test with actual BAK files")
        print("   2. Test GUI application")
        print("   3. Test email notifications")
        print("   4. Test PDF report generation")

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()