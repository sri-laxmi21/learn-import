"""
Data validation module
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, ValidationError

from .logger import get_logger

logger = get_logger(__name__)


class ValidationResult:
    """Result of data validation"""
    
    def __init__(self):
        self.is_valid: bool = True
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.valid_rows: int = 0
        self.invalid_rows: int = 0
    
    def add_error(self, row_index: int, field: str, message: str, value: Any = None):
        """Add validation error"""
        self.is_valid = False
        self.invalid_rows += 1
        self.errors.append({
            'row_index': row_index,
            'field': field,
            'message': message,
            'value': value
        })
    
    def add_warning(self, row_index: int, field: str, message: str, value: Any = None):
        """Add validation warning"""
        self.warnings.append({
            'row_index': row_index,
            'field': field,
            'message': message,
            'value': value
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary"""
        return {
            'is_valid': self.is_valid,
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'valid_rows': self.valid_rows,
            'invalid_rows': self.invalid_rows
        }


class DataValidator:
    """Data validator for import files"""
    
    def __init__(self, schema_config: Dict[str, Any]):
        """
        Initialize validator with schema configuration
        
        Args:
            schema_config: Schema configuration dictionary
        """
        self.schema_config = schema_config
        self.logger = get_logger(__name__)
    
    def validate_schema(self, df: pd.DataFrame, object_type: str) -> ValidationResult:
        """
        Validate DataFrame against schema configuration
        
        Args:
            df: DataFrame to validate
            object_type: Type of object (emp, org, job, skill, etc.)
        
        Returns:
            ValidationResult object
        """
        result = ValidationResult()
        
        if object_type not in self.schema_config:
            result.add_error(0, 'schema', f"Schema not found for object type: {object_type}")
            return result
        
        schema = self.schema_config[object_type]
        required_fields = schema.get('required_fields', [])
        field_types = schema.get('field_types', {})
        field_validations = schema.get('validations', {})
        
        # Check required fields
        missing_fields = set(required_fields) - set(df.columns)
        if missing_fields:
            result.add_error(
                0, 'schema',
                f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        # Validate each row
        for idx, row in df.iterrows():
            row_valid = True
            
            # Check required fields have values
            for field in required_fields:
                if field in df.columns:
                    if pd.isna(row[field]) or str(row[field]).strip() == '':
                        result.add_error(
                            idx, field,
                            f"Required field '{field}' is empty",
                            row[field]
                        )
                        row_valid = False
            
            # Validate field types
            for field, expected_type in field_types.items():
                if field in df.columns and not pd.isna(row[field]):
                    try:
                        self._validate_type(row[field], expected_type)
                    except ValueError as e:
                        result.add_error(
                            idx, field,
                            f"Type validation failed: {str(e)}",
                            row[field]
                        )
                        row_valid = False
            
            # Run custom validations
            for field, validation_rules in field_validations.items():
                if field in df.columns and not pd.isna(row[field]):
                    validation_result = self._run_validations(
                        row[field], validation_rules, idx, field
                    )
                    if not validation_result:
                        row_valid = False
            
            if row_valid:
                result.valid_rows += 1
            else:
                result.invalid_rows += 1
        
        self.logger.info(
            f"Validation completed: {result.valid_rows} valid rows, "
            f"{result.invalid_rows} invalid rows"
        )
        
        return result
    
    def _validate_type(self, value: Any, expected_type: str) -> None:
        """Validate value type"""
        type_mapping = {
            'string': str,
            'integer': int,
            'float': float,
            'boolean': bool,
            'date': str,
            'datetime': str
        }
        
        if expected_type.lower() not in type_mapping:
            return
        
        python_type = type_mapping[expected_type.lower()]
        
        if expected_type.lower() in ['date', 'datetime']:
            # Date/datetime validation would be done separately
            return
        
        try:
            if python_type == bool:
                if isinstance(value, bool):
                    return
                if str(value).lower() in ['true', 'false', '1', '0', 'yes', 'no']:
                    return
                raise ValueError(f"Invalid boolean value: {value}")
            else:
                python_type(value)
        except (ValueError, TypeError):
            raise ValueError(f"Expected {expected_type}, got {type(value).__name__}")
    
    def _run_validations(
        self, value: Any, validation_rules: Dict[str, Any], 
        row_index: int, field: str
    ) -> bool:
        """Run custom validation rules"""
        # This can be extended with more validation rules
        # For now, just return True
        return True
    
    def validate_duplicates(
        self, df: pd.DataFrame, unique_fields: List[str]
    ) -> ValidationResult:
        """
        Validate for duplicate records
        
        Args:
            df: DataFrame to validate
            unique_fields: List of fields that should be unique
        
        Returns:
            ValidationResult object
        """
        result = ValidationResult()
        
        if not unique_fields:
            return result
        
        duplicates = df[df.duplicated(subset=unique_fields, keep=False)]
        
        if not duplicates.empty:
            for idx in duplicates.index:
                result.add_warning(
                    idx, 'duplicate',
                    f"Duplicate record found based on fields: {', '.join(unique_fields)}"
                )
        
        return result

