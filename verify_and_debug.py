
import os
import sys
from sqlalchemy import create_engine, text
import pandas as pd

# Add project root to path
sys.path.append(os.getcwd())

def verify_and_debug():
    common_db_url = "postgresql://postgres:srilaxmi123@localhost:5432/ziora_shared_db"
    tenant_name = "acme_corp"
    
    print("--- Connecting to DB ---")
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
        print("\n--- Verifying DI_org Status (Last Run) ---")
        query = text("""
            SELECT runId, processstatus, errormsg, COUNT(*) as count 
            FROM DI_org 
            WHERE runId = (SELECT MAX(runId) FROM DI_org) 
            GROUP BY runId, processstatus, errormsg
        """)
        print(pd.read_sql(query, conn))

        print("\n--- Verifying Organization Table (Last Created) ---")
        print(pd.read_sql(text("SELECT Code, Name, CreatedBy, ModifiedBy FROM Organization ORDER BY CreatedDate DESC LIMIT 5"), conn))

        print("\n--- Checking DI_skill columns vs Sample CSV ---")
        # Check if we can find mismatched columns for skills
        try:
            skills_df = pd.read_csv("samples/skills_sample.csv")
            print(f"CSV Columns: {list(skills_df.columns)}")
            
            # Get table columns
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'di_skill'"))
            table_cols = [r[0] for r in result.fetchall()]
            print(f"Table Columns: {table_cols}")
            
            # Find extra columns in CSV
            csv_cols_norm = [c.lower().strip().replace(' ', '_') for c in skills_df.columns]
            extra_cols = [c for c in csv_cols_norm if c not in table_cols]
            print(f"Potential Extra Columns in CSV causing issues: {extra_cols}")
            
        except Exception as e:
            print(f"Error checking skills: {e}")

if __name__ == "__main__":
    verify_and_debug()
