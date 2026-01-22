
# Advanced Pattern: Fan-Out, Fan-In & Aggregations

This guide covers advanced patterns for parallel processing and data aggregation using SOE's context history features.

## The Hidden Power of Context: History Lists

Until now, we've treated context fields as single values. However, SOE actually stores every update to a field in a **history list**.

- **Standard Behavior:** `{{ context.field }}` returns the *last* value (most recent update).
- **Advanced Behavior:** You can access the *full history* of updates to perform aggregations, fan-out operations, and complex logic.

This architecture enables powerful distributed patterns without complex infrastructure code.

---

## Pattern 1: Fan-Out (Parallel Processing)

Fan-Out allows you to spawn a child workflow for *each item* in a context field's history. This is true distributable parallelism.

### The `fan_out_field` Parameter

The `child` node type has a special parameter `fan_out_field`.

```yaml
SpawnWorkers:
  node_type: child
  event_triggers: [DATA_READY]
  child_workflow_name: worker_workflow

  # The Magic: Spawn one child for each item in this field's history
  fan_out_field: items_to_process

  # Each child receives one item in this field
  child_input_field: current_item

  # Optional: Sleep between spawns to prevent rate limits
  spawn_interval: 0.1

  # Standard child communication
  signals_to_parent: [WORKER_DONE]
  context_updates_to_parent: [worker_results]
```

**How it works:**
1. If `items_to_process` has 5 items in its history.
2. The node spawns 5 independent child workflows.
3. Each child gets one item injected into `current_item`.

---

## Pattern 2: Fan-In (Waiting for Completion)

To synchronize parallel workers, the parent workflow must wait until all children have completed.

### The Router Check

Use a `router` to compare the number of results with the number of input items.

```yaml
CheckCompletion:
  node_type: router
  event_triggers: [WORKER_DONE]
  event_emissions:
    # Compare the length of the results history vs input history
    - condition: "{{ context.worker_results | accumulated | length == context.items_to_process | accumulated | length }}"
      signal_name: ALL_DONE

    - condition: "{{ context.worker_results | accumulated | length < context.items_to_process | accumulated | length }}"
      signal_name: WAITING
```

**Note:** The `| accumulated` filter returns the full history list of a field. The `| length` filter then returns the count of items in that list.

---

## Pattern 3: Aggregation (Processing History)

Once data is collected, you often need to aggregate it (summarize, vote, select).

### Tool Aggregation

You can configure a tool to receive the *full history list* instead of just the last value.

**Tool Registry:**
```python
tools_registry = {
    "summarize_results": {
        "function": my_summary_function,
        "process_accumulated": True  # <--- This enables history access
    }
}
```

When `process_accumulated: True`, the tool function receives the entire history list as its first positional argument.

### LLM Aggregation (The "Judge" Pattern)

You can also pass the full history to an LLM prompt using the `| accumulated` filter.

```yaml
JudgeBestResult:
  node_type: llm
  event_triggers: [ALL_DONE]
  prompt: |
    Here are the proposed solutions:
    {{ context.worker_results | accumulated }}

    Please select the best solution and explain why.
  output_field: best_solution
```

---

## Complete Workflow Examples

### Example 1: Fan-Out / Fan-In with Tool Aggregation

This complete workflow demonstrates the full pattern: spawn workers, wait for completion, aggregate results.

```yaml
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
      - condition: "&#123;&#123; context.worker_result | accumulated | length == context.items_to_process | accumulated | length &#125;&#125;"
        signal_name: ALL_DONE
      - condition: "&#123;&#123; context.worker_result | accumulated | length < context.items_to_process | accumulated | length &#125;&#125;"
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
```

### Example 2: The Judge Pattern (LLM Selection)

This workflow generates multiple options and uses an LLM to select the best one.

```yaml
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
      - condition: "&#123;&#123; context.tagline | accumulated | length == context.prompts | accumulated | length &#125;&#125;"
        signal_name: ALL_TAGLINES_READY

  SelectBest:
    node_type: llm
    event_triggers: [ALL_TAGLINES_READY]
    prompt: |
      You are a marketing expert. Review these tagline options:
      &#123;% for t in context.tagline | accumulated %&#125;
      Option &#123;&#123; loop.index &#125;&#125;: &#123;&#123; t &#125;&#125;
      &#123;% endfor %&#125;

      Select the best tagline and explain why in JSON format.
    output_field: winner
    event_emissions:
      - signal_name: COMPLETE

creative_workflow:
  GenerateOne:
    node_type: llm
    event_triggers: [START]
    prompt: |
      &#123;&#123; context.creative_prompt &#125;&#125;

      Generate a creative tagline. Output as JSON with key "tagline".
    output_field: tagline
    event_emissions:
      - signal_name: TAGLINE_READY
```

### Example 3: Map-Reduce Pattern

This workflow processes data chunks in parallel and reduces to a single summary.

```yaml
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
      - condition: "&#123;&#123; context.chunk_result | accumulated | length == context.data_chunks | accumulated | length &#125;&#125;"
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
```

---

## Summary of New Parameters

### Child Node
| Parameter | Type | Description |
|-----------|------|-------------|
| `fan_out_field` | string | The context field to iterate over. Spawns one child per history item. |
| `child_input_field` | string | The field name in the child's context where the item will be injected. |
| `spawn_interval` | float | (Optional) Seconds to sleep between spawns to prevent throttling. |

### Tool Registry
| Key | Type | Description |
|-----|------|-------------|
| `process_accumulated` | bool | If True, the tool receives the full history list instead of the last value. |

### Jinja Filters
| Filter | Description |
|--------|-------------|
| `| accumulated` | Returns the full history list of the field. |
| `| accumulated | length` | Returns the number of items in the history list. |

---

## Non-Dynamic Fan-Out

You can create non-dynamic fan-out by explicitly defining child nodes for each worker. This is more verbose but provides explicit control:

```yaml
orchestrator:
  Start:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: SPAWN_WORKERS

  Worker1:
    node_type: child
    event_triggers: [SPAWN_WORKERS]
    child_workflow_name: worker_workflow
    child_initial_signals: [START]
    input_fields: [chunk_1]
    signals_to_parent: [WORKER_DONE]
    context_updates_to_parent: [result_1]

  Worker2:
    node_type: child
    event_triggers: [SPAWN_WORKERS]
    child_workflow_name: worker_workflow
    child_initial_signals: [START]
    input_fields: [chunk_2]
    signals_to_parent: [WORKER_DONE]
    context_updates_to_parent: [result_2]

  # ... more workers
```

**Trade-off**: Explicit control vs. verbose configuration. Use `fan_out_field` for dynamic scenarios.

---

## Related Patterns

For more complex multi-agent coordination patterns (voting, consensus, jury systems), see [Swarm Intelligence](swarm_intelligence.md).
