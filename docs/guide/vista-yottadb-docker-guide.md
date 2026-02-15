# YottaDB Docker on macOS Apple Silicon (M4)

## Table of Contents

- [Purpose](#purpose)
- [Prerequisites](#prerequisites)
- [Confirm image architecture support](#confirm-image-architecture-support)
- [Pull image first (recommended)](#pull-image-first-recommended)
- [Run native ARM64 container](#run-native-arm64-container)
- [Choose your container lifecycle mode](#choose-your-container-lifecycle-mode)
- [Recommended bind-mount development workflow](#recommended-bind-mount-development-workflow)
- [Verify container architecture](#verify-container-architecture)
- [When to use amd64 emulation](#when-to-use-amd64-emulation)
- [Write and run M code](#write-and-run-m-code)
- [Optional explicit compile step](#optional-explicit-compile-step)
- [Python workflow and cheat sheet](#python-workflow-and-cheat-sheet)
- [Container management](#container-management)
- [Recommended med-ydb project structure](#recommended-med-ydb-project-structure)
- [References](#references)

## Purpose

This guide provides a practical, developer-focused setup for running **YottaDB natively on Apple Silicon** using Docker Desktop, with a pull-first workflow and a minimal M routine development cycle.

Reviewed: 2026-02-13

## Prerequisites

1. Install Docker Desktop for Mac (Apple Silicon).
2. Start Docker Desktop and verify Docker works:

```bash
docker version
docker info
```

## Confirm image architecture support

Check the manifest list for the image you plan to run:

```bash
docker buildx imagetools inspect download.yottadb.com/yottadb/yottadb-debian:latest
```

If output includes `Platform: linux/arm64`, you can run natively on M4 (recommended).

## Pull image first (recommended)

Pull explicitly before running so download/auth issues are found early:

```bash
docker pull --platform linux/arm64 download.yottadb.com/yottadb/yottadb-debian:latest
```

Notes:
- `docker run` can auto-pull, but explicit `docker pull` is often clearer for onboarding docs.
- For team reproducibility, pin to a specific tag or digest once validated.

## Run native ARM64 container

Create persistent host directories for database, M routines, and Python code:

```bash
mkdir -p "$PWD/ydb-data" "$PWD/src/routines" "$PWD/app"
```

Start an interactive development container:

```bash
docker run --rm -it \
  --name yottadb-dev \
  --platform linux/arm64 \
  -v "$PWD/ydb-data:/data" \
  -v "$PWD/src/routines:/data/r" \
  -v "$PWD/app:/data/app" \
  download.yottadb.com/yottadb/yottadb-debian:latest
```

## Choose your container lifecycle mode

Use one of these two modes based on how you work:

- Ephemeral container (`--rm`): good for temporary sessions. Container is removed when it stops.
- Reusable container (no `--rm`): preferred if you use Docker Desktop Start/Stop buttons and want the same container to persist.

Reusable mode example:

```bash
docker run -d \
  --name yottadb-dev \
  --platform linux/arm64 \
  --entrypoint /bin/bash \
  -v "$PWD/ydb-data:/data" \
  -v "$PWD/src/routines:/data/r" \
  -v "$PWD/app:/data/app" \
  download.yottadb.com/yottadb/yottadb-debian:latest \
  -lc 'sleep infinity'
```

## Recommended bind-mount development workflow

For source-controlled development, keep routines in your host project and mount them into the container.

From your project root (`~/swdev/med/med-ydb`):

```bash
mkdir -p "$PWD/src/routines" "$PWD/app" "$PWD/ydb-data"

docker run -d \
  --name yottadb-dev \
  --platform linux/arm64 \
  --entrypoint /bin/bash \
  -v "$PWD/ydb-data:/data" \
  -v "$PWD/src/routines:/data/r" \
  -v "$PWD/app:/data/app" \
  download.yottadb.com/yottadb/yottadb-debian:latest \
  -lc 'sleep infinity'
```

With this setup:
- Edit `.m` files locally in `src/routines/` with your normal editor.
- Edit Python scripts locally in `app/`.
- Run code with `docker exec` commands.
- Avoid manual `docker cp` for normal development.

## Verify container architecture

From the host, verify container architecture:

```bash
docker exec -it yottadb-dev uname -m
```

Expected result for native Apple Silicon: `aarch64`

Also verify YottaDB is available:

```bash
docker exec -it yottadb-dev /usr/local/bin/ydb -version
```

If you prefer calling `yottadb` directly, initialize the YottaDB environment first:

```bash
docker exec -it yottadb-dev bash -lc '. /usr/local/etc/ydb_env_set && yottadb -version'
```

## When to use amd64 emulation

Use `--platform linux/amd64` only when:
- A required image/tag does not provide `linux/arm64`, or
- You must match amd64 behavior for compatibility testing.

On Apple Silicon, amd64 emulation works but is typically slower than native arm64.

## Write and run M code

Using the bind-mount workflow, create a routine on the host:

```bash
cat > "$PWD/src/routines/HELLO.m" <<'EOF'
HELLO ;
  WRITE "Hello from YottaDB on ARM64!",!
  QUIT
EOF
```

Run it from the host via Docker exec:
```bash
docker exec -it yottadb-dev bash -lc '. /usr/local/etc/ydb_env_set && yottadb -run HELLO'
```

Or use the wrapper command:
```bash
docker exec -it yottadb-dev /usr/local/bin/ydb -run HELLO
```

Expected behavior:
- YottaDB resolves/loads routine code from routine paths.
- Routine compile/link is generally handled automatically during execution (no separate mandatory compile step for normal development).


Recommended default for day-to-day use:

```bash
docker exec -it yottadb-dev /usr/local/bin/ydb -run HELLO
```
This is shorter, clearer, and consistently initializes the environment.

## Optional explicit compile step

If you want to compile directly:

```bash
docker exec -it yottadb-dev bash -lc '$ydb_dist/mumps /data/r/HELLO.m'
```

Then run again:

```bash
docker exec -it yottadb-dev /usr/local/bin/ydb -run HELLO
```

## Python workflow and cheat sheet

For this project, run Python inside the container (not host `.venv`) so Python and YottaDB share one runtime context.

Check Python and pip availability:

```bash
docker exec -it yottadb-dev bash -lc 'python3 --version && python3 -m pip --version'
```

Run a Python script from `app/`:

```bash
docker exec -it yottadb-dev bash -lc '. /usr/local/etc/ydb_env_set && python3 /data/app/your_script.py'
```

Install Python dependencies in the running container:

```bash
docker exec -it yottadb-dev bash -lc 'python3 -m pip install <package>'
```

For example:
```bash
docker exec -it yottadb-dev bash -lc 'python3 -m pip install yottadb'
```

Install from requirements file in your project:

```bash
docker exec -it yottadb-dev bash -lc 'python3 -m pip install -r /data/app/requirements.txt'
```

Notes:
- Package installs done this way persist only as long as the container exists.
- If you recreate the container often, prefer a `Dockerfile` that installs Python dependencies during build.

## Container management

Run detached instead of interactive:

```bash
docker run -d \
  --name yottadb-dev \
  --platform linux/arm64 \
  --entrypoint /bin/bash \
  -v "$PWD/ydb-data:/data" \
  -v "$PWD/src/routines:/data/r" \
  -v "$PWD/app:/data/app" \
  download.yottadb.com/yottadb/yottadb-debian:latest \
  -lc 'sleep infinity'
```

Open a shell in that running container:

```bash
docker exec -it yottadb-dev bash
```

Stop and remove:

```bash
docker stop yottadb-dev
docker rm yottadb-dev
```

**Note:** Use -f when you want one command that works whether container is running or not.
If running, Docker sends kill/stop and then removes it.

Force-remove a container:
```bash
docker rm -f yottadb-dev
```

If `docker exec` reports that the container is not running, check:

```bash
docker ps -a --filter name=yottadb-dev
docker logs --tail=100 yottadb-dev
```

You can also verify Docker context alignment with Docker Desktop:

```bash
docker context show
docker context ls
```

## Recommended med-ydb project structure

If your GitHub repository is named `med-ydb`, use the same local folder name for consistency:

```text
~/swdev/med/med-ydb
```

Suggested starter layout:

```text
~/swdev/med/med-ydb/
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

Folder intent:
- `src/routines/`: primary `.m` routines for application code.
- `src/libraries/`: reusable utility routines.
- `src/apps/`: small app entry points or grouped app modules.
- `tests/routines/`: test routines and regression checks.
- `scripts/`: repeatable development commands.
- `ydb-data/`: persistent container-mounted data for local development.
- `app/`: Python scripts that interact with YottaDB.

Recommended `.gitignore` baseline:

```gitignore
ydb-data/
.env
.DS_Store
```

Practical learning workflow:
1. Create routines in `src/routines/`.
2. Run with `docker exec -it yottadb-dev /usr/local/bin/ydb -run ROUTINENAME`.
3. Create Python scripts in `app/` and run via `docker exec ... python3 /data/app/...`.
4. Add tests in `tests/routines/` as features grow.

## References

- YottaDB Get Started (Docker section): <https://yottadb.com/product/get-started/#a-docker-container>
- YottaDB container docs: <https://docs.yottadb.com/AdminOpsGuide/containers.html>
- YottaDB development cycle: <https://docs.yottadb.com/ProgrammersGuide/devcycle.html>
- Docker multi-platform docs: <https://docs.docker.com/build/building/multi-platform/>
