"""
Tests for setup_orchestration and create_all_nodes.

These test the high-level setup API that external users call.
Ensures both simple function format and full config dict format work.
"""

import pytest
from soe import setup_orchestration, create_all_nodes, orchestrate
from tests.test_cases.lib import create_test_backends, create_call_llm


def sample_tool(x: int) -> int:
    """A simple test tool."""
    return x * 2


def another_tool(name: str) -> str:
    """Another test tool."""
    return f"Hello, {name}!"


class TestCreateAllNodesToolsRegistry:
    """Test create_all_nodes with different tools_registry formats."""

    def test_tools_registry_simple_functions(self):
        """
        tools_registry with simple functions: {"name": function}
        This is the format used in documentation examples.
        """
        backends = create_test_backends("simple_funcs")
        call_llm = create_call_llm(stub=lambda p, c: '{"output": "test"}')

        tools_registry = {
            "sample_tool": sample_tool,
            "another_tool": another_tool,
        }

        nodes, broadcast = create_all_nodes(
            backends=backends,
            call_llm=call_llm,
            tools_registry=tools_registry,
        )

        assert "router" in nodes
        assert "llm" in nodes
        assert "agent" in nodes
        assert "tool" in nodes

        backends.cleanup_all()

    def test_tools_registry_full_config_dicts(self):
        """
        tools_registry with full config dicts: {"name": {"function": fn, "max_retries": 3}}
        This is the format used by soe_evolve and agentic_playground.
        """
        backends = create_test_backends("config_dicts")
        call_llm = create_call_llm(stub=lambda p, c: '{"output": "test"}')

        tools_registry = {
            "sample_tool": {"function": sample_tool, "max_retries": 3},
            "another_tool": {"function": another_tool, "failure_signal": "TOOL_FAILED"},
        }

        nodes, broadcast = create_all_nodes(
            backends=backends,
            call_llm=call_llm,
            tools_registry=tools_registry,
        )

        assert "router" in nodes
        assert "llm" in nodes
        assert "agent" in nodes
        assert "tool" in nodes

        backends.cleanup_all()

    def test_tools_registry_mixed_formats(self):
        """
        tools_registry with mixed formats: some functions, some dicts.
        Should handle both gracefully.
        """
        backends = create_test_backends("mixed_formats")
        call_llm = create_call_llm(stub=lambda p, c: '{"output": "test"}')

        tools_registry = {
            "sample_tool": sample_tool,  # Simple function
            "another_tool": {"function": another_tool, "max_retries": 2},  # Full config
        }

        nodes, broadcast = create_all_nodes(
            backends=backends,
            call_llm=call_llm,
            tools_registry=tools_registry,
        )

        assert "router" in nodes
        assert "llm" in nodes
        assert "agent" in nodes
        assert "tool" in nodes

        backends.cleanup_all()


class TestSetupOrchestration:
    """Test setup_orchestration convenience function."""

    def test_setup_with_simple_functions(self):
        """setup_orchestration works with simple function format."""
        call_llm = create_call_llm(stub=lambda p, c: '{"output": "test"}')

        tools_registry = {
            "sample_tool": sample_tool,
        }

        backends, broadcast = setup_orchestration(
            storage_dir="./test_data/setup_simple",
            call_llm=call_llm,
            tools_registry=tools_registry,
        )

        assert backends is not None
        assert broadcast is not None
        assert callable(broadcast)

        backends.cleanup_all()

    def test_setup_with_config_dicts(self):
        """setup_orchestration works with full config dict format."""
        call_llm = create_call_llm(stub=lambda p, c: '{"output": "test"}')

        tools_registry = {
            "sample_tool": {"function": sample_tool, "max_retries": 3},
        }

        backends, broadcast = setup_orchestration(
            storage_dir="./test_data/setup_dicts",
            call_llm=call_llm,
            tools_registry=tools_registry,
        )

        assert backends is not None
        assert broadcast is not None
        assert callable(broadcast)

        backends.cleanup_all()
