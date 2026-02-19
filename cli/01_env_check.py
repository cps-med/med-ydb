# -----------------------------------------------------------
# cli/01_env_check.py
# -----------------------------------------------------------
# Confirm Python + YottaDB runtime context inside vehu-311
# -----------------------------------------------------------

"""
# Use default global (^DIC)
docker exec -it vehu-311 python3 /opt/med-ydb/cli/01_env_check.py

# Test against patient file (i.e., "probe" the global)
docker exec -it vehu-311 python3 /opt/med-ydb/cli/01_env_check.py --probe-global ^DPT

# Can omit the ^ prefix (normalize_global_name adds it)
docker exec -it vehu-311 python3 /opt/med-ydb/cli/01_env_check.py --probe-global DPT
"""

import os
import argparse
import platform
import sys
from itertools import islice
from typing import Optional, List, Any
import yottadb
from yottadb import YDBError
from constants_config import *

def parse_args() -> argparse.Namespace:
    """
    Parses command-line arguments for the VEHU YottaDB validation utility.

    Returns:
        argparse.Namespace: An object containing the parsed arguments, 
            specifically the global name to be probed.
    """
    parser = argparse.ArgumentParser(
        description="Validate VEHU Python + YottaDB runtime access (read-only)."
    )
    parser.add_argument(
        "--probe-global",
        default="^DIC",
        help="Global to probe with read-only checks (default: ^DIC).",
    )
    return parser.parse_args()

def normalize_global_name(name: str) -> str:
    """
    Normalizes a global name by ensuring that it is formatted as "^{name}"

    Returns:
        str: A properly formatted global name.
    """
    return name if name.startswith("^") else f"^{name}"

def to_display(value: Optional[bytes]) -> str:
    """
    Converts raw bytes to a human-readable string for display.

    Returns "<no value>" if input is None, the UTF-8 decoded string if 
    successful, or the formal representation (repr) if decoding fails.
    """
    if value is None:
        return "<no value>"
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError:
        return repr(value)

def probe_child_node(key: yottadb.Key, subscript: Any, label: str) -> None:
    """
    Fetches and prints the status and value of a specific child node.
    """
    print(f"{label:>13} child: {key.name}({subscript!r})")
    
    child_node = key[subscript]
    val_display = to_display(child_node.value) if child_node.has_value else "<none>"
    print(f"{label:>7} child value: {val_display}")


def main() -> int:
    args = parse_args()
    probe_global = normalize_global_name(args.probe_global)

    print(f"\n{YELLOW}{'=' * 82}")
    print(f"{CYAN}{'VEHU runtime sanity check (v2.0.0+)':>58}{RESET}")
    print(f"{YELLOW}{'=' * 82}")
    print(f"{'Current PWD:':>20} {os.getcwd()}")
    print(f"{'System PATH:':>20} {os.environ.get('PATH', '<not set>')}")
    print(f"{'Python executable:':>20} {sys.executable}")
    print(f"{'Python version:':>20} {platform.python_version()}")
    print(f"{'User (Env Var):':>20} {os.environ.get('USER', 'unknown')}")
    print("-" * 82)
    print(f"{'Probe global:':>20} {probe_global}")

    try:
        release = yottadb.get("$ZYRELEASE").decode("utf-8")
        print(f"{'YottaDB release:':>20} {release}")

        key = yottadb.Key(probe_global)

        if key.has_value:
            print(f"{'Root value:':>20} {to_display(key.value)}")
        else:
            print(f"{'Root value:':>20} <no value (node exists: {key.has_subtree})>")

        # Only sample the first few children to keep this check fast and safe.
        # Converting `key.subscripts` to a full list can be expensive for large
        # globals (e.g., ^DPT), because it materializes every first-level node.
        sampled_children = list(islice(key.subscripts, 3))

        if not sampled_children:
            print("         First child: <none>")
        else:
            # Define the ordinal labels we want to display
            labels = ["First", "Second", "Third"]

            # Print discovered children, then explicitly show missing slots.
            for i, subscript in enumerate(sampled_children):
                probe_child_node(key, subscript, labels[i])
            for label in labels[len(sampled_children):]:
                print(f"{label:>13} child: <none>")

    except YDBError as exc:
        print(f"\n[!] YottaDB Error: {exc}")
        return 1

    print("-" * 82)
    print(f"{'Status:':>20} runtime looks good for read-only exploration.")
    print("=" * 82)
    print(RESET)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
