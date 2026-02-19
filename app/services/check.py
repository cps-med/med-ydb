# ---------------------------------------------------------------------
# app/services/check.py
# ---------------------------------------------------------------------
# Service Layer for the Environment Check function
# ---------------------------------------------------------------------

import logging
from itertools import islice
from typing import Optional
from app.constants_config import *

import yottadb
from yottadb import YDBError

logger = logging.getLogger(__name__)


def normalize_global_name(name: str) -> str:
    """
    Normalizes a global name by ensuring that it is formatted as "^{name}"

    Returns:
        str: A properly formatted global name.
    """
    return name if name.startswith("^") else f"^{name}"


def to_display(value: Optional[bytes]) -> str:
    """
    Converts raw bytes to a human-readable string for display.

    Returns "<no value>" if input is None, the UTF-8 decoded string if
    successful, or the formal representation (repr) if decoding fails.
    """
    if value is None:
        return "<no value>"
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError:
        return repr(value)


def get_yottadb_values(probe_global: str = "^DIC") -> dict[str, str]:
    """
    Returns probe details for the UI, ported from cli/01_env_check.py:
    - Root value
    - First child key reference
    - First child value
    """

    logger.debug(f"{MAGENTA}Starting get_yottadb_values() function.{RESET}")

    normalized_global = normalize_global_name(probe_global)
    results = {
        "probe_global": normalized_global,
        "root_value": "<unknown>",
        "first_child": "<none>",
        "first_child_value": "<none>",
        "error": "",
    }

    try:
        key = yottadb.Key(normalized_global)

        if key.has_value:
            results["root_value"] = to_display(key.value)
        else:
            results["root_value"] = f"<no value (node exists: {key.has_subtree})>"

        sampled_children = list(islice(key.subscripts, 1))
        if sampled_children:
            first_subscript = sampled_children[0]
            child_node = key[first_subscript]
            results["first_child"] = f"{key.name}({first_subscript!r})"
            results["first_child_value"] = (
                to_display(child_node.value) if child_node.has_value else "<none>"
            )
    except YDBError as exc:
        logger.exception("YottaDB probe failed for global %s", normalized_global)
        results["error"] = str(exc)
        results["root_value"] = "<YottaDB error>"
        results["first_child"] = "<YottaDB error>"
        results["first_child_value"] = "<YottaDB error>"

    logger.debug(f"{MAGENTA}Returning results dictionary.{RESET}")

    return results
    
