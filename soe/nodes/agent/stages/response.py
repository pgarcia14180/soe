from typing import List, Optional, Type, Any, TYPE_CHECKING
from pydantic import BaseModel, Field
from ...lib.llm_resolver import resolve_llm_call
from ...lib.response_builder import (
    build_response_model,
    extract_output_from_response,
    extract_signal_from_response,
)
from ....types import CallLlm
from ..types import ResponseStageInput, FinalResponse

if TYPE_CHECKING:
    from ..state import AgentContext
    from ..lib.loop_state import AgentLoopState


def execute_response_stage(
    call_llm: CallLlm,
    agent_context: "AgentContext",
    loop_state: "AgentLoopState",
    config: dict,
    output_field: Optional[str] = None,
    output_schema: Optional[Type[BaseModel]] = None,
    signal_options: Optional[List[str]] = None,
    max_retries: int = 3,
) -> FinalResponse:
    """Execute the Response stage to generate the final output."""
    input_data = ResponseStageInput(
        task_description=agent_context.agent_prompt,
        context=agent_context.context_string,
        conversation_history=loop_state.get_context_for_llm(),
    )

    response_model = build_response_model(
        output_field=output_field,
        output_schema=output_schema,
        signal_options=signal_options,
    )

    raw_response = resolve_llm_call(
        call_llm=call_llm,
        input_data=input_data,
        config=config,
        response_model=response_model,
        max_retries=max_retries,
    )

    output_value = extract_output_from_response(raw_response, output_field)
    selected_signal = extract_signal_from_response(raw_response)

    return FinalResponse(
        output=output_value,
        selected_signal=selected_signal,
    )
