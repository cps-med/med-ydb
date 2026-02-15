# M to Python Patterns - Quick Reference

**Purpose**: Side-by-side comparison for translating M code to Python

**Usage**: Keep this open while reading VistA M routines

---

## Variables and Assignment

| M | Python |
|---|--------|
| `SET name="John"` | `name = "John"` |
| `SET age=42` | `age = 42` |
| `SET x=5,y=10,z=15` | `x, y, z = 5, 10, 15` |
| `NEW temp` | (automatic - local scope) |
| `KILL temp` | `del temp` |

---

## String Operations

| M | Python |
|---|--------|
| `SET full=first_" "_last` | `full = first + " " + last` |
| `$LENGTH(str)` | `len(str)` |
| `$EXTRACT(str,1,5)` | `str[0:5]` *(M is 1-indexed!)* |
| `$FIND(str,"abc")` | `str.find("abc") + 1` *(M returns position after match)* |
| `$TRANSLATE(str,"a","A")` | `str.replace("a", "A")` |
| `$JUSTIFY(num,5)` | `str(num).rjust(5)` |

---

## String Parsing (Critical for VistA)

### `$PIECE()` - Split on Delimiter

**M**:
```m
SET record="Smith,John^M^2450101"
SET name=$PIECE(record,"^",1)    ; "Smith,John"
SET sex=$PIECE(record,"^",2)     ; "M"
SET dob=$PIECE(record,"^",3)     ; "2450101"
```

**Python**:
```python
record = "Smith,John^M^2450101"
parts = record.split("^")
name = parts[0]  # "Smith,John"  (0-indexed!)
sex = parts[1]   # "M"
dob = parts[2]   # "2450101"
```

**Or safer**:
```python
def piece(string, delimiter, position):
    """M $PIECE equivalent (1-indexed)."""
    parts = string.split(delimiter)
    if 0 < position <= len(parts):
        return parts[position - 1]  # Convert to 0-indexed
    return ""

name = piece(record, "^", 1)  # Now 1-indexed like M
```

---

## Global Access

| M | Python |
|---|--------|
| `SET x=^DPT(123,0)` | `x = yottadb.Key("^DPT")[123][0].value` |
| `SET ^DPT(123,0)="data"` | `yottadb.Key("^DPT")[123][0].value = b"data"` |
| `SET name=$PIECE(^DPT(dfn,0),"^",1)` | `name = yottadb.Key("^DPT")[dfn][0].value.decode().split("^")[0]` |

---

## Safe Reading with Defaults

### `$GET()` - Read with Default

**M**:
```m
SET value=$GET(^DPT(123,0),"")
SET name=$GET(^DPT(123,.01),"UNKNOWN")
```

**Python**:
```python
try:
    value = yottadb.Key("^DPT")[123][0].value
except YDBError:
    value = b""

# Or as a helper function:
def get_node(key, default=b""):
    try:
        return key.value
    except YDBError:
        return default

value = get_node(yottadb.Key("^DPT")[123][0], b"")
```

---

## Checking Node Existence

### `$DATA()` - Check if Node Exists

**M**:
```m
SET exists=$DATA(^DPT(123))
IF exists DO something
```

**M return values**:
- `0` = doesn't exist
- `1` = has value, no descendants
- `10` = no value, has descendants
- `11` = has value and descendants

**Python**:
```python
def data(key):
    """Approximate $DATA() behavior."""
    has_value = False
    has_children = False

    try:
        _ = key.value
        has_value = True
    except YDBError:
        pass

    try:
        next(iter(key.subscripts))
        has_children = True
    except StopIteration:
        pass

    if not has_value and not has_children:
        return 0
    elif has_value and not has_children:
        return 1
    elif has_children and not has_value:
        return 10
    else:
        return 11

exists = data(yottadb.Key("^DPT")[123])
if exists:
    # Node exists in some form
    pass
```

---

## Iteration / Traversal

### `$ORDER()` - Get Next Subscript

**M Pattern**:
```m
SET patientId=""
FOR  SET patientId=$ORDER(^DPT(patientId)) QUIT:patientId=""  DO
. ; Process ^DPT(patientId)
. WRITE "Patient: ",patientId,!
```

**Python Equivalent**:
```python
for patient_id in yottadb.Key("^DPT").subscripts:
    # Process patient_id
    print(f"Patient: {patient_id}")
```

**M with Reverse Order** (`$ORDER(...,-1)`):
```m
SET patientId=""
FOR  SET patientId=$ORDER(^DPT(patientId),-1) QUIT:patientId=""  DO
. WRITE patientId,!
```

**Python Reverse** (requires manual implementation):
```python
# Collect all, then reverse
patient_ids = list(yottadb.Key("^DPT").subscripts)
for patient_id in reversed(patient_ids):
    print(patient_id)
```

### Bounded Iteration

