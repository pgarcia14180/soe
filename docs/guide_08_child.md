
# SOE Guide: Chapter 8 - Suborchestration

## Introduction to Child Nodes

**Child Nodes** spawn sub-workflows for modular composition. A parent workflow can delegate work to child workflows, receive signals back, and share context data.

### Why Suborchestration?

- **Modularity**: Break complex workflows into reusable components.
- **Isolation**: Child workflows have their own context namespace—no pollution of parent state.
- **Composition**: Build complex systems from simple building blocks.
- **Parallel Execution**: Multiple children can run concurrently.
- **Custom Agent Solvers**: Encapsulate agent logic as reusable sub-workflows.

### The Power of Isolation

Child workflows run in **isolated context**:

```
Parent Context: { user_id: "alice", request: "analyze data" }
    ↓ input_fields: [request]
Child Context: { request: "analyze data" }  ← Only copied fields!
    ↓ child does work, creates temp_data, intermediate_results...
Child Context: { request: "...", result: "done", temp_data: "...", ... }
    ↓ context_updates_to_parent: [result]
Parent Context: { user_id: "alice", request: "...", result: "done" }
```

The parent never sees `temp_data` or `intermediate_results`. This means:
- **No namespace collisions**: Child can use any field names.
- **Clean interfaces**: Explicit input/output contracts.
- **Testable units**: Test child workflows independently.
- **Safe experimentation**: Child failures don't corrupt parent state.

### Domain-Specific Business Logic

Each child workflow can encapsulate its **own domain** with specialized logic:

```yaml
# E-commerce orchestration - each domain is a separate workflow
order_workflow:
  ProcessPayment:
    node_type: child
    event_triggers: [ORDER_PLACED]
    child_workflow_name: payment_domain    # Payment team owns this
    input_fields: [amount, payment_method]
    signals_to_parent: [PAYMENT_COMPLETE, PAYMENT_FAILED]
    context_updates_to_parent: [transaction_id]

  ShipOrder:
    node_type: child
    event_triggers: [PAYMENT_COMPLETE]
    child_workflow_name: shipping_domain   # Logistics team owns this
    input_fields: [items, address]
    signals_to_parent: [SHIPPED]
    context_updates_to_parent: [tracking_number]

  NotifyCustomer:
    node_type: child
    event_triggers: [SHIPPED]
    child_workflow_name: notification_domain  # Comms team owns this
    input_fields: [email, tracking_number]
    signals_to_parent: [NOTIFIED]
```

**Think in Steps, Not Monoliths:**

| Domain | Owns | Knows About |
|--------|------|-------------|
| `payment_domain` | Card processing, fraud detection, retries | Nothing about shipping |
| `shipping_domain` | Carrier selection, label generation, tracking | Nothing about payments |
| `notification_domain` | Email templates, SMS, push notifications | Nothing about logistics |

Each team develops, tests, and deploys their domain workflow independently. The parent orchestrator only knows the **interface**: input fields, output signals, context updates.

This enables:
- **Separation of concerns**: Payment logic doesn't leak into shipping.
- **Team autonomy**: Each team owns their workflow.
- **Independent evolution**: Update payment flow without touching shipping.
- **Domain expertise**: Specialists focus on their area.

## Your First Child Node

Spawn a simple child workflow:

### The Workflow

```yaml
parent_workflow:
  SpawnChild:
    node_type: child
    event_triggers: [START]
    child_workflow_name: child_workflow
    child_initial_signals: [START]
    signals_to_parent: [CHILD_DONE]

  ChildDoneHandler:
    node_type: router
    event_triggers: [CHILD_DONE]
    event_emissions:
      - signal_name: WORKFLOW_COMPLETE

child_workflow:
  DoWork:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: WORK_COMPLETE

  Finish:
    node_type: router
    event_triggers: [WORK_COMPLETE]
    event_emissions:
      - signal_name: CHILD_DONE
```

### Configuration

| Field | Required | Description |
|-------|----------|-------------|
| `child_workflow_name` | ✓ | Name of workflow to spawn |
| `child_initial_signals` | ✓ | Signals to start child with |
| `signals_to_parent` | Optional | Child signals that propagate to parent |
| `input_fields` | Optional | Context fields to copy to child |
| `context_updates_to_parent` | Optional | Child context fields to copy back |

### How It Works

