
import sys
from ziora_imports.config.tenant_config_db import TenantConfigDB
from ziora_imports.core.database import db_manager
from sqlalchemy import text

def verify_fix(run_id, tenant):
    with open("verify_result.txt", "w") as f:
        try:
            if not db_manager.test_connection(tenant):
                f.write(f"Failed to connect to tenant {tenant}\n")
                return

            session = db_manager.get_session(tenant)
            
            # Check fileImport status
            f.write(f"Checking runId: {run_id}\n")
            file_import = session.execute(text("SELECT * FROM fileImport WHERE importPK = :run_id"), {"run_id": run_id}).mappings().first()
            if not file_import:
                f.write(f"Run ID {run_id} not found in fileImport\n")
            else:
                f.write(f"FileImport Status: {file_import['status']} (Expected: 1 or 2)\n")

            # Check DI_emp processstatus
            stats = session.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE processstatus = 0) as pending,
                    COUNT(*) FILTER (WHERE processstatus = 1) as success,
                    COUNT(*) FILTER (WHERE processstatus = 2) as failed
                FROM DI_emp 
                WHERE runId = :run_id
            """), {"run_id": run_id}).mappings().first()
            
            f.write(f"DI_emp Stats: {dict(stats)}\n")
            
            if stats['pending'] == 0 and (stats['success'] > 0 or stats['failed'] > 0):
                f.write("\nSUCCESS: Data has been processed (no pending records).\n")
            else:
                f.write("\nWARNING: Some records are still pending or no records found.\n")

        except Exception as e:
            f.write(f"Error: {e}\n")
        finally:
            db_manager.close_all()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_fix.py <run_id>")
        sys.exit(1)
    
    verify_fix(int(sys.argv[1]), "acme_corp")
