# Import Tracking Architecture - Recommendations

## Executive Summary

Your proposed approach is **solid and well-structured**. The two-stage validation (Python-level schema validation, then DB-level processing) is excellent. However, there are several enhancements that will improve tracking, reporting, and error handling.

## Comparison: Current vs. Recommended Approach

| Aspect | Current Approach | Recommended Enhancement | Benefit |
|--------|-----------------|------------------------|---------|
| **File Tracking** | Implicit in fileImport table | Explicit `import_file` table with metadata | Better file-level tracking, progress, and reporting |
| **Batch Grouping** | Not explicit | `import_batch` table groups multiple files | Better multi-file import management |
| **Status Granularity** | File-level only | Batch + File + Record level | More detailed progress tracking |
| **Error Aggregation** | Manual aggregation | Automated via views and functions | Real-time error summaries |
| **File Storage** | Not tracked | File path, size, hash tracked | Better file management and duplicate detection |
| **Processing Order** | Manual enforcement | Tracked in batch metadata | Automatic dependency handling |
| **Progress Reporting** | Basic counts | Progress percentages + ETA | Better user experience |
| **Error Logging** | Tenant DB only | Common DB + Tenant DB | Centralized error reporting |

## Key Recommendations

### 1. ✅ **Add Batch Concept** (HIGH PRIORITY)

**Why**: When users upload multiple files, you need to group them and track as a single unit.

**Implementation**:
- Create `import_batch` table in common DB
- Link all files to a batch
- Track batch-level status and progress

**Benefits**:
- Users can see all files in one import job
- Batch-level reporting and status
- Better error aggregation

### 2. ✅ **Enhanced File Tracking** (HIGH PRIORITY)

**Why**: Need detailed file metadata for better management and reporting.

**Implementation**:
- Create `import_file` table with:
  - File path, size, format, hash
  - Row counts (total, valid, invalid)
  - Processing results (inserted, updated, ignored, failed)
  - File-level status

**Benefits**:
- Track file uploads separately
- File-level progress reporting
- Duplicate file detection (via hash)
- Better error attribution

### 3. ✅ **Schema Validation Logging** (MEDIUM PRIORITY)

**Why**: Need to track Python-level validation errors separately from DB-level processing errors.

**Implementation**:
- Create `import_file_validation_log` table
- Log schema validation errors (format, required fields, types)
- Link to file_id for easy querying

**Benefits**:
- Separate validation errors from processing errors
- Better error categorization
- Easier debugging

### 4. ✅ **Error Aggregation** (MEDIUM PRIORITY)

**Why**: Need efficient way to aggregate errors from tenant DBs to common DB for reporting.

**Implementation**:
- Create `import_batch_error_summary` table
- Periodically aggregate errors from tenant DBs
- Categorize errors by type

**Benefits**:
- Centralized error reporting
- Error categorization
- Better error analysis

### 5. ✅ **Progress Tracking** (MEDIUM PRIORITY)

**Why**: Users need real-time progress updates.

**Implementation**:
- Add progress percentage calculations
- Add estimated completion time
- Track current processing step

**Benefits**:
- Better user experience
- Real-time progress updates
- Estimated completion times

### 6. ✅ **Processing Order Management** (LOW PRIORITY)

**Why**: Need to enforce dependency order (org → job → skill → emp → emp_associations).

**Implementation**:
- Store processing order in batch metadata
- Track current processing step
- Automatically handle dependencies

**Benefits**:
- Automatic dependency handling
- Better error handling for dependencies
- Clearer progress reporting

## Recommended Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    COMMON DB (LearnImports)                 │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ import_batch (Batch-level tracking)                  │ │
│  │   - batch_id, tenant_id, status, progress            │ │
│  └───────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ import_file (File-level tracking)                     │ │
│  │   - file_id, batch_id, file_name, status, progress   │ │
│  └───────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ import_file_validation_log (Schema validation errors)│ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              TENANT DB (Tenant-Specific)                    │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ fileImport (File import session)                       │ │
│  │   - importPK, FileName, Status, linked to import_file │ │
│  └───────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ processfiletmp_* (Temp tables for data)               │ │
│  │   - Raw data from files, processing status            │ │
│  └───────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ fileImport_Log (Processing errors)                    │ │
│  │   - Processing errors from DB-level validation        │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Steps

