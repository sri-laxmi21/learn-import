-- ============================================================================
-- PostgreSQL Object-Specific Temporary Tables for File Import Processing
-- ============================================================================
-- These tables are used to load file data after initial file validation.
-- Data is processed from these temp tables at DB level and updates records
-- with success or failed status.
--
-- Prerequisites:
--   - fileImport table must exist
--   - fileImport_Log table must exist
--   - Person table must exist (for fileImport.InitiatedBy FK)
--
-- ============================================================================

-- ============================================================================
-- SEQUENCES
-- ============================================================================

CREATE SEQUENCE IF NOT EXISTS DI_org_sequence START 1 INCREMENT 1;
CREATE SEQUENCE IF NOT EXISTS DI_job_sequence START 1 INCREMENT 1;
CREATE SEQUENCE IF NOT EXISTS DI_skill_sequence START 1 INCREMENT 1;
CREATE SEQUENCE IF NOT EXISTS DI_emp_sequence START 1 INCREMENT 1;
CREATE SEQUENCE IF NOT EXISTS DI_empAssociations_sequence START 1 INCREMENT 1;

-- ============================================================================
-- TEMPORARY TABLE: DI_org
-- Purpose: Temporary table for Organization file imports
-- ============================================================================

CREATE TABLE IF NOT EXISTS DI_org (
    processfilepk INTEGER NOT NULL DEFAULT nextval('DI_org_sequence'::regclass),
    runId INTEGER REFERENCES fileImport(importPK),
    
    -- Organization fields
    org_id VARCHAR(50),
    org_name VARCHAR(200),
    org_code VARCHAR(20),
    OrgType VARCHAR(255), -- Code table reference (CatCd=1001)
    parent_org_id VARCHAR(50),
    Description VARCHAR(4000), -- Organization description
    active SMALLINT, -- 0 or 1 (boolean converted to smallint)
    
    -- Common fields
    address VARCHAR(255),
    city VARCHAR(100),
    country VARCHAR(100),
    Lang_Cd VARCHAR(50), -- References Lang table
    Timezone_Cd VARCHAR(50), -- References Timezone table
    CountryCode VARCHAR(255), -- Code table reference (CatCd=1006)
    
    -- Processing status fields
    deleted SMALLINT DEFAULT 0, -- 0=active, 1=deleted
    objpk INTEGER, -- Resolved Organization PK after processing
    objprntfk INTEGER, -- Resolved parent Organization PK
    processstatus SMALLINT, -- 0=Pending, 1=Success, 2=Failed
    errormsg VARCHAR(2000), -- Error message if processing failed
    
    CONSTRAINT DI_org_pkey PRIMARY KEY (processfilepk)
);

CREATE INDEX IF NOT EXISTS idx_DI_org_runid ON DI_org(runId);
CREATE INDEX IF NOT EXISTS idx_DI_org_processstatus ON DI_org(processstatus);
CREATE INDEX IF NOT EXISTS idx_DI_org_org_id ON DI_org(org_id);
CREATE INDEX IF NOT EXISTS idx_DI_org_org_code ON DI_org(org_code);

COMMENT ON TABLE DI_org IS 'Temporary table for Organization file imports';
COMMENT ON COLUMN DI_org.processstatus IS '0=Pending, 1=Success, 2=Failed';
COMMENT ON COLUMN DI_org.deleted IS '0=active, 1=deleted';

-- ============================================================================
-- TEMPORARY TABLE: DI_job
-- Purpose: Temporary table for Job/Position file imports
-- ============================================================================

CREATE TABLE IF NOT EXISTS DI_job (
    processfilepk INTEGER NOT NULL DEFAULT nextval('DI_job_sequence'::regclass),
    runId INTEGER REFERENCES fileImport(importPK),
    
    -- Job fields
    job_id VARCHAR(50),
    job_title VARCHAR(200),
    job_code VARCHAR(20),
    department VARCHAR(100),
    level INTEGER,
    min_salary NUMERIC(10, 2),
    max_salary NUMERIC(10, 2),
    active SMALLINT, -- 0 or 1 (boolean converted to smallint)
    
    -- Common fields
    Lang_Cd VARCHAR(50),
    Timezone_Cd VARCHAR(50),
    CountryCode VARCHAR(255),
    
    -- Processing status fields
    deleted SMALLINT DEFAULT 0,
    objpk INTEGER, -- Resolved Job PK after processing
    processstatus SMALLINT, -- 0=Pending, 1=Success, 2=Failed
    errormsg VARCHAR(2000),
    
    CONSTRAINT DI_job_pkey PRIMARY KEY (processfilepk)
);

