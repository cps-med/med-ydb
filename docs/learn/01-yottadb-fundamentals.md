# YottaDB Fundamentals

**Goal**: Understand YottaDB's hierarchical database model and how it differs from relational databases

**Prerequisite**: Have VEHU container running with `app/01_env_check.py` working

---

## What is YottaDB?

YottaDB is a **hierarchical key-value database** optimized for high-performance transactional workloads. It evolved from GT.M, which evolved from MUMPS (M) database systems used in healthcare since the 1970s.

### Key Characteristics
- **In-process**: The database engine runs in the same process as your application (not client/server)
- **Persistent globals**: Data persists across restarts in hierarchical tree structures
- **Multi-versioned concurrency**: Optimistic locking allows high read/write concurrency
- **Transaction support**: ACID compliance with `TSTART`/`TCOMMIT`

---

## The Global: YottaDB's Core Data Structure

A **global** is a persistent hierarchical variable. Think of it like a filesystem:
- A global is like a directory
- Subscripts are like subdirectories and files
- Values are the file contents
- You can have both directories AND files at the same path

### Global Naming Convention
- Global names start with `^`
- Examples: `^DPT`, `^DIC`, `^VA(200)`, `^ZZTEST`
- The `^` distinguishes globals (persistent) from local variables (ephemeral)

### Hierarchical Structure Example

```
^DPT                          ← Root node (can have a value here)
^DPT(1)                       ← First patient record
^DPT(1,0)                     ← Patient header/demographics
^DPT(1,.01)                   ← Patient name field
^DPT(1,.02)                   ← Patient sex field
^DPT(1,.03)                   ← Patient date of birth
^DPT(1,"DIS",1)               ← First discharge record
^DPT(1,"DIS",1,0)             ← Discharge details
^DPT(2)                       ← Second patient record
^DPT(2,0)
...
```

This is fundamentally different from SQL's flat tables. **Each node can have both a value AND children**.

---

## The Key Object in Python

The `yottadb.Key` object is your handle to navigate and manipulate globals.

### Creating a Key

```python
import yottadb

# Reference the root of a global
patient_file = yottadb.Key("^DPT")

# Reference a specific subscript
patient_1 = yottadb.Key("^DPT")[1]

# Reference a nested subscript
patient_1_name = yottadb.Key("^DPT")[1][".01"]

# Alternative: build incrementally
key = yottadb.Key("^DPT")
key = key[1]
key = key[".01"]
```

### Reading Values

```python
key = yottadb.Key("^DPT")[1][0]

try:
    value = key.value  # Returns bytes or raises YDBError if no value
    print(value.decode("utf-8"))
except YDBError:
    print("No value at this node")
```

**Important**: Not all nodes have values. A node might exist only as a parent to children.

### Writing Values

```python
# Set a value (bytes object)
key = yottadb.Key("^ZZTEST")
key.value = b"Hello from Python"

# UTF-8 encoding for strings
key.value = "Hello world".encode("utf-8")

# Set nested values
key["subscript1"]["subscript2"].value = b"Nested value"
```

### Iterating Children

```python
# Loop through all immediate children
parent = yottadb.Key("^DPT")

for subscript in parent.subscripts:
    child_key = parent[subscript]
    print(f"Subscript: {subscript}")

    try:
        print(f"Value: {child_key.value.decode('utf-8')}")
    except YDBError:
        print("(no value at this node)")
```

**What `subscripts` does**: Returns an iterator of the immediate child subscripts at this level. Equivalent to M's `$ORDER()` function.

---

## Intrinsic Special Variables (ISVs)

ISVs are system-provided variables that start with `$`. They provide runtime information.

### Common ISVs

| ISV | Purpose | Example in Python |
|-----|---------|-------------------|
| `$ZYRELEASE` | YottaDB version string | `yottadb.get("$ZYRELEASE")` |
| `$ZVERSION` | Full version info | `yottadb.get("$ZVERSION")` |
| `$JOB` | Current process ID | `yottadb.get("$JOB")` |
| `$STORAGE` | Available memory | `yottadb.get("$STORAGE")` |
| `$HOROLOG` | Current date/time (M format) | `yottadb.get("$HOROLOG")` |

### Example from `01_env_check.py`

```python
# Line 58
release = yottadb.get("$ZYRELEASE")
print(f"YottaDB release: {release.decode('utf-8')}")
```

ISVs are read-only and don't persist (they're computed at runtime).

---

## Node vs. Tree: A Critical Distinction

This is where YottaDB differs from Python dicts or SQL tables.

### Node
A single point in the hierarchy that may have:
- A value (data stored at this exact location)
- No value (but could still have children)

### Tree
A node and all its descendants (children, grandchildren, etc.)

### Visual Example

```
^DPT(1)           ← Node (might have a value)
├── ^DPT(1,0)     ← Child node (has a value: patient demographics)
├── ^DPT(1,.01)   ← Child node (has a value: patient name)
└── ^DPT(1,"DIS") ← Child node (no value itself)
    └── ^DPT(1,"DIS",1)    ← Grandchild (has a value: discharge record)
    └── ^DPT(1,"DIS",1,0)  ← Great-grandchild
```

