# Ziora Data Imports - Project Structure

## Overview

This is a multi-tenant Python project for importing data into the Ziora system. It supports multiple object types (Employee, Organization, Job, Skill, etc.) with separate databases for each tenant.

## Directory Structure

```
Learn_Imports/
│
├── ziora_imports/              # Main package
│   ├── __init__.py            # Package initialization
│   │
│   ├── config/                 # Configuration modules
│   │   ├── __init__.py
│   │   ├── tenant_config.py   # Tenant configuration management
│   │   └── schema_config.py   # Schema/file format configuration
│   │
│   ├── core/                   # Core functionality
│   │   ├── __init__.py
│   │   ├── logger.py          # Centralized logging module
│   │   ├── database.py        # Multi-tenant database management
│   │   └── validator.py       # Data validation module
│   │
│   ├── processors/             # Import processors
│   │   ├── __init__.py
│   │   ├── base_processor.py  # Base processor class
│   │   ├── emp_processor.py   # Employee import processor
│   │   ├── org_processor.py   # Organization import processor
│   │   ├── job_processor.py   # Job import processor
│   │   └── skill_processor.py # Skill import processor
│   │
│   └── utils/                  # Utility modules
│       ├── __init__.py
│       └── file_handler.py    # File handling utilities
│
├── config/                      # Configuration files
│   ├── tenants.yaml            # Tenant definitions
│   └── schemas.yaml            # Schema definitions for each object type
│
├── logs/                        # Log files directory (created automatically)
│
├── main.py                      # Main entry point
├── example_usage.py            # Example usage script
├── setup.py                     # Package setup script
├── requirements.txt             # Python dependencies
├── README.md                    # Project documentation
├── USAGE.md                     # Usage guide
├── PROJECT_STRUCTURE.md         # This file
└── .gitignore                   # Git ignore rules

```

## Key Components

### 1. Core Modules (`ziora_imports/core/`)

#### `logger.py`
- Centralized logging for all file processing and validation
- Supports console and file logging
- Configurable log levels and file formats
- Singleton pattern for logger instances

#### `database.py`
- Multi-tenant database connection management
- Separate database connections per tenant
- Connection pooling and session management
- Database connection testing

#### `validator.py`
- Schema validation against configuration
- Data type validation
- Required field validation
- Duplicate detection
- Custom validation rules

### 2. Configuration (`ziora_imports/config/`)

#### `tenant_config.py`
- Loads tenant configuration from YAML
- Validates tenant settings
- Manages tenant enable/disable status

#### `schema_config.py`
- Loads schema definitions from YAML
- Defines file formats for each object type
- Manages field types, required fields, and validation rules

### 3. Processors (`ziora_imports/processors/`)

#### `base_processor.py`
- Abstract base class for all processors
- Common file loading, validation, and transformation logic
- Template method pattern for import workflow

#### Specific Processors
- `emp_processor.py`: Employee data imports
- `org_processor.py`: Organization data imports
- `job_processor.py`: Job/Position data imports
- `skill_processor.py`: Skill data imports

Each processor:
- Extends `BaseProcessor`
- Implements object-specific transformations
- Handles database insertion logic

### 4. Configuration Files (`config/`)

#### `tenants.yaml`
- Defines all tenants
- Maps tenant names to database environment variables
- Tenant metadata and settings

#### `schemas.yaml`
- Defines file formats for each object type
- Required fields, field types, validation rules
- Unique field constraints

## Data Flow

```
1. User runs: python main.py --tenant <tenant> --object <type> --file <path>
   │
   ├─> Load tenant configuration
   ├─> Load schema configuration
   ├─> Test database connection
   │
2. File Processing
   │
   ├─> Load file (CSV/Excel)
   ├─> Validate schema (required fields, types, format)
   ├─> Check for duplicates
   ├─> Transform data (normalize, clean)
   │
3. Database Import
   │
   ├─> Get database session for tenant
   ├─> Insert records (with error handling)
   ├─> Commit transaction
   │
4. Results
   │
   └─> Return processing results (success, errors, warnings)
```

## Extension Points

### Adding a New Object Type

1. Create processor: `ziora_imports/processors/new_object_processor.py`
2. Add schema: Update `config/schemas.yaml`
3. Register processor: Add to `PROCESSOR_MAP` in `main.py`

### Adding a New Tenant

1. Add tenant config: Update `config/tenants.yaml`
2. Set environment variable: Add `TENANT_NAME_DB_URL` to `.env`
3. Configure database: Ensure database exists and is accessible

### Custom Validation Rules

1. Extend `validator.py` with new validation methods
2. Add validation rules to `config/schemas.yaml`
3. Update `_run_validations()` method in `validator.py`

## Environment Variables

Required for each tenant:
- `{TENANT_NAME}_DB_URL`: Database connection string

Optional:
- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_DIR`: Log directory (default: logs)
- `LOG_FILE_FORMAT`: Log file format (default: {object_type}_%Y%m%d.log)

## Database Support

Supports any database supported by SQLAlchemy:
- PostgreSQL
- MySQL
- SQLite
- Oracle
- SQL Server
- etc.

Connection string format: `{dialect}://{user}:{password}@{host}:{port}/{database}`

Example: `postgresql://user:pass@localhost:5432/mydb`

