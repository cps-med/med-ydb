from datetime import datetime
import yottadb

def safe_get(global_name, subscripts):
    """
    Safely retrieves a value from YottaDB.
    - Ensures all subscripts are strings to avoid TypeErrors.
    - Decodes bytes to UTF-8 strings.
    - Returns None instead of crashing if the node is empty.
    """
    try:
        # Cast all subscripts to strings to satisfy YDB 2.0.0 wrapper
        str_subs = tuple(str(s) for s in subscripts)
        
        val = yottadb.get(global_name, str_subs)
        
        if val is None:
            return None
            
        return val.decode('utf-8') if isinstance(val, (bytes, bytearray)) else val
    except Exception:
        return None

def get_piece(data, piece_num, delimiter="^"):
    """Shorthand for VistA/Mumps $P(data, "^", piece_num)"""
    if not data:
        return ""
    pieces = data.split(delimiter)
    return pieces[piece_num - 1] if len(pieces) >= piece_num else ""


def fm_to_date(fm_date, format_str="%m/%d/%Y"):
    """
    Converts a FileMan internal date string (e.g., 2660512) to a readable string.
    FileMan format: (Year-1700)MMDD.HHMMSS
    """
    if not fm_date or not str(fm_date).strip():
        return "N/A"
    
    try:
        # Strip time if present (e.g., 2660512.1030)
        date_part = str(fm_date).split(".")[0]
        
        # VistA logic: add 1700 to the first 3 digits
        year = int(date_part[:3]) + 1700
        month = int(date_part[3:5])
        day = int(date_part[5:7])
        
        dt = datetime(year, month, day)
        return dt.strftime(format_str)
    except (ValueError, IndexError):
        return f"Invalid Date ({fm_date})"