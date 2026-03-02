# Quick Start: Process org_sample.csv

## Current Status

The import system is trying to load tenant configuration from `config/tenants.yaml`, but we've migrated to using the `Tenants` table in the database. 

## Option 1: Quick Test (Temporary Config File)

For immediate testing, create a temporary tenant config file:

**Create `config/tenants.yaml`:**
```yaml
tenants:
  acme_corp:
    display_name: "ACME Corporation"
    database_url_env: "ACME_CORP_DB_URL"
    enabled: true
    metadata:
      description: "ACME Corporation tenant"
      contact_email: "admin@acme.com"
```

**Set environment variable:**
```bash
# Windows PowerShell
$env:ACME_CORP_DB_URL="postgresql://user:password@localhost:5432/acme_corp_db"

# Windows CMD
set ACME_CORP_DB_URL=postgresql://user:password@localhost:5432/acme_corp_db

# Linux/Mac
export ACME_CORP_DB_URL="postgresql://user:password@localhost:5432/acme_corp_db"
```

**Then run:**
```bash
python main.py --tenant acme_corp --object org --file samples/org_sample.csv
```

## Option 2: Use Database Configuration (Recommended)

### Step 1: Set up Common DB

1. Create common database (LearnImports)
2. Run `scripts/create_import_tracking_schema.sql`
3. Update `config/dbConfig.json` with common DB connection string

### Step 2: Add Tenant to Database

```sql
INSERT INTO Tenants (TenantId, Name, DBString, Enabled, ContactEmail)
VALUES (
    'acme_corp',
    'ACME Corporation',
    'postgresql://user:password@localhost:5432/acme_corp_db',
    1,
    'admin@acme.com'
);
```

### Step 3: Update Application Code

The application code needs to be updated to load tenant configuration from the database instead of files. This requires updating:
- `ziora_imports/config/tenant_config.py` or `tenant_config_json.py`
- `ziora_imports/core/database.py`

### Step 4: Run Import

```bash
python main.py --tenant acme_corp --object org --file samples/org_sample.csv
```

## Prerequisites Checklist

Before processing, ensure:

- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Tenant database exists and is accessible
- [ ] Tenant configuration set up (file or database)
- [ ] Database connection string configured
- [ ] Required tables exist in tenant database:
  - `Organization` table
  - `processfiletmp_org` table
  - `fileImport` table
  - `fileImport_Log` table
- [ ] Reference tables populated:
  - `Code` table (for OrgType, CountryCode)
  - `Lang` table (for Lang_Cd)
  - `Timezone` table (for Timezone_Cd)

## Command Reference

```bash
# Basic import
python main.py --tenant <tenant_name> --object org --file samples/org_sample.csv

# With debug logging
python main.py --tenant acme_corp --object org --file samples/org_sample.csv --log-level DEBUG

# Batch import (processes all files in directory)
python main.py --tenant acme_corp --batch --files-dir samples/
```

## Expected Output

```
============================================================
Ziora Data Imports - Starting Import Process
============================================================
Tenant: acme_corp
Object Type: org
File: samples/org_sample.csv
Processing file: samples/org_sample.csv
============================================================
Import Results
============================================================
Success: True
Total Rows: 10
Processed Rows: 10
Failed Rows: 0
Import completed successfully
```

## Troubleshooting

**Error: Tenant not found**
- Check tenant exists in config file or database
- Verify tenant name matches exactly (case-sensitive)

**Error: Database connection failed**
- Verify connection string is correct
- Test database connection manually
- Check database server is running

**Error: Table does not exist**
- Run tenant database schema scripts:
  - `scripts/create_tenant_fileimport_enhanced.sql`
  - `scripts/create_processfiletmp_tables.sql`

**Error: Foreign key violation**
- Ensure reference tables are populated:
  - Code table (CatCd=1001 for OrgType, CatCd=1006 for CountryCode)
  - Lang table
  - Timezone table

