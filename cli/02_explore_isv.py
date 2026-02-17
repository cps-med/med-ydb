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


def as_text(value):
    """Convert YottaDB bytes to displayable string."""
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError:
        return repr(value)  # Fallback to raw representation


def horolog_to_datetime(horolog_str):
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


print(YELLOW)
print("=" * 75)
print("                YottaDB Intrinsic Special Variables (ISVs)")
print("=" * 75)
print("  ZYRELEASE:", as_text(yottadb.get("$ZYRELEASE")))
print("   ZVERSION:", as_text(yottadb.get("$ZVERSION")))
print("        JOB:", as_text(yottadb.get("$JOB")))

storage_raw = as_text(yottadb.get("$STORAGE"))
storage_num = int(storage_raw)
print("    STORAGE:", f"{storage_num:,}")

horolog_raw = as_text(yottadb.get("$HOROLOG"))
print("    HOROLOG:", horolog_raw)
print("  (decoded):", horolog_to_datetime(horolog_raw))
print("=" * 75)
print(RESET)
