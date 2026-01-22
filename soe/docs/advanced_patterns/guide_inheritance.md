
# Advanced Pattern: Configuration and Context Inheritance

This guide covers inheritance patterns for workflow chaining and multi-phase execution using SOE's `inherit_config_from_id` and `inherit_context_from_id` parameters.

## The Hidden Power: Execution Chaining

Until now, each `orchestrate()` call required a full config. However, SOE supports **inheritance** between executions, enabling:

- **Workflow Chaining**: Run Phase 2 using Phase 1's config (workflows, identities, schema)
- **Context Sharing**: Continue with existing context data from a previous execution
- **Operational Reset**: Always start fresh operational counters even when inheriting context

This architecture enables powerful multi-phase patterns without re-sending configuration.

---

## The Two Inheritance Parameters

| Parameter | Inherits | Behavior |
|-----------|----------|----------|
| `inherit_config_from_id` | Workflows, identities, context_schema | Config becomes optional |
| `inherit_context_from_id` | Context fields (excludes `__operational__`) | **Always** resets operational state |

**Key Rule**: At least one of `config` or `inherit_config_from_id` must be provided.

---

## Pattern 1: Config Inheritance

Inherit workflows, identities, and context_schema from an existing execution.

### The Workflow

```yaml
workflows:
  main_workflow:
    ProcessData:
      node_type: tool
      event_triggers: [START]
      tool_name: process
      context_parameter_field: input_data
      output_field: result
      event_emissions:
        - signal_name: PROCESSED

    Complete:
      node_type: router
      event_triggers: [PROCESSED]
      event_emissions:
        - signal_name: COMPLETE

identities:
  assistant: "You are a helpful assistant."
  analyst: "You are a data analyst."

context_schema:
  input_data:
    type: object
    description: "Input data to process"
  result:
    type: object
    description: "Processing result"
```

### Usage: First Execution

```python
# First execution - establishes config
first_id = orchestrate(
    config=workflow_config,
    initial_workflow_name="main_workflow",
    initial_signals=["START"],
    initial_context={"input_data": {"value": "test1"}},
    backends=backends,
    broadcast_signals_caller=broadcast,
)
```

### Usage: Inherited Execution

```python
# Second execution - inherits config, no need to resend
second_id = orchestrate(
    config=None,  # Not needed!
    initial_workflow_name="main_workflow",
    initial_signals=["START"],
    initial_context={"input_data": {"value": "test2"}},
    backends=backends,
    broadcast_signals_caller=broadcast,
    inherit_config_from_id=first_id,  # <-- Inherit from first
)
```

**What gets inherited:**
- Workflows registry (all workflow definitions)
- Identities (LLM system prompts)
- Context schema (field definitions)

---

## Pattern 2: Context Inheritance

Inherit context from an existing execution, but **always** reset operational state.

### The Workflow

```yaml
workflows:
  main_workflow:
    Step1:
      node_type: tool
      event_triggers: [START]
      tool_name: step1_tool
      output_field: step1_result
      event_emissions:
        - signal_name: STEP1_DONE

    Step2:
      node_type: tool
      event_triggers: [STEP1_DONE]
      tool_name: step2_tool
      context_parameter_field: step1_result
      output_field: step2_result
      event_emissions:
        - signal_name: COMPLETE

  retry_workflow:
    RetryStep2:
      node_type: tool
      event_triggers: [START]
      tool_name: step2_tool_v2
      context_parameter_field: step1_result
      output_field: step2_result
      event_emissions:
        - signal_name: RETRY_COMPLETE
```

### Usage: Retry with Existing Context

```python
# First execution - builds up context
first_id = orchestrate(
    config=workflow_config,
    initial_workflow_name="main_workflow",
    initial_signals=["START"],
    initial_context={},
    backends=backends,
    broadcast_signals_caller=broadcast,
)

# Second execution - inherits context, runs retry workflow
second_id = orchestrate(
    config=None,
    initial_workflow_name="retry_workflow",
    initial_signals=["START"],
    initial_context={},
    backends=backends,
    broadcast_signals_caller=broadcast,
    inherit_config_from_id=first_id,
    inherit_context_from_id=first_id,  # <-- Inherit context too
)
```

