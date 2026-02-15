# -----------------------------------------------------------
# app/01_env)check.py
# -----------------------------------------------------------

"""
Confirm Python + YottaDB runtime context inside VEHU.

This script is intentionally read-only and minimal. It helps you validate:
 1) Python is available in the running container.
 2) The yottadb module imports successfully.
 3) The YottaDB engine is reachable from this process.
 4) A known global can be inspected without writing.

To Run:

# Use default global (^DIC)
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
python3 /opt/med-ydb/app/01_env_check.py'

# Test against patient file (i.e., "probe" the global)
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
python3 /opt/med-ydb/app/01_env_check.py --probe-global ^DPT'

# Can omit the ^ prefix (normalize_global_name adds it)
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
python3 /opt/med-ydb/app/01_env_check.py --probe-global DPT'
"""

import argparse
import platform
import sys
from typing import Optional
import yottadb
from yottadb import YDBError
from constants_config import *


def normalize_global_name(name: str) -> str:
    return name if name.startswith("^") else f"^{name}"


def to_display(value: Optional[bytes]) -> str:
    if value is None:
        return "<no value>"
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError:
        return repr(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate VEHU Python + YottaDB runtime access (read-only)."
    )
    parser.add_argument(
        "--probe-global",
        default="^DIC",
        help="Global to probe with read-only checks (default: ^DIC).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    probe_global = normalize_global_name(args.probe_global)

    print(CYAN)
    print("=" * 72)
    print("01_env_check.py - VEHU runtime sanity check (read-only)")
    print("=" * 72)
    print(f"  Python executable: {sys.executable}")
    print(f"     Python version: {platform.python_version()}")
    print(f"       Probe global: {probe_global}")

    try:
        release = yottadb.get("$ZYRELEASE")
        print(f"    YottaDB release: {to_display(release)}")
    except YDBError as exc:
        print(f"    YottaDB release: <error: {exc}>")
        return 1

    key = yottadb.Key(probe_global)
    try:
        # Compatibility note:
        # Older yottadb Python bindings (like those paired with Python 3.6 in VEHU)
        # may not expose Key.has_value / Key.has_tree. We use read attempts instead.
        root_value = key.value
        print(f"         Root value: {to_display(root_value)}")
    except YDBError as exc:
        print(f"         Root value: <error reading value: {exc}>")
        return 1

    try:
        first_subscript = None
        for sub in key.subscripts:
            first_subscript = sub
            break
        if first_subscript is None:
            print("First child:       <none>")
        else:
            print(f"        First child: {probe_global}({first_subscript!r})")
            child_value = key[first_subscript].value
            print(f"  First child value: {to_display(child_value)}")
    except YDBError as exc:
        print(f"Error reading first child for {probe_global}: {exc}")
        return 1

    print("\n             Status: runtime looks good for read-only exploration.")
    print("=" * 72)
    print(RESET)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
