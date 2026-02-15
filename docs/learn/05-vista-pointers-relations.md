# VistA Pointers and Relationships

**Goal**: Understand how VistA implements relationships between files using pointers

**Prerequisites**:
- Read `02-fileman-architecture.md` (FileMan basics)
- Read `04-vista-patient-data.md` (File #2)
- Read `04b-vista-new-person-file.md` (File #200)

---

## Overview: VistA's Relational Model

VistA doesn't use SQL foreign keys. Instead, it uses **pointers** - field values that contain the IEN of a record in another file.

### Pointer = Manual Foreign Key

**SQL equivalent**:
```sql
-- SQL foreign key
CREATE TABLE patients (
    id INT PRIMARY KEY,
    provider_id INT REFERENCES providers(id)
);
```

**VistA equivalent**:
```
File #2, Field .104 = Pointer to File #200
^DPT(patient_ien, .104) = provider_ien
```

**Key difference**: VistA doesn't enforce referential integrity at the database level. It's enforced by application code (FileMan APIs).

---

## How Pointers Work

### Pointer Field Definition

In `^DD`, pointer fields are marked with type `P`:

```
^DD(2, .104, 0) = "PRIMARY CARE PROVIDER^P200'^VA(200,^..."
                                         ↑         ↑
                                    Points to    Target
                                    File #200    global
```

**Parse this**:
- Field name: `PRIMARY CARE PROVIDER`
- Type: `P200'` → Pointer to File #200
- Target global: `^VA(200,`

### Pointer Storage

**What's stored**: The IEN (Internal Entry Number) of the referenced record

**Example**:
```
^DPT(123, .104) = "59"
```

**Translation**: Patient with IEN 123 has primary care provider with IEN 59 in File #200

### Following a Pointer (One-to-One)

**Step 1**: Read the pointer value from source file
```python
patient_ien = "123"
provider_ien = yottadb.Key("^DPT")[patient_ien][".104"].value.decode('utf-8')
```

**Step 2**: Use that IEN to access the target file
```python
if provider_ien:
    provider_zeroth = yottadb.Key("^VA")["200"][provider_ien][0].value
    provider_name = provider_zeroth.decode('utf-8').split("^")[0]
    print(f"Provider: {provider_name}")
```

**Complete function**:
```python
def get_patient_provider(patient_ien):
    """Get patient's primary care provider name.

    Args:
        patient_ien: Patient IEN

    Returns:
        Provider name string, or None if no provider
    """
    try:
        # Step 1: Get pointer value
        provider_ien = yottadb.Key("^DPT")[patient_ien][".104"].value
        provider_ien = provider_ien.decode('utf-8').strip()

        if not provider_ien:
            return None

        # Step 2: Follow pointer
        provider_zeroth = yottadb.Key("^VA")["200"][provider_ien][0].value
        provider_name = provider_zeroth.decode('utf-8').split("^")[0]

        return provider_name

    except YDBError:
        return None
```

---

## Common Pointer Patterns

### Pattern 1: One-to-One Relationship

**Example**: Patient → Primary Care Provider

```
File #2 (PATIENT) → File #200 (NEW PERSON)

^DPT(123, .104) = "59"  ; One patient → One provider
```

**Use case**: Each patient has exactly one primary care provider (or none)

### Pattern 2: One-to-Many via Sub-File

**Example**: Patient → Multiple Admissions

```
File #2 (PATIENT) → File #2.312 (ADMISSIONS sub-file)

^DPT(123, "DIS", 1, 0) = "admission data..."
^DPT(123, "DIS", 2, 0) = "admission data..."
^DPT(123, "DIS", 3, 0) = "admission data..."
```

Each admission might have pointers to:
- Attending physician (→ File #200)
- Ward location (→ File #4)
- Diagnosis (→ File #80)

**Accessing**:
```python
patient = yottadb.Key("^DPT")["123"]
admissions = patient["DIS"]

for admission_seq in admissions.subscripts:
    admission_data = admissions[admission_seq][0].value.decode('utf-8')
    print(f"Admission #{admission_seq}: {admission_data}")
```

### Pattern 3: Many-to-Many (Implicit)

**Example**: Patients ← Orders → Providers

```
File #100 (ORDERS)
- Has pointer to patient (File #2)
- Has pointer to ordering provider (File #200)

^OR(100, order_ien, 0) contains:
- Patient IEN (piece X)
- Provider IEN (piece Y)
```

This creates a many-to-many relationship:
- One patient can have many orders
- One provider can write many orders
- Many patients, many providers, connected through orders

**To find**: "All orders for patient 123"
- Iterate through orders file
- Filter where patient pointer = 123

**To find**: "All patients for provider 59"
- Iterate through orders file
- Filter where provider pointer = 59
- Collect unique patient IENs

---

## Patient-Provider Relationships in Detail

### File #2 (PATIENT) Pointers to File #200 (NEW PERSON)

Common pointer fields in File #2:

| Field # | Field Name | Points To | Purpose |
|---------|------------|-----------|---------|
| .104 | PRIMARY CARE PROVIDER | File #200 | PCP assignment |
| .1041 | PRIMARY CARE TEAM | File #404.51 | Care team |
| Multiple in admissions | ATTENDING PHYSICIAN | File #200 | Doctor during admission |
| Multiple in orders | ENTERED BY | File #200 | Who placed the order |

### Example: Complete Patient-Provider Map

```python
def map_patient_providers(patient_ien):
    """Map all provider relationships for a patient.

    Args:
        patient_ien: Patient IEN

    Returns:
        dict with different provider types
    """
    providers = {}

    try:
        # Primary care provider
        pcp_ien = yottadb.Key("^DPT")[patient_ien][".104"].value.decode('utf-8')
        if pcp_ien:
            pcp_name = get_provider_name(pcp_ien)
            providers["primary_care"] = {"ien": pcp_ien, "name": pcp_name}
    except YDBError:
        pass

    # Could add: attending physicians from admissions, etc.

    return providers


def get_provider_name(provider_ien):
    """Helper: Get provider name by IEN."""
    try:
        zeroth = yottadb.Key("^VA")["200"][provider_ien][0].value
        return zeroth.decode('utf-8').split("^")[0]
    except YDBError:
        return "(unknown)"


# Usage
patient_ien = "123"
providers = map_patient_providers(patient_ien)

print(f"Patient {patient_ien} providers:")
for role, info in providers.items():
    print(f"  {role}: {info['name']} (IEN {info['ien']})")
```

---

## Reverse Lookups: Finding All Patients for a Provider

**Problem**: Given a provider IEN, find all their patients

**Challenge**: Pointers only go one direction (patient → provider). There's no automatic reverse index.

### Solution 1: Iterate All Patients (Brute Force)

```python
def find_patients_by_provider(provider_ien):
    """Find all patients with a given primary care provider.

    Args:
        provider_ien: Provider IEN (string)

    Returns:
        list of patient IENs
    """
    patient_list = []
    patients = yottadb.Key("^DPT")

    for patient_ien in patients.subscripts:
        try:
            pcp_ien = patients[patient_ien][".104"].value.decode('utf-8')
            if pcp_ien == provider_ien:
                patient_list.append(patient_ien)
        except YDBError:
            pass

    return patient_list


# Usage
provider_ien = "59"
patients = find_patients_by_provider(provider_ien)
print(f"Provider {provider_ien} has {len(patients)} patients")
```

**Performance**: Slow for large databases (must scan all patients)

### Solution 2: Cross-References (VistA's Indexes)

FileMan maintains **cross-references** (indexes) automatically.

**Example**: The "B" cross-reference indexes by name

```
^DPT("B", name, ien) = ""
```

**For pointers**, VistA can maintain reverse cross-references:

```
^DPT("APC", provider_ien, patient_ien) = ""
```

This index allows fast lookup of all patients for a provider.

**Accessing cross-reference**:
```python
def find_patients_by_provider_fast(provider_ien):
    """Find patients using cross-reference (if it exists).

    Args:
        provider_ien: Provider IEN

    Returns:
        list of patient IENs
    """
    patient_list = []

    try:
        # "APC" is hypothetical - check your VistA for actual cross-ref name
        apc_index = yottadb.Key("^DPT")["APC"][provider_ien]

        for patient_ien in apc_index.subscripts:
            patient_list.append(patient_ien)

    except YDBError:
        # Cross-reference might not exist
        pass

    return patient_list
```

**How to find cross-references**: Look in `^DD(file#, field#, 1, ...)`

---

## Pointer Chains: Multi-Level Relationships

**Example**: Patient → Provider → Service/Section

```python
def get_patient_provider_service(patient_ien):
    """Trace patient → provider → service.

    Args:
        patient_ien: Patient IEN

    Returns:
        dict with provider and service info
    """
    result = {}

    try:
        # Step 1: Patient → Provider
        provider_ien = yottadb.Key("^DPT")[patient_ien][".104"].value.decode('utf-8')
        if not provider_ien:
            return result

        provider_zeroth = yottadb.Key("^VA")["200"][provider_ien][0].value
        provider_name = provider_zeroth.decode('utf-8').split("^")[0]

        result["provider_ien"] = provider_ien
        result["provider_name"] = provider_name

        # Step 2: Provider → Service (hypothetical field)
        # service_ien = yottadb.Key("^VA")["200"][provider_ien]["5"].value.decode('utf-8')
        # (Would continue following pointer chain)

    except YDBError:
        pass

    return result
```

**Use cases**:
- Patient → Order → Medication → Pharmacy
- Patient → Visit → Clinic → Ward → Building
- Patient → Problem → ICD Code → Code System

---

## Null Pointers and Dangling References

### Null Pointer (Empty Field)

**Definition**: Pointer field has no value

```python
try:
    provider_ien = yottadb.Key("^DPT")["123"][".104"].value
except YDBError:
    # Field doesn't exist = null pointer
    provider_ien = None
```

**Meaning**: Patient has no assigned provider

### Dangling Reference (Data Integrity Issue)

**Definition**: Pointer points to a deleted record

```
^DPT(123, .104) = "999"  ; Points to provider IEN 999
^VA(200, 999, ...)  ; Doesn't exist (deleted)
```

**Detection**:
```python
def validate_pointer(patient_ien, pointer_field, target_global, target_file):
    """Check if pointer is valid (target exists).

    Returns:
        tuple (is_valid, pointer_value)
    """
    try:
        pointer_value = yottadb.Key("^DPT")[patient_ien][pointer_field].value
        pointer_value = pointer_value.decode('utf-8').strip()

        if not pointer_value:
            return (False, None)  # Null pointer

        # Check if target exists
        target_key = yottadb.Key(target_global)[target_file][pointer_value][0]
        _ = target_key.value  # Try to read

        return (True, pointer_value)  # Valid pointer

    except YDBError:
        return (False, pointer_value)  # Dangling reference


# Usage
is_valid, provider_ien = validate_pointer("123", ".104", "^VA", "200")
if not is_valid:
    print(f"Invalid pointer: patient 123 → provider {provider_ien}")
```

**VistA prevention**: FileMan APIs check referential integrity when deleting records

---

## Practical Exercises

### Exercise 1: Patient-Provider Report

Generate a report showing patient names and their providers:

```python
def patient_provider_report():
    """Generate patient → provider report."""
    print(f"{'Patient Name':<30} {'Provider Name':<30}")
    print("=" * 60)

    patients = yottadb.Key("^DPT")

    for patient_ien in patients.subscripts:
        try:
            # Get patient name
            patient_zeroth = patients[patient_ien][0].value.decode('utf-8')
            patient_name = patient_zeroth.split("^")[0]

            # Get provider
            try:
                provider_ien = patients[patient_ien][".104"].value.decode('utf-8')
                provider_zeroth = yottadb.Key("^VA")["200"][provider_ien][0].value
                provider_name = provider_zeroth.decode('utf-8').split("^")[0]
            except YDBError:
                provider_name = "(none)"

            print(f"{patient_name:<30} {provider_name:<30}")

        except YDBError:
            pass


patient_provider_report()
```

### Exercise 2: Provider Workload

Count how many patients each provider has:

```python
def provider_workload():
    """Count patients per provider."""
    from collections import defaultdict

    workload = defaultdict(int)
    provider_names = {}

    # Iterate all patients
    patients = yottadb.Key("^DPT")

    for patient_ien in patients.subscripts:
        try:
            provider_ien = patients[patient_ien][".104"].value.decode('utf-8')
            if provider_ien:
                workload[provider_ien] += 1

                # Cache provider name
                if provider_ien not in provider_names:
                    zeroth = yottadb.Key("^VA")["200"][provider_ien][0].value
                    provider_names[provider_ien] = zeroth.decode('utf-8').split("^")[0]
        except YDBError:
            pass

    # Print sorted by patient count
    print(f"{'Provider':<30} {'Patient Count':<15}")
    print("=" * 45)

    for provider_ien, count in sorted(workload.items(), key=lambda x: x[1], reverse=True):
        name = provider_names.get(provider_ien, "(unknown)")
        print(f"{name:<30} {count:<15}")


provider_workload()
```

### Exercise 3: Validate All Pointers

Check for dangling references in patient-provider pointers:

```python
def audit_patient_provider_pointers():
    """Find dangling provider pointers."""
    errors = []
    patients = yottadb.Key("^DPT")

    for patient_ien in patients.subscripts:
        try:
            provider_ien = patients[patient_ien][".104"].value.decode('utf-8')

            if provider_ien:
                # Try to access provider record
                try:
                    _ = yottadb.Key("^VA")["200"][provider_ien][0].value
                except YDBError:
                    # Dangling reference!
                    errors.append({
                        "patient_ien": patient_ien,
                        "provider_ien": provider_ien,
                        "error": "Provider record not found"
                    })
        except YDBError:
            pass

    # Report
    if errors:
        print(f"Found {len(errors)} dangling references:")
        for err in errors:
            print(f"  Patient {err['patient_ien']} → Provider {err['provider_ien']} (missing)")
    else:
        print("No dangling references found")


audit_patient_provider_pointers()
```

---

## Comparing to SQL

### SQL Foreign Key
```sql
CREATE TABLE patients (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    provider_id INT REFERENCES providers(id) ON DELETE SET NULL
);

-- Query: patients with their providers
SELECT p.name, prov.name
FROM patients p
LEFT JOIN providers prov ON p.provider_id = prov.id;
```

### VistA Pointer Equivalent

**Definition** (in `^DD`):
```
^DD(2, .104, 0) = "PRIMARY CARE PROVIDER^P200'^VA(200,^..."
```

**Query** (Python):
```python
for patient_ien in yottadb.Key("^DPT").subscripts:
    patient_zeroth = yottadb.Key("^DPT")[patient_ien][0].value
    patient_name = patient_zeroth.decode('utf-8').split("^")[0]

    try:
        provider_ien = yottadb.Key("^DPT")[patient_ien][".104"].value.decode('utf-8')
        provider_zeroth = yottadb.Key("^VA")["200"][provider_ien][0].value
        provider_name = provider_zeroth.decode('utf-8').split("^")[0]
    except YDBError:
        provider_name = None  # LEFT JOIN equivalent

    print(f"{patient_name} | {provider_name}")
```

**Key differences**:
1. **No declarative JOIN** - manual pointer traversal
2. **No cascading deletes** - application enforces rules
3. **No database-level referential integrity** - FileMan APIs handle it
4. **Cross-references for performance** - manually defined indexes

---

## VistA Relationship Patterns Summary

### One-to-One
- Patient → Primary Care Provider
- User → Primary Menu Option
- **Implementation**: Single pointer field

### One-to-Many
- Patient → Multiple Admissions
- Provider → Multiple Patients
- **Implementation**: Sub-file or reverse cross-reference

### Many-to-Many
- Patients ←→ Providers (via Orders)
- Providers ←→ Clinics (via assignments)
- **Implementation**: Junction file (e.g., Orders) with pointers to both

---

## Key Takeaways

1. **Pointers = IENs stored in fields** - not automatic foreign keys
2. **Follow pointers manually** - read IEN, then read target record
3. **One direction only** - patient → provider (not automatic reverse)
4. **Cross-references enable reverse lookups** - VistA's indexes
5. **No database-level integrity** - FileMan APIs enforce rules
6. **Pointer chains are common** - patient → provider → service → building
7. **Always validate** - check for null and dangling pointers

---

## Next Steps

- Practice Exercise 1-3 above with your VEHU data
- Explore other pointer fields in File #2 (admissions, allergies, etc.)
- Read `^DD(2, ..., 1, ...)` to discover cross-references
- Map out the relationship diagram for major VistA files

---

## References

- FileMan Pointer documentation: VA FileMan Developer Guide
- Your scripts: `app/03_explore_allowlisted.py` (explore both File #2 and #200)
- VistA Data Dictionary: `^DD(2, ...)` and `^DD(200, ...)`
