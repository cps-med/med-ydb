# `cli/03_list_globals.py` Technical Reference

## Purpose

`cli/03_list_globals.py` is a **read-only discovery tool** for listing YottaDB global roots (for example, `^DPT`, `^DIC`, `^VA`).

It is designed for early exploration in a VEHU VistA environment:

1. Show available globals quickly.
2. Keep output bounded with `--limit`.
3. Survive environment differences by using fallback strategies.
4. Optionally enrich output with FileMan metadata (file number and file name).

---

## Audience Assumptions

This guide assumes you:

1. Know basic Python syntax/functions/loops/exceptions.
2. Do **not** yet know YottaDB, VistA, M (MUMPS), or the `yottadb` Python package.

---

## Quick Domain Primer

### What is a “global”?

In YottaDB, a global is a persistent hierarchical key-value tree.  
Global names start with `^`, such as `^DPT` or `^DIC`.

### What is `^$GLOBAL`?

`^$GLOBAL` is a system-provided global index used to discover global names.

### What is `^DIC(file#,0,"GL")`?

In VistA/FileMan, many file definitions store their root global in this location.  
Example idea: if file `2` maps to patients, the `GL` node can indicate `^DPT(`.

### Deep Dive: Template Root vs Real Global Node

This is the most important distinction:

1. `^DPT(` in `^DIC(file#,0,"GL")` is a **template root string**.
2. `^DPT(123,0)` is a **real data node reference**.

The `GL` value often ends with `(` because old M code builds full references by concatenating subscripts.

Example flow for File `2`:

1. `^DIC(2,0,"GL")` stores `^DPT(`
2. Application chooses a record IEN, for example `123`
3. Full record node becomes `^DPT(123,0)`

In practice:

1. M code often builds string references, then dereferences them.
2. Python `yottadb.Key` code usually normalizes the template to `^DPT` and appends subscripts structurally.

M-style concept:

```text
ROOT = "^DPT("
REF  = ROOT_"123,0)"    -> "^DPT(123,0)"
```

Python-style concept:

```python
base = "^DPT("
base_root = base.split("(")[0]   # "^DPT"
node = yottadb.Key(base_root)["123"]["0"]
```

### Example Patient Global Structure (Illustrative)

Below is a simplified, illustrative example (not exact production schema) showing how patient data can be arranged under `^DPT`:

```text
^DPT
└── (123)
    ├── (0)                = "DOE,JOHN^M^19600115^^..."
    ├── (.01)              = "DOE,JOHN"
    ├── (.02)              = "M"
    ├── (.03)              = "19600115"
    ├── ("ADDR",1,0)       = "123 MAIN ST^^LANSING^MI^48933"
    ├── ("PHONE",1,0)      = "517-555-1212"
    └── ("VISIT",42,0)     = "3240101.1015^CARDIOLOGY^FOLLOW-UP"
```

Interpretation of this tree:

