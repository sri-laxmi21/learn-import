-- ============================================================================
-- Tenant-Specific fileImport and fileImport_Log Tables
-- ============================================================================
-- This script creates the fileImport and fileImport_Log tables with enhancements
-- to link with the common DB import_file table for better tracking and reporting.
--
-- Run this in each tenant database
-- ============================================================================

-- Drop existing tables if they exist (CASCADE to handle dependencies)
DROP TABLE IF EXISTS fileImport_Log CASCADE;
DROP TABLE IF EXISTS fileImport CASCADE;

-- Drop existing views if they exist
DROP VIEW IF EXISTS vw_fileimport_status CASCADE;

-- Drop existing functions if they exist
DROP FUNCTION IF EXISTS update_common_file_status(INTEGER, VARCHAR, INTEGER, INTEGER, INTEGER, INTEGER) CASCADE;

-- ============================================================================
-- TABLE: fileImport
-- Purpose: Tracks file import sessions in tenant database
-- ============================================================================

CREATE TABLE fileImport (
    importPK INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    FileName VARCHAR(200) NOT NULL,
    
    -- Timestamps
    StartDtTime TIMESTAMP DEFAULT (timezone('utc', now())),
    EndDtTime TIMESTAMP DEFAULT (timezone('utc', now())),
    
    -- Status tracking
    Status SMALLINT NOT NULL DEFAULT 0,
    -- Status values: 0=Initiated, 1=InProgress, 2=Failed, 3=Completed, 4=Successful
    
    -- User tracking
    InitiatedBy INT REFERENCES Person(PersonPK),
    
    -- Common DB linking (for integration with LearnImports common DB)
    common_file_id UUID, -- References import_file(file_id) in common DB (LearnImports)
    common_batch_id UUID, -- References import_batch(batch_id) in common DB (LearnImports)
    
    -- Processing results summary
    records_inserted INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_ignored INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    
    -- Metadata
    metadata JSONB -- Additional metadata
);

-- Indexes
CREATE INDEX idx_fileimport_status ON fileImport(Status);
CREATE INDEX idx_fileimport_startdttime ON fileImport(StartDtTime);
CREATE INDEX idx_fileimport_initiatedby ON fileImport(InitiatedBy);
CREATE INDEX idx_fileimport_common_file_id ON fileImport(common_file_id);
CREATE INDEX idx_fileimport_common_batch_id ON fileImport(common_batch_id);

-- Comments
COMMENT ON TABLE fileImport IS 'Tracks file import sessions in tenant database';
COMMENT ON COLUMN fileImport.Status IS '0=Initiated, 1=InProgress, 2=Failed, 3=Completed, 4=Successful';
COMMENT ON COLUMN fileImport.common_file_id IS 'References import_file(file_id) in common DB (LearnImports)';
COMMENT ON COLUMN fileImport.common_batch_id IS 'References import_batch(batch_id) in common DB (LearnImports)';
COMMENT ON COLUMN fileImport.records_inserted IS 'Number of records inserted during processing';
COMMENT ON COLUMN fileImport.records_updated IS 'Number of records updated during processing';
COMMENT ON COLUMN fileImport.records_ignored IS 'Number of records ignored during processing';
COMMENT ON COLUMN fileImport.records_failed IS 'Number of records failed during processing';

-- ============================================================================
-- TABLE: fileImport_Log
-- Purpose: Logs errors during import processing
-- ============================================================================

CREATE TABLE fileImport_Log (
    logPK INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    runId INT NOT NULL REFERENCES fileImport(importPK) ON DELETE CASCADE,
    
    -- Error details
    errMsg VARCHAR(2000),
    errLog TEXT,
    
    -- Timestamp
    lstUpd TIMESTAMP DEFAULT (timezone('utc', now())),
    
    -- Additional error metadata
    error_type VARCHAR(50), -- foreign_key_error, validation_error, business_rule_error, etc.
    row_number INTEGER, -- Row number in file (if applicable)
    error_details JSONB -- Additional error details
);

-- Indexes
CREATE INDEX idx_fileimport_log_runid ON fileImport_Log(runId);
CREATE INDEX idx_fileimport_log_lstupd ON fileImport_Log(lstUpd);
CREATE INDEX idx_fileimport_log_error_type ON fileImport_Log(error_type);

