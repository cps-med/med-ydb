# M Language Primer for Python Developers

**Goal**: Develop reading literacy in M (MUMPS) language to understand VistA code

**Audience**: Python developers who need to read (not write) M code

**Approach**: Side-by-side M and Python comparisons

---

## What is M (MUMPS)?

**M** (originally MUMPS - Massachusetts General Hospital Utility Multi-Programming System) is the language VistA is written in. It's been in continuous use since 1966, primarily in healthcare.

### Key Characteristics
- **Terse syntax**: Minimal punctuation, short keywords, lots of abbreviations
- **Integrated database**: Language and database (globals) are inseparable
- **Weak typing**: Variables have no declared types
- **Line-oriented**: Each line is a command (usually)
- **Whitespace-significant**: Spacing matters for control structures

### Your Goal: Reading, Not Writing

You don't need to write M code. You need to **read VistA routines** to understand:
- How VistA accesses patient data
- What business rules exist
- How to call VistA functions from Python (later)

---

## M vs. Python: Core Concepts

### Variables

**Python**:
```python
name = "John Smith"
age = 42
patient_id = 123
```

**M**:
```m
SET name="John Smith"
SET age=42
SET patientId=123
```

- `SET` assigns a value (abbrev: `S`)
- Variable names are case-insensitive in M (usually seen as camelCase)
- No type declarations

### Comments

**Python**:
```python
# This is a comment
x = 5  # Inline comment
```

**M**:
```m
; This is a comment
SET x=5  ; Inline comment
```

Comments start with `;` (semicolon).

### Printing Output

**Python**:
```python
print("Hello world")
print(f"Patient: {name}")
```

**M**:
```m
WRITE "Hello world",!
WRITE "Patient: ",name,!
```

- `WRITE` outputs text (abbrev: `W`)
- `,!` is newline
- `,` separates multiple items to write
- No string interpolation - concatenate with commas

---

## Control Structures

### If Statements

**Python**:
```python
if age >= 18:
    print("Adult")
else:
    print("Minor")
```

**M**:
```m
IF age>=18 WRITE "Adult",!
ELSE  WRITE "Minor",!
```

Or with command postconditionals (M idiom):
```m
WRITE:age>=18 "Adult",!
WRITE:age<18 "Minor",!
```

**Postconditional syntax**: `COMMAND:condition` - execute command only if condition is true.

### For Loops

**Python**:
```python
for i in range(1, 11):
    print(i)
```

**M**:
```m
FOR i=1:1:10 DO
. WRITE i,!
```

**M for syntax**: `FOR variable=start:increment:stop`
- Periods (`.`) indicate indented block scope
- `DO` starts a block
- `QUIT` exits a block

### While Loops (Sort of)

**Python**:
```python
while condition:
    do_something()
    if should_break:
        break
```

**M**:
```m
FOR  DO  QUIT:shouldBreak
. ; do something
```

**M infinite loop**: `FOR  DO  QUIT:condition`
- `FOR` with no parameters = infinite loop
- `QUIT:condition` = break if condition true

---

## M's Critical Functions

### `$ORDER()` - Traversal

