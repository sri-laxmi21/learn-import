# Organization Import File Samples

## Overview

This document provides sample organization import files in different formats (CSV, TXT pipe-delimited) that match the org schema definition.

## Schema Fields

### Required Fields
- `org_id` (VARCHAR(50)) - Unique organization identifier
- `org_name` (VARCHAR(200)) - Organization name

### Optional Fields
- `org_code` (VARCHAR(20)) - Organization code
- `OrgType` (VARCHAR(255)) - Organization type from Code table (CatCd=1001)
  - Examples: `-1` (Division), `Dept` (Department)
- `parent_org_id` (VARCHAR(50)) - Parent organization ID (for hierarchy)
- `address` (VARCHAR(500)) - Street address
- `city` (VARCHAR(100)) - City name
- `country` (VARCHAR(100)) - Country name
- `active` (BOOLEAN/SMALLINT) - Active status (0 or 1, true/false)

### Common Fields (Available to all objects)
- `Lang_Cd` (VARCHAR(50)) - Language code (references Lang table)
  - Examples: `EN` (English), `FR` (French), `ES` (Spanish)
- `Timezone_Cd` (VARCHAR(50)) - Timezone code (references Timezone table)
  - Examples: `EST`, `PST`, `CST`, `GMT`, `UTC`
- `CountryCode` (VARCHAR(255)) - Country code from Code table (CatCd=1006)
  - Examples: `US` (United States), `CA` (Canada), `GB` (United Kingdom)

## File Format: CSV

**File:** `org_sample.csv`

```csv
org_id,org_name,org_code,OrgType,parent_org_id,address,city,country,active,Lang_Cd,Timezone_Cd,CountryCode
ACME001,ACME Corporation Headquarters,ACME-HQ,Dept,,123 Corporate Blvd,New York,United States,1,EN,EST,US
ACME002,Sales Department,ACME-SALES,Dept,ACME001,456 Sales Street,New York,United States,1,EN,EST,US
ACME003,Engineering Department,ACME-ENG,Dept,ACME001,789 Tech Avenue,San Francisco,United States,1,EN,PST,US
ACME004,Marketing Division,ACME-MKTG,Dept,ACME001,321 Marketing Lane,Chicago,United States,1,EN,CST,US
ACME005,ACME Canada Office,ACME-CA,Dept,,100 Maple Street,Toronto,Canada,1,EN,EST,CA
```

## File Format: TXT (Pipe-Delimited)

**File:** `org_sample.txt`

```
org_id|org_name|org_code|OrgType|parent_org_id|address|city|country|active|Lang_Cd|Timezone_Cd|CountryCode
ACME001|ACME Corporation Headquarters|ACME-HQ|Dept||123 Corporate Blvd|New York|United States|1|EN|EST|US
ACME002|Sales Department|ACME-SALES|Dept|ACME001|456 Sales Street|New York|United States|1|EN|EST|US
ACME003|Engineering Department|ACME-ENG|Dept|ACME001|789 Tech Avenue|San Francisco|United States|1|EN|PST|US
ACME004|Marketing Division|ACME-MKTG|Dept|ACME001|321 Marketing Lane|Chicago|United States|1|EN|CST|US
ACME005|ACME Canada Office|ACME-CA|Dept||100 Maple Street|Toronto|Canada|1|EN|EST|CA
```

## File Format: XLSX (Excel)

**File:** `org_sample.xlsx`

The Excel file should have the same columns as CSV, with the first row as headers:

| org_id | org_name | org_code | OrgType | parent_org_id | address | city | country | active | Lang_Cd | Timezone_Cd | CountryCode |
|--------|----------|----------|---------|---------------|---------|------|---------|--------|---------|-------------|-------------|
| ACME001 | ACME Corporation Headquarters | ACME-HQ | Dept | | 123 Corporate Blvd | New York | United States | 1 | EN | EST | US |
| ACME002 | Sales Department | ACME-SALES | Dept | ACME001 | 456 Sales Street | New York | United States | 1 | EN | EST | US |
| ACME003 | Engineering Department | ACME-ENG | Dept | ACME001 | 789 Tech Avenue | San Francisco | United States | 1 | EN | PST | US |