1.  `SpawnChild` triggered by `START`.
2.  Spawns `child_workflow` with `[START]` signal.
3.  Child runs independently, emits `CHILD_DONE`.
4.  `CHILD_DONE` propagates to parent via `signals_to_parent`.
5.  `ChildDoneHandler` receives signal, emits `WORKFLOW_COMPLETE`.

## Passing Data to Child

Use `input_fields` to copy context to child:

### The Workflow

```yaml
parent_workflow:
  SpawnProcessor:
    node_type: child
    event_triggers: [START]
    child_workflow_name: processor_workflow
    child_initial_signals: [START]
    input_fields: [data_to_process]
    signals_to_parent: [PROCESSED]

  ProcessedHandler:
    node_type: router
    event_triggers: [PROCESSED]
    event_emissions:
      - signal_name: PARENT_COMPLETE

processor_workflow:
  ProcessData:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: PROCESSED
        condition: "&#123;&#123; context.data_to_process is defined &#125;&#125;"
```

### Data Flow

1.  Parent has `data_to_process: "important_data"` in context.
2.  Child node specifies `input_fields: [data_to_process]`.
3.  Child workflow receives copy of `data_to_process` in its context.
4.  Child can use `{{ context.data_to_process }}` in conditions/prompts.

## Receiving Data from Child

Use `context_updates_to_parent` to propagate child data back:

### The Workflow

```yaml
parent_workflow:
  SpawnCalculator:
    node_type: child
    event_triggers: [START]
    child_workflow_name: calculator_workflow
    child_initial_signals: [START]
    input_fields: [calc_params]
    signals_to_parent: [CALCULATION_DONE]
    context_updates_to_parent: [result]

  ResultHandler:
    node_type: router
    event_triggers: [CALCULATION_DONE]
    event_emissions:
      - signal_name: PARENT_COMPLETE

calculator_workflow:
  Calculate:
    node_type: tool
    event_triggers: [START]
    tool_name: sum_numbers
    context_parameter_field: calc_params
    output_field: result
    event_emissions:
      - signal_name: CALCULATION_DONE
```

### Data Flow

1.  Parent passes `numbers: [1, 2, 3, 4, 5]` to child.
2.  Child runs `sum_numbers` tool, stores result in `result`.
3.  `context_updates_to_parent: [result]` copies `result` back.
4.  Parent context now has `result: 15`.

## Child Continues After Callback

`signals_to_parent` is NOT a "done" signal—child can keep working!

### The Workflow

```yaml
parent_workflow:
  SpawnWorker:
    node_type: child
    event_triggers: [START]
    child_workflow_name: worker_workflow
    child_initial_signals: [START]
    signals_to_parent: [PROGRESS, COMPLETED]

  ProgressHandler:
    node_type: router
    event_triggers: [PROGRESS]
    event_emissions:
      - signal_name: PROGRESS_LOGGED

  CompleteHandler:
    node_type: router
    event_triggers: [COMPLETED]
    event_emissions:
      - signal_name: ALL_DONE

worker_workflow:
  Phase1:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: PHASE1_DONE

  ReportProgress:
    node_type: router
    event_triggers: [PHASE1_DONE]
    event_emissions:
      - signal_name: PROGRESS

  Phase2:
    node_type: router
    event_triggers: [PROGRESS]
    event_emissions:
      - signal_name: PHASE2_DONE

  ReportComplete:
    node_type: router
    event_triggers: [PHASE2_DONE]
    event_emissions:
      - signal_name: COMPLETED
```

### Execution Flow

1.  Child starts, does Phase1.
2.  Emits `PROGRESS` → propagates to parent → `PROGRESS_LOGGED`.
3.  Child **continues** to Phase2 (not terminated).
4.  Emits `COMPLETED` → propagates to parent → `ALL_DONE`.

This enables:
- Progress reporting
- Streaming updates
- Multi-phase child workflows

## Multiple Children (Parallel)

Multiple child nodes can spawn from the same trigger:

### The Workflow

```yaml
parent_workflow:
  SpawnWorkerA:
    node_type: child
    event_triggers: [START]
    child_workflow_name: worker_a
    child_initial_signals: [START]
    signals_to_parent: [A_DONE]

  SpawnWorkerB:
    node_type: child
    event_triggers: [START]
    child_workflow_name: worker_b
    child_initial_signals: [START]
    signals_to_parent: [B_DONE]

  WaitForBoth:
    node_type: router
    event_triggers: [A_DONE, B_DONE]
    event_emissions:
      - signal_name: ALL_WORKERS_DONE

worker_a:
  DoWorkA:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: A_DONE

worker_b:
  DoWorkB:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: B_DONE
```

