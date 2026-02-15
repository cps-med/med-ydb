# Exercise 1: Explore File #2 (PATIENT) and File #200 (NEW PERSON)

**Goal**: Hands-on exploration of VistA's core patient and provider files

**Time**: 45-60 minutes

**Prerequisites**:
- VEHU container running
- Read `04-vista-patient-data.md`
- Read `04b-vista-new-person-file.md`
- `^VA` added to allowlist in `03_explore_allowlisted.py`

---

## Part 1: Explore File Structure (15 min)

### Task 1.1: Find the Global Locations

Use `^DIC` to look up where these files are stored:

```bash
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 -c "
import yottadb

# File #2 (PATIENT)
dic2 = yottadb.Key(\"^DIC\")[\"2\"][0]
print(\"File #2:\", dic2.value.decode(\"utf-8\"))
print(\"Global:\", dic2[\"GL\"].value.decode(\"utf-8\"))
print()

# File #200 (NEW PERSON)
dic200 = yottadb.Key(\"^DIC\")[\"200\"][0]
print(\"File #200:\", dic200.value.decode(\"utf-8\"))
print(\"Global:\", dic200[\"GL\"].value.decode(\"utf-8\"))
"'
```

**Expected output**:
```
File #2: PATIENT^2^...
Global: ^DPT(

File #200: NEW PERSON^200^...
Global: ^VA(200,
```

**Question**: Why is File #200 stored under `^VA(200,` instead of `^NEW(` or similar?

<details>
<summary>Answer</summary>
`^VA` is a multi-purpose global for various VA-specific files. File #200 is one of many files stored under the `^VA` global root, organized by file number subscript.
</details>

### Task 1.2: Count Records

How many patients and how many users exist in your VEHU?

```python
#!/usr/bin/env python3
import yottadb

def count_records(global_root, file_subscript=None):
    """Count records in a global."""
    count = 0
    if file_subscript:
        key = yottadb.Key(global_root)[file_subscript]
    else:
        key = yottadb.Key(global_root)

    for _ in key.subscripts:
        count += 1
    return count

# Count patients
patient_count = count_records("^DPT")
print(f"Patients in File #2: {patient_count}")

# Count users
user_count = count_records("^VA", "200")
print(f"Users in File #200: {user_count}")
```

**Record your results**:
- Patients: _______
- Users: _______

---

## Part 2: Parse the 0-Nodes (20 min)

### Task 2.1: Map File #2 (PATIENT) 0-Node

Examine a patient's 0-node and document the pieces:

```bash
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 -c "
import yottadb

# Get first patient
patients = yottadb.Key(\"^DPT\")
patient_ien = next(iter(patients.subscripts))

# Read 0-node
zeroth = patients[patient_ien][0].value.decode(\"utf-8\")
print(f\"Patient IEN: {patient_ien}\")
print(f\"0-node: {zeroth}\")
print()

# Parse pieces
pieces = zeroth.split(\"^\")
for i, piece in enumerate(pieces[:10], 1):  # First 10 pieces
    print(f\"Piece {i}: {piece}\")
"'
```

**Fill in this table** (use `^DD(2, ...)` to look up field names):

| Piece | Field # | Field Name | Example Value |
|-------|---------|------------|---------------|
| 1 | .01 | NAME | |
| 2 | .02 | SEX | |
| 3 | .03 | DATE OF BIRTH | |
| 9 | .09 | SSN | |

### Task 2.2: Map File #200 (NEW PERSON) 0-Node

Do the same for a user record:

```bash
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 -c "
import yottadb

# Get first user
users = yottadb.Key(\"^VA\")[\"200\"]
user_ien = next(iter(users.subscripts))

# Read 0-node
zeroth = users[user_ien][0].value.decode(\"utf-8\")
print(f\"User IEN: {user_ien}\")
print(f\"0-node: {zeroth}\")
print()

# Parse pieces
pieces = zeroth.split(\"^\")
for i, piece in enumerate(pieces[:10], 1):  # First 10 pieces
    print(f\"Piece {i}: {piece}\")
"'
```

**Fill in this table**:

| Piece | Field # | Field Name | Example Value |
|-------|---------|------------|---------------|
| 1 | .01 | NAME | |
| 2 | .02 | ACCESS CODE | |
| 7 | .07 | INITIAL | |

---

## Part 3: Follow Pointer Relationships (20 min)

### Task 3.1: Patient → Provider Lookup

Find a patient's primary care provider:

