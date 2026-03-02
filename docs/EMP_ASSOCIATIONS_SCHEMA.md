# Employee Associations Schema

## Overview

The Employee Associations (`emp_associations`) schema handles associations between Employees and other objects (Organizations, Jobs, Skills, etc.). This schema must be processed **after** all other objects (Org, Job, Skill, Emp) have been imported.

## Processing Order

When processing files for a tenant, files must be processed in this order:

1. **Org** - Organizations must exist first
2. **Job** - Jobs must exist second
3. **Skill** - Skills must exist third
4. **Emp** - Employees must exist fourth
5. **EmpAssociations** - Associations are created last (references all above)

## Schema Fields

### Required Fields
- **Emp_No** (string, max 200) - Employee number (PersonNumber) - references Person table
- **Obj_Cd** (string, max 255) - Object code - the code value for the associated object
- **Obj_Type** (integer) - Object type identifier

### Optional Fields
- **AssociationType** (integer) - Association type (defaults to Obj_Type if not specified)

## Obj_Type Values

| Obj_Type | Object Type | Code Field | PK Field | Table |
|----------|-------------|------------|----------|-------|
| 0 | Organization | org_code | OrgPK | Organization |
| 1 | Job | job_code | job_id | Job |
| 2 | Skill | skill_code | skill_id | Skill |
| 3+ | (Future) | - | - | - |

## Field Details

### Emp_No
- **Type:** string
- **Length:** 200
- **Required:** Yes
- **References:** Person table via PersonNumber
- **Description:** Employee number that must exist in Person table

### Obj_Cd
- **Type:** string
- **Length:** 255
- **Required:** Yes
- **Description:** Code value for the associated object (e.g., org_code, job_code, skill_code)

### Obj_Type
- **Type:** integer
- **Required:** Yes
- **Range:** 0-10
- **Description:** Object type identifier (0=Org, 1=Job, 2=Skill, etc.)

### AssociationType
- **Type:** integer
- **Required:** No (defaults to Obj_Type)
- **Range:** 0-10
- **Description:** Association type (same as Obj_Type if not specified)

## Import File Format

### CSV Example
```csv
Emp_No,Obj_Cd,Obj_Type,AssociationType
P001,ORG001,0,0
P001,JOB001,1,1
P002,SKILL001,2,2
P002,ORG002,0,0
```

### Explanation
- Row 1: Employee P001 associated with Organization ORG001 (Obj_Type=0)
- Row 2: Employee P001 associated with Job JOB001 (Obj_Type=1)
- Row 3: Employee P002 associated with Skill SKILL001 (Obj_Type=2)
- Row 4: Employee P002 associated with Organization ORG002 (Obj_Type=0)

## Processing Logic

1. **Resolve Emp_No** → Lookup PersonNumber → Get PersonPK
2. **Resolve Obj_Cd** → Based on Obj_Type:
   - Obj_Type=0: Lookup Organization.org_code → Get OrgPK
   - Obj_Type=1: Lookup Job.job_code → Get job_id
   - Obj_Type=2: Lookup Skill.skill_code → Get skill_id
3. **Insert Association** → Create EmpAssociations record with:
   - PersonFK = resolved PersonPK
   - ObjFK = resolved object PK
   - ObjType = Obj_Type value
   - AssociationType = AssociationType (or Obj_Type if not provided)

## Validation Rules

- **Emp_No**: Must exist in Person table
- **Obj_Cd**: Must exist in the appropriate table based on Obj_Type
- **Obj_Type**: Must be 0-10
- **AssociationType**: Must be 0-10 (if provided)

## Error Handling

- If Emp_No not found → Row fails with error: "Person not found for Emp_No: {value}"
- If Obj_Cd not found → Row fails with error: "Object not found: Obj_Cd='{value}', Obj_Type={type}"
- If Obj_Type invalid → Row fails with error: "Unknown Obj_Type: {value}"

## Batch Processing

When using batch mode (`--batch`), the system automatically processes files in the correct order:

```bash
python main.py --tenant acme_corp --batch --files-dir ./import_files
```

The system will:
1. Process `org.csv` first
2. Process `job.csv` second
3. Process `skill.csv` third
4. Process `emp.csv` fourth
5. Process `emp_associations.csv` last

## Database Schema

Expected database table structure:

```sql
CREATE TABLE EmpAssociations (
    PersonFK int REFERENCES Person(PersonPK),
    ObjFK int NOT NULL,
    ObjType int NOT NULL,
    AssociationType int,
    -- Additional fields as needed
    PRIMARY KEY (PersonFK, ObjFK, ObjType)
);
```

## Notes

- Associations are created **after** all referenced objects exist
- One employee can have multiple associations (one per row)
- Same employee can be associated with multiple objects of the same type
- Duplicate associations (same PersonFK, ObjFK, ObjType) are skipped (ON CONFLICT DO NOTHING)
- AssociationType defaults to Obj_Type if not provided