1. `^DPT` is the patient-file root global.
2. `123` is one patient record (IEN).
3. `0`, `.01`, `.02`, `.03` are common field-storage nodes for the record.
4. `"ADDR"` and `"PHONE"` represent grouped child nodes.
5. `"VISIT",42,0` shows a nested child record (visit #42).

Same example as node/value pairs:

```text
^DPT(123,0)               -> "DOE,JOHN^M^19600115^^..."
^DPT(123,.01)             -> "DOE,JOHN"
^DPT(123,.02)             -> "M"
^DPT(123,.03)             -> "19600115"
^DPT(123,"ADDR",1,0)      -> "123 MAIN ST^^LANSING^MI^48933"
^DPT(123,"PHONE",1,0)     -> "517-555-1212"
^DPT(123,"VISIT",42,0)    -> "3240101.1015^CARDIOLOGY^FOLLOW-UP"
```

How applications use this:

1. Discover the root from `^DIC(file#,0,"GL")`
2. Build a concrete key path by adding subscripts
3. Read/write the terminal node value
4. Traverse children for grouped or repeating data

### Why fallback methods?

Depending on binding/version behavior, direct Python access to `^$GLOBAL` can fail (`YDBError`, often `INVVARNAME`).  
This script then tries:

1. M direct-mode `$ORDER(^$GLOBAL(...))`
2. FileMan dictionary inference via `^DIC(...,"GL")`

---

## Script Responsibilities at a Glance

1. Parse CLI flags (`--limit`, `--prefix`, `--raw`)
2. Normalize/validate input
3. Try primary global enumeration (`yottadb.Key("^$GLOBAL").subscripts`)
4. On failure, use fallback enumeration
5. Print aligned output safely and consistently

---

## CLI Interface

### Command

```bash
python3 cli/03_list_globals.py [--limit N] [--prefix PREFIX] [--raw]
```

### Arguments

1. `--limit` (default `50`)
   - Max number of globals shown.
   - Script enforces minimum `1` via `max(1, args.limit)`.
2. `--prefix` (default empty)
   - Optional filter like `^D` or `D`.
   - `normalize_prefix()` guarantees leading `^` if provided.
3. `--raw` (flag)
   - Prints repr-style output to reveal exact raw values/bytes behavior.

---

## `yottadb.Key` Reference (Essential for This Script)

`yottadb.Key` is the main Python object for navigating YottaDB globals.

Think of it as a pointer to a specific node path:

1. Root only: `yottadb.Key("^DPT")`
2. One subscript deeper: `yottadb.Key("^DPT")["123"]`
3. Deeper path: `yottadb.Key("^DPT")["123"]["0"]`

### Core Behaviors

1. **Path composition with `[]`**
   - Each `[]` adds one subscript level.
   - Subscripts may be strings or numbers (typically represented as text in code for consistency).
2. **Read node value with `.value`**
   - Returns bytes when value exists.
   - Raises `YDBError` for missing/invalid access patterns.
3. **Iterate children with `.subscripts`**
   - Returns iterator over immediate child subscripts at that node.
   - This corresponds to M `$ORDER()` traversal behavior.

### Basic Example

```python
import yottadb
from yottadb import YDBError

root = yottadb.Key("^DPT")
patient = root["123"]
zero_node = patient["0"]

try:
    raw = zero_node.value
    text = raw.decode("utf-8")
except YDBError:
    text = "<no value at ^DPT(123,0)>"
```

### Iteration Example (similar to this script)

```python
globals_index = yottadb.Key("^$GLOBAL")

for raw_name in globals_index.subscripts:
    # raw_name may be bytes depending on environment
    # script uses as_text(raw_name) to normalize
    print(raw_name)
```

### Relationship to `03_list_globals.py`

The script uses `Key` in two major ways:

1. `yottadb.Key("^$GLOBAL").subscripts`
   - Enumerates global names directly (primary strategy).
2. `yottadb.Key("^DIC")[file_sub]["0"]["GL"].value`
   - Reads FileMan dictionary metadata for fallback enrichment.

### Common Pitfalls for New Developers

1. **Template root vs concrete root**
   - `^DIC(...,"GL")` can return `^DPT(`.
   - `Key` generally needs concrete root `^DPT` (no trailing `(`), so normalize first.
2. **Bytes vs str confusion**
   - Many reads return bytes; decode before display logic.
3. **Missing node assumptions**
   - Not every node has a value; children may exist even when parent value is absent.
4. **Unbounded iteration**
   - Always cap traversal (`--limit` pattern) in exploratory scripts.

### Quick Mapping: M vs Python

```text
M reference             Python Key path
----------------------  -----------------------------
^DPT                    yottadb.Key("^DPT")
^DPT(123)               yottadb.Key("^DPT")["123"]
^DPT(123,0)             yottadb.Key("^DPT")["123"]["0"]
^DIC(2,0,"GL")          yottadb.Key("^DIC")["2"]["0"]["GL"]
```

### `Node` vs `Key` (Which Should You Use?)

In this environment, both `yottadb.Node` and `yottadb.Key` exist, and `Key` is implemented as a subclass alias for backward compatibility.

Practical result:

1. They expose the same core behaviors used in this project.
2. Code written with either one is typically equivalent at runtime.

Equivalent examples:

```python
import yottadb

# Key style
k = yottadb.Key("^DPT")["123"]["0"]

# Node style
n = yottadb.Node("^DPT")["123"]["0"]
```

Recommended pattern for this repository:

1. Prefer `yottadb.Key` in project code and docs.
2. Reason: existing scripts and learning docs already standardize on `Key`, so this minimizes cognitive load for new developers.

When to choose one over the other:

1. Use `Key` when working in this repo, extending existing scripts, or teaching newcomers with local examples.
2. Use `Node` only when:
   - external/upstream docs or sample code you are following uses `Node`, and
   - you are intentionally aligning with that external material.

Team consistency guidance:

1. Do not mix `Node` and `Key` styles within the same module unless there is a specific interoperability reason.
2. If migrating style, do it as a small, dedicated cleanup change rather than gradually mixing both names.

---

## High-Level Control Flow

```text
+----------------------+
| parse CLI arguments  |
+----------+-----------+
           |
           v
+----------------------+
| normalize limit/pfx  |
+----------+-----------+
           |
           v
+------------------------------+
| Primary: ^$GLOBAL via Python |
| yottadb.Key("^$GLOBAL")      |
+----------+-------------------+
           |
      success? -------- no ----------------------+
           |                                     |
          yes                                    v
           |                          +---------------------------+
           v                          | Fallback #1: mumps -direct|
+------------------------+            | $ORDER(^$GLOBAL(...))     |
| print rows / truncate  |            +-------------+-------------+
+-----------+------------+                          |
            |                                 success + rows?
            |                                        |
            +-----------------------------+----------+
                                          | yes
                                          v
                                 +-------------------+
                                 | print enriched    |
                                 | rows + truncate   |
                                 +---------+---------+
                                           |
                                      no rows / fail
                                           |
                                           v
                           +-------------------------------+
                           | Fallback #2: ^DIC(...,"GL")   |
                           | derive global roots from DD   |
                           +---------------+---------------+
                                           |
                                           v
                                   print or no-match
```

---

## Architecture and Design Approach

The script uses a **layered discovery strategy**:

1. **Fast path**: ask YottaDB directly for global names.
2. **Compatibility path**: run direct M code when Python API handling is strict.
3. **Semantic fallback**: infer likely globals from FileMan data dictionary.

This is a pragmatic architecture for mixed/legacy environments:

1. Works on “ideal” systems quickly.
2. Still useful on partially incompatible systems.
3. Remains read-only through all paths.

---

## Function-by-Function Walkthrough

### `parse_args()`

Creates the argument parser and exposes script flags.

### `normalize_prefix(prefix)`

Ensures filters compare against full global roots:

1. Empty input stays empty.
2. Non-empty input gets `^` prefix if missing.

This avoids repeated string cleanup in later code.

### `as_text(value)`

Converts `bytes | str -> str`.

1. Returns strings unchanged.
2. Attempts UTF-8 decode for bytes.
3. Falls back to `repr(value)` on decode failure.

Why this matters: YottaDB values/subscripts can appear as bytes; display code needs robust text conversion.

### `parse_file_name_from_dic0(dic0_value)`

Extracts a friendly FileMan file name from the `0` node text (typically `NAME^FILE#^...`).

### `build_global_metadata_map(prefix)`

Builds:

```python
{
  "^DPT": [("2", "PATIENT")],
  "^VA": [("200", "NEW PERSON"), ...]
}
```

Process:

1. Iterate `^DIC` file entries.
2. Read `^DIC(file#,0,"GL")` for root global.
3. Normalize to base root (`split("(")[0]`).
4. Optional prefix filtering.
5. Read `^DIC(file#,0)` for file name.
6. Store unique `(file_number, file_name)` tuples.

This metadata is used to annotate fallback output.

### `metadata_suffix(global_name, metadata)`

Formats annotations:

1. One reference: `[#2 PATIENT]`
2. Multiple references: `[#200 NEW PERSON; #...; +N more]`

### `print_aligned_rows(rows, raw=False, start_index=1)`

Handles clean terminal formatting:

1. Computes longest global name for alignment.
2. Prints numbered rows.
3. Uses `repr()` when `--raw` is set.

### `_m_escape(s)`

Escapes double quotes for M string literals (`"` -> `""`).

### `list_globals_via_m_direct(prefix, limit, raw=False)`

Fallback #1.  
Builds and runs M code via:

```bash
bash -lc "mumps -direct"
```

The M loop:

1. Uses `$ORDER(^$GLOBAL(g))` to walk global names.
2. Applies prefix filter.
3. Writes count + global name.
4. Stops at `limit`.

Post-processing in Python:

1. Removes `GTM>` / `VEHU>` prompt lines.
2. Parses returned names.
3. Appends FileMan metadata suffixes (if available).
4. Prints aligned output.

Return contract:

1. `-1` = failure
2. `0` = success but no rows
3. `>0` = number of printed rows

### `list_globals_via_data_dictionary(prefix, limit, raw=False)`

Fallback #2.  
Uses only metadata inference from FileMan dictionary:

1. Build metadata map.
2. Sort inferred global roots.
3. Print up to `limit`.

Same return contract as above (`-1`, `0`, `>0`).

### `main()`

Main orchestration:

1. Parse args and print header.
2. Attempt primary enumeration from `^$GLOBAL`.
3. If primary fails:
   - Try M direct fallback.
   - If empty/failure, try FileMan dictionary fallback.
4. Print truncation indicator when needed.
5. Return process exit code (`0` success, `1` on hard failure).

---

## Data and Error Handling Model

### Normalized string handling

All external data (subscripts/values) is normalized through helper functions before display.

### Exception strategy

The script catches `YDBError` around operations likely to fail in sparse/mixed data:

1. Missing nodes
2. Special variable access differences
3. Environment binding incompatibilities

### User-visible behavior

Errors are informative but non-destructive:

1. Print error context to `stderr`
2. Attempt next fallback path
3. Exit `1` only when no method can proceed

---

## Read-Only and Safety Characteristics

1. No `.value = ...` writes anywhere in script.
2. Traversal is bounded by `limit`.
3. Prefix filtering reduces accidental wide scans.
4. Fallbacks are also read-only (`$ORDER`, dictionary reads).

---

## Practical Example Scenarios

### 1) Quick scan

```bash
python3 cli/03_list_globals.py
```

Expected: first 50 globals, possibly truncated.

### 2) Focused exploration

```bash
python3 cli/03_list_globals.py --prefix ^D --limit 25
```

Expected: globals starting with `^D`.

### 3) Debug raw representation

```bash
python3 cli/03_list_globals.py --raw --limit 10
```

Expected: repr-formatted lines to inspect raw behavior/encoding.

---

## Text Diagram: Metadata Enrichment

```text
^DIC(file#,0,"GL")  ---->  "^DPT("
       |                        |
       | split("(")[0]          v
       +------------------> "^DPT" (base root)
                                |
^DIC(file#,0) ----> "PATIENT^2^..."  -> parse name "PATIENT"
                                |
                                v
                    metadata["^DPT"] += ("2", "PATIENT")
```

Printed output can become:

```text
1. ^DPT    [#2 PATIENT]
```

---

## Known Limitations and Nuances

1. `^$GLOBAL` behavior can vary by environment/binding details.
2. Data-dictionary fallback shows globals represented in FileMan metadata, not necessarily all runtime globals.
3. `split("(")[0]` canonicalizes roots for display, which may hide argumented forms (`^VA(200,...)` shown as `^VA` base family in metadata map semantics).
4. UTF-8 decode assumptions are practical defaults; non-UTF bytes appear as `repr(...)`.

---

## Suggested Extension Ideas

1. Add `--json` output mode for tooling integration.
2. Add `--show-source` to display which method succeeded (`simpleapi`, `m-direct`, `dic`).
3. Add elapsed-time metrics per method.
4. Add optional “include metadata” toggle for primary path too.

---

## Developer Mental Model Summary

Think of this script as a **resilient read-only index browser**:

1. It prefers direct API discovery.
2. It falls back to native M traversal when needed.
3. It finally falls back to FileMan dictionary inference.
4. It always prioritizes safe, bounded output over exhaustive scanning.
