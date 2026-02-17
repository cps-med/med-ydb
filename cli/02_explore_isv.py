# ---------------------------------------------------------------------------
# exercise/ex_01_explore_isv.py
# ---------------------------------------------------------------------------
# Explore Intrinsic Special Variables (ISVs)
# ISVs are system-provided variables that start with $.
# They provide runtime information.
# ---------------------------------------------------------------------------

"""
docker exec -it vehu-311 python3 /opt/med-ydb/cli/02_explore_isv.py
"""

import yottadb
from datetime import datetime, timedelta
from constants_config import *


def as_text(value) ->str:
    """Convert YottaDB bytes to displayable string."""
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError:
        return repr(value)  # Fallback to raw representation


def horolog_to_datetime(horolog_str: str) ->str:
    """
    Convert HOROLOG format to readable date/time.
    HOROLOG format: "days,seconds"
      - days: number of days since December 31, 1840
      - seconds: number of seconds since midnight
    """
    try:
        days_str, seconds_str = horolog_str.split(",")
        days = int(days_str)
        seconds = int(seconds_str)

        # Base date: December 31, 1840
        base_date = datetime(1840, 12, 31)

        # Calculate the actual date/time
        target_datetime = base_date + timedelta(days=days, seconds=seconds)

        return target_datetime.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        return "<invalid HOROLOG format>"

def main():
    print(f"\n{YELLOW}{'=' * 75}")
    print(f"{CYAN}{'YottaDB Intrinsic Special Variables (ISVs)':>58}")
    print(f"{YELLOW}{'=' * 75}")
    print(f"{'ZYRELEASE:':>13}", as_text(yottadb.get("$ZYRELEASE")))
    print(f"{'ZVERSION:':>13}", as_text(yottadb.get("$ZVERSION")))
    print(f"{'JOB:':>13}", as_text(yottadb.get("$JOB")))

    storage_raw = as_text(yottadb.get("$STORAGE"))
    storage_num = int(storage_raw)
    print(f"{'STORAGE:':>13} {storage_num:,}")

    horolog_raw = as_text(yottadb.get("$HOROLOG"))
    print(f"{'HOROLOG:':>13} horolog_raw")
    print(f"{'(decoded):':>13} {horolog_to_datetime(horolog_raw)}")
    print(f"{'=' * 75}{RESET}\n")

if __name__ == "__main__":
    raise SystemExit(main())
