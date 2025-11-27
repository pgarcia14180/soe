"""
Guide Chapter 2: LLM Nodes

This test demonstrates LLM nodes - direct LLM calls without the agent loop.
LLM nodes are simpler than Agent nodes: they call the LLM once and emit signals.

Learning Goals:
- Understanding node_type: llm
- Understanding prompt templates with Jinja2
- Understanding output_field (where LLM response is stored)
- Understanding identity for conversation history
- Understanding LLM signal selection (resolution step)
"""

from soe import orchestrate
from tests.test_cases.lib import create_test_backends, create_llm_nodes, extract_signals, create_call_llm
from tests.test_cases.workflows.guide_llm import (
    simple_llm_call,
    llm_with_identity,
    llm_chain,
    llm_signal_selection,
)


def test_simple_llm_call():
    """
    LLM node calls the model and stores response in output_field
    """
    # Stub LLM that returns JSON with the output field
    def stub_llm(prompt: str, config: dict) -> str:
        return '{"summary": "This is a one-sentence summary."}'

    call_llm = create_call_llm(stub=stub_llm)
    backends = create_test_backends("llm_simple")
    nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

    execution_id = orchestrate(
        config=simple_llm_call,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"text": "A long document about Python..."},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    # Assert on backend state
    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # LLM output stored in output_field
    assert "summary" in context
    assert "SUMMARY_COMPLETE" in signals

    backends.cleanup_all()


def test_llm_with_identity():
    """
    LLM node with identity maintains conversation history across calls
    """
    def stub_llm(prompt: str, config: dict) -> str:
        return '{"response": "Hello! How can I help you today?"}'

    call_llm = create_call_llm(stub=stub_llm)
    backends = create_test_backends("llm_identity")
    nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

    execution_id = orchestrate(
        config=llm_with_identity,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"message": "Hi there!"},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    # Assert on backend state
    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # LLM output stored in output_field
    assert "response" in context
    assert "RESPONSE_COMPLETE" in signals

    # Conversation history is saved under main_execution_id (for persistent identity across sub-orchestration)
    history = backends.conversation_history.get_conversation_history(execution_id)
    assert len(history) == 2  # user prompt + assistant response
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"

    backends.cleanup_all()


def test_llm_chain():
    """
    Multiple LLM nodes execute in sequence, each using the previous output
    """
    def stub_llm(prompt: str, config: dict) -> str:
        # Detect which node is calling based on prompt content
        if "Translate" in prompt:
            return '{"spanish_text": "Hola, este es el texto traducido."}'
        else:
            return '{"summary": "Resumen del texto español."}'

    backends = create_test_backends("llm_chain")
    call_llm = create_call_llm(stub=stub_llm)
    nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

    execution_id = orchestrate(
        config=llm_chain,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"text": "Hello, this is the original text."},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    # Assert on backend state
    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    # Both LLM outputs should be in context (works for stub and real LLM)
    assert "spanish_text" in context
    assert "summary" in context

    # Signals should be emitted in order
    assert "TRANSLATED" in signals
    assert "CHAIN_COMPLETE" in signals

    backends.cleanup_all()


def test_llm_signal_selection():
    """
    LLM selects which signal to emit based on plain-text conditions (resolution step)
    """
    def stub_llm(prompt: str, config: dict) -> str:
        # LLM returns JSON with output field and selected signal
        return '{"analysis": "The sentiment is very positive and happy.", "selected_signal": "POSITIVE"}'

    backends = create_test_backends("llm_signal_selection")
    call_llm = create_call_llm(stub=stub_llm)
    nodes, broadcast_signals_caller = create_llm_nodes(backends, call_llm)

    execution_id = orchestrate(
        config=llm_signal_selection,
        initial_workflow_name="example_workflow",
        initial_signals=["START"],
        initial_context={"user_message": "I love this product! It's amazing!"},
        backends=backends,
        broadcast_signals_caller=broadcast_signals_caller,
    )

    # Assert on backend state
    context = backends.context.get_context(execution_id)
    signals = extract_signals(backends, execution_id)

    assert "analysis" in context

    # One of the sentiment signals should be emitted
    sentiment_signals = {"POSITIVE", "NEGATIVE", "NEUTRAL"}
    assert any(s in sentiment_signals for s in signals)

    backends.cleanup_all()
