import pyodbc
import json
from datetime import datetime
import numpy as np
from decimal import Decimal

# SQL Server connection details
server = 'localhost'
username = 'sa'
password = 'windows0819'

def analyze_date_columns(cursor, table_name, db_name):
    """Analyze date/time columns in a specific table"""
    print(f'\nAnalyzing date columns in: {db_name}.{table_name}')

    # Get date/time columns information
    cursor.execute(f"""
        SELECT
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table_name}'
        AND DATA_TYPE IN ('datetime', 'date', 'datetime2', 'smalldatetime', 'time', 'datetimeoffset')
        ORDER BY ORDINAL_POSITION
    """)

    date_columns = cursor.fetchall()

    if not date_columns:
        print(f'No date/time columns found in {table_name}')
        return None

    date_analysis = {
        'table_name': table_name,
        'database': db_name,
        'date_columns': [],
        'data_ranges': {},
        'sample_data': {}
    }

    for col in date_columns:
        col_name = col[0]
        data_type = col[1]
        is_nullable = col[2]
        default_value = col[3]

        print(f'Found date column: {col_name} ({data_type})')

        column_info = {
            'column_name': col_name,
            'data_type': data_type,
            'is_nullable': is_nullable,
            'default_value': default_value
        }

        # Get data range
        try:
            cursor.execute(f"""
                SELECT
                    MIN({col_name}) as min_date,
                    MAX({col_name}) as max_date,
                    COUNT({col_name}) as non_null_count,
                    COUNT(*) as total_count
                FROM {table_name}
                WHERE {col_name} IS NOT NULL
            """)

            range_data = cursor.fetchone()
            if range_data[0] is not None:
                column_info['data_range'] = {
                    'min_date': range_data[0],
                    'max_date': range_data[1],
                    'non_null_count': range_data[2],
                    'total_count': range_data[3],
                    'null_percentage': round(((range_data[3] - range_data[2]) / range_data[3]) * 100, 2) if range_data[3] > 0 else 0
                }

                # Get date distribution by year
                cursor.execute(f"""
                    SELECT
                        YEAR({col_name}) as year_val,
                        COUNT(*) as count
                    FROM {table_name}
                    WHERE {col_name} IS NOT NULL
                    GROUP BY YEAR({col_name})
                    ORDER BY year_val
                """)

                year_distribution = cursor.fetchall()
                column_info['year_distribution'] = {str(row[0]): row[1] for row in year_distribution}

                # Get date distribution by month (for recent years)
                cursor.execute(f"""
                    SELECT TOP 24
                        FORMAT({col_name}, 'yyyy-MM') as month_val,
                        COUNT(*) as count
                    FROM {table_name}
                    WHERE {col_name} IS NOT NULL
                    GROUP BY FORMAT({col_name}, 'yyyy-MM')
                    ORDER BY FORMAT({col_name}, 'yyyy-MM') DESC
                """)

                month_distribution = cursor.fetchall()
                column_info['month_distribution'] = {row[0]: row[1] for row in month_distribution}

        except Exception as e:
            print(f'Error getting range for {col_name}: {e}')
            column_info['error'] = str(e)

        date_analysis['date_columns'].append(column_info)

    return date_analysis

try:
    # Create connection string
    conn_str = f'DRIVER={{SQL Server}};SERVER={server};UID={username};PWD={password}'
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    print('Connected to SQL Server successfully')

    # Define tables to analyze for date columns
    date_tables_to_analyze = [
        {'db': 'staging_PTRJ_iFES_Plantware', 'table': 'Gwscannerdata'},
        {'db': 'staging_PTRJ_iFES_Plantware', 'table': 'Ffbscannerdata'},
        {'db': 'db_ptrj', 'table': 'PR_Taskreg'},
        {'db': 'db_ptrj', 'table': 'IN_FUELISSUE'},
        {'db': 'VenusHR14', 'table': 'HR_T_TAMachine'}
    ]

    # Initialize results dictionary
    date_analysis_results = {
        'timestamp': datetime.now().isoformat(),
        'analysis_focus': 'Date column analysis for time-based features',
        'databases': {}
    }

    # Analyze date columns in each table
    for table_info in date_tables_to_analyze:
        db_name = table_info['db']
        table_name = table_info['table']

        print(f'\n=== Analyzing {db_name}.{table_name} ===')

        # Switch to the correct database
        cursor.execute(f'USE {db_name}')

        # Analyze date columns
        table_date_analysis = analyze_date_columns(cursor, table_name, db_name)

        if table_date_analysis:
            # Add to results
            if db_name not in date_analysis_results['databases']:
                date_analysis_results['databases'][db_name] = {}

            date_analysis_results['databases'][db_name][table_name] = table_date_analysis

        print(f'Completed date analysis for {table_name}')

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

    with open('date_column_analysis.json', 'w') as f:
        json.dump(date_analysis_results, f, indent=2, cls=DateTimeEncoder)

    print('\nDate column analysis completed and saved to date_column_analysis.json')

    # Create summary report
    summary_report = "# Date Column Analysis Summary\n\n"
    summary_report += f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    for db_name, db_data in date_analysis_results['databases'].items():
        summary_report += f"## Database: {db_name}\n\n"

        for table_name, table_data in db_data.items():
            summary_report += f"### Table: {table_name}\n"

            for col in table_data['date_columns']:
                summary_report += f"- **{col['column_name']}** ({col['data_type']})\n"
                if 'data_range' in col:
                    dr = col['data_range']
                    summary_report += f"  - Range: {dr['min_date']} to {dr['max_date']}\n"
                    summary_report += f"  - Records: {dr['non_null_count']:,} / {dr['total_count']:,}\n"
                    summary_report += f"  - Null %: {dr['null_percentage']}%\n"
                summary_report += "\n"

    with open('date_analysis_summary.md', 'w') as f:
        f.write(summary_report)

    print('Summary report saved to date_analysis_summary.md')

    cursor.close()
    conn.close()

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()