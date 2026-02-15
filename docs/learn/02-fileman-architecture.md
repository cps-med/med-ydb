# FileMan Architecture Overview

**Goal**: Understand FileMan as VistA's data abstraction layer

**Prerequisites**: Read `01-yottadb-fundamentals.md` (global structure basics)

---

## What is FileMan?

**FileMan** is VistA's database management system - think of it as VistA's ORM (Object-Relational Mapper), but for hierarchical globals instead of SQL tables.

### Key Concepts
- **File**: Like a SQL table - a collection of related records
- **Field**: Like a SQL column - a data element within a record
- **Record/Entry**: Like a SQL row - one instance of data
- **IEN**: Internal Entry Number - the primary key (auto-incremented)
- **Data Dictionary**: Metadata about files and fields (schema definition)

### Why FileMan Exists

**Problem**: Raw globals are flexible but unstructured. You could store anything anywhere.

**Solution**: FileMan provides:
- Schema definition (which fields exist, their types, validation rules)
- Data validation (required fields, value sets, formats)
- Referential integrity (pointers between files)
- Audit trails
- Standard CRUD operations

**VistA code uses FileMan APIs** instead of writing directly to globals for safety.

---

## The Data Dictionary: VistA's Self-Documenting Schema

FileMan stores its schema **in the database itself** using two main globals:

### 1. `^DIC` - File Definitions

**Structure**: `^DIC(file_number, ...)`

**Purpose**: Defines which files exist and where they're stored

**Key nodes**:
```
^DIC(file#, 0) = "FILE_NAME^FILE_NUMBER^..."
^DIC(file#, 0, "GL") = "^GLOBAL_ROOT("
^DIC(file#, 0, "NM") = "FILE_NAME"
```

**Example - File #2 (PATIENT)**:
```
^DIC(2, 0) = "PATIENT^2^..."
^DIC(2, 0, "GL") = "^DPT("
^DIC(2, 0, "NM") = "PATIENT"
```

This tells you: "File #2 is named PATIENT and stores data in global ^DPT"

### 2. `^DD` - Field Definitions

**Structure**: `^DD(file_number, field_number, ...)`

**Purpose**: Defines which fields exist in each file

**Key nodes**:
```
^DD(file#, field#, 0) = "FIELD_NAME^TYPE^...^STORAGE_LOCATION^..."
^DD(file#, field#, 3) = "Help text for this field"
^DD(file#, field#, "DT") = Last modification timestamp
```

**Example - File #2, Field .01 (NAME)**:
```
^DD(2, .01, 0) = "NAME^RFX^^0;1^K:$L(X)>30!($L(X)<3) X"
```

Parse this:
- Field name: `NAME`
- Type: `RFX` (Required, Free text, Cross-referenced)
- Storage: `0;1` → 0-node, piece 1
- Validation: Name must be 3-30 characters

---

## FileMan File Numbering System

Files are numbered with a hierarchical system:

### Main Files
- **1-999**: Core VistA files (e.g., 2 = PATIENT, 200 = NEW PERSON)
- **1000+**: Package-specific files (e.g., 9000011 = PCE visit data)

### Sub-Files (Multi-Valued Fields)
- **Decimal notation**: `file.subfile` (e.g., 2.01 = PATIENT ALIAS)
- **Storage**: Separate subscript under parent record

**Example**:
- File #2 = PATIENT (stored in `^DPT(ien, ...)`)
- File #2.01 = PATIENT ALIAS sub-file (stored in `^DPT(ien, "ALIAS", seq, ...)`)

### Field Numbering
- **.01**: Always the file's primary identifier field (usually NAME)
- **.02-.09**: Other key fields
- **Integers**: Regular fields
- **Decimals**: Sub-fields or special uses

---

## How FileMan Stores Data

### The 0-Node Pattern

**Convention**: The `0` subscript stores the primary data as delimited fields

```
^GLOBAL(IEN, 0) = "piece1^piece2^piece3^..."
```

Each piece corresponds to a field defined in `^DD`.

**Example - Patient Record**:
```
^DPT(123, 0) = "SMITH,JOHN^M^2450101^000-00-0001^..."
                 ↑field.01  ↑.02 ↑.03    ↑.09
```

**Why this pattern?**
- Efficient: One read gets multiple fields
- Standard: All FileMan files follow this
- Parseable: Use `$PIECE()` to extract fields

