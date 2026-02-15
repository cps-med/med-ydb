# med-ydb New Thread Handoff

## Scope
- New working repo: `/Users/chuck/swdev/med/med-ydb`
- Goal: build Python-based read access to WorldVistA VEHU globals via YottaDB, then evolve into a web UI/API layer.

## Current Docker State (`docker ps`)

```text
CONTAINER ID   IMAGE                                                COMMAND                  CREATED        STATUS         PORTS                                                                                                                                                                                                                         NAMES
e5a4fb3f2735   download.yottadb.com/yottadb/yottadb-debian:latest   "/bin/bash -lc 'slee…"   25 hours ago   Up 8 hours     1337/tcp, 9080/tcp                                                                                                                                                                                                            yottadb-dev
0f5fec992e80   worldvista/vehu:202504                               "/bin/sh -c ${entry_…"   43 hours ago   Up 4 hours     0.0.0.0:5001->5001/tcp, [::]:5001->5001/tcp, 0.0.0.0:8001->8001/tcp, [::]:8001->8001/tcp, 0.0.0.0:8080->8080/tcp, [::]:8080->8080/tcp, 0.0.0.0:9430->9430/tcp, [::]:9430->9430/tcp, 0.0.0.0:2222->22/tcp, [::]:2222->22/tcp   vehu
191902d4f54c   postgres:16                                          "docker-entrypoint.s…"   2 months ago   Up 8 seconds   0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp                                                                                                                                                                                   postgres16
fb5566fd5f6b   quay.io/minio/minio                                  "/usr/bin/docker-ent…"   3 months ago   Up 7 seconds   0.0.0.0:9000-9001->9000-9001/tcp, [::]:9000-9001->9000-9001/tcp                                                                                                                                                               med-insight-minio
8b3dcb74dde1   mcr.microsoft.com/mssql/server:2019-latest           "/opt/mssql/bin/perm…"   3 months ago   Up 9 seconds   0.0.0.0:1433->1433/tcp, [::]:1433->1433/tcp                                                                                                                                                                                   sqlserver2019
```

## Key Technical Conclusion
- `yottadb` Python module is in-process/local to the runtime where YottaDB libs + globals are present.
- Therefore, to access VEHU globals, Python should run in the `vehu` container (or an equivalent runtime sharing VEHU YottaDB env/files), not in separate `yottadb-dev` by default.

## What Was Validated in Prior Thread
1. Your script at `/Users/chuck/swdev/med/med-ydb/app/main.py` was reviewed.
2. `vehu` has YottaDB runtime and env script: `/usr/local/etc/ydb_env_set`.
3. `vehu` initially lacked Python build prereqs for `pip install yottadb`.
4. Installed inside `vehu`:
   - `python3-devel`
   - `libffi-devel`
   - `gcc`
   - `make`
5. Installed Python package in `vehu` with env sourced:
   - `. /usr/local/etc/ydb_env_set && python3 -m pip install --user yottadb`
6. Script execution in `vehu` succeeded after install.

## Working Command Pattern (VEHU)

```bash
# Copy script into VEHU container
docker cp /Users/chuck/swdev/med/med-ydb/app/main.py vehu:/tmp/med-ydb-main.py

# Run against VEHU globals
docker exec -it vehu bash -lc '. /usr/local/etc/ydb_env_set && python3 /tmp/med-ydb-main.py'
```

## Read-Only Script Version Prepared
- A read-only sample script was created at `/tmp/main.py`.
- It performs value reads + child traversal only (no writes/deletes).
- Example run:

```bash
docker cp /tmp/main.py vehu:/tmp/main.py
docker exec -it vehu bash -lc '. /usr/local/etc/ydb_env_set && python3 /tmp/main.py --show-release --global ^DPT --max-nodes 25'
```

## Recommended Immediate Tasks in New Thread
1. Move read-only logic into `/Users/chuck/swdev/med/med-ydb` (source-controlled).
2. Add a small FastAPI app with read-only endpoints, e.g.:
   - `GET /health`
   - `GET /globals/{name}`
   - `GET /globals/{name}/children?subscript=...&limit=...`
3. Add guardrails:
   - default read-only mode
   - max-node limits
   - explicit allowlist of globals for initial development
4. Add containerized dev workflow (likely `docker-compose.yml`) so app + runtime are reproducible.

## Notes / Constraints
- VEHU image is `linux/amd64`; Mac M4 runs it under emulation.
- Container-local package installs are ephemeral if container is recreated; consider creating a derived image or startup bootstrap script.
- Avoid write/delete operations on production-like VistA globals until explicitly needed.

## Request to Assistant in New Thread
- Work directly in `/Users/chuck/swdev/med/med-ydb`.
- Implement a read-only YottaDB explorer service and wire it to FastAPI.
- Keep first iteration small, testable, and safe.
