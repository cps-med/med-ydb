# ---------------------------------------------------------------------
# app/05_rpc_explorer.py
# ---------------------------------------------------------------------
# Explore VistA Remote Procedure Call (RPC) definitions in File #8994.
#
# Design goals:
# 1) Read-only exploration of RPC metadata
# 2) Discover RPCs by name pattern (prefix search)
# 3) Show RPC structure: name, M routine, parameters, return type
# 4) Trace RPC to underlying M code location
# 5) Educational output for learning VistA's API layer
# ---------------------------------------------------------------------

"""
# Run Example
docker exec -it vehu-311 python3 /opt/med-ydb/cli/05_rpc_explorer.py --prefix ORWPT --limit 10

# List patient-related RPCs
docker exec -it vehu-311 python3 /opt/med-ydb/cli/05_rpc_explorer.py --prefix ORWPT

# List authentication RPCs
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
python3 /opt/med-ydb/app/04_rpc_explorer.py --prefix XUS'

# Get details on a specific RPC
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
python3 /opt/med-ydb/app/04_rpc_explorer.py --name "ORWPT SELECT"'

# List all RPCs (bounded by --limit)
docker exec -it vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
python3 /opt/med-ydb/app/04_rpc_explorer.py --limit 50'

# See rich details on authentication RPC
docker exec vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
python3 /opt/med-ydb/app/04_rpc_explorer.py --name "XUS SIGNON SETUP"'

# Explore patient RPCs with --detail flag
docker exec vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
python3 /opt/med-ydb/app/04_rpc_explorer.py --prefix ORWPT --limit 5 --detail'

# Find order-related RPCs
docker exec vehu-dev bash -lc '. /usr/local/etc/ydb_env_set && \
python3 /opt/med-ydb/app/04_rpc_explorer.py --prefix ORWDX --limit 10'
"""

import argparse
import sys
from typing import Any, Dict, List, Optional

import yottadb
from yottadb import YDBError


# File #8994: REMOTE PROCEDURE file
RPC_FILE_GLOBAL = "^XWB"
RPC_FILE_NUMBER = "8994"


def safe_decode(value: Optional[bytes]) -> str:
    """Decode bytes to UTF-8 string, with fallback."""
    if value is None:
        return ""
    try:
        return value.decode("utf-8").strip()
    except (UnicodeDecodeError, AttributeError):
        return repr(value)


