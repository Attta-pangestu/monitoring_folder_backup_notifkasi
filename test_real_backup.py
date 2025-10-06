from sql_server_zip_restore import SQLServerZipRestore
import subprocess

# Test with real backup file
backup_file = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup\BackupStaging 2025-10-04 09;16;30.zip"
print(f"Testing with real backup file: {backup_file}")

try:
    # Create restorer and extract BAK file
    restorer = SQLServerZipRestore()
    bak_path = restorer.extract_zip_file(backup_file)
    print(f'BAK file extracted to: {bak_path}')
    
    # Check if BAK file exists and its size
    import os
    if os.path.exists(bak_path):
        size = os.path.getsize(bak_path)
        print(f'BAK file size: {size} bytes')
        
        # Try to get backup info first
        try:
            info_cmd = f'sqlcmd -S localhost -U sa -P windows0819 -Q "RESTORE HEADERONLY FROM DISK = \'{bak_path}\'" -h -1'
            info_result = subprocess.run(info_cmd, shell=True, capture_output=True, text=True, timeout=60)
            print(f'Backup header info return code: {info_result.returncode}')
            if info_result.returncode == 0:
                print('Backup file is valid!')
                print(f'Header info: {info_result.stdout[:200]}...')
            else:
                print(f'Backup header error: {info_result.stderr}')
        except Exception as e:
            print(f'Error checking backup header: {e}')
        
        # Try manual restore
        db_name = 'Test_Real_Backup_DB'
        restore_cmd = f'sqlcmd -S localhost -U sa -P windows0819 -Q "RESTORE DATABASE [{db_name}] FROM DISK = \'{bak_path}\' WITH REPLACE"'
        print(f'Restore command: {restore_cmd}')
        
        result = subprocess.run(restore_cmd, shell=True, capture_output=True, text=True, timeout=300)
        print(f'Return code: {result.returncode}')
        print(f'STDOUT: {result.stdout}')
        print(f'STDERR: {result.stderr}')
        
        # Check if database exists
        check_cmd = f'sqlcmd -S localhost -U sa -P windows0819 -Q "SELECT name FROM sys.databases WHERE name = \'{db_name}\'" -h -1'
        check_result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        print(f'Database check result: {check_result.stdout}')
        
    else:
        print('BAK file not found after extraction!')
        
except Exception as e:
    print(f'Error: {e}')