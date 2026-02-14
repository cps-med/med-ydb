# med-ydb
YottaDB / M Language Learning and Experimentation

## Goals

- Learn core M language syntax and patterns
- Build small routines and sample applications
- Practice working with globals and persistent data
- Maintain reproducible local development via Docker

## Project Layout

```text
med-ydb/
├── README.md
├── .gitignore
├── docker-compose.yml
├── .env.example
├── app/
│   ├── python_scripts.py
├── docs/
│   ├── getting-started.md
│   ├── m-language-notes.md
│   └── experiments-log.md
├── src/
│   ├── routines/
│   ├── libraries/
│   └── apps/
├── tests/
│   └── routines/
├── scripts/
│   ├── run.sh
│   ├── shell.sh
│   └── reset-data.sh
└── ydb-data/
```

## Prerequisites

- Docker Desktop for Mac
- Apple Silicon Mac (M1/M2/M3/M4)

## Pull YottaDB Image (ARM64)

```bash
docker pull --platform linux/arm64 download.yottadb.com/yottadb/yottadb-debian:latest
```

## Run YottaDB Container

```bash
mkdir -p "$PWD/ydb-data"

docker run --rm -it \
  --name yottadb-dev \
  --platform linux/arm64 \
  -v "$PWD/ydb-data:/data" \
  download.yottadb.com/yottadb/yottadb-debian:latest
```

## Verify Native ARM64 Runtime

Inside the container:

```bash
uname -m
```

Expected: `aarch64`

## First M Routine

Inside the container:

```bash
mkdir -p /data/r
cat > /data/r/HELLO.m <<'EOF'
HELLO ;
  WRITE "Hello from med-ydb!",!
  QUIT
EOF
```

Run:

```bash
yottadb -run HELLO
```

## Compile Behavior

For normal development, YottaDB generally compiles/links routines as needed when run.  
Optional explicit compile:

```bash
$ydb_dist/mumps /data/r/HELLO.m
```

## Development Notes

- Keep reusable routines in `src/libraries/`
- Keep app entry routines in `src/apps/`
- Keep disposable experiments in `examples/`
- Add regression checks under `tests/routines/`
- Treat `ydb-data/` as local runtime data (not source code)

## Suggested .gitignore

```gitignore
ydb-data/
.env
.DS_Store
```

## Recommended Dev Workflow (Bind Mounts)

Run from project root (`~/swdev/med/med-ydb`):

```bash
mkdir -p "$PWD/src/routines" "$PWD/ydb-data"

docker run -d \
docker run -d \
  --name yottadb-dev \
  --platform linux/arm64 \
  --entrypoint /bin/bash \
  -v "$PWD/ydb-data:/data" \
  -v "$PWD/src/routines:/data/r" \
  download.yottadb.com/yottadb/yottadb-debian:latest \
  -lc 'sleep infinity'
```

Why this pattern:
- Source code stays on host in git (`src/routines`)
- Runtime/persistent data stays in `ydb-data` (gitignored)
- No manual `docker cp` loop

## Container Lifecycle Note

- Use **no `--rm`** for reusable containers you manage with Docker Desktop Start/Stop.
- Use `--rm` only for temporary one-off sessions.

## Verify Native ARM64 Runtime

```bash
docker exec -it yottadb-dev uname -m
```

Expected: `aarch64`

Check YottaDB:

```bash
docker exec -it yottadb-dev yottadb -version
```

## First M Routine

Create on host:

```bash
cat > "$PWD/src/routines/HELLO.m" <<'EOF'
HELLO ;
  WRITE "Hello from med-ydb!",!
  QUIT
EOF
```

Run from host via container:

```bash
docker exec -it yottadb-dev yottadb -run HELLO
```

## Compile Behavior

For normal development, YottaDB typically compiles/links routines as needed when run.

Optional explicit compile:

```bash
docker exec -it yottadb-dev bash -lc '$ydb_dist/mumps /data/r/HELLO.m'
```

## Common Commands

Open shell:

```bash
docker exec -it yottadb-dev bash
```

Stop/start:

```bash
docker stop yottadb-dev
docker start yottadb-dev
```

Remove container:

```bash
docker rm -f yottadb-dev
```
