"""
Example usage script for Ziora Data Imports
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from ziora_imports.core.logger import setup_logger, get_logger
from ziora_imports.core.database import db_manager
from ziora_imports.config.tenant_config import TenantConfig
from ziora_imports.config.schema_config import SchemaConfig
from ziora_imports.processors import EmpProcessor, OrgProcessor, JobProcessor, SkillProcessor

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logger(log_level="INFO")


def example_import():
    """Example import function"""
    
    # Load configurations
    tenant_config = TenantConfig()
    schema_config = SchemaConfig()
    
    # Example: Import employee data
    tenant_name = "acme_corp"
    object_type = "emp"
    file_path = "data/employees.csv"
    
    logger.info(f"Example: Importing {object_type} data for tenant {tenant_name}")
    
    # Check if tenant exists
    if not tenant_config.is_tenant_enabled(tenant_name):
        logger.error(f"Tenant {tenant_name} not found or disabled")
        return
    
    # Test database connection
    if not db_manager.test_connection(tenant_name):
        logger.error(f"Database connection failed for tenant {tenant_name}")
        return
    
    # Get processor
    processor = EmpProcessor(tenant_name, schema_config, db_manager)
    
    # Process file (if it exists)
    if Path(file_path).exists():
        result = processor.process_file(file_path)
        logger.info(f"Import result: {result}")
    else:
        logger.warning(f"File not found: {file_path}")


if __name__ == "__main__":
    example_import()

