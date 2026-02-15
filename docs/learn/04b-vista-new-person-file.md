# VistA NEW PERSON File (File #200)

**Goal**: Understand how VistA stores user/provider information in File #200

**Prerequisites**:
- Read `01-yottadb-fundamentals.md` (global structure)
- Read `02-fileman-architecture.md` (FileMan basics)
- Read `04-vista-patient-data.md` (helps with comparison)

---

## Overview: File #200 (NEW PERSON)

The **NEW PERSON file** is VistA's registry of all system users: providers, clinicians, nurses, administrative staff, and other personnel.

### Key Facts
- **Global storage**: `^VA(200,`
- **File number**: 200
- **Primary key**: IEN (Internal Entry Number)
- **Purpose**: User authentication, provider identification, access control, clinical staff registry

### Critical Distinction
**File #2 (PATIENT)** = People receiving care
**File #200 (NEW PERSON)** = People providing care / using the system

### FileMan File Definition Location
```python
# The file definition is in ^DIC:
yottadb.Key("^DIC")["200"][0]  # Returns: "NEW PERSON^200^..."
yottadb.Key("^DIC")["200"][0]["GL"]  # Returns: "^VA(200,"
```

---

## The `^VA(200,` Global Structure

### Root Level: User/Provider Records

```
^VA(200, IEN)           ← User record root
^VA(200, IEN, 0)        ← Primary data (0-node)
^VA(200, IEN, .1)       ← Alternate identifiers
^VA(200, IEN, 1)        ← User characteristics
^VA(200, IEN, 2)        ← Access code (encrypted)
^VA(200, IEN, "PS")     ← Person class (provider types)
^VA(200, IEN, "SRV")    ← Service/Section assignment
... (many more subscripts)
```

### The 0-Node: Primary User Data

The **0-node** (`^VA(200, IEN, 0)`) contains core user information:

**Format** (simplified - actual has many pieces):
```
^VA(200, IEN, 0) = "NAME^ACCESS_CODE^VERIFY_CODE^..."
```

**Actual example from VEHU**:
```
^VA(200, 1, 0) = "PROGRAMMER,ONE^PRO^1234^1^^^PRO1234^..."
```

Parsed:
- Piece 1: `PROGRAMMER,ONE` (name in LAST,FIRST format)
- Piece 2: `PRO` (access code - for login)
- Piece 3: `1234` (verify code - encrypted)
- Piece 7: `PRO1234` (initial/user code - often used as username)

---

## User Identifiers in File #200

### 1. IEN (Internal Entry Number)

**What it is**: YottaDB's internal sequential ID for the user record

**Characteristics**:
- Unique within this VistA instance
- Auto-incremented by FileMan
- The subscript in `^VA(200, IEN, ...)`
- Used in pointer fields from other files

**Example**: `^VA(200, 59, ...)` → IEN is `59`

**Usage**: When File #2 (PATIENT) has a provider field, it stores this IEN

### 2. Name (Piece 1 of 0-Node)

**Format**: `LAST,FIRST MIDDLE SUFFIX`

**Examples**:
- `SMITH,JOHN Q`
- `DOE,JANE`
- `PROGRAMMER,ONE`

**Issues**:
- Not unique (two providers could have same name)
- Can change (marriage, legal name change)
- Used for display, not as unique key

### 3. Access Code (Piece 2 of 0-Node)

**What it is**: First part of login credentials (like a username)

**Characteristics**:
- Typically 3-8 characters
- Used for authentication
- Should be unique across users
- Examples: `PRO`, `DOC`, `NURSE123`

### 4. Verify Code (Piece 3 of 0-Node)

**What it is**: Password (encrypted in database)

**Characteristics**:
- Encrypted using VistA's encryption
- User enters during login
- Changed periodically per policy

### 5. Initial/User Code (Piece 7 of 0-Node)

**What it is**: Human-readable user identifier (like modern username)

**Characteristics**:
- Often combination of name + number
- Examples: `PRO1234`, `JSMITH`, `DOE456`
- More stable than Access Code
- Used in audit logs, signatures

### Identifier Comparison Table

