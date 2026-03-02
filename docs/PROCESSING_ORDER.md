# Processing Order for Batch Imports

## Overview

When processing multiple files for a tenant, files **must** be processed in a specific order to ensure foreign key dependencies are satisfied.

## Processing Order

The system processes files in this **fixed order**:

1. **Org** (Organizations)
2. **Job** (Jobs/Positions)
3. **Skill** (Skills)
4. **Emp** (Employees/Persons)
5. **EmpAssociations** (Employee Associations)

## Why This Order?

### Dependency Chain

```
Org (no dependencies)
  ↓
Job (may reference Org)
  ↓
Skill (no dependencies)
  ↓
Emp (may reference Org, Job, Skill via codes)
  ↓
EmpAssociations (references Emp + Org/Job/Skill)
```

### Detailed Dependencies

1. **Org** - Base objects, no dependencies
2. **Job** - May reference Organizations
3. **Skill** - Independent objects
4. **Emp** - References:
   - Organizations (via OrgFK/OrgCode)
   - Jobs (via Job references)
   - Skills (via Skill references)
   - Roles, Currency, Lang, Timezone, etc.
5. **EmpAssociations** - References:
   - Employees (via Emp_No → PersonNumber)
   - Organizations (via Obj_Cd when Obj_Type=0)
   - Jobs (via Obj_Cd when Obj_Type=1)
   - Skills (via Obj_Cd when Obj_Type=2)

## Batch Processing

### Command Line Usage

```bash
python main.py --tenant acme_corp --batch --files-dir ./import_files
```

### File Naming Convention

The system looks for files with these names (in order of preference):

**Supported File Formats:**
- **CSV** (`.csv`) - Comma-delimited
- **Excel** (`.xlsx`, `.xls`) - Excel format
- **Text** (`.txt`) - Pipe-delimited (`|`)

| Object Type | File Names (in order) |
|-------------|----------------------|
| org | `org.csv`, `org.xlsx`, `org.txt`, `organization.csv`, `organization.xlsx`, `organization.txt` |
| job | `job.csv`, `job.xlsx`, `job.txt`, `jobs.csv`, `jobs.xlsx`, `jobs.txt` |
| skill | `skill.csv`, `skill.xlsx`, `skill.txt`, `skills.csv`, `skills.xlsx`, `skills.txt` |
| emp | `emp.csv`, `emp.xlsx`, `emp.txt`, `employee.csv`, `employee.xlsx`, `employee.txt`, `person.csv`, `person.xlsx`, `person.txt` |
| emp_associations | `emp_associations.csv`, `emp_associations.xlsx`, `emp_associations.txt`, `associations.csv`, `associations.xlsx`, `associations.txt` |

### Example Directory Structure

```
import_files/
├── org.csv
├── job.csv
├── skill.csv
├── emp.csv
└── emp_associations.csv
```

## Processing Flow

### Step-by-Step Execution

1. **Load Configuration**
   - Load tenant configuration
   - Load schema configurations
   - Test database connection

2. **Process Org**
   - Load `org.csv`
   - Validate schema
   - Insert organizations
   - Commit transaction

3. **Process Job**
   - Load `job.csv`
   - Validate schema
   - Resolve any Org references
   - Insert jobs
   - Commit transaction

4. **Process Skill**
   - Load `skill.csv`
   - Validate schema
   - Insert skills
   - Commit transaction

5. **Process Emp**
   - Load `emp.csv`
   - Validate schema
   - Resolve FK references (Org, Job, Skill, Roles, Currency, etc.)
   - Insert persons
   - Insert PersonOptional records (if fields present)
   - Insert UserLogin records (if fields present)
   - Insert PersonOrg records (if fields present)
   - Commit transaction

6. **Process EmpAssociations**
   - Load `emp_associations.csv`
   - Validate schema
   - Resolve Emp_No → PersonPK
   - Resolve Obj_Cd → Object PK (based on Obj_Type)
   - Insert associations
   - Commit transaction

## Error Handling

### If a File is Missing

- System logs a warning
- Skips that object type
- Continues with next object type
- Reports skipped files in summary

### If Processing Fails

- Current object type processing stops
- Previous object types remain committed
- Error is logged with details
- Batch marked as failed
- Can resume from failed object type

### Transaction Management

- Each object type is processed in its own transaction
- If one object type fails, previous ones remain committed
- Allows partial success and easier recovery

## Single File Processing

You can still process individual files:

```bash
python main.py --tenant acme_corp --object emp --file emp.csv
```

**Note:** When processing individual files, ensure dependencies are already imported:
- To import `emp.csv`, ensure `org.csv`, `job.csv`, `skill.csv` are already imported
- To import `emp_associations.csv`, ensure all other files are already imported

## API Usage

### Single File Import

```python
POST /import
{
    "tenant_id": "acme_corp",
    "customer_id": "customer1",
    "object_type": "emp",
    "file_path": "/path/to/emp.csv"
}
```

### Batch Import (Future Enhancement)

A batch import endpoint could be added:

```python
POST /import/batch
{
    "tenant_id": "acme_corp",
    "customer_id": "customer1",
    "files_dir": "/path/to/import_files"
}
```

## Best Practices

1. **Always use batch mode** when importing all files for a tenant
2. **Verify file names** match expected patterns
3. **Check processing order** in logs
4. **Review skipped files** in batch summary
5. **Handle errors** by fixing and re-running from failed object type

## Example Batch Output

```
============================================================
Batch Import - Processing files in order
============================================================
Processing order: org → job → skill → emp → emp_associations

--- Processing ORG ---
Processing: org.csv
✓ org: 50 rows processed

--- Processing JOB ---
Processing: job.csv
✓ job: 30 rows processed

--- Processing SKILL ---
Processing: skill.csv
✓ skill: 100 rows processed

--- Processing EMP ---
Processing: emp.csv
✓ emp: 200 rows processed

--- Processing EMP_ASSOCIATIONS ---
Processing: emp_associations.csv
✓ emp_associations: 500 rows processed

============================================================
Batch Import Summary
============================================================
Success: True
Processed: 5 files
Failed: 0 files
Skipped: 0 files

Processed Files:
  ✓ org: 50 rows
  ✓ job: 30 rows
  ✓ skill: 100 rows
  ✓ emp: 200 rows
  ✓ emp_associations: 500 rows
```

