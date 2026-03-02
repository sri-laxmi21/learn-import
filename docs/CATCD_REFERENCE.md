# Category Code (CatCd) Reference Guide

This document provides a reference for all Category Codes (CatCd) used in the Code table for foreign key lookups.

## Code Table Structure

```sql
Code(
    ItmId INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    CatCd int NOT NULL,
    ItmCd varchar(255),
    LngCd smallint,
    ItmTxt varchar(500),
    IsDeleted smallint,
    UNIQUE(CatCd, ItmCd)
);
```

## Category Code Values

### CatCd = 1001: Organization Type

**Field:** `OrgType` (in org schema)

**Example Values:**
- `'-1'` → Division
- `'Dept'` → Department

**Usage:**
```sql
SELECT ItmId FROM Code WHERE CatCd = 1001 AND ItmCd = '-1'
```

**Import Example:**
```csv
org_id,org_name,OrgType
ORG001,Engineering Division,-1
ORG002,HR Department,Dept
```

---

### CatCd = 1003: Skill Type

**Field:** `SkillType` (in skill schema)

**Example Values:**
- `'1'` → Conceptual
- `'2'` → Procedural

**Usage:**
```sql
SELECT ItmId FROM Code WHERE CatCd = 1003 AND ItmCd = '1'
```

**Import Example:**
```csv
skill_id,skill_name,SkillType
SK001,Problem Solving,1
SK002,Data Entry,2
```

---

### CatCd = 1004: Person Active Status

**Field:** `StatusCodeId` (in emp schema)

**Example Values:**
- `'Active'` → Active
- `'Inactive'` → Inactive
- `'LOA'` → Leave of Absence

**Usage:**
```sql
SELECT ItmId FROM Code WHERE CatCd = 1004 AND ItmCd = 'Active'
```

**Import Example:**
```csv
PersonNumber,FirstName,LastName,StatusCodeId
P001,John,Doe,Active
P002,Jane,Smith,LOA
```

---

### CatCd = 1006: Country Codes

**Field:** `CountryCode` (common field, available to all objects)

**Example Values:**
- `'US'` → United States
- `'CA'` → Canada

**Usage:**
```sql
SELECT ItmId FROM Code WHERE CatCd = 1006 AND ItmCd = 'US'
```

**Import Example:**
```csv
PersonNumber,FirstName,LastName,CountryCode
P001,John,Doe,US
P002,Jane,Smith,CA
```

---

## Lookup Pattern

All Code table lookups follow this pattern:

```python
# Using FKResolver
fk_resolver = FKResolver(session)

# Resolve with CatCd
itm_id = fk_resolver.resolve_code(
    code_value="Active",  # ItmCd value
    cat_cd=1004           # CatCd value
)

# Or using schema-based resolution
itm_id = fk_resolver.resolve_fk_from_schema(
    field_name="StatusCodeId",
    field_value="Active",
    schema=schema
)
```

**SQL Equivalent:**
```sql
SELECT ItmId 
FROM Code 
WHERE CatCd = <cat_cd_value> 
  AND ItmCd = <code_value>
  AND IsDeleted = 0
```

## Field Mapping Summary

| CatCd | Field Name | Object Type | Example ItmCd Values |
|-------|-----------|-------------|---------------------|
| 1001 | OrgType | org | '-1', 'Dept' |
| 1003 | SkillType | skill | '1', '2' |
| 1004 | StatusCodeId | emp | 'Active', 'Inactive', 'LOA' |
| 1006 | CountryCode | common | 'US', 'CA' |

## Adding New Category Codes

When adding a new category code:

1. **Insert into Code table:**
   ```sql
   INSERT INTO Code (CatCd, ItmCd, LngCd, ItmTxt, IsDeleted)
   VALUES (1007, 'VALUE', 0, 'Description', 0);
   ```

2. **Update schema configuration:**
   - Add field to appropriate schema in `config/schemas.json`
   - Include `cat_cd` value in field configuration
   - Add FK mapping if needed

3. **Update this documentation:**
   - Add new CatCd entry with examples
   - Update field mapping summary table

## Notes

- **CatCd values are static** - They represent fixed categories in the Code table
- **ItmCd values are dynamic** - They represent the actual code values that can be imported
- **Unique constraint** - The combination of (CatCd, ItmCd) must be unique
- **Language support** - LngCd field supports multiple languages (0 = default/English)
- **Soft delete** - Use `IsDeleted = 0` to filter active codes only

## Common Patterns

### Resolving Multiple Code Types

```python
# Person with status and country
status_pk = fk_resolver.resolve_code("Active", cat_cd=1004)
country_pk = fk_resolver.resolve_code("US", cat_cd=1006)

# Organization with type and country
org_type_pk = fk_resolver.resolve_code("-1", cat_cd=1001)
country_pk = fk_resolver.resolve_code("US", cat_cd=1006)

# Skill with type
skill_type_pk = fk_resolver.resolve_code("1", cat_cd=1003)
```

### Error Handling

```python
try:
    code_pk = fk_resolver.resolve_code("InvalidCode", cat_cd=1004)
    if code_pk is None:
        raise ValueError(f"Code 'InvalidCode' not found for CatCd=1004")
except Exception as e:
    logger.error(f"Failed to resolve code: {str(e)}")
    # Handle error appropriately
```

