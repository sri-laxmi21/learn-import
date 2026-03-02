# Ziora Data Imports - Usage Guide

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

### 2. Configuration

#### Environment Variables

Create a `.env` file in the project root:

```env
# Database URLs for each tenant
ACME_CORP_DB_URL=postgresql://user:password@localhost:5432/acme_corp_db
TECHNOVA_DB_URL=postgresql://user:password@localhost:5432/technova_db

# Logging configuration
LOG_LEVEL=INFO
LOG_DIR=logs
```

#### Tenant Configuration

Edit `config/tenants.yaml` to add or modify tenants:

```yaml
tenants:
  your_tenant:
    display_name: "Your Tenant Name"
    database_url_env: "YOUR_TENANT_DB_URL"
    enabled: true
    metadata:
      description: "Description"
```

#### Schema Configuration

Edit `config/schemas.yaml` to define file formats and validation rules for each object type.

### 3. Running Imports

#### Command Line Usage

```bash
python main.py --tenant <tenant_name> --object <object_type> --file <file_path>
```

Examples:

```bash
# Import employee data
python main.py --tenant acme_corp --object emp --file data/employees.csv

# Import organization data
python main.py --tenant technova --object org --file data/organizations.xlsx

# Import job data with debug logging
python main.py --tenant acme_corp --object job --file data/jobs.csv --log-level DEBUG
```

#### Programmatic Usage

```python
from ziora_imports.core.logger import setup_logger
from ziora_imports.core.database import db_manager
from ziora_imports.config.tenant_config import TenantConfig
from ziora_imports.config.schema_config import SchemaConfig
from ziora_imports.processors import EmpProcessor

# Setup
logger = setup_logger()
tenant_config = TenantConfig()
schema_config = SchemaConfig()

# Get processor
processor = EmpProcessor("acme_corp", schema_config, db_manager)

# Process file
result = processor.process_file("data/employees.csv")

print(f"Success: {result['success']}")
print(f"Processed: {result['processed_rows']} rows")
```

## File Format Requirements

### Employee (emp) Import

Required columns:
- `employee_id` (string, unique)
- `name` (string)
- `email` (string, unique, must be valid email)

Optional columns:
- `phone` (string)
- `department` (string)
- `hire_date` (date)
- `salary` (float)
- `active` (boolean)

### Organization (org) Import

Required columns:
- `org_id` (string, unique)
- `org_name` (string)

Optional columns:
- `org_code` (string, unique)
- `parent_org_id` (string)
- `address` (string)
- `city` (string)
- `country` (string)
- `active` (boolean)

### Job (job) Import

Required columns:
- `job_id` (string, unique)
- `job_title` (string)

Optional columns:
- `job_code` (string, unique)
- `department` (string)
- `level` (integer, 1-10)
- `min_salary` (float)
- `max_salary` (float)
- `active` (boolean)

### Skill (skill) Import

Required columns:
- `skill_id` (string, unique)
- `skill_name` (string)

Optional columns:
- `skill_code` (string, unique)
- `category` (string)
- `description` (string)
- `level` (integer, 1-5)
- `active` (boolean)

## Supported File Formats

- **CSV files** (`.csv`) - Comma-delimited
- **Excel files** (`.xlsx`, `.xls`) - Excel format
- **Text files** (`.txt`) - Pipe-delimited (`|`)

The system automatically detects the file format based on the file extension and processes accordingly.

## Logging

Logs are written to:
- Console (INFO level and above)
- File: `logs/{tenant_name}/{object_type}_YYYYMMDD.log` (DEBUG level and above)
  - Example: `logs/acme_corp/emp_20240101.log`
  - Example: `logs/technova/job_20240101.log`

Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

Each object type gets its own log file within the tenant directory for better organization.

## Error Handling

The import process validates data before importing:
1. **Schema Validation**: Checks required fields, data types, and format
2. **Duplicate Detection**: Identifies duplicate records based on unique fields
3. **Data Transformation**: Normalizes and cleans data
4. **Database Import**: Inserts validated data with error handling

Errors are logged and reported in the import result.

## Adding New Object Types

1. Create a new processor class in `ziora_imports/processors/`:

```python
from .base_processor import BaseProcessor

class YourObjectProcessor(BaseProcessor):
    def __init__(self, tenant_name, schema_config, db_manager):
        super().__init__(tenant_name, 'your_object', schema_config, db_manager)
    
    def _import_data(self, df):
        # Implement your import logic
        pass
```

2. Add schema configuration in `config/schemas.yaml`
3. Register processor in `main.py` PROCESSOR_MAP

## Multi-Tenant Architecture

- Each tenant has a separate database connection
- Database URLs are configured via environment variables
- Tenant configuration is managed in `config/tenants.yaml`
- All tenants share the same codebase and schema definitions

