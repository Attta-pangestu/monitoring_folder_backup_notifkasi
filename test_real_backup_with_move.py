from sql_server_zip_restore import SQLServerZipRestore
import subprocess

# Test with real backup file using the proper restore method
backup_file = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup\BackupStaging 2025-10-04 09;16;30.zip"
print(f"Testing with real backup file: {backup_file}")

try:
    # Create restorer and use the proper restore method
    restorer = SQLServerZipRestore()
    restorer.keep_database = True  # Make sure we keep the database
    
    # Extract and restore using the proper method
    bak_path = restorer.extract_zip_file(backup_file)
    print(f'BAK file extracted to: {bak_path}')
    
    # Use the restore_database method which handles WITH MOVE
    db_name = restorer.restore_database(bak_path, "Test_Real_Staging_DB")
    print(f'Database restored as: {db_name}')
    
    # Check if database exists
    check_cmd = f'sqlcmd -S localhost -U sa -P windows0819 -Q "SELECT name FROM sys.databases WHERE name = \'{db_name}\'" -h -1'
    check_result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
    print(f'Database check result: {check_result.stdout.strip()}')
    
    if db_name in check_result.stdout:
        print('SUCCESS: Database was restored and persists!')
        
        # Try to connect with DateExtractionMicroFeature
        from date_extraction_micro_feature import DateExtractionMicroFeature
        
        date_extractor = DateExtractionMicroFeature(db_name)
        connection = date_extractor.get_database_connection()
        
        if connection:
            print('SUCCESS: DateExtractionMicroFeature can connect to the restored database!')
            connection.close()
        else:
            print('FAILED: DateExtractionMicroFeature cannot connect to the restored database')
    else:
        print('FAILED: Database was not found after restore')
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()