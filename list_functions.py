
import os
import sys
from sqlalchemy import create_engine, text
import pandas as pd

# Add project root to path
sys.path.append(os.getcwd())

def list_functions():
    common_db_url = "postgresql://postgres:srilaxmi123@localhost:5432/ziora_shared_db"
    tenant_name = "acme_corp"
    
    try:
        common_engine = create_engine(common_db_url)
        with common_engine.connect() as conn:
            result = conn.execute(text(f"SELECT DBString FROM Tenants WHERE TenantId = '{tenant_name}'")).fetchone()
            if not result:
                print(f"Tenant {tenant_name} not found.")
                return
            tenant_db_url = result[0]
            print(f"Connected to Tenant DB: {tenant_db_url}")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    engine = create_engine(tenant_db_url)
    
    with engine.connect() as conn:
        print("\n--- Listing Functions named 'DI_processOrgs' (case insensitive) ---")
        query = text("""
            SELECT 
                routine_name, 
                data_type as return_type, 
                routine_definition 
            FROM information_schema.routines 
            WHERE routine_type = 'FUNCTION' 
              AND lower(routine_name) = 'di_processorgs'
        """)
        # routin_definition might not show full body easily in this view for older pg
        
        # Better query for pg_proc
        pg_query = text("""
            SELECT 
                p.proname as function_name, 
                pg_get_function_arguments(p.oid) as arguments,
                pg_get_function_result(p.oid) as return_type
            FROM pg_proc p 
            JOIN pg_namespace n ON p.pronamespace = n.oid 
            WHERE n.nspname = 'public' 
              AND lower(p.proname) = 'di_processorgs'
        """)
        
        df = pd.read_sql(pg_query, conn)
        print(df)
        
        if not df.empty:
            print(f"\nFound {len(df)} functions named DI_processOrgs")
            for idx, row in df.iterrows():
                print(f"\nFunction {idx+1}: {row['function_name']}")
                print(f"Arguments: {row['arguments']}")
                print(f"Returns: {row['return_type']}")

if __name__ == "__main__":
    list_functions()
