# med-ydb-developer-setup-guide.md

## 🏗️ Project Architecture

The project is structured to separate application logic from database output, mounted into a high-performance **Python 3.11** environment running on top of the **WorldVistA VEHU** image.

```text
med-ydb/
├── cli/                # Python discovery and CLI scripts
├── output/             # Mounted directory for CSV/data exports
├── requirements.txt    # Python dependencies (yottadb, pandas, etc.)
└── docker-compose.yaml # Container orchestration

```

---

## 🐳 Docker Configuration

The following configuration solves the environment variable resolution issues by explicitly mapping the VistA instance paths.

### **docker-compose.yaml**

```yaml
services:
  vista-dev:
    build: .
    container_name: vehu-311
    platform: linux/amd64
    ports:
      - "9000:9000"   # VistA RPC
      - "8010:8010"   # FastAPI / Web
    volumes:
      - ./cli:/opt/med-ydb/cli:ro
      - ./output:/opt/med-ydb/output:rw
    environment:
      # Critical: VEHU instance path mappings
      - ydb_gbldir=/home/vehu/g/vehu.gld
      - ydb_dist=/opt/yottadb/r2.00_x86_64
      - ydb_routines=/opt/med-ydb/cli /home/vehu/r /home/vehu/p /opt/yottadb/r2.00_x86_64/libyottadbutil.so
    entrypoint: >
      /bin/bash -c "source /home/vehu/etc/env && tail -f /dev/null"
    stdin_open: true
    tty: true
    restart: unless-stopped

```

---

## 🛠️ Execution & Discovery

Because the environment variables are defined in the `docker-compose.yaml`, you can run Python scripts directly without manual sourcing.

### **How to Run a Script**

Use the following pattern to execute any discovery or extraction script:

```bash
docker exec -it vehu-311 python3 /opt/med-ydb/cli/ex_02_explore_files.py

```

### **Connection Smoke Test**

Verify the Python-to-YottaDB bridge with this one-liner:

```bash
docker exec -it vehu-311 python3 -c "import yottadb; val = yottadb.get('^DD', ('ROU',)); print('Connected! FileMan Version:', val.decode('utf-8') if val else 'Empty')"

```

---

## 💡 Developer Best Practices

### **1. Type-Safety (Bytes vs. Strings)**

The `yottadb` 2.0.0 wrapper requires subscripts to be **strings** or **bytes**. Using integers will cause a `TypeError`.

* **Wrong**: `yottadb.get("^DPT", (1, 0))`
* **Right**: `yottadb.get("^DPT", ("1", "0"))`

### **2. Handling Sparse Data**

VistA globals are sparse. Always check if a value is `None` before attempting to decode it to avoid `AttributeError`.

```python
val = yottadb.get("^DIC", ("2", "0"))
if val:
    decoded_val = val.decode('utf-8')

```

### **3. Global Traversal**

To iterate through VistA records, use the `subscript_next()` method on the `yottadb.Key` object.

```python
key = yottadb.Key("^DIC")
while True:
    try:
        key = key.subscript_next()
        # Process logic here...
    except yottadb.YDBNodeEnd:
        break

```

---

## 📋 Common Paths (VEHU Instance)

| Variable | Value |
| --- | --- |
| **Global Directory** | `/home/vehu/g/vehu.gld` |
| **YDB Distribution** | `/opt/yottadb/r2.00_x86_64` |
| **Env Source** | `/home/vehu/etc/env` |
