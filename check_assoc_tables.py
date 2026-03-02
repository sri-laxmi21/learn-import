
import os
import sys
from sqlalchemy import create_engine, text

# Add project root to path
sys.path.append(os.getcwd())

def check_tables():
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
        print("\n--- Checking Tables ---")
        tables_to_check = ['EmpAssociations', 'PersonOrg', 'empassociations', 'personorg']
        for t in tables_to_check:
            exists = conn.execute(text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{t.lower()}')")).scalar()
            print(f"Table '{t}': {'Exists' if exists else 'Missing'}")
            
            if exists:
                print(f"  Columns for {t}:")
                cols = conn.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{t.lower()}'")).fetchall()
                for c in cols:
                    print(f"    - {c[0]} ({c[1]})")

if __name__ == "__main__":
    check_tables()
