# Project Context for Claude

## Project Overview

This is a personal learning project for understanding YottaDB and the VistA (Veterans Health Information Systems and Technology Architecture) healthcare application running on the VEHU (VistA Environment for Healthcare Utilities) platform.

## Primary Goals

1. **Learn YottaDB**: Understand global-based hierarchical database concepts, key/subscript patterns, and Python integration
2. **Learn VistA Architecture**: Focus on data structures, FileMan data dictionary, and patient data management
3. **Learn M Language**: Develop ability to read and understand MUMPS code used throughout VistA
4. **Future Goal**: Build a modern Python/FastAPI web UI to replace the "roll-and-scroll" terminal interface

## Current Phase: Deep Learning (Not Production)

- **Timeline**: No rush - focused on understanding fundamentals
- **Mode**: Read-only exploration with safety guardrails
- **Writes**: Not yet, but will be needed eventually
- **Audience**: Personal learning project

## Technical Environment

### Runtime
- **Container**: `worldvista/vehu:202504` (linux/amd64)
- **Container Name**: `vehu-dev`
- **Host Platform**: macOS Apple Silicon (M-series)
- **Python Version in VEHU**: 3.6.8 (stay compatible)
- **YottaDB**: Via `/usr/local/etc/ydb_env_set` in container

### Docker Setup
- Managed via `docker-compose.yaml` at repo root
- Bind mounts: `./app`, `./docs`, `./src`, `./tests` → `/opt/med-ydb/*` (read-only)
- Ports: 2222 (SSH), 5001 (HL7), 8001, 8080, 9430 (VEHU services)

### Dependencies (Container-Local)
- Must install in container: `python3-devel`, `gcc`, `make`, `libffi-devel`
- Python package: `yottadb` (installed with `python3 -m pip install --user yottadb`)
- Installation is ephemeral (lost on container recreation)

## Repository Structure

```text
med-ydb/
├── CLAUDE.md                    # This file
├── README.md                    # Project overview
├── docker-compose.yaml          # Container orchestration
├── app/                         # Python scripts (mounted into container)
│   ├── 01_env_check.py         # Runtime sanity check
│   ├── 02_list_globals.py      # Global discovery with fallbacks
│   ├── 03_explore_allowlisted.py # Safe read-only explorer
│   ├── sample_01.py            # Early experiment (has writes!)
│   └── sample_02.py            # Early read-only sample
├── docs/
│   ├── guide/                   # Operational how-to guides
│   │   ├── vista-vehu-docker-guide.md
│   │   ├── yottadb-python-vehu-readonly-lab.md
│   │   └── ...
│   ├── spec/                    # Reference specs and handoffs
│   │   └── med-ydb-new-thread-handoff.md
│   └── learn/                   # Learning materials and exercises
│       ├── 00-learning-plan.md
│       ├── exercises/
│       └── reference/
└── src/
    └── routines/
        └── HELLO.m              # Sample M routine

```

## Running Scripts Pattern

Scripts must run inside VEHU container with YottaDB environment:

```bash
# Standard pattern
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && python3 /opt/med-ydb/app/SCRIPT.py [args]'

# Examples
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && python3 /opt/med-ydb/app/01_env_check.py'
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && python3 /opt/med-ydb/app/02_list_globals.py --prefix ^D --limit 50'
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && python3 /opt/med-ydb/app/03_explore_allowlisted.py --global ^DPT --max-nodes 20'
```

## Current Learning Focus

### Immediate Interests
1. **VistA Architecture**: How the system is organized, self-documenting structure
2. **Patient Data**: File #2 (PATIENT), demographics, identifiers in `^DPT` global
3. **FileMan**: Data dictionary (`^DIC`), field definitions (`^DD`), file structure
4. **M Language**: Syntax, patterns, reading existing VistA code

### Key VistA Concepts to Explore
- **Globals**: Hierarchical persistent variables (e.g., `^DPT`, `^DIC`, `^VA`)
- **FileMan Files**: VistA's database abstraction layer (like ORM)
- **Pointers**: VistA's way of implementing relationships between files
- **0-nodes**: Metadata storage pattern (subscript "0" contains record header)
- **Piece notation**: Field delimiters using `^` within values

## Safety Philosophy

