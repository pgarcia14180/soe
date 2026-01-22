# SOE Advanced Patterns: Self-Evolving Workflows

## Introduction

One of SOE's most powerful capabilities is **runtime workflow modification**. Because workflows are YAML text interpreted at runtime, they can be modified *during execution*.

This enables:
- **Deterministic injection** — Add predefined workflows/nodes based on conditions
- **LLM-driven generation** — Let an AI architect new workflow components
- **Self-improving systems** — Workflows that adapt based on performance
- **Self-awareness** — Workflows that understand their own capabilities via `soe_explore_docs`

---

## Self-Awareness with soe_explore_docs

Before a workflow can evolve intelligently, it needs to understand what's possible. The `soe_explore_docs` built-in enables **self-awareness**:

```yaml
SelfAwareAgent:
  node_type: agent
  event_triggers: [NEED_CAPABILITY]
  prompt: |
    The user needs: {{ context.user_request }}

    First, explore the documentation to understand what SOE can do.
    Then decide if we need to create a new workflow or modify existing ones.
  tools: [soe_explore_docs, soe_inject_workflow, soe_inject_node]
  output_field: evolution_result
```

**Why this matters**:
- Reduces the need for extensive prompting about SOE capabilities
- Agent can discover what node types, builtins, and patterns are available
- Works especially well with agent nodes that can iteratively explore

See [Built-in Tools: soe_explore_docs](../builtins/soe_explore_docs.md) for details.

---

## Built-in Injection Tools

SOE provides built-in tools for runtime modification:

| Tool | Purpose |
|------|---------|
| `soe_inject_workflow` | Add a complete new workflow to the registry |
| `soe_inject_node` | Add a node to an existing workflow |
| `soe_remove_workflow` | Remove a workflow from the registry |
| `soe_remove_node` | Remove a node from a workflow |
| `soe_get_workflows` | Query current workflow definitions |
| `call_tool` | Dynamically call any registered tool by name |

The `call_tool` builtin is particularly powerful for self-evolution: you can create a new tool and immediately have a node call it without modifying the workflow structure.

Both injection tools are created with factory functions that bind them to the current execution:

```python
from soe.builtin_tools.soe_inject_workflow import create_soe_inject_workflow_tool
from soe.builtin_tools.soe_inject_node import create_soe_inject_node_tool

# Create tools bound to the current execution
soe_inject_workflow = create_soe_inject_workflow_tool(execution_id, backends)
inject_node = create_soe_inject_node_tool(execution_id, backends)
```

---

## Pattern 1: Deterministic Workflow Injection

Inject a predefined workflow based on runtime conditions.

### The Workflow

```yaml
example_workflow:
  Start:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: soe_inject_workflow

  InjectNewWorkflow:
    node_type: tool
    event_triggers: [soe_inject_workflow]
    tool_name: soe_inject_workflow
    context_parameter_field: inject_params
    output_field: injection_result
    event_emissions:
      - signal_name: WORKFLOW_INJECTED

  Complete:
    node_type: router
    event_triggers: [WORKFLOW_INJECTED]
    event_emissions:
      - signal_name: DONE
```

### How It Works

1. **Start** — Router triggers `soe_inject_workflow`
2. **InjectNewWorkflow** — Tool node calls `soe_inject_workflow` with parameters from `inject_params` in context
3. **Complete** — Confirms injection and emits `DONE`

The `inject_params` context field must contain:
- `workflow_name`: Name for the new workflow
- `workflow_data`: YAML or JSON string with the workflow definition

### The Injected Workflow

The `workflow_data` in context contains the new workflow:

```yaml
InjectedWorkflow:
  ProcessData:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: INJECTED_COMPLETE
```

After injection, this workflow can be triggered by a child node or by switching the current workflow.

---

## Pattern 2: Deterministic Node Injection

Add a node to an existing workflow at runtime.

### The Workflow

```yaml
example_workflow:
  Start:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: INJECT_NODE

  InjectNewNode:
    node_type: tool
    event_triggers: [INJECT_NODE]
    tool_name: soe_inject_node
    context_parameter_field: inject_params
    output_field: injection_result
    event_emissions:
      - signal_name: NODE_INJECTED

  Complete:
    node_type: router
    event_triggers: [NODE_INJECTED]
    event_emissions:
      - signal_name: DONE
```

### How It Works

1. **Start** — Router triggers `INJECT_NODE`
2. **InjectNewNode** — Tool node calls `soe_inject_node` with parameters from `inject_params`:
   - `workflow_name`: Which workflow to modify
   - `node_name`: Name for the new node
   - `node_config_data`: The node configuration (YAML or JSON)
3. **Complete** — Confirms injection

### The Injected Node

```yaml
node_type: router
event_triggers: [TRIGGER_NEW_NODE]
event_emissions:
  - signal_name: NEW_NODE_COMPLETE
```

---

## Pattern 3: LLM-Driven Workflow Generation

The most powerful pattern: let an LLM generate workflow components.

### The Workflow

