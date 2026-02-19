# med-ydb

Learning workspace for WorldVistA VEHU + YottaDB Python integration.

## Project Status

Current focus is read-only backend exploration against a running VEHU container, using Python scripts mounted from this repo.

- Runtime target: `worldvista/vehu:202504`
- Container name in current docs/examples: `vehu-dev`
- Host platform assumption: macOS on Apple Silicon (VEHU runs as `linux/amd64` via emulation)

## Primary Goals

1. **Learn YottaDB**: Understand global-based hierarchical database, Python integration patterns
2. **Learn VistA Architecture**: Data structures, FileMan, patient data management
3. **Learn M Language**: Develop reading literacy for VistA MUMPS code
4. **Long-term**: Build modern Python/FastAPI web UI to replace "roll-and-scroll" interface

## Quick Start

### 1. Setup Environment

Use these operational guides in order:

1. `docs/guide/vista-vehu-docker-guide.md` - Docker container setup
2. `docs/guide/yottadb-python-vehu-readonly-lab.md` - Python + YottaDB validation

### 2. Learning Path

For deep learning (recommended for understanding fundamentals):

1. `docs/learn/00-learning-plan.md` - **Start here** - overview and progression
2. `docs/learn/01-yottadb-fundamentals.md` - Database concepts (globals, keys, traversal)
3. `docs/learn/02-fileman-architecture.md` - VistA's data abstraction layer
4. `docs/learn/03-m-language-primer.md` - M language for Python developers
5. `docs/learn/04-vista-patient-data.md` - Patient file (File #2) deep dive
6. `docs/learn/04b-vista-new-person-file.md` - Provider/user file (File #200) deep dive
7. `docs/learn/05-vista-pointers-relations.md` - How files connect via pointers
8. `docs/learn/exercises/ex01-explore-file-2-and-200.md` - Comprehensive hands-on exercise
9. `docs/learn/reference/m-to-python-patterns.md` - Quick lookup while reading M code

## Current Python Exploration Scripts

- `/Users/chuck/swdev/med/med-ydb/app/01_env_check.py`
  - Runtime sanity check (Python + YottaDB + read-only probe)
- `/Users/chuck/swdev/med/med-ydb/app/02_list_globals.py`
  - Global listing with VEHU-compatible fallback paths
- `/Users/chuck/swdev/med/med-ydb/app/03_explore_allowlisted.py`
  - Read-only exploration with strict allowlist and max-node guardrails
- `/Users/chuck/swdev/med/med-ydb/app/sample_01.py`
  - Older experimental script (includes writes/deletes; not default path)
- `/Users/chuck/swdev/med/med-ydb/app/sample_02.py`
  - Earlier read-only sample (superseded by numbered scripts)

## Repository Layout

```text
med-ydb/
├── README.md                    # This file
├── CLAUDE.md                    # Project context for Claude AI sessions
├── docker-compose.yaml          # Container orchestration
├── app/                         # Python scripts (mounted into container)
│   ├── 01_env_check.py         # Runtime sanity check
│   ├── 02_list_globals.py      # Global discovery with fallbacks
│   ├── 03_explore_allowlisted.py  # Safe read-only explorer
│   ├── sample_01.py            # Early experiment (has writes!)
│   └── sample_02.py            # Earlier read-only sample
├── docs/
│   ├── guide/                   # Operational how-to guides
│   │   ├── vista-vehu-docker-guide.md
│   │   ├── yottadb-python-vehu-readonly-lab.md
│   │   ├── vista-first-session-lab.md
│   │   └── ...
│   ├── spec/                    # Reference specs and handoffs
│   │   └── med-ydb-new-thread-handoff.md
│   └── learn/                   # Learning materials (NEW!)
│       ├── 00-learning-plan.md                # Start here - overview
│       ├── 01-yottadb-fundamentals.md         # Database concepts
│       ├── 02-fileman-architecture.md         # FileMan/data dictionary
│       ├── 03-m-language-primer.md            # M language guide
│       ├── 04-vista-patient-data.md           # File #2 (PATIENT)
│       ├── 04b-vista-new-person-file.md       # File #200 (NEW PERSON)
│       ├── 05-vista-pointers-relations.md     # Pointer relationships
│       ├── exercises/
│       │   └── ex01-explore-file-2-and-200.md # Patient & provider exercise
│       └── reference/
│           └── m-to-python-patterns.md        # M to Python quick lookup
└── src/
    └── routines/
        └── HELLO.m              # Sample M routine
```

## Operational Notes

1. Python must run inside VEHU runtime context for YottaDB access.
2. `yottadb` Python package is container-local and must be installed in the container.
3. Current VEHU runtime has Python `3.6.8`; scripts are written for that compatibility level.
4. Read-only defaults are intentional: allowlist + bounded traversal.

## Learning Focus Areas

Current learning priorities (see `docs/learn/00-learning-plan.md` for full plan):

1. **YottaDB Fundamentals**: Global structure, Key objects, traversal patterns
2. **VistA Architecture**: FileMan data dictionary (`^DIC`, `^DD`), self-documenting structure
3. **Core VistA Files**:
   - File #2 (PATIENT): Demographics, identifiers (IEN/DFN/SSN/ICN)
   - File #200 (NEW PERSON): Providers/users, person classes, security keys
4. **Pointer Relationships**: Patient→Provider connections, pointer traversal patterns
5. **M Language**: Reading VistA MUMPS code, common patterns, function translation

## Roadmap

### Near-term (Learning Phase - Current)
- Complete understanding of File #2 (PATIENT) structure
- Map common VistA globals and FileMan files
- Build M language reading literacy
- Create custom exploration scripts as learning exercises

### Medium-term
- Explore other VistA domains (orders, pharmacy, lab)
- Learn write patterns with test globals
- Understand FileMan API for validated updates

### Long-term
- Harden read-only logic into reusable Python modules
- Add minimal FastAPI endpoints with guardrails
- Build HTMX-based web UI for patient data browsing
- Create derived container image with Python dependencies

## Docker Commands

Rebuild and Replace docker image via Docker and docker-compose.yaml
```bash
docker compose up -d --build
```