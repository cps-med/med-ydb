# VistA Patient Data Structure

**Goal**: Understand how VistA stores and manages patient information in File #2 (PATIENT)

**Prerequisites**:
- Read `01-yottadb-fundamentals.md` (global structure)
- Read `03-m-language-primer.md` (M syntax)

---

## Overview: File #2 (PATIENT)

The **PATIENT file** is VistA's core patient registry. In FileMan terms, it's **File #2**.

### Key Facts
- **Global storage**: `^DPT(` (Demographics, Patient)
- **File number**: 2
- **Primary key**: IEN (Internal Entry Number), also called DFN in patient contexts
- **Purpose**: Store patient demographics, identifiers, and administrative data

### FileMan File Definition Location
```python
# The file definition is in ^DIC:
yottadb.Key("^DIC")[2][0]  # Returns: "PATIENT^2^..."
yottadb.Key("^DIC")[2][0]["GL"]  # Returns: "^DPT("
```

---

## The `^DPT` Global Structure

### Root Level: Patient Records

```
^DPT(IEN)         ← Patient record root
^DPT(IEN,0)       ← Demographics (0-node, primary data)
^DPT(IEN,.01)     ← NAME field
^DPT(IEN,.02)     ← SEX field
^DPT(IEN,.03)     ← DATE OF BIRTH field
^DPT(IEN,.09)     ← SOCIAL SECURITY NUMBER field
^DPT(IEN,"DIS")   ← Discharge sub-file
^DPT(IEN,"ICN")   ← Integration Control Number (national identifier)
... (many more subscripts)
```

### The 0-Node: Most Important Node

The **0-node** (`^DPT(IEN,0)`) contains the primary patient data in a delimited format:

**Format** (simplified - actual has 30+ pieces):
```
^DPT(123,0) = "NAME^SEX^DOB^SSN^..."
```

**Actual example from VEHU**:
```
^DPT(1,0) = "PROVIDER,ONE^M^2450101^000-00-0001^^^^^..."
```

Parsed:
- Piece 1: `PROVIDER,ONE` (name in LAST,FIRST format)
- Piece 2: `M` (sex: M/F)
- Piece 3: `2450101` (DOB in FileMan date format)
- Piece 4: `000-00-0001` (SSN)
- Pieces 5+: Various other demographics

---

## Patient Identifiers in VistA

VistA uses multiple identifiers for patients. Understanding them is critical.

### 1. IEN (Internal Entry Number) / DFN

**What it is**: YottaDB's internal sequential ID for the patient record

**Characteristics**:
- Unique within this VistA instance
- Auto-incremented by FileMan on record creation
- Never changes, never reused (even if patient deleted)
- The subscript in `^DPT(IEN)`

**Example**: `^DPT(123)` → IEN is `123`

**In M code**: Often stored in variable `DFN` (Demographics File Number)

```m
SET DFN=123  ; Set patient context
SET name=$PIECE($GET(^DPT(DFN,0)),"^",1)
```

**In Python**:
```python
ien = 123
patient_key = yottadb.Key("^DPT")[ien]
```

### 2. SSN (Social Security Number)

**What it is**: U.S. Social Security Number (for U.S. patients)

**Storage**: Piece 9 of the 0-node
```
^DPT(123,0) = "...^...^...^...^...^...^...^...^SSN^..."
                                               ↑ piece 9
```

**Usage**:
- Patient lookup
- Identity verification
- Not always present (non-U.S. patients, privacy concerns)

**In M**:
```m
SET ssn=$PIECE($GET(^DPT(dfn,0)),"^",9)
```

### 3. ICN (Integration Control Number)

**What it is**: National patient identifier across all VA facilities

**Storage**: Separate subscript `^DPT(IEN,"ICN")`

**Purpose**: Link patient records across different VistA instances

**Format**: Typically `NNNNNNNVNN` (10 digits with checksum)

**In Python**:
```python
try:
    icn = yottadb.Key("^DPT")[ien]["ICN"].value
except YDBError:
    icn = None  # Not all patients have ICN
```

### 4. Name (Natural Key)

**What it is**: Patient's name in `LAST,FIRST MIDDLE SUFFIX` format

**Storage**: Piece 1 of the 0-node

**Issues**:
- Not unique (multiple John Smiths)
- Can change (marriage, legal name change)
- Not suitable as primary key

**Example**: `SMITH,JOHN Q JR`

### Identifier Comparison Table

| Identifier | Scope | Unique? | Changes? | Purpose |
|------------|-------|---------|----------|---------|
| IEN/DFN | Single VistA instance | Yes | Never | Database primary key |
| SSN | National | Usually* | Rarely | Patient lookup, identity |
| ICN | Nationwide VA | Yes | Never | Cross-facility patient matching |
| Name | N/A | No | Sometimes | Human identification |

*SSN should be unique but data quality issues exist

---

## FileMan Date Format

VistA uses **FileMan date format**, not Unix timestamps or ISO dates.

### Format: `YYYMMDD` (sometimes with `.HHMMSS` time)

