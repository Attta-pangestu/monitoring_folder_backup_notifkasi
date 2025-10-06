import pyodbc
import subprocess

# Test different connection methods to the restored database
db_name = "D_Drive_Staging_DB"
server = "localhost"
username = "sa"
password = "windows0819"

print(f"Testing connections to database: {db_name}")

# First, verify the database exists
print("Step 1: Verifying database exists...")
check_cmd = f'sqlcmd -S localhost -U sa -P windows0819 -Q "SELECT name FROM sys.databases WHERE name = \'{db_name}\'" -h -1'
check_result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
print(f'Database check result: "{check_result.stdout.strip()}"')

if db_name in check_result.stdout:
    print("Database exists! Testing connection methods...")
    
    # Test 1: Basic connection string
    print("\nTest 1: Basic ODBC connection string")
    try:
        conn_str = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={db_name};UID={username};PWD={password};Trusted_Connection=no'
        print(f"Connection string: {conn_str}")
        conn = pyodbc.connect(conn_str)
        print("SUCCESS: Basic connection works!")
        conn.close()
    except Exception as e:
        print(f"FAILED: {e}")
    
    # Test 2: With explicit port
    print("\nTest 2: Connection with explicit port")
    try:
        conn_str = f'DRIVER={{SQL Server}};SERVER={server},1433;DATABASE={db_name};UID={username};PWD={password};Trusted_Connection=no'
        print(f"Connection string: {conn_str}")
        conn = pyodbc.connect(conn_str)
        print("SUCCESS: Connection with port works!")
        conn.close()
    except Exception as e:
        print(f"FAILED: {e}")
    
    # Test 3: With timeout
    print("\nTest 3: Connection with timeout")
    try:
        conn_str = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={db_name};UID={username};PWD={password};Trusted_Connection=no;Connection Timeout=30'
        print(f"Connection string: {conn_str}")
        conn = pyodbc.connect(conn_str)
        print("SUCCESS: Connection with timeout works!")
        conn.close()
    except Exception as e:
        print(f"FAILED: {e}")
    
    # Test 4: ODBC Driver 17 for SQL Server
    print("\nTest 4: ODBC Driver 17 for SQL Server")
    try:
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={db_name};UID={username};PWD={password};Trusted_Connection=no'
        print(f"Connection string: {conn_str}")
        conn = pyodbc.connect(conn_str)
        print("SUCCESS: ODBC Driver 17 works!")
        conn.close()
    except Exception as e:
        print(f"FAILED: {e}")
    
    # Test 5: SQL Server Native Client
    print("\nTest 5: SQL Server Native Client")
    try:
        conn_str = f'DRIVER={{SQL Server Native Client 11.0}};SERVER={server};DATABASE={db_name};UID={username};PWD={password};Trusted_Connection=no'
        print(f"Connection string: {conn_str}")
        conn = pyodbc.connect(conn_str)
        print("SUCCESS: Native Client works!")
        conn.close()
    except Exception as e:
        print(f"FAILED: {e}")
    
    # Test 6: Check available drivers
    print("\nTest 6: Available ODBC drivers")
    drivers = pyodbc.drivers()
    print("Available drivers:")
    for driver in drivers:
        print(f"  - {driver}")
    
    # Test 7: Test with DateExtractionMicroFeature
    print("\nTest 7: DateExtractionMicroFeature connection")
    try:
        from date_extraction_micro_feature import DateExtractionMicroFeature
        
        date_extractor = DateExtractionMicroFeature(db_name)
        connection = date_extractor.get_database_connection()
        
        if connection:
            print('SUCCESS: DateExtractionMicroFeature can connect!')
            connection.close()
        else:
            print('FAILED: DateExtractionMicroFeature cannot connect')
    except Exception as e:
        print(f'ERROR in DateExtractionMicroFeature: {e}')
        
else:
    print("Database does not exist!")