CREATE INDEX IF NOT EXISTS idx_DI_job_runid ON DI_job(runId);
CREATE INDEX IF NOT EXISTS idx_DI_job_processstatus ON DI_job(processstatus);
CREATE INDEX IF NOT EXISTS idx_DI_job_job_id ON DI_job(job_id);
CREATE INDEX IF NOT EXISTS idx_DI_job_job_code ON DI_job(job_code);

COMMENT ON TABLE DI_job IS 'Temporary table for Job/Position file imports';
COMMENT ON COLUMN DI_job.processstatus IS '0=Pending, 1=Success, 2=Failed';

-- ============================================================================
-- TEMPORARY TABLE: DI_skill
-- Purpose: Temporary table for Skill file imports
-- ============================================================================

CREATE TABLE IF NOT EXISTS DI_skill (
    processfilepk INTEGER NOT NULL DEFAULT nextval('DI_skill_sequence'::regclass),
    runId INTEGER REFERENCES fileImport(importPK),
    
    -- Skill fields
    skill_id VARCHAR(50),
    skill_name VARCHAR(200),
    skill_code VARCHAR(20),
    SkillType VARCHAR(255), -- Code table reference (CatCd=1003)
    category VARCHAR(100),
    description VARCHAR(1000),
    level INTEGER,
    active SMALLINT, -- 0 or 1 (boolean converted to smallint)
    
    -- Common fields
    Lang_Cd VARCHAR(50),
    Timezone_Cd VARCHAR(50),
    CountryCode VARCHAR(255),
    
    -- Processing status fields
    deleted SMALLINT DEFAULT 0,
    objpk INTEGER, -- Resolved Skill PK after processing
    processstatus SMALLINT, -- 0=Pending, 1=Success, 2=Failed
    errormsg VARCHAR(2000),
    
    CONSTRAINT DI_skill_pkey PRIMARY KEY (processfilepk)
);

CREATE INDEX IF NOT EXISTS idx_DI_skill_runid ON DI_skill(runId);
CREATE INDEX IF NOT EXISTS idx_DI_skill_processstatus ON DI_skill(processstatus);
CREATE INDEX IF NOT EXISTS idx_DI_skill_skill_id ON DI_skill(skill_id);
CREATE INDEX IF NOT EXISTS idx_DI_skill_skill_code ON DI_skill(skill_code);

COMMENT ON TABLE DI_skill IS 'Temporary table for Skill file imports';
COMMENT ON COLUMN DI_skill.processstatus IS '0=Pending, 1=Success, 2=Failed';

