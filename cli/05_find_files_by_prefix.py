# ---------------------------------------------------------------------
# cli/05_find_files_by_prefix.py
# ---------------------------------------------------------------------
# Discover All Files Starting with “X” or "XYZ" (any letter(s))
# List all FileMan files whose names start with a given prefix.
# ---------------------------------------------------------------------

"""
docker exec -it vehu-311 python3 /opt/med-ydb/cli/05_find_files_by_prefix.py
"""

import sys
import argparse
import yottadb
from yottadb import YDBError
from constants_config import *


def as_text(value):
    """Convert YottaDB bytes to displayable string."""
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError:
        return repr(value)  # Fallback to raw representation


def find_files_by_prefix(prefix):
    print(f"\n{YELLOW}{'=' * 72}")
    print(f"{CYAN}{f'Find Files by Prefix: {prefix}':>48}")
    print(f"{YELLOW}{'=' * 72}")

    dic = yottadb.Key("^DIC")
    for file_num in dic.subscripts:
        try:
            file_def_value = dic[file_num]["0"].value
            if not file_def_value:
                continue
            file_def = file_def_value.decode('utf-8')
            file_name = file_def.split("^")[0]
            if file_name.startswith(prefix):
                print(f"{f'File #  {as_text(file_num)}':<20} {file_name}")
        except YDBError:
            pass

    print(f"{'=' * 72}{RESET}\n")

def main():
    parser = argparse.ArgumentParser(
        description="Explore VistA Files: find files by filename prefix",
        add_help=True
    )

    parser.add_argument("prefix", help="File Prefix, e.g., 'A' or 'BILL'")

    if len(sys.argv) < 1:
        parser.print_help()
        sys.exit(0)
    
    args = parser.parse_args()

    find_files_by_prefix(args.prefix)


if __name__ == "__main__":
    raise SystemExit(main())