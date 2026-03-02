import pytest
import pandas as pd
from ziora_imports.core.validator import DataValidator

def test_validate_required_fields(mock_schema_config):
    """Test validation of required fields"""
    validator = DataValidator(mock_schema_config.schemas)
    
    # Missing org_name
    df = pd.DataFrame([{'org_id': 'ORG001'}])
    result = validator.validate_schema(df, 'org')
    
    assert not result.is_valid
    assert any('Missing required fields' in str(err) for err in result.errors)

def test_validate_types(mock_schema_config):
    """Test type validation"""
    validator = DataValidator(mock_schema_config.schemas)
    
    # Invalid integer for level
    df = pd.DataFrame([{'org_id': 'ORG001', 'org_name': 'Acme Corp', 'level': 'invalid'}])
    result = validator.validate_schema(df, 'org')
    
    assert not result.is_valid
    assert any('Type validation failed' in str(err) for err in result.errors)

def test_validate_duplicates(mock_schema_config):
    """Test duplicate detection"""
    validator = DataValidator(mock_schema_config.schemas)
    
    df = pd.DataFrame([
        {'org_id': 'ORG001', 'org_name': 'Acme Corp'},
        {'org_id': 'ORG001', 'org_name': 'Acme Corp Duplicate'}
    ])
    
    # validate_duplicates returns ValidationResult with warnings
    result = validator.validate_duplicates(df, ['org_id'])
    
    assert len(result.warnings) == 2
    assert all('Duplicate record found' in str(warn) for warn in result.warnings)

def test_valid_data(mock_schema_config, sample_org_df):
    """Test with completely valid data"""
    validator = DataValidator(mock_schema_config.schemas)
    result = validator.validate_schema(sample_org_df, 'org')
    
    assert result.is_valid
    assert result.valid_rows == 2
    assert len(result.errors) == 0
