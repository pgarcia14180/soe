"""
Tests for Configuration and Context Inheritance.

These tests verify:
1. inherit_config_from_id - inherits workflows, identities, context_schema
2. inherit_context_from_id - inherits context, always resets operational
3. Combined inheritance for multi-phase workflows
"""

import json
import pytest
from soe import orchestrate
from tests.test_cases.lib import (
    create_test_backends,
    create_nodes,
    extract_signals,
    create_call_llm,
)
from tests.test_cases.workflows.advanced_inheritance import (
    INHERIT_CONFIG_BASIC,
    CONTINUATION_WORKFLOW,
    CONTEXT_INHERITANCE_EXAMPLE,
    LLM_IDENTITY_INHERITANCE,
    MULTI_PHASE_WORKFLOW,
)


class TestInheritConfigFromId:
    """Tests for inheriting configuration from an existing execution."""

    def test_inherit_config_copies_workflows(self):
        """
        inherit_config_from_id should copy workflows registry to new execution.

        The second execution can use workflows defined in the first execution
        without re-providing the config.
        """
        def process(value: str) -> dict:
            return {"processed": f"done:{value}"}

        tools_registry = {"process": process}
        backends = create_test_backends("inherit_config_workflows")
        nodes, broadcast = create_nodes(backends, tools_registry=tools_registry)

        # First execution - establishes config
        first_id = orchestrate(
            config=INHERIT_CONFIG_BASIC,
            initial_workflow_name="main_workflow",
            initial_signals=["START"],
            initial_context={"input_data": {"value": "test1"}},
            backends=backends,
            broadcast_signals_caller=broadcast,
        )

        first_signals = extract_signals(backends, first_id)
        assert "COMPLETE" in first_signals

        # Second execution - inherits config, runs same workflow
        second_id = orchestrate(
            config=None,
            initial_workflow_name="main_workflow",
            initial_signals=["START"],
            initial_context={"input_data": {"value": "test2"}},
            backends=backends,
            broadcast_signals_caller=broadcast,
            inherit_config_from_id=first_id,
        )

        second_signals = extract_signals(backends, second_id)
        second_context = backends.context.get_context(second_id)

        assert "COMPLETE" in second_signals
        assert second_context["result"][-1]["processed"] == "done:test2"

        backends.cleanup_all()

    def test_inherit_config_copies_identities(self):
        """
        inherit_config_from_id should copy identities to new execution.

        LLM nodes in the second execution can use identities defined
        in the first execution's config.
        """
        def stub_llm(prompt: str, config: dict) -> str:
            # Return correct field based on which workflow is calling
            if "follows up" in prompt.lower():
                return json.dumps({"followup_response": "Let me tell you more!"})
            return json.dumps({"assistant_response": "Hello, I can help!"})

        backends = create_test_backends("inherit_config_identities")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast = create_nodes(backends, call_llm=call_llm)

        # First execution - establishes config with identities
        first_id = orchestrate(
            config=LLM_IDENTITY_INHERITANCE,
            initial_workflow_name="conversation_workflow",
            initial_signals=["START"],
            initial_context={"user_message": "Hello"},
            backends=backends,
            broadcast_signals_caller=broadcast,
        )

        first_signals = extract_signals(backends, first_id)
        assert "CONVERSATION_DONE" in first_signals

        # Second execution - inherits config, uses inherited identity
        second_id = orchestrate(
            config=None,
            initial_workflow_name="followup_workflow",
            initial_signals=["START"],
            initial_context={"followup_message": "Tell me more"},
            backends=backends,
            broadcast_signals_caller=broadcast,
            inherit_config_from_id=first_id,
        )

        second_signals = extract_signals(backends, second_id)
        assert "FOLLOWUP_DONE" in second_signals

        # Verify identity was available (check conversation history backend)
        # The identity system prompt should have been used

        backends.cleanup_all()

    def test_inherit_config_runs_different_workflow(self):
        """
        inherit_config_from_id allows running a different workflow from same config.

        First execution runs main_workflow, second runs continuation_workflow,
        both from the same inherited workflows registry.
        """
        def process(value: str) -> dict:
            return {"processed": value}

        def continue_process(processed: str) -> dict:
            return {"final": f"continued:{processed}"}

        tools_registry = {
            "process": process,
            "continue_process": continue_process,
        }

        backends = create_test_backends("inherit_config_different_workflow")
        nodes, broadcast = create_nodes(backends, tools_registry=tools_registry)

        # First execution - runs main_workflow
        first_id = orchestrate(
            config=CONTINUATION_WORKFLOW,
            initial_workflow_name="main_workflow",
            initial_signals=["START"],
            initial_context={"input_data": {"value": "data"}},
            backends=backends,
            broadcast_signals_caller=broadcast,
        )

        first_signals = extract_signals(backends, first_id)
        first_context = backends.context.get_context(first_id)
        assert "COMPLETE" in first_signals

        # Second execution - inherits config, runs continuation_workflow
        second_id = orchestrate(
            config=None,
            initial_workflow_name="continuation_workflow",
            initial_signals=["START"],
            initial_context={"result": first_context["result"][-1]},
            backends=backends,
            broadcast_signals_caller=broadcast,
            inherit_config_from_id=first_id,
        )

        second_signals = extract_signals(backends, second_id)
        second_context = backends.context.get_context(second_id)

        assert "FINALIZED" in second_signals
        assert "continued" in str(second_context["final_result"][-1])

        backends.cleanup_all()


