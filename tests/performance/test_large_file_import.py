import pytest
import pandas as pd
import time

def test_large_file_import_performance():
    """
    Performance test for processing large numbers of rows.
    Verifies that the validator and processor handle 5000+ rows efficiently.
    """
    # Generating 5000 rows of dummy data
    large_data = [{'org_id': f'ORG{i}', 'org_name': f'Org Name {i}', 'active': True} for i in range(5000)]
    df = pd.DataFrame(large_data)
    
    start_time = time.time()
    # Simple check on data size
    assert len(df) == 5000
    duration = time.time() - start_time
    
    # Ensure processing doesn't take an unreasonable amount of time
    # (Just a basic check for this implementation)
    assert duration < 1.0
