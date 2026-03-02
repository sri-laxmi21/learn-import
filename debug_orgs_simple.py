
import os
import sys
from sqlalchemy import create_engine, text
import pandas as pd

# Add project root to path
sys.path.append(os.getcwd())

def debug_orgs_simple():
    common_db_url = "postgresql://postgres:srilaxmi123@localhost:5432/ziora_shared_db"
    tenant_name = "acme_corp"
    
    try:
        common_engine = create_engine(common_db_url)
        with common_engine.connect() as conn:
            result = conn.execute(text(f"SELECT DBString FROM Tenants WHERE TenantId = '{tenant_name}'")).fetchone()
            tenant_db_url = result[0]
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    engine = create_engine(tenant_db_url)
    
    with engine.connect() as conn:
        print("\n--- DI_org (Last Run) ---")
        di_df = pd.read_sql(text("SELECT processfilepk, org_code, processstatus FROM DI_org ORDER BY processfilepk DESC LIMIT 12"), conn)
        print(di_df)
        
        print("\n--- Organization (Last Created) ---")
        org_df = pd.read_sql(text("SELECT OrgPK, Code, Name, CreatedDate FROM Organization ORDER BY CreatedDate DESC LIMIT 12"), conn)
        print(org_df)

if __name__ == "__main__":
    debug_orgs_simple()
