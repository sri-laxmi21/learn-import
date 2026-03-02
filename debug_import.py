
import os
import sys
from sqlalchemy import create_engine, text
from pathlib import Path
import pandas as pd

# Add project root to path to import config
sys.path.append(os.getcwd())

def debug_database():
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
            print(f"Found tenant DB URL: {tenant_db_url}")
    except Exception as e:
        print(f"Error connecting to common DB: {e}")
        return

    print(f"Connecting to tenant database...")
    engine = create_engine(tenant_db_url)
    
    with engine.connect() as conn:
        print("\n--- Inspecting DI_job (Temp Table - might be empty if transaction closed) ---")
        # Note: DI_job is NOT temporary in schema, it's a regular table used as valid temp storage.
        # Let's check the latest runs
        di_jobs = pd.read_sql(text("SELECT * FROM DI_job ORDER BY processfilepk DESC LIMIT 20"), conn)
        print(f"DI_job rows: {len(di_jobs)}")
        if not di_jobs.empty:
            print(di_jobs[['processfilepk', 'runid', 'job_code', 'processstatus', 'errormsg']])
        
        print("\n--- Inspecting Job (Target Table) ---")
        jobs = pd.read_sql(text("SELECT * FROM Job"), conn)
        print(f"Job rows: {len(jobs)}")
        if not jobs.empty:
            # Show relevant columns
            cols = ['jobpk', 'code', 'name', 'createddate', 'modifieddate', 'createdby', 'modifiedby']
            # specific columns might vary, let's just print columns found
            available_cols = [c for c in cols if c.lower() in [x.lower() for x in jobs.columns]]
            print(jobs[available_cols].head(20))
            
            # Check for matches
            if not di_jobs.empty:
                print("\n--- Checking matches ---")
                di_code = di_jobs.iloc[0]['job_code']
                print(f"Checking for match with DI_job code: '{di_code}'")
                
                match = jobs[jobs['code'].str.lower() == di_code.lower()]
                print(f"Matches found in Job table: {len(match)}")
                if not match.empty:
                    print(match[available_cols])

if __name__ == "__main__":
    debug_database()
