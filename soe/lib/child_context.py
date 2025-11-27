"""
Child context preparation utilities.

Prepares initial context for child workflows with parent metadata.
"""

import copy
from typing import Any, Dict

from .context_fields import get_field


PARENT_INFO_KEY = "__parent__"


def prepare_child_context(
    parent_context: Dict[str, Any],
    node_config: Dict[str, Any],
    parent_execution_id: str,
    main_execution_id: str,
) -> Dict[str, Any]:
    """
    Prepare initial context for child workflow.

    Includes:
    - Input fields copied from parent context (current value, not full history)
    - __parent__ metadata for communication back to parent
    """
    child_context: Dict[str, Any] = {}

    # Copy specified input fields from parent (current value only)
    # orchestrate() will wrap these in history lists
    for field_name in node_config.get("input_fields", []):
        if field_name in parent_context:
            # Use get_field to get current value, not full history
            child_context[field_name] = copy.deepcopy(get_field(parent_context, field_name))

    # Inject parent info for child-to-parent communication
    child_context[PARENT_INFO_KEY] = {
        "parent_execution_id": parent_execution_id,
        "signals_to_parent": node_config.get("signals_to_parent", []),
        "context_updates_to_parent": node_config.get("context_updates_to_parent", []),
        "main_execution_id": main_execution_id,
    }

    return child_context
