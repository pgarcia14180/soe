"""
Guide Chapter 3: Agent Nodes - Edge Cases

This test suite covers edge cases and failure modes for Agent nodes:
- Tool execution failures (exceptions)
- Parameter validation failures
- Max retries exceeded (infinite loops)
- Invalid router actions

NOTE: These tests use deliberate stub responses to simulate failures.
They are skipped in integration mode since real LLMs won't produce these
specific failure patterns on demand.
"""

import os
import pytest
from soe import orchestrate
from tests.test_cases.lib import create_test_backends, create_agent_nodes, create_call_llm

# Skip all tests in this module when running integration tests
pytestmark = pytest.mark.skipif(
    os.environ.get("SOE_INTEGRATION") == "1",
    reason="Edge case tests use stubs to simulate deliberate failures"
)

# --- Workflows ---

# Agent with low retries for testing limits
agent_low_retries = """
example_workflow:
  FragileAgent:
    node_type: agent
    event_triggers: [START]
    prompt: "Do something risky"
    tools: [risky_tool]
    retries: 2
    output_field: result
    event_emissions:
      - signal_name: DONE
"""

# Agent with llm_failure_signal configured
agent_with_llm_failure_signal = """
example_workflow:
  AgentWithLLMFailure:
    node_type: agent
    event_triggers: [START]
    prompt: "Do something risky"
    tools: [risky_tool]
    retries: 2
    output_field: result
    llm_failure_signal: AGENT_LLM_FAILED
    event_emissions:
      - signal_name: DONE
"""

# --- Tools ---

def risky_tool(should_fail: bool) -> str:
    """Tool that can be instructed to fail."""
    if should_fail:
        raise ValueError("Tool crashed!")
    return "Success"

# --- Tests ---

