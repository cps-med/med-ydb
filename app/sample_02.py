# -----------------------------------------------------------
# app/sample_02.py
# -----------------------------------------------------------

"""
Read-only VistA global browser for YottaDB.

Run inside the VEHU container, e.g.:
  . /usr/local/etc/ydb_env_set && python3 /tmp/main.py --global ^DPT --max-nodes 25

This is the read-only version (no writes/deletes).
Quick run example in vehu:

docker cp /tmp/main.py vehu:/tmp/main.py
docker exec -it vehu bash -lc '. /usr/local/etc/ydb_env_set && python3 /tmp/main.py --show-release --global ^DPT --max-nodes 25'

How I run sample_01.py:
docker exec -it yottadb-dev bash -lc '. /usr/local/etc/ydb_env_set && python3 /data/app/your_script.py'
"""

import argparse
import sys

import yottadb
from yottadb import YDBError


def _to_display(value, raw=False):
    if value is None:
        return "<no value>"
    if raw:
        return repr(value)
    try:
        return value.decode("utf-8")
    except Exception:
        return repr(value)


def _normalize_global_name(name):
    return name if name.startswith("^") else f"^{name}"


def _build_key(global_name, subscripts):
    key = yottadb.Key(_normalize_global_name(global_name))
    for sub in subscripts:
        key = key[sub]
    return key


def print_node(key, raw=False):
    try:
        value = key.value
    except YDBError as exc:
        print(f"{key}: <error reading value: {exc}>")
        return
    print(f"{key}: {_to_display(value, raw=raw)}")


def list_children(key, max_nodes=20, raw=False):
    count = 0
    try:
        for subscript in key.subscripts:
            child = key[subscript]
            print_node(child, raw=raw)
            count += 1
            if count >= max_nodes:
                print(f"... truncated at {max_nodes} child node(s)")
                break
    except YDBError as exc:
        print(f"Error iterating children of {key}: {exc}")
        return

    if count == 0:
        print("<no child nodes>")


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Read-only YottaDB global browser")
    parser.add_argument("--global", dest="global_name", default="^DPT", help="Global name (default: ^DPT)")
    parser.add_argument("--subscript", action="append", default=[], help="Add a subscript (repeatable)")
    parser.add_argument("--max-nodes", type=int, default=20, help="Max child nodes to print (default: 20)")
    parser.add_argument("--raw", action="store_true", help="Show raw bytes repr instead of UTF-8 decode")
    parser.add_argument("--show-release", action="store_true", help="Show YottaDB release string")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])

    if args.show_release:
        try:
            release = yottadb.get("$ZYRELEASE")
            print(f"YottaDB release: {_to_display(release, raw=True)}")
        except YDBError as exc:
            print(f"Could not read $ZYRELEASE: {exc}")

    root = _build_key(args.global_name, args.subscript)

    print("=" * 72)
    print("Read-only global inspection")
    print(f"Root: {root}")
    print("Operations: read value + list child nodes only (no writes/deletes)")
    print("=" * 72)

    print("\nRoot value")
    print_node(root, raw=args.raw)

    print("\nChild nodes")
    list_children(root, max_nodes=max(1, args.max_nodes), raw=args.raw)


if __name__ == "__main__":
    main()
