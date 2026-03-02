# Schema Configuration Simplification

## Overview

The schema configuration has been simplified to reduce redundancy and improve maintainability. Foreign key references now use simplified attributes instead of repeating table, PK field, and code field information.

## Simplified Attributes

### 1. `cat_cd_ref` - Code Table References

For Code table references, use the `cat_cd_ref` attribute with the Category Code value.

**Old Format:**
```json
{
  "StatusCodeId": {
    "type": "string",
    "fk_reference": "Code",
    "fk_field": "ItmId",
    "fk_code_field": "ItmCd",
    "cat_cd": 1004
  }
}
```

**New Format:**
```json
{
  "StatusCodeId": {
    "type": "string",
    "cat_cd_ref": 1004
  }
}
```

**How it works:**
- System automatically knows: table = "Code", pk_field = "ItmId", code_field = "ItmCd"
- Only the CatCd value needs to be specified

### 2. `schema_ref` - Other Table References

For other foreign key tables (Currency, Lang, Timezone, Roles, Person), use the `schema_ref` attribute.

**Old Format:**
```json
{
  "Currency_Cd": {
    "type": "string",
    "fk_reference": "Currency",
    "fk_field": "CurrencyPK",
    "fk_code_field": "Currency_Cd"
  }
}
```

**New Format:**
```json
{
  "Currency_Cd": {
    "type": "string",
    "schema_ref": "Currency"
  }
}
```

**How it works:**
- System looks up the mapping in `config/common_fields.json` (under `schema_refs` section)
- Automatically resolves: table, pk_field, code_field

## Schema Reference Mappings

The `config/common_fields.json` file defines mappings for all schema references (under the `schema_refs` section):

```json
{
  "schema_refs": {
    "Currency": {
      "table": "Currency",
      "pk_field": "CurrencyPK",
      "code_field": "Currency_Cd"
    },
    "Lang": {
      "table": "Lang",
      "pk_field": "LangPK",
      "code_field": "Lang_Cd"
    },
    "Timezone": {
      "table": "Timezone",
      "pk_field": "TimezonePK",
      "code_field": "Timezone_Cd"
    },
    "Roles": {
      "table": "Roles",
      "pk_field": "RolePK",
      "code_field": "Role_Cd"
    },
    "Person": {
      "table": "Person",
      "pk_field": "PersonPK",
      "code_field": "PersonNumber"
    }
  }
}
```

## Examples

### Code Table Reference (cat_cd_ref)

```json
{
  "StatusCodeId": {
    "type": "string",
    "length": 255,
    "cat_cd_ref": 1004,
    "description": "Person active status"
  },
  "OrgType": {
    "type": "string",
    "length": 255,
    "cat_cd_ref": 1001,
    "description": "Organization type"
  },
  "SkillType": {
    "type": "string",
    "length": 255,
    "cat_cd_ref": 1003,
    "description": "Skill type"
  }
}
```

### Schema Reference (schema_ref)

```json
{
  "Currency_Cd": {
    "type": "string",
    "length": 50,
    "schema_ref": "Currency",
    "description": "Currency code"
  },
  "Lang_Cd": {
    "type": "string",
    "length": 50,
    "schema_ref": "Lang",
    "description": "Language code"
  },
  "Role_Cd": {
    "type": "string",
    "length": 50,
    "schema_ref": "Roles",
    "description": "Role code"
  },
  "MgrPersonNumber": {
    "type": "string",
    "length": 200,
    "schema_ref": "Person",
    "description": "Manager PersonNumber"
  }
}
```

## FK Resolver Usage

The FK resolver automatically handles both formats:

```python
from ziora_imports.core.fk_resolver import FKResolver

fk_resolver = FKResolver(session)

# Resolve using field config (simplified format)
field_config = {
    "cat_cd_ref": 1004  # For Code table
}
status_pk = fk_resolver.resolve_fk_from_field_config(
    field_name="StatusCodeId",
    field_value="Active",
    field_config=field_config
)

# Or with schema_ref
field_config = {
    "schema_ref": "Currency"  # For Currency table
}
currency_pk = fk_resolver.resolve_fk_from_field_config(
    field_name="Currency_Cd",
    field_value="USD",
    field_config=field_config
)
```

## Benefits

1. **Reduced Redundancy:** No need to repeat table, PK field, and code field for every FK reference
2. **Easier Maintenance:** Update mappings in one place (`config/common_fields.json` under `schema_refs`)
3. **Cleaner Schemas:** More concise and readable configuration files
4. **Type Safety:** CatCd values are explicit and documented
5. **Backward Compatible:** Old format still supported for migration
6. **Centralized Configuration:** Schema references and common fields are now in one file

## Migration Guide

### Step 1: Update Field Configurations

Replace old format:
```json
{
  "Currency_Cd": {
    "fk_reference": "Currency",
    "fk_field": "CurrencyPK",
    "fk_code_field": "Currency_Cd"
  }
}
```

With new format:
```json
{
  "Currency_Cd": {
    "schema_ref": "Currency"
  }
}
```

### Step 2: Update Code References

Replace old format:
```json
{
  "StatusCodeId": {
    "fk_reference": "Code",
    "fk_field": "ItmId",
    "fk_code_field": "ItmCd",
    "cat_cd": 1004
  }
}
```

With new format:
```json
{
  "StatusCodeId": {
    "cat_cd_ref": 1004
  }
}
```

### Step 3: Remove fk_mappings Sections

The `fk_mappings` sections in schemas are no longer needed and can be removed. The FK resolver uses field-level configuration instead.

## Adding New Schema References

To add a new schema reference:

1. **Add to `config/common_fields.json` (under `schema_refs` section):**
   ```json
   {
     "NewTable": {
       "table": "NewTable",
       "pk_field": "NewTablePK",
       "code_field": "NewTable_Cd"
     }
   }
   ```

2. **Use in schemas:**
   ```json
   {
     "NewTable_Cd": {
       "type": "string",
       "schema_ref": "NewTable"
     }
   }
   ```

## CatCd Reference Values

Common CatCd values (use with `cat_cd_ref`):

| CatCd | Description | Example Values |
|-------|-------------|----------------|
| 1001 | Organization Type | '-1', 'Dept' |
| 1003 | Skill Type | '1', '2' |
| 1004 | Person Active Status | 'Active', 'Inactive', 'LOA' |
| 1006 | Country Codes | 'US', 'CA' |

See `docs/CATCD_REFERENCE.md` for complete reference.

