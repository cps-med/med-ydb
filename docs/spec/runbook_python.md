# Python Runbook

Cheetsheet & Convenience Guide

## /app

### 01_env_check.py

```bash
# Use default global (^DIC)
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
python3 /opt/med-ydb/app/01_env_check.py'

# Test against patient file (i.e., "probe" the global)
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
python3 /opt/med-ydb/app/01_env_check.py --probe-global ^DPT'

# Can omit the ^ prefix (normalize_global_name adds it)
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
python3 /opt/med-ydb/app/01_env_check.py --probe-global DPT'
```

### 02_list_globals.py

```bash
# With a couple arguments
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
python3 /opt/med-ydb/app/02_list_globals.py --prefix ^DPT --limit 10'
```

## /exercise

### ex_01_1_isv.py

```bash
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
python3 /opt/med-ydb/exercise/ex_01_1_isv.py'
```
