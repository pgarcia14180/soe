
# SOE Guide: Chapter 9 - The Workflows Ecosystem

## Understanding the Big Picture

Before diving deeper into SOE, it's important to understand **why** workflows are structured the way they are. This chapter explains the ecosystem—how workflows relate to each other, how data persists, and how you can build sophisticated multi-workflow systems.

---

## Combined Config: The Recommended Pattern

The most powerful way to configure SOE is with **combined config**—a single structure containing workflows, context schemas, and identities:

```yaml
workflows:
  example_workflow:
    Analyze:
      node_type: llm
      event_triggers: [START]
      identity: analyst
      prompt: "Analyze: &#123;&#123; context.input &#125;&#125;"
      output_field: analysis
      event_emissions:
        - signal_name: ANALYZED

    Summarize:
      node_type: llm
      event_triggers: [ANALYZED]
      identity: analyst
      prompt: "Summarize the analysis: &#123;&#123; context.analysis &#125;&#125;"
      output_field: summary
      event_emissions:
        - signal_name: DONE

context_schema:
  input:
    type: string
    description: The input to analyze
  analysis:
    type: object
    description: Detailed analysis result
  summary:
    type: string
    description: A concise summary

identities:
  analyst: "You are a thorough analyst. Be precise and structured in your analysis."
```

### Why Combined Config?

1. **Single source of truth**: All configuration in one place
2. **Automatic setup**: Schemas and identities are saved to backends automatically
3. **Keyed by execution**: Child workflows can access parent's schemas and identities
4. **Clear structure**: Easy to understand what your workflow ecosystem contains

### Combined Config Sections

| Section | Purpose | Required |
|---------|---------|----------|
| `workflows` | Workflow definitions (nodes, signals) | Yes |
| `context_schema` | Field type validation for LLM outputs | No |
| `identities` | System prompts for LLM/Agent nodes | No |

---

## Multi-Workflow Ecosystems

When you call `orchestrate()`, you pass a **config**. This config can contain multiple workflow definitions:

```python
execution_id = orchestrate(
    config=my_config,                      # Contains MULTIPLE workflows
    initial_workflow_name="main_workflow", # Which one to start
    initial_signals=["START"],
    initial_context={...},
    backends=backends,
    broadcast_signals_caller=broadcast,
)
```

### Why Multiple Workflows?

The config is your **ecosystem**. Workflows can:

1. **Spawn children** — One workflow triggers another via child nodes
2. **Share definitions** — Common sub-workflows reused across your system
3. **Run in parallel** — Multiple child workflows executing simultaneously
4. **Share schemas and identities** — Via `main_execution_id` keying

### Example: Full Ecosystem Config

```yaml
workflows:
  main_workflow:
    Classifier:
      node_type: router
      event_triggers: [START]
      event_emissions:
        - signal_name: HANDLE_TEXT
          condition: "&#123;&#123; context.input_type == 'text' &#125;&#125;"
        - signal_name: HANDLE_IMAGE
          condition: "&#123;&#123; context.input_type == 'image' &#125;&#125;"

    DelegateToTextProcessor:
      node_type: child
      event_triggers: [HANDLE_TEXT]
      child_workflow_name: text_workflow
      child_initial_signals: [START]
      input_fields: [content]
      signals_to_parent: [DONE]
      context_updates_to_parent: [result]
      event_emissions:
        - signal_name: PROCESSING_COMPLETE

    DelegateToImageProcessor:
      node_type: child
      event_triggers: [HANDLE_IMAGE]
      child_workflow_name: image_workflow
      child_initial_signals: [START]
      input_fields: [content]
      signals_to_parent: [DONE]
      context_updates_to_parent: [result]
      event_emissions:
        - signal_name: PROCESSING_COMPLETE

    Finalize:
      node_type: router
      event_triggers: [PROCESSING_COMPLETE]
      event_emissions:
        - signal_name: COMPLETE

  text_workflow:
    AnalyzeText:
      node_type: llm
      event_triggers: [START]
      identity: text_analyzer
      prompt: "Analyze this text: &#123;&#123; context.content &#125;&#125;"
      output_field: result
      event_emissions:
        - signal_name: DONE

  image_workflow:
    AnalyzeImage:
      node_type: llm
      event_triggers: [START]
      identity: image_analyzer
      prompt: "Describe this image: &#123;&#123; context.content &#125;&#125;"
      output_field: result
      event_emissions:
        - signal_name: DONE

context_schema:
  content:
    type: string
    description: The input content to process
  result:
    type: object
    description: The processing result

identities:
  text_analyzer: "You are an expert text analyst. Provide detailed, structured analysis."
  image_analyzer: "You are an expert image analyst. Describe visual elements precisely."
```

