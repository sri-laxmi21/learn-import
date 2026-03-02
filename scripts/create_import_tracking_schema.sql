-- common database
-- ============================================================================
-- PostgreSQL Schema for Import Tracking (Common DB - LearnImports)
-- ============================================================================
-- This schema tracks all import jobs across all tenants in a common database.
-- Tenant-specific data processing happens in tenant databases.
--
-- Database: LearnImports (Common DB for all tenants)
-- ============================================================================

-- ============================================================================
-- TABLE: Tenants
-- Purpose: Stores tenant configuration including database connection strings
-- ============================================================================

CREATE TABLE IF NOT EXISTS Tenants (
    TenantPK INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    TenantId VARCHAR(50) NOT NULL UNIQUE,
    Name VARCHAR(250) NOT NULL,
    DBString TEXT NOT NULL, -- Database connection string for tenant
    Enabled SMALLINT DEFAULT 1, -- 0=Disabled, 1=Enabled
    ContactEmail TEXT,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB -- Additional tenant metadata
);

CREATE INDEX idx_tenants_tenantid ON Tenants(TenantId);
CREATE INDEX idx_tenants_enabled ON Tenants(Enabled);

COMMENT ON TABLE Tenants IS 'Stores tenant configuration including database connection strings';
COMMENT ON COLUMN Tenants.TenantId IS 'Unique tenant identifier (e.g., acme_corp, technova)';
COMMENT ON COLUMN Tenants.DBString IS 'Database connection string for tenant-specific database';
COMMENT ON COLUMN Tenants.Enabled IS '0=Disabled, 1=Enabled';

-- ============================================================================
-- TABLE: import_batch
-- Purpose: Groups multiple files into a single import job/batch
-- Note: Normalized table - only overall batch status. File details in import_file table.
-- Processing order comes from schemas.json __processing_order__
-- ============================================================================

CREATE TABLE IF NOT EXISTS import_batch (
    batch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    TenantPK INT NOT NULL REFERENCES Tenants(TenantPK),
    
    -- Batch identification
    batch_name VARCHAR(255),
    description TEXT,
    
    -- Overall status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'uploaded',
    -- Status values: uploaded, validating, validated, processing, completed, failed, cancelled
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- User tracking
    created_by INTEGER, -- References Person(PersonPK) if available
    initiated_by INTEGER, -- References Person(PersonPK)
    
    -- Overall error summary
    error_summary TEXT,
    
    -- Metadata
    metadata JSONB -- Additional metadata (file paths, settings, etc.)
);

CREATE INDEX idx_import_batch_tenantpk ON import_batch(TenantPK);
CREATE INDEX idx_import_batch_status ON import_batch(status);
CREATE INDEX idx_import_batch_created_at ON import_batch(created_at);
CREATE INDEX idx_import_batch_tenantpk_status ON import_batch(TenantPK, status);

COMMENT ON TABLE import_batch IS 'Groups multiple files into a single import job/batch. Normalized - only overall status. File details in import_file table.';
COMMENT ON COLUMN import_batch.TenantPK IS 'References Tenants(TenantPK)';
COMMENT ON COLUMN import_batch.status IS 'uploaded, validating, validated, processing, completed, failed, cancelled';
COMMENT ON COLUMN import_batch.error_summary IS 'Overall error summary for the batch';

-- ============================================================================
-- TABLE: import_file
-- Purpose: Tracks individual files within a batch
-- ============================================================================

CREATE TABLE IF NOT EXISTS import_file (
    file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES import_batch(batch_id) ON DELETE CASCADE,
    
    -- File identification
    file_name VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000), -- Physical file path/location
    file_size BIGINT, -- File size in bytes
    file_format VARCHAR(20), -- csv, xlsx, txt
    file_hash VARCHAR(64), -- SHA-256 hash for duplicate detection
    
    -- Object type
    object_type VARCHAR(50) NOT NULL,
    -- Values: org, job, skill, emp, emp_associations
    
    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'uploaded',
    -- Status values: uploaded, validating, validated, validation_failed, 
    --                loaded, processing, completed, failed, cancelled
    
    -- File-level validation
    validation_status VARCHAR(50), -- valid, invalid, partial
    validation_errors INTEGER DEFAULT 0,
    validation_warnings INTEGER DEFAULT 0,
    
    -- Row counts (from file)
    total_rows INTEGER DEFAULT 0,
    valid_rows INTEGER DEFAULT 0,
    invalid_rows INTEGER DEFAULT 0,
    
    -- Processing results (from tenant DB processing)
    records_inserted INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_ignored INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    records_success INTEGER DEFAULT 0, -- Calculated: records_inserted + records_updated
    
    -- Tenant DB references
    tenant_file_import_id INTEGER, -- References fileImport(importPK) in tenant DB
    tenant_run_id INTEGER, -- Same as tenant_file_import_id (for compatibility)
    
    -- Timestamps
    uploaded_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    validated_at TIMESTAMPTZ,
    loaded_at TIMESTAMPTZ,
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ
    
);

