"""
Patterns Tests - Building Custom Workflows

Tests that demonstrate how to combine the three core node types (Tool, LLM, Router)
to build sophisticated patterns like chain-of-thought, custom ReAct loops, and more.

Learning Goals:
- Building chain-of-thought reasoning
- Implementing custom ReAct loops
- Creating metacognition (self-reflection) patterns
- Parallel analysis with voting
- Iterative refinement patterns
"""

import json
from soe import orchestrate
from tests.test_cases.lib import (
    create_test_backends,
    create_nodes,
    extract_signals,
    create_call_llm,
)
from tests.test_cases.workflows.guide_patterns import (
    chain_of_thought,
    custom_react_loop,
    metacognition,
    parallel_voting,
    iterative_refinement,
    hierarchical_decomposition,
)


class TestChainOfThought:
    """Test chain-of-thought reasoning pattern."""

    def test_chain_of_thought_completes_all_steps(self):
        """
        Chain-of-thought workflow completes Understand -> Plan -> Execute.
        """
        def stub_llm(prompt: str, config: dict) -> str:
            if "Analyze this problem" in prompt:
                return '{"understanding": "The user wants to calculate 2+2"}'
            elif "Create a step-by-step plan" in prompt:
                return '{"plan": "Step 1: Add 2 + 2. Step 2: Return result."}'
            elif "execute the plan" in prompt:
                return '{"answer": "4"}'
            return '{"result": "unknown"}'

        call_llm = create_call_llm(stub=stub_llm)
        backends = create_test_backends("cot_test")
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=chain_of_thought,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"problem": "What is 2+2?"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)
        context = backends.context.get_context(execution_id)

        assert "UNDERSTOOD" in signals
        assert "PLANNED" in signals
        assert "COMPLETE" in signals
        assert "understanding" in context
        assert "plan" in context
        assert "answer" in context

        backends.cleanup_all()


class TestCustomReactLoop:
    """Test custom ReAct loop pattern."""

    def test_react_loop_uses_tool_then_finishes(self):
        """
        Custom ReAct loop calls tool, then finishes.
        """
        call_count = [0]

        def stub_llm(prompt: str, config: dict) -> str:
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: decide to use tool
                return '{"decision": {"action": "use_tool", "tool": "calculator", "args": {"a": 2, "b": 2}}}'
            else:
                # Second call: finish
                return '{"decision": {"action": "finish", "answer": "4"}}'

        def dynamic_tool(**kwargs) -> dict:
            return {"result": 4}

        call_llm = create_call_llm(stub=stub_llm)
        backends = create_test_backends("react_test")
        tools_registry = {"dynamic_tool": dynamic_tool}
        nodes, broadcast_signals_caller = create_nodes(
            backends, call_llm=call_llm, tools_registry=tools_registry
        )

        execution_id = orchestrate(
            config=custom_react_loop,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"task": "Calculate 2+2"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "DECIDED" in signals
        assert "TASK_COMPLETE" in signals or "USE_TOOL" in signals

        backends.cleanup_all()


class TestMetacognition:
    """Test metacognition (self-reflection) pattern."""

    def test_metacognition_accepts_good_draft(self):
        """
        Metacognition accepts draft when no revision needed.
        """
        def stub_llm(prompt: str, config: dict) -> str:
            if "Write a response" in prompt:
                return '{"draft": "This is a well-written response."}'
            elif "Review this response" in prompt:
                return '{"review": {"needs_revision": false, "critique": "Looks good!"}}'
            return '{"result": "unknown"}'

        call_llm = create_call_llm(stub=stub_llm)
        backends = create_test_backends("metacog_accept")
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=metacognition,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"request": "Write a greeting"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "DRAFT_READY" in signals
        assert "REVIEWED" in signals
        assert "COMPLETE" in signals or "FINALIZE" in signals

        backends.cleanup_all()

    def test_metacognition_revises_when_needed(self):
        """
        Metacognition revises draft when critique suggests changes.
        """
        call_count = [0]

        def stub_llm(prompt: str, config: dict) -> str:
            call_count[0] += 1
            if "Write a response" in prompt:
                return '{"draft": "This needs work."}'
            elif "Review this response" in prompt:
                return '{"review": {"needs_revision": true, "critique": "Too brief, add more detail."}}'
            elif "Write an improved version" in prompt:
                return '{"final_response": "This is a much better, more detailed response."}'
            return '{"result": "unknown"}'

        call_llm = create_call_llm(stub=stub_llm)
        backends = create_test_backends("metacog_revise")
        nodes, broadcast_signals_caller = create_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=metacognition,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"request": "Write a greeting"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)
        context = backends.context.get_context(execution_id)

        assert "DRAFT_READY" in signals
        assert "REVIEWED" in signals
        # Should have triggered revision
        assert "REVISE" in signals or "final_response" in context

        backends.cleanup_all()


class TestParallelVoting:
    """Test parallel analysis with voting pattern."""

    def test_parallel_voting_fans_out(self):
        """
        Parallel voting fans out to multiple analyzers.
        """
        def stub_llm(prompt: str, config: dict) -> str:
            if "safe" in prompt.lower():
                return '{"safety_result": {"safe": true, "reason": "Content is appropriate"}}'
            elif "quality" in prompt.lower():
                return '{"quality_result": {"score": 8, "feedback": "Good quality"}}'
            elif "relevance" in prompt.lower():
                return '{"relevance_result": {"relevant": true}}'
            return '{"result": "unknown"}'

        def aggregate_votes(**kwargs) -> dict:
            return {"approved": True, "votes": 3}

        call_llm = create_call_llm(stub=stub_llm)
        backends = create_test_backends("voting_test")
        tools_registry = {"aggregate_votes": aggregate_votes}
        nodes, broadcast_signals_caller = create_nodes(
            backends, call_llm=call_llm, tools_registry=tools_registry
        )

        execution_id = orchestrate(
            config=parallel_voting,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"content": "Test content", "topic": "testing"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        # Should fan out to all analyzers
        assert "ANALYZE_SAFETY" in signals
        assert "ANALYZE_QUALITY" in signals
        assert "ANALYZE_RELEVANCE" in signals

        backends.cleanup_all()


class TestIterativeRefinement:
    """Test iterative refinement pattern."""

    def test_iterative_refinement_succeeds_first_try(self):
        """
        Iterative refinement succeeds when code is valid on first try.
        """
        def stub_llm(prompt: str, config: dict) -> str:
            return '{"code": "def add(a, b): return a + b"}'

        def lint_code(code: str = None, **kwargs) -> dict:
            return {"errors": [], "valid": True}

        call_llm = create_call_llm(stub=stub_llm)
        backends = create_test_backends("refine_success")
        tools_registry = {"lint_code": lint_code}
        nodes, broadcast_signals_caller = create_nodes(
            backends, call_llm=call_llm, tools_registry=tools_registry
        )

        execution_id = orchestrate(
            config=iterative_refinement,
            initial_workflow_name="example_workflow",
            initial_signals=["START"],
            initial_context={"task": "Write an add function"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "CODE_GENERATED" in signals
        assert "VALID" in signals or "CODE_COMPLETE" in signals

        backends.cleanup_all()
