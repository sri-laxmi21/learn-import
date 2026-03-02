
import os
import sys
from sqlalchemy import create_engine, text
import pandas as pd

# Add project root to path
sys.path.append(os.getcwd())

def verify_org_status():
    common_db_url = "postgresql://postgres:srilaxmi123@localhost:5432/ziora_shared_db"
    tenant_name = "acme_corp"
    
    # Get Tenant DB URL
    try:
        common_engine = create_engine(common_db_url)
        with common_engine.connect() as conn:
            result = conn.execute(text(f"SELECT DBString FROM Tenants WHERE TenantId = '{tenant_name}'")).fetchone()
            tenant_db_url = result[0]
            print(f"Connected to Tenant DB: {tenant_name}")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    engine = create_engine(tenant_db_url)
    
    with engine.connect() as conn:
        print("\n--- Checking Latest Import Run in DI_org ---")
        # Get latest runId
        latest_run = conn.execute(text("SELECT MAX(runId) FROM DI_org")).scalar()
        print(f"Latest Run ID: {latest_run}")
        
        if latest_run:
            # Check status distribution
            query = text(f"""
                SELECT processstatus, COUNT(*) as count 
                FROM DI_org 
                WHERE runId = {latest_run}
                GROUP BY processstatus
            """)
            status_df = pd.read_sql(query, conn)
            print("Process Status Distribution (0=Pending, 1=Success, 2=Failed):")
            print(status_df)
            
            # Check for any failures
            # Check for any failures or validation errors (marked as processstatus=1 now)
            error_query = text(f"SELECT processfilepk, org_code, processstatus, errormsg FROM DI_org WHERE runId = {latest_run} AND errormsg IS NOT NULL")
            error_df = pd.read_sql(error_query, conn)
            if not error_df.empty:
                print("\nRecords with Error Messages:")
                print(error_df)
            
            # Check Code table for Dept
            print("\n--- Checking Code Table for OrgType 'Dept' ---")
            code_query = text("SELECT * FROM Code WHERE CatCd = 1001 AND LOWER(ItmCd) = 'dept'")
            code_df = pd.read_sql(code_query, conn)
            print(code_df)
            
            # Verify Organization table
            print("\n--- Verifying Data in Organization Table ---")
            org_query = text(f"""
                SELECT o.Code, o.Name, o.CreatedBy, o.ModifiedBy, o.CreatedDate 
                FROM Organization o
                JOIN DI_org d ON LOWER(o.Code) = LOWER(d.org_code)
                WHERE d.runId = {latest_run}
                LIMIT 5
            """)
            org_df = pd.read_sql(org_query, conn)
            print(org_df)

if __name__ == "__main__":
    verify_org_status()