```yaml
example_workflow:
  Start:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: GENERATE_WORKFLOW

  GenerateWorkflow:
    node_type: llm
    event_triggers: [GENERATE_WORKFLOW]
    prompt: |
      You are a workflow architect. Generate a simple SOE workflow.

      The workflow should be named "&#123;&#123; context.workflow_name &#125;&#125;" and have:
      - A router node that triggers on START
      - Emit signal: GENERATED_COMPLETE

      Provide the workflow_name and the workflow_data (as YAML string).
    schema_name: Generated_WorkflowResponse
    output_field: inject_params
    event_emissions:
      - signal_name: WORKFLOW_GENERATED

  InjectGeneratedWorkflow:
    node_type: tool
    event_triggers: [WORKFLOW_GENERATED]
    tool_name: soe_inject_workflow
    context_parameter_field: inject_params
    output_field: injection_result
    event_emissions:
      - signal_name: INJECTION_COMPLETE

  Complete:
    node_type: router
    event_triggers: [INJECTION_COMPLETE]
    event_emissions:
      - signal_name: DONE
```

### How It Works

1. **GenerateWorkflow** — LLM node receives a prompt describing what to generate
2. **LLM Response** — Returns valid YAML for a new workflow, stored in `generated_workflow`
3. **PrepareInjection** — Router node assembles `inject_params` from the LLM output
4. **InjectGeneratedWorkflow** — Tool node injects the workflow using `inject_params`
5. **Complete** — The new workflow is now available

### The Prompt

The prompt instructs the LLM to generate valid SOE YAML:

```
You are a workflow architect. Generate a simple SOE workflow in YAML format.

The workflow should:
- Be named "{{ context.workflow_name }}"
- Have a router node that triggers on START
- Update context with: generated=true
- Emit signal: GENERATED_COMPLETE

Return ONLY valid YAML, no explanation.
```

### Safety Considerations

When using LLM-generated workflows:

1. **Validation** — SOE validates all workflows before execution
2. **Sandboxing** — Consider what node types the generated workflow can use
3. **Review** — Log generated workflows for human review
4. **Constraints** — Use specific prompts to limit what the LLM can generate

---

## Pattern 4: LLM-Driven Node Generation

Generate individual nodes rather than complete workflows:

```yaml
example_workflow:
  Start:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: GENERATE_NODE

  GenerateNode:
    node_type: llm
    event_triggers: [GENERATE_NODE]
    prompt: |
      You are a workflow architect. Generate a SOE node configuration.

      The node should:
      - Be a router node
      - Trigger on signal: &#123;&#123; context.trigger_signal &#125;&#125;
      - Emit signal: DYNAMIC_NODE_DONE

      Target workflow: &#123;&#123; context.target_workflow &#125;&#125;
      Node name: &#123;&#123; context.node_name &#125;&#125;

      Provide the workflow_name, node_name, and node_config_data (as YAML string).
    schema_name: Generated_NodeResponse
    output_field: inject_params
    event_emissions:
      - signal_name: NODE_GENERATED

  InjectGeneratedNode:
    node_type: tool
    event_triggers: [NODE_GENERATED]
    tool_name: soe_inject_node
    context_parameter_field: inject_params
    output_field: injection_result
    event_emissions:
      - signal_name: NODE_INJECTION_COMPLETE

  Complete:
    node_type: router
    event_triggers: [NODE_INJECTION_COMPLETE]
    event_emissions:
      - signal_name: DONE
```

This is more surgical—add specific capabilities to existing workflows based on context.

---

## Use Cases

### Self-Healing Workflows

```yaml
MonitorPerformance:
  node_type: router
  event_triggers: [CHECK_HEALTH]
  event_emissions:
    - signal_name: PERFORMANCE_DEGRADED
      condition: "{{ context.error_rate > 0.1 }}"

GenerateFix:
  node_type: llm
  event_triggers: [PERFORMANCE_DEGRADED]
  prompt: |
    The workflow has error rate {{ context.error_rate }}.
    Generate a retry node with exponential backoff...
```

### Dynamic Skill Acquisition

```yaml
CheckCapability:
  node_type: router
  event_triggers: [NEW_TASK]
  event_emissions:
    - signal_name: NEED_NEW_SKILL
      condition: "{{ context.task_type not in context.available_skills }}"

AcquireSkill:
  node_type: llm
  event_triggers: [NEED_NEW_SKILL]
  prompt: |
    Generate a workflow for handling {{ context.task_type }} tasks...
```

### A/B Testing Workflows

Inject variant workflows and track which performs better:

```yaml
SelectVariant:
  node_type: tool
  event_triggers: [START]
  tool_name: select_ab_variant
  output_field: variant_workflow

InjectVariant:
  node_type: tool
  event_triggers: [VARIANT_SELECTED]
  tool_name: soe_inject_workflow
  input_fields: [variant_name, variant_workflow]
```

---

## Best Practices

1. **Start Deterministic** — Begin with predefined injections before using LLM generation
2. **Validate Outputs** — Always check LLM-generated YAML is valid before injection
3. **Log Everything** — Record all injections for debugging and audit
4. **Limit Scope** — Constrain what the LLM can generate (node types, signals)
5. **Test Thoroughly** — Create test cases for injection scenarios

---

## Summary

| Pattern | Complexity | Use Case |
|---------|------------|----------|
| Deterministic Workflow Injection | Low | Plugin systems, feature flags |
| Deterministic Node Injection | Low | Dynamic capability extension |
| LLM Workflow Generation | High | Self-evolving systems, adaptive behavior |
| LLM Node Generation | Medium | Targeted self-improvement |

Self-evolving workflows unlock SOE's full potential as a **protocol for intelligence**—systems that can modify their own behavior based on experience.
