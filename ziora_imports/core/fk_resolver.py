"""
Foreign Key Resolver Utility
Resolves code values to primary keys for foreign key fields
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session

from .logger import get_logger

logger = get_logger(__name__)


class FKResolver:
    """Resolves foreign key code values to primary keys"""
    
    def __init__(self, session: Session, common_fields_path: Optional[str] = None):
        """
        Initialize FK resolver
        
        Args:
            session: Database session
            common_fields_path: Path to common_fields.json (optional)
        """
        self.session = session
        self._cache: Dict[str, Dict[str, int]] = {}
        self._schema_ref_mappings: Dict[str, Dict[str, str]] = {}
        self._load_schema_ref_mappings(common_fields_path)
    
    def _load_schema_ref_mappings(self, config_path: Optional[str] = None):
        """Load schema reference mappings from common_fields.json file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "common_fields.json"
        
        try:
            config_path = Path(config_path)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self._schema_ref_mappings = config_data.get('schema_refs', {})
                logger.info(f"Loaded {len(self._schema_ref_mappings)} schema reference mappings")
            else:
                logger.warning(f"Common fields config file not found: {config_path}")
        except Exception as e:
            logger.error(f"Error loading schema ref mappings: {str(e)}")
    
    def resolve_fk_code(
        self,
        table_name: str,
        code_field: str,
        code_value: str,
        pk_field: str,
        cat_cd: Optional[int] = None
    ) -> Optional[int]:
        """
        Resolve a code value to primary key
        
        Args:
            table_name: Name of the referenced table
            code_field: Name of the code field (e.g., 'Lang_Cd', 'ItmCd')
            code_value: Code value from import file
            pk_field: Name of the primary key field (e.g., 'LangPK', 'ItmId')
            cat_cd: Category code for Code table lookups (optional)
        
        Returns:
            Primary key value or None if not found
        
        Raises:
            ValueError: If code value is required but not found
        """
        if not code_value or (isinstance(code_value, str) and code_value.strip() == ''):
            return None
        
        # Check cache first (include cat_cd in cache key if provided)
        cache_key = f"{table_name}:{code_field}"
        if cat_cd is not None:
            cache_key = f"{cache_key}:CatCd={cat_cd}"
        
        if cache_key in self._cache:
            if code_value in self._cache[cache_key]:
                return self._cache[cache_key][code_value]
        
        try:
            # For Code table with CatCd, use composite lookup
            if table_name == "Code" and cat_cd is not None:
                query = text(f"""
                    SELECT {pk_field} 
                    FROM {table_name} 
                    WHERE CatCd = :cat_cd AND {code_field} = :code_value
                """)
                params = {
                    "cat_cd": cat_cd,
                    "code_value": str(code_value).strip()
                }
            else:
                # Standard lookup
                query = text(f"""
                    SELECT {pk_field} 
                    FROM {table_name} 
                    WHERE {code_field} = :code_value
                """)
                params = {"code_value": str(code_value).strip()}
            
            result = self.session.execute(query, params).fetchone()
            
            if result:
                pk_value = result[0]
                
                # Cache the result
                if cache_key not in self._cache:
                    self._cache[cache_key] = {}
                self._cache[cache_key][code_value] = pk_value
                
                return pk_value
            else:
                logger.warning(
                    f"FK lookup failed: {table_name}.{code_field}='{code_value}' "
                    f"{f'(CatCd={cat_cd}) ' if cat_cd is not None else ''}"
                    f"not found (looking for {pk_field})"
                )
                return None
                
        except Exception as e:
            logger.error(
                f"Error resolving FK: {table_name}.{code_field}='{code_value}' "
                f"{f'(CatCd={cat_cd}) ' if cat_cd is not None else ''}"
                f"-> {pk_field}: {str(e)}"
            )
            raise
    
    def resolve_person_number(self, person_number: str) -> Optional[int]:
        """
        Resolve PersonNumber to PersonPK
        
        Args:
            person_number: PersonNumber value
        
        Returns:
            PersonPK or None if not found
        """
        return self.resolve_fk_code(
            table_name="Person",
            code_field="PersonNumber",
            code_value=person_number,
            pk_field="PersonPK"
        )
    
    def resolve_role_code(self, role_code: str) -> Optional[int]:
        """
        Resolve Role_Cd to RolePK
        
        Args:
            role_code: Role code value
        
        Returns:
            RolePK or None if not found
        """
        return self.resolve_fk_code(
            table_name="Roles",
            code_field="Role_Cd",
            code_value=role_code,
            pk_field="RolePK"
        )
    
    def resolve_lang_code(self, lang_code: str) -> Optional[int]:
        """
        Resolve Lang_Cd to LangPK
        
        Args:
            lang_code: Language code value
        
        Returns:
            LangPK or None if not found
        """
        return self.resolve_fk_code(
            table_name="Lang",
            code_field="Lang_Cd",
            code_value=lang_code,
            pk_field="LangPK"
        )
    
    def resolve_timezone_code(self, timezone_code: str) -> Optional[int]:
        """
        Resolve Timezone_Cd to TimezonePK
        
        Args:
            timezone_code: Timezone code value
        
        Returns:
            TimezonePK or None if not found
        """
        return self.resolve_fk_code(
            table_name="Timezone",
            code_field="Timezone_Cd",
            code_value=timezone_code,
            pk_field="TimezonePK"
        )
    
    def resolve_currency_code(self, currency_code: str) -> Optional[int]:
        """
        Resolve Currency_Cd to CurrencyPK
        
        Args:
            currency_code: Currency code value
        
        Returns:
            CurrencyPK or None if not found
        """
        return self.resolve_fk_code(
            table_name="Currency",
            code_field="Currency_Cd",
            code_value=currency_code,
            pk_field="CurrencyPK"
        )
    
    def resolve_code(
        self,
        code_value: str,
        cat_cd: int
    ) -> Optional[int]:
        """
        Resolve ItmCd to ItmId from Code table with specific CatCd
        
        Args:
            code_value: Item code value (ItmCd)
            cat_cd: Category code (CatCd) - static value that identifies the code category
        
        Returns:
            ItmId or None if not found
        """
        return self.resolve_fk_code(
            table_name="Code",
            code_field="ItmCd",
            code_value=code_value,
            pk_field="ItmId",
            cat_cd=cat_cd
        )
    
    def resolve_fk_from_schema(
        self,
        field_name: str,
        field_value: str,
        schema: Dict[str, Any]
    ) -> Optional[int]:
        """
        Resolve FK using schema configuration
        
        Args:
            field_name: Name of the field
            field_value: Value from import file
            schema: Schema configuration dictionary
        
        Returns:
            Primary key value or None if not found
        """
        fk_mappings = schema.get('fk_mappings', {})
        
        if field_name not in fk_mappings:
            return None
        
        mapping = fk_mappings[field_name]
        table_name = mapping['table']
        pk_field = mapping['pk_field']
        code_field = mapping['code_field']
        cat_cd = mapping.get('cat_cd')  # Optional CatCd for Code table
        
        return self.resolve_fk_code(
            table_name=table_name,
            code_field=code_field,
            code_value=field_value,
            pk_field=pk_field,
            cat_cd=cat_cd
        )
    
    def resolve_fk_from_field_config(
        self,
        field_name: str,
        field_value: str,
        field_config: Dict[str, Any]
    ) -> Optional[int]:
        """
        Resolve FK using field configuration (from field_types or common_fields)
        Supports simplified attributes: schema_ref and cat_cd_ref
        
        Args:
            field_name: Name of the field
            field_value: Value from import file
            field_config: Field configuration dictionary
        
        Returns:
            Primary key value or None if not found
        """
        # Check for cat_cd_ref (Code table reference)
        if 'cat_cd_ref' in field_config:
            cat_cd = field_config['cat_cd_ref']
            return self.resolve_code(
                code_value=field_value,
                cat_cd=cat_cd
            )
        
        # Check for schema_ref (other table references)
        if 'schema_ref' in field_config:
            schema_ref = field_config['schema_ref']
            if schema_ref in self._schema_ref_mappings:
                mapping = self._schema_ref_mappings[schema_ref]
                return self.resolve_fk_code(
                    table_name=mapping['table'],
                    code_field=mapping['code_field'],
                    code_value=field_value,
                    pk_field=mapping['pk_field']
                )
            else:
                logger.warning(f"Unknown schema_ref: {schema_ref} for field {field_name}")
                return None
        
        # Fallback to old format for backward compatibility
        if 'fk_reference' in field_config:
            table_name = field_config['fk_reference']
            pk_field = field_config.get('fk_field')
            code_field = field_config.get('fk_code_field')
            cat_cd = field_config.get('cat_cd')
            
            if pk_field and code_field:
                return self.resolve_fk_code(
                    table_name=table_name,
                    code_field=code_field,
                    code_value=field_value,
                    pk_field=pk_field,
                    cat_cd=cat_cd
                )
        
        return None
    
    def clear_cache(self):
        """Clear the FK resolution cache"""
        self._cache.clear()