-- Comments
COMMENT ON TABLE fileImport_Log IS 'Logs errors during import processing';
COMMENT ON COLUMN fileImport_Log.runId IS 'References fileImport(importPK)';
COMMENT ON COLUMN fileImport_Log.error_type IS 'Error category: foreign_key_error, validation_error, business_rule_error, etc.';

-- ============================================================================
-- FUNCTION: update_common_file_status
-- Purpose: Update fileImport status and prepare data for syncing to common DB
-- ============================================================================

CREATE OR REPLACE FUNCTION update_common_file_status(
    p_import_pk INTEGER,
    p_status VARCHAR,
    p_records_inserted INTEGER DEFAULT NULL,
    p_records_updated INTEGER DEFAULT NULL,
    p_records_ignored INTEGER DEFAULT NULL,
    p_records_failed INTEGER DEFAULT NULL
)
RETURNS VOID AS $$
DECLARE
    v_common_file_id UUID;
BEGIN
    -- Get common_file_id from fileImport
    SELECT common_file_id INTO v_common_file_id
    FROM fileImport
    WHERE importPK = p_import_pk;
    
    -- Update local fileImport table
    UPDATE fileImport
    SET 
        Status = CASE 
            WHEN p_status = 'completed' THEN 4  -- Successful
            WHEN p_status = 'failed' THEN 2      -- Failed
            WHEN p_status = 'processing' THEN 1  -- InProgress
            WHEN p_status = 'initiated' THEN 0   -- Initiated
            ELSE Status
        END,
        EndDtTime = CASE 
            WHEN p_status IN ('completed', 'failed') THEN timezone('utc', now())
            ELSE EndDtTime
        END,
        records_inserted = COALESCE(p_records_inserted, records_inserted),
        records_updated = COALESCE(p_records_updated, records_updated),
        records_ignored = COALESCE(p_records_ignored, records_ignored),
        records_failed = COALESCE(p_records_failed, records_failed)
    WHERE importPK = p_import_pk;
    
    -- Note: Actual update to common DB should be done by application
    -- This function prepares the data for the application to sync
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_common_file_status IS 'Update fileImport status and prepare data for syncing to common DB';

-- ============================================================================
-- VIEW: vw_fileimport_status
-- Purpose: View for easy querying of file import status with summary statistics
-- ============================================================================

CREATE OR REPLACE VIEW vw_fileimport_status AS
SELECT 
    fi.importPK,
    fi.FileName,
    fi.common_file_id,
    fi.common_batch_id,
    fi.Status,
    CASE fi.Status
        WHEN 0 THEN 'Initiated'
        WHEN 1 THEN 'InProgress'
        WHEN 2 THEN 'Failed'
        WHEN 3 THEN 'Completed'
        WHEN 4 THEN 'Successful'
        ELSE 'Unknown'
    END AS status_text,
    fi.StartDtTime,
    fi.EndDtTime,
    fi.InitiatedBy,
    fi.records_inserted,
    fi.records_updated,
    fi.records_ignored,
    fi.records_failed,
    (fi.records_inserted + fi.records_updated + fi.records_ignored + fi.records_failed) AS total_processed,
    -- Get error count from fileImport_Log
    (SELECT COUNT(*) FROM fileImport_Log WHERE runId = fi.importPK) AS error_count,
    -- Calculate duration
    CASE 
        WHEN fi.EndDtTime IS NOT NULL THEN 
            fi.EndDtTime - fi.StartDtTime
        ELSE 
            CURRENT_TIMESTAMP - fi.StartDtTime
    END AS duration
FROM fileImport fi;

COMMENT ON VIEW vw_fileimport_status IS 'View for easy querying of file import status with summary statistics';

-- ============================================================================
-- GRANT PERMISSIONS (Adjust as needed for your security model)
-- ============================================================================

-- Grant usage on sequences
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- Grant permissions on tables
-- GRANT SELECT, INSERT, UPDATE, DELETE ON fileImport TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON fileImport_Log TO your_app_user;

-- Grant permissions on views
-- GRANT SELECT ON vw_fileimport_status TO your_app_user;

-- ============================================================================
-- END OF SCRIPT
-- ============================================================================