-- ============================================================================
-- TEMPORARY TABLE: DI_emp
-- Purpose: Temporary table for Person/Employee file imports
-- Includes fields from Person, PersonOptional, UserLogin, and PersonOrg tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS DI_emp (
    processfilepk INTEGER NOT NULL DEFAULT nextval('DI_emp_sequence'::regclass),
    runId INTEGER REFERENCES fileImport(importPK),
    
    -- Person table fields
    PersonNumber VARCHAR(200),
    FirstName VARCHAR(500),
    MiddleName VARCHAR(200),
    LastName VARCHAR(500),
    Preferredname VARCHAR(500),
    Email VARCHAR(200),
    Active SMALLINT, -- 0 or 1
    LoginEnabled SMALLINT, -- 0 or 1
    Inst SMALLINT DEFAULT 0,
    title VARCHAR(200),
    Role_Cd VARCHAR(50), -- References Roles table
    photourl VARCHAR(200),
    Currency_Cd VARCHAR(50), -- References Currency table
    StatusCodeId VARCHAR(255), -- Code table reference (CatCd=1004)
    TypeCodeId VARCHAR(255), -- Code table reference (CatCd=200)
    IsDeleted SMALLINT DEFAULT 0,
    StartDate TIMESTAMPTZ,
    EndDate TIMESTAMPTZ,
    City VARCHAR(255),
    State VARCHAR(255),
    MgrPersonNumber VARCHAR(200), -- References Person table (PersonNumber)
    
    -- PersonOptional table fields (Text1-Text30)
    Text1 VARCHAR(255), Text2 VARCHAR(255), Text3 VARCHAR(255), Text4 VARCHAR(255), Text5 VARCHAR(255),
    Text6 VARCHAR(255), Text7 VARCHAR(255), Text8 VARCHAR(255), Text9 VARCHAR(255), Text10 VARCHAR(255),
    Text11 VARCHAR(255), Text12 VARCHAR(255), Text13 VARCHAR(255), Text14 VARCHAR(255), Text15 VARCHAR(255),
    Text16 VARCHAR(255), Text17 VARCHAR(255), Text18 VARCHAR(255), Text19 VARCHAR(255), Text20 VARCHAR(255),
    Text21 VARCHAR(255), Text22 VARCHAR(255), Text23 VARCHAR(255), Text24 VARCHAR(255), Text25 VARCHAR(255),
    Text26 VARCHAR(255), Text27 VARCHAR(255), Text28 VARCHAR(255), Text29 VARCHAR(255), Text30 VARCHAR(255),
    
    -- PersonOptional table fields (Date1-Date5)
    Date1 TIMESTAMPTZ, Date2 TIMESTAMPTZ, Date3 TIMESTAMPTZ, Date4 TIMESTAMPTZ, Date5 TIMESTAMPTZ,
    
    -- UserLogin table fields
    UserName VARCHAR(100),
    Password VARCHAR(255),
    MustChangePwd SMALLINT, -- 0 or 1
    
    -- PersonOrg table fields
    OrgFK VARCHAR(50), -- References Organization table (org_code)
    IsPrimary SMALLINT, -- 0 or 1
    PersonOrgIsDeleted SMALLINT DEFAULT 0,
    
    -- Common fields
    Lang_Cd VARCHAR(50), -- References Lang table (maps to LocaleFK)
    Timezone_Cd VARCHAR(50), -- References Timezone table (maps to TimezoneID)
    CountryCode VARCHAR(255), -- Code table reference (CatCd=1006, maps to CountryCodeId)
    
    -- Processing status fields
    deleted SMALLINT DEFAULT 0,
    objpk INTEGER, -- Resolved Person PK after processing
    objprntfk INTEGER, -- Resolved Manager Person PK (MgrFK)
    processstatus SMALLINT, -- 0=Pending, 1=Success, 2=Failed
    errormsg VARCHAR(2000),
    
    CONSTRAINT DI_emp_pkey PRIMARY KEY (processfilepk)
);

CREATE INDEX IF NOT EXISTS idx_DI_emp_runid ON DI_emp(runId);
CREATE INDEX IF NOT EXISTS idx_DI_emp_processstatus ON DI_emp(processstatus);
CREATE INDEX IF NOT EXISTS idx_DI_emp_person_number ON DI_emp(PersonNumber);
CREATE INDEX IF NOT EXISTS idx_DI_emp_email ON DI_emp(Email);

COMMENT ON TABLE DI_emp IS 'Temporary table for Person/Employee file imports (includes PersonOptional, UserLogin, PersonOrg fields)';
COMMENT ON COLUMN DI_emp.processstatus IS '0=Pending, 1=Success, 2=Failed';

-- ============================================================================
-- TEMPORARY TABLE: DI_empAssociations
-- Purpose: Temporary table for Employee Associations file imports
-- ============================================================================

CREATE TABLE IF NOT EXISTS DI_empAssociations (
    processfilepk INTEGER NOT NULL DEFAULT nextval('DI_empAssociations_sequence'::regclass),
    runId INTEGER REFERENCES fileImport(importPK),
    
    -- EmpAssociations fields
    Emp_No VARCHAR(200), -- References Person table (PersonNumber)
    Obj_Cd VARCHAR(255), -- Object code (org_code, job_code, skill_code, etc.)
    Obj_Type INTEGER, -- 0=Organization, 1=Job, 2=Skill, etc.
    AssociationType INTEGER, -- Same as Obj_Type if not specified
    
    -- Processing status fields
    deleted SMALLINT DEFAULT 0,
    objpk INTEGER, -- Resolved EmpAssociations PK after processing
    objprntfk INTEGER, -- Resolved Employee Person PK
    objprntfk2 INTEGER, -- Resolved Object PK (Organization, Job, or Skill PK)
    processstatus SMALLINT, -- 0=Pending, 1=Success, 2=Failed
    errormsg VARCHAR(2000),
    
    CONSTRAINT DI_empAssociations_pkey PRIMARY KEY (processfilepk)
);

CREATE INDEX IF NOT EXISTS idx_DI_emp_assoc_runid ON DI_empAssociations(runId);
CREATE INDEX IF NOT EXISTS idx_DI_emp_assoc_processstatus ON DI_empAssociations(processstatus);
CREATE INDEX IF NOT EXISTS idx_DI_emp_assoc_emp_no ON DI_empAssociations(Emp_No);
CREATE INDEX IF NOT EXISTS idx_DI_emp_assoc_obj_cd ON DI_empAssociations(Obj_Cd);
CREATE INDEX IF NOT EXISTS idx_DI_emp_assoc_obj_type ON DI_empAssociations(Obj_Type);

