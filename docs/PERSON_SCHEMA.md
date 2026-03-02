# Person/Employee Schema Configuration

## Overview

The Person/Employee (`emp`) schema is based on the `Person` table structure from the database. This schema supports importing person/employee data with proper foreign key handling using code values instead of primary keys.

## Schema Fields

### Required Fields
- **PersonNumber** (string, max 200) - Unique person identifier

### Core Person Fields
- **FirstName** (string, max 500) - First name
- **MiddleName** (string, max 200) - Middle name
- **LastName** (string, max 500) - Last name
- **Preferredname** (string, max 500) - Preferred name
- **Email** (string, max 200) - Email address (validated with email pattern)
- **title** (string, max 200) - Job title

### Status Flags (smallint: 0 or 1)
- **Active** (integer) - Active status flag
- **LoginEnabled** (integer) - Login enabled flag
- **Inst** (integer, default 0) - Institution flag
- **IsDeleted** (integer, default 0) - Soft delete flag

### Foreign Key Fields (Using Code Values)

All foreign key fields use code values from the referenced tables:

#### Role Reference
- **Role_Cd** (string, max 50)
  - References: `Roles` table
  - Maps: `Role_Cd` → `RolePK`
  - Description: Role code from Roles table

#### Locale/Language Reference
- **Lang_Cd** (string, max 50)
  - References: `Lang` table
  - Maps: `Lang_Cd` → `LangPK`
  - Description: Language code from Lang table

#### Timezone Reference
- **Timezone_Cd** (string, max 50)
  - References: `Timezone` table
  - Maps: `Timezone_Cd` → `TimezonePK`
  - Description: Timezone code from Timezone table

#### Currency Reference
- **Currency_Cd** (string, max 50)
  - References: `Currency` table
  - Maps: `Currency_Cd` → `CurrencyPK`
  - Description: Currency code from Currency table

#### Code References (Status, Type, Country)
- **StatusCodeId** (string, max 50)
  - References: `Code` table
  - Maps: `Code_Cd` → `ItmId`
  - Description: Status code from Code table

- **TypeCodeId** (string, max 50)
  - References: `Code` table
  - Maps: `Code_Cd` → `ItmId`
  - Description: Type code from Code table

- **CountryCodeId** (string, max 50)
  - References: `Code` table
  - Maps: `Code_Cd` → `ItmId`
  - Description: Country code from Code table

#### Manager Reference
- **MgrPersonNumber** (string, max 200)
  - References: `Person` table (self-reference)
  - Maps: `PersonNumber` → `PersonPK`
  - Description: Manager's PersonNumber (references another Person record)

### Location Fields
- **City** (string, max 255) - City
- **State** (string, max 255) - State/Province

### Date Fields
- **StartDate** (datetime, nullable) - Start date (TIMESTAMPTZ)
- **EndDate** (datetime, nullable) - End date (TIMESTAMPTZ)
- **CreatedDate** (datetime) - Creation timestamp (TIMESTAMPTZ)
- **ModifiedDate** (datetime) - Last modification timestamp (TIMESTAMPTZ)

### Audit Fields
- **CreatedBy** (integer) - Creator user ID
- **ModifiedBy** (integer) - Modifier user ID

### Other Fields
- **photourl** (string, max 200) - Photo URL

## Foreign Key Mapping Strategy

### How It Works

When importing data, the system expects **code values** in the import file, not primary keys. The processor will:

1. Read the code value from the import file (e.g., `Lang_Cd = "EN"`)
2. Look up the corresponding primary key in the referenced table (e.g., find `LangPK` where `Lang_Cd = "EN"`)
3. Use the primary key value when inserting into the Person table (e.g., `LocaleFK = <resolved LangPK>`)

### Example

**Import File (CSV):**
```csv
PersonNumber,FirstName,LastName,Email,Lang_Cd,Timezone_Cd,Role_Cd
P001,John,Doe,john@example.com,EN,EST,ADMIN
```

**Processing:**
1. Read `Lang_Cd = "EN"` → Lookup `Lang` table → Get `LangPK = 1` → Set `LocaleFK = 1`
2. Read `Timezone_Cd = "EST"` → Lookup `Timezone` table → Get `TimezonePK = 5` → Set `TimeZoneFK = 5`
3. Read `Role_Cd = "ADMIN"` → Lookup `Roles` table → Get `RolePK = 10` → Set `RoleFK = 10`

**Database Insert:**
```sql
INSERT INTO Person (
    PersonNumber, FirstName, LastName, Email,
    LocaleFK, TimeZoneFK, RoleFK
) VALUES (
    'P001', 'John', 'Doe', 'john@example.com',
    1, 5, 10
);
```

## Validation Rules

### Email Validation
- Pattern: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
- Must be a valid email format

### PersonNumber Validation
- Minimum length: 1
- Maximum length: 200
- Must be unique

### Status Flags Validation
- **Active**: Must be 0 or 1
- **LoginEnabled**: Must be 0 or 1
- **IsDeleted**: Must be 0 or 1
- **Inst**: Must be 0 or 1

## Unique Constraints

- **PersonNumber** - Must be unique across all persons
- **Email** - Must be unique (if provided)

## Related Tables

### PersonOptional
The `PersonOptional` table stores optional text and date fields (Text1-Text30, Date1-Date5) linked to Person via `PersonFK`. This is typically handled separately or as part of an extended import.

### UserLogin
The `UserLogin` table stores login credentials linked to Person via `PersonFK`. This is typically handled separately or as part of an extended import.

## Implementation Notes

### Code-to-PK Resolution

The processor should implement a lookup mechanism for foreign keys:

```python
def resolve_fk_code(session, table_name, code_field, code_value, pk_field):
    """
    Resolve a code value to primary key
    
    Args:
        session: Database session
        table_name: Name of the referenced table
        code_field: Name of the code field (e.g., 'Lang_Cd')
        code_value: Code value from import file
        pk_field: Name of the primary key field (e.g., 'LangPK')
    
    Returns:
        Primary key value or None if not found
    """
    query = f"SELECT {pk_field} FROM {table_name} WHERE {code_field} = :code_value"
    result = session.execute(text(query), {"code_value": code_value}).fetchone()
    return result[0] if result else None
```

### Error Handling

- If a code value cannot be resolved to a primary key, the import should fail for that row with a clear error message
- Example: `"Invalid Lang_Cd 'XYZ': Code not found in Lang table"`

## Sample Import File Format

### CSV Example
```csv
PersonNumber,FirstName,MiddleName,LastName,Preferredname,Email,Active,LoginEnabled,title,Lang_Cd,Timezone_Cd,Currency_Cd,StatusCodeId,City,State,CountryCodeId,MgrPersonNumber
P001,John,Michael,Doe,John,john.doe@example.com,1,1,Manager,EN,EST,USD,ACTIVE,New York,NY,US,P000
P002,Jane,,Smith,Jane,jane.smith@example.com,1,0,Developer,EN,PST,USD,ACTIVE,Los Angeles,CA,US,P001
```

### Excel Example
Same columns as CSV, with headers in the first row.

## Field Lengths Summary

| Field | Max Length | Type |
|-------|-----------|------|
| PersonNumber | 200 | string |
| FirstName | 500 | string |
| LastName | 500 | string |
| Preferredname | 500 | string |
| Email | 200 | string |
| title | 200 | string |
| photourl | 200 | string |
| City | 255 | string |
| State | 255 | string |
| MiddleName | 200 | string |
| FK Code fields | 50 | string |

