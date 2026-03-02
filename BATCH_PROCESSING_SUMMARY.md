# Batch Processing and EmpAssociations Summary

## What Was Created

### 1. EmpAssociations Schema ✅

Created new schema for Employee Associations with fields:
- **Emp_No** (required) - Employee number (PersonNumber), references Person table
- **Obj_Cd** (required) - Object code (org_code, job_code, skill_code, etc.)
- **Obj_Type** (required) - Object type: 0=Org, 1=Job, 2=Skill, etc.
- **AssociationType** (optional) - Association type (defaults to Obj_Type)

### 2. EmpAssociations Processor ✅

Created `EmpAssociationsProcessor` that:
- Resolves Emp_No to PersonPK
- Resolves Obj_Cd to object PK based on Obj_Type
- Handles different object types (Org, Job, Skill)
- Inserts associations into EmpAssociations table

### 3. Batch Processing Support ✅

Enhanced `main.py` with:
- `--batch` flag for batch processing
- `--files-dir` for specifying directory with all files
- Automatic processing in correct order
- File name pattern matching
- Batch results summary

### 4. Processing Order Enforcement ✅

Defined `PROCESSING_ORDER` constant:
```python
PROCESSING_ORDER = ['org', 'job', 'skill', 'emp', 'emp_associations']
```

## Processing Order

Files are processed in this **fixed order**:

1. **Org** → Organizations (base objects)
2. **Job** → Jobs/Positions (may reference Org)
3. **Skill** → Skills (independent)
4. **Emp** → Employees/Persons (references Org, Job, Skill, etc.)
5. **EmpAssociations** → Associations (references Emp + Org/Job/Skill)

## Usage

### Batch Processing

```bash
python main.py --tenant acme_corp --batch --files-dir ./import_files
```

**File Structure:**
```
import_files/
├── org.csv          # Processed 1st
├── job.csv          # Processed 2nd
├── skill.csv        # Processed 3rd
├── emp.csv          # Processed 4th
└── emp_associations.csv  # Processed 5th
```

### Single File Processing

```bash
python main.py --tenant acme_corp --object emp_associations --file associations.csv
```

**Note:** Ensure Org, Job, Skill, and Emp files are already imported.

## EmpAssociations Import Format

### CSV Example
```csv
Emp_No,Obj_Cd,Obj_Type,AssociationType
P001,ORG001,0,0
P001,JOB001,1,1
P002,SKILL001,2,2
```

### Field Mapping

| Import Field | Description | Example |
|-------------|-------------|---------|
| Emp_No | Employee PersonNumber | P001 |
| Obj_Cd | Object code value | ORG001, JOB001, SKILL001 |
| Obj_Type | Object type code | 0=Org, 1=Job, 2=Skill |
| AssociationType | Association type (optional) | Same as Obj_Type if not provided |

## Obj_Type Reference

| Obj_Type | Object Type | Code Field | PK Field | Table |
|----------|-------------|------------|----------|-------|
| 0 | Organization | org_code | OrgPK | Organization |
| 1 | Job | job_code | job_id | Job |
| 2 | Skill | skill_code | skill_id | Skill |

## Files Updated/Created

1. ✅ `config/schemas.json` - Added emp_associations schema
2. ✅ `config/schemas.yaml` - Added emp_associations schema
3. ✅ `ziora_imports/processors/emp_associations_processor.py` - NEW processor
4. ✅ `ziora_imports/processors/__init__.py` - Added EmpAssociationsProcessor
5. ✅ `main.py` - Added batch processing support
6. ✅ `ziora_imports/api/service.py` - Added EmpAssociationsProcessor
7. ✅ `docs/EMP_ASSOCIATIONS_SCHEMA.md` - Documentation
8. ✅ `docs/PROCESSING_ORDER.md` - Processing order guide

## Benefits

1. **Enforced Order**: System automatically processes files in correct dependency order
2. **Batch Support**: Process all files for a tenant with one command
3. **Error Recovery**: If one file fails, previous files remain committed
4. **Clear Dependencies**: Processing order makes dependencies explicit
5. **Flexible**: Can still process individual files if needed

## Next Steps

1. Test batch processing with sample files
2. Verify FK resolution for all object types
3. Update database schema if EmpAssociations table structure differs
4. Add more Obj_Type mappings if needed