The **tree** rooted at `^DPT(1)` includes ALL nodes shown above.

### Deleting: Node vs. Tree

```python
key = yottadb.Key("^DPT")[1]

# Delete only the value at this node, keep children
key.delete_node()  # ^DPT(1) value gone, but ^DPT(1,0) still exists

# Delete this node AND all descendants (entire subtree)
key.delete_tree()  # ^DPT(1) and ALL children gone
```

**Be very careful with `delete_tree()`** - it's recursive and permanent.

---

## Traversal Patterns

YottaDB uses `$ORDER()` to traverse subscripts in sorted order (collation order).

### Python Equivalent: `subscripts` Iterator

```python
# Traverse all patients
patients = yottadb.Key("^DPT")

for patient_id in patients.subscripts:
    patient = patients[patient_id]

    # Get patient demographics from 0-node
    try:
        demographics = patient[0].value
        print(f"Patient {patient_id}: {demographics.decode('utf-8')}")
    except YDBError:
        print(f"Patient {patient_id}: (no 0-node)")
```

### Bounded Traversal (Safety Pattern)

```python
# Don't iterate forever - use a limit
MAX_NODES = 20
count = 0

for patient_id in patients.subscripts:
    print(f"Patient ID: {patient_id}")
    count += 1
    if count >= MAX_NODES:
        print(f"... stopped at {MAX_NODES} nodes")
        break
```

This pattern is used in `03_explore_allowlisted.py` to prevent runaway exploration.

---

## Collation Order (Sorting)

YottaDB sorts subscripts using a specific collation order:
1. Numeric strings (sorted numerically): `"1"`, `"2"`, `"10"`, `"100"`
2. Empty string: `""`
3. String literals (sorted lexically): `"A"`, `"B"`, `"Z"`, `"a"`, `"b"`

### Example

```python
# If global has subscripts: 10, 2, "ABC", 100, "AAA", 1
# $ORDER() traversal returns: 1, 2, 10, 100, "AAA", "ABC"

for sub in key.subscripts:
    print(sub)  # Prints in collation order, not insertion order
```

**Key insight**: Numeric IDs sort numerically, not lexically. `"10"` comes after `"2"`.

---

## Subscript Data Types

Subscripts can be:
- **Strings**: `^DPT("NAME")`
- **Numeric strings**: `^DPT(123)` (stored as string `"123"` but sorts numerically)
- **Mixed**: `^DPT(1, "DIS", 5, 0)`

**In Python**: Subscripts are passed as strings or objects that convert to strings.

```python
# These are equivalent
key1 = yottadb.Key("^DPT")["123"]
key2 = yottadb.Key("^DPT")[123]  # Converted to "123"

# But for clarity, prefer explicit string conversion
key3 = yottadb.Key("^DPT")[str(patient_id)]
```

### ⚠️ IMPORTANT: Always Use String Subscripts

**Best Practice**: Always use **string subscripts**, especially when working with subscripts returned from `.subscripts` iterator.

**Common Gotcha**:
```python
# ❌ WRONG - Using integer subscript
key = yottadb.Key("^XWB")["8994"]
zeroth_node = key[0].value  # ERROR: 'subsarray' argument invalid

# ✅ CORRECT - Using string subscript
zeroth_node = key["0"].value  # Works correctly
```

**When working with subscripts from iteration**:
```python
# ❌ WRONG - Decoding subscript before reuse
for file_num in dic.subscripts:
    file_num_str = file_num.decode('utf-8')  # Convert to string
    value = dic[file_num_str]["0"].value     # ERROR with nested subscripts!

# ✅ CORRECT - Keep subscript in original format
for file_num in dic.subscripts:
    value = dic[file_num]["0"].value         # Works correctly
    # Only decode for display:
    print(f"File #{file_num.decode('utf-8')}")
```

**Key Rules**:
1. **Subscripts from `.subscripts`** → Use directly, decode only for display
2. **Numeric subscripts** → Use strings: `["0"]`, `["1"]`, `["2"]`
3. **When in doubt** → Use explicit strings: `[str(value)]`

---

## Sparse Arrays: Why Globals are Efficient

YottaDB globals are **sparse** - you only store what exists.

```python
# In SQL, you might have gaps in IDs due to deletions:
# patients table: ID 1, 2, 5, 7, 100 (IDs 3, 4, 6, 8-99 deleted)

# In YottaDB:
^DPT(1)    ← exists
^DPT(2)    ← exists
^DPT(5)    ← exists
^DPT(7)    ← exists
^DPT(100)  ← exists
# IDs 3, 4, 6, 8-99 simply don't exist (no storage used)

# Traversal using $ORDER() automatically skips gaps:
for patient_id in yottadb.Key("^DPT").subscripts:
    # Iterates: 1, 2, 5, 7, 100 (skips missing IDs)
```

This is more efficient than SQL with large gaps.

---

## Comparing to SQL/NoSQL

### vs. SQL Tables

