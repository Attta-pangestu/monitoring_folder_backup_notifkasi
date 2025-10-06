from sql_server_zip_restore import SQLServerZipRestore
import subprocess
import time

# Debug the restore process step by step
backup_file = r"D:\Gawean Rebinmas\App_Auto_Backup\Backup\BackupStaging 2025-10-04 09;16;30.zip"
print(f"Debugging restore process with: {backup_file}")

try:
    # Create restorer
    restorer = SQLServerZipRestore()
    restorer.keep_database = True
    
    print("Step 1: Extracting ZIP file...")
    bak_path = restorer.extract_zip_file(backup_file)
    print(f'BAK file extracted to: {bak_path}')
    
    print("Step 2: Getting logical names...")
    data_file, log_file = restorer.get_backup_logical_names(bak_path)
    print(f'Data file logical name: {data_file}')
    print(f'Log file logical name: {log_file}')
    
    print("Step 3: Attempting restore...")
    db_name = "Debug_Staging_DB"
    
    # Create the restore command manually to see what's happening
    import os
    from datetime import datetime
    
    # Create directory for database files
    db_dir = "C:\\SQLData"
    if not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir)
            print(f"Created directory: {db_dir}")
        except Exception as e:
            print(f"Could not create directory {db_dir}: {e}")
            db_dir = None
    
    if db_dir:
        data_path = os.path.join(db_dir, f"{db_name}_Data.mdf")
        log_path = os.path.join(db_dir, f"{db_name}_Log.ldf")
        
        restore_cmd = f'''sqlcmd -S localhost -U sa -P windows0819 -Q "
        RESTORE DATABASE [{db_name}] FROM DISK = '{bak_path}' WITH 
        MOVE '{data_file}' TO '{data_path}',
        MOVE '{log_file}' TO '{log_path}',
        REPLACE"'''
        
        print(f"Restore command: {restore_cmd}")
        
        result = subprocess.run(restore_cmd, shell=True, capture_output=True, text=True, timeout=300)
        print(f'Restore return code: {result.returncode}')
        print(f'Restore STDOUT: {result.stdout}')
        print(f'Restore STDERR: {result.stderr}')
        
        if result.returncode == 0:
            print("Step 4: Restore completed successfully!")
            restorer.restored_db_name = db_name
            
            # Grant permissions
            print("Step 5: Granting permissions...")
            permission_cmd = f'''sqlcmd -S localhost -U sa -P windows0819 -Q "
            USE [{db_name}];
            IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'sa')
            BEGIN
                CREATE USER [sa] FOR LOGIN [sa];
            END
            ALTER ROLE db_owner ADD MEMBER [sa];"'''
            
            perm_result = subprocess.run(permission_cmd, shell=True, capture_output=True, text=True, timeout=30)
            print(f'Permission return code: {perm_result.returncode}')
            print(f'Permission STDOUT: {perm_result.stdout}')
            print(f'Permission STDERR: {perm_result.stderr}')
            
            # Check database immediately
            print("Step 6: Checking database existence...")
            check_cmd = f'sqlcmd -S localhost -U sa -P windows0819 -Q "SELECT name FROM sys.databases WHERE name = \'{db_name}\'" -h -1'
            check_result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
            print(f'Database check result: "{check_result.stdout.strip()}"')
            
            # Wait and check again
            print("Step 7: Waiting 2 seconds and checking again...")
            time.sleep(2)
            check_result2 = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
            print(f'Database check result after wait: "{check_result2.stdout.strip()}"')
            
            # Keep the restorer object alive
            print("Step 8: Keeping restorer object alive...")
            print(f"Restorer object: {restorer}")
            print(f"Restored DB name: {restorer.restored_db_name}")
            print(f"Keep database flag: {restorer.keep_database}")
            
        else:
            print("Restore failed!")
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()