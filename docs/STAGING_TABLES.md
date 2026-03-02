# Staging Tables Documentation

## Overview

Staging tables are intermediate tables where data from import files is loaded after format validation, before being processed and loaded into the actual application tables. This approach provides several benefits:

1. **Data Validation**: Validate data format before processing
2. **Error Tracking**: Track validation errors per row
3. **Batch Processing**: Group imports by batch ID
4. **Audit Trail**: Track when data was imported and processed
5. **Recovery**: Ability to reprocess failed records

## Table Structure

### Common Metadata Columns

All staging tables include these metadata columns:

| Column | Type | Description |
|--------|------|-------------|
| `staging_id` | BIGSERIAL | Primary key for staging record |
| `import_batch_id` | VARCHAR(100) | Batch identifier for grouping imports |
| `row_number` | INTEGER | Row number from source file |
| `validation_status` | VARCHAR(20) | Status: `pending`, `valid`, `invalid`, `processed` |
| `error_message` | TEXT | Error message if validation failed |
| `created_at` | TIMESTAMPTZ | When record was created in staging |
| `processed_at` | TIMESTAMPTZ | When record was processed into actual table |

### Staging Tables

#### 1. `staging.stg_org` - Organization Staging

**Purpose**: Staging table for Organization imports

**Fields**:
- `org_id` (VARCHAR(50), required)
- `org_name` (VARCHAR(200), required)
- `org_code` (VARCHAR(20))
- `OrgType` (VARCHAR(255)) - Code table reference (CatCd=1001)
- `parent_org_id` (VARCHAR(50))
- `address` (VARCHAR(500))
- `city` (VARCHAR(100))
- `country` (VARCHAR(100))
- `active` (BOOLEAN)
- Common fields: `Lang_Cd`, `Timezone_Cd`, `CountryCode`

#### 2. `staging.stg_job` - Job Staging

**Purpose**: Staging table for Job/Position imports

**Fields**:
- `job_id` (VARCHAR(50), required)
- `job_title` (VARCHAR(200), required)
- `job_code` (VARCHAR(20))
- `department` (VARCHAR(100))
- `level` (INTEGER)
- `min_salary` (NUMERIC(10, 2))
- `max_salary` (NUMERIC(10, 2))
- `active` (BOOLEAN)
- Common fields: `Lang_Cd`, `Timezone_Cd`, `CountryCode`

#### 3. `staging.stg_skill` - Skill Staging

**Purpose**: Staging table for Skill imports

**Fields**:
- `skill_id` (VARCHAR(50), required)
- `skill_name` (VARCHAR(200), required)
- `skill_code` (VARCHAR(20))
- `SkillType` (VARCHAR(255)) - Code table reference (CatCd=1003)
- `category` (VARCHAR(100))
- `description` (VARCHAR(1000))
- `level` (INTEGER)
- `active` (BOOLEAN)
- Common fields: `Lang_Cd`, `Timezone_Cd`, `CountryCode`

#### 4. `staging.stg_emp` - Employee Staging

**Purpose**: Staging table for Person/Employee imports

**Includes fields from**:
- Person table
- PersonOptional table (Text1-Text30, Date1-Date5)
- UserLogin table
- PersonOrg table

**Fields**:
- **Person fields**: `PersonNumber`, `FirstName`, `MiddleName`, `LastName`, `Preferredname`, `Email`, `Active`, `LoginEnabled`, `Inst`, `title`, `Role_Cd`, `photourl`, `Currency_Cd`, `StatusCodeId`, `TypeCodeId`, `IsDeleted`, `StartDate`, `EndDate`, `City`, `State`, `MgrPersonNumber`
- **PersonOptional fields**: `Text1` through `Text30` (VARCHAR(255)), `Date1` through `Date5` (TIMESTAMPTZ)
- **UserLogin fields**: `UserName`, `Password`, `MustChangePwd`
- **PersonOrg fields**: `OrgFK`, `IsPrimary`, `PersonOrgIsDeleted`
- Common fields: `Lang_Cd`, `Timezone_Cd`, `CountryCode`

#### 5. `staging.stg_emp_associations` - Employee Associations Staging

**Purpose**: Staging table for Employee Associations imports

**Fields**:
- `Emp_No` (VARCHAR(200), required) - References Person table (PersonNumber)
- `Obj_Cd` (VARCHAR(255), required) - Object code (org_code, job_code, skill_code, etc.)
- `Obj_Type` (INTEGER, required) - 0=Organization, 1=Job, 2=Skill, etc.
- `AssociationType` (INTEGER) - Same as Obj_Type if not specified

## Installation

### Option 1: Shared Staging Schema (Recommended)

All tenants use the same staging schema with shared tables:

```sql
-- Run the script
\i scripts/create_staging_tables.sql
```

