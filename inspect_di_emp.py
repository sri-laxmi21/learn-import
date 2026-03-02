
import os
import sys
from sqlalchemy import create_engine, text
import pandas as pd

# Add project root to path
sys.path.append(os.getcwd())

def inspect_di_emp():
    common_db_url = "postgresql://postgres:srilaxmi123@localhost:5432/ziora_shared_db"
    tenant_name = "acme_corp"
    
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
        print("\n--- DI_emp Table Columns ---")
        cols = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'di_emp'")).fetchall()
        for c in cols:
            print(f"{c[0]} ({c[1]})")

        print("\n--- Data for Latest Run ---")
        # Get latest runId
        run_id = conn.execute(text("SELECT MAX(runId) FROM DI_emp")).scalar()
        if run_id:
            print(f"Latest runId: {run_id}")
            df = pd.read_sql(text(f"SELECT personnumber, processstatus, errormsg, statuscodeid, typecodeid FROM DI_emp WHERE runId = {run_id}"), conn)
            print(df.to_string())
        else:
            print("No data in DI_emp")

if __name__ == "__main__":
    inspect_di_emp()
