"""
Employee data import processor
"""

import pandas as pd
from typing import Dict, Any

from .base_processor import BaseProcessor
from ..core.logger import get_logger

logger = get_logger(__name__)


class EmpProcessor(BaseProcessor):
    """Processor for Employee data imports"""
    
    def __init__(self, tenant_name: str, schema_config, db_manager):
        super().__init__(tenant_name, 'emp', schema_config, db_manager)
    
    def _transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform employee data"""
        df_transformed = df.copy()
        
        # Normalize column names (convert to lowercase, replace spaces with underscores)
        df_transformed.columns = df_transformed.columns.str.lower().str.replace(' ', '_')
        
        # Example transformations
        # Convert email to lowercase
        if 'email' in df_transformed.columns:
            df_transformed['email'] = df_transformed['email'].str.lower().str.strip()
        
        # Normalize phone numbers (example)
        if 'phone' in df_transformed.columns:
            df_transformed['phone'] = df_transformed['phone'].astype(str).str.replace(r'[^\d]', '', regex=True)
        
        return df_transformed
    
    def _import_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Import employee data into database"""
        from sqlalchemy import text
        from pathlib import Path
        
        result = {
            'success': False,
            'processed_rows': 0,
            'failed_rows': 0,
            'errors': []
        }
        
        session = self._get_session()
        
        try:
            # Get file name
            file_path = df.attrs.get('file_path', 'emp_import.csv')
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
            self.logger.info(f"Created fileImport record with importPK: {run_id}")
            
            # Step 2: Insert data into DI_emp table
            self.logger.info(f"Inserting {len(df)} rows into DI_emp table")
            processed = 0
            failed = 0
            
            insert_stmt = text("""
                INSERT INTO DI_emp (
                    runId, PersonNumber, FirstName, MiddleName, LastName, Preferredname, Email,
                    Active, LoginEnabled, Inst, title, Role_Cd, photourl, Currency_Cd,
                    StatusCodeId, TypeCodeId, IsDeleted, StartDate, EndDate, City, State, MgrPersonNumber,
                    UserName, Password, MustChangePwd, OrgFK, IsPrimary, PersonOrgIsDeleted,
                    processstatus, deleted
                )
                VALUES (
                    :runId, :PersonNumber, :FirstName, :MiddleName, :LastName, :Preferredname, :Email,
                    :Active, :LoginEnabled, :Inst, :title, :Role_Cd, :photourl, :Currency_Cd,
                    :StatusCodeId, :TypeCodeId, :IsDeleted, :StartDate, :EndDate, :City, :State, :MgrPersonNumber,
                    :UserName, :Password, :MustChangePwd, :OrgFK, :IsPrimary, :PersonOrgIsDeleted,
                    0, 0
                )
            """)
            
            for idx, row in df.iterrows():
                try:
                    # Helper for boolean/smallint conversion
                    def to_int_bool(val, default=0):
                        if pd.isna(val) or val is None or str(val).strip() == '':
                            return default
                        if isinstance(val, bool):
                            return 1 if val else 0
                        try:
                            return 1 if int(val) == 1 else 0
                        except:
                            return default

                    # Handle empty strings and NaN as NULL
                    def to_null(val):
                        if val is None:
                            return None
                        if isinstance(val, float) and pd.isna(val):
                            return None
                        if isinstance(val, str) and val.strip() == '':
                            return None
                        return val
                    
                    session.execute(
                        insert_stmt,
                        {
                            'runId': run_id,
                            'PersonNumber': to_null(row.get('personnumber')),
                            'FirstName': to_null(row.get('firstname')),
                            'MiddleName': to_null(row.get('middlename')),
                            'LastName': to_null(row.get('lastname')),
                            'Preferredname': to_null(row.get('preferredname')),
                            'Email': to_null(row.get('email')),
                            'Active': to_int_bool(row.get('active'), 1),
                            'LoginEnabled': to_int_bool(row.get('loginenabled'), 0),
                            'Inst': to_int_bool(row.get('inst'), 0),
                            'title': to_null(row.get('title')),
                            'Role_Cd': to_null(row.get('role_cd')),
                            'photourl': to_null(row.get('photourl')),
                            'Currency_Cd': to_null(row.get('currency_cd')),
                            'StatusCodeId': to_null(row.get('statuscodeid')),
                            'TypeCodeId': to_null(row.get('typecodeid')),
                            'IsDeleted': to_int_bool(row.get('isdeleted'), 0),
                            'StartDate': to_null(row.get('startdate')),
                            'EndDate': to_null(row.get('enddate')),
                            'City': to_null(row.get('city')),
                            'State': to_null(row.get('state')),
                            'MgrPersonNumber': to_null(row.get('mgrpersonnumber')),
                            'UserName': to_null(row.get('username')),
                            'Password': to_null(row.get('password')),
                            'MustChangePwd': to_int_bool(row.get('mustchangepwd'), 0),
                            'OrgFK': to_null(row.get('orgfk')),
                            'IsPrimary': to_int_bool(row.get('isprimary'), 1),
                            'PersonOrgIsDeleted': to_int_bool(row.get('personorgisdeleted'), 0)
                        }
                    )
                    processed += 1
                except Exception as e:
                    failed += 1
                    error_msg = f"Row {idx + 1}: {str(e)}"
                    result['errors'].append({
                        'row_index': idx,
                        'error': error_msg
                    })
                    self.logger.error(f"Error inserting row {idx + 1}: {str(e)}")
            
            # Step 3: Call stored procedure
            self.logger.info(f"Calling DI_processEmps stored procedure with run_id={run_id}")
            
            # Commit the inserts first so they are visible to the stored procedure
            session.commit()
            
            sp_result = session.execute(
                text("SELECT * FROM DI_processEmps(CAST(:run_id AS INTEGER))"),
                {"run_id": run_id}
            ).fetchone()
            
            session.commit()
            
            result['processed_rows'] = sp_result.processed_count
            result['failed_rows'] = sp_result.failed_count
            result['run_id'] = run_id
            
            if sp_result.processed_count > 0 or sp_result.failed_count == 0:
                result['success'] = True
                self.logger.info("Import Employee completed successfully.")
                
                # Update fileImport status to 1 (Success/InProgress)
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
                f"DI_processEmps completed | "
                f"Inserted: {sp_result.inserted_count}, "
                f"Updated: {sp_result.updated_count}, "
                f"Failed: {sp_result.failed_count}"
            )

            # Step 4: Log detailed record results
            from ..core.logger import ZioraLogger
            
            # Fetch all records for this run to log details
            detailed_results = session.execute(
                text("SELECT * FROM DI_emp WHERE runId = :run_id ORDER BY processfilepk"),
                {"run_id": run_id}
            ).fetchall()

            for row in detailed_results:
                mapping = row._mapping
                log_fields = {
                    'PersonNumber': mapping.get('personnumber'),
                    'FirstName': mapping.get('firstname'),
                    'LastName': mapping.get('lastname'),
                    'Email': mapping.get('email'),
                    'Active': mapping.get('active'),
                    'title': mapping.get('title'),
                    'Role_Cd': mapping.get('role_cd'),
                    'OrgFK': mapping.get('orgfk'),
                    'City': mapping.get('city'),
                    'State': mapping.get('state'),
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
            self.logger.error("Employee import failed", exc_info=True)
            
            result['errors'].append({
                'type': 'import_error',
                'message': str(e)
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
                    pass
        finally:
            session.close()
        
        return result

