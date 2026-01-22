
# Built-in: Context Management

## Execution State Control

These built-in tools enable workflows to **manage execution context**. Context is the shared state that flows through nodes—reading, updating, and copying it enables sophisticated patterns like parallel execution, state persistence, and dynamic behavior.

---

## Available Tools

| Tool | Purpose |
|------|---------|
| `soe_get_context` | Read the current execution context |
| `soe_update_context` | Modify context fields |
| `soe_copy_context` | Clone context for parallel execution |
| `soe_list_contexts` | Discover available contexts |

---

## soe_get_context

Read the current execution context snapshot.

```yaml
example_workflow:
  GetContext:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_get_context
    output_field: current_context
    event_emissions:
      - signal_name: CONTEXT_RETRIEVED
```

Returns the full context dictionary including all fields and `__operational__` state.

### Use Cases

- **Introspection** — Let LLMs see full workflow state
- **Debugging** — Inspect context during development
- **Decision making** — Base routing on complete state

---

## soe_update_context

Modify context fields programmatically.

```yaml
example_workflow:
  UpdateContext:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_update_context
    context_parameter_field: context_updates
    output_field: update_result
    event_emissions:
      - signal_name: CONTEXT_UPDATED
```

### Context Setup

The `context_updates` field should contain key-value pairs:

```python
{
    "new_field": "new_value",
    "counter": 42,
    "nested": {"key": "value"}
}
```

### Use Cases

- **State injection** — Add computed values to context
- **Reset/clear** — Modify state for retry patterns
- **Enrichment** — Add metadata or derived values

---

## soe_copy_context

Clone context for parallel execution or branching.

```yaml
example_workflow:
  CopyContext:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_copy_context
    context_parameter_field: copy_params
    output_field: copy_result
    event_emissions:
      - signal_name: CONTEXT_COPIED
```

### Context Setup

The `copy_params` field specifies target:

```python
{
    "target_execution_id": "new_execution_123",
    "fields_to_copy": ["user_data", "config"]  # Optional: copy specific fields only
}
```

### Use Cases

- **Parallel workers** — Each worker gets its own context copy
- **Branching** — Create alternative execution paths
- **Snapshotting** — Save state before risky operations

---

## soe_list_contexts

Discover available contexts (useful for multi-execution patterns).

```yaml
example_workflow:
  ListAllContexts:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_list_contexts
    output_field: available_contexts
    event_emissions:
      - signal_name: CONTEXTS_LISTED
```

Returns a list of execution IDs with contexts.

### Use Cases

- **Orchestration** — Manage multiple parallel executions
- **Cleanup** — Find old contexts to archive
- **Aggregation** — Collect results from multiple executions

---

## Context Patterns

### Context Inspection for LLMs

Let an LLM reason about full state:

```yaml
reflective_workflow:
  GatherState:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_get_context
    output_field: full_state
    event_emissions:
      - signal_name: STATE_GATHERED
```

---

## Related

- [Built-in Tools Overview](../guide_11_builtins.md) — All available built-ins
- [Operational Features](../advanced_patterns/operational.md) — Context structure details
