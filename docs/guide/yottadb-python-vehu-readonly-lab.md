# YottaDB Python Read-Only Lab (VEHU, Compose Workflow)

Reviewed: 2026-02-14

This runbook is a practical, repeatable startup guide for Python + YottaDB read-only exploration against VEHU.

## Scope

- Repo root: `/Users/chuck/swdev/med/med-ydb`
- Runtime container: `vehu-dev`
- Scripts:
  - `/Users/chuck/swdev/med/med-ydb/app/01_env_check.py`
  - `/Users/chuck/swdev/med/med-ydb/app/02_list_globals.py`
  - `/Users/chuck/swdev/med/med-ydb/app/03_explore_allowlisted.py`
- Mode: read-only by default

## Why this workflow

YottaDB Python access is in-process. Python must run in the same runtime context as VEHU's YottaDB environment and data.

Local scripts are bind-mounted into the container, so no `docker cp` step is required.

## Prerequisites

1. Docker Desktop is running.
2. VEHU container exists and is running as `vehu-dev`.
3. Local repo has bind mounts configured to `/opt/med-ydb/...` in container.

Quick check:

```bash
cd /Users/chuck/swdev/med/med-ydb
docker ps --filter "name=vehu-dev"
```

## Step 0 - Install Python build dependencies (one-time per container)

Concept:
- `yottadb` Python package builds a native extension.
- You need Python headers and compiler toolchain inside VEHU.

Command:

```bash
docker exec -it vehu-dev bash -lc 'yum install -y python3-devel gcc make libffi-devel'
```

## Step 1 - Install Python `yottadb` package (one-time per container)

Concept:
- Install inside container so VEHU Python can import it.
- Container recreation requires reinstall unless you later use a custom image.

**Note:** Also installing pandas

Command:

```bash
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && python3 -m pip install --user yottadb pandas'

docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && pip3 list'
```

## Step 2 - Run environment sanity check

Concept:
- Confirm Python runtime, YottaDB release access, and a read-only global probe.
- `01_env_check.py` is updated for Python 3.6 compatibility in VEHU.

Command:

```bash
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && python3 /opt/med-ydb/app/01_env_check.py --probe-global ^DIC'
```

Expected pattern:
- Python version prints
- YottaDB release prints
- First child under probe global is readable
- Script exits with success message

## Step 3 - List available globals

Concept:
- Some VEHU bindings reject direct `^$GLOBAL` access via SimpleAPI.
- `02_list_globals.py` has two fallbacks:
  1. read-only `mumps -direct` query
  2. FileMan data dictionary fallback using `^DIC(file#,0,"GL")`

Command examples:

```bash
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && python3 /opt/med-ydb/app/02_list_globals.py --limit 50'
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && python3 /opt/med-ydb/app/02_list_globals.py --prefix ^D --limit 50'
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && python3 /opt/med-ydb/app/02_list_globals.py --prefix ^VA --limit 50'
```

Expected pattern:
- If SimpleAPI fails on `^$GLOBAL`, script prints fallback notice.
- Script still returns usable global roots from fallback logic.

## Step 4 - Explore with strict allowlist

Concept:
- Safety is policy + code checks.
- `03_explore_allowlisted.py` blocks non-allowlisted globals before traversal.

Current starter allowlist:
- `^DIC`
- `^DPT`
- `^VA`

Commands:

```bash
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && python3 /opt/med-ydb/app/03_explore_allowlisted.py --list-allowlist'
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && python3 /opt/med-ydb/app/03_explore_allowlisted.py --show-release --global ^DPT --max-nodes 20'
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && python3 /opt/med-ydb/app/03_explore_allowlisted.py --global ^DIC --subscript 4 --max-nodes 15'
```

Negative test (expected policy block):

```bash
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && python3 /opt/med-ydb/app/03_explore_allowlisted.py --global ^AUPNPAT --max-nodes 5'
```

## Step 5 - Edit locally and rerun immediately