| SQL | YottaDB |
|-----|---------|
| Table with rows/columns | Global with hierarchical subscripts |
| Schema required | Schema-less (store any structure) |
| Foreign keys enforced | Pointers by convention (not enforced) |
| Query language (SQL) | Programmatic traversal |
| Indexes separate | Subscripts ARE the index |

### vs. Document Databases (MongoDB)

| MongoDB | YottaDB |
|---------|---------|
| Collections of JSON docs | Globals with nested subscripts |
| Documents = unstructured | Structure by convention (FileMan) |
| Query language | Programmatic traversal |
| Atomic document updates | Atomic node updates |

### vs. Key-Value Stores (Redis)

| Redis | YottaDB |
|-------|---------|
| Flat key-value | Hierarchical key-value |
| Hash/List/Set types | Just hierarchical nodes |
| In-memory (optional persistence) | Persistent (in-process access) |
| No nested structures | Unlimited nesting |

**YottaDB's uniqueness**: Hierarchical, sparse, sorted, persistent, with ACID transactions.

---

## Hands-On Exercises

### Exercise 1: Explore ISVs

```bash
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && python3 -c "
import yottadb
print(\"ZYRELEASE:\", yottadb.get(\"\$ZYRELEASE\"))
print(\"JOB:\", yottadb.get(\"\$JOB\"))
print(\"HOROLOG:\", yottadb.get(\"\$HOROLOG\"))
"'
```

What does `$HOROLOG` format mean? (Hint: it's days since a base date, then seconds since midnight)

### Exercise 2: Count Nodes in a Global

Modify `03_explore_allowlisted.py` to add a `--count` flag that counts total children without printing them.

```python
def count_children(key):
    count = 0
    for _ in key.subscripts:
        count += 1
    return count
```

How many patients are in `^DPT`?

### Exercise 3: Find the Largest Subscript

Write a function to find the numerically largest patient ID:

```python
def find_max_subscript(key):
    max_sub = None
    for sub in key.subscripts:
        # $ORDER() returns in sorted order, so last one is largest
        max_sub = sub
    return max_sub

# Usage
patients = yottadb.Key("^DPT")
max_patient_id = find_max_subscript(patients)
print(f"Highest patient IEN: {max_patient_id}")
```

Why does this work? (Hint: collation order)

---

## Common Errors and Solutions

### `YDBError: -150373850, %YDB-E-GVUNDEF`
**Meaning**: Global or node does not have a value

**Solution**: Check if node exists before reading, or use try/except

```python
try:
    value = key.value
except YDBError as e:
    if "GVUNDEF" in str(e):
        value = None  # Node has no value
    else:
        raise  # Different error, re-raise
```

### `YDBError: -150373914, %YDB-E-INVVARNAME`
**Meaning**: Invalid variable name (common with `^$GLOBAL`)

**Solution**: Use fallback methods (see `02_list_globals.py`)

### `UnicodeDecodeError`
**Meaning**: Trying to decode bytes that aren't UTF-8

**Solution**: Use raw mode or handle decode errors

```python
try:
    text = value.decode("utf-8")
except UnicodeDecodeError:
    text = repr(value)  # Show raw bytes
```

### `TypeError: 'subsarray' argument invalid: item N is not a bytes-like object`
**Meaning**: Using wrong subscript type (integer instead of string, or decoded subscript)

**Solution**: Always use string subscripts, keep `.subscripts` results in original format

```python
# ❌ WRONG - These cause the error
key[0]                              # Integer subscript
key[file_num.decode('utf-8')]       # Decoded subscript

# ✅ CORRECT - Use these patterns
key["0"]                            # String subscript
key[file_num]                       # Keep subscript from .subscripts as-is

# Example from iteration
for file_num in dic.subscripts:
    # Use subscript directly
    value = dic[file_num]["0"].value

    # Only decode for display
    print(f"File: {file_num.decode('utf-8')}")
```

**See also**: `exercise/ex_02_explore_files.py` for working pattern

---

## Key Takeaways

1. **Globals are hierarchical trees**, not flat key-value pairs
2. **Nodes can have values AND children** - this is different from most databases
3. **Subscripts are always sorted** in collation order (numeric then string)
4. **Subscripts must be strings** - use `["0"]` not `[0]`, keep `.subscripts` results in original format
5. **Sparse structure** - only existing nodes consume space
6. **In-process access** - YottaDB runs in your Python process, not as a separate server
7. **Use `subscripts` iterator** for traversal (equivalent to M's `$ORDER()`)
8. **Always bound your traversals** to prevent exploring massive globals

---

## Next Steps

- Read `03-m-language-primer.md` to understand M's `$ORDER()`, `$GET()`, `$DATA()` functions
- Read `02-fileman-architecture.md` to see how VistA structures data on top of globals
- Complete Exercise 2 and Exercise 3 above
- Experiment with creating your own test global (`^ZZTEST`) to practice writes

---

## References

- YottaDB Programmer's Guide: https://docs.yottadb.com/ProgrammersGuide/
- YottaDB Python Wrapper: https://gitlab.com/YottaDB/Lang/YDBPython
- Your script: `app/01_env_check.py` (demonstrates Key patterns)
