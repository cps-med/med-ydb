# ---------------------------------------------------------------------------
# cli/03_list_globals.py
# ---------------------------------------------------------------------------
# Phase 1 - Step 2: list available global names (read-only, bounded).
#
# Concept:
# - VistA data lives in globals (e.g. ^DPT, ^DIC).
# - The YottaDB intrinsic global ^$GLOBAL provides global-name discovery.
# - We keep this bounded with --limit so first runs stay fast and safe.
# ---------------------------------------------------------------------------

"""
docker exec -it vehu-311 python3 /opt/med-ydb/cli/03_list_globals.py
"""

import argparse
import subprocess
import sys
from collections import defaultdict
from typing import Dict, List, Tuple, Union

import yottadb
from yottadb import YDBError
from constants_config import *


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List global names from ^$GLOBAL (read-only)."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=125,
        help="Maximum number of global names to print (default: 125).",
    )
    parser.add_argument(
        "--prefix",
        default="",
        help="Optional prefix filter, e.g. ^D or ^VA (default: no filter).",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print raw repr of names as returned by YottaDB.",
    )
    return parser.parse_args()


def normalize_prefix(prefix: str) -> str:
    if not prefix:
        return ""
    return prefix if prefix.startswith("^") else f"^{prefix}"


def as_text(value: Union[bytes, str]) -> str:
    if isinstance(value, str):
        return value
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError:
        return repr(value)


def parse_file_name_from_dic0(dic0_value: Union[bytes, str]) -> str:
    text = as_text(dic0_value)
    # FileMan 0-node commonly looks like: NAME^FILE#^...
    if "^" in text:
        return text.split("^", 1)[0].strip() or "<unnamed file>"
    return text.strip() or "<unnamed file>"


def build_global_metadata_map(
    prefix: str,
) -> Dict[str, List[Tuple[str, str]]]:
    """
    Build mapping:
      global root -> list of (file_number, file_name)
    from FileMan dictionary entries in ^DIC(file#,0,"GL").
    """
    meta: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    dic = yottadb.Key("^DIC")

    for file_sub in dic.subscripts:
        try:
            gl_value = dic[file_sub]["0"]["GL"].value
        except YDBError:
            continue

        if not gl_value:
            continue
        gl_text = as_text(gl_value).strip()
        if not gl_text.startswith("^"):
            continue

        base = gl_text.split("(")[0]
        if prefix and not base.startswith(prefix):
            continue

        file_num = as_text(file_sub)
        try:
            dic0_value = dic[file_sub]["0"].value
            file_name = parse_file_name_from_dic0(dic0_value)
        except YDBError:
            file_name = "<unknown file name>"

        pair = (file_num, file_name)
        if pair not in meta[base]:
            meta[base].append(pair)

    return meta


def metadata_suffix(
    global_name: str, metadata: Dict[str, List[Tuple[str, str]]]
) -> str:
    refs = metadata.get(global_name, [])
    if not refs:
        return ""
    if len(refs) == 1:
        file_num, file_name = refs[0]
        return "[#{0} {1}]".format(file_num, file_name)

    joined = "; ".join("#{0} {1}".format(num, name) for num, name in refs[:3])
    if len(refs) > 3:
        joined += "; +{0} more".format(len(refs) - 3)
    return "[{0}]".format(joined)


def print_aligned_rows(
    rows: List[Tuple[str, str]], raw: bool = False, start_index: int = 1
) -> None:
    if not rows:
        return

    max_global_len = max(len(global_name) for global_name, _ in rows)
    name_width = max_global_len + 2

    for idx, (global_name, suffix) in enumerate(rows, start=start_index):
        base = "{0:4d}. {1}".format(idx, global_name.ljust(name_width))
        line = "{0}{1}".format(base, suffix) if suffix else base.rstrip()
        if raw:
            print(repr(line))
        else:
            print(line)


def _m_escape(s: str) -> str:
    # Escape double quotes for a M string literal.
    return s.replace('"', '""')


