#!/usr/bin/env python3
"""
Phase 1 - Step 3: read-only global exploration with strict allowlist guardrails.

Design goals:
1) Never write/delete.
2) Block non-allowlisted globals before any traversal.
3) Limit breadth with --max-nodes.
4) Keep output human-readable for interactive learning.
"""

import argparse
import sys
from typing import List, Optional

import yottadb
from yottadb import YDBError

# Strict starter allowlist for initial learning.
# Expand this deliberately over time instead of allowing everything.
ALLOWED_GLOBALS = {
    "^DIC",
    "^DPT",
    "^VA",
}


def normalize_global_name(name: str) -> str:
    return name if name.startswith("^") else f"^{name}"


def is_allowed(global_name: str) -> bool:
    # Exact match only, by policy for strictness in early development.
    return global_name in ALLOWED_GLOBALS


def to_display(value: Optional[bytes], raw: bool = False) -> str:
    if value is None:
        return "<no value>"
    if raw:
        return repr(value)
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError:
        return repr(value)


def build_key(global_name: str, subscripts: List[str]) -> yottadb.Key:
    key = yottadb.Key(global_name)
    for sub in subscripts:
        key = key[sub]
    return key


def print_node_value(key: yottadb.Key, raw: bool) -> None:
    try:
        print(f"{key}: {to_display(key.value, raw=raw)}")
    except YDBError as exc:
        print(f"{key}: <error reading value: {exc}>")


def list_children(key: yottadb.Key, max_nodes: int, raw: bool) -> None:
    count = 0
    try:
        for sub in key.subscripts:
            child = key[sub]
            print_node_value(child, raw=raw)
            count += 1
            if count >= max_nodes:
                print(f"... truncated at {max_nodes} child node(s)")
                break
    except YDBError as exc:
        print(f"Error iterating children of {key}: {exc}")
        return

    if count == 0:
        print("<no child nodes>")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only global explorer with strict allowlist."
    )
    parser.add_argument(
        "--global",
        dest="global_name",
        default="^DPT",
        help="Target global name (default: ^DPT).",
    )
    parser.add_argument(
        "--subscript",
        action="append",
        default=[],
        help="Add one subscript level (repeatable).",
    )
    parser.add_argument(
        "--max-nodes",
        type=int,
        default=20,
        help="Maximum child nodes to display (default: 20).",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Show raw byte representations for values.",
    )
    parser.add_argument(
        "--show-release",
        action="store_true",
        help="Print YottaDB release string before exploration.",
    )
    parser.add_argument(
        "--list-allowlist",
        action="store_true",
        help="Print allowed globals and exit.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.list_allowlist:
        print("Allowed globals:")
        for name in sorted(ALLOWED_GLOBALS):
            print(f"- {name}")
        return 0

    global_name = normalize_global_name(args.global_name)
    if not is_allowed(global_name):
        print(
            f"Blocked by allowlist policy: {global_name}\n"
            f"Allowed set: {', '.join(sorted(ALLOWED_GLOBALS))}",
            file=sys.stderr,
        )
        return 2

    if args.show_release:
        try:
            release = yottadb.get("$ZYRELEASE")
            print(f"YottaDB release: {to_display(release, raw=True)}")
        except YDBError as exc:
            print(f"Could not read $ZYRELEASE: {exc}", file=sys.stderr)
            return 1

    root = build_key(global_name, args.subscript)
    max_nodes = max(1, args.max_nodes)

    print("=" * 72)
    print("03_explore_allowlisted.py - read-only global inspection")
    print("=" * 72)
    print(f"Root:       {root}")
    print(f"Guardrails: allowlist + max_nodes={max_nodes} + no writes/deletes")

    print("\nRoot value")
    print_node_value(root, raw=args.raw)

    print("\nChild nodes")
    list_children(root, max_nodes=max_nodes, raw=args.raw)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