COMMENT ON TABLE DI_empAssociations IS 'Temporary table for Employee Associations file imports';
COMMENT ON COLUMN DI_empAssociations.processstatus IS '0=Pending, 1=Success, 2=Failed';
COMMENT ON COLUMN DI_empAssociations.Obj_Type IS '0=Organization, 1=Job, 2=Skill, etc.';

-- ============================================================================
-- HELPER VIEWS FOR MONITORING
-- ============================================================================

-- View to check processing status by runId
CREATE OR REPLACE VIEW vw_DI_status AS
SELECT 
    'org' AS object_type,
    runId,
    COUNT(*) AS total_records,
    COUNT(*) FILTER (WHERE processstatus = 0) AS pending,
    COUNT(*) FILTER (WHERE processstatus = 1) AS success,
    COUNT(*) FILTER (WHERE processstatus = 2) AS failed
FROM DI_org
GROUP BY runId
UNION ALL
SELECT 
    'job' AS object_type,
    runId,
    COUNT(*) AS total_records,
    COUNT(*) FILTER (WHERE processstatus = 0) AS pending,
    COUNT(*) FILTER (WHERE processstatus = 1) AS success,
    COUNT(*) FILTER (WHERE processstatus = 2) AS failed
FROM DI_job
GROUP BY runId
UNION ALL
SELECT 
    'skill' AS object_type,
    runId,
    COUNT(*) AS total_records,
    COUNT(*) FILTER (WHERE processstatus = 0) AS pending,
    COUNT(*) FILTER (WHERE processstatus = 1) AS success,
    COUNT(*) FILTER (WHERE processstatus = 2) AS failed
FROM DI_skill
GROUP BY runId
UNION ALL
SELECT 
    'emp' AS object_type,
    runId,
    COUNT(*) AS total_records,
    COUNT(*) FILTER (WHERE processstatus = 0) AS pending,
    COUNT(*) FILTER (WHERE processstatus = 1) AS success,
    COUNT(*) FILTER (WHERE processstatus = 2) AS failed
FROM DI_emp
GROUP BY runId
UNION ALL
SELECT 
    'empAssociations' AS object_type,
    runId,
    COUNT(*) AS total_records,
    COUNT(*) FILTER (WHERE processstatus = 0) AS pending,
    COUNT(*) FILTER (WHERE processstatus = 1) AS success,
    COUNT(*) FILTER (WHERE processstatus = 2) AS failed
FROM DI_empAssociations
GROUP BY runId;

COMMENT ON VIEW vw_DI_status IS 'View to monitor processing status by object type and runId';

-- ============================================================================
-- CLEANUP FUNCTION
-- ============================================================================
-- Function to clean up processed records older than specified days

CREATE OR REPLACE FUNCTION cleanup_processed_tmp_tables(
    days_to_keep INTEGER DEFAULT 7,
    object_type VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    table_name TEXT,
    deleted_count BIGINT
) AS $$
DECLARE
    table_names TEXT[] := ARRAY['DI_org', 'DI_job', 'DI_skill', 
                                 'DI_emp', 'DI_empAssociations'];
    tbl_name TEXT;
    deleted_count BIGINT;
    sql_text TEXT;
    cutoff_date TIMESTAMP;
BEGIN
    cutoff_date := CURRENT_TIMESTAMP - (days_to_keep || ' days')::INTERVAL;
    
    FOREACH tbl_name IN ARRAY table_names
    LOOP
        IF object_type IS NULL OR tbl_name = 'DI_' || object_type THEN
            -- Get runIds older than cutoff date
            sql_text := format('
                DELETE FROM %I 
                WHERE runId IN (
                    SELECT importPK FROM fileImport 
                    WHERE EndDtTime < %L
                )
                AND processstatus IN (1, 2)', -- Success or Failed
                tbl_name,
                cutoff_date
            );
            EXECUTE sql_text;
            GET DIAGNOSTICS deleted_count = ROW_COUNT;
            RETURN QUERY SELECT tbl_name::TEXT, deleted_count;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_processed_tmp_tables IS 'Clean up processed temporary records older than specified days based on fileImport.EndDtTime';

-- ============================================================================
-- GRANT PERMISSIONS (Adjust as needed for your security model)
-- ============================================================================

-- Grant usage on sequences
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- Grant permissions on tables
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;

-- ============================================================================
-- END OF SCRIPT
-- ============================================================================