**Critical**: `inherit_context_from_id` **always** resets `__operational__`:
- Fresh signal list
- Fresh counters (llm_calls, tool_calls, errors)
- New main_execution_id

This ensures each execution has its own operational tracking.

---

## Pattern 3: Multi-Phase Execution

Combine both inheritance types for complex, multi-phase workflows.

### The Workflow

```yaml
workflows:
  phase1_workflow:
    Analyze:
      node_type: llm
      event_triggers: [START]
      identity: analyst
      prompt: "Analyze this data: &#123;&#123; context.raw_data &#125;&#125;"
      output_field: analysis
      event_emissions:
        - signal_name: ANALYSIS_DONE

    Validate:
      node_type: tool
      event_triggers: [ANALYSIS_DONE]
      tool_name: validate_analysis
      context_parameter_field: analysis
      output_field: validated_analysis
      event_emissions:
        - signal_name: PHASE1_COMPLETE

  phase2_workflow:
    Generate:
      node_type: llm
      event_triggers: [START]
      identity: writer
      prompt: "Based on analysis: &#123;&#123; context.validated_analysis &#125;&#125;, generate report"
      output_field: report
      event_emissions:
        - signal_name: REPORT_DONE

    Finalize:
      node_type: router
      event_triggers: [REPORT_DONE]
      event_emissions:
        - signal_name: PHASE2_COMPLETE

identities:
  analyst: "You are a data analyst. Focus on insights and patterns."
  writer: "You are a technical writer. Be clear and professional."

context_schema:
  raw_data:
    type: string
    description: "Raw data to analyze"
  analysis:
    type: object
    description: "Analysis results"
  validated_analysis:
    type: object
    description: "Validated analysis"
  report:
    type: string
    description: "Generated report"
```

### Usage: Phase 1 → Phase 2

```python
# Phase 1 - Analysis
phase1_id = orchestrate(
    config=multi_phase_config,
    initial_workflow_name="phase1_workflow",
    initial_signals=["START"],
    initial_context={"raw_data": "sample data"},
    backends=backends,
    broadcast_signals_caller=broadcast,
)

# Phase 2 - Generation (inherits everything)
phase2_id = orchestrate(
    config=None,
    initial_workflow_name="phase2_workflow",
    initial_signals=["START"],
    initial_context={},  # Uses Phase 1's context
    backends=backends,
    broadcast_signals_caller=broadcast,
    inherit_config_from_id=phase1_id,
    inherit_context_from_id=phase1_id,
)
```

**Benefits:**
- Phase 2 has access to Phase 1's `validated_analysis`
- Phase 2 uses same identities (`analyst`, `writer`)
- Phase 2 has fresh operational state for clean tracking

---

## Pattern 4: Identity Sharing Across Conversations

Inherit config to share identities across multiple conversation executions.

### The Workflow

```yaml
workflows:
  conversation_workflow:
    FirstMessage:
      node_type: llm
      event_triggers: [START]
      identity: assistant
      prompt: "User says: &#123;&#123; context.user_message &#125;&#125;"
      output_field: assistant_response
      event_emissions:
        - signal_name: RESPONDED

    Complete:
      node_type: router
      event_triggers: [RESPONDED]
      event_emissions:
        - signal_name: CONVERSATION_DONE

  followup_workflow:
    FollowUp:
      node_type: llm
      event_triggers: [START]
      identity: assistant
      prompt: "User follows up: &#123;&#123; context.followup_message &#125;&#125;"
      output_field: followup_response
      event_emissions:
        - signal_name: FOLLOWUP_DONE

identities:
  assistant: "You are a helpful assistant. Be concise and friendly."
```

