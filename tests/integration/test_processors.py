import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from ziora_imports.processors.base_processor import BaseProcessor
from ziora_imports.processors.org_processor import OrgProcessor
from ziora_imports.processors.emp_processor import EmpProcessor

class MockProcessor(BaseProcessor):
    """Mock implementation of BaseProcessor for testing"""
    def _import_data(self, df: pd.DataFrame):
        return {'success': True, 'processed_rows': len(df), 'failed_rows': 0}

@pytest.fixture
def mock_db_manager():
    return MagicMock()

@pytest.fixture
def mock_schema_config():
    config = MagicMock()
    config.schemas = {
        'org': {
            'required_fields': ['org_id', 'org_name'],
            'field_types': {'org_id': 'string'}
        }
    }
    config.get_unique_fields.return_value = ['org_id']
    return config

def test_base_processor_load_csv(tmp_path, mock_db_manager, mock_schema_config):
    """Test loading a CSV file in BaseProcessor"""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("org_id,org_name\nORG001,Acme Corp")
    
    processor = MockProcessor("test_tenant", "org", mock_schema_config, mock_db_manager)
    df = processor._load_file(str(csv_file))
    
    assert len(df) == 1
    assert df.iloc[0]['org_id'] == 'ORG001'

def test_base_processor_process_flow(tmp_path, mock_db_manager, mock_schema_config):
    """Test the full process_file flow with mocks"""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("org_id,org_name\nORG001,Acme Corp")
    
    processor = MockProcessor("test_tenant", "org", mock_schema_config, mock_db_manager)
    result = processor.process_file(str(csv_file))
    
    assert result['success']
    assert result['total_rows'] == 1
    assert result['processed_rows'] == 1
    assert result['failed_rows'] == 0

def test_base_processor_validation_failure(tmp_path, mock_db_manager, mock_schema_config):
    """Test process_file handles validation failures"""
    csv_file = tmp_path / "test.csv"
    # Missing required field 'org_name'
    csv_file.write_text("org_id\nORG001")
    
    processor = MockProcessor("test_tenant", "org", mock_schema_config, mock_db_manager)
    result = processor.process_file(str(csv_file))
    
    # Validation failure in BaseProcessor still calls _import_data for the rows that might be valid?
    # Wait, looking at BaseProcessor.process_file:
    # if not validation_result.is_valid:
    #     result['errors'].extend(validation_result.errors)
    #     result['failed_rows'] = validation_result.invalid_rows
    # ... but it continues to transform and import!
    
    # In my MockProcessor, it just returns success.
    # In a real processor, it would handle the invalid rows.
    
    assert len(result['errors']) > 0

def test_org_processor_deduplication(tmp_path, mock_db_manager, mock_schema_config):
    """Test OrgProcessor's custom deduplication logic"""
    csv_file = tmp_path / "org_with_dupes.csv"
    # Duplicate org_code: ACME-HQ
    csv_file.write_text("org_id,org_name,org_code\nORG001,Acme HQ,ACME-HQ\nORG002,Acme Duplicate,ACME-HQ")
    
    processor = OrgProcessor("test_tenant", mock_schema_config, mock_db_manager)
    df = processor._load_file(str(csv_file))
    
    # Should only keep the first row
    assert len(df) == 1
    assert df.iloc[0]['org_id'] == 'ORG001'

def test_emp_processor_normalization(mock_db_manager, mock_schema_config):
    """Test EmpProcessor's data transformation logic"""
    df = pd.DataFrame([{'PersonNumber': 'EMP001', 'Email': ' JOHN@Example.Com ', 'Phone': '(123) 456-7890'}])
    
    processor = EmpProcessor("test_tenant", mock_schema_config, mock_db_manager)
    df_transformed = processor._transform_data(df)
    
    # Email should be lowercase and stripped
    assert df_transformed.iloc[0]['email'] == 'john@example.com'
    # Phone should be numbers only
    assert df_transformed.iloc[0]['phone'] == '1234567890'
    # Column names should be normalized
    assert 'personnumber' in df_transformed.columns
