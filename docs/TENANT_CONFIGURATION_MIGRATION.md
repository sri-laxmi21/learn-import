# Tenant Configuration Migration Guide

## Overview

Tenant configuration has been migrated from JSON/YAML/XML files to a database table in the common DB (LearnImports). This provides better security, centralized management, and easier updates.

## Changes Made

### 1. Database Schema Updates

**New Table: `Tenants`** (in common DB)
- `TenantPK` - Primary key (INT, auto-increment)
- `TenantId` - Unique tenant identifier (VARCHAR(50), e.g., 'acme_corp')
- `Name` - Tenant display name (VARCHAR(250))
- `DBString` - Database connection string (TEXT)
- `Enabled` - Active status (SMALLINT: 0=Disabled, 1=Enabled)
- `ContactEmail` - Contact email (TEXT)
- `created_at`, `updated_at` - Timestamps
- `metadata` - Additional metadata (JSONB)

**Updated Table: `import_batch`**
- Added `TenantPK` column (INT, references `Tenants(TenantPK)`)
- Kept `tenant_id` column (VARCHAR) for denormalized TenantId (easier querying)
- Both columns are indexed for performance

### 2. Configuration Files

**Removed:**
- `config/tenants.json` - No longer needed
- `config/tenants.yaml` - No longer needed
- `config/tenants.xml` - No longer needed
- `config/schemas.xml` - Duplicate (schemas.json and schemas.yaml exist)
- `config/schema_ref_mappings.yaml` - Duplicate (merged into common_fields.json)
- `config/schema_ref_mappings.json` - Merged into common_fields.json

**Created:**
- `config/dbConfig.json` - Contains ONLY the common DB connection string

**Remaining:**
- `config/schemas.json` - Object schema definitions
- `config/schemas.yaml` - Object schema definitions (alternative format)
- `config/common_fields.json` - Common field definitions and schema reference mappings (merged)

## Migration Steps

### Step 1: Create Tenants Table

Run the updated `scripts/create_import_tracking_schema.sql` in your common DB (LearnImports).

### Step 2: Migrate Existing Tenant Data

Insert existing tenants into the `Tenants` table:

```sql
-- Example: Insert tenants from old configuration
INSERT INTO Tenants (TenantId, Name, DBString, Enabled, ContactEmail)
VALUES 
    ('acme_corp', 'ACME Corporation', 'postgresql://user:pass@host:5432/acme_db', 1, 'admin@acme.com'),
    ('technova', 'Technova Inc', 'postgresql://user:pass@host:5432/technova_db', 1, 'admin@technova.com');
```

**Note:** Replace connection strings with actual values. Consider using environment variables or secure vault for production.

### Step 3: Update Application Code

Update your application code to:
1. Load tenant configuration from the `Tenants` table instead of JSON/YAML files
2. Use `TenantPK` when creating import batches
3. Query tenant DB connection strings from the database

### Step 4: Update dbConfig.json

Update `config/dbConfig.json` with your actual common DB connection string:

```json
{
  "common_db": {
    "connection_string": "postgresql://your_user:your_password@your_host:5432/LearnImports"
  }
}
```

**Security Note:** Do not commit actual credentials. Use environment variables or secure vault.

## Usage Examples

### Query Tenant Configuration

```sql
-- Get all enabled tenants
SELECT TenantPK, TenantId, Name, ContactEmail
FROM Tenants
WHERE Enabled = 1;

-- Get tenant DB connection string
SELECT DBString
FROM Tenants
WHERE TenantId = 'acme_corp';
```

### Create Import Batch with Tenant Reference

```sql
-- Create batch with TenantPK reference
INSERT INTO import_batch (TenantPK, tenant_id, batch_name, status)
SELECT TenantPK, TenantId, 'Batch 2024-01-01', 'uploaded'
FROM Tenants
WHERE TenantId = 'acme_corp';
```

### Query Batch with Tenant Information

```sql
-- Get batch details with tenant information
SELECT 
    b.batch_id,
    t.TenantId,
    t.Name AS tenant_name,
    b.batch_name,
    b.status
FROM import_batch b
JOIN Tenants t ON b.TenantPK = t.TenantPK
WHERE b.batch_id = 'your-batch-id';
```

## Application Code Updates Required

### Python Code Changes

**Old Approach (from JSON/YAML):**
```python
from ziora_imports.config.tenant_config_json import TenantConfig

config = TenantConfig()
tenant = config.get_tenant('acme_corp')
db_url = os.getenv(tenant.database_url_env)
```

**New Approach (from Database):**
```python
# Query tenant from database
from sqlalchemy import create_engine, text

common_db_url = load_common_db_url()  # From dbConfig.json
engine = create_engine(common_db_url)

with engine.connect() as conn:
    result = conn.execute(
        text("SELECT TenantPK, TenantId, DBString FROM Tenants WHERE TenantId = :tenant_id"),
        {"tenant_id": "acme_corp"}
    )
    tenant = result.fetchone()
    db_url = tenant.DBString
```

## Benefits

1. **Centralized Management**: All tenant configuration in one place
2. **Better Security**: Connection strings stored securely in database
3. **Easier Updates**: Update tenant config without code changes
4. **Audit Trail**: Track when tenants were created/updated
5. **Referential Integrity**: Foreign key constraints ensure data consistency
6. **Simplified Configuration**: Only one config file (dbConfig.json) for common DB

## Rollback Plan

If you need to rollback:

1. Restore deleted tenant config files from version control
2. Revert application code changes
3. Keep `Tenants` table for future migration (optional)

## Security Considerations

1. **Encrypt DBString**: Consider encrypting connection strings in the database
2. **Access Control**: Restrict access to `Tenants` table
3. **Audit Logging**: Log all changes to tenant configuration
4. **Environment Variables**: Use environment variables for sensitive data
5. **Secure Vault**: Consider using a secure vault for production

## Next Steps

1. ✅ Run updated schema script
2. ⏳ Migrate existing tenant data
3. ⏳ Update application code to use database
4. ⏳ Update dbConfig.json with actual connection string
5. ⏳ Test import functionality
6. ⏳ Remove old tenant config loading code