def get_rpc_definition(rpc_ien) -> Optional[Dict[str, Any]]:
    """
    Get RPC definition from File #8994.

    Args:
        rpc_ien: Internal entry number of the RPC (bytes or str from subscripts)

    Returns:
        Dict with RPC metadata, or None if error
    """
    try:
        # Use rpc_ien directly as subscript (don't decode)
        rpc_key = yottadb.Key(RPC_FILE_GLOBAL)[RPC_FILE_NUMBER][rpc_ien]

        # Get 0-node (main definition)
        try:
            zeroth_node = safe_decode(rpc_key["0"].value)
        except YDBError:
            return None

        # Parse the 0-node pieces
        # Format: NAME^TAG^ROUTINE^TYPE^...
        pieces = zeroth_node.split("^")

        rpc_name = pieces[0] if len(pieces) > 0 else ""
        tag = pieces[1] if len(pieces) > 1 else ""
        routine = pieces[2] if len(pieces) > 2 else ""
        rpc_type = pieces[3] if len(pieces) > 3 else ""

        # Get multi-line description from field 1
        # Field 1 structure: [1,0] = header, [1,n,0] = line n
        description_lines = []
        try:
            desc_field = rpc_key["1"]
            # Header at [1,0] tells us how many lines: ^^COUNT^COUNT^DATE^
            try:
                header = safe_decode(desc_field["0"].value)
                line_count = int(header.split("^")[2]) if len(header.split("^")) > 2 else 0
            except:
                line_count = 10  # Fallback: try up to 10 lines

            # Read each line of description
            for line_num in range(1, line_count + 1):
                try:
                    line_val = desc_field[str(line_num)]["0"].value
                    description_lines.append(safe_decode(line_val))
                except:
                    pass
        except:
            pass

        description = "\n".join(description_lines) if description_lines else "(no description)"

        # Get parameters from field 2
        # Field 2 structure: [2,0] = header, [2,n,0] = param n
        parameters = []
        try:
            param_field = rpc_key["2"]
            # Header at [2,0] tells us parameter count
            try:
                header = safe_decode(param_field["0"].value)
                # Format: ^8994.02A^COUNT^COUNT
                param_count = int(header.split("^")[2]) if len(header.split("^")) > 2 else 0
            except:
                param_count = 10  # Fallback

            # Read each parameter definition
            for param_num in range(1, param_count + 1):
                try:
                    param_val = param_field[str(param_num)]["0"].value
                    param_def = safe_decode(param_val)
                    # Format: NAME^TYPE^LENGTH^REQUIRED^SEQUENCE
                    parts = param_def.split("^")
                    param_name = parts[0] if len(parts) > 0 else ""
                    param_type = parts[1] if len(parts) > 1 else ""
                    param_required = parts[3] if len(parts) > 3 else ""

                    parameters.append({
                        "name": param_name,
                        "type": param_type,
                        "required": param_required == "1",
                        "definition": param_def
                    })
                except:
                    pass
        except:
            pass

        # Get return type from 0-node (piece 4 might indicate return type)
        # Type: 1=single value, 2=array, etc.
        return_type_code = rpc_type
        return_type_map = {
            "1": "Single Value",
            "2": "Array",
            "3": "Global",
            "4": "Word Processing"
        }
        return_type = return_type_map.get(return_type_code, f"Type {return_type_code}")

        return {
            "ien": safe_decode(rpc_ien),  # Decode only for display in return dict
            "name": rpc_name,
            "tag": tag,
            "routine": routine,
            "type": rpc_type,
            "description": description,
            "return_type": return_type,
            "parameters": parameters,
            "entry_point": f"DO {tag}^{routine}" if tag and routine else "(not specified)",
        }

    except YDBError as e:
        print(f"Error reading RPC IEN {safe_decode(rpc_ien)}: {e}", file=sys.stderr)
        return None


def find_rpc_by_name(rpc_name: str) -> Optional[Dict[str, Any]]:
    """
    Find RPC by exact name using FileMan "B" index.

    Args:
        rpc_name: Exact RPC name (e.g., "ORWPT SELECT")

    Returns:
        RPC definition dict, or None if not found
    """
    try:
        # Use "B" cross-reference: ^XWB(8994, "B", RPC_NAME, IEN)
        b_index = yottadb.Key(RPC_FILE_GLOBAL)[RPC_FILE_NUMBER]["B"][rpc_name]

        # Get first (should be only) IEN for this name
        # Keep in original format (bytes or str) for use as subscript
        rpc_ien = next(b_index.subscripts)

        return get_rpc_definition(rpc_ien)

    except StopIteration:
        return None
    except YDBError as e:
        print(f"Error searching for RPC '{rpc_name}': {e}", file=sys.stderr)
        return None


def list_rpcs_by_prefix(prefix: str = "", limit: int = 20) -> List[Dict[str, Any]]:
    """
    List RPCs matching a name prefix.

    Args:
        prefix: RPC name prefix (e.g., "ORWPT" for patient RPCs)
        limit: Maximum number of RPCs to return

    Returns:
        List of RPC definition dicts
    """
    rpcs = []

    try:
        # Traverse the "B" index
        b_index = yottadb.Key(RPC_FILE_GLOBAL)[RPC_FILE_NUMBER]["B"]

        for rpc_name in b_index.subscripts:
            # Decode subscript
            rpc_name_str = safe_decode(rpc_name if isinstance(rpc_name, bytes) else str(rpc_name).encode('utf-8'))

            # Filter by prefix if specified
            if prefix and not rpc_name_str.startswith(prefix):
                continue

            # Get the IEN for this RPC name
            try:
                # Keep rpc_ien in original format (bytes or str) for use as subscript
                rpc_ien = next(b_index[rpc_name].subscripts)

                # Get full definition (function will handle decoding internally)
                rpc_def = get_rpc_definition(rpc_ien)
                if rpc_def:
                    rpcs.append(rpc_def)

                # Check limit
                if len(rpcs) >= limit:
                    break

            except StopIteration:
                # No IEN found for this name (shouldn't happen)
                continue

    except YDBError as e:
        print(f"Error traversing RPC index: {e}", file=sys.stderr)

    return rpcs