Create `app/ex01_patient_provider.py`:

```python
#!/usr/bin/env python3
"""Exercise: Patient → Provider pointer traversal."""

import sys
import yottadb
from yottadb import YDBError


def get_patient_info(patient_ien):
    """Get patient name and demographics."""
    try:
        zeroth = yottadb.Key("^DPT")[patient_ien][0].value
        parts = zeroth.decode('utf-8').split("^")
        return {
            "name": parts[0] if len(parts) > 0 else "",
            "sex": parts[1] if len(parts) > 1 else "",
            "dob": parts[2] if len(parts) > 2 else "",
        }
    except YDBError:
        return None


def get_provider_info(provider_ien):
    """Get provider name and details."""
    try:
        zeroth = yottadb.Key("^VA")["200"][provider_ien][0].value
        parts = zeroth.decode('utf-8').split("^")
        return {
            "name": parts[0] if len(parts) > 0 else "",
            "access_code": parts[1] if len(parts) > 1 else "",
        }
    except YDBError:
        return None


def find_patient_provider(patient_ien):
    """Find patient's primary care provider (if assigned)."""
    try:
        # Field .104 = PRIMARY CARE PROVIDER (pointer to File #200)
        provider_ien = yottadb.Key("^DPT")[patient_ien][".104"].value
        provider_ien = provider_ien.decode('utf-8').strip()
        return provider_ien if provider_ien else None
    except YDBError:
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 ex01_patient_provider.py <patient_ien>")
        return 1

    patient_ien = sys.argv[1]

    # Get patient info
    patient = get_patient_info(patient_ien)
    if not patient:
        print(f"Patient {patient_ien} not found")
        return 1

    print("=" * 60)
    print("Patient → Provider Lookup")
    print("=" * 60)
    print(f"Patient IEN:  {patient_ien}")
    print(f"Patient Name: {patient['name']}")
    print(f"Sex:          {patient['sex']}")
    print(f"DOB (FM):     {patient['dob']}")
    print()

    # Follow pointer to provider
    provider_ien = find_patient_provider(patient_ien)

    if provider_ien:
        provider = get_provider_info(provider_ien)
        if provider:
            print(f"Primary Care Provider:")
            print(f"  IEN:         {provider_ien}")
            print(f"  Name:        {provider['name']}")
            print(f"  Access Code: {provider['access_code']}")
        else:
            print(f"Provider {provider_ien} not found (dangling pointer!)")
    else:
        print("No primary care provider assigned")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Run it**:
```bash
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
  python3 /opt/med-ydb/app/ex01_patient_provider.py 1'
```

**Questions**:
1. Does patient IEN 1 have a provider assigned?
2. If yes, what is the provider's IEN?
3. What is the provider's name?

### Task 3.2: Reverse Lookup - Provider → Patients

Find all patients for a given provider:

Add to `app/ex01_patient_provider.py`:

```python
def find_provider_patients(provider_ien):
    """Find all patients assigned to this provider.

    Warning: This is a brute-force scan (slow for large datasets).
    """
    patient_list = []
    patients = yottadb.Key("^DPT")

    for patient_ien in patients.subscripts:
        try:
            pcp_ien = yottadb.Key("^DPT")[patient_ien][".104"].value
            pcp_ien = pcp_ien.decode('utf-8').strip()

            if pcp_ien == provider_ien:
                patient = get_patient_info(patient_ien)
                if patient:
                    patient_list.append({
                        "ien": patient_ien,
                        "name": patient["name"]
                    })
        except YDBError:
            pass

    return patient_list


# Add to main():
# After showing patient → provider, ask user if they want reverse lookup
print("\n" + "=" * 60)
response = input("Find all patients for this provider? (y/n): ")

if response.lower() == 'y' and provider_ien:
    print(f"\nFinding patients for provider {provider_ien}...")
    patients = find_provider_patients(provider_ien)

    if patients:
        print(f"\nFound {len(patients)} patient(s):")
        for p in patients:
            print(f"  - {p['name']} (IEN {p['ien']})")
    else:
        print("No patients found for this provider")