In this example:
- `main_workflow` is the entry point that routes to specialized workflows
- `text_workflow` and `image_workflow` are child workflows
- Both child workflows share identities defined in the config
- Schema validation ensures consistent data structures

---

## Data vs Execution: A Critical Distinction

SOE separates two concerns:

| Concept | What It Is | Where It Lives |
|---------|------------|----------------|
| **Workflow Definition** | The YAML describing nodes and signals | `WorkflowBackend` |
| **Workflow Execution** | The running state of a specific run | `ContextBackend` |

### Workflow Definitions Are Data

Your workflow YAML is **just data**. It can be:

- Stored in files, databases, or version control
- Loaded dynamically at runtime
- Modified without restarting your application
- Versioned using any strategy you prefer

```python
# Load from file
with open("workflows/my_workflow.yaml") as f:
    workflow_yaml = f.read()

# Load from database
workflow_yaml = db.get_workflow("my_workflow", version="2.1.0")

# Pass to orchestrate
orchestrate(config=workflow_yaml, ...)
```

### Executions Are Immutable

When you start an orchestration, the workflow definition is **captured** and stored in the `WorkflowBackend` for that execution. This means:

1. **No version conflicts**: If you update your workflow, existing executions continue with their original definition
2. **Natural versioning**: Each execution remembers which workflow version it started with
3. **Audit trail**: You can inspect what any historical execution ran

```
Execution 001 → Uses workflow v1.0 (stored in workflow backend)
Execution 002 → Uses workflow v1.1 (stored in workflow backend)
Execution 003 → Uses workflow v2.0 (stored in workflow backend)

↓ You update the workflow file ↓

Execution 001 → Still uses v1.0 (continues unchanged)
Execution 004 → Uses new version
```

### Why This Matters

This architecture means:

- **No downtime migrations**: Update workflows without stopping running processes
- **Rollback safety**: Bad workflow version? New executions use the old; existing continue
- **Debugging**: Inspect exactly what workflow an execution used, even months later

---

## Parallel Workflow Execution

Child workflows can run **in parallel**. When a router emits multiple signals and each triggers a child node, all children start simultaneously (in infrastructure that supports it):

### Fan-Out Pattern with Combined Config

```yaml
workflows:
  orchestrator_workflow:
    FanOut:
      node_type: router
      event_triggers: [START]
      event_emissions:
        - signal_name: START_WORKER_A
        - signal_name: START_WORKER_B
        - signal_name: START_WORKER_C

    WorkerA:
      node_type: child
      event_triggers: [START_WORKER_A]
      child_workflow_name: worker_workflow
      child_initial_signals: [START]
      input_fields: [chunk_a]
      signals_to_parent: [WORKER_DONE]
      context_updates_to_parent: [result_a]
      event_emissions:
        - signal_name: A_COMPLETE

    WorkerB:
      node_type: child
      event_triggers: [START_WORKER_B]
      child_workflow_name: worker_workflow
      child_initial_signals: [START]
      input_fields: [chunk_b]
      signals_to_parent: [WORKER_DONE]
      context_updates_to_parent: [result_b]
      event_emissions:
        - signal_name: B_COMPLETE

    WorkerC:
      node_type: child
      event_triggers: [START_WORKER_C]
      child_workflow_name: worker_workflow
      child_initial_signals: [START]
      input_fields: [chunk_c]
      signals_to_parent: [WORKER_DONE]
      context_updates_to_parent: [result_c]
      event_emissions:
        - signal_name: C_COMPLETE

    Aggregate:
      node_type: llm
      event_triggers: [A_COMPLETE, B_COMPLETE, C_COMPLETE]
      identity: aggregator
      prompt: |
        Aggregate the results:
        - Result A: &#123;&#123; context.result_a &#125;&#125;
        - Result B: &#123;&#123; context.result_b &#125;&#125;
        - Result C: &#123;&#123; context.result_c &#125;&#125;
      output_field: final_result
      event_emissions:
        - signal_name: ALL_DONE

  worker_workflow:
    ProcessData:
      node_type: llm
      event_triggers: [START]
      identity: data_processor
      prompt: "Process this data chunk: &#123;&#123; context.data &#125;&#125;"
      output_field: result
      event_emissions:
        - signal_name: WORKER_DONE

context_schema:
  chunk_a:
    type: object
    description: Data chunk for worker A
  chunk_b:
    type: object
    description: Data chunk for worker B
  chunk_c:
    type: object
    description: Data chunk for worker C
  result_a:
    type: object
    description: Processing result from worker A
  result_b:
    type: object
    description: Processing result from worker B
  result_c:
    type: object
    description: Processing result from worker C
  final_result:
    type: object
    description: Aggregated final result

identities:
  data_processor: "You are a data processing specialist. Extract and transform data accurately."
  aggregator: "You are an expert at synthesizing multiple data sources into coherent summaries."
```