**M**:
```m
SET count=0,limit=20
SET patientId=""
FOR  SET patientId=$ORDER(^DPT(patientId)) QUIT:patientId=""  QUIT:count>=limit  DO
. SET count=count+1
. WRITE patientId,!
```

**Python**:
```python
limit = 20
for count, patient_id in enumerate(yottadb.Key("^DPT").subscripts, 1):
    print(patient_id)
    if count >= limit:
        break
```

---

## Control Structures

### If/Else

**M**:
```m
IF age>=18 WRITE "Adult"
ELSE  WRITE "Minor"
```

**Python**:
```python
if age >= 18:
    print("Adult")
else:
    print("Minor")
```

### Postconditional (M Idiom)

**M**:
```m
WRITE:age>=18 "Adult"
DO:condition SUBROUTINE
QUIT:done
```

**Python** (no direct equivalent, use explicit if):
```python
if age >= 18:
    print("Adult")
if condition:
    subroutine()
if done:
    return
```

### For Loop

**M**:
```m
FOR i=1:1:10 DO
. WRITE i,!
```

**Python**:
```python
for i in range(1, 11):  # 11 because range is exclusive
    print(i)
```

**M with Step**:
```m
FOR i=0:5:100 DO  ; 0, 5, 10, ..., 100
. WRITE i,!
```

**Python**:
```python
for i in range(0, 101, 5):
    print(i)
```

---

## Functions

### Function Definition and Call

**M**:
```m
GETNAME(dfn) ; Get patient name by DFN
 NEW name
 SET name=$PIECE($GET(^DPT(dfn,0)),"^",1)
 QUIT name

; Call it:
SET patientName=$$GETNAME(123)
```

**Python**:
```python
def get_name(dfn):
    """Get patient name by DFN."""
    try:
        zeroth = yottadb.Key("^DPT")[dfn][0].value
        name = zeroth.decode('utf-8').split("^")[0]
    except YDBError:
        name = ""
    return name

# Call it:
patient_name = get_name(123)
```

---

## Common VistA Patterns

### Pattern 1: Read and Parse 0-Node

**M**:
```m
SET DFN=123
SET VADM=$GET(^DPT(DFN,0))
SET name=$PIECE(VADM,"^",1)
SET sex=$PIECE(VADM,"^",2)
SET dob=$PIECE(VADM,"^",3)
```

**Python**:
```python
dfn = 123
try:
    vadm = yottadb.Key("^DPT")[dfn][0].value.decode('utf-8')
    parts = vadm.split("^")
    name = parts[0]
    sex = parts[1]
    dob = parts[2]
except (YDBError, IndexError, UnicodeDecodeError):
    name = sex = dob = ""
```

### Pattern 2: Loop and Collect Data

**M**:
```m
LISTPAT() ; List all patient names
 NEW DFN,name,list
 SET DFN=""
 FOR  SET DFN=$ORDER(^DPT(DFN)) QUIT:DFN=""  DO
 . SET name=$PIECE($GET(^DPT(DFN,0)),"^",1)
 . SET list(DFN)=name
 QUIT
```

**Python**:
```python
def list_patients():
    """List all patient names."""
    patient_list = {}
    for dfn in yottadb.Key("^DPT").subscripts:
        try:
            zeroth = yottadb.Key("^DPT")[dfn][0].value.decode('utf-8')
            name = zeroth.split("^")[0]
            patient_list[dfn] = name
        except (YDBError, UnicodeDecodeError):
            pass
    return patient_list
```

### Pattern 3: Follow a Pointer

**M**:
```m
; Get patient's provider name
SET DFN=123
SET providerIen=$GET(^DPT(DFN,.104))
IF providerIen'="" DO
. SET providerName=$PIECE($GET(^VA(200,providerIen,0)),"^",1)
. WRITE "Provider: ",providerName,!
```

**Python**:
```python
dfn = 123
try:
    provider_ien = yottadb.Key("^DPT")[dfn][".104"].value.decode('utf-8')
    if provider_ien:
        provider_zeroth = yottadb.Key("^VA")["200"][provider_ien][0].value.decode('utf-8')
        provider_name = provider_zeroth.split("^")[0]
        print(f"Provider: {provider_name}")
except YDBError:
    print("Provider not found")
```

---

## Operators

### Comparison

| M | Python | Meaning |
|---|--------|---------|
| `=` | `==` | Equal |
| `'=` | `!=` | Not equal |
| `>` | `>` | Greater than |
| `<` | `<` | Less than |
| `>=` or `'>` | `>=` | Greater or equal |
| `<=` or `'<` | `<=` | Less or equal |

### Logical

| M | Python | Meaning |
|---|--------|---------|
| `&` | `and` | Logical AND |
| `!` | `or` | Logical OR |
| `'` | `not` | Logical NOT |

**Example**:
```m
IF age>=18&sex="M" DO something
```

```python
if age >= 18 and sex == "M":
    do_something()
```

### Arithmetic