CREATE INDEX idx_import_file_batch_id ON import_file(batch_id);
CREATE INDEX idx_import_file_status ON import_file(status);
CREATE INDEX idx_import_file_object_type ON import_file(object_type);
CREATE INDEX idx_import_file_batch_status ON import_file(batch_id, status);
CREATE INDEX idx_import_file_tenant_import_id ON import_file(tenant_file_import_id);

COMMENT ON TABLE import_file IS 'Tracks individual files within an import batch with detailed file-level statistics';
COMMENT ON COLUMN import_file.status IS 'uploaded, validating, validated, validation_failed, loaded, processing, completed, failed, cancelled';
COMMENT ON COLUMN import_file.object_type IS 'org, job, skill, emp, emp_associations';
COMMENT ON COLUMN import_file.tenant_file_import_id IS 'References fileImport(importPK) in tenant-specific database';
COMMENT ON COLUMN import_file.total_rows IS 'Total number of rows in the file';
COMMENT ON COLUMN import_file.records_inserted IS 'Number of records successfully inserted';
COMMENT ON COLUMN import_file.records_updated IS 'Number of records successfully updated';
COMMENT ON COLUMN import_file.records_ignored IS 'Number of records ignored (duplicates, etc.)';
COMMENT ON COLUMN import_file.records_failed IS 'Number of records that failed processing';
COMMENT ON COLUMN import_file.records_success IS 'Number of successful records (inserted + updated)';

-- ============================================================================
-- TABLE: import_file_validation_log
-- Purpose: Logs schema validation errors at file level (Python/Server validation)
-- ============================================================================