| Identifier | Piece | Unique? | Purpose |
|------------|-------|---------|---------|
| IEN | (subscript) | Yes | Database primary key, pointers |
| Name | 1 | No | Display, human identification |
| Access Code | 2 | Yes* | Login username |
| Verify Code | 3 | N/A | Login password (encrypted) |
| Initial Code | 7 | Usually | Audit trails, signatures |

*Should be unique but enforced by business rules, not database

---

## Person Classes: Provider Types

VistA tracks **what kind of provider** each person is using Person Classes.

### Storage: `^VA(200, IEN, "PS", seq, 0)`

**Example**:
```
^VA(200, 59, "PS", 1, 0) = "PHYSICIAN^S.PHYSICIAN^1^3000101^^1"
^VA(200, 59, "PS", 2, 0) = "NURSE PRACTITIONER^S.NURSE PRACTITIONER^1^..."
```

A single person can have multiple person classes (e.g., both Physician and Researcher).

### Common Person Classes
- **Physician** (various specialties)
- **Nurse Practitioner**
- **Physician Assistant**
- **Registered Nurse**
- **Pharmacist**
- **Social Worker**
- **Administrative Staff**

### Why Person Classes Matter

**Clinical significance**:
- Determines what orders they can sign
- Controls prescription authority
- Defines clinical privileges

**From Patient File**: When you see a provider IEN in File #2, you can look up their person class to understand their role.

---

## Service/Section Assignment

**Storage**: `^VA(200, IEN, 5)` or related nodes

**Purpose**: Which department/service this person works in

**Examples**:
- Cardiology
- Emergency Medicine
- Radiology
- Pharmacy

**Usage**: Routing, workload reporting, access control

---

## Access Control: Keys and Options

VistA uses **security keys** and **menu options** to control what users can do.

### Security Keys

**Storage**: `^VA(200, IEN, 51, key_name, 0)`

**Purpose**: Grant specific privileges

**Examples**:
- `PROVIDER` - Can sign orders
- `XUPROG` - Programmer access
- `ORES` - Order entry/results
- `XUMGR` - User manager

**Checking if user has a key**:
```python
def has_key(user_ien, key_name):
    try:
        key_node = yottadb.Key("^VA")["200"][user_ien]["51"][key_name][0].value
        return True
    except YDBError:
        return False

# Example
if has_key("59", "PROVIDER"):
    print("User 59 is a provider")
```

### Menu Options

**Storage**: `^VA(200, IEN, 203, option_ien, 0)`

**Purpose**: Which menus/features the user can access

**Examples**:
- `GMPL PROBLEM LIST` - Problem list management
- `OR CPRS GUI CHART` - CPRS (Computerized Patient Record System)
- `PSO LM BACKDOOR ORDERS` - Pharmacy backdoor orders

---

## Electronic Signature

**Storage**: `^VA(200, IEN, 20)` and related nodes

**Purpose**: Digital signing of clinical documents, orders

**Contains**:
- Signature block text
- Electronic signature code (like a PIN)

**Usage**: When a provider signs an order or note, VistA verifies:
1. The user has appropriate privileges (keys/person classes)
2. The electronic signature matches

---

## Common Use Cases for File #200

### Use Case 1: Patient's Primary Care Provider

**Patient File #2** has a pointer to **File #200**:

```python
# Get patient's primary care provider
patient_ien = "123"
try:
    provider_ien = yottadb.Key("^DPT")[patient_ien][".104"].value.decode('utf-8')

    # Look up provider details
    provider_zeroth = yottadb.Key("^VA")["200"][provider_ien][0].value
    provider_name = provider_zeroth.decode('utf-8').split("^")[0]

    print(f"Patient {patient_ien}'s PCP: {provider_name}")
except YDBError:
    print("No primary care provider assigned")
```

### Use Case 2: Who Entered an Order?

Orders track who placed them:

```python
# Hypothetical: orders file would have provider IEN
order_ien = "456"
# ordering_provider_ien = ... (from order record)

# Look up who placed the order
provider_name = get_provider_name(ordering_provider_ien)
print(f"Order placed by: {provider_name}")
```

### Use Case 3: Authentication

When a user logs into VistA:

1. User enters Access Code + Verify Code
2. VistA searches `^VA(200,` for matching Access Code (piece 2)
3. Verifies the Verify Code (piece 3, encrypted comparison)
4. Sets user context to that IEN
5. Loads their keys, options, person classes

