from uuid import uuid4
from typing import Dict, List, Any, Union, Callable, Optional
from .types import Backends, BroadcastSignalsCaller
from .local_backends import EventTypes
from .lib.register_event import register_event
from .lib.yaml_parser import parse_yaml
from .lib.operational import add_operational_state
from .lib.context_fields import set_field
from .lib.parent_sync import get_signals_for_parent
from .lib.inheritance import (
    inherit_config,
    inherit_context,
    extract_and_save_config_sections,
)
from .validation import validate_config, validate_operational, validate_orchestrate_params
from .types import WorkflowValidationError


def orchestrate(
    config: Optional[Union[str, Dict[str, Any]]],
    initial_workflow_name: str,
    initial_signals: List[str],
    initial_context: Dict[str, Any],
    backends: Backends,
    broadcast_signals_caller: BroadcastSignalsCaller,
    inherit_config_from_id: Optional[str] = None,
    inherit_context_from_id: Optional[str] = None,
) -> str:
    """
    Initialize orchestration with config and trigger initial signals.

    Config can be either:

    1. Workflows only (legacy format):
       config = {
           "workflow_name": {
               "node_name": {...}
           }
       }

    2. Combined config with workflows, context_schema, and identities:
       config = {
           "workflows": {...},
           "context_schema": {...},  # optional
           "identities": {...}       # optional
       }

    3. Inherited config (config=None, inherit_config_from_id provided):
       Inherits workflows, identities, and context_schema from an existing
       execution. Useful for workflow chaining and continuation.

    Inheritance options:

    - inherit_config_from_id: Copy workflows, identities, and context_schema
      from the specified execution ID. When provided, config is optional.

    - inherit_context_from_id: Copy context from the specified execution ID,
      but ALWAYS reset __operational__ state. Useful for continuing work
      with existing context data.

    When context_schema and identities are present (either from config or
    inherited), they are automatically saved to their respective backends,
    keyed by the main execution ID so children can access them.
    """
    validate_orchestrate_params(initial_workflow_name, initial_signals)

    if config is None and inherit_config_from_id is None:
        raise WorkflowValidationError(
            "Either 'config' or 'inherit_config_from_id' must be provided"
        )

    id = str(uuid4())

    if inherit_config_from_id:
        register_event(
            backends, id, EventTypes.CONFIG_INHERITANCE_START,
            {"source_execution_id": inherit_config_from_id}
        )
        parsed_registry = inherit_config(inherit_config_from_id, id, backends)
        if config:
            validate_config(config)
            parsed_config = parse_yaml(config)
            parsed_registry = extract_and_save_config_sections(parsed_config, id, backends)
    else:
        validate_config(config)
        parsed_config = parse_yaml(config)
        parsed_registry = extract_and_save_config_sections(parsed_config, id, backends)

    register_event(
        backends, id, EventTypes.ORCHESTRATION_START,
        {"workflow_name": initial_workflow_name}
    )

    backends.workflow.save_workflows_registry(id, parsed_registry)

    if initial_workflow_name not in parsed_registry:
        available = list(parsed_registry.keys())
        raise WorkflowValidationError(
            f"Workflow '{initial_workflow_name}' not found in config. "
            f"Available workflows: {available}"
        )

    backends.workflow.save_current_workflow_name(id, initial_workflow_name)

    if inherit_context_from_id:
        register_event(
            backends, id, EventTypes.CONTEXT_INHERITANCE_START,
        )
        context = inherit_context(inherit_context_from_id, backends)
        if initial_context:
            register_event(
                backends, id, EventTypes.CONTEXT_MERGE,
                {"fields": list(initial_context.keys())}
            )
            for field, value in initial_context.items():
                set_field(context, field, value)
    else:
        context = {
            k: [v] if not k.startswith("__") else v
            for k, v in initial_context.items()
        }

    context = add_operational_state(id, context)
    backends.context.save_context(id, context)

    broadcast_signals_caller(id, initial_signals)

    return id


def broadcast_signals(
    id: str,
    signals: List[str],
    nodes: Dict[str, Callable[[str, Dict[str, Any]], None]],
    backends: Backends,
) -> None:
    """Broadcast signals to matching nodes in the current workflow"""
    context = validate_operational(id, backends)

    register_event(backends, id, EventTypes.SIGNALS_BROADCAST, {"signals": signals})

    workflows_registry = backends.workflow.soe_get_workflows_registry(id)

    workflow_name = backends.workflow.get_current_workflow_name(id)
    workflow = workflows_registry.get(workflow_name, {})

    for node_name, node_config in workflow.items():
        triggers = node_config.get("event_triggers", [])
        if set(triggers) & set(signals):
            node_type = node_config["node_type"]
            node_executor = nodes[node_type]

            register_event(
                backends, id, EventTypes.NODE_EXECUTION,
                {"node_name": node_name, "node_type": node_type}
            )

            node_config["name"] = node_name
            node_executor(id, node_config)

    context = backends.context.get_context(id)
    parent_id, signals_to_sync = get_signals_for_parent(signals, context)

    if parent_id and signals_to_sync:
        register_event(
            backends, id, EventTypes.SIGNALS_TO_PARENT,
            {"signals": signals_to_sync, "parent_id": parent_id}
        )
        broadcast_signals(parent_id, signals_to_sync, nodes, backends)