CREATE TABLE IF NOT EXISTS import_file_validation_log (
    log_id BIGSERIAL PRIMARY KEY,
    file_id UUID NOT NULL REFERENCES import_file(file_id) ON DELETE CASCADE,
    batch_id UUID NOT NULL REFERENCES import_batch(batch_id) ON DELETE CASCADE,
    
    -- Error details
    error_type VARCHAR(50), -- schema_error, format_error, required_field_missing, type_mismatch, etc.
    error_severity VARCHAR(20), -- error, warning, info
    error_message TEXT NOT NULL,
    error_details JSONB, -- Additional error details (column, row, value, etc.)
    
    -- Location
    row_number INTEGER, -- Row number in file (if applicable)
    column_name VARCHAR(255), -- Column name (if applicable)
    field_name VARCHAR(255), -- Field name from schema
    
    -- Timestamp
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_import_file_validation_log_file_id ON import_file_validation_log(file_id);
CREATE INDEX idx_import_file_validation_log_batch_id ON import_file_validation_log(batch_id);
CREATE INDEX idx_import_file_validation_log_error_type ON import_file_validation_log(error_type);
CREATE INDEX idx_import_file_validation_log_severity ON import_file_validation_log(error_severity);

COMMENT ON TABLE import_file_validation_log IS 'Logs schema validation errors at file level (Python/Server validation)';
COMMENT ON COLUMN import_file_validation_log.error_type IS 'schema_error, format_error, required_field_missing, type_mismatch, duplicate_value, etc.';

-- ============================================================================
-- TABLE: import_batch_error_summary
-- Purpose: Aggregated error summary from tenant DBs (updated periodically)
-- ============================================================================

CREATE TABLE IF NOT EXISTS import_batch_error_summary (
    summary_id BIGSERIAL PRIMARY KEY,
    batch_id UUID NOT NULL REFERENCES import_batch(batch_id) ON DELETE CASCADE,
    file_id UUID REFERENCES import_file(file_id) ON DELETE CASCADE,
    
    -- Error aggregation
    error_category VARCHAR(100), -- foreign_key_error, validation_error, business_rule_error, etc.
    error_code VARCHAR(50), -- Error code for categorization
    error_message TEXT,
    error_count INTEGER DEFAULT 0,
    
    -- Sample data
    sample_row_numbers INTEGER[], -- Array of row numbers with this error
    sample_error_details JSONB, -- Sample error details
    
    -- Timestamp
    last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_import_batch_error_summary_batch_id ON import_batch_error_summary(batch_id);
CREATE INDEX idx_import_batch_error_summary_file_id ON import_batch_error_summary(file_id);
CREATE INDEX idx_import_batch_error_summary_category ON import_batch_error_summary(error_category);

COMMENT ON TABLE import_batch_error_summary IS 'Aggregated error summary from tenant DBs (updated periodically)';

-- ============================================================================
-- VIEW: vw_import_batch_summary
-- Purpose: Summary view for import batch status
-- ============================================================================

CREATE OR REPLACE VIEW vw_import_batch_summary AS
SELECT 
    b.batch_id,
    b.TenantPK,
    t.TenantId,
    t.Name AS tenant_name,
    b.batch_name,
    b.description,
    b.status,
    b.created_at,
    b.started_at,
    b.completed_at,
    b.created_by,
    b.initiated_by,
    b.error_summary,
    -- Aggregated file statistics
    (SELECT COUNT(*) FROM import_file f WHERE f.batch_id = b.batch_id) AS total_files,
    (SELECT COUNT(*) FROM import_file f WHERE f.batch_id = b.batch_id AND f.status = 'completed') AS files_completed,
    (SELECT COUNT(*) FROM import_file f WHERE f.batch_id = b.batch_id AND f.status = 'failed') AS files_failed,
    (SELECT COUNT(*) FROM import_file f WHERE f.batch_id = b.batch_id AND f.status = 'processing') AS files_processing,
    (SELECT COUNT(*) FROM import_file f WHERE f.batch_id = b.batch_id AND f.status = 'validated') AS files_validated,
    -- Aggregated record statistics
    (SELECT COALESCE(SUM(total_rows), 0) FROM import_file f WHERE f.batch_id = b.batch_id) AS total_records,
    (SELECT COALESCE(SUM(records_inserted + records_updated + records_ignored + records_failed), 0) FROM import_file f WHERE f.batch_id = b.batch_id) AS records_processed,
    (SELECT COALESCE(SUM(records_inserted), 0) FROM import_file f WHERE f.batch_id = b.batch_id) AS records_inserted,
    (SELECT COALESCE(SUM(records_updated), 0) FROM import_file f WHERE f.batch_id = b.batch_id) AS records_updated,
    (SELECT COALESCE(SUM(records_ignored), 0) FROM import_file f WHERE f.batch_id = b.batch_id) AS records_ignored,
    (SELECT COALESCE(SUM(records_failed), 0) FROM import_file f WHERE f.batch_id = b.batch_id) AS records_failed,
    (SELECT COALESCE(SUM(records_inserted + records_updated), 0) FROM import_file f WHERE f.batch_id = b.batch_id) AS records_success,
    --(SELECT COALESCE(SUM(error_count), 0) FROM import_file f WHERE f.batch_id = b.batch_id) AS error_count,
    -- Calculate progress percentage
    CASE 
        WHEN (SELECT COUNT(*) FROM import_file f WHERE f.batch_id = b.batch_id) > 0 THEN 
            ROUND((SELECT COUNT(*) FROM import_file f WHERE f.batch_id = b.batch_id AND f.status = 'completed')::NUMERIC / 
                  (SELECT COUNT(*) FROM import_file f WHERE f.batch_id = b.batch_id)::NUMERIC * 100, 2)
        ELSE 0 
    END AS file_progress_pct,
    CASE 
        WHEN (SELECT COALESCE(SUM(total_rows), 0) FROM import_file f WHERE f.batch_id = b.batch_id) > 0 THEN 
            ROUND((SELECT COALESCE(SUM(records_inserted + records_updated + records_ignored + records_failed), 0) FROM import_file f WHERE f.batch_id = b.batch_id)::NUMERIC / 
                  (SELECT COALESCE(SUM(total_rows), 0) FROM import_file f WHERE f.batch_id = b.batch_id)::NUMERIC * 100, 2)
        ELSE 0 
    END AS record_progress_pct,
    -- Calculate duration
    CASE 
        WHEN b.completed_at IS NOT NULL THEN 
            b.completed_at - b.started_at
        WHEN b.started_at IS NOT NULL THEN 
            CURRENT_TIMESTAMP - b.started_at
        ELSE NULL
    END AS duration
FROM import_batch b
LEFT JOIN Tenants t ON b.TenantPK = t.TenantPK;

COMMENT ON VIEW vw_import_batch_summary IS 'Summary view for import batch status with progress calculations';

-- ============================================================================
-- VIEW: vw_import_file_status
-- Purpose: Detailed file status view
-- ============================================================================

CREATE OR REPLACE VIEW vw_import_file_status AS
SELECT 
    f.file_id,
    f.batch_id,
    b.TenantPK,
    t.TenantId,
    t.Name AS tenant_name,
    f.file_name,
    f.file_path,
    f.file_size,
    f.file_format,
    f.object_type,
    f.status,
    f.validation_status,
    -- Row counts
    f.total_rows,
    f.valid_rows,
    f.invalid_rows,
    -- Processing results
    f.records_inserted,
    f.records_updated,
    f.records_ignored,
    f.records_failed,
    f.records_success,
    f.validation_errors,
    f.validation_warnings,
    --f.error_count,
    -- Timestamps
    f.uploaded_at,
    f.validated_at,
    f.loaded_at,
    f.processing_started_at,
    f.processing_completed_at,
    -- Error tracking
    --f.error_summary,
    --f.last_error,
    -- Tenant DB reference
    f.tenant_file_import_id,
    -- Calculate progress
    CASE 
        WHEN f.total_rows > 0 THEN 
            ROUND(((f.records_inserted + f.records_updated + f.records_ignored + f.records_failed)::NUMERIC / f.total_rows::NUMERIC) * 100, 2)
        ELSE 0 
    END AS processing_progress_pct,
    -- Calculate duration
    CASE 
        WHEN f.processing_completed_at IS NOT NULL THEN 
            f.processing_completed_at - f.processing_started_at
        WHEN f.processing_started_at IS NOT NULL THEN 
            CURRENT_TIMESTAMP - f.processing_started_at
        ELSE NULL
    END AS processing_duration
FROM import_file f
JOIN import_batch b ON f.batch_id = b.batch_id
LEFT JOIN Tenants t ON b.TenantPK = t.TenantPK;

COMMENT ON VIEW vw_import_file_status IS 'Detailed file status view with progress and duration calculations';

-- ============================================================================
-- FUNCTION: update_batch_summary
-- Purpose: Update batch summary statistics from file statistics
-- ============================================================================

CREATE OR REPLACE FUNCTION update_batch_status(batch_uuid UUID)
RETURNS VOID AS $$
DECLARE
    v_total_files INTEGER;
    v_completed_files INTEGER;
    v_failed_files INTEGER;
    v_processing_files INTEGER;
    v_new_status VARCHAR(50);
BEGIN
    -- Get file counts
    SELECT 
        COUNT(*),
        COUNT(*) FILTER (WHERE status = 'completed'),
        COUNT(*) FILTER (WHERE status = 'failed'),
        COUNT(*) FILTER (WHERE status = 'processing')
    INTO v_total_files, v_completed_files, v_failed_files, v_processing_files
    FROM import_file
    WHERE batch_id = batch_uuid;
    
    -- Determine batch status based on file statuses
    IF v_total_files = 0 THEN
        v_new_status := 'uploaded';
    ELSIF v_processing_files > 0 THEN
        v_new_status := 'processing';
    ELSIF v_completed_files = v_total_files THEN
        v_new_status := 'completed';
    ELSIF v_failed_files = v_total_files THEN
        v_new_status := 'failed';
    ELSIF v_failed_files > 0 THEN
        v_new_status := 'failed'; -- Some files failed
    ELSIF v_completed_files > 0 THEN
        v_new_status := 'processing'; -- Some completed, some still processing
    ELSE
        v_new_status := 'validating'; -- Files being validated
    END IF;
    
    -- Update batch status
    UPDATE import_batch
    SET 
        status = v_new_status,
        started_at = COALESCE(started_at, CASE WHEN v_processing_files > 0 THEN CURRENT_TIMESTAMP ELSE NULL END),
        completed_at = CASE WHEN v_new_status IN ('completed', 'failed') THEN CURRENT_TIMESTAMP ELSE completed_at END
    WHERE batch_id = batch_uuid;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_batch_status IS 'Update batch overall status based on file statuses';

-- ============================================================================
-- FUNCTION: get_batch_progress
-- Purpose: Get detailed progress information for a batch
-- ============================================================================

CREATE OR REPLACE FUNCTION get_batch_progress(batch_uuid UUID)
RETURNS TABLE (
    batch_id UUID,
    status VARCHAR,
    file_progress_pct NUMERIC,
    record_progress_pct NUMERIC,
    files_completed INTEGER,
    files_total INTEGER,
    records_processed INTEGER,
    records_total INTEGER,
    current_step VARCHAR,
    estimated_completion TIMESTAMPTZ
) AS $$
DECLARE
    batch_rec RECORD;
    v_files_total INTEGER;
    v_files_completed INTEGER;
    v_records_total INTEGER;
    v_records_processed INTEGER;
    avg_processing_time INTERVAL;
BEGIN
    SELECT * INTO batch_rec FROM import_batch WHERE batch_id = batch_uuid;
    
    IF batch_rec IS NULL THEN
        RETURN;
    END IF;
    
    -- Get aggregated counts from files
    SELECT 
        COUNT(*),
        COUNT(*) FILTER (WHERE status = 'completed'),
        COALESCE(SUM(total_rows), 0),
        COALESCE(SUM(records_inserted + records_updated + records_ignored + records_failed), 0)
    INTO v_files_total, v_files_completed, v_records_total, v_records_processed
    FROM import_file
    WHERE batch_id = batch_uuid;
    
    -- Calculate average processing time per record (from completed files)
    SELECT AVG(processing_completed_at - processing_started_at) INTO avg_processing_time
    FROM import_file
    WHERE batch_id = batch_uuid 
    AND processing_completed_at IS NOT NULL
    AND total_rows > 0;
    
    RETURN QUERY
    SELECT 
        batch_rec.batch_id,
        batch_rec.status,
        CASE 
            WHEN v_files_total > 0 THEN 
                ROUND((v_files_completed::NUMERIC / v_files_total::NUMERIC) * 100, 2)
            ELSE 0 
        END AS file_progress_pct,
        CASE 
            WHEN v_records_total > 0 THEN 
                ROUND((v_records_processed::NUMERIC / v_records_total::NUMERIC) * 100, 2)
            ELSE 0 
        END AS record_progress_pct,
        v_files_completed AS files_completed,
        v_files_total AS files_total,
        v_records_processed AS records_processed,
        v_records_total AS records_total,
        NULL::VARCHAR AS current_step, -- Processing order comes from schemas.json
        CASE 
            WHEN avg_processing_time IS NOT NULL AND v_records_total > v_records_processed THEN
                CURRENT_TIMESTAMP + (avg_processing_time * (v_records_total - v_records_processed) / NULLIF(
                    (SELECT AVG(total_rows) FROM import_file WHERE batch_id = batch_uuid AND total_rows > 0), 0
                ))
            ELSE NULL
        END AS estimated_completion;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_batch_progress IS 'Get detailed progress information for a batch including estimated completion time. Processing order comes from schemas.json.';

-- ============================================================================
-- TRIGGER: Update batch summary on file update
-- Purpose: Automatically update batch summary when file status changes
-- ============================================================================

CREATE OR REPLACE FUNCTION trigger_update_batch_status()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM update_batch_status(NEW.batch_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_batch_status_on_file_update
AFTER INSERT OR UPDATE ON import_file
FOR EACH ROW
EXECUTE FUNCTION trigger_update_batch_status();

-- ============================================================================
-- GRANT PERMISSIONS (Adjust as needed for your security model)
-- ============================================================================

-- Grant usage on schema
-- GRANT USAGE ON SCHEMA public TO your_app_user;

-- Grant permissions on tables
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- Grant permissions on views
-- GRANT SELECT ON vw_import_batch_summary TO your_app_user;
-- GRANT SELECT ON vw_import_file_status TO your_app_user;

-- ============================================================================
-- END OF SCRIPT
-- ============================================================================