```

**Question**: If your VEHU has 50+ patients, how long does the reverse lookup take? Why?

<details>
<summary>Answer</summary>
The reverse lookup must scan all patients (O(n) complexity) because pointers only go one direction. VistA uses cross-references (indexes) to make this faster in production, but we're doing a manual scan here.
</details>

---

## Part 4: Data Quality Audit (10 min)

### Task 4.1: Find Patients Without Providers

```python
def audit_missing_providers():
    """Find patients with no primary care provider assigned."""
    missing = []
    patients = yottadb.Key("^DPT")

    for patient_ien in patients.subscripts:
        try:
            pcp_ien = yottadb.Key("^DPT")[patient_ien][".104"].value
            if not pcp_ien.decode('utf-8').strip():
                # Empty provider field
                patient = get_patient_info(patient_ien)
                if patient:
                    missing.append((patient_ien, patient['name']))
        except YDBError:
            # No .104 field = no provider
            patient = get_patient_info(patient_ien)
            if patient:
                missing.append((patient_ien, patient['name']))

    return missing


# Usage
missing = audit_missing_providers()
print(f"\nPatients without PCP: {len(missing)}")
for ien, name in missing[:10]:  # Show first 10
    print(f"  - {name} (IEN {ien})")
```

**Record**: How many patients have no provider assigned? _______

### Task 4.2: Find Dangling Pointers

```python
def audit_dangling_pointers():
    """Find patients pointing to non-existent providers."""
    dangling = []
    patients = yottadb.Key("^DPT")

    for patient_ien in patients.subscripts:
        try:
            pcp_ien = yottadb.Key("^DPT")[patient_ien][".104"].value
            pcp_ien = pcp_ien.decode('utf-8').strip()

            if pcp_ien:
                # Check if provider exists
                try:
                    _ = yottadb.Key("^VA")["200"][pcp_ien][0].value
                except YDBError:
                    # Provider doesn't exist!
                    patient = get_patient_info(patient_ien)
                    if patient:
                        dangling.append((patient_ien, patient['name'], pcp_ien))
        except YDBError:
            pass

    return dangling


# Usage
dangling = audit_dangling_pointers()
if dangling:
    print(f"\nDangling pointers found: {len(dangling)}")
    for patient_ien, patient_name, bad_provider_ien in dangling:
        print(f"  - {patient_name} → Provider {bad_provider_ien} (missing)")
else:
    print("\nNo dangling pointers found (good!)")
```

**Record**: Any dangling pointers? _______

---

## Bonus Challenges

### Challenge 1: Provider Workload Report

Create a report showing each provider and their patient count, sorted by workload:

```
Provider Workload Report
========================
PROVIDER,ONE (IEN 59)          : 25 patients
PROVIDER,TWO (IEN 60)          : 18 patients
SMITH,JANE MD (IEN 123)        : 12 patients
...
```

### Challenge 2: Patient Demographics Export

Export patient demographics to CSV format:

```csv
IEN,Name,Sex,DOB,Provider IEN,Provider Name
1,PATIENT,ONE,M,2450101,59,PROVIDER,ONE
2,PATIENT,TWO,F,2500615,60,PROVIDER,TWO
```

### Challenge 3: Person Classes

For each provider, list their person classes (e.g., PHYSICIAN, NURSE PRACTITIONER):

```python
def get_person_classes(provider_ien):
    """Get provider's person classes."""
    classes = []
    try:
        ps_key = yottadb.Key("^VA")["200"][provider_ien]["PS"]
        for seq in ps_key.subscripts:
            try:
                ps_zeroth = ps_key[seq][0].value.decode('utf-8')
                class_name = ps_zeroth.split("^")[0]
                classes.append(class_name)
            except YDBError:
                pass
    except YDBError:
        pass
    return classes
```

---

## Reflection Questions

After completing this exercise, answer these:

1. **Data Model**: How does VistA's pointer-based model differ from SQL foreign keys?

2. **Performance**: What are the trade-offs of VistA's one-directional pointers vs. SQL's bidirectional joins?

3. **Data Quality**: What mechanisms does VistA use to prevent dangling pointers? (Hint: FileMan APIs)

4. **Real-World**: In a production VistA with 100,000+ patients, how would you optimize the "provider → patients" reverse lookup?

---

## What You Learned

- ✅ How to read FileMan file definitions from `^DIC`
- ✅ How to parse 0-nodes from File #2 and File #200
- ✅ How to follow pointer fields (patient → provider)
- ✅ How to perform reverse lookups (provider → patients)
- ✅ How to audit data quality (missing/dangling pointers)
- ✅ The structure and purpose of File #2 and File #200

---

## Next Steps

- Try Exercise 2: Trace multi-level pointer chains
- Explore other VistA files (orders, pharmacy, lab)
- Read `05-vista-pointers-relations.md` for advanced pointer patterns
