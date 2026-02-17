# -----------------------------------------------------------
# cli/07_security_explorer.py
# -----------------------------------------------------------

"""
Security-first, read-only VistA global explorer.

Design goals:
1) Read-only operations only.
2) Explicit allowlist enforcement.
3) Bounded traversal.
4) PHI redaction by default.
5) Explicit opt-in flag for unredacted output.

To run:
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
python3 /opt/med-ydb/app/05_security_explorer.py --global ^DPT --max-nodes 10'
"""

import argparse
import sys
from typing import List, Optional

import yottadb
from yottadb import YDBError

from constants_config import *


ALLOWED_GLOBALS = {
    "^DIC",
    "^DPT",
    "^VA",
    "^XWB",
}

SENSITIVE_GLOBALS = {
    "^DPT",
    "^VA",
}


def normalize_global_name(name: str) -> str:
    return name if name.startswith("^") else f"^{name}"


def as_text(value: Optional[bytes], raw: bool = False) -> str:
    if value is None:
        return "<no value>"
    if raw:
        return repr(value)
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError:
        return repr(value)


def redact_text(text: str) -> str:
    pieces = text.count("^") + 1 if text else 0
    return "<redacted: {0} chars, {1} piece(s)>".format(len(text), pieces)


def safe_display(
    value: Optional[bytes],
    global_name: str,
    include_phi: bool,
    raw: bool = False,
) -> str:
    text = as_text(value, raw=raw)
    if include_phi:
        return text
    if global_name in SENSITIVE_GLOBALS and text not in ("<no value>",):
        return redact_text(text)
    return text


def build_key(global_name: str, subscripts: List[str]) -> yottadb.Key:
    key = yottadb.Key(global_name)
    for sub in subscripts:
        key = key[sub]
    return key


def print_node_value(
    key: yottadb.Key,
    global_name: str,
    include_phi: bool,
    raw: bool,
) -> None:
    try:
        print(
            "{0}: {1}".format(
                key, safe_display(key.value, global_name, include_phi, raw=raw)
            )
        )
    except YDBError as exc:
        print(f"{key}: <error reading value: {exc}>")


def list_children(
    key: yottadb.Key,
    global_name: str,
    max_nodes: int,
    include_phi: bool,
    raw: bool,
) -> None:
    count = 0
    try:
        for sub in key.subscripts:
            child = key[sub]
            print_node_value(
                child,
                global_name=global_name,
                include_phi=include_phi,
                raw=raw,
            )
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
        description="Security-first read-only global explorer."
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
        help="Show raw byte representations.",
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
    parser.add_argument(
        "--include-phi",
        action="store_true",
        help="Display unredacted values for sensitive globals (unsafe for logs/screens).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print(YELLOW)

    if args.list_allowlist:
        print("Allowed globals:")
        for name in sorted(ALLOWED_GLOBALS):
            print(f"- {name}")
        print(RESET)
        return 0

    global_name = normalize_global_name(args.global_name)
    if global_name not in ALLOWED_GLOBALS:
        print(
            f"Blocked by allowlist policy: {global_name}\n"
            f"Allowed set: {', '.join(sorted(ALLOWED_GLOBALS))}",
            file=sys.stderr,
        )
        print(RESET)
        return 2

    if args.show_release:
        try:
            release = yottadb.get("$ZYRELEASE")
            print(f"YottaDB release: {as_text(release, raw=True)}")
        except YDBError as exc:
            print(f"Could not read $ZYRELEASE: {exc}", file=sys.stderr)
            print(RESET)
            return 1

    if args.include_phi:
        print(
            "WARNING: --include-phi enabled. Output may contain sensitive patient/user data.",
            file=sys.stderr,
        )

    root = build_key(global_name, args.subscript)
    max_nodes = max(1, args.max_nodes)

    print("=" * 72)
    print("05_security_explorer.py - security-first read-only inspection")
    print("=" * 72)
    print(f"Root:       {root}")
    print(
        "Guardrails: allowlist + max_nodes={0} + no writes/deletes + redact={1}".format(
            max_nodes, "off" if args.include_phi else "on"
        )
    )

    print("\nRoot value")
    print_node_value(
        root,
        global_name=global_name,
        include_phi=args.include_phi,
        raw=args.raw,
    )

    print("\nChild nodes")
    list_children(
        root,
        global_name=global_name,
        max_nodes=max_nodes,
        include_phi=args.include_phi,
        raw=args.raw,
    )

    print("=" * 72)
    print(RESET)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

