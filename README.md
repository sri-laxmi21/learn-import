# Ziora Data Imports

A multi-tenant Python project for importing data into Ziora system for multiple objects (Employee, Organization, Job, Skill, etc.).

## Architecture

**React → .NET API → Python Service → PostgreSQL**

This project implements a Python microservice that can be invoked via HTTP from a .NET API, supporting:
- Multi-tenant architecture with separate databases per tenant
- Per-tenant log directories for isolation
- Job tracking with shared database
- Background processing with FastAPI
- HTTP-based API for integration with .NET services

## Features

- **Multi-tenant support**: Separate databases per tenant with dynamic routing
- **Per-tenant logging**: Separate log directories for each tenant (`logs/{tenant_name}/`)
- **Job tracking**: Shared database for tracking import jobs across tenants
- **FastAPI service**: HTTP endpoints for .NET API integration
- **Background processing**: Asynchronous file processing with FastAPI BackgroundTasks
- **Configurable file format/schema definitions**: YAML-based schema configuration
- **Multiple object types**: Support for Emp, Org, Job, Skill, and extensible for more
- **Data validation**: Comprehensive validation with error reporting
- **CLI support**: Command-line interface for direct file imports

## Project Structure

```
ziora_imports/
├── ziora_imports/
│   ├── __init__.py
│   ├── api/                    # FastAPI service
│   │   ├── __init__.py
│   │   └── service.py         # HTTP endpoints for .NET integration
│   ├── config/
│   │   ├── __init__.py
│   │   ├── tenant_config.py   # Tenant configuration management
│   │   └── schema_config.py   # Schema/file format configuration
│   ├── core/
│   │   ├── __init__.py
│   │   ├── logger.py          # Per-tenant logging module
│   │   ├── database.py        # Multi-tenant database management
│   │   ├── validator.py       # Data validation
│   │   └── job_tracker.py     # Job tracking with shared DB
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── base_processor.py  # Base processor class
│   │   ├── emp_processor.py   # Employee imports
│   │   ├── org_processor.py   # Organization imports
│   │   ├── job_processor.py   # Job imports
│   │   └── skill_processor.py # Skill imports
│   └── utils/
│       ├── __init__.py
│       └── file_handler.py    # File utilities
├── config/
│   ├── tenants.yaml           # Tenant definitions
│   └── schemas.yaml           # Schema definitions
├── logs/                       # Log directory (per-tenant subdirectories)
│   ├── {tenant1}/
│   └── {tenant2}/
├── env.example                 # Environment variables template
├── requirements.txt           # Python dependencies
├── main.py                    # CLI entry point
└── api_server.py              # FastAPI server entry point
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
# Copy env.example to .env
cp env.example .env

# Edit .env and configure:
# - Tenant database URLs (TENANT_NAME_DB_URL)
# - Shared database URL for job tracking (SHARED_DB_URL)
# - Logging configuration (LOG_LEVEL, LOG_DIR)
```

3. Configure tenants in `config/tenants.yaml`

4. Configure schemas in `config/schemas.yaml`

5. (Optional) Initialize shared database for job tracking:
```sql
-- The tables will be created automatically on first run
-- Or create manually using the schema in ziora_imports/core/job_tracker.py
```

## Usage

### CLI Usage (Direct Import)

```bash
python main.py --tenant <tenant_name> --object <object_type> --file <file_path>
```

Example:
```bash
python main.py --tenant acme_corp --object emp --file data/employees.csv
```

### FastAPI Service (For .NET Integration)

Start the FastAPI server:
```bash
python api_server.py
# Or: uvicorn api_server:app --host 0.0.0.0 --port 8080
```

API Endpoints:
- `POST /import` - Create import job (called by .NET API)
- `GET /status/{job_id}` - Get job status (polled by React via .NET API)
- `GET /health` - Health check

Example API call:
```bash
curl -X POST "http://localhost:8080/import" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "acme_corp",
    "customer_id": "cust_001",
    "object_type": "emp",
    "file_path": "/path/to/employees.csv"
  }'
```

## Logging

Logs are organized by tenant with object-type prefixes:
- Base directory: `logs/` (configurable via LOG_DIR)
- Per-tenant: `logs/{tenant_name}/{object_type}_YYYYMMDD.log`
  - Example: `logs/acme_corp/emp_20240101.log`
  - Example: `logs/acme_corp/job_20240101.log`
  - Example: `logs/technova/skill_20240101.log`
- Console output: INFO level and above
- File output: DEBUG level and above

## Configuration

- **Tenant configuration**: `config/tenants.yaml` - Define tenants and their database mappings
- **Schema configuration**: `config/schemas.yaml` - Define file formats and validation rules
- **Environment variables**: `.env` - Database URLs, logging, and API settings

