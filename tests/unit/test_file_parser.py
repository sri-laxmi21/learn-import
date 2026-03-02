import pytest
import pandas as pd
from ziora_imports.processors.base_processor import BaseProcessor
from unittest.mock import MagicMock

class SimpleProcessor(BaseProcessor):
    def _transform_data(self, df): return df
    def _import_data(self, df): return {"success": True}

@pytest.fixture
def processor(mock_schema_config, mock_db_manager):
    return SimpleProcessor("test_tenant", "org", mock_schema_config, mock_db_manager)

def test_load_csv_file(processor, tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("col1,col2\nval1,val2")
    df = processor._load_file(str(csv_file))
    assert len(df) == 1
    assert list(df.columns) == ["col1", "col2"]

def test_load_txt_pipe_file(processor, tmp_path):
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("col1|col2\nval1|val2")
    df = processor._load_file(str(txt_file))
    assert len(df) == 1
    assert list(df.columns) == ["col1", "col2"]

def test_load_excel_file(processor, tmp_path):
    try:
        import openpyxl
        excel_file = tmp_path / "test.xlsx"
        df_new = pd.DataFrame([{"col1": "val1", "col2": "val2"}])
        df_new.to_excel(excel_file, index=False)
        df = processor._load_file(str(excel_file))
        assert len(df) == 1
    except ImportError:
        pytest.skip("openpyxl not installed")
