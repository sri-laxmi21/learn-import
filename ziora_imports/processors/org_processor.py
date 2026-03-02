"""
Organization data import processor
"""

import pandas as pd
from typing import Dict, Any

from .base_processor import BaseProcessor
from ..core.logger import get_logger

logger = get_logger(__name__)


class OrgProcessor(BaseProcessor):
    """Processor for Organization data imports"""
    def __init__(self, tenant_name: str, schema_config, db_manager):
        super().__init__(tenant_name, 'org', schema_config, db_manager)
    def _load_file(self, file_path: str) -> pd.DataFrame:
        """
        Override load_file to pre-process data before validation
        """
        df = super()._load_file(file_path)
        
        # 1. Deduplicate based on org_code (case insensitive check for column)
        # We need to find the column name that corresponds to 'org_code'
        org_code_col = next((col for col in df.columns if col.strip().lower() == 'org_code'), None)
        if org_code_col:
            initial_count = len(df)
            df = df.drop_duplicates(subset=[org_code_col], keep='first')
            if len(df) < initial_count:
                self.logger.info(f"Dropped {initial_count - len(df)} duplicate rows based on {org_code_col}")
        
        # 2. Clean active field
        active_col = next((col for col in df.columns if col.strip().lower() == 'active'), None)
        if active_col:
            def clean_active_pre(val):
                if pd.isna(val): return 1
                s_val = str(val).lower().strip()
                if s_val in ['1', 'true', 'yes', 'y', 'en']: 
                    return 1
                return 0 # Default to 0 for unknown False-like values
            df[active_col] = df[active_col].apply(clean_active_pre)
            
        return df

    def _transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform organization data"""
        df_transformed = df.copy()
        # Normalize column names
        df_transformed.columns = df_transformed.columns.str.lower().str.replace(' ', '_')
        
        # Example transformations
        if 'org_name' in df_transformed.columns:
            df_transformed['org_name'] = df_transformed['org_name'].str.strip()
        
        if 'org_code' in df_transformed.columns:
            df_transformed['org_code'] = df_transformed['org_code'].str.upper().str.strip()
            
        return df_transformed
    
    def _import_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Import organization data into DI_org table
        
        After file validation, data is loaded into the temp table with processstatus = 0 (Pending).
        Actual processing from temp table to Organization table happens at DB level.
        """
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
            # Get file name from the dataframe attributes or use a default
            file_path = df.attrs.get('file_path', 'org_import.csv')
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
                {"file_name": Path(file_name).name}
            )
            run_id = result_fileimport.scalar()
            self.logger.info(f"Created fileImport record with importPK: {run_id}")
            
            # Step 2: Insert data into DI_org table
            self.logger.info(f"Inserting {len(df)} rows into DI_org table")
            processed = 0
            failed = 0
            insert_stmt = text("""
                INSERT INTO DI_org (
                    runId, org_id, org_name, org_code, OrgType, parent_org_id,
                    address, city, country,
                    Description, active,
                    Lang_Cd, Timezone_Cd, CountryCode,
                    processstatus, deleted
                )
                VALUES (
                    :runId, :org_id, :org_name, :org_code, :OrgType, :parent_org_id,
                    :address, :city, :country,
                    :Description, :active,
                    :Lang_Cd, :Timezone_Cd, :CountryCode,
                    0, 0
                )
            """)
            
            for idx, row in df.iterrows():
                try:
                    # Active is cleaned in _load_file, but ensure safe access
                    active_value = row.get('active', 1)
                    
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
                            'org_id': to_null(row.get('org_id')),
                            'org_name': to_null(row.get('org_name')),
                            'org_code': to_null(row.get('org_code')),
                            'OrgType': to_null(row.get('orgtype')),  # lowercase from transform
                            'parent_org_id': to_null(row.get('parent_org_id')),
                            'address': to_null(row.get('address')),
                            'city': to_null(row.get('city')),
                            'country': to_null(row.get('country')),
                            'Description': to_null(row.get('description')),  # lowercase from transform
                            'active': active_value,
                            'Lang_Cd': to_null(row.get('lang_cd')),  # lowercase from transform
                            'Timezone_Cd': to_null(row.get('timezone_cd')),  # lowercase from transform
                            'CountryCode': to_null(row.get('countrycode'))  # lowercase from transform
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
            
            # Step 2.5: Call stored procedure
            self.logger.info(f"Calling DI_processOrgs stored procedure with run_id={run_id}")
            
            # Commit inserts to make them visible to SP
            session.commit()
            
            # Explicit cast using standard SQL syntax to avoid ambiguity and syntax errors
            sp_result = session.execute(
                text("SELECT * FROM DI_processOrgs(CAST(:run_id AS INTEGER))"),
                {"run_id": run_id}
            ).fetchone()
            
            session.commit()
            
            self.logger.info(
                f"DI_processOrgs completed | "
                f"Inserted: {sp_result.inserted_count}, "
                f"Updated: {sp_result.updated_count}, "
                f"Failed: {sp_result.failed_count}"
            )

            # Step 2.6: Log detailed record results
            from ..core.logger import ZioraLogger
            
            # Fetch all records for this run to log details
            detailed_results = session.execute(
                text("SELECT * FROM DI_org WHERE runId = :run_id ORDER BY processfilepk"),
                {"run_id": run_id}
            ).fetchall()

            for row in detailed_results:
                # Use _mapping to access columns by name (SQLAlchemy Row object)
                mapping = row._mapping
                
                # Create a dict of relevant fields to log
                log_fields = {
                    'org_id': mapping.get('org_id'),
                    'org_name': mapping.get('org_name'),
                    'org_code': mapping.get('org_code'),
                    'OrgType': mapping.get('orgtype'), # PG lowercases unquoted names
                    'parent_org_id': mapping.get('parent_org_id'),
                    'address': mapping.get('address'),
                    'city': mapping.get('city'),
                    'country': mapping.get('country'),
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
                warnings=0, # Summary doesn't explicitly track warnings yet in result set, but we can count if needed
                failed=sp_result.failed_count
            )

            # Step 3: Update fileImport status to InProgress
            if sp_result.processed_count > 0 or sp_result.failed_count == 0:
                update_fileimport = text("""
                    UPDATE fileImport
                    SET Status = 1, EndDtTime = timezone('utc', now())
                    WHERE importPK = :run_id
                """)
                session.execute(update_fileimport, {"run_id": run_id})
                session.commit()
                result['success'] = True
                self.logger.info(f"Successfully inserted {processed} rows into DI_org (runId: {run_id})")
            else:
                # No rows processed, mark as failed
                update_fileimport = text("""
                    UPDATE fileImport
                    SET Status = 2, EndDtTime = timezone('utc', now())
                    WHERE importPK = :run_id
                """)
                session.execute(update_fileimport, {"run_id": run_id})
                session.commit()
            
            result['processed_rows'] = processed
            result['failed_rows'] = failed
            result['run_id'] = run_id  # Return runId for reference
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error during import: {str(e)}", exc_info=True)
            result['errors'].append({
                'type': 'import_error',
                'message': str(e)
            })
        finally:
            session.close()
        
        return result

