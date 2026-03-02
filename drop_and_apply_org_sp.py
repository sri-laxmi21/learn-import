
import os
import sys
from sqlalchemy import create_engine, text
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

def drop_and_apply():
    common_db_url = "postgresql://postgres:srilaxmi123@localhost:5432/ziora_shared_db"
    tenant_name = "acme_corp"
    
    print(f"Connecting to common database: {common_db_url}")
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
    
    # 1. Drop all functions named DI_processOrgs
    drop_all_query = text("""
        DO $$ 
        DECLARE 
            r RECORD; 
        BEGIN 
            FOR r IN (
                SELECT ns.nspname || '.' || p.proname || '(' || pg_get_function_identity_arguments(p.oid) || ')' as func_signature 
                FROM pg_proc p 
                JOIN pg_namespace ns ON p.pronamespace = ns.oid 
                WHERE lower(p.proname) = 'di_processorgs'
            ) 
            LOOP 
                RAISE NOTICE 'Dropping function: %', r.func_signature;
                EXECUTE 'DROP FUNCTION IF EXISTS ' || r.func_signature || ' CASCADE'; 
            END LOOP; 
        END $$;
    """)
    
    script_path = Path("scripts/DI_processOrgs.sql")
    if not script_path.exists():
        print(f"Error: Script not found at {script_path}")
        return
        
    sql_content = script_path.read_text()
    
    # Remove the manual DROP we added if we are doing it dynamically, 
    # but keeping it is also fine as it won't find it.
    
    try:
        with engine.connect() as conn:
            print("Dropping all existing DI_processOrgs functions...")
            conn.execute(drop_all_query)
            conn.commit()
            print("Dropped all variants.")
            
            print("Applying DI_processOrgs.sql...")
            conn.execute(text(sql_content))
            conn.commit()
            print("Successfully re-applied DI_processOrgs.sql")
            
    except Exception as e:
        print(f"Error executing script: {e}")

if __name__ == "__main__":
    drop_and_apply()
