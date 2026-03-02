# ProcessFileTmp Tables Documentation

## Overview

The `processfiletmp_*` tables are object-specific temporary tables used to load file data after initial file validation. Data is processed from these temp tables at the database level, and records are updated with success or failed status.

## Architecture

### Related Tables

1. **`fileImport`** - Tracks file import sessions
   - `importPK` - Primary key
   - `FileName` - Name of imported file
   - `StartDtTime` - Import start time
   - `EndDtTime` - Import end time
   - `Status` - 0=Initiated, 1=InProgress, 2=Failed, 3=Completed, 4=Successful
   - `InitiatedBy` - References Person(PersonPK)

2. **`fileImport_Log`** - Logs errors during import
   - `logPK` - Primary key
   - `runId` - References fileImport(importPK)
   - `errMsg` - Error message (VARCHAR(2000))
   - `errLog` - Detailed error log (TEXT)
   - `lstUpd` - Last update timestamp

3. **`processfiletmp_*`** - Object-specific temporary tables (one per object type)

## Temporary Tables

### 1. `processfiletmp_org` - Organization Temporary Table

**Purpose**: Temporary storage for Organization imports

**Key Fields**:
- `processfilepk` - Primary key (from sequence)
- `runId` - References fileImport(importPK)
- `org_id`, `org_name`, `org_code`, `OrgType`, `parent_org_id`, `address`, `city`, `country`, `active`
- Common fields: `Lang_Cd`, `Timezone_Cd`, `CountryCode`
- Status fields: `deleted`, `objpk`, `objprntfk`, `processstatus`, `errormsg`

### 2. `processfiletmp_job` - Job Temporary Table

**Purpose**: Temporary storage for Job/Position imports

**Key Fields**:
- `processfilepk` - Primary key (from sequence)
- `runId` - References fileImport(importPK)
- `job_id`, `job_title`, `job_code`, `department`, `level`, `min_salary`, `max_salary`, `active`
- Common fields: `Lang_Cd`, `Timezone_Cd`, `CountryCode`
- Status fields: `deleted`, `objpk`, `processstatus`, `errormsg`

### 3. `processfiletmp_skill` - Skill Temporary Table

**Purpose**: Temporary storage for Skill imports

**Key Fields**:
- `processfilepk` - Primary key (from sequence)
- `runId` - References fileImport(importPK)
- `skill_id`, `skill_name`, `skill_code`, `SkillType`, `category`, `description`, `level`, `active`
- Common fields: `Lang_Cd`, `Timezone_Cd`, `CountryCode`
- Status fields: `deleted`, `objpk`, `processstatus`, `errormsg`

### 4. `processfiletmp_emp` - Employee Temporary Table

**Purpose**: Temporary storage for Person/Employee imports

**Includes fields from**:
- Person table
- PersonOptional table (Text1-Text30, Date1-Date5)
- UserLogin table
- PersonOrg table

**Key Fields**:
- `processfilepk` - Primary key (from sequence)
- `runId` - References fileImport(importPK)
- Person fields: `PersonNumber`, `FirstName`, `MiddleName`, `LastName`, `Preferredname`, `Email`, `Active`, `LoginEnabled`, `Inst`, `title`, `Role_Cd`, `photourl`, `Currency_Cd`, `StatusCodeId`, `TypeCodeId`, `IsDeleted`, `StartDate`, `EndDate`, `City`, `State`, `MgrPersonNumber`
- PersonOptional: `Text1`-`Text30`, `Date1`-`Date5`
- UserLogin: `UserName`, `Password`, `MustChangePwd`
- PersonOrg: `OrgFK`, `IsPrimary`, `PersonOrgIsDeleted`
- Common fields: `Lang_Cd`, `Timezone_Cd`, `CountryCode`
- Status fields: `deleted`, `objpk`, `objprntfk`, `processstatus`, `errormsg`

### 5. `processfiletmp_emp_associations` - Employee Associations Temporary Table

**Purpose**: Temporary storage for Employee Associations imports

**Key Fields**:
- `processfilepk` - Primary key (from sequence)
- `runId` - References fileImport(importPK)
- `Emp_No` - Employee number (PersonNumber)
- `Obj_Cd` - Object code (org_code, job_code, skill_code, etc.)
- `Obj_Type` - 0=Organization, 1=Job, 2=Skill, etc.
- `AssociationType` - Association type
- Status fields: `deleted`, `objpk`, `objprntfk`, `objprntfk2`, `processstatus`, `errormsg`

## Status Fields

### `processstatus` Values

- **0** - Pending (not yet processed)
- **1** - Success (processed successfully)
- **2** - Failed (processing failed)

### `deleted` Values

- **0** - Active record
- **1** - Deleted record

### `objpk` Field

After successful processing, this field stores the resolved primary key of the created/updated record in the actual table (e.g., `Organization.OrgPK`, `Person.PersonPK`).

### `objprntfk` Field

Stores resolved foreign key references (e.g., parent Organization PK, Manager Person PK).

## Data Flow