### Execution

1.  `START` triggers both `SpawnWorkerA` and `SpawnWorkerB`.
2.  Both child workflows run concurrently.
3.  `WaitForBoth` listens for `A_DONE` and `B_DONE`.
4.  When both arrive, emits `ALL_WORKERS_DONE`.

Use this for:
- Fan-out/fan-in patterns
- Parallel processing
- Concurrent sub-tasks

## Nested Children (Grandchild)

Children can spawn their own children:

### The Workflow

```yaml
main_workflow:
  SpawnChild:
    node_type: child
    event_triggers: [START]
    child_workflow_name: child_workflow
    child_initial_signals: [START]
    signals_to_parent: [CHILD_COMPLETE]

  MainDone:
    node_type: router
    event_triggers: [CHILD_COMPLETE]
    event_emissions:
      - signal_name: MAIN_COMPLETE

child_workflow:
  SpawnGrandchild:
    node_type: child
    event_triggers: [START]
    child_workflow_name: grandchild_workflow
    child_initial_signals: [START]
    signals_to_parent: [GRANDCHILD_DONE]

  ChildDone:
    node_type: router
    event_triggers: [GRANDCHILD_DONE]
    event_emissions:
      - signal_name: CHILD_COMPLETE

grandchild_workflow:
  DoDeepWork:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: GRANDCHILD_DONE
```

### Signal Flow

```
main_workflow
    ↓ spawns
child_workflow
    ↓ spawns
grandchild_workflow
    ↓ emits GRANDCHILD_DONE
child_workflow (receives, emits CHILD_COMPLETE)
    ↓
main_workflow (receives CHILD_COMPLETE, emits MAIN_COMPLETE)
```

## Child with LLM

Child workflows can contain any node type:

### The Workflow

```yaml
parent_workflow:
  SpawnAnalyzer:
    node_type: child
    event_triggers: [START]
    child_workflow_name: analyzer_workflow
    child_initial_signals: [START]
    input_fields: [textToAnalyze]
    signals_to_parent: [ANALYSIS_COMPLETE]
    context_updates_to_parent: [analysisResult]

  AnalysisDone:
    node_type: router
    event_triggers: [ANALYSIS_COMPLETE]
    event_emissions:
      - signal_name: PARENT_DONE

analyzer_workflow:
  AnalyzeText:
    node_type: llm
    event_triggers: [START]
    prompt: "Analyze this text: &#123;&#123; context.textToAnalyze &#125;&#125;"
    output_field: analysisResult
    event_emissions:
      - signal_name: ANALYSIS_COMPLETE
```

### Use Cases

- **AI Analysis Modules**: Reusable analysis sub-workflows.
- **Agent Delegation**: Parent routes to specialized agent children.
- **Tool Orchestration**: Child manages complex tool sequences.

## Suborchestration Patterns

### Pattern: Custom Agent Solvers

The most powerful use of child nodes is **encapsulating agents as reusable solvers**. Instead of embedding agent logic in your main workflow, create specialized agent workflows:

```yaml
main_workflow:
  AnalyzeRequest:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: NEEDS_RESEARCH
        condition: "{{ 'research' in context.task|lower }}"
      - signal_name: NEEDS_CODING
        condition: "{{ 'code' in context.task|lower }}"

  ResearchSolver:
    node_type: child
    event_triggers: [NEEDS_RESEARCH]
    child_workflow_name: research_agent_workflow
    child_initial_signals: [START]
    input_fields: [task, sources]
    signals_to_parent: [RESEARCH_COMPLETE]
    context_updates_to_parent: [findings]

  CodingSolver:
    node_type: child
    event_triggers: [NEEDS_CODING]
    child_workflow_name: coding_agent_workflow
    child_initial_signals: [START]
    input_fields: [task, language]
    signals_to_parent: [CODE_COMPLETE]
    context_updates_to_parent: [code_output]

# Reusable research agent - can be used by any parent workflow
research_agent_workflow:
  ResearchAgent:
    node_type: agent
    event_triggers: [START]
    system_prompt: "You are a research specialist. Use available tools to gather information."
    user_prompt: "Research task: {{ context.task }}. Sources: {{ context.sources }}"
    output_field: findings
    available_tools: [web_search, summarize]
    event_emissions:
      - signal_name: RESEARCH_COMPLETE

# Reusable coding agent - encapsulates coding expertise
coding_agent_workflow:
  CodingAgent:
    node_type: agent
    event_triggers: [START]
    system_prompt: "You are an expert {{ context.language }} developer."
    user_prompt: "Task: {{ context.task }}"
    output_field: code_output
    available_tools: [write_file, run_tests, lint_code]
    event_emissions:
      - signal_name: CODE_COMPLETE
```

