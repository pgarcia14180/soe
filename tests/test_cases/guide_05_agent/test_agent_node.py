"""
Guide Chapter 3: Agent Nodes

This test demonstrates Agent nodes - the core of the framework.
Agent nodes run a loop: Router -> Parameter Generation -> Tool Execution -> Response.

Learning Goals:
- Understanding node_type: agent
- Configuring tools
- Understanding the Agent Loop (Router -> Tool -> Router -> Finish)
- Using Identity for persistent conversation history
"""

import json
from soe import orchestrate
from tests.test_cases.lib import create_test_backends, create_agent_nodes, extract_signals, create_call_llm
from tests.test_cases.workflows.guide_agent import (
    agent_simple,
)

# --- Tool Definitions ---

def calculator(a: int, b: int, op: str) -> int:
    """
    Perform basic arithmetic.
    Args:
        a: First number
        b: Second number
        op: Operation (add/+, sub/-, mul/*, div//)
    """
    if op in ("add", "+"): return a + b
    if op in ("sub", "-"): return a - b
    if op in ("mul", "*"): return a * b
    if op in ("div", "/"): return int(a / b)
    raise ValueError(f"Unknown operation: {op}. Use: add, sub, mul, div")

# --- Tests ---

def test_simple_agent_with_tool():
    """
    Agent calls a tool (calculator) and then finishes.
    Flow: Router(call_tool) -> Parameter -> Tool(exec) -> Router(finish) -> Response
    """

    # We need a stateful stub to handle the sequence of calls
    call_sequence = []

    def stub_llm(prompt: str, config: dict) -> str:
        # Identify stage by unique fields in the JSON prompt:
        # - Router: has "available_tools"
        # - Parameter: has "tool_name" but NOT "available_tools"
        # - Response: has neither

        is_router = '"available_tools":' in prompt
        is_parameter = '"tool_name":' in prompt and not is_router

        # 1. Router Stage (First pass)
        if is_router and len(call_sequence) == 0:
            call_sequence.append("router_1")
            return '{"action": "call_tool", "tool_name": "calculator"}'

        # 2. Parameter Stage
        if is_parameter:
            call_sequence.append("param")
            return '{"a": 5, "b": 3, "op": "add"}'

        # 3. Router Stage (Second pass - after tool execution)
        if is_router and len(call_sequence) >= 2:
            call_sequence.append("router_2")
            return '{"action": "finish"}'

        # 4. Response Stage
        if not is_router and not is_parameter:
            call_sequence.append("response")
            return '{"result": "The answer is 8"}'

        return '{}'

    backends = create_test_backends("agent_simple")

    # Define tools list
    tools = [{"function": calculator, "max_retries": 0}]

    call_llm = create_call_llm(stub=stub_llm)
    nodes, broadcast_signals_caller = create_agent_nodes(backends, call_llm, tools)

    execution_id = orchestrate(
        config=agent_simple,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"problem": "What is 5 + 3?"},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # Verify the result contains the answer
    assert "8" in str(context["result"])
    assert "CALCULATION_DONE" in signals

    backends.cleanup_all()
