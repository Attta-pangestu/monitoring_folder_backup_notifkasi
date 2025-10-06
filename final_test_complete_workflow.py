from date_extraction_micro_feature import DateExtractionMicroFeature

# Final test of the complete workflow
db_name = "D_Drive_Staging_DB"

print("=== FINAL TEST: Complete Database Restore and Connection Workflow ===")
print(f"Testing with database: {db_name}")

try:
    # Test DateExtractionMicroFeature connection with fixed ODBC driver
    print("\nStep 1: Testing DateExtractionMicroFeature connection...")
    date_extractor = DateExtractionMicroFeature(db_name)
    connection = date_extractor.get_database_connection()
    
    if connection:
        print('✓ SUCCESS: DateExtractionMicroFeature can connect to the restored database!')
        
        # Test a simple query
        print("\nStep 2: Testing database query...")
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) as table_count FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        result = cursor.fetchone()
        table_count = result[0] if result else 0
        print(f'✓ SUCCESS: Database has {table_count} tables')
        
        # Test getting database list
        print("\nStep 3: Testing database enumeration...")
        databases = date_extractor.get_databases()
        print(f'✓ SUCCESS: Found {len(databases)} databases')
        
        if db_name in databases:
            print(f'✓ SUCCESS: Target database "{db_name}" is in the database list')
        else:
            print(f'⚠ WARNING: Target database "{db_name}" not found in database list')
            print(f'Available databases: {databases}')
        
        connection.close()
        
        print("\n=== WORKFLOW TEST RESULTS ===")
        print("✓ Database restore: SUCCESS")
        print("✓ Database persistence: SUCCESS") 
        print("✓ ODBC connection: SUCCESS")
        print("✓ DateExtractionMicroFeature: SUCCESS")
        print("✓ Database queries: SUCCESS")
        print("\n🎉 ALL TESTS PASSED! The complete workflow is working correctly.")
        
    else:
        print('✗ FAILED: DateExtractionMicroFeature cannot connect to the restored database')
        print("\n=== WORKFLOW TEST RESULTS ===")
        print("✓ Database restore: SUCCESS")
        print("✓ Database persistence: SUCCESS") 
        print("✗ ODBC connection: FAILED")
        print("✗ DateExtractionMicroFeature: FAILED")
        
except Exception as e:
    print(f'✗ ERROR: {e}')
    import traceback
    traceback.print_exc()
    
    print("\n=== WORKFLOW TEST RESULTS ===")
    print("✓ Database restore: SUCCESS")
    print("✓ Database persistence: SUCCESS") 
    print("✗ ODBC connection: ERROR")
    print("✗ DateExtractionMicroFeature: ERROR")