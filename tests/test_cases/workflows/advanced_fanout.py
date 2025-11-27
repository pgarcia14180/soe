"""
Workflow definitions for Fan-Out / Fan-In advanced patterns.

These workflows are used in both documentation and tests.
"""

# =============================================================================
# FAN-OUT / FAN-IN WITH TOOL AGGREGATION
# =============================================================================

FAN_OUT_TOOL_AGGREGATION = """
main_workflow:
  SpawnWorkers:
    node_type: child
    event_triggers: [START]
    child_workflow_name: worker_workflow
    child_initial_signals: [START]
    fan_out_field: items_to_process
    child_input_field: current_item
    signals_to_parent: [WORKER_DONE]
    context_updates_to_parent: [worker_result]

  CheckCompletion:
    node_type: router
    event_triggers: [WORKER_DONE]
    event_emissions:
      - condition: "{{ context.worker_result | accumulated | length == context.items_to_process | accumulated | length }}"
        signal_name: ALL_DONE
      - condition: "{{ context.worker_result | accumulated | length < context.items_to_process | accumulated | length }}"
        signal_name: WAITING

  AggregateResults:
    node_type: tool
    event_triggers: [ALL_DONE]
    tool_name: aggregate
    context_parameter_field: worker_result
    output_field: final_result
    event_emissions:
      - signal_name: COMPLETE

worker_workflow:
  ProcessItem:
    node_type: tool
    event_triggers: [START]
    tool_name: process_item
    context_parameter_field: current_item
    output_field: worker_result
    event_emissions:
      - signal_name: WORKER_DONE
"""

# =============================================================================
# THE JUDGE PATTERN (LLM SELECTION)
# =============================================================================

JUDGE_PATTERN = """
main_workflow:
  GenerateTaglines:
    node_type: child
    event_triggers: [START]
    child_workflow_name: creative_workflow
    child_initial_signals: [START]
    fan_out_field: prompts
    child_input_field: creative_prompt
    signals_to_parent: [TAGLINE_READY]
    context_updates_to_parent: [tagline]

  WaitForTaglines:
    node_type: router
    event_triggers: [TAGLINE_READY]
    event_emissions:
      - condition: "{{ context.tagline | accumulated | length == context.prompts | accumulated | length }}"
        signal_name: ALL_TAGLINES_READY

  SelectBest:
    node_type: llm
    event_triggers: [ALL_TAGLINES_READY]
    prompt: |
      You are a marketing expert. Review these tagline options:
      {% for t in context.tagline | accumulated %}
      Option {{ loop.index }}: {{ t }}
      {% endfor %}

      Select the best tagline and explain why in JSON format.
    output_field: winner
    event_emissions:
      - signal_name: COMPLETE

creative_workflow:
  GenerateOne:
    node_type: llm
    event_triggers: [START]
    prompt: |
      {{ context.creative_prompt }}

      Generate a creative tagline. Output as JSON with key "tagline".
    output_field: tagline
    event_emissions:
      - signal_name: TAGLINE_READY
"""

# =============================================================================
# MAP-REDUCE PATTERN
# =============================================================================

MAP_REDUCE_PATTERN = """
main_workflow:
  ProcessChunks:
    node_type: child
    event_triggers: [START]
    child_workflow_name: mapper_workflow
    child_initial_signals: [START]
    fan_out_field: data_chunks
    child_input_field: chunk
    signals_to_parent: [CHUNK_DONE]
    context_updates_to_parent: [chunk_result]

  WaitForMappers:
    node_type: router
    event_triggers: [CHUNK_DONE]
    event_emissions:
      - condition: "{{ context.chunk_result | accumulated | length == context.data_chunks | accumulated | length }}"
        signal_name: MAP_COMPLETE

  ReduceResults:
    node_type: tool
    event_triggers: [MAP_COMPLETE]
    tool_name: reduce_results
    context_parameter_field: chunk_result
    output_field: final_summary
    event_emissions:
      - signal_name: COMPLETE

mapper_workflow:
  ProcessOneChunk:
    node_type: tool
    event_triggers: [START]
    tool_name: process_chunk
    context_parameter_field: chunk
    output_field: chunk_result
    event_emissions:
      - signal_name: CHUNK_DONE
"""
