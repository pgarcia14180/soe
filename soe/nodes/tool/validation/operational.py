"""Tool node operational validation.

Calls shared operational validation. Tool node has no additional backend requirements.
"""

from typing import Dict, Any
from ....types import Backends
from ....validation.operational import validate_operational


def validate_tool_node_runtime(
    execution_id: str,
    backends: Backends,
) -> Dict[str, Any]:
    """Validate runtime state for Tool node. Delegates to shared validation."""
    return validate_operational(execution_id, backends)