**Purpose**: Iterate through subscripts of a global (like Python's iterator)

**Python**:
```python
for patient_id in yottadb.Key("^DPT").subscripts:
    print(patient_id)
```

**M**:
```m
SET patientId=""
FOR  SET patientId=$ORDER(^DPT(patientId)) QUIT:patientId=""  DO
. WRITE "Patient: ",patientId,!
```

**How `$ORDER()` works**:
- `$ORDER(^DPT(""))` returns first subscript
- `$ORDER(^DPT(lastValue))` returns next subscript after `lastValue`
- Returns `""` (empty string) when no more subscripts
- Traverse in collation order (numeric first, then strings)

**Common pattern**:
```m
SET sub=""
FOR  SET sub=$ORDER(^GLOBAL(sub)) QUIT:sub=""  DO
. ; Process ^GLOBAL(sub)
```

### `$GET()` - Safe Read

**Purpose**: Read a value with a default if undefined (prevents GVUNDEF errors)

**Python**:
```python
try:
    value = key.value
except YDBError:
    value = b""  # Default
```

**M**:
```m
SET value=$GET(^DPT(patientId,0),"")
```

**Syntax**: `$GET(reference, default)`
- If `^DPT(patientId,0)` exists, returns its value
- If not, returns default (second argument)
- Default defaults to `""` if omitted

**Common usage**:
```m
; Get patient name or "(unknown)" if not set
SET name=$GET(^DPT(patientId,.01),"(unknown)")
```

### `$PIECE()` - String Splitting

**Purpose**: Extract fields from delimited strings (VistA uses `^` delimiter)

**Python**:
```python
record = "SMITH,JOHN^M^2451201^555-1234"
fields = record.split("^")
name = fields[0]        # "SMITH,JOHN"
sex = fields[1]         # "M"
dob = fields[2]         # "2451201"
```

**M**:
```m
SET record="SMITH,JOHN^M^2451201^555-1234"
SET name=$PIECE(record,"^",1)      ; "SMITH,JOHN"
SET sex=$PIECE(record,"^",2)       ; "M"
SET dob=$PIECE(record,"^",3)       ; "2451201"
```

**Syntax**: `$PIECE(string, delimiter, piece_number)`
- Piece numbers start at 1 (not 0!)
- Can extract ranges: `$PIECE(record,"^",2,4)` gets pieces 2-4

**Common in VistA**:
```m
; Read patient 0-node
SET zeroth=$GET(^DPT(patientId,0))
SET name=$PIECE(zeroth,"^",1)
SET sex=$PIECE(zeroth,"^",2)
SET dob=$PIECE(zeroth,"^",3)
```

### `$DATA()` - Check Existence

**Purpose**: Check if a node has data and/or descendants

**Python** (approximate):
```python
# Check if node has value
try:
    value = key.value
    has_value = True
except YDBError:
    has_value = False
```

**M**:
```m
SET dataStatus=$DATA(^DPT(patientId,0))
```

**Return values**:
- `0` = node doesn't exist (no value, no descendants)
- `1` = node has value but no descendants
- `10` = node has descendants but no value
- `11` = node has both value and descendants

**Common usage**:
```m
IF $DATA(^DPT(patientId)) DO
. ; Patient record exists
```

### `$LENGTH()` - String Length

**Python**:
```python
text = "Hello"
length = len(text)  # 5
```

**M**:
```m
SET text="Hello"
SET length=$LENGTH(text)  ; 5
```

### `$EXTRACT()` - Substring

**Python**:
```python
text = "Hello World"
first_five = text[:5]       # "Hello"
from_index_6 = text[6:]     # "World"
middle = text[6:8]          # "Wo"
```

**M**:
```m
SET text="Hello World"
SET firstFive=$EXTRACT(text,1,5)      ; "Hello"
SET fromIndex6=$EXTRACT(text,7,999)   ; "World"  (M is 1-indexed!)
SET middle=$EXTRACT(text,7,8)         ; "Wo"
```

**Key difference**: M strings are 1-indexed, Python is 0-indexed.

---

## M Syntax Quirks for Python Developers

### 1. No Indentation - Use Periods

**Python**:
```python
if condition:
    line1()
    line2()
```

**M**:
```m
IF condition DO
. ; line1
. ; line2
```

Periods indicate "this line is in the block above."

### 2. Command Abbreviations

M allows (and encourages) abbreviating commands:

| Full | Abbrev | Purpose |
|------|--------|---------|
| `SET` | `S` | Assign variable |
| `WRITE` | `W` | Output |
| `QUIT` | `Q` | Return/exit |
| `DO` | `D` | Call subroutine |
| `FOR` | `F` | Loop |
| `IF` | `I` | Conditional |
| `ELSE` | `E` | Else branch |
| `KILL` | `K` | Delete variable |
| `NEW` | `N` | Create local scope |

**You'll see both** in VistA code. Older code uses abbreviations heavily.

### 3. Concatenation

**Python**:
```python
full_name = first + " " + last
# or
full_name = f"{first} {last}"
```

**M**:
```m
SET fullName=first_" "_last
```

`_` is the string concatenation operator.

### 4. Multiple Commands Per Line

**M allows multiple commands per line separated by spaces**:

```m
SET x=5 SET y=10 SET z=x+y WRITE z,!
```

This is legal (but harder to read). More common:
```m
SET x=5,y=10,z=x+y WRITE z,!
```

### 5. Naked References (Advanced - Avoid)

M remembers the last global reference and allows "naked" subscripts:

```m
SET x=^DPT(123,0)     ; Full reference
SET y=^(1)            ; "Naked" - means ^DPT(123,1)
```

**Why this matters**: You'll see `^(subscript)` in VistA code. It refers to the last global name used.

**Why to avoid**: Hard to read, error-prone. Use full references in your own code.

---

## Reading a VistA Routine Example

Let's read a simplified patient lookup routine:

**M code**:
```m
GETPAT(patientId) ; Get patient demographics
 ; Input: patientId - Patient IEN
 ; Output: Patient name^sex^DOB or "" if not found
 ;
 NEW zeroth,name,sex,dob
 SET zeroth=$GET(^DPT(patientId,0))
 IF zeroth="" QUIT ""
 SET name=$PIECE(zeroth,"^",1)
 SET sex=$PIECE(zeroth,"^",2)
 SET dob=$PIECE(zeroth,"^",3)
 QUIT name_"^"_sex_"^"_dob
```

**Translation to Python**:
```python
def get_patient(patient_id):
    """Get patient demographics.

    Args:
        patient_id: Patient IEN

    Returns:
        "name^sex^dob" or "" if not found
    """
    try:
        zeroth = yottadb.Key("^DPT")[patient_id][0].value
    except YDBError:
        return b""

    # Parse pieces (split on ^)
    parts = zeroth.decode('utf-8').split("^")
    name = parts[0] if len(parts) > 0 else ""
    sex = parts[1] if len(parts) > 1 else ""
    dob = parts[2] if len(parts) > 2 else ""

    result = f"{name}^{sex}^{dob}"
    return result.encode('utf-8')
```

**Line-by-line M analysis**:
1. `GETPAT(patientId)` - Function definition with parameter
2. `; comments` - Documentation
3. `NEW zeroth,name,sex,dob` - Declare local variables (prevents side effects)
4. `SET zeroth=$GET(^DPT(patientId,0))` - Read patient 0-node, default to ""
5. `IF zeroth="" QUIT ""` - Return empty if patient doesn't exist
6. `SET name=$PIECE(zeroth,"^",1)` - Extract name field
7. `QUIT name_"^"_sex_"^"_dob` - Return concatenated result

---

## Common M Patterns in VistA

### Pattern 1: Looping Through a Global

```m
; List all patient names
SET patientId=""
FOR  SET patientId=$ORDER(^DPT(patientId)) QUIT:patientId=""  DO
. SET name=$PIECE($GET(^DPT(patientId,0)),"^",1)
. WRITE "Patient ",patientId,": ",name,!
```

**Python equivalent**:
```python
for patient_id in yottadb.Key("^DPT").subscripts:
    try:
        zeroth = yottadb.Key("^DPT")[patient_id][0].value
        name = zeroth.decode('utf-8').split("^")[0]
        print(f"Patient {patient_id}: {name}")
    except YDBError:
        print(f"Patient {patient_id}: (no 0-node)")
```

### Pattern 2: Finding a Record by Field

```m
; Find patient by SSN
FINDSSN(ssn) ; Return patient IEN or "" if not found
 NEW patientId,zeroth,patientSsn
 SET patientId=""
 FOR  SET patientId=$ORDER(^DPT(patientId)) QUIT:patientId=""  DO  QUIT:patientId'=""
 . SET zeroth=$GET(^DPT(patientId,0))
 . SET patientSsn=$PIECE(zeroth,"^",9)  ; SSN is piece 9
 . IF patientSsn=ssn SET patientId=patientId QUIT
 QUIT patientId
```

**What it does**: Linear scan through all patients until SSN matches.

### Pattern 3: Using FileMan API

```m
; Call FileMan to update a field
DO UPDATE^DIE("","FDA","ERROR")
```

**Note**: FileMan has its own API for safe updates. You'll see `^DIE`, `^DIC`, `^DIK` calls in VistA.

---

## M Functions Reference (Quick Lookup)

| Function | Purpose | Example |
|----------|---------|---------|
| `$ORDER(global(sub))` | Get next subscript | `$ORDER(^DPT(123))` → next after 123 |
| `$GET(ref, default)` | Read with default | `$GET(^DPT(123,0),"")` |
| `$PIECE(str, delim, n)` | Extract field | `$PIECE("A^B^C","^",2)` → "B" |
| `$DATA(ref)` | Check existence | `$DATA(^DPT(123))` → 0/1/10/11 |
| `$LENGTH(str)` | String length | `$LENGTH("Hello")` → 5 |
| `$EXTRACT(str, start, end)` | Substring (1-indexed) | `$EXTRACT("Hello",1,2)` → "He" |
| `$FIND(str, substr)` | Find substring | `$FIND("Hello","ll")` → 4 |
| `$JUSTIFY(str, width)` | Right-justify | `$JUSTIFY(123,5)` → "  123" |
| `$TRANSLATE(str, from, to)` | Character replace | `$TRANSLATE("abc","a","A")` → "Abc" |

---

## Hands-On: Reading VistA Code

### Exercise 1: Understand This M Snippet

```m
SET DFN=123
SET VADM(1)=$PIECE($GET(^DPT(DFN,0)),"^",1)
SET VADM(2)=$PIECE($GET(^DPT(DFN,0)),"^",2)
SET VADM(3)=$PIECE($GET(^DPT(DFN,0)),"^",3)
```

**Questions**:
1. What is `DFN`? (Hint: it's VistA's term for patient IEN)
2. What is being stored in `VADM(1)`, `VADM(2)`, `VADM(3)`?
3. Translate this to Python

<details>
<summary>Answer</summary>

`DFN` = patient internal entry number (IEN)
- `VADM(1)` = patient name (piece 1)
- `VADM(2)` = patient sex (piece 2)
- `VADM(3)` = patient DOB (piece 3)

**Python**:
```python
dfn = 123
key = yottadb.Key("^DPT")[dfn][0]
zeroth = key.value.decode('utf-8')
vadm = {}
vadm[1] = zeroth.split("^")[0]  # Name
vadm[2] = zeroth.split("^")[1]  # Sex
vadm[3] = zeroth.split("^")[2]  # DOB
```
</details>

### Exercise 2: Find This Pattern in VEHU

SSH into VEHU and examine a routine:

```bash
docker exec -it vehu-dev su - vehu
# At VistA prompt:
mumps -direct
# At M prompt (>):
ZPRINT ^DPTLK1
# Press Enter repeatedly to see the code
```

Find examples of:
- `$ORDER()` usage
- `$PIECE()` usage
- `$GET()` with defaults

### Exercise 3: Translate M to Python

Given this M function:

```m
COUNTPAT() ; Count total patients
 NEW count,patientId
 SET count=0
 SET patientId=""
 FOR  SET patientId=$ORDER(^DPT(patientId)) QUIT:patientId=""  DO
 . SET count=count+1
 QUIT count
```

Write the Python equivalent. Test it with `03_explore_allowlisted.py`.

---

## Tips for Reading VistA M Code

1. **Start with comments** - M routines have header comments explaining purpose
2. **Focus on globals accessed** - Look for `^DPT`, `^DIC`, etc. to understand data flow
3. **Identify `$ORDER()` loops** - These are traversals you can replicate in Python
4. **Note `$PIECE()` positions** - Document which piece is which field
5. **Ignore naked references initially** - Come back to them once you understand the routine
6. **Use VistA documentation** - The VDL (VistA Document Library) explains FileMan files

---

## M Idioms You'll See Often

### Idiom 1: "Set and Quit"
```m
SET result=value QUIT result
```
Could be two lines, but M style combines them.

### Idiom 2: Postconditional Everything
```m
DO:condition SUBROUTINE
QUIT:done
WRITE:verbose message,!
```
`command:condition` is pervasive in M.

### Idiom 3: "NEW Everything"
```m
NEW var1,var2,var3
```
Prevents variable pollution. Like Python's function-local scope, but explicit.

### Idiom 4: Empty String Tests
```m
IF x="" DO something
IF x'="" DO somethingElse
```
`'` is the "not" operator. `x'=""` means `x != ""`.

---

## Key Takeaways

1. **M is terse** - abbreviations, minimal syntax, lots packed per line
2. **`$ORDER()` is everywhere** - it's how you traverse globals
3. **`$PIECE()` is critical** - VistA stores delimited data; piece numbers map to fields
4. **`$GET()` prevents errors** - always use it when reading possibly-undefined nodes
5. **1-indexed strings** - M strings start at position 1, not 0
6. **Periods mean scope** - indentation is visual; periods are functional
7. **You don't need to write M** - just understand patterns to read VistA code

---

## Next Steps

- Read `04-vista-patient-data.md` to see M patterns in context (patient file structure)
- Practice translating M snippets to Python in `docs/learn/exercises/`
- Use `reference/m-to-python-patterns.md` as a cheat sheet when reading VistA routines
- Explore actual VistA routines in VEHU (start with `^DPTLK*` - patient lookup routines)

---

## References

- M Language Specification: https://docs.yottadb.com/ProgrammersGuide/langfeat.html
- VistA Routine Documentation: https://www.va.gov/vdl/
- Your script: `app/02_list_globals.py` lines 147-222 (contains M code example in subprocess)