**Examples**:
- `2450101` = January 1, 1945
- `3240715` = July 15, 2024
- `3240715.143000` = July 15, 2024 at 2:30:00 PM

**Why weird?**:
- Base year is 1700
- Year 2000 is `300` (3000000 + MMDD)
- Year 2024 is `324` (3240000 + MMDD)

### Converting FileMan Dates

**M built-in**: `$$FMTE^XLFDT(fmDate)` converts to human format

**Python conversion** (simplified):
```python
def fileman_to_python_date(fm_date):
    """Convert FileMan date (YYYMMDD) to Python date.

    Args:
        fm_date: FileMan date string (e.g., "3240715")

    Returns:
        datetime.date object
    """
    from datetime import date

    # Extract components
    fm_str = str(fm_date).split(".")[0]  # Remove time component
    if len(fm_str) < 7:
        return None

    yyy = int(fm_str[:3])  # First 3 digits = year code
    mm = int(fm_str[3:5])  # Next 2 = month
    dd = int(fm_str[5:7])  # Last 2 = day

    # Convert FileMan year to actual year
    # Years 000-099 = 1700-1799
    # Years 100-199 = 1800-1899
    # Years 200-299 = 1900-1999
    # Years 300-399 = 2000-2099
    if yyy < 100:
        year = 1700 + yyy
    elif yyy < 200:
        year = 1800 + (yyy - 100)
    elif yyy < 300:
        year = 1900 + (yyy - 200)
    else:  # 300-399
        year = 2000 + (yyy - 300)

    return date(year, mm, dd)

# Example usage
dob_fm = "2450101"
dob_py = fileman_to_python_date(dob_fm)
print(dob_py)  # 1945-01-01
```

---

## Exploring Patient Data Hands-On

### Step 1: Find Patients in Your VEHU

```bash
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 /opt/med-ydb/app/03_explore_allowlisted.py --global ^DPT --max-nodes 10'
```

**Expected output** (example):
```
^DPT(1): <no value>
^DPT(2): <no value>
^DPT(10): <no value>
...
```

Most patient root nodes have no value - data is in subscripts.

### Step 2: Examine a Patient's 0-Node

```bash
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 /opt/med-ydb/app/03_explore_allowlisted.py --global ^DPT --subscript 1 --subscript 0 --max-nodes 1'
```

**Expected output** (example):
```
^DPT(1,0): PROVIDER,ONE^M^2450101^000-00-0001^...
```

### Step 3: Parse the 0-Node Programmatically

Create a test script `app/04_patient_parser.py`:

