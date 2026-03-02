# Person Related Tables Schema

## Overview

The Person (`emp`) schema now includes fields from related tables:
- **PersonOptional** - Optional text and date fields
- **UserLogin** - Login credentials
- **PersonOrg** - Person-Organization relationships

All fields from these tables are included in the Person import schema, allowing a single import file to populate multiple related tables.

## Related Tables Structure

### PersonOptional Table

Stores optional text and date fields linked to Person via `PersonFK`.

**Fields Added to Schema:**
- **Text1 through Text30** (30 fields) - varchar(255)
- **Date1 through Date5** (5 fields) - TIMESTAMPTZ, nullable

**Example:**
```csv
PersonNumber,FirstName,LastName,Text1,Text2,Date1
P001,John,Doe,Custom Field 1,Custom Field 2,2024-01-01
```

### UserLogin Table

Stores login credentials linked to Person via `PersonFK`.

**Fields Added to Schema:**
- **UserName** - varchar(100) - User login username
- **Password** - varchar(255) - User login password
- **MustChangePwd** - smallint (0 or 1) - Must change password flag

**Example:**
```csv
PersonNumber,FirstName,LastName,UserName,Password,MustChangePwd
P001,John,Doe,jdoe,encrypted_password,1
```

### PersonOrg Table

Stores Person-Organization relationships.

**Fields Added to Schema:**
- **OrgFK** - References Organization(OrgPK) - Organization foreign key (uses Organization code)
- **IsPrimary** - smallint (0 or 1) - Primary organization flag
- **PersonOrgIsDeleted** - smallint (default 0) - Soft delete flag

**Example:**
```csv
PersonNumber,FirstName,LastName,OrgFK,IsPrimary
P001,John,Doe,ORG001,1
```

## Complete Import Example

A single CSV file can include fields from all related tables:

```csv
PersonNumber,FirstName,LastName,Email,StatusCodeId,UserName,Password,OrgFK,IsPrimary,Text1,Date1
P001,John,Doe,john@example.com,Active,jdoe,encrypted_password,ORG001,1,Custom Data,2024-01-01
P002,Jane,Smith,jane@example.com,Active,jsmith,encrypted_password,ORG002,0,Other Data,2024-01-02
```

## Field Summary

### Person Table Fields
- PersonNumber, FirstName, MiddleName, LastName, Preferredname
- Email, Active, LoginEnabled, Inst, title
- Role_Cd, Currency_Cd, StatusCodeId, TypeCodeId
- StartDate, EndDate, City, State, MgrPersonNumber
- Common fields: Lang_Cd, Timezone_Cd, CountryCode

### PersonOptional Table Fields (35 fields)
- Text1 through Text30 (30 text fields)
- Date1 through Date5 (5 date fields)

### UserLogin Table Fields (3 fields)
- UserName
- Password
- MustChangePwd

### PersonOrg Table Fields (3 fields)
- OrgFK (references Organization via schema_ref)
- IsPrimary
- PersonOrgIsDeleted

## Processing Logic

When importing Person data with related table fields:

1. **Insert Person record** with Person table fields
2. **If PersonOptional fields present:**
   - Insert/Update PersonOptional record with PersonFK = PersonPK
3. **If UserLogin fields present:**
   - Insert/Update UserLogin record with PersonFK = PersonPK
4. **If PersonOrg fields present:**
   - Insert/Update PersonOrg record with PersonFK = PersonPK and resolved OrgFK

## Organization Reference

The `OrgFK` field uses `schema_ref: "Organization"` which maps to:
- Table: `Organization`
- PK Field: `OrgPK`
- Code Field: `org_code`

**Import Format:**
- Use Organization code (org_code) in the import file
- System resolves to OrgPK automatically

## Notes

- All related table fields are **optional** - only include them if needed
- PersonOptional, UserLogin, and PersonOrg records are created/updated based on PersonFK
- If a Person record already exists, related records are updated (not duplicated)
- PersonOrg allows multiple organizations per person (one row per organization)
- For PersonOrg, if multiple organizations are needed, use separate import rows or handle programmatically

## Validation

- **MustChangePwd**: Must be 0 or 1
- **IsPrimary**: Must be 0 or 1
- **PersonOrgIsDeleted**: Must be 0 or 1 (default 0)
- **OrgFK**: Must exist in Organization table (validated via FK resolution)
- **Date fields**: Must be valid datetime format (nullable)