**Benefits of Agent Solvers:**

- **Reusability**: Same agent workflow used by multiple parents.
- **Specialization**: Each agent has focused tools and prompts.
- **Testability**: Test agent workflows in isolation with mock tools.
- **Swappability**: Replace `coding_agent_workflow` without changing parent.
- **Identity per solver**: Each agent can have its own conversation history.

### Pattern: Specialized Agents

```yaml
parent_workflow:
  Router:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: CODING_TASK
        condition: "{{ 'code' in context.request|lower }}"
      - signal_name: WRITING_TASK

  CodingAgent:
    node_type: child
    event_triggers: [CODING_TASK]
    child_workflow_name: coding_workflow
    child_initial_signals: [START]
    input_fields: [request]
    signals_to_parent: [AGENT_DONE]
    context_updates_to_parent: [response]

  WritingAgent:
    node_type: child
    event_triggers: [WRITING_TASK]
    child_workflow_name: writing_workflow
    child_initial_signals: [START]
    input_fields: [request]
    signals_to_parent: [AGENT_DONE]
    context_updates_to_parent: [response]
```

### Pattern: Pipeline with Stages

```yaml
pipeline_workflow:
  Stage1:
    node_type: child
    event_triggers: [START]
    child_workflow_name: extraction_workflow
    child_initial_signals: [START]
    input_fields: [raw_data]
    signals_to_parent: [EXTRACTED]
    context_updates_to_parent: [extracted_data]

  Stage2:
    node_type: child
    event_triggers: [EXTRACTED]
    child_workflow_name: transformation_workflow
    child_initial_signals: [START]
    input_fields: [extracted_data]
    signals_to_parent: [TRANSFORMED]
    context_updates_to_parent: [final_data]
```

## Shared Conversation History Across Sub-Orchestration

When you spawn child workflows, conversation history is **automatically shared** with the parent. This enables powerful patterns where child workflows continue conversations started by parents.

### How It Works

SOE maintains a `main_execution_id` in the operational context:
- For the root orchestration, `main_execution_id` equals the execution ID
- For child workflows, `main_execution_id` is inherited from the parent
- Conversation history is keyed by `main_execution_id`, not the child's execution ID

This means all nodes in the orchestration tree share the same conversation history—if they use `identity`.

### Parent-Child Conversation Example

```yaml
# ERROR: File not found: tests/test_cases/workflows/guide_07_child.py
```

### Execution Flow

1. `ParentLLMCall` executes with `identity: shared_session`
2. Conversation is stored using `main_execution_id`
3. Child workflow spawns, inheriting `main_execution_id`
4. `ChildLLMCall` has same `identity: shared_session`
5. Child sees parent's conversation in `conversation_history`
6. Both exchanges are stored under the same `main_execution_id`

### Nested Sub-Orchestration

The pattern extends to any depth:

```yaml
# ERROR: File not found: tests/test_cases/workflows/guide_07_child.py
```

Main → Child → Grandchild: The grandchild sees the full conversation from main.

### Use Cases

- **Progressive problem-solving**: Parent breaks down task, children solve parts while seeing full context
- **Iterative refinement**: Each sub-workflow builds on previous responses
- **Distributed agents**: Specialized child agents share knowledge with parent
- **Long-running workflows**: History persists across the entire orchestration tree

## Key Points

- **Isolated context**: Children have their own namespace—no state pollution.
- **Modular composition**: Break workflows into reusable sub-workflows.
- **Custom agent solvers**: Encapsulate agents as reusable child workflows.
- **Bidirectional data**: `input_fields` (parent→child), `context_updates_to_parent` (child→parent).
- **Signal propagation**: `signals_to_parent` specifies which child signals reach parent.
- **Child continues**: Signals to parent don't terminate child—it can keep working.
- **Nesting**: Children can spawn grandchildren indefinitely.
- **Shared conversation history**: Children share conversation history with parent via `main_execution_id`.
- **Recursive calls**: A child workflow can technically call itself! This enables recursive patterns, though use with caution and always have termination conditions.

## Next Steps

Now that you understand child workflows and composition, let's explore [The Workflows Ecosystem](guide_09_ecosystem.md) for multi-workflow registries and versioning →