```python
#!/usr/bin/env python3
"""Parse patient demographics from ^DPT 0-node."""

import sys
import yottadb
from yottadb import YDBError


def parse_patient_zeroth(ien):
    """Parse patient 0-node into structured data.

    Args:
        ien: Patient IEN (Internal Entry Number)

    Returns:
        dict with patient data, or None if patient doesn't exist
    """
    try:
        zeroth = yottadb.Key("^DPT")[str(ien)][0].value
    except YDBError:
        return None

    # Decode and split on ^
    data = zeroth.decode("utf-8", errors="replace")
    pieces = data.split("^")

    # Extract key fields (piece positions from FileMan DD)
    # Note: List indices are 0-based, piece numbers are 1-based
    return {
        "ien": ien,
        "name": pieces[0] if len(pieces) > 0 else "",
        "sex": pieces[1] if len(pieces) > 1 else "",
        "dob_fm": pieces[2] if len(pieces) > 2 else "",
        "ssn": pieces[8] if len(pieces) > 8 else "",  # Piece 9 = index 8
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 04_patient_parser.py <patient_ien>")
        return 1

    ien = sys.argv[1]
    patient = parse_patient_zeroth(ien)

    if patient is None:
        print(f"Patient {ien} not found or has no 0-node")
        return 1

    print("=" * 60)
    print("Patient Demographics")
    print("=" * 60)
    print(f"IEN/DFN:  {patient['ien']}")
    print(f"Name:     {patient['name']}")
    print(f"Sex:      {patient['sex']}")
    print(f"DOB (FM): {patient['dob_fm']}")
    print(f"SSN:      {patient['ssn']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Run it:
```bash
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 /opt/med-ydb/app/04_patient_parser.py 1'
```

---

## Field Definitions in `^DD`

To know which piece is which field, look in the **data dictionary** (`^DD`).

### Structure: `^DD(file#, field#, ...)`

For File #2, field definitions are in `^DD(2, ...)`.

**Example**: What is field .01?

```bash
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 -c "
import yottadb
# Field .01 definition
field_def = yottadb.Key(\"^DD\")[\"2\"][\".01\"][0].value
print(field_def.decode(\"utf-8\"))
"'
```

**Expected output** (simplified):
```
NAME^RFX^^0;1^...
```

Parse this:
- Field name: `NAME`
- Type: `RFX` (required, free text, cross-referenced)
- Storage: `0;1` → node 0, piece 1

**Translation**: "Field .01 is NAME, stored in 0-node piece 1."

### Common Patient File Fields

| Field # | Name | 0-Node Piece | Type |
|---------|------|--------------|------|
| .01 | NAME | 1 | Text |
| .02 | SEX | 2 | Set of codes (M/F) |
| .03 | DATE OF BIRTH | 3 | Date |
| .09 | SOCIAL SECURITY NUMBER | 9 | Numeric |
| .111 | STREET ADDRESS [LINE 1] | Separate node | Text |
| .131 | PHONE NUMBER [RESIDENCE] | Separate node | Text |

(Many more fields exist - over 100 in File #2)

---

## Sub-Files: Multi-Valued Fields

Some patient data can have multiple values (e.g., multiple phone numbers, addresses).

### Example: Patient Aliases (File #2.01)

**Storage**: `^DPT(IEN,"ALIAS",seq#,0)`

```
^DPT(123,"ALIAS",1,0) = "SMITH,JOHN"
^DPT(123,"ALIAS",2,0) = "SMITH,J"
```

**Access pattern**:
```python
patient = yottadb.Key("^DPT")[123]
alias_subscript = patient["ALIAS"]

for seq in alias_subscript.subscripts:
    try:
        alias = alias_subscript[seq][0].value
        print(f"Alias: {alias.decode('utf-8')}")
    except YDBError:
        pass
```

### Common Sub-Files

| Sub-File # | Name | Storage Subscript |
|------------|------|-------------------|
| 2.01 | ALIAS | `^DPT(IEN,"ALIAS",seq)` |
| 2.101 | PATIENT ELIGIBILITIES | `^DPT(IEN,"E",seq)` |
| 2.312 | ADMISSIONS | `^DPT(IEN,"DIS",seq)` |

---

## Pointers: Linking to Other Files

VistA doesn't have foreign keys. It uses **pointers** - field values that reference other files.

### Example: Primary Care Provider (Pointer to File #200)

**Field**: .1041 (PRIMARY CARE PROVIDER)
**Points to**: File #200 (NEW PERSON)

**Storage**: Separate node, value is IEN of provider in `^VA(200,`

```
^DPT(123,.104) = "456"  ; Pointer to provider IEN 456
```

To get provider name:
```python
# Get provider IEN from patient record
patient_ien = 123
provider_ien = yottadb.Key("^DPT")[patient_ien][".104"].value.decode("utf-8")

# Follow pointer to File #200
provider_name_piece = yottadb.Key("^VA")["200"][provider_ien][0].value.decode("utf-8")
provider_name = provider_name_piece.split("^")[0]

print(f"Patient {patient_ien}'s provider: {provider_name}")
```

**This is VistA's "join" pattern** - manual pointer traversal.

---

## Practical Exercises

### Exercise 1: List All Patients with Demographics

Write a script to:
1. Iterate through `^DPT`
2. Parse each patient's 0-node
3. Print IEN, name, sex, DOB in a table

**Expected output**:
```
IEN    Name              Sex  DOB (FM)
-----  ----------------  ---  --------
1      PROVIDER,ONE      M    2450101
2      PROVIDER,TWO      F    2500615
10     PATIENT,DEMO      M    2800101
...
```

### Exercise 2: Find Patients by Sex

Modify Exercise 1 to accept a `--sex` argument and filter results:

```bash
python3 list_patients.py --sex M  # Only male patients
```

### Exercise 3: Trace Provider Pointer

For a given patient IEN:
1. Read their primary care provider field (.104 or similar)
2. Follow the pointer to File #200
3. Print the provider's name and title

### Exercise 4: Calculate Patient Age

For each patient:
1. Parse DOB from 0-node (FileMan format)
2. Convert to Python date
3. Calculate age as of today
4. Print patients sorted by age (oldest first)

---

## Security and Privacy Notes

### HIPAA Considerations

Even in a learning environment:
- **Don't export real patient data** to files or logs
- **Keep SSNs masked** when displaying (show last 4 only)
- **Understand audit logging** (VistA logs all patient data access)

### Real vs. Test Data in VEHU

VEHU contains **synthetic test data** for demo/learning purposes. But:
- Treat it as if it were real for practice
- Develop privacy-safe habits now
- Understand that production VistA has audit requirements

---

## Key Takeaways

1. **File #2 = ^DPT** - core patient demographics
2. **IEN/DFN is the primary key** - use it for all patient references
3. **0-node contains most demographics** - delimited by `^`
4. **Field positions documented in ^DD** - look up piece numbers there
5. **FileMan dates are YYYMMDD** - convert to Python dates for display
6. **Pointers are manual references** - traverse them explicitly
7. **Sub-files handle multi-valued data** - explore subscripts like "ALIAS"

---

## Next Steps

- Read `05-vista-pointers-relations.md` to understand VistA's relational model
- Complete exercises above to practice patient data parsing
- Explore File #200 (NEW PERSON) to understand provider data
- Study `^DD(2,...)` to map all fields in the PATIENT file

---

## References

- FileMan File #2 (PATIENT): https://www.va.gov/vdl/application.asp?appid=5
- VistA Data Dictionary: Accessible via `^DD(2,...)` in YottaDB
- Your script: `app/03_explore_allowlisted.py` (use to explore ^DPT structure)
