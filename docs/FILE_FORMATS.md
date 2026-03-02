# Supported File Formats

## Overview

The import system supports multiple file formats for data import. The file format is automatically detected based on the file extension.

## Supported Formats

### 1. CSV Files (`.csv`)

**Format:** Comma-delimited text files

**Example:**
```csv
PersonNumber,FirstName,LastName,Email,Active
P001,John,Doe,john.doe@example.com,1
P002,Jane,Smith,jane.smith@example.com,1
```

**Usage:**
```bash
python main.py --tenant acme_corp --object emp --file employees.csv
```

**Details:**
- Delimiter: Comma (`,`)
- Encoding: UTF-8
- First row typically contains column headers
- Standard CSV format

### 2. Excel Files (`.xlsx`, `.xls`)

**Format:** Microsoft Excel format

**Example:**
Excel spreadsheet with columns:
- PersonNumber | FirstName | LastName | Email | Active
- P001 | John | Doe | john.doe@example.com | 1
- P002 | Jane | Smith | jane.smith@example.com | 1

**Usage:**
```bash
python main.py --tenant acme_corp --object emp --file employees.xlsx
```

**Details:**
- Format: Excel 2007+ (`.xlsx`) or Excel 97-2003 (`.xls`)
- First row typically contains column headers
- Supports multiple sheets (first sheet is used by default)
- Engine: `openpyxl` for `.xlsx`, default for `.xls`

### 3. Text Files (`.txt`)

**Format:** Pipe-delimited text files

**Example:**
```txt
PersonNumber|FirstName|LastName|Email|Active
P001|John|Doe|john.doe@example.com|1
P002|Jane|Smith|jane.smith@example.com|1
```

**Usage:**
```bash
python main.py --tenant acme_corp --object emp --file employees.txt
```

**Details:**
- Delimiter: Pipe (`|`)
- Encoding: UTF-8
- First row typically contains column headers
- Useful for systems that export pipe-delimited files

## File Format Detection

The system automatically detects the file format based on the file extension:

| Extension | Format | Delimiter |
|-----------|--------|-----------|
| `.csv` | CSV | Comma (`,`) |
| `.xlsx` | Excel | N/A (Excel format) |
| `.xls` | Excel | N/A (Excel format) |
| `.txt` | Text | Pipe (`\|`) |

## Batch Processing

When using batch processing, the system looks for files with any supported extension:

```bash
python main.py --tenant acme_corp --batch --files-dir ./import_files
```

**File Discovery:**
The system searches for files in this order:
1. `{object_type}.csv`
2. `{object_type}.xlsx`
3. `{object_type}.txt`
4. Alternative names (e.g., `organization.csv`, `employee.xlsx`, etc.)

**Example Directory:**
```
import_files/
├── org.csv          # Will be processed
├── job.xlsx         # Will be processed
├── skill.txt        # Will be processed
├── emp.csv          # Will be processed
└── emp_associations.xlsx  # Will be processed
```

## File Format Selection Guidelines

### When to Use CSV

- ✅ Simple data structures
- ✅ Cross-platform compatibility
- ✅ Easy to edit in text editors
- ✅ Small to medium file sizes
- ✅ Standard format for most systems

### When to Use Excel

- ✅ Complex data with formatting
- ✅ Multiple sheets (though only first sheet is imported)
- ✅ Users familiar with Excel
- ✅ Data already in Excel format
- ✅ Need to preserve Excel-specific features

### When to Use Text (Pipe-Delimited)

- ✅ Legacy system exports
- ✅ Data contains commas (avoids CSV escaping issues)
- ✅ System-specific export format
- ✅ Fixed-width or delimited text requirements

## Error Handling

### Invalid File Format

If an unsupported file format is provided:

```
ValueError: Unsupported file format: .pdf. Supported formats: .csv, .xlsx, .xls, .txt
```

### Empty File

If a file is empty:

```
ValueError: File is empty: /path/to/file.csv
```

### Parsing Errors

If the file cannot be parsed:

```
ValueError: Error parsing file /path/to/file.csv: {error details}
```

### File Not Found

If the file does not exist:

```
FileNotFoundError: File not found: /path/to/file.csv
```

## Best Practices

1. **Consistent Format**: Use the same file format across all imports for a tenant
2. **UTF-8 Encoding**: Ensure files are saved with UTF-8 encoding
3. **Header Row**: Always include column headers in the first row
4. **File Naming**: Use descriptive names that match the object type
5. **File Size**: For very large files (>100MB), consider splitting into multiple files
6. **Validation**: Validate file format before import using a text editor or Excel

## Examples

### CSV Import
```bash
python main.py --tenant acme_corp --object emp --file employees.csv
```

### Excel Import
```bash
python main.py --tenant acme_corp --object org --file organizations.xlsx
```

### Text File Import
```bash
python main.py --tenant acme_corp --object job --file jobs.txt
```

### Batch Import (Mixed Formats)
```bash
python main.py --tenant acme_corp --batch --files-dir ./import_files
```

Where `import_files/` contains:
- `org.csv`
- `job.xlsx`
- `skill.txt`
- `emp.csv`
- `emp_associations.xlsx`

All files will be processed in the correct order regardless of format.

