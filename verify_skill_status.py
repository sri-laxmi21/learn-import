
import os
import sys
from sqlalchemy import create_engine, text
import pandas as pd

# Add project root to path
sys.path.append(os.getcwd())

def verify_skill_status():
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
        print("\n--- Checking Valid Skill Types (CatCd=1003) ---")
        code_query = text("SELECT * FROM Code WHERE CatCd = 1003 AND IsDeleted = 0")
        code_df = pd.read_sql(code_query, conn)
        print(code_df)
        
        print("\n--- Checking Latest Import Run in DI_skill ---")
        # Get latest runId
        latest_run = conn.execute(text("SELECT MAX(runId) FROM DI_skill")).scalar()
        print(f"Latest Run ID: {latest_run}")
        
        if latest_run:
            # Check status distribution
            query = text(f"""
                SELECT processstatus, COUNT(*) as count 
                FROM DI_skill 
                WHERE runId = {latest_run}
                GROUP BY processstatus
            """)
            status_df = pd.read_sql(query, conn)
            print("Process Status Distribution (1=Success/Processed, 2=Failed):")
            print(status_df)
            
            # Check for failures/errors
            error_query = text(f"SELECT processfilepk, skill_id, processstatus, errormsg FROM DI_skill WHERE runId = {latest_run} AND errormsg IS NOT NULL")
            error_df = pd.read_sql(error_query, conn)
            if not error_df.empty:
                print("\nRecords with Error Messages:")
                print(error_df)
            
            # Verify Skill table
            print("\n--- Verifying Data in Skill Table ---")
            # Verify Skill table
            print("\n--- Verifying Data in Skill Table ---")
            skill_query = text(f"""
                SELECT s.Code, s.Name, s.LstUpd, s.LstUpdBy 
                FROM Skill s
                JOIN DI_skill d ON LOWER(s.Code) = LOWER(d.skill_id)
                WHERE d.runId = {latest_run}
                LIMIT 5
            """)
            skill_df = pd.read_sql(skill_query, conn)
            print(skill_df)
            
        print("\n--- Skill Table Columns and Nullability ---")
        cols = conn.execute(text("SELECT column_name, is_nullable, data_type FROM information_schema.columns WHERE table_name = 'skill'")).fetchall()
        for c in cols:
            print(f"{c[0]} ({c[2]}): Nullable={c[1]}")

if __name__ == "__main__":
    verify_skill_status()