def test_tool_execution_failure_and_recovery():
    """
    If a tool fails, the agent sees the error in the history and can try again.
    """
    call_sequence = []

    def stub_llm(prompt: str, config: dict) -> str:
        is_router = '"available_tools":' in prompt
        is_parameter = '"tool_name":' in prompt and not is_router
        has_error = "Tool crashed!" in prompt
        has_success = "Success" in prompt

        # Check success FIRST - history accumulates, so both error and success may be present
        # 5. Router: Finish after success
        if is_router and has_success:
            call_sequence.append("router_3")
            return '{"action": "finish"}'

        # 3. Router: See error, try again (recovery)
        if is_router and has_error:
            call_sequence.append("router_2")
            return '{"action": "call_tool", "tool_name": "risky_tool"}'

        # 1. Router: Call tool (first attempt - no error yet)
        if is_router:
            call_sequence.append("router_1")
            return '{"action": "call_tool", "tool_name": "risky_tool"}'

        # 4. Parameter: Generate args (success second time - after we've seen the error)
        if is_parameter and has_error:
            call_sequence.append("param_2")
            return '{"should_fail": false}'

        # 2. Parameter: Generate args (fail first time)
        if is_parameter:
            call_sequence.append("param_1")
            return '{"should_fail": true}'

        # 6. Response
        if not is_router and not is_parameter:
            return '{"result": "Recovered"}'

        return '{}'

    backends = create_test_backends("agent_tool_fail")
    tools = [{"function": risky_tool, "max_retries": 0}]
    call_llm = create_call_llm(stub=stub_llm)
    nodes, broadcast_signals_caller = create_agent_nodes(backends, call_llm, tools)

    execution_id = orchestrate(
        config=agent_low_retries,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    context = backends.context.get_context(execution_id)
    assert context["result"][-1] == "Recovered"
    assert "router_2" in call_sequence # Confirms we went back to router after error

    backends.cleanup_all()


def test_max_retries_exceeded():
    """
    If the agent keeps looping (Router -> Tool -> Router -> Tool...) without finishing,
    it should eventually hit the max_retries limit and raise an exception.
    """
    def stub_llm(prompt: str, config: dict) -> str:
        is_router = '"available_tools":' in prompt
        is_parameter = '"tool_name":' in prompt and not is_router

        # Always call tool from router
        if is_router:
            return '{"action": "call_tool", "tool_name": "risky_tool"}'
        # Always fail tool (causes error -> retry counter increments)
        if is_parameter:
            return '{"should_fail": true}'
        return '{}'

    backends = create_test_backends("agent_infinite_loop")
    tools = [{"function": risky_tool, "max_retries": 0}]
    call_llm = create_call_llm(stub=stub_llm)
    nodes, broadcast_signals_caller = create_agent_nodes(backends, call_llm, tools)

    # Expect RuntimeError due to max retries
    with pytest.raises(RuntimeError) as excinfo:
        orchestrate(
            config=agent_low_retries, # retries: 2
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

    assert "exceeded max retries" in str(excinfo.value)

    backends.cleanup_all()


def test_invalid_router_action():
    """
    If the router returns an invalid action (e.g. "dance"), it should be treated as an error
    and the agent should retry the router step.
    """
    call_count = {"n": 0}

    def stub_llm(prompt: str, config: dict) -> str:
        is_router = '"available_tools":' in prompt
        is_parameter = '"tool_name":' in prompt and not is_router

        if is_router:
            call_count["n"] += 1
            if call_count["n"] == 1:
                return '{"action": "dance"}' # Invalid action
            else:
                return '{"action": "finish"}' # Valid recovery

        if not is_router and not is_parameter:
            return '{"result": "Done"}'

        return '{}'


    backends = create_test_backends("agent_invalid_action")
    tools = [{"function": risky_tool, "max_retries": 0}]
    call_llm = create_call_llm(stub=stub_llm)
    nodes, broadcast_signals_caller = create_agent_nodes(backends, call_llm, tools)

    execution_id = orchestrate(
        config=agent_low_retries,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    # Should succeed after recovery
    context = backends.context.get_context(execution_id)
    assert context["result"][-1] == "Done"
    assert call_count["n"] == 2 # 1 fail + 1 success

    backends.cleanup_all()


def test_llm_failure_signal_emitted():
    """
    When llm_failure_signal is configured and agent exceeds max retries,
    the agent emits the failure signal instead of raising RuntimeError.
    """
    def stub_llm(prompt: str, config: dict) -> str:
        is_router = '"available_tools":' in prompt
        is_parameter = '"tool_name":' in prompt and not is_router

        # Always call tool from router
        if is_router:
            return '{"action": "call_tool", "tool_name": "risky_tool"}'
        # Always fail tool (causes error -> retry counter increments)
        if is_parameter:
            return '{"should_fail": true}'
        return '{}'

    backends = create_test_backends("agent_llm_failure_signal")
    tools = [{"function": risky_tool, "max_retries": 0}]
    call_llm = create_call_llm(stub=stub_llm)
    nodes, broadcast_signals_caller = create_agent_nodes(backends, call_llm, tools)

    # Should NOT raise - emits failure signal instead
    from tests.test_cases.lib import extract_signals

    execution_id = orchestrate(
        config=agent_with_llm_failure_signal,  # has llm_failure_signal: AGENT_LLM_FAILED
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    signals = extract_signals(backends, execution_id)

    # Failure signal emitted, not DONE
    assert "AGENT_LLM_FAILED" in signals
    assert "DONE" not in signals

    backends.cleanup_all()


# Agent with condition on output
agent_condition_on_output = """
example_workflow:
  AgentConditionOnOutput:
    node_type: agent
    event_triggers: [START]
    prompt: "Do something"
    tools: []
    output_field: result
    event_emissions:
      - signal_name: SUCCESS_SIGNAL
        condition: "{{ 'SUCCESS' in context.result }}"
      - signal_name: FAILURE_SIGNAL
        condition: "{{ 'FAILURE' in context.result }}"
"""

def test_agent_condition_on_output_field():
    """
    Test that Agent event_emissions conditions can reference the output_field
    that was JUST generated by the agent in the current execution.
    """
    def stub_llm(prompt: str, config: dict) -> str:
        # Simple agent: just finish immediately
        return '{"action": "finish", "result": "Operation was a SUCCESS"}'

    backends = create_test_backends("agent_condition_output")
    tools = [] # No tools needed
    call_llm = create_call_llm(stub=stub_llm)
    nodes, broadcast_signals_caller = create_agent_nodes(backends, call_llm, tools)

    execution_id = orchestrate(
        config=agent_condition_on_output,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    from tests.test_cases.lib import extract_signals
    signals = extract_signals(backends, execution_id)

    # The condition {{ 'SUCCESS' in context.result }} should evaluate to True
    # because context.result should contain the output we just generated.
    assert "SUCCESS_SIGNAL" in signals
    assert "FAILURE_SIGNAL" not in signals

    backends.cleanup_all()
