"""
Tests for Advanced Patterns: Self-Evolving Workflows

Tests workflow and node injection capabilities:
1. Deterministic workflow injection
2. Deterministic node injection
3. LLM-driven workflow generation (with stub)
"""

import os
import pytest
from soe import orchestrate
from tests.test_cases.lib import create_test_backends, create_nodes, extract_signals
from tests.test_cases.workflows.advanced_self_evolving import (
    soe_inject_workflow_base,
    injected_workflow_data,
    inject_node_base,
    injected_node_data,
    llm_workflow_generator,
)
from soe.builtin_tools.soe_inject_workflow import create_soe_inject_workflow_tool
from soe.builtin_tools.soe_inject_node import create_soe_inject_node_tool


def test_soe_inject_workflow_deterministic():
    """Test injecting a new workflow at runtime"""
    backends = create_test_backends("soe_inject_workflow")

    # We need to create the soe_inject_workflow tool with a reference that gets the execution_id
    # This is a bit tricky since we don't have execution_id yet
    # The tool is created per-execution, so we need custom setup

    tools_registry = {}
    nodes, broadcast_signals_caller = create_nodes(
        backends,
        tools_registry=tools_registry
    )

    # Execute orchestration - inject_params contains the tool parameters
    execution_id = orchestrate(
        config=soe_inject_workflow_base,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={
            "inject_params": {
                "workflow_name": "new_dynamic_workflow",
                "workflow_data": injected_workflow_data,
            }
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    # The tool was called - check context
    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # Verify the injection happened (check the tool's output_field)
    injection_result = context.get("injection_result")
    assert injection_result is not None
    assert injection_result[-1].get("injected") == True
    assert "DONE" in signals

    # Verify the workflow was actually injected into the registry
    workflows = backends.workflow.get_workflows_registry(execution_id)
    assert "new_dynamic_workflow" in workflows

    # Cleanup
    backends.cleanup_all()


def test_inject_node_deterministic():
    """Test injecting a node into an existing workflow at runtime"""
    backends = create_test_backends("inject_node")

    tools_registry = {}
    nodes, broadcast_signals_caller = create_nodes(
        backends,
        tools_registry=tools_registry
    )

    # Execute orchestration - inject_params contains the tool parameters
    execution_id = orchestrate(
        config=inject_node_base,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={
            "inject_params": {
                "workflow_name": "example_workflow",
                "node_name": "DynamicNode",
                "node_config_data": injected_node_data,
            }
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    # Check results
    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # Verify the node injection happened (check the tool's output_field)
    injection_result = context.get("injection_result")
    assert injection_result is not None
    assert injection_result[-1].get("injected") == True
    assert "DONE" in signals

    # Verify the node was injected into the workflow
    workflows = backends.workflow.get_workflows_registry(execution_id)
    assert "DynamicNode" in workflows["example_workflow"]

    # Cleanup
    backends.cleanup_all()


@pytest.mark.skipif(
    os.environ.get("SOE_INTEGRATION") == "1",
    reason="Requires LLM to generate valid YAML workflow - stub-only test"
)
def test_llm_workflow_generator():
    """Test LLM-driven workflow generation with stub"""
    backends = create_test_backends("llm_workflow_gen")

    # LLM stub that returns JSON matching the schema.
    # The LLM node uses schema_name=Generated_WorkflowResponse and output_field=inject_params
    # The schema creates a wrapper: {"inject_params": {actual fields}}
    def llm_stub(prompt: str, config: dict) -> str:
        import json
        workflow_yaml = """generated_workflow:
  GeneratedStart:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: GENERATED_COMPLETE
"""
        # Return JSON with wrapper matching output_field name
        return json.dumps({
            "inject_params": {
                "workflow_name": "generated_workflow",
                "workflow_data": workflow_yaml
            }
        })

    tools_registry = {}
    nodes, broadcast_signals_caller = create_nodes(
        backends,
        call_llm=llm_stub,
        tools_registry=tools_registry
    )

    # Execute orchestration - LLM outputs directly to inject_params field
    execution_id = orchestrate(
        config=llm_workflow_generator,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={
            "workflow_name": "generated_workflow",
        },
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    # Check results
    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # Verify the LLM workflow generation and injection completed
    injection_result = context.get("injection_result")
    assert injection_result is not None
    assert injection_result[-1].get("injected") == True
    assert "DONE" in signals

    # Verify the LLM-generated workflow was injected
    workflows = backends.workflow.get_workflows_registry(execution_id)
    assert "generated_workflow" in workflows

    # Cleanup
    backends.cleanup_all()
