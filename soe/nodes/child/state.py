"""Child node state retrieval."""

import copy
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from ...types import Backends
from ...lib.context_fields import get_accumulated
from ...lib.child_context import prepare_child_context


class ChildOperationalState(BaseModel):
    """All data needed for child node execution."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    context: Dict[str, Any]
    main_execution_id: str
    child_workflow_name: str
    child_initial_signals: List[str]
    child_initial_context: Dict[str, Any]
    workflows_registry: Dict[str, Any]
    fan_out_items: List[Any] = Field(default_factory=list)
    child_input_field: Optional[str] = None
    spawn_interval: float = 0.0


def get_operational_state(
    execution_id: str,
    node_config: Dict[str, Any],
    backends: Backends,
) -> ChildOperationalState:
    """Retrieve all state needed for child node execution."""
    context = backends.context.get_context(execution_id)
    operational = context["__operational__"]
    main_execution_id = operational["main_execution_id"]

    child_initial_context = prepare_child_context(
        parent_context=context,
        node_config=node_config,
        parent_execution_id=execution_id,
        main_execution_id=main_execution_id,
    )

    workflows_registry = copy.deepcopy(backends.workflow.get_workflows_registry(execution_id))

    fan_out_field = node_config.get("fan_out_field")
    fan_out_items = get_accumulated(context, fan_out_field) if fan_out_field else []

    return ChildOperationalState(
        context=context,
        main_execution_id=main_execution_id,
        child_workflow_name=node_config["child_workflow_name"],
        child_initial_signals=node_config["child_initial_signals"],
        child_initial_context=child_initial_context,
        workflows_registry=workflows_registry,
        fan_out_items=fan_out_items,
        child_input_field=node_config.get("child_input_field"),
        spawn_interval=node_config.get("spawn_interval", 0.0),
    )