### Usage: Continued Conversation

```python
# First conversation
first_id = orchestrate(
    config=conversation_config,
    initial_workflow_name="conversation_workflow",
    initial_signals=["START"],
    initial_context={"user_message": "Hello"},
    backends=backends,
    broadcast_signals_caller=broadcast,
)

# Follow-up conversation (same identity definitions)
second_id = orchestrate(
    config=None,
    initial_workflow_name="followup_workflow",
    initial_signals=["START"],
    initial_context={"followup_message": "Tell me more"},
    backends=backends,
    broadcast_signals_caller=broadcast,
    inherit_config_from_id=first_id,
)
```

---

## Override Behavior

### Config Override

If both `config` and `inherit_config_from_id` are provided, `config` takes precedence:

```python
# Inherits, then overrides with new config
orchestrate(
    config=new_config,  # <-- This wins
    initial_workflow_name="workflow",
    initial_signals=["START"],
    initial_context={},
    backends=backends,
    broadcast_signals_caller=broadcast,
    inherit_config_from_id=old_id,  # <-- Loaded first, then overridden
)
```

### Context Append (History Preservation)

`initial_context` fields are **appended** to inherited context history using `set_field()`. This preserves the full history chain:

```python
# Inherits context, appends new values to history
orchestrate(
    config=None,
    initial_workflow_name="retry_workflow",
    initial_signals=["START"],
    initial_context={"user_input": "new message"},  # <-- Appends to history
    backends=backends,
    broadcast_signals_caller=broadcast,
    inherit_config_from_id=first_id,
    inherit_context_from_id=first_id,
)

# Result: context["user_input"] = ["old message", "new message"]
# Reading with get_field() returns "new message" (latest)
# Reading with get_accumulated() returns ["old message", "new message"] (full history)
```

---

## Validation Rules

| Scenario | Result |
|----------|--------|
| `config=None`, `inherit_config_from_id=None` | **Error**: Must provide one |
| `inherit_config_from_id="nonexistent"` | **Error**: Execution not found |
| `inherit_context_from_id="nonexistent"` | **Error**: Context not found |
| `inherit_context_from_id` without `inherit_config_from_id` | Valid if `config` provided |

---

## When to Use Each Pattern

| Use Case | Pattern |
|----------|---------|
| Run same workflow with different inputs | Config inheritance only |
| Retry failed step with existing context | Config + context inheritance |
| Multi-phase pipelines | Config + context inheritance |
| Share identities across API calls | Config inheritance only |
| Fresh start with same config | Config inheritance only (no context) |
| Continue with old version of workflow | Config inheritance from old execution |
| Continue with evolved workflow | Config inheritance from evolved execution |

### Version Management with Inheritance

Inheritance enables interesting version management patterns:

1. **Continue with Old Version**: If you have a running process and update your workflow definition, existing executions continue with their captured config. New executions use the new definition.

2. **Continue with Evolved Version**: If a workflow self-evolves (using `soe_inject_workflow` or `inject_node`), you can start new executions that inherit the evolved config:

```python
# Original execution - workflow may have self-evolved
evolved_id = orchestrate(
    config=original_config,
    initial_workflow_name="self_evolving_workflow",
    initial_signals=["START"],
    ...
)

# New execution inherits the evolved config (including injected nodes)
new_execution = orchestrate(
    config=None,
    initial_workflow_name="self_evolving_workflow",
    initial_signals=["START"],
    inherit_config_from_id=evolved_id,  # Gets evolved workflow
    ...
)
```

---

## Best Practices

1. **Always reset operational for retries**: Use `inherit_context_from_id` to get fresh counters
2. **Store execution IDs**: Keep track of execution IDs for chaining
3. **Explicit is better**: When in doubt, provide full config
4. **Test inheritance chains**: Multi-phase tests catch subtle bugs
5. **Don't assume context shape**: Validate inherited context before use
