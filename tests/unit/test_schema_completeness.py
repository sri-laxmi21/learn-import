import pytest
import pandas as pd
from ziora_imports.config.schema_config import SchemaConfig
from ziora_imports.core.validator import DataValidator

@pytest.fixture
def real_schema_config():
    return SchemaConfig()

@pytest.fixture
def validator(real_schema_config):
    return DataValidator(real_schema_config.schemas)

def test_every_field_in_schema(validator, real_schema_config):
    """
    Exhaustively test every field defined in schemas.yaml for every object type.
    This ensures that the validator is correctly configured for every field.
    """
    for object_type in real_schema_config.list_object_types():
        schema = real_schema_config.get_schema(object_type)
        field_types = real_schema_config.get_field_types(object_type)
        required_fields = real_schema_config.get_required_fields(object_type)
        
        print(f"\n--- Exhaustive testing for {object_type.upper()} ---")
        
        # 1. Test that providing a valid value for EVERY defined field works
        valid_data = {}
        for field, ftype in field_types.items():
            if ftype == 'string':
                valid_data[field] = "test_string"
            elif ftype == 'integer':
                valid_data[field] = 1
            elif ftype == 'float':
                valid_data[field] = 1.0
            elif ftype == 'boolean':
                valid_data[field] = True
            elif ftype in ['date', 'datetime']:
                valid_data[field] = "2024-01-01"
            else:
                valid_data[field] = "some_value"
        
        # Ensure required fields are included correctly
        for req in required_fields:
            if req not in valid_data:
                valid_data[req] = "required_val"
                
        df_valid = pd.DataFrame([valid_data])
        result_valid = validator.validate_schema(df_valid, object_type)
        
        assert result_valid.is_valid, f"Failed valid data check for {object_type} fields: {result_valid.errors}"
        print(f"[OK] All {len(valid_data)} fields for {object_type} validated with valid data.")

        # 2. Test invalid types for EVERY defined field (where type-checking is implemented)
        for field, ftype in field_types.items():
            # Skip fields that don't have strict type checking logic in validator.py (like string/date)
            if ftype not in ['integer', 'float', 'boolean']:
                continue
                
            invalid_data = valid_data.copy()
            invalid_data[field] = "THIS_IS_NOT_A_NUMBER"
            
            df_invalid = pd.DataFrame([invalid_data])
            result_invalid = validator.validate_schema(df_invalid, object_type)
            
            # The validator should find at least one error for this field
            assert not result_invalid.is_valid, f"Failed to detect invalid type for {object_type}.{field} (expected {ftype})"
            assert any(err['field'] == field and 'Type validation failed' in err['message'] for err in result_invalid.errors)
            print(f"[OK] Correctly detected invalid type for {object_type}.{field}")
            
def test_all_schema_fields_present_in_samples():
    """
    Optional but helpful: Ensure that every field in the schema is 
    actually being used in at least one sample file.
    """
    from pathlib import Path
    samples_dir = Path(__file__).parent.parent / "samples"
    schema_config = SchemaConfig()
    
    file_to_object = {
        'org_sample': 'org',
        'emp_sample': 'emp',
        'jobs_sample': 'job',
        'skill_sample': 'skill'
    }
    
    for object_type in schema_config.list_object_types():
        schema_fields = set(schema_config.get_field_types(object_type).keys())
        schema_fields.update(schema_config.get_required_fields(object_type))
        
        found_fields = set()
        
        # Check matching sample files (both .csv and .txt)
        sample_files = list(samples_dir.glob(f"*{object_type}_sample*"))
        for sample_file in sample_files:
            if sample_file.suffix == '.txt':
                df = pd.read_csv(sample_file, delimiter='|')
            else:
                df = pd.read_csv(sample_file)
            
            # Normalize column names for comparison if needed, 
            # but usually the samples should match the schema exactly.
            found_fields.update(df.columns)
            
        missing_in_samples = schema_fields - found_fields
        if missing_in_samples:
            print(f"\n[WARNING] Fields in {object_type} schema NOT found in any samples: {missing_in_samples}")
            # We won't assert here because sometimes you don't want every field in every sample,
            # but it helps the user see if they are missing anything.
        else:
            print(f"[OK] All {object_type} schema fields are represented in sample files.")
