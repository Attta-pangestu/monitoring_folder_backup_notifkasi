import pyodbc
import json
from datetime import datetime
import numpy as np
from decimal import Decimal

# SQL Server connection details
server = 'localhost'
username = 'sa'
password = 'windows0819'

try:
    # Create connection string
    conn_str = f'DRIVER={{SQL Server}};SERVER={server};UID={username};PWD={password}'
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    print('Connected to SQL Server successfully')

    # Get list of databases
    cursor.execute('SELECT name FROM sys.databases')
    databases = [row[0] for row in cursor.fetchall()]
    print(f'Available databases: {databases}')

    # Check specific databases mentioned
    target_dbs = ['staging_PTRJ_iFES_Plantware', 'db_ptrj', 'VenusHR14']
    available_dbs = [db for db in target_dbs if db in databases]
    print(f'Target databases available: {available_dbs}')

    # Initialize results dictionary
    results = {
        'timestamp': datetime.now().isoformat(),
        'databases': {}
    }

    # Analyze each database
    for db_name in available_dbs:
        print(f'\nAnalyzing database: {db_name}')
        cursor.execute(f'USE {db_name}')

        # Get tables
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f'Tables in {db_name}: {tables}')

        db_info = {
            'tables': {}
        }

        # Check specific tables
        if db_name == 'staging_PTRJ_iFES_Plantware':
            target_tables = ['Gwscannerdata', 'Ffbscannerdata', 'Gwcanner', 'FFBscnner']
            for table in target_tables:
                if table in tables:
                    print(f'\nAnalyzing table: {table}')

                    # Get column info
                    cursor.execute(f"""
                        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_NAME = '{table}'
                        ORDER BY ORDINAL_POSITION
                    """)
                    columns = cursor.fetchall()

                    # Get row count
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    row_count = cursor.fetchone()[0]

                    # Get sample data (first 5 rows)
                    cursor.execute(f'SELECT TOP 5 * FROM {table}')
                    sample_data = cursor.fetchall()

                    db_info['tables'][table] = {
                        'columns': [(col[0], col[1], col[2], col[3]) for col in columns],
                        'row_count': row_count,
                        'sample_data': [list(row) for row in sample_data]
                    }
                    print(f'Table {table} has {row_count} rows')

        results['databases'][db_name] = db_info

    # Custom JSON encoder to handle datetime, decimal, and numpy types
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, 'isoformat'):  # Handle other datetime-like objects
                return obj.isoformat()
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, Decimal):
                return float(obj)
            return super().default(obj)

    # Save results to file
    with open('database_analysis.json', 'w') as f:
        json.dump(results, f, indent=2, cls=DateTimeEncoder)

    print('\nAnalysis completed and saved to database_analysis.json')

    cursor.close()
    conn.close()

except Exception as e:
    print(f'Error: {e}')