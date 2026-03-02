import pytest
import pandas as pd
from ziora_imports.core.validator import DataValidator

def test_duplicate_detection_in_dataframe():
    """Test validator detection of duplicates in input data"""
    schemas = {
        'test_obj': {
            'unique_fields': ['id_field'],
            'required_fields': ['id_field'],
            'field_types': {'id_field': 'string'}
        }
    }
    validator = DataValidator(schemas)
    
    # Data with duplicate id_field
    df = pd.DataFrame([
        {'id_field': 'UNIQUE1', 'data': 'val1'},
        {'id_field': 'UNIQUE1', 'data': 'val2'}
    ])
    
    # In this implementation, duplicates are checked via validate_duplicates
    result = validator.validate_duplicates(df, ['id_field'])
    
    # Validator returns warnings for duplicates
    assert any("Duplicate" in err['message'] for err in result.warnings)
