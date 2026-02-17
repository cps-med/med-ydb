# ---------------------------------------------------------------------
# cli/03a_explore_files.py
# ---------------------------------------------------------------------
# Discover All Files Starting with “P”
# Write a script to list all FileMan files whose names start with “X”
# ---------------------------------------------------------------------

"""
docker exec -it vehu-311 python3 /opt/med-ydb/cli/03a_explore_files.py
"""

# Import dependencies
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
    dic = yottadb.Key("^DIC")
    for file_num in dic.subscripts:
        try:
            file_def_value = dic[file_num]["0"].value
            if not file_def_value:
                continue
            file_def = file_def_value.decode('utf-8')
            file_name = file_def.split("^")[0]
            if file_name.startswith(prefix):
                print(f"File #{as_text(file_num)}: {file_name}")
        except YDBError:
            pass


def main():
    find_files_by_prefix("A")
    find_files_by_prefix("N")
    find_files_by_prefix("P")


if __name__ == "__main__":
    main()