def list_globals_via_m_direct(prefix: str, limit: int, raw: bool = False) -> int:
    """
    Fallback for environments where SimpleAPI rejects ^$GLOBAL as invalid.
    Uses read-only M direct mode and $ORDER(^$GLOBAL(...)).
    """
    m_prefix = _m_escape(prefix)
    m_code = (
        "set cnt=0\n"
        "set limit={limit}\n"
        "set prefix=\"{prefix}\"\n"
        "set g=\"\"\n"
        "for  set g=$order(^$GLOBAL(g)) quit:g=\"\"  do  quit:cnt'<limit\n"
        ". set full=\"^\"_g\n"
        ". quit:$extract(full,1,$length(prefix))'=prefix\n"
        ". set cnt=cnt+1\n"
        ". write cnt,?6,full,!\n"
        "if cnt=0 write \"No globals matched your filter.\",!\n"
        "halt\n"
    ).format(limit=limit, prefix=m_prefix)

    proc = subprocess.run(
        ["bash", "-lc", "mumps -direct"],
        input=m_code,
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if proc.returncode != 0:
        err = proc.stderr.strip() or "<no stderr>"
        print(
            "Fallback listing via mumps -direct failed: {0}".format(err),
            file=sys.stderr,
        )
        return -1

    metadata = build_global_metadata_map(prefix=prefix)

    # mumps -direct may emit prompts (e.g., GTM>, VEHU>); keep output clean.
    lines = []
    for line in proc.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("GTM>"):
            continue
        if stripped.startswith("VEHU>"):
            continue
        if stripped == "No globals matched your filter.":
            continue
        lines.append(line)

    if not lines:
        return 0

    rows: List[Tuple[str, str]] = []
    for line in lines:
        # mumps output format is: "<count><spaces>^GLOBAL"
        parts = line.strip().split()
        global_name = parts[-1] if parts else line.strip()
        if global_name.startswith("^"):
            rows.append((global_name, metadata_suffix(global_name, metadata)))

    if rows:
        print_aligned_rows(rows, raw=raw, start_index=1)
    else:
        # Fallback if parsing unexpected output format.
        for line in lines:
            if raw:
                print(repr(line))
            else:
                print(line)

    if len(lines) >= limit:
        print("... truncated at {0}".format(limit))
    return len(lines)


def list_globals_via_data_dictionary(prefix: str, limit: int, raw: bool = False) -> int:
    """
    Secondary fallback: derive globals from FileMan data dictionary pointers.
    Reads ^DIC(file#,0,"GL"), which stores the root global for many files.
    """
    try:
        metadata = build_global_metadata_map(prefix=prefix)
    except YDBError as exc:
        print("Data dictionary fallback failed: {0}".format(exc), file=sys.stderr)
        return -1

    globals_found = sorted(metadata.keys())
    if not globals_found:
        return 0

    shown = 0
    rows: List[Tuple[str, str]] = []
    for name in globals_found:
        shown += 1
        rows.append((name, metadata_suffix(name, metadata)))
        if shown >= limit:
            break

    print_aligned_rows(rows, raw=raw, start_index=1)
    if shown >= limit:
        print("... truncated at {0}".format(limit))
    return shown


def main() -> int:
    args = parse_args()
    limit = max(1, args.limit)
    prefix = normalize_prefix(args.prefix)

    print(YELLOW)
    print("=" * 72)
    print("02_list_globals.py - list globals via ^$GLOBAL (read-only)")
    print("=" * 72)
    print(f"  Limit: {limit}")
    print(f" Prefix: {prefix or '<none>'}\n")

    # First attempt: SimpleAPI access to ^$GLOBAL.
    # In some VEHU/YDB bindings this raises INVVARNAME for "^$GLOBAL".
    globals_index = yottadb.Key("^$GLOBAL")
    shown = 0
    rows: List[Tuple[str, str]] = []
    try:
        for raw_name in globals_index.subscripts:
            name_text = as_text(raw_name)
            global_name = name_text if name_text.startswith("^") else f"^{name_text}"

            if prefix and not global_name.startswith(prefix):
                continue

            shown += 1
            if args.raw:
                rows.append((global_name, "<raw {0!r}>".format(raw_name)))
            else:
                rows.append((global_name, ""))

            if shown >= limit:
                break
    except YDBError as exc:
        print(
            "SimpleAPI listing via ^$GLOBAL failed: {0}".format(exc),
            file=sys.stderr,
        )
        print("Falling back to read-only M direct-mode listing...\n")
        m_count = list_globals_via_m_direct(prefix=prefix, limit=limit, raw=args.raw)
        if m_count < 0:
            return 1
        if m_count > 0:
            return 0

        print("M direct-mode method returned no globals.")
        print("Trying FileMan data dictionary fallback (^DIC(...,\"GL\"))...\n")
        dd_count = list_globals_via_data_dictionary(
            prefix=prefix, limit=limit, raw=args.raw
        )
        if dd_count < 0:
            return 1
        if dd_count == 0:
            print("No globals matched your filter.")

        print("=" * 72)
        print(RESET)
        return 0

    if shown == 0:
        print("No globals matched your filter.")
    else:
        print_aligned_rows(rows, raw=args.raw, start_index=1)
    if shown >= limit:
        print(f"... truncated at {limit}")

    print("=" * 72)
    print(RESET)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
