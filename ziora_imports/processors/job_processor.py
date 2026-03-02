"""
Job data import processor
"""

import pandas as pd
from typing import Dict, Any
from sqlalchemy import text

from .base_processor import BaseProcessor
from ..core.logger import get_logger

logger = get_logger(__name__)


class JobProcessor(BaseProcessor):
    """Processor for Job data imports"""

    def __init__(self, tenant_name: str, schema_config, db_manager):
        super().__init__(tenant_name, "job", schema_config, db_manager)

    def _transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform job data"""
        df = df.copy()

        # Normalize column names
        df.columns = df.columns.str.lower().str.strip().str.replace(" ", "_")

        # Clean string fields
        if "job_code" in df.columns:
            df["job_code"] = df["job_code"].astype(str).str.upper().str.strip()

        if "job_title" in df.columns:
            df["job_title"] = df["job_title"].astype(str).str.strip()

        # Default values
        if "active" in df.columns:
            df["active"] = df["active"].fillna(1)

        # Required by DI_job logic
        df["processstatus"] = 0
        df["deleted"] = 0
        df["errormsg"] = None

        return df

    def _import_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Import job data using DI_job + DI_processJobs"""
        import pandas as pd
        from pathlib import Path

        session = self._get_session()

        result = {
            "success": False,
            "processed_rows": 0,
            "failed_rows": 0,
            "errors": []
        }

        try:
            # Get file name from the dataframe attributes or use a default
            file_path = df.attrs.get('file_path', 'job_import.csv')
            file_name = Path(file_path).name

            # Step 1: Create fileImport record
            self.logger.info("Creating fileImport record")
            insert_fileimport = text("""
                INSERT INTO fileImport (FileName, Status)
                VALUES (:file_name, 0)
                RETURNING importPK
            """)
            result_fileimport = session.execute(
                insert_fileimport,
                {"file_name": file_name}
            )
            run_id = result_fileimport.scalar()
            session.commit() # Commit to make run_id visible to to_sql (which uses a fresh connection)
            self.logger.info(f"Created fileImport record with importPK: {run_id}")

            # Assign runId to dataframe
            df["runid"] = run_id

            # Step 2: Insert data into DI_job table
            self.logger.info(f"Inserting {len(df)} rows into DI_job table")

            # Bulk insert into DI_job
            df.to_sql(
                name="di_job",
                con=session.bind,
                if_exists="append",
                index=False,
                method="multi"
            )
            
            self.logger.info(f"Successfully inserted {len(df)} rows into DI_job (runId: {run_id})")

            # Step 3: Call stored procedure
            self.logger.info(f"Calling DI_processJobs stored procedure with run_id={run_id}")

            sp_result = session.execute(
                text("SELECT * FROM DI_processJobs(:run_id)"),
                {"run_id": run_id}
            ).fetchone()
            
            session.commit()

            result["processed_rows"] = sp_result.processed_count
            result["failed_rows"] = sp_result.failed_count
            result["run_id"] = run_id

            if sp_result.processed_count > 0 or sp_result.failed_count == 0:
                result["success"] = True
                self.logger.info("Import Job completed successfully.")
                
                # Update fileImport status to 1 (Success/InProgress)
                # Matches org_processor logic where >0 processed leads to status 1
                update_fileimport = text("""
                    UPDATE fileImport
                    SET Status = 1, EndDtTime = timezone('utc', now())
                    WHERE importPK = :run_id
                """)
                session.execute(update_fileimport, {"run_id": run_id})
                session.commit()
            else:
                 # Mark as failed if no rows processed and failures occurred
                update_fileimport = text("""
                    UPDATE fileImport
                    SET Status = 2, EndDtTime = timezone('utc', now())
                    WHERE importPK = :run_id
                """)
                session.execute(update_fileimport, {"run_id": run_id})
                session.commit()

            self.logger.info(
                f"DI_processJobs completed | "
                f"Inserted: {sp_result.inserted_count}, "
                f"Updated: {sp_result.updated_count}, "
                f"Failed: {sp_result.failed_count}"
            )

            # Step 4: Log detailed record results
            from ..core.logger import ZioraLogger
            
            # Fetch all records for this run to log details
            detailed_results = session.execute(
                text("SELECT * FROM DI_job WHERE runId = :run_id ORDER BY processfilepk"),
                {"run_id": run_id}
            ).fetchall()

            for row in detailed_results:
                mapping = row._mapping
                log_fields = {
                    'job_id': mapping.get('job_id'),
                    'job_title': mapping.get('job_title'),
                    'job_code': mapping.get('job_code'),
                    'department': mapping.get('department'),
                    'level': mapping.get('level'),
                    'active': mapping.get('active'),
                    'Lang_Cd': mapping.get('lang_cd'),
                    'Timezone_Cd': mapping.get('timezone_cd'),
                    'CountryCode': mapping.get('countrycode')
                }
                
                status = 'SUCCESS'
                message = "Inserted successfully"
                if mapping.get('errormsg'):
                    status = 'ERROR' if mapping.get('deleted') == 1 else 'WARNING'
                    message = mapping.get('errormsg')
                
                ZioraLogger.record_detailed(self.logger, status, log_fields, message)

            # Log Summary
            ZioraLogger.log_summary(
                self.logger,
                total=len(detailed_results),
                success=sp_result.inserted_count + sp_result.updated_count,
                warnings=0,
                failed=sp_result.failed_count
            )

        except Exception as e:
            session.rollback()
            self.logger.error("Job import failed", exc_info=True)

            result["errors"].append({
                "type": "import_error",
                "message": str(e)
            })
            
            # Try to update fileImport status to 2 (Failed) if run_id exists
            if 'run_id' in locals():
                try:
                    update_fileimport = text("""
                        UPDATE fileImport
                        SET Status = 2, EndDtTime = timezone('utc', now())
                        WHERE importPK = :run_id
                    """)
                    session.execute(update_fileimport, {"run_id": run_id})
                    session.commit()
                except Exception:
                    pass # Ignore errors during error handling

        finally:
            session.close()

        return result