---

## Exploring File #200 Data

### Step 1: List Users in Your VEHU

```bash
# First, add ^VA to your allowlist
# Edit app/03_explore_allowlisted.py:
# ALLOWED_GLOBALS = {
#     "^DIC",
#     "^DPT",
#     "^VA",  # Add this
# }

docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 /opt/med-ydb/app/03_explore_allowlisted.py --global "^VA(200" --max-nodes 10'
```

Note the special syntax: `"^VA(200"` to access the specific file number under `^VA`.

### Step 2: Examine a User's 0-Node

```bash
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 -c "
import yottadb
key = yottadb.Key(\"^VA\")[\"200\"][\"1\"][0]
zeroth = key.value.decode(\"utf-8\")
print(\"User IEN 1 (0-node):\", zeroth)
"'
```

### Step 3: Parse User Demographics

Create `app/05_user_parser.py`:

```python
#!/usr/bin/env python3
"""Parse user/provider data from ^VA(200) 0-node."""

import sys
import yottadb
from yottadb import YDBError


def parse_user_zeroth(ien):
    """Parse user 0-node into structured data.

    Args:
        ien: User IEN (Internal Entry Number)

    Returns:
        dict with user data, or None if user doesn't exist
    """
    try:
        zeroth = yottadb.Key("^VA")["200"][str(ien)][0].value
    except YDBError:
        return None

    # Decode and split on ^
    data = zeroth.decode("utf-8", errors="replace")
    pieces = data.split("^")

    # Extract key fields (piece positions from FileMan DD)
    return {
        "ien": ien,
        "name": pieces[0] if len(pieces) > 0 else "",
        "access_code": pieces[1] if len(pieces) > 1 else "",
        # Piece 2 (verify code) - skip, it's encrypted
        "title": pieces[8] if len(pieces) > 8 else "",  # Piece 9
        "initial_code": pieces[6] if len(pieces) > 6 else "",  # Piece 7
    }


def get_person_classes(ien):
    """Get all person classes for a user.

    Args:
        ien: User IEN

    Returns:
        list of person class names
    """
    classes = []
    try:
        ps_key = yottadb.Key("^VA")["200"][str(ien)]["PS"]
        for seq in ps_key.subscripts:
            try:
                ps_zeroth = ps_key[seq][0].value.decode("utf-8")
                class_name = ps_zeroth.split("^")[0]
                classes.append(class_name)
            except YDBError:
                pass
    except YDBError:
        pass

    return classes


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 05_user_parser.py <user_ien>")
        return 1

    ien = sys.argv[1]
    user = parse_user_zeroth(ien)

    if user is None:
        print(f"User {ien} not found or has no 0-node")
        return 1

    print("=" * 60)
    print("User/Provider Information")
    print("=" * 60)
    print(f"IEN:          {user['ien']}")
    print(f"Name:         {user['name']}")
    print(f"Access Code:  {user['access_code']}")
    print(f"Initial Code: {user['initial_code']}")
    print(f"Title:        {user['title']}")

    # Get person classes
    classes = get_person_classes(ien)
    if classes:
        print(f"\nPerson Classes:")
        for cls in classes:
            print(f"  - {cls}")
    else:
        print("\nPerson Classes: (none)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Run it:
```bash
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 /opt/med-ydb/app/05_user_parser.py 1'
```

---

## File #200 vs File #2 Comparison

| Aspect | File #2 (PATIENT) | File #200 (NEW PERSON) |
|--------|-------------------|------------------------|
| **Global** | `^DPT(` | `^VA(200,` |
| **Purpose** | People receiving care | People providing care |
| **Primary ID** | DFN (patient IEN) | User IEN |
| **Name Field** | .01 (piece 1) | .01 (piece 1) |
| **Key Identifiers** | SSN, ICN | Access Code, Initial Code |
| **Demographics** | DOB, sex, address | Title, service/section |
| **Clinical Data** | Diagnoses, visits, orders | Person classes, privileges |
| **Relationships** | → Providers (pointers to #200) | ← Patients (pointed to by #2) |

---

## Common Fields in File #200

Based on `^DD(200, ...)`:

| Field # | Name | 0-Node Piece | Description |
|---------|------|--------------|-------------|
| .01 | NAME | 1 | User's full name (LAST,FIRST) |
| .02 | ACCESS CODE | 2 | Login username |
| .03 | VERIFY CODE | 3 | Password (encrypted) |
| .07 | INITIAL | 7 | User initials/code |
| .09 | TITLE | 9 | Professional title |
| .111 | STREET ADDRESS | Separate node | Home address |
| .131 | OFFICE PHONE | Separate node | Contact number |
| .151 | EMAIL ADDRESS | Separate node | Email |
| 2 | ACCESS CODE | (duplicate of .02) | |
| 8 | DATE ENTERED | Separate node | When user created |
| 9 | CREATOR | Separate node | Who created this user |
| 28 | PROVIDER CLASS | Sub-file | Person Classes |
| 51 | KEYS | Sub-file | Security keys |
| 203 | SECONDARY MENU OPTIONS | Sub-file | Menu access |

---

## Practical Exercises

### Exercise 1: List All Providers

Write a script to list all users in File #200 with their names:

```python
def list_all_users():
    users = yottadb.Key("^VA")["200"]

    for ien in users.subscripts:
        try:
            zeroth = users[ien][0].value.decode('utf-8')
            name = zeroth.split("^")[0]
            print(f"IEN {ien}: {name}")
        except YDBError:
            pass

list_all_users()
```

### Exercise 2: Find Users with "PROVIDER" Key

List all users who have the "PROVIDER" security key:

```python
def find_providers():
    users = yottadb.Key("^VA")["200"]

    for ien in users.subscripts:
        try:
            # Check if PROVIDER key exists
            _ = users[ien]["51"]["PROVIDER"][0].value
            # If we get here, key exists
            name = users[ien][0].value.decode('utf-8').split("^")[0]
            print(f"Provider: {name} (IEN {ien})")
        except YDBError:
            # No PROVIDER key for this user
            pass

find_providers()
```

### Exercise 3: Map Patient to Provider

For each patient in File #2, show their primary care provider:

```python
def map_patients_to_providers():
    patients = yottadb.Key("^DPT")

    for patient_ien in patients.subscripts:
        try:
            # Get patient name
            patient_zeroth = patients[patient_ien][0].value.decode('utf-8')
            patient_name = patient_zeroth.split("^")[0]

            # Get provider IEN
            provider_ien = patients[patient_ien][".104"].value.decode('utf-8')

            if provider_ien:
                # Get provider name
                provider_zeroth = yottadb.Key("^VA")["200"][provider_ien][0].value
                provider_name = provider_zeroth.decode('utf-8').split("^")[0]
            else:
                provider_name = "(none assigned)"

            print(f"{patient_name} → {provider_name}")

        except YDBError:
            pass

map_patients_to_providers()
```

---

## Security and Privacy Notes

### Authentication Data

**Never log or expose**:
- Access Codes (piece 2) in production
- Verify Codes (piece 3) - always encrypted
- Electronic signature codes

**Even in test environments**: Treat authentication data carefully to develop good habits.

### User Audit Trails

In production VistA:
- All user actions are logged
- Logs include user IEN, timestamp, action
- Required for HIPAA compliance

---

## Key Takeaways

1. **File #200 = Users/Providers** (people using VistA, not patients)
2. **Stored in `^VA(200,`** - distinct from patient global `^DPT`
3. **IEN is the primary key** - used in pointers from patient records
4. **Person Classes define provider types** - Physician, NP, RN, etc.
5. **Security keys control access** - Check keys to understand privileges
6. **Access Code + Verify Code = login** - authentication credentials
7. **Patient → Provider relationship** - File #2 points to File #200

---

## Next Steps

- Read `05-vista-pointers-relations.md` to understand how File #2 and File #200 connect
- Complete Exercise 3 above to see patient-provider relationships
- Explore `^DD(200,...)` to discover all fields in File #200
- Compare File #200 structure to File #2 to understand VistA patterns

---

## References

- FileMan File #200 (NEW PERSON): https://www.va.gov/vdl/application.asp?appid=5
- VistA Security documentation
- Your script: `app/03_explore_allowlisted.py` (add `^VA` to allowlist to explore)