### Current Guardrails
- **Default read-only**: Scripts avoid writes/deletes
- **Allowlist enforcement**: `03_explore_allowlisted.py` blocks non-approved globals
- **Bounded traversal**: `--max-nodes` limits prevent runaway exploration
- **Progressive complexity**: Scripts numbered 01→02→03 build on each other

### Allowed Globals (Current)
```python
ALLOWED_GLOBALS = {
    "^DIC",  # FileMan data dictionary
    "^DPT",  # Patient file
    "^VA",   # Various VA files
}
```

Expand deliberately as learning progresses.

## Python Version Strategy

**Decision**: Stay on Python 3.6.x for now
- VEHU container provides Python 3.6.8
- Current scripts are compatible
- Upgrade to 3.10+ later via derived Docker image (see `docs/guide/yottadb-python-vehu-readonly-lab.md` Appendix A)
- No rush - focus is on learning YottaDB/VistA, not fighting Python versions

## Known Quirks and Workarounds

### YottaDB Python Binding Issues in VEHU
1. **`^$GLOBAL` access fails via SimpleAPI**: Raises `INVVARNAME` error
   - Workaround: `02_list_globals.py` falls back to M direct mode or FileMan dictionary
2. **No `.has_value`/`.has_tree` methods**: Older binding version
   - Workaround: Use try/except on `.value` access instead
3. **M prompt noise in subprocess output**: `VEHU>` or `GTM>` prompts appear
   - Workaround: Filter prompt lines in parsing logic

## Assistant Guidance

### When Helping with Code
- Maintain Python 3.6 compatibility (no f-strings with `=`, no `:=` walrus, etc.)
- Keep safety-first philosophy (read-only defaults, allowlists, bounds)
- Explain YottaDB/VistA concepts alongside code
- Reference M language patterns when relevant
- Use type hints (3.6-compatible: `from typing import ...`)

### YottaDB Python Subscript Rules (CRITICAL)
**Always use string subscripts in YottaDB Python code:**

```python
# ✅ CORRECT patterns
key["0"]              # Use string for numeric subscripts
key["NAME"]           # String subscripts
dic[file_num]["0"]    # Keep subscript from .subscripts in original format

# ❌ WRONG patterns - will cause 'subsarray' argument invalid errors
key[0]                # Integer subscript fails
dic[file_num.decode('utf-8')]["0"]  # Decoding before reuse fails in nested access
```

**Rules when iterating subscripts:**
1. Use subscripts from `.subscripts` directly (don't decode first)
2. Only decode subscripts for display/logging purposes
3. Always use string literals for known subscripts: `["0"]`, `["1"]`, `["B"]`
4. See `exercise/ex_02_explore_files.py` for reference pattern

### When Explaining VistA/M
- Provide side-by-side M vs Python comparisons
- Explain FileMan abstractions (files, fields, pointers)
- Show how to use `^DIC` and `^DD` for self-discovery
- Relate concepts to SQL/ORMs when helpful for mental models

### When Recommending Next Steps
- Prioritize learning depth over production features
- Suggest hands-on exercises with concrete outputs
- Encourage exploration of VistA's self-documenting structure
- Defer web UI work until fundamentals are solid

## Useful Reference Commands

### Container Management
```bash
docker compose up -d              # Start VEHU
docker compose ps                 # Check status
docker logs --tail=200 vehu-dev   # View logs
docker exec -it vehu-dev su - vehu -c 'mumps -r ZU'  # VistA roll-and-scroll
docker compose stop/start         # Stop/start without recreating
docker compose down               # Tear down completely
```

### VistA Access
```bash
# SSH (alternative to docker exec)
ssh -p2222 vehutied@localhost

# Direct M programmer mode
docker exec -it vehu-dev su - vehu
# then: mumps -direct
```

## Project History

- **Initial commit**: Basic repo structure
- **Current state**: Three working read-only Python exploration scripts with comprehensive guides
- **Previous work**: Validated YottaDB Python integration in VEHU container, installed build dependencies
- **Documentation**: Operational guides complete, now building learning materials

## Questions to Avoid Assumptions

If unclear during a conversation, ask about:
1. Whether this is for learning exploration vs. production use (likely learning)
2. Whether writes are needed yet (likely not yet)
3. Python version constraints (stay 3.6-compatible)
4. Safety requirements (always maintain guardrails)
