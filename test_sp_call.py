
import os
import sys
from sqlalchemy import create_engine, text

# Add project root to path
sys.path.append(os.getcwd())

def test_sp():
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
    
    try:
        with engine.connect() as conn:
            print("Calling DI_processOrgs(12345)...") # Random RunID, doesn't matter if empty
            # If ambiguous, this will fail
            conn.execute(text("SELECT * FROM DI_processOrgs(12345)"))
            print("Call successful (no AmbiguousFunction error).")
    except Exception as e:
        print(f"Call failed: {e}")

if __name__ == "__main__":
    test_sp()