This creates tables in the `staging` schema:
- `staging.stg_org`
- `staging.stg_job`
- `staging.stg_skill`
- `staging.stg_emp`
- `staging.stg_emp_associations`

### Option 2: Tenant-Specific Tables

Each tenant gets its own staging tables:

```sql
-- Create staging tables for a specific tenant
SELECT create_tenant_staging_tables('acme_corp');
SELECT create_tenant_staging_tables('technova');
```

This creates tables with tenant prefix:
- `acme_corp_stg_org`
- `acme_corp_stg_job`
- etc.

## Data Flow

```
1. Import File (CSV/XLSX/TXT)
   ↓
2. Format Validation
   ↓
3. Load into Staging Table
   ├─ Set validation_status = 'pending'
   ├─ Assign import_batch_id
   └─ Store row_number
   ↓
4. Data Validation
   ├─ Schema validation
   ├─ Foreign key resolution
   └─ Business rule validation
   ↓
5. Update validation_status
   ├─ 'valid' if all checks pass
   └─ 'invalid' if errors found (with error_message)
   ↓
6. Process Valid Records
   ├─ Transform data
   ├─ Resolve foreign keys
   ├─ Insert into actual tables
   └─ Set validation_status = 'processed', processed_at = NOW()
```

## Usage Examples

### Loading Data into Staging

```python
# After format validation, load into staging
import pandas as pd
from sqlalchemy import create_engine

# Load file
df = pd.read_csv('employees.csv')

# Add metadata columns
df['import_batch_id'] = 'batch_20240101_001'
df['row_number'] = range(1, len(df) + 1)
df['validation_status'] = 'pending'
df['created_at'] = pd.Timestamp.now()

# Load into staging table
engine = create_engine(db_url)
df.to_sql('stg_emp', engine, schema='staging', if_exists='append', index=False)
```

### Querying Staging Data

```sql
-- Check validation status
SELECT validation_status, COUNT(*) 
FROM staging.stg_emp 
WHERE import_batch_id = 'batch_20240101_001'
GROUP BY validation_status;

-- View invalid records
SELECT row_number, error_message, PersonNumber, Email
FROM staging.stg_emp
WHERE validation_status = 'invalid'
AND import_batch_id = 'batch_20240101_001';

-- View unprocessed valid records
SELECT *
FROM staging.stg_emp
WHERE validation_status = 'valid'
AND processed_at IS NULL;
```

### Processing Valid Records

```sql
-- Process valid records (example)
INSERT INTO Person (PersonNumber, FirstName, LastName, ...)
SELECT PersonNumber, FirstName, LastName, ...
FROM staging.stg_emp
WHERE validation_status = 'valid'
AND processed_at IS NULL;

-- Mark as processed
UPDATE staging.stg_emp
SET validation_status = 'processed',
    processed_at = CURRENT_TIMESTAMP
WHERE validation_status = 'valid'
AND processed_at IS NULL;
```

## Cleanup

### Manual Cleanup

```sql
-- Delete processed records older than 30 days
DELETE FROM staging.stg_emp
WHERE validation_status = 'processed'
AND processed_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
```

### Using Cleanup Function

```sql
-- Clean up all staging tables (keeps 30 days)
SELECT * FROM staging.cleanup_processed_staging(30);

-- Clean up specific object type (keeps 7 days)
SELECT * FROM staging.cleanup_processed_staging(7, 'emp');
```

## Indexes

All staging tables have indexes on:
- `import_batch_id` - For batch queries
- `validation_status` - For filtering by status
- Primary key fields (`org_id`, `job_id`, `skill_id`, `PersonNumber`, `Emp_No`) - For lookups

## Best Practices

1. **Batch IDs**: Use consistent batch ID format (e.g., `{tenant}_{date}_{sequence}`)
2. **Validation**: Always validate data before marking as 'valid'
3. **Error Messages**: Provide clear, actionable error messages
4. **Cleanup**: Regularly clean up processed records to manage table size
5. **Monitoring**: Monitor staging table sizes and validation failure rates
6. **Retry Logic**: Allow reprocessing of 'invalid' records after fixes

## Security Considerations

- Grant appropriate permissions to application users
- Consider row-level security if needed
- Audit staging table access
- Encrypt sensitive data (e.g., passwords) before loading

## Troubleshooting

### Staging Table Not Found

```sql
-- Check if staging schema exists
SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'staging';

-- Check if tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'staging';
```

### Performance Issues

- Ensure indexes are created
- Consider partitioning by `import_batch_id` for large imports
- Monitor table bloat and run VACUUM regularly

### Data Type Mismatches

- Ensure staging table column types match import file data types
- Use appropriate casting when loading data
- Validate data types during format validation

