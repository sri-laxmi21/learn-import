# Import Tracking - Quick Reference Guide

## Database Schema Overview

### Common DB (LearnImports) - All Tenants

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `import_batch` | Groups multiple files into a batch | `batch_id`, `tenant_id`, `status`, progress fields |
| `import_file` | Tracks individual files | `file_id`, `batch_id`, `object_type`, `status`, row counts |
| `import_file_validation_log` | Schema validation errors | `log_id`, `file_id`, `error_type`, `error_message` |
| `import_batch_error_summary` | Aggregated errors | `summary_id`, `batch_id`, `error_category`, `error_count` |

### Tenant DB - Per Tenant

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `fileImport` | File import session | `importPK`, `FileName`, `Status`, `common_file_id` |
| `fileImport_Log` | Processing errors | `logPK`, `runId`, `errMsg`, `errLog` |
| `processfiletmp_*` | Temp tables for data | `processfilepk`, `runId`, `processstatus`, `objpk` |

## Status Values

### Batch Status (`import_batch.status`)
- `uploaded` - Files uploaded, waiting for validation
- `validating` - Schema validation in progress
- `validated` - All files validated successfully
- `processing` - Data processing in progress
- `completed` - All files processed successfully
- `failed` - One or more files failed
- `cancelled` - Import cancelled by user

### File Status (`import_file.status`)
- `uploaded` - File uploaded
- `validating` - Schema validation in progress
- `validated` - Schema validation passed
- `validation_failed` - Schema validation failed
- `loaded` - Data loaded to temp tables
- `processing` - DB-level processing in progress
- `completed` - Processing completed successfully
- `failed` - Processing failed
- `cancelled` - File processing cancelled

### FileImport Status (`fileImport.Status`)
- `0` - Initiated
- `1` - InProgress
- `2` - Failed
- `3` - Completed
- `4` - Successful

### ProcessFileTmp Status (`processfiletmp_*.processstatus`)
- `0` - Pending
- `1` - Success
- `2` - Failed

## Common Queries

### Get Batch Status
```sql
SELECT * FROM vw_import_batch_summary 
WHERE batch_id = 'your-batch-id';
```

### Get File Status
```sql
SELECT * FROM vw_import_file_status 
WHERE batch_id = 'your-batch-id';
```

### Get Batch Progress
```sql
SELECT * FROM get_batch_progress('your-batch-id');
```

### Get Validation Errors
```sql
SELECT * FROM import_file_validation_log 
WHERE file_id = 'your-file-id'
ORDER BY created_at DESC;
```

### Get Processing Errors (Tenant DB)
```sql
SELECT * FROM fileImport_Log 
WHERE runId = (SELECT importPK FROM fileImport WHERE common_file_id = 'your-file-id')
ORDER BY lstUpd DESC;
```

### Get Failed Records (Tenant DB)
```sql
SELECT * FROM processfiletmp_emp 
WHERE runId = (SELECT importPK FROM fileImport WHERE common_file_id = 'your-file-id')
AND processstatus = 2;
```

## Data Flow

```
1. Upload Files → Create import_batch → Create import_file records
2. Validate Schema → Log to import_file_validation_log
3. Load to Tenant DB → Create fileImport → Link via common_file_id
4. Load to Temp Tables → processfiletmp_* tables
5. Process Data → Update processfiletmp_* status
6. Log Errors → fileImport_Log
7. Update Status → Update import_file → Update import_batch
```

## Key Relationships

```
import_batch (1) ──→ (many) import_file
import_file (1) ──→ (many) import_file_validation_log
import_file (1) ──→ (1) fileImport (via common_file_id)
fileImport (1) ──→ (many) processfiletmp_* (via runId)
fileImport (1) ──→ (many) fileImport_Log (via runId)
```

## API Endpoints (Recommended)

### Batch Management
- `POST /api/import/batch` - Create new import batch
- `GET /api/import/batch/{batch_id}` - Get batch status
- `GET /api/import/batch/{batch_id}/progress` - Get batch progress
- `GET /api/import/batch/{batch_id}/files` - Get files in batch
- `GET /api/import/batch/{batch_id}/errors` - Get batch errors

### File Management
- `POST /api/import/file` - Upload file to batch
- `GET /api/import/file/{file_id}` - Get file status
- `GET /api/import/file/{file_id}/errors` - Get file errors
- `GET /api/import/file/{file_id}/validation-errors` - Get validation errors

### Reporting
- `GET /api/import/batch/{batch_id}/report` - Generate batch report
- `GET /api/import/batch/{batch_id}/error-report` - Generate error report
- `GET /api/import/tenant/{tenant_id}/batches` - Get all batches for tenant

## Error Handling

### Validation Errors (Python-level)
- Stored in: `import_file_validation_log`
- Examples: Missing columns, type mismatches, format errors
- Action: Prevent loading to temp tables

### Processing Errors (DB-level)
- Stored in: `fileImport_Log` (tenant DB)
- Examples: Foreign key violations, business rule violations
- Action: Mark record as failed, continue processing

### System Errors
- Stored in: Both common DB and tenant DB
- Examples: Database errors, file read errors
- Action: Mark batch/file as failed

## Best Practices

1. **Always create batch first** before uploading files
2. **Link files to batch** via `batch_id`
3. **Link tenant fileImport to common import_file** via `common_file_id`
4. **Update status atomically** when processing completes
5. **Aggregate errors periodically** to avoid performance issues
6. **Use views** for reporting instead of direct table queries
7. **Clean up old data** regularly to manage table sizes

## Migration Checklist

- [ ] Create common DB schema (`create_import_tracking_schema.sql`)
- [ ] Update tenant DB schema (`create_tenant_fileimport_enhanced.sql`)
- [ ] Update file upload logic to create batches
- [ ] Update validation logic to log errors
- [ ] Update processing logic to update status
- [ ] Implement error aggregation logic
- [ ] Create API endpoints for tracking
- [ ] Create reporting views/queries
- [ ] Test end-to-end flow
- [ ] Document for team