Local file path:
- `/Users/chuck/swdev/med/med-ydb/app/*.py`

Container path:
- `/opt/med-ydb/app/*.py`

Because of bind mounts, local edits are available in container without copy.

## Troubleshooting

1. `ModuleNotFoundError: No module named 'yottadb'`
- Run Step 0 and Step 1.

2. `fatal error: Python.h: No such file or directory` during pip install
- Missing `python3-devel`; run Step 0.

3. `SyntaxError: future feature annotations is not defined`
- Indicates script version mismatch. Pull latest scripts from this repo.

4. `AttributeError: 'Key' object has no attribute ...`
- VEHU Python binding is older. Use current repo versions of scripts (they contain compatibility fixes).

5. `INVVARNAME` on `^$GLOBAL`
- Expected in this environment; script handles this via fallback.

6. Prompt noise like `VEHU>` during fallback listing
- Informational only; current script filters prompt lines.

7. `No such container: vehu-dev`
- Start or recreate the container, then retry.

## Notes for future maintainers

1. VEHU currently runs Python `3.6.8` in this setup.
2. Keep script syntax compatible with Python 3.6 unless runtime changes.
3. Container-local dependency installs are ephemeral.
4. If this environment becomes long-lived, create a derived image with dependencies preinstalled.

## Next milestone

After this runbook, next step is to wrap the same read-only patterns into FastAPI endpoints while preserving:

1. strict allowlist checks
2. max-node limits
3. default read-only behavior

## Appendix A - Future Upgrade Path to Python 3.10+

This appendix is for future planning. It is not required for current lab steps.

### Why consider upgrading later

Potential long-term advantages:

1. Access to modern Python language features and typing improvements.
2. Better support window for libraries and tooling.
3. Cleaner script code (fewer Python 3.6 compatibility workarounds).
4. Better foundation for FastAPI ecosystem versions over time.

### Why defer for now

Current tradeoffs in this VEHU environment:

1. VEHU image is appliance-like; replacing base Python can break assumptions.
2. `yottadb` Python package includes native extension build concerns.
3. Added maintenance burden if custom runtime diverges from stock VEHU.

### Upgrade options

Option 1 (recommended): build a derived VEHU image with Python 3.10 alongside system Python.

- Keep existing `/usr/bin/python3` untouched.
- Install `python3.10` as an additional interpreter.
- Install `yottadb` using `python3.10 -m pip`.
- Run project scripts explicitly with `python3.10`.

Option 2 (not recommended early): in-place modification of a running container.

- Fast to test once.
- Not reproducible.
- Lost when container is recreated.

Option 3 (later): complete migration to a newer VEHU/base image if upstream supports newer Python.

- Lowest long-term maintenance if available.
- Depends on upstream image choices.

### Recommended future implementation steps (Option 1)

1. Create a `Dockerfile` based on `worldvista/vehu:202504`.
2. Install Python 3.10 runtime + dev headers + build tools.
3. Install `pip` for Python 3.10.
4. Install `yottadb` with Python 3.10 while YottaDB env is active.
5. Add smoke test command in build or startup:
   - import `yottadb`
   - print `$ZYRELEASE`
6. Update compose to build/use derived image.
7. Keep an explicit script runner command:
   - `. /usr/local/etc/ydb_env_set && python3.10 /opt/med-ydb/app/...`

### Validation checklist after upgrade

1. `python3.10 --version` works in container.
2. `python3.10 -c "import yottadb"` succeeds.
3. `01_env_check.py` passes with `python3.10`.
4. `02_list_globals.py` fallback behavior still works.
5. `03_explore_allowlisted.py` policy behavior is unchanged.
6. VistA roll-and-scroll startup (`mumps -r ZU`) remains unaffected.

### Rollback strategy

1. Keep current `worldvista/vehu:202504` compose path available.
2. If issues appear, switch compose back to stock image and restart container.
3. Continue running scripts with stock Python 3.6 path until upgrade branch is stable.