This combined config includes:
- **workflows**: Orchestrator that fans out to workers
- **context_schema**: Validates data chunks and results
- **identities**: Specialized prompts for processor and aggregator

### How Parallel Execution Works

```
START
  │
  ▼
┌─────────┐
│ FanOut  │
│(Router) │
└────┬────┘
     │
     ├──────────────┬──────────────┐
     ▼              ▼              ▼
┌─────────┐   ┌─────────┐   ┌─────────┐
│Worker A │   │Worker B │   │Worker C │
│ (Child) │   │ (Child) │   │ (Child) │
└────┬────┘   └────┬────┘   └────┬────┘
     │              │              │
     └──────────────┴──────────────┘
                    │
                    ▼
              ┌───────────┐
              │ Aggregate │
              │  (Router) │
              └───────────┘
```

Each worker:
- Runs independently (potentially on different infrastructure)
- Updates its own context (isolated)
- Propagates results back via `context_updates_to_parent`

---

## Fire-and-Forget vs Callbacks

Child workflows offer two patterns:

### Fire-and-Forget

Start a child and continue immediately—don't wait for completion:

```yaml
main_workflow:
  LaunchBackground:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: TASK_LAUNCHED
      - signal_name: START_BACKGROUND

  StartBackgroundTask:
    node_type: child
    event_triggers: [START_BACKGROUND]
    child_workflow_name: background_workflow
    child_initial_signals: [START]
    input_fields: [task_data]
    # No signals_to_parent - we don't wait for completion

  ContinueImmediately:
    node_type: router
    event_triggers: [TASK_LAUNCHED]
    event_emissions:
      - signal_name: PARENT_COMPLETE

background_workflow:
  LongRunningTask:
    node_type: tool
    event_triggers: [START]
    tool_name: long_task
    context_parameter_field: task_data
    output_field: result
    event_emissions:
      - signal_name: BACKGROUND_DONE
```

**Use cases:**
- Background processing
- Logging/analytics
- Notifications that don't affect the main flow

### Callback (Wait for Child)

Wait for specific signals from the child before continuing:

```yaml
# From child node configuration
signals_to_parent: [CHILD_DONE]  # Wait for this signal
context_updates_to_parent: [result]  # Get this data back
```

**Use cases:**
- Sequential processing
- When parent needs child's result
- Validation before proceeding

---

## External Triggers and Continuation

Workflows don't have to complete in one `orchestrate()` call. When there are no more signals to process, the execution simply **stops**. It can be resumed at any time by sending new signals:

### The Pattern

```yaml
waiting_workflow:
  Initialize:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: WAITING_FOR_APPROVAL

  # This workflow pauses here. An external system must send APPROVED or REJECTED
  # using broadcast_signals with the execution_id

  HandleApproval:
    node_type: router
    event_triggers: [APPROVED]
    event_emissions:
      - signal_name: PROCESS_APPROVED

  HandleRejection:
    node_type: router
    event_triggers: [REJECTED]
    event_emissions:
      - signal_name: PROCESS_REJECTED

  ProcessApproved:
    node_type: tool
    event_triggers: [PROCESS_APPROVED]
    tool_name: finalize_approved
    output_field: final_result
    event_emissions:
      - signal_name: COMPLETE

  NotifyRejection:
    node_type: tool
    event_triggers: [PROCESS_REJECTED]
    tool_name: notify_rejection
    output_field: rejection_notice
    event_emissions:
      - signal_name: COMPLETE
```

### How It Works

1. Workflow starts, processes available signals, then stops (no more matching triggers)
2. Returns `execution_id` to the caller
3. Later: external system (human, API, event) sends a signal using that ID
4. Workflow resumes and continues processing

```python
# Start the workflow
execution_id = orchestrate(
    config=waiting_workflow,
    initial_workflow_name="waiting_workflow",
    initial_signals=["START"],
    ...
)
# Execution stops after emitting WAITING_FOR_APPROVAL (no nodes listen for it yet)

# Later... external system sends approval
broadcast_signals(
    execution_id=execution_id,
    signals=["APPROVED"],
    backends=backends,
)
# Workflow resumes and runs to completion
```

**Key insight**: There's no "waiting state" or "paused" status. The execution is simply stopped. Anyone with the `execution_id` can send a signal to trigger it again—even the original workflow you created months ago.

### Use Cases

- Human-in-the-loop approval
- External API callbacks (webhooks)
- Long-running processes that span days/weeks
- Event-driven architectures
- Triggering old executions with new data

