"""
Child node factory
"""

import copy
import time
from typing import Dict, Any

from ...validation.operational import validate_operational
from .validation import validate_node_config
from .state import get_operational_state
from ...lib.register_event import register_event
from ...local_backends import EventTypes
from ...types import ChildNodeCaller, OrchestrateCaller


def create_child_node_caller(
    backends,
    orchestrate_caller: OrchestrateCaller,
) -> ChildNodeCaller:
    """Create child node caller with pre-loaded dependencies."""

    def execute_child_node(id: str, node_config: Dict[str, Any]) -> None:
        validate_operational(id, backends)
        validate_node_config(node_config)

        state = get_operational_state(id, node_config, backends)

        register_event(
            backends, id, EventTypes.NODE_EXECUTION,
            {
                "node_type": "child",
                "child_workflow": state.child_workflow_name,
                "parent_id": id,
            }
        )

        if state.fan_out_items and state.child_input_field:
            for i, item in enumerate(state.fan_out_items):
                child_context = copy.deepcopy(state.child_initial_context)
                child_context[state.child_input_field] = item

                if i > 0 and state.spawn_interval > 0:
                    time.sleep(state.spawn_interval)

                orchestrate_caller(
                    config=state.workflows_registry,
                    initial_workflow_name=state.child_workflow_name,
                    initial_signals=state.child_initial_signals,
                    initial_context=child_context,
                    backends=backends,
                )
        else:
            orchestrate_caller(
                config=state.workflows_registry,
                initial_workflow_name=state.child_workflow_name,
                initial_signals=state.child_initial_signals,
                initial_context=state.child_initial_context,
                backends=backends,
            )

    return execute_child_node