| M | Python |
|---|--------|
| `+` | `+` |
| `-` | `-` |
| `*` | `*` |
| `/` | `/` |
| `\` | `//` (integer division) |
| `#` | `%` (modulo) |

---

## Output

| M | Python |
|---|--------|
| `WRITE "text",!` | `print("text")` |
| `WRITE var,!` | `print(var)` |
| `WRITE "Name: ",name,!` | `print(f"Name: {name}")` |
| `WRITE !` | `print()` (newline) |

**M comma notation**:
- `,` separates items to write
- `!` is newline
- `#` is form feed
- `?n` is tab to column n

---

## Common M Intrinsic Functions

| M Function | Python Equivalent | Purpose |
|------------|-------------------|---------|
| `$ORDER(global(sub))` | `for sub in key.subscripts` | Iterate subscripts |
| `$GET(ref, default)` | `try: key.value except: default` | Safe read |
| `$PIECE(str, delim, n)` | `str.split(delim)[n-1]` | Extract field |
| `$DATA(ref)` | Custom function | Check existence |
| `$LENGTH(str)` | `len(str)` | String length |
| `$EXTRACT(str, s, e)` | `str[s-1:e]` | Substring (1-indexed!) |
| `$FIND(str, sub)` | `str.find(sub) + 1` | Find position |
| `$TRANSLATE(s, from, to)` | `s.replace(from, to)` | Replace chars |
| `$JUSTIFY(str, width)` | `str.rjust(width)` | Right justify |
| `$SELECT(cond1:val1,...)` | `val1 if cond1 else ...` | Conditional select |
| `$RANDOM(n)` | `random.randint(0, n-1)` | Random number 0 to n-1 |

---

## Naked References (Advanced)

**M allows omitting global name after first reference**:

```m
SET x=^DPT(123,0)
SET y=^(1)        ; Means ^DPT(123,1)
SET z=^(.01)      ; Means ^DPT(123,.01)
```

**Python** (always use explicit references):
```python
x = yottadb.Key("^DPT")[123][0].value
y = yottadb.Key("^DPT")[123][1].value
z = yottadb.Key("^DPT")[123][".01"].value
```

**Why avoid**: Hard to read, error-prone. Always use full paths in new code.

---

## Quick Translation Workflow

When reading M code:

1. **Identify the globals** being accessed (start with `^`)
2. **Find `$ORDER()` loops** - these are traversals you can replicate
3. **Map `$PIECE()` calls** - document which piece is which field
4. **Note `$GET()` defaults** - understand fallback values
5. **Translate control flow** - `IF`/`FOR`/`QUIT` to Python equivalents
6. **Watch for postconditionals** - expand to explicit `if` statements
7. **Handle 1-indexing** - `$EXTRACT(str,1,5)` is `str[0:5]` in Python

---

## Practical Example: Full Routine Translation

**M Routine**:
```m
FINDSSN(ssn) ; Find patient by SSN
 ; Input: ssn - Social Security Number
 ; Output: Patient IEN or "" if not found
 NEW dfn,zeroth,patientSsn
 SET dfn=""
 FOR  SET dfn=$ORDER(^DPT(dfn)) QUIT:dfn=""  DO  QUIT:dfn'=""
 . SET zeroth=$GET(^DPT(dfn,0))
 . IF zeroth="" QUIT
 . SET patientSsn=$PIECE(zeroth,"^",9)
 . IF patientSsn=ssn SET dfn=dfn QUIT
 QUIT dfn
```

**Python Translation**:
```python
def find_patient_by_ssn(ssn):
    """Find patient by SSN.

    Args:
        ssn: Social Security Number (string)

    Returns:
        Patient IEN (as string) or "" if not found
    """
    for dfn in yottadb.Key("^DPT").subscripts:
        try:
            zeroth = yottadb.Key("^DPT")[dfn][0].value
            zeroth_str = zeroth.decode('utf-8')
        except (YDBError, UnicodeDecodeError):
            continue

        parts = zeroth_str.split("^")
        if len(parts) < 9:
            continue

        patient_ssn = parts[8]  # Piece 9 = index 8
        if patient_ssn == ssn:
            return dfn

    return ""
```

---

## Tips for Reading VistA M Code

1. **Start with header comments** - they explain inputs/outputs
2. **Map globals to FileMan files** - use `^DIC` to look up file numbers
3. **Document piece positions** - create a reference for each global's 0-node
4. **Ignore abbreviations initially** - expand `S`→`SET`, `W`→`WRITE` mentally
5. **Focus on `$ORDER()` and `$PIECE()`** - these are the most common patterns
6. **Use `^DD` to verify field positions** - don't guess piece numbers

---

## See Also

- `03-m-language-primer.md` - Full M language introduction
- `01-yottadb-fundamentals.md` - Global structure and Key objects
- `04-vista-patient-data.md` - Real-world usage in patient file

---

## Keep This Handy

Bookmark this file and refer to it when reading VistA routines. Over time, these patterns will become second nature.
