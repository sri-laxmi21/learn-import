# Tenant Database Configuration from Tenants Table

## Overview

The import system now loads tenant database configuration from the `Tenants` table in the common database (LearnImports) instead of configuration files. Tenant lookup is case-insensitive (converted to lowercase).

## Implementation

### Key Changes

1. **New Module**: `ziora_imports/config/tenant_config_db.py`
   - Loads tenant configuration from `Tenants` table
   - Case-insensitive tenant lookup (lowercase)
   - Gets `DBString` directly from database

2. **Updated**: `ziora_imports/core/database.py`
   - `get_connection_string()` now queries `Tenants` table first
   - Falls back to environment variables for backward compatibility
   - Case-insensitive tenant ID matching

3. **Updated**: `main.py`
   - Uses `TenantConfigDB` instead of `TenantConfig`
   - Validates tenant exists before processing
   - Stops processing if tenant not found

## How It Works

### 1. Load Common DB Configuration

The system loads the common database connection string from `config/dbConfig.json`:

```json
{
  "common_db": {
    "connection_string": "postgresql://user:password@localhost:5432/LearnImports"
  }
}
```

### 2. Query Tenants Table

On startup, the system queries the `Tenants` table:

```sql
SELECT TenantPK, TenantId, Name, DBString, Enabled, ContactEmail, metadata
FROM Tenants
WHERE Enabled = 1
```

### 3. Case-Insensitive Lookup

Tenant IDs are stored with lowercase keys for case-insensitive matching:

```python
# User provides: "ACME_Corp" or "acme_corp" or "Acme_Corp"
# System converts to: "acme_corp" (lowercase)
# Looks up in: _tenants["acme_corp"]
```

### 4. Get Database Connection String

When processing a file:

```python
# 1. Lookup tenant (case-insensitive)
tenant = tenant_config.get_tenant("acme_corp")  # or "ACME_CORP"

# 2. Get DBString
db_string = tenant.DBString

# 3. Create database connection
engine = create_engine(db_string)
```

### 5. Validation Before Processing

The system validates tenant exists and is enabled **before** processing:

```python
if not tenant_config.is_tenant_enabled(tenant_id):
    logger.error(f"Tenant '{tenant_id}' not found or not enabled")
    sys.exit(1)  # Stop processing
```

## Tenant Lookup Flow

```
User provides tenant_id: "ACME_Corp"
    ↓
Convert to lowercase: "acme_corp"
    ↓
Query Tenants table: WHERE LOWER(TenantId) = 'acme_corp'
    ↓
Found? → Get DBString → Process file
Not Found? → Error → Stop processing
```

## Database Schema

The `Tenants` table structure:

```sql
CREATE TABLE Tenants (
    TenantPK INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    TenantId VARCHAR(50) NOT NULL UNIQUE,
    Name VARCHAR(250) NOT NULL,
    DBString TEXT NOT NULL,
    Enabled SMALLINT DEFAULT 1,
    ContactEmail TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);
```

## Example Usage

### Add Tenant to Database

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

### Process File

```bash
# Case-insensitive tenant ID
python main.py --tenant ACME_CORP --object org --file samples/org_sample.csv
python main.py --tenant acme_corp --object org --file samples/org_sample.csv
python main.py --tenant Acme_Corp --object org --file samples/org_sample.csv
# All work the same way
```

## Error Handling

### Tenant Not Found

```
ERROR - Tenant 'acme_corp' not found in Tenants table or not enabled
INFO - Available tenants: technova, test_tenant
```

**Action**: Processing stops immediately, file is not processed.

### Database Connection Failed

```
ERROR - Error initializing database connection: [error details]
WARNING - Common database URL not configured. Tenant configuration will not be loaded.
```

**Action**: Processing stops, tenant configuration cannot be loaded.

### Tenant Disabled

```
ERROR - Tenant 'acme_corp' not found in Tenants table or not enabled
```

**Action**: Only enabled tenants (Enabled=1) are loaded, processing stops.

## Backward Compatibility

The system maintains backward compatibility with environment variables:

1. **First**: Try to get tenant from `Tenants` table
2. **Fallback**: If not found, try environment variable `{TENANT_ID}_DB_URL`
3. **Error**: If neither found, raise ValueError

```python
# Priority order:
# 1. Tenants table (DBString)
# 2. Environment variable ({TENANT_ID}_DB_URL)
# 3. Error if neither found
```

## Benefits

1. **Centralized Configuration**: All tenant config in one database table
2. **Case-Insensitive**: User-friendly tenant ID matching
3. **Early Validation**: Stops processing if tenant not found
4. **Security**: Database connection strings stored securely
5. **Easy Updates**: Update tenant config without code changes
6. **Audit Trail**: Track tenant creation/updates via timestamps

## Migration Notes

- Old code using `TenantConfig` (from files) still works
- New code uses `TenantConfigDB` (from database)
- Both can coexist during migration
- Environment variables still work as fallback

## Testing

To test tenant lookup:

```python
from ziora_imports.config.tenant_config_db import TenantConfigDB

# Initialize
config = TenantConfigDB()

# Check if tenant exists (case-insensitive)
if config.is_tenant_enabled("acme_corp"):
    tenant = config.get_tenant("acme_corp")
    print(f"Found: {tenant.Name}")
    print(f"DB: {tenant.DBString}")
else:
    print("Tenant not found")
```

