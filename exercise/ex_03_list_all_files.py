# -----------------------------------------------------------
# exercise/list_all_files.py
# -----------------------------------------------------------

"""
Discovering FileMan Structure
List All Files

Prerequisite:
docker exec -it vehu-dev bash -lc 'python3 -m pip install --user yottadb pandas'

To run:
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
python3 /opt/med-ydb/exercise/ex_03_list_all_files.py'
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
                continue
            file_def = file_def_value.decode('utf-8')
            file_name = file_def.split("^")[0]

            # Get global root location from ^DIC(file#,0,"GL")
            try:
                gl_node_value = dic[file_num]["0"]["GL"].value
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
    print("\nFileMan Files Summary:")
    print("=" * 22)
    print(df.to_string(index=False))
    print(f"\nTotal files found: {len(df)}")

    # Save to CSV
    output_file = '/opt/med-ydb/output/fileman_files.csv'
    df.to_csv(output_file, index=False)
    print(f"\nData saved to: {output_file}\n")


if __name__ == "__main__":
    main()