---

## Versioning Strategies

SOE doesn't mandate a versioning strategy—it gives you the **primitives** to implement any strategy:

### Strategy 1: Context-Based Routing

Route to different workflow versions based on context:

```yaml
entry_workflow:
  RouteByVersion:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: USE_V1
        condition: "&#123;&#123; context.api_version == 'v1' &#125;&#125;"
      - signal_name: USE_V2
        condition: "&#123;&#123; context.api_version == 'v2' &#125;&#125;"
      - signal_name: USE_LATEST
        condition: "&#123;&#123; context.api_version is not defined &#125;&#125;"

  ExecuteV1:
    node_type: child
    event_triggers: [USE_V1]
    child_workflow_name: processor_v1
    child_initial_signals: [START]
    input_fields: [request]
    signals_to_parent: [V1_DONE]
    context_updates_to_parent: [response]

  ExecuteV2:
    node_type: child
    event_triggers: [USE_V2, USE_LATEST]
    child_workflow_name: processor_v2
    child_initial_signals: [START]
    input_fields: [request]
    signals_to_parent: [V2_DONE]
    context_updates_to_parent: [response]

  HandleV1Done:
    node_type: router
    event_triggers: [V1_DONE]
    event_emissions:
      - signal_name: COMPLETE

  HandleV2Done:
    node_type: router
    event_triggers: [V2_DONE]
    event_emissions:
      - signal_name: COMPLETE

processor_v1:
  ProcessOldWay:
    node_type: llm
    event_triggers: [START]
    prompt: "Process (v1 legacy format): &#123;&#123; context.request &#125;&#125;"
    output_field: response
    event_emissions:
      - signal_name: V1_DONE

processor_v2:
  ProcessNewWay:
    node_type: llm
    event_triggers: [START]
    prompt: "Process with enhanced capabilities: &#123;&#123; context.request &#125;&#125;"
    output_field: response
    event_emissions:
      - signal_name: V2_DONE
```

### Strategy 2: Natural Versioning (No Migration)

Since execution state includes the workflow definition:

1. **New version**: Just deploy new workflow YAML
2. **Existing executions**: Continue with their captured version
3. **New executions**: Use the new version

No migration needed—versions coexist naturally.

### Strategy 3: Context Migration

For executions that need to switch to a new workflow version:

1. **Read old context**: Get the execution's current state
2. **Transform context**: Map old fields to new schema
3. **Start new execution**: With the new workflow and migrated context
4. **Mark old execution**: Complete or archive it

```python
# Migrate an execution to a new workflow version
old_context = backends.context.get_context(old_execution_id)

migrated_context = migrate_context_v1_to_v2(old_context)

new_execution_id = orchestrate(
    config=new_workflow_v2,
    initial_workflow_name="main_workflow",
    initial_signals=["RESUME"],  # Custom signal for migrations
    initial_context=migrated_context,
    backends=backends,
    broadcast_signals_caller=broadcast,
)
```

---

## Execution IDs: The Key to Everything

Every orchestration returns an `execution_id`. This ID is:

- **Unique**: Identifies this specific execution
- **Persistent**: Stored in the context backend
- **The key**: Used to send signals, read context, continue execution

### Sending Signals to Existing Executions

```python
# External system sends a signal
broadcast_signals(
    execution_id="abc-123-def",
    signals=["USER_APPROVED"],
    backends=backends,
)
```

### Reading Execution State

```python
# Inspect an execution
context = backends.context.get_context("abc-123-def")
print(context["current_step"])
print(context["__operational__"]["active_signals"])
```

### Cross-Execution Communication

One execution can trigger signals in another:

```python
# In a tool function
def notify_other_workflow(other_execution_id: str) -> dict:
    broadcast_signals(
        execution_id=other_execution_id,
        signals=["EXTERNAL_EVENT"],
        backends=global_backends,
    )
    return {"notified": True}
```

---

## Key Takeaways

1. **Workflows are data** — Store, version, and compose them freely
2. **Executions are immutable** — Each run captures its workflow definition in the workflow backend
3. **Multiple workflows compose** — Build ecosystems, not monoliths
4. **Parallel is natural** — Fan-out to children for concurrent processing
5. **Executions stop, not pause** — Send signals anytime to continue any execution
6. **Execution IDs connect everything** — The key to cross-workflow communication

This ecosystem approach means you can:
- Deploy updates without breaking running processes
- Build sophisticated multi-workflow systems
- Handle long-running, event-driven processes
- Scale from simple scripts to enterprise orchestration

## Next Steps

Now that you understand the workflows ecosystem, let's explore [Infrastructure](guide_10_infrastructure.md) for custom backends and production deployments →
