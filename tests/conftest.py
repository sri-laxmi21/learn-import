import pytest
import pandas as pd
from unittest.mock import MagicMock

@pytest.fixture
def mock_schema_config():
    """Mock SchemaConfig that returns predictable schema data"""
    mock = MagicMock()
    mock.schemas = {
        'org': {
            'required_fields': ['org_id', 'org_name'],
            'field_types': {
                'org_id': 'string',
                'active': 'boolean',
                'level': 'integer'
            },
            'validations': {
                'org_id': {'min_length': 1}
            },
            'unique_fields': ['org_id']
        },
        'emp': {
            'required_fields': ['PersonNumber'],
            'field_types': {
                'PersonNumber': 'string',
                'Email': 'string',
                'Active': 'integer'
            },
            'unique_fields': ['PersonNumber']
        },
        'job': {
             'required_fields': ['job_id', 'job_title'],
             'field_types': {
                'job_id': 'string',
                'job_title': 'string'
            }
        },
        'skill': {
             'required_fields': ['skill_id', 'skill_name'],
             'field_types': {
                'skill_id': 'string',
                'skill_name': 'string'
            }
        }
    }
    mock.get_required_fields.side_effect = lambda obj: mock.schemas[obj].get('required_fields', [])
    mock.get_field_types.side_effect = lambda obj: mock.schemas[obj].get('field_types', {})
    mock.get_unique_fields.side_effect = lambda obj: mock.schemas[obj].get('unique_fields', [])
    mock.list_object_types.return_value = list(mock.schemas.keys())
    mock.get_schema.side_effect = lambda obj: mock.schemas[obj]
    return mock

@pytest.fixture
def mock_db_manager():
    """Mock DatabaseManager"""
    mock = MagicMock()
    mock.get_session.return_value = MagicMock()
    return mock

@pytest.fixture
def sample_org_df():
    return pd.DataFrame([
        {'org_id': 'ORG001', 'org_name': 'Acme Corp', 'active': True, 'level': 1},
        {'org_id': 'ORG002', 'org_name': 'Tech Nova', 'active': False, 'level': 2}
    ])
