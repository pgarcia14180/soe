"""LLM node state retrieval."""

import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict
from ...types import Backends
from ..lib.conversation_history import get_conversation_history, format_conversation_history
from ...lib.jinja_render import get_context_for_prompt
from ..lib.output import get_output_model, get_signal_options


class LlmOperationalState(BaseModel):
    """All data needed for LLM node execution."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    context: Dict[str, Any]
    main_execution_id: str
    prompt: str
    identity: Optional[str]
    output_field: Optional[str]
    event_emissions: List[Dict[str, Any]]
    max_retries: int
    llm_failure_signal: Optional[str]
    current_workflow_name: str
    history_key: Optional[str]
    conversation_history: List[Dict[str, Any]]
    context_data: Dict[str, Any]
    context_str: str
    history_str: str
    output_model: Optional[Any]
    signal_options: Optional[List[Dict[str, str]]]


def get_operational_state(
    execution_id: str,
    node_config: Dict[str, Any],
    backends: Backends,
) -> LlmOperationalState:
    """Retrieve all state needed for LLM node execution."""
    context = backends.context.get_context(execution_id)
    operational = context["__operational__"]
    identity = node_config.get("identity")
    prompt = node_config["prompt"]
    output_field = node_config.get("output_field")
    event_emissions = node_config.get("event_emissions", [])
    current_workflow_name = backends.workflow.get_current_workflow_name(execution_id)

    history_key, conversation_history = get_conversation_history(
        execution_id, identity, backends
    )

    context_data, _ = get_context_for_prompt(context, prompt)
    context_str = json.dumps(context_data, indent=2) if context_data else ""
    history_str = format_conversation_history(conversation_history)
    main_execution_id = operational["main_execution_id"]
    output_model = get_output_model(backends, main_execution_id, output_field)
    signal_options = get_signal_options(event_emissions)

    return LlmOperationalState(
        context=context,
        main_execution_id=main_execution_id,
        prompt=prompt,
        identity=identity,
        output_field=output_field,
        event_emissions=event_emissions,
        max_retries=node_config.get("retries", 3),
        llm_failure_signal=node_config.get("llm_failure_signal"),
        current_workflow_name=current_workflow_name,
        history_key=history_key,
        conversation_history=conversation_history,
        context_data=context_data,
        context_str=context_str,
        history_str=history_str,
        output_model=output_model,
        signal_options=signal_options,
    )
