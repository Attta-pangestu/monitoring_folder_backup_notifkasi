import pyodbc
import json
from datetime import datetime
import numpy as np
from decimal import Decimal

# SQL Server connection details
server = 'localhost'
username = 'sa'
password = 'windows0819'

def analyze_table_structure(cursor, table_name, db_name):
    """Analyze table structure and sample data"""
    print(f'\nAnalyzing table: {table_name}')

    # Get column info with data types, constraints, and defaults
    cursor.execute(f"""
        SELECT
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.CHARACTER_MAXIMUM_LENGTH,
            c.NUMERIC_PRECISION,
            c.NUMERIC_SCALE,
            c.IS_NULLABLE,
            c.COLUMN_DEFAULT,
            COLUMNPROPERTY(OBJECT_ID(c.TABLE_SCHEMA+'.'+c.TABLE_NAME), c.COLUMN_NAME, 'IsIdentity') as IS_IDENTITY,
            pk.COLUMN_NAME as PRIMARY_KEY
        FROM INFORMATION_SCHEMA.COLUMNS c
        LEFT JOIN (
            SELECT ku.TABLE_SCHEMA, ku.TABLE_NAME, ku.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
                ON tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
                AND tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
        ) pk ON c.TABLE_SCHEMA = pk.TABLE_SCHEMA
            AND c.TABLE_NAME = pk.TABLE_NAME
            AND c.COLUMN_NAME = pk.COLUMN_NAME
        WHERE c.TABLE_NAME = '{table_name}'
        ORDER BY c.ORDINAL_POSITION
    """)

    columns_info = cursor.fetchall()

    # Get row count
    cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
    row_count = cursor.fetchone()[0]

    # Get indexes
    cursor.execute(f"""
        SELECT
            i.name as index_name,
            c.name as column_name,
            i.is_unique,
            i.is_primary_key
        FROM sys.indexes i
        JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
        JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        WHERE i.object_id = OBJECT_ID('{table_name}')
        ORDER BY i.name, ic.key_ordinal
    """)
    indexes = cursor.fetchall()

    # Get foreign keys
    cursor.execute(f"""
        SELECT
            f.name as constraint_name,
            c.name as column_name,
            r.name as referenced_table,
            rc.name as referenced_column
        FROM sys.foreign_keys f
        JOIN sys.foreign_key_columns fc ON f.object_id = fc.parent_object_id
        JOIN sys.columns c ON fc.parent_object_id = c.object_id AND fc.parent_column_id = c.column_id
        JOIN sys.tables r ON fc.referenced_object_id = r.object_id
        JOIN sys.columns rc ON fc.referenced_object_id = rc.object_id AND fc.referenced_column_id = rc.column_id
        WHERE f.parent_object_id = OBJECT_ID('{table_name}')
    """)
    foreign_keys = cursor.fetchall()

    # Get sample data (first 10 rows)
    cursor.execute(f'SELECT TOP 10 * FROM {table_name}')
    sample_data = cursor.fetchall()

    # Get column names for sample data
    column_names = [desc[0] for desc in cursor.description]

    # Get data ranges for numeric/date columns
    data_ranges = {}
    for col_info in columns_info:
        col_name = col_info[0]
        data_type = col_info[1]

        if data_type in ('int', 'bigint', 'smallint', 'tinyint', 'decimal', 'numeric', 'float', 'real'):
            try:
                cursor.execute(f'SELECT MIN({col_name}), MAX({col_name}) FROM {table_name} WHERE {col_name} IS NOT NULL')
                min_max = cursor.fetchone()
                if min_max[0] is not None:
                    data_ranges[col_name] = {'min': min_max[0], 'max': min_max[1], 'type': 'numeric'}
            except:
                pass
        elif data_type in ('datetime', 'date', 'datetime2'):
            try:
                cursor.execute(f'SELECT MIN({col_name}), MAX({col_name}) FROM {table_name} WHERE {col_name} IS NOT NULL')
                min_max = cursor.fetchone()
                if min_max[0] is not None:
                    data_ranges[col_name] = {'min': min_max[0], 'max': min_max[1], 'type': 'date'}
            except:
                pass

    # Get distinct counts for key columns
    distinct_counts = {}
    if row_count > 0:
        for col_info in columns_info[:5]:  # First 5 columns only
            col_name = col_info[0]
            try:
                cursor.execute(f'SELECT COUNT(DISTINCT {col_name}) FROM {table_name} WHERE {col_name} IS NOT NULL')
                distinct_count = cursor.fetchone()[0]
                distinct_counts[col_name] = distinct_count
            except:
                pass

    return {
        'table_name': table_name,
        'database': db_name,
        'row_count': row_count,
        'columns': [list(col) for col in columns_info],
        'indexes': [list(idx) for idx in indexes],
        'foreign_keys': [list(fk) for fk in foreign_keys],
        'sample_data': [list(row) for row in sample_data],
        'column_names': column_names,
        'data_ranges': data_ranges,
        'distinct_counts': distinct_counts
    }

try:
    # Create connection string
    conn_str = f'DRIVER={{SQL Server}};SERVER={server};UID={username};PWD={password}'
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    print('Connected to SQL Server successfully')

    # Define tables to analyze in detail
    tables_to_analyze = [
        {'db': 'staging_PTRJ_iFES_Plantware', 'table': 'Gwscannerdata'},
        {'db': 'staging_PTRJ_iFES_Plantware', 'table': 'Ffbscannerdata'},
        {'db': 'db_ptrj', 'table': 'PR_Taskreg'},
        {'db': 'db_ptrj', 'table': 'IN_FUELISSUE'},
        {'db': 'VenusHR14', 'table': 'HR_T_TAMachine'}
    ]

    # Initialize results dictionary
    results = {
        'timestamp': datetime.now().isoformat(),
        'analysis_focus': 'Detailed table analysis for specific business tables',
        'databases': {}
    }

    # Analyze each table
    for table_info in tables_to_analyze:
        db_name = table_info['db']
        table_name = table_info['table']

        print(f'\n=== Analyzing {db_name}.{table_name} ===')

        # Switch to the correct database
        cursor.execute(f'USE {db_name}')

        # Analyze table structure
        table_analysis = analyze_table_structure(cursor, table_name, db_name)

        # Add to results
        if db_name not in results['databases']:
            results['databases'][db_name] = {}

        results['databases'][db_name][table_name] = table_analysis

        print(f'Completed analysis for {table_name} ({table_analysis["row_count"]:,} rows)')

    # Save results to file
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, 'isoformat'):
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

    with open('detailed_table_analysis.json', 'w') as f:
        json.dump(results, f, indent=2, cls=DateTimeEncoder)

    print('\nDetailed analysis completed and saved to detailed_table_analysis.json')

    cursor.close()
    conn.close()

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()