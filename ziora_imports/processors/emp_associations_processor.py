"""
Employee Associations data import processor
Handles associations between Employees and other objects (Org, Job, Skill, etc.)
"""

import pandas as pd
from typing import Dict, Any, Optional
from sqlalchemy import text

from .base_processor import BaseProcessor
from ..core.logger import get_logger
from ..core.fk_resolver import FKResolver

logger = get_logger(__name__)


class EmpAssociationsProcessor(BaseProcessor):
    """Processor for Employee Associations data imports"""
    
    # Object type mapping: Obj_Type -> (table_name, code_field, pk_field)
    # Maps Obj_Type to table lookup configuration
    OBJ_TYPE_MAP = {
        0: ("Organization", "org_code", "OrgPK"),  # Organization - lookup by org_code, PK is OrgPK
        1: ("Job", "job_code", "job_id"),  # Job - lookup by job_code, PK is job_id (or JobPK if different)
        2: ("Skill", "skill_code", "skill_id"),  # Skill - lookup by skill_code, PK is skill_id (or SkillPK if different)
        # Add more object types as needed
    }
    
    def __init__(self, tenant_name: str, schema_config, db_manager):
        super().__init__(tenant_name, 'emp_associations', schema_config, db_manager)
        self.fk_resolver = None
    
    def _transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform employee associations data"""
        df_transformed = df.copy()
        
        # Normalize column names (convert to lowercase, replace spaces with underscores)
        df_transformed.columns = df_transformed.columns.str.lower().str.replace(' ', '_')
        
        # Ensure Obj_Type is integer
        if 'obj_type' in df_transformed.columns:
            df_transformed['obj_type'] = pd.to_numeric(df_transformed['obj_type'], errors='coerce').astype('Int64')
        
        # Set AssociationType to Obj_Type if not provided
        if 'associationtype' in df_transformed.columns:
            df_transformed['associationtype'] = pd.to_numeric(df_transformed['associationtype'], errors='coerce').astype('Int64')
        else:
            df_transformed['associationtype'] = df_transformed.get('obj_type', None)
        
        return df_transformed
    
    def _resolve_object_fk(self, session, obj_type: int, obj_cd: str) -> Optional[int]:
        """
        Resolve object code to primary key based on Obj_Type
        
        Args:
            session: Database session
            obj_type: Object type (0=Org, 1=Job, 2=Skill, etc.)
            obj_cd: Object code value
        
        Returns:
            Primary key value or None if not found
        """
        if obj_type not in self.OBJ_TYPE_MAP:
            logger.warning(f"Unknown Obj_Type: {obj_type}")
            return None
        
        table_name, code_field, pk_field = self.OBJ_TYPE_MAP[obj_type]
        
        try:
            query = text(f"""
                SELECT {pk_field} 
                FROM {table_name} 
                WHERE {code_field} = :obj_cd
            """)
            
            result = session.execute(query, {"obj_cd": str(obj_cd).strip()}).fetchone()
            
            if result:
                return result[0]
            else:
                logger.warning(
                    f"Object lookup failed: {table_name}.{code_field}='{obj_cd}' "
                    f"not found (Obj_Type={obj_type})"
                )
                return None
                
        except Exception as e:
            logger.error(
                f"Error resolving object FK: {table_name}.{code_field}='{obj_cd}' "
                f"(Obj_Type={obj_type}) -> {pk_field}: {str(e)}"
            )
            return None
    
    def _import_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Import employee associations data into database"""
        result = {
            'success': False,
            'processed_rows': 0,
            'failed_rows': 0,
            'errors': []
        }
        
        session = self._get_session()
        
        if not self.fk_resolver:
            self.fk_resolver = FKResolver(session)
        
        try:
            processed = 0
            failed = 0
            
            for idx, row in df.iterrows():
                try:
                    # Get values
                    emp_no = row.get('emp_no')
                    obj_cd = row.get('obj_cd')
                    obj_type = row.get('obj_type')
                    association_type = row.get('associationtype', obj_type)
                    
                    # Validate required fields
                    if not emp_no or pd.isna(emp_no):
                        raise ValueError("Emp_No is required")
                    if not obj_cd or pd.isna(obj_cd):
                        raise ValueError("Obj_Cd is required")
                    if pd.isna(obj_type):
                        raise ValueError("Obj_Type is required")
                    
                    # Resolve Emp_No to PersonPK
                    person_pk = self.fk_resolver.resolve_person_number(str(emp_no))
                    if not person_pk:
                        raise ValueError(f"Person not found for Emp_No: {emp_no}")
                    
                    # Resolve Obj_Cd to object PK based on Obj_Type
                    obj_pk = self._resolve_object_fk(session, int(obj_type), str(obj_cd))
                    if not obj_pk:
                        raise ValueError(f"Object not found: Obj_Cd='{obj_cd}', Obj_Type={obj_type}")
                    
                    # Insert into EmpAssociations table
                    # Note: Adjust table name and column names based on your actual database schema
                    insert_query = text("""
                        INSERT INTO EmpAssociations (PersonFK, ObjFK, ObjType, AssociationType)
                        VALUES (:person_fk, :obj_fk, :obj_type, :association_type)
                        ON CONFLICT DO NOTHING
                    """)
                    
                    session.execute(insert_query, {
                        "person_fk": person_pk,
                        "obj_fk": obj_pk,
                        "obj_type": int(obj_type),
                        "association_type": int(association_type) if not pd.isna(association_type) else int(obj_type)
                    })
                    
                    processed += 1
                    
                except Exception as e:
                    failed += 1
                    error_msg = f"Row {idx + 1}: {str(e)}"
                    result['errors'].append({
                        'row_index': idx,
                        'error': error_msg
                    })
                    self.logger.error(error_msg)
            
            if processed > 0:
                session.commit()
                result['success'] = True
            
            result['processed_rows'] = processed
            result['failed_rows'] = failed
            
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

