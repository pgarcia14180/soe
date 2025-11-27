
# Built-in: Workflow Modification

## Runtime Workflow Evolution

These built-in tools enable workflows to **modify themselves at runtime**. This is the core capability for self-evolution—a workflow can inspect its structure, add new nodes, inject new workflows, and remove obsolete components.

---

## Available Tools

| Tool | Purpose |
|------|---------|
| `soe_get_workflows` | Query registered workflow definitions |
| `soe_inject_workflow` | Add new workflows to the registry |
| `soe_inject_node` | Add or modify nodes in existing workflows |
| `soe_remove_workflow` | Remove workflows from registry |
| `soe_remove_node` | Remove nodes from workflows |

---

## soe_get_workflows

Query the current workflow registry to see all registered workflows and their structure.

```yaml
example_workflow:
  GetWorkflows:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_get_workflows
    output_field: workflows_list
    event_emissions:
      - signal_name: WORKFLOWS_RETRIEVED
```

Returns a dictionary of all registered workflows with their node configurations.

### Use Cases

- **Introspection** — See what workflows are available
- **Validation** — Check if a workflow exists before spawning it
- **Evolution planning** — Understand current structure before modifying

---

## soe_inject_workflow

Add a completely new workflow to the registry at runtime.

```yaml
example_workflow:
  InjectNew:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_inject_workflow
    context_parameter_field: workflow_to_inject
    output_field: injection_result
    event_emissions:
      - signal_name: WORKFLOW_INJECTED
        condition: "&#123;&#123; result.status == 'success' &#125;&#125;"
      - signal_name: INJECTION_FAILED
        condition: "&#123;&#123; result.status != 'success' &#125;&#125;"
```

### Context Setup

The `workflow_to_inject` context field should contain:

```python
{
    "workflow_name": "new_workflow",
    "workflow_definition": {
        "StartNode": {
            "node_type": "router",
            "event_triggers": ["START"],
            "event_emissions": [{"signal_name": "READY"}]
        }
    }
}
```

### Use Cases

- **Dynamic workflow creation** — LLM designs new workflows
- **Plugin systems** — Load workflows based on configuration
- **A/B testing** — Inject alternative workflow versions

---

## soe_inject_node

Add or modify a single node in an existing workflow.

```yaml
example_workflow:
  InjectNode:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_inject_node
    context_parameter_field: node_to_inject
    output_field: node_injection_result
    event_emissions:
      - signal_name: NODE_INJECTED
        condition: "&#123;&#123; result.status == 'success' &#125;&#125;"
```

### Context Setup

The `node_to_inject` context field should contain:

```python
{
    "workflow_name": "example_workflow",
    "node_name": "NewProcessor",
    "node_configuration": {
        "node_type": "tool",
        "event_triggers": ["PROCESS"],
        "tool_name": "process_data",
        "output_field": "result",
        "event_emissions": [{"signal_name": "PROCESSED"}]
    }
}
```

### Use Cases

- **Incremental evolution** — Add nodes one at a time
- **Patching** — Modify existing node behavior
- **Extension** — Add new capabilities to existing workflows

---

## soe_remove_workflow

Remove a workflow from the registry.

```yaml
example_workflow:
  RemoveOldWorkflow:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_remove_workflow
    context_parameter_field: remove_params
    output_field: removal_result
    event_emissions:
      - signal_name: WORKFLOW_REMOVED
```

---

## soe_remove_node

Remove a specific node from a workflow.

```yaml
example_workflow:
  RemoveNode:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_remove_node
    context_parameter_field: remove_params
    output_field: node_removal_result
    event_emissions:
      - signal_name: NODE_REMOVED
```

---

## Evolution Pattern

Combine these tools for full self-evolution:

```yaml
evolving_workflow:
  AnalyzeState:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_get_workflows
    output_field: current_state
    event_emissions:
      - signal_name: STATE_ANALYZED

  ApplyImprovement:
    node_type: tool
    event_triggers: [STATE_ANALYZED]
    tool_name: soe_inject_node
    context_parameter_field: designed_node
    output_field: injection_result
    event_emissions:
      - signal_name: EVOLVED
```

---

## Related

- [Built-in Tools Overview](../guide_11_builtins.md) — All available built-ins
- [Self-Evolving Workflows](../advanced_patterns/self_evolving_workflows.md) — Complete evolution patterns
