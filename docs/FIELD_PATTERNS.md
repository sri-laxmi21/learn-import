# Field Patterns Documentation

## Overview

Field patterns allow you to define multiple similar fields using a range-based pattern instead of repeating the same field definition multiple times. This significantly reduces schema size and improves maintainability.

## Pattern Syntax

Field Pattern Syntax

Field patterns are defined in a `field_patterns` section within each schema:

```json
{
  "schemas": {
    "emp": {
      "field_types": {
        // Individual fields here
      },
      "field_patterns": {
        "Text": {
          "prefix": "Text",
          "range": [1, 30],
          "type": "string",
          "length": 255,
          "required": false,
          "description_template": "Optional text field {n} (PersonOptional table)"
        }
      }
    }
  }
}
```

## Pattern Configuration

Each pattern requires:

- **`prefix`** (string): The field name prefix (e.g., "Text", "Date")
- **`range`** (array): `[start, end]` - Inclusive range of numbers to generate
- **`type`** (string): Data type for all fields in the pattern
- **`description_template`** (string, optional): Template for field descriptions. Use `{n}` for the number and `{prefix}` for the prefix

All other field attributes (length, required, nullable, etc.) are applied to all generated fields.

## Example: Text1-Text30

**Before (30 repeated fields):**
```json
{
  "Text1": {
    "type": "string",
    "length": 255,
    "required": false,
    "description": "Optional text field 1 (PersonOptional table)"
  },
  "Text2": {
    "type": "string",
    "length": 255,
    "required": false,
    "description": "Optional text field 2 (PersonOptional table)"
  },
  // ... 28 more fields
}
```

**After (1 pattern):**
```json
{
  "field_patterns": {
    "Text": {
      "prefix": "Text",
      "range": [1, 30],
      "type": "string",
      "length": 255,
      "required": false,
      "description_template": "Optional text field {n} (PersonOptional table)"
    }
  }
}
```

This generates: `Text1`, `Text2`, `Text3`, ..., `Text30`

## Example: Date1-Date5

```json
{
  "field_patterns": {
    "Date": {
      "prefix": "Date",
      "range": [1, 5],
      "type": "datetime",
      "required": false,
      "nullable": true,
      "description_template": "Optional date field {n} (PersonOptional table, TIMESTAMPTZ, nullable)"
    }
  }
}
```

This generates: `Date1`, `Date2`, `Date3`, `Date4`, `Date5`

## Pattern Expansion

The schema loader automatically expands patterns into individual fields when loading the configuration. After expansion:

- Patterns are removed from the schema
- Generated fields are added to `field_types`
- All fields are accessible as if they were individually defined

## Generated Field Names

Field names are generated as: `{prefix}{number}`

Examples:
- Pattern `Text` with range `[1, 30]` → `Text1`, `Text2`, ..., `Text30`
- Pattern `Date` with range `[1, 5]` → `Date1`, `Date2`, `Date3`, `Date4`, `Date5`
- Pattern `CustomField` with range `[10, 15]` → `CustomField10`, `CustomField11`, ..., `CustomField15`

## Description Templates

Use placeholders in `description_template`:

- `{n}` - Replaced with the field number
- `{prefix}` - Replaced with the prefix value

**Example:**
```json
{
  "description_template": "Optional {prefix} field {n} (PersonOptional table)"
}
```

Generates:
- Text1: "Optional Text field 1 (PersonOptional table)"
- Text2: "Optional Text field 2 (PersonOptional table)"
- etc.

## Usage in Code

After loading, patterns are expanded and fields are accessible normally:

```python
from ziora_imports.config.schema_config_json import SchemaConfig

schema_config = SchemaConfig()
schema = schema_config.get_schema('emp')

# Access generated fields as normal
text1_config = schema['field_types']['Text1']
text30_config = schema['field_types']['Text30']
date1_config = schema['field_types']['Date1']
```

## Benefits

1. **Reduced Schema Size**: 30 fields become 1 pattern definition
2. **Easier Maintenance**: Update pattern once, affects all generated fields
3. **Less Error-Prone**: No copy-paste errors
4. **Clearer Intent**: Pattern clearly shows the range and structure

## Limitations

- Patterns generate fields with the same attributes (except description)
- Cannot have different attributes for different numbers in the range
- If you need different attributes, define those fields individually

## Best Practices

1. Use patterns for fields with identical attributes
2. Use descriptive prefixes (e.g., "Text", "Date", not "F1", "F2")
3. Keep ranges reasonable (e.g., [1, 30] is fine, [1, 1000] might be excessive)
4. Use clear description templates
5. Document patterns in schema comments

## Migration from Individual Fields

To convert existing repeated fields to patterns:

1. Identify fields with same attributes (e.g., Text1-Text30)
2. Extract common attributes
3. Determine prefix and range
4. Create pattern definition
5. Remove individual field definitions
6. Test that all fields are still accessible

