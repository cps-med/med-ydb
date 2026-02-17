# -----------------------------------------------------------
# cli/08_staff_finder.py
# -----------------------------------------------------------

"""
docker exec -it vehu-311 python3 /opt/med-ydb/cli/08_staff_finder.py 5
docker exec -it vehu-311 python3 /opt/med-ydb/cli/08_staff_finder.py --show 10
"""
import argparse
import sys
import yottadb
from utils import safe_get, get_piece

def get_staff_details(ien, silent=False):
    """Fetches identity data for a specific staff/provider IEN from File #200."""
    # REFIX: Global name is '^VA', Subscripts are (200, ien, 0)
    zero_node = safe_get("^VA", ("200", ien, 0))
    
    if not zero_node:
        if not silent:
            print(f"❌ Staff member with IEN {ien} not found.")
        return None

    data = {
        "ien": ien,
        "name": get_piece(zero_node, 1),
        "title": get_piece(zero_node, 9),
    }
    
    if not silent:
        print(f"\n--- Staff IEN: {data['ien']} ---")
        print(f"Name:  {data['name']}")
        print(f"Title/ID: {data['title']}")
        
    return data

def show_multiple_staff(limit, start_ien):
    """Walks ^VA(200, starting from start_ien to find 'limit' staff members."""
    print(f"\n--- Showing up to {limit} records starting AFTER IEN: {start_ien} ---")
    print(f"{'IEN':<10} | {'Name':<30} | {'Title/ID'}")
    print("-" * 60)
    
    count = 0
    current_ien = str(start_ien)
    
    while count < limit:
        try:
            # REFIX: The Key root is ^VA at subscript level 200
            # We want the next sibling of current_ien UNDER the '200' node
            current_key = yottadb.Key("^VA", ("200", current_ien))
            next_result = current_key.subscript_next()
            
            if hasattr(next_result, 'subscripts'):
                # subscripts[0] is '200', subscripts[1] is the IEN
                next_ien_raw = next_result.subscripts[1]
            else:
                next_ien_raw = next_result
            
            next_ien = next_ien_raw.decode('utf-8') if isinstance(next_ien_raw, bytes) else str(next_ien_raw)
            
            details = get_staff_details(next_ien, silent=True)
            if details:
                print(f"{details['ien']:<10} | {details['name']:<30} | {details['title']}")
                count += 1
            
            current_ien = next_ien
                
        except (yottadb.YDBNodeEnd, StopIteration):
            print("\n--- End of global reached ---")
            break
        except Exception as e:
            print(f"\n❌ Traversal Error: {e}")
            break

        
def main():
    parser = argparse.ArgumentParser(
        description="VistA Staff/Provider Finder: Search by IEN or list multiple records.",
        add_help=True
    )
    
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("ien", nargs="?", help="Specific Staff IEN to look up")
    group.add_argument("--show", type=int, metavar="N", help="Number of records to list")
    
    parser.add_argument("--start", default="0", help="IEN to start searching after (default: 0)")

    if len(sys.argv) == 1 or "?" in sys.argv:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    
    if args.show:
        show_multiple_staff(args.show, args.start)
    elif args.ien:
        get_staff_details(args.ien)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()