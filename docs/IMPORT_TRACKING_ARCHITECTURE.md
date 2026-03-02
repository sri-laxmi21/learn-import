# Import Tracking Architecture - Review & Recommendations

## Current Approach Analysis

### ✅ Strengths

1. **Separation of Concerns**: Common DB for tracking, tenant DBs for data
2. **Two-Stage Validation**: Schema validation before loading, then DB-level processing
3. **Multi-Level Error Tracking**: Errors tracked at file, record, and processing levels
4. **Tenant Isolation**: Data stored in tenant-specific databases
5. **Batch Support**: Supports multiple files per import

### ⚠️ Areas for Improvement

1. **File Storage**: Need to track physical file location/path
2. **Batch/Job Grouping**: Need explicit batch concept to group multiple files
3. **Status Granularity**: Need file-level status in addition to job-level
4. **Processing Order**: Need to track and enforce dependency order (org → job → skill → emp → emp_associations)
5. **Error Aggregation**: Efficient way to aggregate errors from tenant DBs to common DB
6. **Real-time Progress**: Better progress tracking for reporting
7. **File Metadata**: Track file size, format, row counts, etc.
8. **Retry Logic**: Support for retrying failed imports
9. **Error Log Files**: Consider storing errors in DB for better querying/reporting

## Recommended Enhanced Architecture

### Architecture Flow

```
1. User Uploads Files (Multiple files possible)
   ↓
2. Create Import Batch in Common DB (LearnImports)
   ├─ Batch ID generated
   ├─ Tenant association
   └─ Status: 'uploaded'
   ↓
3. Store File Metadata in Common DB
   ├─ File path/location
   ├─ File size, format, row count
   └─ Status: 'pending_validation'
   ↓
4. Schema Validation (Python/Server Level)
   ├─ Validate file format (CSV/XLSX/TXT)
   ├─ Validate schema (columns, types, required fields)
   ├─ Update file status: 'validated' or 'validation_failed'
   └─ Log validation errors to Common DB
   ↓
5. Load to Tenant Temp Tables
   ├─ Load validated data to processfiletmp_* tables
   ├─ Link to fileImport record (runId)
   └─ Update file status: 'loaded'
   ↓
6. Process in Dependency Order (Tenant DB)
   ├─ Process org files first
   ├─ Process job files
   ├─ Process skill files
   ├─ Process emp files
   └─ Process emp_associations files last
   ↓
7. DB-Level Processing
   ├─ Resolve foreign keys
   ├─ Validate business rules
   ├─ Insert/Update actual tables
   ├─ Update processfiletmp_* status
   └─ Log to fileImport_Log
   ↓
8. Aggregate Results to Common DB
   ├─ Update file status: 'completed' or 'failed'
   ├─ Update batch status
   └─ Aggregate error summary
   ↓
9. Generate Error Reports
   ├─ Query errors from tenant DB
   ├─ Generate error log file (optional)
   └─ Update batch with final status
```

## Database Schema Design

### Common DB (LearnImports) - Job Tracking

**Purpose**: Track all imports across all tenants

**Tables**:
1. `import_batch` - Groups multiple files into a single import job
2. `import_file` - Tracks individual files within a batch
3. `import_file_validation_log` - Schema validation errors
4. `import_batch_summary` - Aggregated summary view

### Tenant DB - Data Processing

**Purpose**: Process actual data for each tenant

**Tables**:
1. `fileImport` - File import session (already exists)
2. `fileImport_Log` - Processing errors (already exists)
3. `processfiletmp_*` - Object-specific temp tables (already created)

## Key Improvements

### 1. Batch Concept
- Group multiple files into a single import batch
- Track batch-level status and progress
- Support batch-level reporting

### 2. File-Level Tracking
- Track each file individually
- File-level status and progress
- File metadata (size, format, row counts)

### 3. Enhanced Status Tracking
- More granular statuses
- Progress percentages
- Estimated completion times

### 4. Error Aggregation
- Efficient error summary aggregation
- Error categorization
- Error reporting views

### 5. Processing Order Management
- Track processing order dependencies
- Enforce order constraints
- Handle dependencies automatically

### 6. Real-time Progress
- Progress tracking at batch, file, and record levels
- Support for progress polling
- Progress reporting endpoints

