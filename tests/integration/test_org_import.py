import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from ziora_imports.processors.org_processor import OrgProcessor

def test_org_import_end_to_end(mock_db_manager, mock_schema_config):
    """Test full OrgProcessor flow with mocked DB"""
    processor = OrgProcessor("test_tenant", mock_schema_config, mock_db_manager)
    
    # Sample data
    df = pd.DataFrame([{
        'org_id': 'ORG001',
        'org_name': 'Test Integration Org',
        'org_code': 'TI-ORG',
        'active': True
    }])
    df.attrs['file_path'] = 'test_org_logic.csv'
    
    # Mock session and execution
    mock_session = MagicMock()
    mock_db_manager.get_session.return_value = mock_session
    
    # Mock SP result
    mock_sp_result = MagicMock()
    mock_sp_result.inserted_count = 1
    mock_sp_result.updated_count = 0
    mock_sp_result.failed_count = 0
    mock_sp_result.processed_count = 1
    mock_session.execute.return_value.fetchone.return_value = mock_sp_result
    
    # Mock detailed results fetch
    mock_row = MagicMock()
    mock_row._mapping = {'org_id': 'ORG001', 'org_name': 'Test Integration Org', 'errormsg': None}
    mock_session.execute.return_value.fetchall.return_value = [mock_row]
    
    # BaseProcessor logic: transform then import
    transformed_df = processor._transform_data(df)
    result = processor._import_data(transformed_df)
    
    assert result['success'] is True
    assert result['processed_rows'] == 1
    assert mock_session.commit.called
