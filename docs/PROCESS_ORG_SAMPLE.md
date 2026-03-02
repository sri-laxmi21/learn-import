# Processing org_sample.csv

## Prerequisites

Before processing the sample file, ensure:

1. **Dependencies are installed:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Database is set up:**
   - Common DB (LearnImports) with `Tenants` table created
   - Tenant-specific database exists
   - Tenant is registered in `Tenants` table

3. **Environment variables are configured:**
   - Common DB connection string (or in `config/dbConfig.json`)
   - Tenant DB connection strings (in `Tenants` table `DBString` column)

## Command to Process org_sample.csv

### Single File Import

```bash
python main.py --tenant <tenant_name> --object org --file samples/org_sample.csv
```

**Example:**
```bash
python main.py --tenant acme_corp --object org --file samples/org_sample.csv
```

### With Custom Logging

```bash
python main.py --tenant acme_corp --object org --file samples/org_sample.csv --log-level DEBUG
```

## Expected Output

The import process will:
1. Load and validate the CSV file
2. Check schema compliance
3. Load data into tenant-specific temp tables (`processfiletmp_org`)
4. Process records at database level
5. Insert/update records in actual `Organization` table
6. Report results

## Sample Output

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

### Error: Tenant not found
- Ensure tenant exists in `Tenants` table
- Check `TenantId` matches exactly (case-sensitive)

### Error: Database connection failed
- Verify `DBString` in `Tenants` table is correct
- Test database connection manually
- Check database server is running

### Error: Schema validation failed
- Verify CSV columns match schema
- Check required fields are present
- Validate data types match schema definition

### Error: Foreign key resolution failed
- Ensure parent organizations exist before importing child orgs
- Verify `OrgType` values exist in Code table (CatCd=1001)
- Check `Lang_Cd`, `Timezone_Cd`, `CountryCode` values exist in respective tables

## File Location

The sample file is located at: `samples/org_sample.csv`

## Next Steps

After processing org_sample.csv:
1. Verify data in `Organization` table
2. Check `processfiletmp_org` table for processing status
3. Review logs in `logs/<tenant_name>/org_YYYYMMDD.log`
4. Process other object types (job, skill, emp, emp_associations)