def print_rpc_summary(rpc: Dict[str, Any]) -> None:
    """Print a one-line summary of an RPC."""
    print(f"{rpc['name']:40s} → {rpc['entry_point']}")


def print_rpc_detail(rpc: Dict[str, Any]) -> None:
    """Print detailed information about an RPC."""
    print(f"\nRPC: {rpc['name']}")
    print(f"{'=' * 60}")
    print(f"IEN:          {rpc['ien']}")
    print(f"Entry Point:  {rpc['entry_point']}")
    print(f"  Tag:        {rpc['tag']}")
    print(f"  Routine:    {rpc['routine']}")
    print(f"Return Type:  {rpc['return_type']}")

    # Print parameters if available
    if rpc.get('parameters'):
        print(f"\nParameters:")
        for idx, param in enumerate(rpc['parameters'], 1):
            required = "required" if param['required'] else "optional"
            print(f"  {idx}. {param['name']:20s} (type: {param['type']}, {required})")
    else:
        print(f"\nParameters:   (none)")

    # Print description
    print(f"\nDescription:")
    if rpc['description'] and rpc['description'] != "(no description)":
        for line in rpc['description'].split('\n'):
            print(f"  {line}")
    else:
        print(f"  (no description available)")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Explore VistA RPC definitions (File #8994)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List patient-related RPCs
  %(prog)s --prefix ORWPT --limit 15

  # List authentication RPCs
  %(prog)s --prefix XUS --limit 10

  # Get details on specific RPC
  %(prog)s --name "ORWPT SELECT"

  # List all RPCs (up to limit)
  %(prog)s --limit 50

  # Count RPCs by package
  %(prog)s --prefix OR --limit 100
        """
    )

    parser.add_argument(
        "--name",
        type=str,
        help="Exact RPC name to look up (e.g., 'ORWPT SELECT')"
    )

    parser.add_argument(
        "--prefix",
        type=str,
        default="",
        help="RPC name prefix filter (e.g., 'ORWPT', 'XUS', 'ORWDX')"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of RPCs to display (default: 20)"
    )

    parser.add_argument(
        "--detail",
        action="store_true",
        help="Show detailed output instead of summary"
    )

    args = parser.parse_args()

    # Mode 1: Look up specific RPC by exact name
    if args.name:
        rpc = find_rpc_by_name(args.name)
        if rpc:
            print_rpc_detail(rpc)
        else:
            print(f"RPC '{args.name}' not found", file=sys.stderr)
            sys.exit(1)
        return

    # Mode 2: List RPCs by prefix
    print(f"Searching for RPCs with prefix: '{args.prefix or '(all)'}' (limit: {args.limit})")
    print()

    rpcs = list_rpcs_by_prefix(prefix=args.prefix, limit=args.limit)

    if not rpcs:
        print(f"No RPCs found matching prefix '{args.prefix}'")
        sys.exit(0)

    print(f"Found {len(rpcs)} RPC(s):\n")

    for rpc in rpcs:
        if args.detail:
            print_rpc_detail(rpc)
        else:
            print_rpc_summary(rpc)

    if len(rpcs) >= args.limit:
        print(f"\n... output truncated at {args.limit} RPCs (use --limit to see more)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