### Separate Node Storage

Some fields are stored in their own nodes (not in the 0-node):

```
^DPT(123, 0)      ← 0-node with delimited fields
^DPT(123, .111)   ← Street address (separate node)
^DPT(123, .131)   ← Phone number (separate node)
^DPT(123, "ICN")  ← Integration Control Number (separate node)
```

**Why separate nodes?**
- Long text fields (don't bloat 0-node)
- Frequent updates (avoid rewriting entire 0-node)
- Sub-files (need hierarchical structure)

### Looking Up Storage Location

To find where a field is stored, read `^DD`:

```python
# Where is File #2, Field .111 (STREET ADDRESS) stored?
field_def = yottadb.Key("^DD")["2"][".111"][0].value.decode('utf-8')
# Returns: "STREET ADDRESS [LINE 1]^F^^.11;1^..."
#                                            ↑
# Storage location: .11;1 → node .11, piece 1
```

Translation: `^DPT(ien, .11)` contains the address, piece 1

---

## FileMan Data Types

Common field types in `^DD(file#, field#, 0)`:

| Type Code | Meaning | Example |
|-----------|---------|---------|
| `F` | Free Text | Name, address |
| `N` | Numeric | Age, count |
| `D` | Date/Time (FileMan format) | DOB, appointment time |
| `S` | Set of Codes | Sex (M/F), status codes |
| `P` | Pointer to another file | Provider → File #200 |
| `C` | Computed field | Age (computed from DOB) |
| `K` | Mumps code | Custom validation |
| `W` | Word-processing (multi-line) | Progress notes |

### Modifiers
- `R` = Required field
- `X` = Cross-referenced (indexed)

**Example**: `RFX` = Required Free Text with Cross-reference

---

## FileMan Pointers: VistA's Foreign Keys

A **pointer field** references a record in another file.

### Pointer Storage

**Value stored**: The IEN of the referenced record

**Example**: Patient's primary care provider
```
^DPT(123, .104) = "456"
```

This means: Patient 123's provider is the person with IEN 456 in File #200

### Following a Pointer

**In M**:
```m
SET providerIen=$GET(^DPT(patientIen, .104))
IF providerIen'="" DO
. SET providerName=$PIECE($GET(^VA(200, providerIen, 0)), "^", 1)
```

**In Python**:
```python
# Get pointer value
provider_ien = yottadb.Key("^DPT")[patient_ien][".104"].value.decode('utf-8')

# Follow pointer to File #200
if provider_ien:
    provider_zeroth = yottadb.Key("^VA")["200"][provider_ien][0].value
    provider_name = provider_zeroth.decode('utf-8').split("^")[0]
```

### Pointer Field Definition

In `^DD`, pointer fields show the target file:

```
^DD(2, .104, 0) = "PRIMARY CARE PROVIDER^P200'^VA(200,^..."
                                         ↑
                    Points to File #200 (NEW PERSON)
```

---

## Discovering FileMan Structure

### Method 1: List All Files

```python
# Read ^DIC to find all defined files
dic = yottadb.Key("^DIC")

for file_num in dic.subscripts:
    try:
        file_def = dic[file_num][0].value.decode('utf-8')
        file_name = file_def.split("^")[0]

        # Get global location
        gl_node = dic[file_num][0]["GL"].value.decode('utf-8')

        print(f"File #{file_num}: {file_name} → {gl_node}")
    except YDBError:
        pass
```

### Method 2: List Fields in a File

```python
# List all fields in File #2 (PATIENT)
dd = yottadb.Key("^DD")["2"]

for field_num in dd.subscripts:
    try:
        field_def = dd[field_num][0].value.decode('utf-8')
        field_name = field_def.split("^")[0]
        print(f"Field {field_num}: {field_name}")
    except YDBError:
        pass
```

### Method 3: Map a File's 0-Node

```python
def map_zeroth_node(file_num):
    """Map which fields are in the 0-node and their piece positions."""
    dd = yottadb.Key("^DD")[str(file_num)]
    zeroth_fields = {}

    for field_num in dd.subscripts:
        try:
            field_def = dd[field_num][0].value.decode('utf-8')
            parts = field_def.split("^")

            field_name = parts[0]
            # Storage location is typically in part 4 (0-indexed part 3)
            if len(parts) > 3:
                storage = parts[3]
                # Format: "0;piece" means 0-node, specific piece
                if storage.startswith("0;"):
                    piece = storage.split(";")[1]
                    zeroth_fields[field_num] = {
                        "name": field_name,
                        "piece": piece
                    }
        except (YDBError, IndexError):
            pass

    return zeroth_fields

# Example usage
fields = map_zeroth_node(2)  # File #2 PATIENT
for field_num, info in sorted(fields.items()):
    print(f"Field {field_num} ({info['name']}) = 0-node piece {info['piece']}")
```

---

## FileMan APIs (Overview)

VistA M code uses FileMan APIs instead of raw global access:

### Common FileMan API Calls

| API | Purpose | Example |
|-----|---------|---------|
| `^DIC` | Lookup/Search | Find patient by name |
| `^DIE` | Edit existing record | Update patient address |
| `^DIC(0` | Add new record | Register new patient |
| `^DIK` | Delete record | Remove patient (soft delete) |
| `EN^DIQ` | Query/Display | Print patient demographics |

**Why use APIs?**
- Validation (enforce required fields, data types)
- Cross-reference updates (maintain indexes)
- Audit logging
- Business rule enforcement

**From Python**: You can call these M APIs using subprocess or yottadb call mechanism (advanced).

---

## Key FileMan Files to Know

### System Files
- **File #1**: INSTITUTION (facilities)
- **File #4**: LOCATION (hospital locations/clinics)
- **File #200**: NEW PERSON (users/providers)

### Patient Care Files
- **File #2**: PATIENT
- **File #9000010**: VISIT (patient visits)
- **File #9000011**: V EXAM (visit details)

### Clinical Files
- **File #52**: PRESCRIPTION
- **File #100**: ORDERS
- **File #60**: LAB DATA

### Administrative Files
- **File #19**: OPTION (menu options)
- **File #8989.5**: PARAMETER DEFINITION

---

## Exercises

### Exercise 1: Discover All Files Starting with "P"

Write a script to list all FileMan files whose names start with "P":

```python
def find_files_by_prefix(prefix):
    dic = yottadb.Key("^DIC")
    for file_num in dic.subscripts:
        try:
            file_def = dic[file_num][0].value.decode('utf-8')
            file_name = file_def.split("^")[0]
            if file_name.startswith(prefix):
                print(f"File #{file_num}: {file_name}")
        except YDBError:
            pass

find_files_by_prefix("P")
```

### Exercise 2: Map File #200 Structure

Use the `map_zeroth_node()` function above to document File #200's 0-node.

### Exercise 3: Find All Pointer Fields in File #2

List all fields in File #2 that point to other files:

```python
dd = yottadb.Key("^DD")["2"]

for field_num in dd.subscripts:
    try:
        field_def = dd[field_num][0].value.decode('utf-8')
        parts = field_def.split("^")
        field_name = parts[0]
        field_type = parts[1] if len(parts) > 1 else ""

        # Pointer fields have type starting with "P"
        if field_type.startswith("P"):
            # Extract target file number (format: P<file#>)
            target_file = field_type[1:].split("'")[0]
            print(f"Field {field_num} ({field_name}) → File #{target_file}")
    except (YDBError, IndexError):
        pass
```

---

## Key Takeaways

1. **FileMan is VistA's schema layer** on top of raw globals
2. **`^DIC` defines files** and their global storage locations
3. **`^DD` defines fields** and their data types, storage locations
4. **0-node convention** stores primary data as delimited pieces
5. **Pointers are IENs** stored in fields that reference other files
6. **VistA is self-documenting** - all schema is in `^DIC`/`^DD`
7. **Use FileMan APIs** for writes to ensure validation and audit

---

## Next Steps

- Read `04-vista-patient-data.md` to see FileMan in action with File #2
- Read `04b-vista-new-person-file.md` to understand File #200 structure
- Read `05-vista-pointers-relations.md` to learn pointer traversal patterns
- Explore `^DD(2,...)` and `^DD(200,...)` in your VEHU container

---

## References

- FileMan Documentation: https://www.va.gov/vdl/application.asp?appid=5
- FileMan User Manual: Available in VDL
- Your script: `app/02_list_globals.py` lines 67-105 (uses ^DIC to map files to globals)
