import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get DB URL
db_url = os.getenv("SHARED_DB_URL")
if not db_url:
    print("Error: SHARED_DB_URL not found in .env")
    sys.exit(1)

# Connect to database
# Note: This connects to the shared DB. For tenant data, we might need to adjust if they are separate.
# Based on logs, 'acme_corp' seems to use 'acme_corp_local_db' which might be the same DB or different schema.
# The logs say: "Tenant found: acme_corp_local_db (ID: acme_corp, PK: 1)"
# And the code uses `_get_session` which likely connects to the tenant DB.
# We'll try to use the logic from base_processor to get the tenant connection if possible,
# or just assume it's the same DB for this investigation if the URL points there.
# For simplicity, let's try to query the tables using the shared URL first, 
# but we might need to be specific about the schema or DB.

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        print("\n--- fileImport Table (Last 10) ---")
        result = conn.execute(text("SELECT * FROM fileImport ORDER BY importPK DESC LIMIT 10"))
        for row in result:
            print(row)

        print("\n--- DI_job Table (Last 10 Ordered by processfilepk) ---")
        # Checking if processfilepk exists and is verified
        try:
            result = conn.execute(text("SELECT processfilepk, runid, job_code, job_title FROM DI_job ORDER BY processfilepk DESC LIMIT 10"))
            for row in result:
                print(row)
        except Exception as e:
            print(f"Error querying DI_job: {e}")

        print("\n--- Job Table (Last 10 Ordered by jobpk) ---")
        try:
            result = conn.execute(text("SELECT jobpk, code, name, createddate FROM Job ORDER BY jobpk DESC LIMIT 10"))
            for row in result:
                print(row)
        except Exception as e:
            print(f"Error querying Job: {e}")

except Exception as e:
    print(f"Database connection failed: {e}")
