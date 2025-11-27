from typing import Type, TypeVar, TYPE_CHECKING
from pydantic import BaseModel
from ...lib.llm_resolver import resolve_llm_call
from ..types import ParameterInput
from ....types import CallLlm

if TYPE_CHECKING:
    from ..state import AgentContext
    from ..lib.loop_state import AgentLoopState

T = TypeVar("T", bound=BaseModel)


def execute_parameter_stage(
    call_llm: CallLlm,
    agent_context: "AgentContext",
    loop_state: "AgentLoopState",
    tool_name: str,
    tool_schema: Type[T],
    config: dict,
    max_retries: int = 3,
) -> T:
    """Execute the Parameter Generation stage to generate arguments for a tool."""
    input_data = ParameterInput(
        task_description=agent_context.agent_prompt,
        context=agent_context.context_string,
        tool_name=tool_name,
        conversation_history=loop_state.get_context_for_llm(),
    )

    return resolve_llm_call(
        call_llm=call_llm,
        input_data=input_data,
        config=config,
        response_model=tool_schema,
        max_retries=max_retries,
    )
