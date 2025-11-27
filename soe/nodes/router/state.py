"""
Router node state retrieval.
"""

from typing import Dict, Any, List
from pydantic import BaseModel, ConfigDict
from ...types import Backends


class RouterOperationalState(BaseModel):
    """All data needed for router node execution."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    context: Dict[str, Any]
    main_execution_id: str
    event_emissions: List[Dict[str, Any]]


def get_operational_state(
    execution_id: str,
    node_config: Dict[str, Any],
    backends: Backends,
) -> RouterOperationalState:
    """Retrieve all state needed for router node execution."""
    context = backends.context.get_context(execution_id)
    operational = context["__operational__"]

    return RouterOperationalState(
        context=context,
        main_execution_id=operational["main_execution_id"],
        event_emissions=node_config["event_emissions"],
    )
