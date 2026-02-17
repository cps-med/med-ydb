# -----------------------------------------------------------
# cli/04_list_all_files.py
# -----------------------------------------------------------

"""
Discovering FileMan Structure
List All Files

Prerequisite:
docker exec -it vehu-311 python3 /opt/med-ydb/cli/04_list_all_files.py
"""

# Imports
from typing import Optional, List, Dict
import yottadb
from yottadb import YDBError
import pandas as pd
from constants_config import *
    

def as_text(value: Optional[bytes]) -> str:
    """Convert YottaDB bytes to displayable string."""
    if value is None:
        return "<no value>"
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError:
        return repr(value)  # Fallback to raw representation
    

def main():
    # Read ^DIC to find all defined files

    dic = yottadb.Key("^DIC")

    # Collect data for DataFrame
    data = []  # type: List[Dict[str, str]]

    for file_num in dic.subscripts:
        try:
            file_def_value = dic[file_num]["0"].value
            if not file_def_value:
                print(f"\n{RED}No file_def_value for {dic[file_num]}{RESET}")
                continue
            file_def = file_def_value.decode('utf-8')
            file_name = file_def.split("^")[0]

            # Get global root location from ^DIC(file#,0,"GL")
            try:
                gl_node_value = dic[file_num]["0"]["GL"].value
                if not gl_node_value:
                    print(f"\n{RED}No gl_node_value for {dic[file_num]}{RESET}")
                    continue
                gl_node = gl_node_value.decode('utf-8')
            except YDBError:
                gl_node = ""

            # Add row to data
            data.append({
                'file_num': as_text(file_num),
                'file_name': file_name,
                'gl_node': gl_node
            })
        except YDBError:
            pass

    # Create DataFrame
    df = pd.DataFrame(data)

    # Display to terminal
    print(f"\n{YELLOW}{'=' * 82}")
    print(f"{'FileMan Files Summary':>51}")
    print(f"{'=' * 82}{RESET}")
    print(df.to_string(index=False))
    print(f"\nTotal files found: {len(df)}")

    # Save to CSV
    output_file = '/opt/med-ydb/output/fileman_files.csv'
    df.to_csv(output_file, index=False)
    print(f"\nData saved to: {output_file}\n")


if __name__ == "__main__":
    main()