### Phase 1: Core Schema (Week 1)
1. ✅ Create `import_batch` table
2. ✅ Create `import_file` table
3. ✅ Link files to batches
4. ✅ Update file upload logic to create batches

### Phase 2: Validation Logging (Week 1-2)
1. ✅ Create `import_file_validation_log` table
2. ✅ Log schema validation errors
3. ✅ Update validation logic to write to log

### Phase 3: Progress Tracking (Week 2)
1. ✅ Add progress calculation functions
2. ✅ Create summary views
3. ✅ Add progress reporting endpoints

### Phase 4: Error Aggregation (Week 2-3)
1. ✅ Create `import_batch_error_summary` table
2. ✅ Implement error aggregation logic
3. ✅ Create error reporting views

### Phase 5: Processing Order (Week 3)
1. ✅ Add processing order tracking
2. ✅ Implement dependency handling
3. ✅ Update batch processing logic

## Status Values

### Batch Status
- `uploaded` - Files uploaded, waiting for validation
- `validating` - Schema validation in progress
- `validated` - All files validated successfully
- `processing` - Data processing in progress
- `completed` - All files processed successfully
- `failed` - One or more files failed
- `cancelled` - Import cancelled by user

### File Status
- `uploaded` - File uploaded
- `validating` - Schema validation in progress
- `validated` - Schema validation passed
- `validation_failed` - Schema validation failed
- `loaded` - Data loaded to temp tables
- `processing` - DB-level processing in progress
- `completed` - Processing completed successfully
- `failed` - Processing failed
- `cancelled` - File processing cancelled

## Error Handling Strategy

### Error Levels

1. **Schema Validation Errors** (Python-level)
   - Stored in: `import_file_validation_log`
   - Examples: Missing required fields, type mismatches, format errors
   - Action: Prevent loading to temp tables

2. **Processing Errors** (DB-level)
   - Stored in: `fileImport_Log` (tenant DB)
   - Examples: Foreign key violations, business rule violations
   - Action: Mark record as failed, continue processing

3. **System Errors**
   - Stored in: Both common DB and tenant DB
   - Examples: Database connection errors, file read errors
   - Action: Mark batch/file as failed

### Error Aggregation

- Periodically query tenant DBs for errors
- Aggregate by error type/category
- Store summary in `import_batch_error_summary`
- Generate error reports on demand

## Reporting Capabilities

### Batch-Level Reports
- Overall batch status
- Files processed/failed
- Records inserted/updated/ignored/failed
- Error summary
- Processing duration

### File-Level Reports
- Individual file status
- Validation errors
- Processing errors
- Row-level details

### Error Reports
- Error categorization
- Error frequency
- Sample error details
- Affected records

## Performance Considerations

1. **Indexes**: All foreign keys and status fields indexed
2. **Batch Updates**: Use triggers to auto-update batch summaries
3. **Error Aggregation**: Run periodically, not real-time
4. **Views**: Use materialized views for complex reports (if needed)
5. **Partitioning**: Consider partitioning by date for large volumes

## Security Considerations

1. **Tenant Isolation**: Ensure tenant_id is always set and validated
2. **File Access**: Secure file storage paths
3. **Error Messages**: Sanitize error messages to prevent information leakage
4. **Audit Trail**: Track who initiated imports (created_by, initiated_by)

## Migration Path

### Step 1: Add New Tables
- Create new tables in common DB
- Keep existing `fileImport` table in tenant DBs
- Link via `tenant_file_import_id`

### Step 2: Update Application Logic
- Update file upload to create batches
- Update validation to log errors
- Update processing to update file status

### Step 3: Gradual Migration
- Run both systems in parallel initially
- Migrate existing imports gradually
- Deprecate old tracking when ready

## Conclusion

Your approach is **fundamentally sound**. The recommended enhancements add:
- ✅ Better tracking and reporting
- ✅ Improved error handling
- ✅ Enhanced user experience
- ✅ Better scalability

The schema provided implements all these recommendations and is ready for use.

