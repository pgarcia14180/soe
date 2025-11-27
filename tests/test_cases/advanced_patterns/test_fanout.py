"""
Tests for Fan-Out / Fan-In Advanced Patterns.

These tests verify:
1. fan_out_field parameter on child node
2. | length filter for history lists in Jinja
3. | accumulated filter for history access in prompts
4. process_accumulated in tool registry
"""

import json
from soe import orchestrate
from tests.test_cases.lib import (
    create_test_backends,
    create_nodes,
    extract_signals,
    create_call_llm,
)
from tests.test_cases.workflows.advanced_fanout import (
    FAN_OUT_TOOL_AGGREGATION,
    JUDGE_PATTERN,
    MAP_REDUCE_PATTERN,
)


class TestFanOutFanIn:
    """Tests for the basic fan-out/fan-in pattern with tool aggregation."""

    def test_fan_out_spawns_child_per_item(self):
        """
        Fan-out should spawn one child workflow per item in the field's history.

        Given 3 items in items_to_process, 3 children should run,
        and the aggregator should receive all 3 results.
        """
        def process_item(item_name: str) -> dict:
            return {"processed": f"done:{item_name}"}

        def aggregate(results: list) -> dict:
            # results should be the full list of worker outputs
            return {"count": len(results), "items": results}

        tools_registry = {
            "process_item": process_item,
            "aggregate": {
                "function": aggregate,
                "process_accumulated": True
            }
        }

        backends = create_test_backends("fan_out_basic")
        nodes, broadcast = create_nodes(backends, tools_registry=tools_registry)

        execution_id = orchestrate(
            config=FAN_OUT_TOOL_AGGREGATION,
            initial_workflow_name="main_workflow",
            initial_signals=["START"],
            initial_context={
                # Each item is a dict with the tool's parameter names
                "items_to_process": [
                    {"item_name": "item1"},
                    {"item_name": "item2"},
                    {"item_name": "item3"}
                ]
            },
            backends=backends,
            broadcast_signals_caller=broadcast,
        )

        signals = extract_signals(backends, execution_id)
        context = backends.context.get_context(execution_id)

        # Verify completion
        assert "COMPLETE" in signals
        assert "ALL_DONE" in signals

        # Verify aggregation received all results
        final = context["final_result"][-1]
        assert final["count"] == 3

        backends.cleanup_all()


class TestJudgePattern:
    """Tests for the Judge pattern (LLM selection from accumulated results)."""

    def test_judge_sees_all_accumulated_options(self):
        """
        The judge LLM should receive all accumulated taglines in its prompt.

        The | accumulated filter should provide the full list for iteration.
        """
        received_prompts = []

        def stub_llm(prompt: str, config: dict) -> str:
            received_prompts.append(prompt)
            # Creative workflow generates taglines
            if "Generate a creative tagline" in prompt:
                return json.dumps({"tagline": f"Tagline for: {prompt[:20]}"})
            # Judge selects winner
            if "Review these tagline options" in prompt:
                return json.dumps({
                    "winner": "Option 1",
                    "reason": "Most creative"
                })
            return json.dumps({"result": "ok"})

        call_llm = create_call_llm(stub=stub_llm)
        backends = create_test_backends("judge_pattern")
        nodes, broadcast = create_nodes(backends, call_llm=call_llm)

        execution_id = orchestrate(
            config=JUDGE_PATTERN,
            initial_workflow_name="main_workflow",
            initial_signals=["START"],
            initial_context={
                "prompts": ["Be bold", "Be simple", "Be creative"]
            },
            backends=backends,
            broadcast_signals_caller=broadcast,
        )

        signals = extract_signals(backends, execution_id)

        # Verify completion
        assert "COMPLETE" in signals

        # Verify the judge prompt contained all taglines
        judge_prompt = [p for p in received_prompts if "Review these tagline options" in p]
        assert len(judge_prompt) == 1
        assert "Option 1:" in judge_prompt[0]
        assert "Option 2:" in judge_prompt[0]
        assert "Option 3:" in judge_prompt[0]

        backends.cleanup_all()


class TestMapReduce:
    """Tests for the Map-Reduce pattern."""

    def test_map_reduce_processes_all_chunks(self):
        """
        Map phase should process all chunks in parallel,
        Reduce phase should aggregate all chunk results.
        """
        def process_chunk(text: str) -> dict:
            return {"word_count": len(text.split())}

        def reduce_results(results: list) -> dict:
            total = sum(r["word_count"] for r in results)
            return {"total_words": total, "chunk_count": len(results)}

        tools_registry = {
            "process_chunk": process_chunk,
            "reduce_results": {
                "function": reduce_results,
                "process_accumulated": True
            }
        }

        backends = create_test_backends("map_reduce")
        nodes, broadcast = create_nodes(backends, tools_registry=tools_registry)

        execution_id = orchestrate(
            config=MAP_REDUCE_PATTERN,
            initial_workflow_name="main_workflow",
            initial_signals=["START"],
            initial_context={
                # Each item is a dict with the tool's parameter names
                "data_chunks": [
                    {"text": "hello world"},
                    {"text": "foo bar baz"},
                    {"text": "one two three four"}
                ]
            },
            backends=backends,
            broadcast_signals_caller=broadcast,
        )

        signals = extract_signals(backends, execution_id)
        context = backends.context.get_context(execution_id)

        # Verify completion
        assert "COMPLETE" in signals

        # Verify reduce aggregated correctly
        final = context["final_summary"][-1]
        assert final["chunk_count"] == 3
        assert final["total_words"] == 9  # 2 + 3 + 4

        backends.cleanup_all()


class TestLengthFilter:
    """Tests for the | accumulated | length Jinja filter on history lists."""

    def test_length_filter_counts_history_items(self):
        """
        The | accumulated | length filter should return the number of items in the history,
        not the string length of the last value.
        """
        # This is implicitly tested by the fan-in router conditions
        # If | accumulated | length returned string length, the conditions would never match

        def process_item(item_name: str) -> dict:
            return {"result": item_name}

        def aggregate(results: list) -> dict:
            return {"count": len(results)}

        tools_registry = {
            "process_item": process_item,
            "aggregate": {
                "function": aggregate,
                "process_accumulated": True
            }
        }

        backends = create_test_backends("length_filter")
        nodes, broadcast = create_nodes(backends, tools_registry=tools_registry)

        execution_id = orchestrate(
            config=FAN_OUT_TOOL_AGGREGATION,
            initial_workflow_name="main_workflow",
            initial_signals=["START"],
            initial_context={
                # Each item is a dict with the tool's parameter names
                "items_to_process": [
                    {"item_name": "a"},
                    {"item_name": "b"}
                ]
            },
            backends=backends,
            broadcast_signals_caller=broadcast,
        )

        signals = extract_signals(backends, execution_id)

        # If | accumulated | length worked correctly, we should see ALL_DONE
        # If it returned string length, the condition would never match
        assert "ALL_DONE" in signals
        assert "COMPLETE" in signals

        backends.cleanup_all()