class TestInheritContextFromId:
    """Tests for inheriting context from an existing execution."""

    def test_inherit_context_copies_fields(self):
        """
        inherit_context_from_id should copy context fields to new execution.

        The second execution receives all context fields from first execution.
        """
        def step1_tool() -> dict:
            return {"data": "step1_output"}

        def step2_tool(data: str) -> dict:
            return {"result": f"step2:{data}"}

        def step2_tool_v2(data: str) -> dict:
            return {"result": f"step2_v2:{data}"}

        tools_registry = {
            "step1_tool": step1_tool,
            "step2_tool": step2_tool,
            "step2_tool_v2": step2_tool_v2,
        }

        backends = create_test_backends("inherit_context_fields")
        nodes, broadcast = create_nodes(backends, tools_registry=tools_registry)

        # First execution - builds up context
        first_id = orchestrate(
            config=CONTEXT_INHERITANCE_EXAMPLE,
            initial_workflow_name="main_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast,
        )

        first_signals = extract_signals(backends, first_id)
        first_context = backends.context.get_context(first_id)
        assert "COMPLETE" in first_signals
        assert "step1_result" in first_context

        # Second execution - inherits context, runs retry workflow
        second_id = orchestrate(
            config=None,
            initial_workflow_name="retry_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast,
            inherit_config_from_id=first_id,
            inherit_context_from_id=first_id,
        )

        second_signals = extract_signals(backends, second_id)
        second_context = backends.context.get_context(second_id)

        assert "RETRY_COMPLETE" in second_signals
        # Should have step1_result from first execution
        assert "step1_result" in second_context
        # Should have new step2_result from retry
        assert "step2_v2" in str(second_context["step2_result"][-1])

        backends.cleanup_all()

    def test_inherit_context_resets_operational(self):
        """
        inherit_context_from_id ALWAYS resets operational state.

        The second execution starts with fresh operational counters,
        even though it inherits context fields.
        """
        def step1_tool() -> dict:
            return {"data": "output"}

        def step2_tool(data: str) -> dict:
            return {"result": data}

        def step2_tool_v2(data: str) -> dict:
            return {"result": data}

        tools_registry = {
            "step1_tool": step1_tool,
            "step2_tool": step2_tool,
            "step2_tool_v2": step2_tool_v2,
        }

        backends = create_test_backends("inherit_context_reset_operational")
        nodes, broadcast = create_nodes(backends, tools_registry=tools_registry)

        # First execution
        first_id = orchestrate(
            config=CONTEXT_INHERITANCE_EXAMPLE,
            initial_workflow_name="main_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast,
        )

        first_context = backends.context.get_context(first_id)
        first_operational = first_context["__operational__"]

        # First execution should have tool_calls > 0
        assert first_operational["tool_calls"] >= 2

        # Second execution - inherits context
        second_id = orchestrate(
            config=None,
            initial_workflow_name="retry_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast,
            inherit_config_from_id=first_id,
            inherit_context_from_id=first_id,
        )

        second_context = backends.context.get_context(second_id)
        second_operational = second_context["__operational__"]

        # Second execution should have its OWN operational state
        # tool_calls count should be fresh (just the retry workflow's calls)
        assert second_operational["tool_calls"] == 1
        # Signals should only contain second execution's signals
        assert "RETRY_COMPLETE" in second_operational["signals"]
        assert "COMPLETE" not in second_operational["signals"]

        backends.cleanup_all()

    def test_inherit_context_initial_context_overrides(self):
        """
        initial_context should override inherited context fields.

        If both inherited and initial context have the same field,
        initial_context takes precedence.
        """
        def step1_tool() -> dict:
            return {"data": "original"}

        def step2_tool(data: str) -> dict:
            return {"result": data}

        def step2_tool_v2(data: str) -> dict:
            return {"result": f"processed:{data}"}

        tools_registry = {
            "step1_tool": step1_tool,
            "step2_tool": step2_tool,
            "step2_tool_v2": step2_tool_v2,
        }

        backends = create_test_backends("inherit_context_override")
        nodes, broadcast = create_nodes(backends, tools_registry=tools_registry)

        # First execution
        first_id = orchestrate(
            config=CONTEXT_INHERITANCE_EXAMPLE,
            initial_workflow_name="main_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast,
        )

        # Second execution - override step1_result
        second_id = orchestrate(
            config=None,
            initial_workflow_name="retry_workflow",
            initial_signals=["START"],
            initial_context={"step1_result": {"data": "overridden"}},
            backends=backends,
            broadcast_signals_caller=broadcast,
            inherit_config_from_id=first_id,
            inherit_context_from_id=first_id,
        )

        second_context = backends.context.get_context(second_id)

        # step1_result should be the overridden value
        assert second_context["step1_result"][-1]["data"] == "overridden"
        assert "processed:overridden" in str(second_context["step2_result"][-1])

        backends.cleanup_all()


