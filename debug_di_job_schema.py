
import sys
import os
from dotenv import load_dotenv
from sqlalchemy import inspect, text

# Load env vars
load_dotenv(override=True)

from ziora_imports.core.database import db_manager
from ziora_imports.config.tenant_config_db import TenantConfigDB

def inspect_di_job_table(tenant_name):
    print(f"Inspecting DI_job table for tenant: {tenant_name}")
    
    tenant_config = TenantConfigDB()
    if not tenant_config.is_tenant_enabled(tenant_name):
        print(f"Tenant {tenant_name} not found or disabled.")
        return

    # Ensure connection
    if not db_manager.test_connection(tenant_name):
        print("Connection failed.")
        return

    engine = db_manager.get_engine(tenant_name)
    inspector = inspect(engine)
    
    table_name = "di_job"
    
    # find exact table name
    actual_table_name = None
    tables = inspector.get_table_names()
    for t in tables:
        if t.lower() == table_name:
            actual_table_name = t
            break
            
    if not actual_table_name:
        print(f"{table_name} table not found!")
        return
        
    print(f"Found table: {actual_table_name}")
    
    print("Columns:")
    columns = inspector.get_columns(actual_table_name)
    for col in columns:
        print(f" - {col['name']} ({col['type']})")

    print("\nForeign Keys:")
    fks = inspector.get_foreign_keys(actual_table_name)
    for fk in fks:
        print(f" - {fk}")

if __name__ == "__main__":
    inspect_di_job_table("acme_corp")
