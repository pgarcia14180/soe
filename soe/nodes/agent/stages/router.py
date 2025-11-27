from typing import TYPE_CHECKING
from ...lib.llm_resolver import resolve_llm_call
from ..lib.prompts import get_state_instructions
from ..types import RouterInput, RouterResponse
from ....types import CallLlm

if TYPE_CHECKING:
    from ..state import AgentContext
    from ..lib.loop_state import AgentLoopState


def execute_router_stage(
    call_llm: CallLlm,
    agent_context: "AgentContext",
    loop_state: "AgentLoopState",
    tools_signature: str,
    config: dict,
    max_retries: int = 3,
) -> RouterResponse:
    """Execute the Router stage to decide the next action."""
    state_instructions = get_state_instructions(loop_state.get_execution_state())

    input_data = RouterInput(
        instructions=state_instructions,
        task_description=agent_context.agent_prompt,
        context=agent_context.context_string,
        available_tools=tools_signature,
        conversation_history=loop_state.get_context_for_llm(),
    )

    return resolve_llm_call(
        call_llm=call_llm,
        input_data=input_data,
        config=config,
        response_model=RouterResponse,
        max_retries=max_retries,
    )
