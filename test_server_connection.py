import subprocess
import pyodbc

print("=== SQL Server Connection Diagnostics ===")

# Test 1: Check SQL Server services
print("\nStep 1: Checking SQL Server services...")
try:
    services_cmd = 'sc query type= service state= all | findstr /i "sql"'
    services_result = subprocess.run(services_cmd, shell=True, capture_output=True, text=True)
    print("SQL Server related services:")
    print(services_result.stdout)
except Exception as e:
    print(f"Error checking services: {e}")

# Test 2: Check SQL Server instances
print("\nStep 2: Checking SQL Server instances...")
try:
    instances_cmd = 'sqlcmd -L'
    instances_result = subprocess.run(instances_cmd, shell=True, capture_output=True, text=True, timeout=10)
    print("Available SQL Server instances:")
    print(instances_result.stdout)
except Exception as e:
    print(f"Error checking instances: {e}")

# Test 3: Test different server names
print("\nStep 3: Testing different server connection strings...")

server_names = [
    "localhost",
    ".",
    "(local)",
    "127.0.0.1",
    "GM_ACC",  # Based on the error messages showing Server GM_ACC
    "GM_ACC\\SQLEXPRESS",
    "localhost\\SQLEXPRESS",
    ".\\SQLEXPRESS"
]

db_name = "D_Drive_Staging_DB"
username = "sa"
password = "windows0819"

for server in server_names:
    print(f"\nTesting server: {server}")
    try:
        # Test with ODBC Driver 17
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={db_name};UID={username};PWD={password};Trusted_Connection=no;Connection Timeout=5'
        conn = pyodbc.connect(conn_str)
        print(f"✓ SUCCESS: Connected to {server}")
        conn.close()
        break  # Stop at first successful connection
    except Exception as e:
        print(f"✗ FAILED: {server} - {str(e)[:100]}...")

# Test 4: Check if we can connect without specifying database
print(f"\nStep 4: Testing connection without specific database...")
for server in server_names:
    try:
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};UID={username};PWD={password};Trusted_Connection=no;Connection Timeout=5'
        conn = pyodbc.connect(conn_str)
        print(f"✓ SUCCESS: Connected to {server} (no database specified)")
        
        # Check if our database exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sys.databases WHERE name = ?", db_name)
        result = cursor.fetchone()
        if result:
            print(f"✓ Database '{db_name}' exists on {server}")
        else:
            print(f"✗ Database '{db_name}' not found on {server}")
        
        conn.close()
        break
    except Exception as e:
        print(f"✗ FAILED: {server} - {str(e)[:100]}...")

print("\n=== Diagnostics Complete ===")