from sql_server_zip_restore import SQLServerZipRestore
import subprocess

# Create restorer and extract BAK file
restorer = SQLServerZipRestore()
bak_path = restorer.extract_zip_file('real_test_backups/plantware_backup_2025-10-05.zip')
print(f'BAK file extracted to: {bak_path}')

# Try manual restore with detailed output
db_name = 'Test_Restored_DB_Manual'
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