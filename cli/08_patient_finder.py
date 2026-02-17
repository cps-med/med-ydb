# -----------------------------------------------------------
# cli/08_patient_finder.py
# -----------------------------------------------------------

"""
docker exec -it vehu-311 python3 /opt/med-ydb/cli/08_patient_finder.py
docker exec -it vehu-311 python3 /opt/med-ydb/cli/08_patient_finder.py ?
docker exec -it vehu-311 python3 /opt/med-ydb/cli/08_patient_finder.py 1
docker exec -it vehu-311 python3 /opt/med-ydb/cli/08_patient_finder.py --show 15
docker exec -it vehu-311 python3 /opt/med-ydb/cli/08_patient_finder.py --show 5 --start 10
"""

import argparse
import sys
import yottadb
from utils import safe_get, get_piece, fm_to_date

def get_patient_details(ien, silent=False):
    """Fetches core identity data for a specific patient IEN."""
    zero_node = safe_get("^DPT", (ien, 0))
    
    if not zero_node:
        if not silent:
            print(f"❌ Patient with IEN {ien} not found.")
        return None

    data = {
        "ien": ien,
        "name": get_piece(zero_node, 1),
        "ssn": get_piece(zero_node, 9),
        "dob": fm_to_date(get_piece(zero_node, 3))
    }
    
    if not silent:
        print(f"\n--- Patient IEN: {data['ien']} ---")
        print(f"Name: {data['name']}")
        print(f"SSN:  {data['ssn']}")
        print(f"DOB:  {data['dob']}")
        
    return data

def show_multiple_patients(limit, start_ien):
    """Walks ^DPT starting from start_ien to find 'limit' patients."""
    print(f"\n--- Showing up to {limit} records starting AFTER IEN: {start_ien} ---")
    print(f"{'IEN':<10} | {'Name':<30} | {'SSN':<12} | {'DOB'}")
    print("-" * 70)
    
    count = 0
    # Use a string variable to track our current position
    current_ien = str(start_ien)
    
    while count < limit:
        try:
            # 1. Create a Key at the CURRENT position
            current_key = yottadb.Key("^DPT", (current_ien,))
            
            # 2. Get the next subscript
            next_result = current_key.subscript_next()
            
            # 3. Handle the 'Hybrid' return type of YDB 2.0.0
            if hasattr(next_result, 'subscripts'):
                # It's a Key object
                next_ien_raw = next_result.subscripts[0]
            else:
                # It's a bytes object
                next_ien_raw = next_result
            
            # 4. Decode the result to a string
            next_ien = next_ien_raw.decode('utf-8') if isinstance(next_ien_raw, bytes) else str(next_ien_raw)
            
            # 5. Fetch and print details
            details = get_patient_details(next_ien, silent=True)
            if details:
                print(f"{details['ien']:<10} | {details['name']:<30} | {details['ssn']:<12} | {details['dob']}")
                count += 1
            
            # Move our pointer forward
            current_ien = next_ien
                
        except (yottadb.YDBNodeEnd, StopIteration):
            print("\n--- End of global reached ---")
            break
        except Exception as e:
            print(f"\n❌ Traversal Error: {e}")
            break


def main():
    parser = argparse.ArgumentParser(
        description="VistA Patient Finder: Search by IEN or list multiple records.",
        add_help=True
    )
    
    group = parser.add_mutually_exclusive_group(required=False)
    
    group.add_argument("ien", nargs="?", help="Specific Patient IEN to look up")
    group.add_argument("--show", type=int, metavar="N", help="Number of records to list")
    
    parser.add_argument("--start", default="0", help="IEN to start searching after (default: 0)")

    # Custom Help Trigger: If no args or if '?' is passed anywhere
    if len(sys.argv) == 1 or "?" in sys.argv:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    
    # Logic to handle the mutually exclusive choice
    if args.show:
        show_multiple_patients(args.show, args.start)
    elif args.ien:
        get_patient_details(args.ien)
    else:
        # Fallback if somehow no required args were met
        parser.print_help()

if __name__ == "__main__":
    main()