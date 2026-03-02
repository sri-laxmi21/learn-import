# Architecture Updates Based on Requirements Document

## Summary of Changes

Based on the requirements document `DataImports_Python_Considerations.docx`, the following architectural updates have been implemented:

## 1. Per-Tenant Logging ✅

**Requirement**: Logs should be separated by tenant for better isolation and organization.

**Implementation**:
- Updated `ziora_imports/core/logger.py` to support per-tenant log directories
- Logs are now organized as: `logs/{tenant_name}/{object_type}_YYYYMMDD.log`
- Each tenant has its own subdirectory for complete isolation
- Each object type (emp, org, job, skill) gets its own log file within the tenant directory
- Updated all processors and main.py to use tenant-specific logging with object_type prefix

**Usage**:
```python
logger = setup_logger(tenant_name="acme_corp", object_type="emp")
# Creates logs in: logs/acme_corp/emp_20240101.log
```

## 2. FastAPI Service for HTTP Integration ✅

**Requirement**: Python service should be invokable via HTTP from .NET API (React → .NET API → Python Service).

**Implementation**:
- Created `ziora_imports/api/service.py` with FastAPI endpoints
- Created `api_server.py` as entry point for running the service
- Added endpoints:
  - `POST /import` - Create and queue import job
  - `GET /status/{job_id}` - Get job status (for polling)
  - `GET /health` - Health check

**Architecture Flow**:
```
React → .NET API → Python FastAPI Service → PostgreSQL
```

## 3. Job Tracking with Shared Database ✅

**Requirement**: Shared database for tracking import jobs across all tenants.

**Implementation**:
- Created `ziora_imports/core/job_tracker.py` with:
  - `ImportJob` table for job tracking
  - `ImportLog` table for row-level logging
  - `JobTracker` class for managing jobs
- Supports optional shared database (via `SHARED_DB_URL` env var)
- Gracefully degrades if shared DB not configured

**Database Schema**:
```sql
-- Shared DB (for job tracking)
CREATE TABLE import_jobs (
    job_id UUID PRIMARY KEY,
    tenant_id TEXT,
    customer_id TEXT,
    object_type TEXT,
    source_file TEXT,
    status TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_summary TEXT,
    total_rows INT,
    processed_rows INT,
    failed_rows INT
);

CREATE TABLE import_logs (
    log_id SERIAL PRIMARY KEY,
    job_id UUID REFERENCES import_jobs(job_id),
    row_number INT,
    status TEXT,
    error_message TEXT
);
```

## 4. Background Processing ✅

**Requirement**: Support asynchronous/background processing of import jobs.

**Implementation**:
- Uses FastAPI `BackgroundTasks` for async processing
- Jobs are queued immediately and processed in background
- Status can be polled via `/status/{job_id}` endpoint

## 5. Multi-Tenant Database Routing ✅

**Requirement**: Dynamic database routing based on tenant/customer ID.

**Implementation**:
- `DatabaseManager` already supports multi-tenant routing
- Each tenant has separate database connection
- Database URLs configured via environment variables: `{TENANT_NAME}_DB_URL`

## 6. Updated Dependencies ✅

**New Dependencies**:
- `fastapi>=0.104.0` - HTTP API framework
- `uvicorn>=0.24.0` - ASGI server for FastAPI
- `python-multipart>=0.0.6` - For file uploads (if needed)

## File Structure Changes

### New Files:
- `ziora_imports/api/service.py` - FastAPI service endpoints
- `ziora_imports/api/__init__.py` - API package init
- `ziora_imports/core/job_tracker.py` - Job tracking module
- `api_server.py` - FastAPI server entry point
- `env.example` - Environment variables template

### Modified Files:
- `ziora_imports/core/logger.py` - Added per-tenant logging support
- `ziora_imports/core/__init__.py` - Added JobTracker exports
- `ziora_imports/processors/base_processor.py` - Updated to use tenant-specific logging
- `main.py` - Updated to use tenant-specific logging
- `requirements.txt` - Added FastAPI dependencies
- `README.md` - Updated with new architecture documentation

## Configuration Updates

### Environment Variables

**New Variables**:
- `SHARED_DB_URL` - Shared database for job tracking (optional)
- `API_HOST` - FastAPI server host (default: 0.0.0.0)
- `API_PORT` - FastAPI server port (default: 8080)

**Existing Variables** (still used):
- `{TENANT_NAME}_DB_URL` - Per-tenant database URLs
- `LOG_LEVEL` - Logging level
- `LOG_DIR` - Base log directory (tenant subdirectories created automatically)

## Usage Examples

### 1. CLI Usage (Direct Import)
```bash
python main.py --tenant acme_corp --object emp --file data/employees.csv
```
- Logs created in: `logs/acme_corp/emp_20240101.log`

### 2. FastAPI Service (HTTP Integration)
```bash
# Start server
python api_server.py

# Create import job (from .NET API)
curl -X POST "http://localhost:8080/import" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "acme_corp",
    "customer_id": "cust_001",
    "object_type": "emp",
    "file_path": "/path/to/employees.csv"
  }'

# Check status (polled by React via .NET API)
curl "http://localhost:8080/status/{job_id}"
```

## Log Directory Structure

```
logs/
├── acme_corp/
│   ├── emp_20240101.log
│   ├── org_20240101.log
│   ├── job_20240101.log
│   └── skill_20240101.log
├── technova/
│   ├── emp_20240101.log
│   └── job_20240101.log
└── {other_tenants}/
    └── {object_type}_YYYYMMDD.log
```

**Note**: Each object type (emp, org, job, skill, etc.) gets its own log file within the tenant directory, making it easier to track imports by object type.

## Benefits

1. **Isolation**: Per-tenant logs provide complete isolation
2. **Scalability**: FastAPI supports concurrent requests
3. **Observability**: Job tracking provides visibility into all imports
4. **Integration**: HTTP API enables clean integration with .NET
5. **Flexibility**: Supports both CLI and HTTP invocation

## Next Steps

1. Configure `SHARED_DB_URL` in `.env` for job tracking
2. Deploy FastAPI service on EC2 or container platform
3. Configure .NET API to call Python service endpoints
4. Set up monitoring and alerts for import jobs
5. Configure log rotation for per-tenant logs