## Field Value Examples

### OrgType Values (Code Table CatCd=1001)
- `-1` - Division
- `Dept` - Department
- `Branch` - Branch Office
- `Subsidiary` - Subsidiary Company

### Lang_Cd Values (References Lang table)
- `EN` - English
- `FR` - French
- `ES` - Spanish
- `DE` - German
- `ZH` - Chinese
- `JA` - Japanese

### Timezone_Cd Values (References Timezone table)
- `EST` - Eastern Standard Time
- `PST` - Pacific Standard Time
- `CST` - Central Standard Time
- `MST` - Mountain Standard Time
- `GMT` - Greenwich Mean Time
- `UTC` - Coordinated Universal Time

### CountryCode Values (Code Table CatCd=1006)
- `US` - United States
- `CA` - Canada
- `GB` - United Kingdom
- `AU` - Australia
- `DE` - Germany
- `FR` - France
- `JP` - Japan
- `CN` - China

### Active Values
- `1` or `true` - Active
- `0` or `false` - Inactive

## Minimal Required Fields Example

If you only provide required fields:

```csv
org_id,org_name
ACME001,ACME Corporation Headquarters
ACME002,Sales Department
ACME003,Engineering Department
```

## Complete Example with All Fields

```csv
org_id,org_name,org_code,OrgType,parent_org_id,address,city,country,active,Lang_Cd,Timezone_Cd,CountryCode
ACME001,ACME Corporation Headquarters,ACME-HQ,Dept,,123 Corporate Blvd,New York,United States,1,EN,EST,US
ACME002,Sales Department,ACME-SALES,Dept,ACME001,456 Sales Street,New York,United States,1,EN,EST,US
ACME003,Engineering Department,ACME-ENG,Dept,ACME001,789 Tech Avenue,San Francisco,United States,1,EN,PST,US
ACME004,Marketing Division,ACME-MKTG,Dept,ACME001,321 Marketing Lane,Chicago,United States,1,EN,CST,US
ACME005,ACME Canada Office,ACME-CA,Dept,,100 Maple Street,Toronto,Canada,1,EN,EST,CA
ACME006,HR Department,ACME-HR,Dept,ACME001,555 HR Plaza,New York,United States,1,EN,EST,US
ACME007,Finance Division,ACME-FIN,Dept,ACME001,777 Finance Tower,New York,United States,1,EN,EST,US
ACME008,Operations Department,ACME-OPS,Dept,ACME001,999 Operations Way,Atlanta,United States,1,EN,EST,US
ACME009,IT Support,ACME-IT,Dept,ACME001,111 Tech Center,Austin,United States,1,EN,CST,US
ACME010,Legal Department,ACME-LEGAL,Dept,ACME001,222 Legal Court,Washington,United States,1,EN,EST|US
```

## Notes

1. **Column Order**: Column order doesn't matter, but headers must match field names exactly
2. **Case Sensitivity**: Field names are case-sensitive (`org_id` not `Org_ID`)
3. **Empty Values**: Leave empty for optional fields (or omit the column entirely)
4. **Parent References**: `parent_org_id` must reference an existing `org_id` in the same import or already in the database
5. **Encoding**: Files should be UTF-8 encoded
6. **Special Characters**: If values contain commas (CSV) or pipes (TXT), they should be properly escaped or quoted
7. **Boolean Values**: Use `1`/`0` or `true`/`false` for active field

## Validation Rules

- `org_id`: Required, max 50 characters, must be unique
- `org_name`: Required, max 200 characters
- `org_code`: Optional, max 20 characters, pattern: `^[A-Z0-9]{2,10}$` (if provided)
- `OrgType`: Must exist in Code table where CatCd=1001
- `parent_org_id`: Must reference existing org_id (if provided)
- `Lang_Cd`: Must exist in Lang table (if provided)
- `Timezone_Cd`: Must exist in Timezone table (if provided)
- `CountryCode`: Must exist in Code table where CatCd=1006 (if provided)

## Sample Files Location

Sample files are available in the `samples/` directory:
- `samples/org_sample.csv` - CSV format
- `samples/org_sample.txt` - TXT pipe-delimited format

