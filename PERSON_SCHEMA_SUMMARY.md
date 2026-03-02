# Person/Employee Schema Configuration Summary

## What Was Created

A comprehensive Person/Employee schema configuration based on your SQL `Person` table structure, with support for foreign key resolution using code values.

## Files Updated/Created

### 1. Schema Configuration Files
- ✅ **`config/schemas.json`** - Updated with complete Person schema (JSON format)
- ✅ **`config/schemas.yaml`** - Updated with complete Person schema (YAML format)

### 2. Documentation
- ✅ **`docs/PERSON_SCHEMA.md`** - Comprehensive documentation of the Person schema
  - Field descriptions
  - Foreign key mapping strategy
  - Validation rules
  - Sample import formats

### 3. Utility Code
- ✅ **`ziora_imports/core/fk_resolver.py`** - Foreign key resolver utility
  - Resolves code values to primary keys
  - Caching for performance
  - Helper methods for common FK lookups
  - Schema-based FK resolution

## Key Features

### Foreign Key Handling
All foreign key fields use **code values** instead of primary keys:

| Import Field | Code Value | Maps To | Database Field |
|-------------|------------|---------|----------------|
| `Lang_Cd` | "EN" | `LangPK` | `LocaleFK` |
| `Timezone_Cd` | "EST" | `TimezonePK` | `TimeZoneFK` |
| `Currency_Cd` | "USD" | `CurrencyPK` | `CurrencyFK` |
| `Role_Cd` | "ADMIN" | `RolePK` | `RoleFK` |
| `StatusCodeId` | "ACTIVE" | `ItmId` | `StatusCodeId` |
| `TypeCodeId` | "EMPLOYEE" | `ItmId` | `TypeCodeId` |
| `CountryCodeId` | "US" | `ItmId` | `CountryCodeId` |
| `MgrPersonNumber` | "P001" | `PersonPK` | `MgrFK` |

### Schema Fields

The schema includes **all fields** from your Person table:

**Core Fields:**
- PersonNumber (required, unique)
- FirstName, MiddleName, LastName, Preferredname
- Email (validated)
- title, photourl

**Status Flags:**
- Active, LoginEnabled, Inst, IsDeleted (all smallint: 0 or 1)

**Foreign Keys (using codes):**
- Role_Cd → RoleFK
- Lang_Cd → LocaleFK
- Timezone_Cd → TimeZoneFK
- Currency_Cd → CurrencyFK
- StatusCodeId, TypeCodeId, CountryCodeId → Code references
- MgrPersonNumber → MgrFK (self-reference)

**Location:**
- City, State

**Dates:**
- StartDate, EndDate (nullable)
- CreatedDate, ModifiedDate

**Audit:**
- CreatedBy, ModifiedBy

## Usage Example

### Import File (CSV)
```csv
PersonNumber,FirstName,LastName,Email,Lang_Cd,Timezone_Cd,Role_Cd,Active
P001,John,Doe,john@example.com,EN,EST,ADMIN,1
P002,Jane,Smith,jane@example.com,EN,PST,USER,1
```

### Processing Flow
1. Read CSV file with code values (Lang_Cd="EN", Timezone_Cd="EST", etc.)
2. Use `FKResolver` to resolve codes to primary keys
3. Insert into Person table with resolved FK values

### Code Example
```python
from ziora_imports.core.fk_resolver import FKResolver
from ziora_imports.config.schema_config_json import SchemaConfig

# Get schema
schema_config = SchemaConfig()
schema = schema_config.get_schema('emp')

# Initialize FK resolver
fk_resolver = FKResolver(session)

# Resolve foreign keys
lang_pk = fk_resolver.resolve_lang_code("EN")  # Returns LangPK
timezone_pk = fk_resolver.resolve_timezone_code("EST")  # Returns TimezonePK
role_pk = fk_resolver.resolve_role_code("ADMIN")  # Returns RolePK

# Or use schema-based resolution
locale_fk = fk_resolver.resolve_fk_from_schema(
    field_name="Lang_Cd",
    field_value="EN",
    schema=schema
)
```

## Next Steps

1. **Update Processor** - Modify `ziora_imports/processors/emp_processor.py` to:
   - Use the new field names (PersonNumber, FirstName, etc.)
   - Integrate `FKResolver` for foreign key lookups
   - Handle the new field structure

2. **Test Import** - Create test CSV files with:
   - PersonNumber and other required fields
   - Code values for foreign keys (Lang_Cd, Timezone_Cd, etc.)
   - Test FK resolution

3. **Extend Schema** - If needed, add support for:
   - PersonOptional table (Text1-Text30, Date1-Date5)
   - UserLogin table

## Field Mapping Reference

| Database Column | Import Field | Type | Length | Required |
|----------------|--------------|------|--------|----------|
| PersonPK | (auto-generated) | int | - | - |
| PersonNumber | PersonNumber | string | 200 | ✅ Yes |
| FirstName | FirstName | string | 500 | No |
| MiddleName | MiddleName | string | 200 | No |
| LastName | LastName | string | 500 | No |
| Preferredname | Preferredname | string | 500 | No |
| Email | Email | string | 200 | No |
| Active | Active | integer | - | No |
| LoginEnabled | LoginEnabled | integer | - | No |
| Inst | Inst | integer | - | No |
| title | title | string | 200 | No |
| RoleFK | Role_Cd | string→int | 50 | No |
| photourl | photourl | string | 200 | No |
| LocaleFK | Lang_Cd | string→int | 50 | No |
| TimeZoneFK | Timezone_Cd | string→int | 50 | No |
| CurrencyFK | Currency_Cd | string→int | 50 | No |
| StatusCodeId | StatusCodeId | string→int | 50 | No |
| TypeCodeId | TypeCodeId | string→int | 50 | No |
| IsDeleted | IsDeleted | integer | - | No |
| CreatedDate | CreatedDate | datetime | - | No |
| CreatedBy | CreatedBy | integer | - | No |
| ModifiedDate | ModifiedDate | datetime | - | No |
| ModifiedBy | ModifiedBy | integer | - | No |
| StartDate | StartDate | datetime | - | No |
| EndDate | EndDate | datetime | - | No |
| City | City | string | 255 | No |
| State | State | string | 255 | No |
| CountryCodeId | CountryCodeId | string→int | 50 | No |
| MgrFK | MgrPersonNumber | string→int | 200 | No |

## Validation Rules

- **Email**: Must match pattern `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
- **PersonNumber**: 1-200 characters, must be unique
- **Status Flags** (Active, LoginEnabled, IsDeleted, Inst): Must be 0 or 1
- **Foreign Keys**: Code values must exist in referenced tables

## Notes

- All foreign key fields accept code values in the import file
- The system automatically resolves codes to primary keys during import
- Missing or invalid code values will cause row import to fail with clear error messages
- FK resolution is cached for performance