```
1. File Import Initiated
   ├─ Create record in fileImport table
   ├─ Status = 0 (Initiated)
   └─ Get importPK (runId)
   ↓
2. Initial File Validation
   ├─ Validate file format
   ├─ Check required columns
   └─ Validate data types
   ↓
3. Load into processfiletmp_* table
   ├─ Insert records with runId
   ├─ processstatus = 0 (Pending)
   └─ Store raw data from file
   ↓
4. Update fileImport.Status = 1 (InProgress)
   ↓
5. Database-Level Processing
   ├─ Resolve foreign keys
   ├─ Validate business rules
   ├─ Insert/Update actual tables
   ├─ Update processstatus = 1 (Success) or 2 (Failed)
   ├─ Update objpk with resolved PK
   └─ Store error message in errormsg if failed
   ↓
6. Update fileImport
   ├─ Status = 3 (Completed) or 4 (Successful) or 2 (Failed)
   └─ EndDtTime = CURRENT_TIMESTAMP
   ↓
7. Log Errors (if any)
   └─ Insert into fileImport_Log for failed records
```

## Usage Examples

### Loading Data into Temporary Table

```sql
-- After file validation, load into temp table
INSERT INTO processfiletmp_org (
    runId, org_id, org_name, org_code, OrgType, parent_org_id,
    address, city, country, active, Lang_Cd, Timezone_Cd, CountryCode,
    processstatus
)
SELECT 
    123, -- runId from fileImport
    org_id, org_name, org_code, OrgType, parent_org_id,
    address, city, country, active, Lang_Cd, Timezone_Cd, CountryCode,
    0 -- processstatus = Pending
FROM staging.stg_org
WHERE import_batch_id = 'batch_20240101_001';
```

### Processing Records (Database-Level)

```sql
-- Example: Process Organization records
UPDATE processfiletmp_org
SET 
    objpk = o.OrgPK,
    objprntfk = COALESCE(
        (SELECT OrgPK FROM Organization WHERE org_code = p.parent_org_id),
        NULL
    ),
    processstatus = 1, -- Success
    errormsg = NULL
FROM Organization o
WHERE processfiletmp_org.org_code = o.org_code
AND processfiletmp_org.processstatus = 0 -- Pending
AND processfiletmp_org.runId = 123;

-- Mark failed records
UPDATE processfiletmp_org
SET 
    processstatus = 2, -- Failed
    errormsg = 'Organization code not found'
WHERE processstatus = 0
AND runId = 123
AND objpk IS NULL;
```

### Monitoring Processing Status

```sql
-- Check status by runId
SELECT * FROM vw_processfiletmp_status
WHERE runId = 123;

-- Check failed records
SELECT processfilepk, errormsg, org_id, org_name
FROM processfiletmp_org
WHERE runId = 123
AND processstatus = 2; -- Failed

-- Check pending records
SELECT COUNT(*) AS pending_count
FROM processfiletmp_org
WHERE runId = 123
AND processstatus = 0; -- Pending
```

### Logging Errors

```sql
-- Insert error logs for failed records
INSERT INTO fileImport_Log (runId, errMsg, errLog)
SELECT 
    runId,
    errormsg,
    format('Failed to process org_id: %s, org_name: %s', org_id, org_name) AS errLog
FROM processfiletmp_org
WHERE runId = 123
AND processstatus = 2; -- Failed
```

## Cleanup

### Manual Cleanup

```sql
-- Delete processed records older than 7 days
DELETE FROM processfiletmp_org
WHERE runId IN (
    SELECT importPK FROM fileImport 
    WHERE EndDtTime < CURRENT_TIMESTAMP - INTERVAL '7 days'
)
AND processstatus IN (1, 2); -- Success or Failed
```

### Using Cleanup Function

```sql
-- Clean up all temp tables (keeps 7 days)
SELECT * FROM cleanup_processed_tmp_tables(7);

-- Clean up specific object type (keeps 3 days)
SELECT * FROM cleanup_processed_tmp_tables(3, 'emp');
```

## Indexes

All temporary tables have indexes on:
- `runId` - For batch queries
- `processstatus` - For filtering by status
- Primary identifier fields (`org_id`, `job_id`, `skill_id`, `PersonNumber`, `Emp_No`) - For lookups

## Best Practices

1. **Always set runId**: Link all temp records to fileImport record
2. **Initialize processstatus**: Set to 0 (Pending) when inserting
3. **Update atomically**: Update processstatus, objpk, and errormsg together
4. **Log errors**: Insert into fileImport_Log for failed records
5. **Cleanup regularly**: Remove processed records to manage table size
6. **Monitor status**: Use `vw_processfiletmp_status` view for monitoring
7. **Transaction safety**: Process records within transactions for data integrity

## Troubleshooting

### Records Stuck in Pending Status

```sql
-- Find records stuck in pending status
SELECT runId, COUNT(*) AS pending_count
FROM processfiletmp_org
WHERE processstatus = 0
GROUP BY runId
HAVING COUNT(*) > 0;

-- Check if fileImport is still InProgress
SELECT importPK, FileName, Status, StartDtTime
FROM fileImport
WHERE Status = 1; -- InProgress
```

### Foreign Key Resolution Issues

```sql
-- Check unresolved foreign keys
SELECT processfilepk, org_code, parent_org_id, errormsg
FROM processfiletmp_org
WHERE processstatus = 2
AND errormsg LIKE '%not found%';
```

### Performance Issues

- Ensure indexes are created
- Consider partitioning by `runId` for large imports
- Monitor table bloat and run VACUUM regularly
- Clean up old processed records regularly

