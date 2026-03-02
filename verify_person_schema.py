
import os
import sys
from sqlalchemy import create_engine, text

# Add project root to path
sys.path.append(os.getcwd())

def verify_person_schema():
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
        print("\n--- Person Table Columns and Nullability ---")
        cols = conn.execute(text("SELECT column_name, is_nullable, data_type FROM information_schema.columns WHERE table_name = 'person'")).fetchall()
        for c in cols:
             print(f"{c[0]} ({c[2]}): Nullable={c[1]}")

if __name__ == "__main__":
    verify_person_schema()