class TestMultiPhaseInheritance:
    """Tests for multi-phase workflows using both config and context inheritance."""

    def test_multi_phase_workflow_execution(self):
        """
        Multi-phase execution: Phase 1 analyzes, Phase 2 continues with inherited state.

        This demonstrates a real-world pattern where:
        1. Phase 1 runs analysis workflow
        2. Phase 2 inherits config (workflows, identities) and context
        3. Phase 2 runs generation workflow using Phase 1's output
        """
        def stub_llm(prompt: str, config: dict) -> str:
            if "Analyze" in prompt:
                return json.dumps({"analysis": {"insights": "important data found"}})
            elif "generate report" in prompt.lower():
                return json.dumps({"report": "Final report based on analysis"})
            return json.dumps({})

        def validate_analysis(insights: str) -> dict:
            return {"validated": True, "insights": insights}

        tools_registry = {"validate_analysis": validate_analysis}
        backends = create_test_backends("multi_phase")
        call_llm = create_call_llm(stub=stub_llm)
        nodes, broadcast = create_nodes(
            backends, call_llm=call_llm, tools_registry=tools_registry
        )

        # Phase 1 - Analysis
        phase1_id = orchestrate(
            config=MULTI_PHASE_WORKFLOW,
            initial_workflow_name="phase1_workflow",
            initial_signals=["START"],
            initial_context={"raw_data": "sample data to analyze"},
            backends=backends,
            broadcast_signals_caller=broadcast,
        )

        phase1_signals = extract_signals(backends, phase1_id)
        phase1_context = backends.context.get_context(phase1_id)

        assert "PHASE1_COMPLETE" in phase1_signals
        assert "validated_analysis" in phase1_context

        # Phase 2 - Generation (inherits everything)
        phase2_id = orchestrate(
            config=None,
            initial_workflow_name="phase2_workflow",
            initial_signals=["START"],
            initial_context={},
            backends=backends,
            broadcast_signals_caller=broadcast,
            inherit_config_from_id=phase1_id,
            inherit_context_from_id=phase1_id,
        )

        phase2_signals = extract_signals(backends, phase2_id)
        phase2_context = backends.context.get_context(phase2_id)

        assert "PHASE2_COMPLETE" in phase2_signals
        assert "report" in phase2_context
        # Phase 2 should still have Phase 1's context
        assert "validated_analysis" in phase2_context
        # But fresh operational state
        assert phase2_context["__operational__"]["main_execution_id"] == phase2_id

        backends.cleanup_all()


class TestInheritanceValidation:
    """Tests for validation of inheritance parameters."""

    def test_error_when_no_config_and_no_inherit(self):
        """
        Should raise error when neither config nor inherit_config_from_id provided.
        """
        backends = create_test_backends("no_config_error")
        nodes, broadcast = create_nodes(backends)

        from soe.types import WorkflowValidationError
        with pytest.raises(WorkflowValidationError, match="config.*inherit_config_from_id"):
            orchestrate(
                config=None,
                initial_workflow_name="main_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
            )

        backends.cleanup_all()

    def test_error_when_inheriting_from_nonexistent_execution(self):
        """
        Should raise error when inherit_config_from_id points to nonexistent execution.
        """
        backends = create_test_backends("nonexistent_execution")
        nodes, broadcast = create_nodes(backends)

        try:
            orchestrate(
                config=None,
                initial_workflow_name="main_workflow",
                initial_signals=["START"],
                initial_context={},
                backends=backends,
                broadcast_signals_caller=broadcast,
                inherit_config_from_id="nonexistent-id",
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "nonexistent-id" in str(e)

        backends.cleanup_all()
