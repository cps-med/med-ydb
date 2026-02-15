# WorldVistA VEHU Docker Guide (macOS + Apple Silicon)

This guide is the current, practical workflow for this repo.

- Reviewed: 2026-02-14
- Primary goal: run VEHU once, then execute local Python scripts inside VEHU without `docker cp`
- Primary method: `docker compose` with bind mounts

## Why this workflow

YottaDB Python integration is in-process. Python must run in the same runtime context as the VEHU YottaDB environment and data.

In this repo, local code is mounted into the VEHU container at:

- `/opt/med-ydb/app`
- `/opt/med-ydb/docs`
- `/opt/med-ydb/src`
- `/opt/med-ydb/tests`

This removes the copy loop and keeps your code under version control on the host.

## Prerequisites

1. Docker Desktop is installed and running.
2. You are in repo root:
   - `/Users/chuck/swdev/med/med-ydb`

Optional checks:

```bash
docker version
docker compose version
```

## Compose file location

The project compose file is in the repo root:

- `/Users/chuck/swdev/med/med-ydb/docker-compose.yaml`

## Start VEHU with Compose

From repo root:

```bash
docker compose up -d
```

Check status:

```bash
docker compose ps
docker logs --tail=200 vehu-dev
```

Stop/start:

```bash
docker compose stop
docker compose start
```

Tear down:

```bash
docker compose down
```

## Run VistA roll-and-scroll

```bash
docker exec -it vehu-dev su - vehu -c 'mumps -r ZU'
```

SSH fallback:

```bash
ssh -p2222 vehutied@localhost
```

## Run local Python scripts inside VEHU (no copy step)

Example:

```bash
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && python3 /opt/med-ydb/app/sample_02.py --show-release --global ^DPT --max-nodes 25'
```

Because `./app` is bind-mounted into `/opt/med-ydb/app`, edits you make locally are immediately visible in the container.

## First-time Python dependency install in VEHU

If `yottadb` is not yet installed inside this VEHU container:

```bash
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && python3 -m pip install --user yottadb'
```

Notes:

- This install is container-local.
- If you remove/recreate container, reinstall unless you later build a custom image.

## Safety notes for exploration scripts

1. Keep scripts read-only by default.
2. Add a strict allowlist for globals.
3. Enforce `--max-nodes` limits when traversing children.
4. Avoid write/delete operations until explicitly required.

## Ports exposed by compose in this repo

- `2222` -> SSH
- `5001` -> HL7 listener
- `8001` -> VEHU service
- `8080` -> VEHU web/FHIR-related endpoint (depends on image config)
- `9430` -> VEHU service

## Architecture notes (important on M-series Macs)

- `worldvista/vehu:202504` is `linux/amd64`.
- Apple Silicon runs this through emulation (`platform: linux/amd64`).
- This is expected and typically slower than native arm64 images.

## Legacy/reference notes

- Older docs often used `docker run ... --link ...`; `--link` is legacy and should be avoided.
- Older docs also referenced Docker Toolbox and older host networking guidance; those do not apply to modern Docker Desktop on macOS.

## Working docker run script

docker run -d \
  --platform linux/amd64 \
  --name vehu-dev \
  -p 2222:22 \
  -p 8001:8001 \
  -p 8080:8080 \
  -p 9430:9430 \
  -p 5001:5001 \
  -v "$PWD/app:/opt/med-ydb/app:ro" \
  -v "$PWD/docs:/opt/med-ydb/docs:ro" \
  -v "$PWD/exercise:/opt/med-ydb/exercise:ro" \
  worldvista/vehu:202504

## February 15, 2026 notes

To add the exercise/ directory to your docker run command, simply add another -v (volume mount) line. Here's your updated command:

  docker run -d \
    --platform linux/amd64 \
    --name vehu-dev \
    -p 2222:22 \
    -p 8001:8001 \
    -p 8080:8080 \
    -p 9430:9430 \
    -p 5001:5001 \
    -v "$PWD/app:/opt/med-ydb/app:ro" \
    -v "$PWD/docs:/opt/med-ydb/docs:ro" \
    -v "$PWD/exercise:/opt/med-ydb/exercise:ro" \
    worldvista/vehu:202504

  Steps to Apply

  1. Create the exercise/ directory (if it doesn't exist yet):
  mkdir exercise
  2. Stop and remove the existing container:
  docker stop vehu-dev
  docker rm vehu-dev
  3. Run the updated docker command (shown above)
  4. Verify the mount worked:
  docker exec -it vehu-dev ls -la /opt/med-ydb/

  4. You should see exercise/ listed alongside app/ and docs/

  Running Scripts from exercise/

  Your scripts in exercise/ will follow the same pattern as app/:

  docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && python3 /opt/med-ydb/exercise/my_learning_script.py'

  The :ro (read-only) flag keeps your safety-first philosophy, ensuring the container can't accidentally modify your host files.