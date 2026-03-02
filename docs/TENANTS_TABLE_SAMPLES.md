# Tenants Table - Sample DBString Values

## Overview

The `Tenants` table stores database connection strings for each tenant. The `DBString` column contains the PostgreSQL connection string for the tenant-specific database.

## Sample INSERT Statements

### Basic Connection String Format

```sql
-- PostgreSQL connection string format:
-- postgresql://[user[:password]@][host][:port][/database][?parameters]

-- Example 1: Local development
INSERT INTO Tenants (TenantId, Name, DBString, Enabled, ContactEmail)
VALUES (
    'acme_corp',
    'ACME Corporation',
    'postgresql://postgres:password123@localhost:5432/acme_corp_db',
    1,
    'admin@acme.com'
);

-- Example 2: Remote server with default port
INSERT INTO Tenants (TenantId, Name, DBString, Enabled, ContactEmail)
VALUES (
    'technova',
    'Technova Inc',
    'postgresql://dbuser:securepass@db-server.example.com:5432/technova_db',
    1,
    'admin@technova.com'
);

-- Example 3: With SSL mode
INSERT INTO Tenants (TenantId, Name, DBString, Enabled, ContactEmail)
VALUES (
    'acme_corp',
    'ACME Corporation',
    'postgresql://postgres:password123@localhost:5432/acme_corp_db?sslmode=require',
    1,
    'admin@acme.com'
);

-- Example 4: With connection pool parameters
INSERT INTO Tenants (TenantId, Name, DBString, Enabled, ContactEmail)
VALUES (
    'acme_corp',
    'ACME Corporation',
    'postgresql://postgres:password123@localhost:5432/acme_corp_db?sslmode=prefer&connect_timeout=10',
    1,
    'admin@acme.com'
);

-- Example 5: Using IP address
INSERT INTO Tenants (TenantId, Name, DBString, Enabled, ContactEmail)
VALUES (
    'tenant1',
    'Tenant One',
    'postgresql://dbuser:password@192.168.1.100:5432/tenant1_db',
    1,
    'admin@tenant1.com'
);

-- Example 6: Without password (using .pgpass or peer authentication)
INSERT INTO Tenants (TenantId, Name, DBString, Enabled, ContactEmail)
VALUES (
    'local_dev',
    'Local Development',
    'postgresql://postgres@localhost:5432/local_dev_db',
    1,
    'dev@localhost'
);

-- Example 7: With schema specification
INSERT INTO Tenants (TenantId, Name, DBString, Enabled, ContactEmail)
VALUES (
    'acme_corp',
    'ACME Corporation',
    'postgresql://postgres:password123@localhost:5432/acme_corp_db?options=-csearch_path%3Dpublic',
    1,
    'admin@acme.com'
);
```

## Connection String Components

| Component | Description | Example |
|-----------|-------------|---------|
| `user` | Database username | `postgres`, `dbuser` |
| `password` | Database password | `password123`, `securepass` |
| `host` | Database host | `localhost`, `db-server.example.com`, `192.168.1.100` |
| `port` | Database port | `5432` (default PostgreSQL port) |
| `database` | Database name | `acme_corp_db`, `technova_db` |
| `parameters` | Additional parameters | `sslmode=require`, `connect_timeout=10` |

## Common Parameters

- `sslmode`: SSL connection mode
  - `disable` - No SSL
  - `allow` - Try non-SSL first, then SSL
  - `prefer` - Try SSL first, then non-SSL (default)
  - `require` - Require SSL
  - `verify-ca` - Require SSL and verify CA
  - `verify-full` - Require SSL and verify CA + hostname

- `connect_timeout`: Connection timeout in seconds
- `application_name`: Application name for logging
- `options`: Additional connection options

## Security Best Practices

### 1. Use Environment Variables (Recommended)

Instead of storing passwords directly in the database, use environment variables:

```sql
-- Store connection string template (without password)
INSERT INTO Tenants (TenantId, Name, DBString, Enabled, ContactEmail)
VALUES (
    'acme_corp',
    'ACME Corporation',
    'postgresql://postgres:${ACME_DB_PASSWORD}@localhost:5432/acme_corp_db',
    1,
    'admin@acme.com'
);
```

Then replace `${ACME_DB_PASSWORD}` at runtime from environment variables.

### 2. Encrypt DBString Column

Consider encrypting the `DBString` column for additional security:

```sql
-- Example using pgcrypto extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt when inserting
INSERT INTO Tenants (TenantId, Name, DBString, Enabled, ContactEmail)
VALUES (
    'acme_corp',
    'ACME Corporation',
    pgp_sym_encrypt('postgresql://postgres:password123@localhost:5432/acme_corp_db', 'encryption_key'),
    1,
    'admin@acme.com'
);

-- Decrypt when reading
SELECT TenantId, Name, pgp_sym_decrypt(DBString::bytea, 'encryption_key') AS DBString
FROM Tenants
WHERE TenantId = 'acme_corp';
```

### 3. Use Connection Pooling

For production, consider using connection pooling (e.g., PgBouncer):

```sql
INSERT INTO Tenants (TenantId, Name, DBString, Enabled, ContactEmail)
VALUES (
    'acme_corp',
    'ACME Corporation',
    'postgresql://postgres:password123@pgbouncer.example.com:6432/acme_corp_db',
    1,
    'admin@acme.com'
);
```

## Sample Data for Testing

```sql
-- Insert multiple tenants for testing
INSERT INTO Tenants (TenantId, Name, DBString, Enabled, ContactEmail) VALUES
    ('acme_corp', 'ACME Corporation', 'postgresql://postgres:password123@localhost:5432/acme_corp_db', 1, 'admin@acme.com'),
    ('technova', 'Technova Inc', 'postgresql://postgres:password123@localhost:5432/technova_db', 1, 'admin@technova.com'),
    ('test_tenant', 'Test Tenant', 'postgresql://postgres:password123@localhost:5432/test_db', 1, 'test@example.com'),
    ('disabled_tenant', 'Disabled Tenant', 'postgresql://postgres:password123@localhost:5432/disabled_db', 0, 'disabled@example.com');
```

## Querying Tenant Connection Strings

```sql
-- Get connection string for a tenant
SELECT DBString
FROM Tenants
WHERE TenantId = 'acme_corp'
AND Enabled = 1;

-- Get all enabled tenants with their connection strings
SELECT TenantId, Name, DBString, ContactEmail
FROM Tenants
WHERE Enabled = 1;

-- Get tenant info without exposing full connection string (for security)
SELECT 
    TenantId,
    Name,
    SUBSTRING(DBString FROM 'postgresql://[^@]+@([^:]+)') AS host,
    SUBSTRING(DBString FROM 'postgresql://[^/]+/(.+)') AS database,
    Enabled,
    ContactEmail
FROM Tenants;
```

## Notes

1. **Never commit actual passwords** to version control
2. **Use environment variables** or secure vaults for production
3. **Rotate passwords** regularly
4. **Use SSL** for production connections (`sslmode=require`)
5. **Restrict access** to the `Tenants` table to authorized users only
6. **Audit access** to connection strings
7. **Consider using** connection pooling for better performance

