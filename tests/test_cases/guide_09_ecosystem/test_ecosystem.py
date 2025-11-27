"""
Tests for Chapter 09: Workflows Ecosystem

Tests that demonstrate ecosystem concepts:
- Multiple workflows in a registry
- Fire-and-forget vs callback patterns
- Parallel workflow execution
- Version routing patterns

Learning Goals:
- Understanding the workflows registry concept
- Fire-and-forget child workflows
- Parallel execution with fan-out
- Version-based workflow routing
"""

from soe import orchestrate
from tests.test_cases.lib import (
    create_test_backends,
    setup_nodes,
    extract_signals,
    create_call_llm,
)
from tests.test_cases.workflows.guide_ecosystem import (
    multi_workflow_registry,
    fire_and_forget,
    parallel_workflows,
    version_routing,
)


class TestMultiWorkflowRegistry:
    """Test multiple workflows in a single registry."""

    def test_main_delegates_to_text_workflow(self):
        """
        Main workflow delegates to text_processing_workflow based on input_type.
        """
        def stub_llm(prompt: str, config: dict) -> str:
            if "Analyze this text" in prompt:
                return '{"text_result": "This is text analysis result"}'
            return '{"output": "unknown"}'

        call_llm = create_call_llm(stub=stub_llm)
        backends = create_test_backends("multi_text")
        broadcast_signals_caller = setup_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=multi_workflow_registry,
            initial_workflow_name="main_workflow",
            initial_signals=["START"],
            initial_context={"input_type": "text", "content": "Hello world"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "HANDLE_TEXT" in signals
        assert "PROCESSING_COMPLETE" in signals or "TEXT_DONE" in signals

        backends.cleanup_all()

    def test_main_delegates_to_image_workflow(self):
        """
        Main workflow delegates to image_processing_workflow based on input_type.
        """
        def stub_llm(prompt: str, config: dict) -> str:
            if "Describe this image" in prompt:
                return '{"image_result": "This is an image description"}'
            return '{"output": "unknown"}'

        call_llm = create_call_llm(stub=stub_llm)
        backends = create_test_backends("multi_image")
        broadcast_signals_caller = setup_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=multi_workflow_registry,
            initial_workflow_name="main_workflow",
            initial_signals=["START"],
            initial_context={"input_type": "image", "content": "image_data_here"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "HANDLE_IMAGE" in signals
        assert "PROCESSING_COMPLETE" in signals or "IMAGE_DONE" in signals

        backends.cleanup_all()


class TestFireAndForget:
    """Test fire-and-forget child workflow pattern."""

    def test_parent_continues_without_waiting(self):
        """
        Parent emits PARENT_COMPLETE without waiting for child.
        """
        def long_task(job: str) -> dict:
            return {"completed": True, "job": job}

        backends = create_test_backends("fire_forget")
        tools_registry = {"long_task": long_task}
        broadcast_signals_caller = setup_nodes(
            backends, tools_registry=tools_registry
        )

        execution_id = orchestrate(
            config=fire_and_forget,
            initial_workflow_name="main_workflow",
            initial_signals=["START"],
            initial_context={"task_data": {"job": "background_job"}},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        # Parent should complete immediately
        assert "TASK_LAUNCHED" in signals
        assert "PARENT_COMPLETE" in signals

        backends.cleanup_all()


class TestParallelWorkflows:
    """Test parallel workflow execution."""

    def test_fan_out_to_multiple_workers(self):
        """
        Orchestrator fans out to multiple worker children.
        """
        def process_chunk(**kwargs) -> dict:
            return {"processed": True}

        backends = create_test_backends("parallel")
        tools_registry = {"process_chunk": process_chunk}
        broadcast_signals_caller = setup_nodes(
            backends, tools_registry=tools_registry
        )

        execution_id = orchestrate(
            config=parallel_workflows,
            initial_workflow_name="orchestrator_workflow",
            initial_signals=["START"],
            initial_context={
                "data_chunk_a": {"id": "a"},
                "data_chunk_b": {"id": "b"},
                "data_chunk_c": {"id": "c"},
            },
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        # All workers should start
        assert "START_WORKER_A" in signals
        assert "START_WORKER_B" in signals
        assert "START_WORKER_C" in signals

        backends.cleanup_all()


class TestVersionRouting:
    """Test version-based workflow routing."""

    def test_routes_to_v1_when_specified(self):
        """
        Routes to processor_v1 when api_version is 'v1'.
        """
        def stub_llm(prompt: str, config: dict) -> str:
            if "v1 legacy format" in prompt:
                return '{"response": "v1 response"}'
            return '{"response": "unknown"}'

        call_llm = create_call_llm(stub=stub_llm)
        backends = create_test_backends("version_v1")
        broadcast_signals_caller = setup_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=version_routing,
            initial_workflow_name="entry_workflow",
            initial_signals=["START"],
            initial_context={"api_version": "v1", "request": "do something"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "USE_V1" in signals
        assert "COMPLETE" in signals

        backends.cleanup_all()

    def test_routes_to_v2_when_specified(self):
        """
        Routes to processor_v2 when api_version is 'v2'.
        """
        def stub_llm(prompt: str, config: dict) -> str:
            if "enhanced capabilities" in prompt:
                return '{"response": "v2 response"}'
            return '{"response": "unknown"}'

        call_llm = create_call_llm(stub=stub_llm)
        backends = create_test_backends("version_v2")
        broadcast_signals_caller = setup_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=version_routing,
            initial_workflow_name="entry_workflow",
            initial_signals=["START"],
            initial_context={"api_version": "v2", "request": "do something"},
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "USE_V2" in signals
        assert "COMPLETE" in signals

        backends.cleanup_all()

    def test_routes_to_latest_when_no_version(self):
        """
        Routes to latest (v2) when api_version is not specified.
        """
        def stub_llm(prompt: str, config: dict) -> str:
            if "enhanced capabilities" in prompt:
                return '{"response": "latest response"}'
            return '{"response": "unknown"}'

        call_llm = create_call_llm(stub=stub_llm)
        backends = create_test_backends("version_latest")
        broadcast_signals_caller = setup_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=version_routing,
            initial_workflow_name="entry_workflow",
            initial_signals=["START"],
            initial_context={"request": "do something"},  # No api_version
            backends=backends,
            broadcast_signals_caller=broadcast_signals_caller,
        )

        signals = extract_signals(backends, execution_id)

        assert "USE_LATEST" in signals
        assert "COMPLETE" in signals

        backends.cleanup_all()
