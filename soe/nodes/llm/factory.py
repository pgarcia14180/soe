"""
LLM node factory

Simple node that calls LLM directly without agent loop, tools, or routing.
Supports conversation history via identity and schema validation via Pydantic.
Prompts use Jinja templates - variables are auto-extracted from {{ context.field }}.
"""

from typing import Dict, Any, Callable
from ..lib.llm_resolver import resolve_llm_call
from ..lib.signal_emission import emit_completion_signals, handle_llm_failure
from ..lib.response_builder import (
    build_response_model,
    extract_output_from_response,
    extract_signal_from_response,
)
from ...types import CallLlm, BroadcastSignalsCaller, Backends, LlmNodeCaller, EventTypes
from ...lib.register_event import register_event
from ..lib.context import save_output_to_context
from ..lib.conversation_history import save_conversation_turn
from ...lib.jinja_render import render_prompt
from ...validation.operational import validate_operational
from .validation import validate_node_config
from .state import get_operational_state
from .types import LlmNodeInput


def create_llm_node_caller(
    backends: Backends,
    call_llm: CallLlm,
    broadcast_signals_caller: BroadcastSignalsCaller,
) -> LlmNodeCaller:
    """Create LLM node caller with pre-loaded dependencies."""

    def execute_llm_node(id: str, node_config: Dict[str, Any]) -> None:
        validate_operational(id, backends)
        validate_node_config(node_config)

        state = get_operational_state(id, node_config, backends)

        register_event(backends, id, EventTypes.LLM_CALL, {"identity": state.identity})

        rendered_prompt, warnings = render_prompt(state.prompt, state.context)

        if warnings:
            register_event(backends, id, EventTypes.CONTEXT_WARNING, {"warnings": warnings})

        input_data = LlmNodeInput(
            prompt=rendered_prompt,
            context=state.context_str,
            conversation_history=state.history_str,
        )

        response_model = build_response_model(
            output_field=state.output_field,
            output_schema=state.output_model,
            signal_options=state.signal_options,
        )

        try:
            raw_response = resolve_llm_call(
                call_llm=call_llm,
                input_data=input_data,
                config=node_config,
                response_model=response_model,
                max_retries=state.max_retries,
            )

            output_value = extract_output_from_response(raw_response, state.output_field)
            save_output_to_context(id, state.output_field, output_value, backends)

            if state.output_field:
                if state.output_field in state.context:
                    state.context[state.output_field].append(output_value)
                else:
                    state.context[state.output_field] = [output_value]

            save_conversation_turn(
                state.history_key, state.conversation_history,
                rendered_prompt, str(output_value), backends
            )

            selected_signal = extract_signal_from_response(raw_response)

            emit_completion_signals(
                selected_signal=selected_signal,
                node_config=node_config,
                operational_state=state,
                broadcast_signals_caller=broadcast_signals_caller,
                execution_id=id,
            )

        except Exception as e:
            handle_llm_failure(
                failure_signal=state.llm_failure_signal,
                error_message=str(e),
                node_type="llm",
                execution_id=id,
                backends=backends,
                broadcast_signals_caller=broadcast_signals_caller,
            )

    return execute_llm_node
