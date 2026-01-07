"""Agent node state retrieval."""

import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict
from ...types import Backends
from ..lib.conversation_history import get_conversation_history
from ...lib.jinja_render import render_prompt, get_context_for_prompt


class AgentOperationalState(BaseModel):
    """All data needed for agent node execution."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    context: Dict[str, Any]
    main_execution_id: str
    prompt: str
    identity: Optional[str]
    output_field: Optional[str]
    event_emissions: List[Dict[str, Any]]
    max_retries: int
    tools: List[str]
    llm_failure_signal: Optional[str]
    current_workflow_name: str
    history_key: Optional[str]
    conversation_history: List[Dict[str, Any]]


class AgentContext(BaseModel):
    """Context data prepared for each agent loop iteration."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    context: Dict[str, Any]
    filtered_context: Dict[str, Any]
    context_string: str
    workflows_registry: Dict[str, Any]
    workflow_name: str
    error_note: str
    agent_prompt: str
    tool_names: List[str]
    event_emissions: List[Dict[str, Any]]


def get_operational_state(
    execution_id: str,
    node_config: Dict[str, Any],
    backends: Backends,
) -> AgentOperationalState:
    """Retrieve all state needed for agent node execution."""
    context = backends.context.get_context(execution_id)
    operational = context["__operational__"]
    identity = node_config.get("identity")
    current_workflow_name = backends.workflow.get_current_workflow_name(execution_id)
    history_key, conversation_history = get_conversation_history(
        execution_id, identity, backends
    )

    return AgentOperationalState(
        context=context,
        main_execution_id=operational["main_execution_id"],
        prompt=node_config["prompt"],
        identity=identity,
        output_field=node_config.get("output_field"),
        event_emissions=node_config.get("event_emissions", []),
        max_retries=node_config.get("retries", 3),
        tools=node_config.get("tools", []),
        llm_failure_signal=node_config.get("llm_failure_signal"),
        current_workflow_name=current_workflow_name,
        history_key=history_key,
        conversation_history=conversation_history,
    )


def prepare_agent_context(
    execution_id: str,
    node_config: Dict[str, Any],
    backends,
    tool_responses: Dict[str, Any],
) -> AgentContext:
    """Prepare all context data for agent execution."""
    context = backends.context.get_context(execution_id)
    workflows_registry = backends.workflow.get_workflows_registry(execution_id)
    workflow_name = backends.workflow.get_current_workflow_name(execution_id)

    prompt_template = node_config["prompt"]
    rendered_prompt, _ = render_prompt(prompt_template, context)

    filtered_context, _ = get_context_for_prompt(context, prompt_template)

    has_errors = (
        any("Error:" in str(v) for v in tool_responses.values())
        if tool_responses
        else False
    )
    error_note = (
        "\n⚠️  Previous tool calls had errors. Please fix the parameters and try again."
        if has_errors
        else ""
    )

    return AgentContext(
        context=context,
        filtered_context=filtered_context,
        context_string=json.dumps(filtered_context, indent=2),
        workflows_registry=workflows_registry,
        workflow_name=workflow_name,
        error_note=error_note,
        agent_prompt=rendered_prompt,
        tool_names=node_config.get("tools", []),
        event_emissions=node_config.get("event_emissions", []),
    )
