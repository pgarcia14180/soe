
# Appendix A: Operational Features

## Introduction

SOE provides **operational context** and **infrastructure configurations** that give you fine-grained control over workflow execution. These features enable advanced patterns like:

- Waiting for multiple signals (AND logic)
- Limiting LLM calls
- Circuit breaker patterns
- Loop prevention
- Retry configurations

## The Operational Context

Every workflow execution has a reserved `__operational__` namespace in context. This is **read-only** for your workflows but provides valuable runtime information.

### Structure

```python
context["__operational__"] = {
    "signals": ["START", "TASK_A_DONE", ...],  # All signals emitted
    "nodes": {"NodeName": 3, ...},              # Execution count per node
    "llm_calls": 5,                             # Total LLM calls
    "tool_calls": 2,                            # Total tool calls
    "errors": 0,                                # Total errors
    "main_execution_id": "abc-123-...",         # Root orchestration ID
}
```

### Main Execution ID

The `main_execution_id` is the root orchestration ID that persists across sub-orchestrations:

- For root workflows: `main_execution_id` equals the execution ID
- For child workflows: `main_execution_id` is inherited from the parent
- Used by conversation history to share state across the orchestration tree

This enables **persistent identity** where children share conversation history with their parent (see [Identity Guide](guide_07_identity.md)).

### Accessing in Jinja

Use `context.__operational__` in any condition:


```yaml
condition: "{{ 'TASK_A_DONE' in context.__operational__.signals }}"
condition: "{{ context.__operational__.llm_calls < 10 }}"
condition: "{{ context.__operational__.tool_calls < 50 }}"
condition: "{{ context.__operational__.errors >= 3 }}"
condition: "{{ context.__operational__.nodes.get('MyNode', 0) < 5 }}"
```


---

## broadcast_signals: Post-Execution Control

After `orchestrate()` returns, you can send additional signals to continue or manipulate the execution using `broadcast_signals`.

### Understanding the Relationship

When you call `orchestrate()`, it:
1. Generates a new `execution_id`
2. Initializes clean operational context (`__operational__`)
3. Runs the workflow until no more signals trigger nodes
4. Returns the `execution_id`

The `broadcast_signals` function lets you send signals to that execution **after** `orchestrate()` returns.

### Important: Avoid START with broadcast_signals

```python
# ❌ WRONG - Don't use START with broadcast_signals
execution_id = orchestrate(
    config=workflow,
    initial_signals=["START"],
    ...
)
broadcast_signals(execution_id, ["START"], nodes, backends)  # BAD!
```

**Why this is wrong**: Sending `START` via `broadcast_signals` will double-process nodes and corrupt the operational context. The operational counters were already incremented during the initial `orchestrate()`.

### Proper Usage of broadcast_signals

```python
# ✅ CORRECT - Use for continuation or specific signals
execution_id = orchestrate(
    config=workflow,
    initial_signals=["START"],
    ...
)

# Later, send a specific signal to continue
broadcast_signals(execution_id, ["EXTERNAL_EVENT"], nodes, backends)
broadcast_signals(execution_id, ["RETRY_PHASE_2"], nodes, backends)
```

### Use Cases for broadcast_signals

1. **Delayed Scheduling**: SOE is infrastructure-agnostic and doesn't include a scheduler. You can use any external scheduler by starting with no signals:
   ```python
   # Create the execution but don't start
   execution_id = orchestrate(
       config=workflow,
       initial_signals=[],  # No signals yet!
       ...
   )

   # Later, via external scheduler (cron, AWS EventBridge, etc.)
   broadcast_signals(execution_id, ["START"], nodes, backends)
   ```

2. **External Event Handling**: Continue a workflow based on external events:
   ```python
   # Workflow waiting for approval
   broadcast_signals(execution_id, ["APPROVED"], nodes, backends)
   ```

3. **Retries and Remediation**: Trigger specific retry paths:
   ```python
   broadcast_signals(execution_id, ["RETRY_FAILED_STEP"], nodes, backends)
   ```

### For Clean Restarts, Use Inheritance

If you need to restart a workflow completely (fresh operational context), use [Config Inheritance](guide_inheritance.md) instead:

```python
# Fresh execution inheriting config from previous run
new_execution_id = orchestrate(
    config=None,
    initial_signals=["START"],
    initial_context={},
    inherit_config_from_id=old_execution_id,  # Reuse config
    ...
)
```

This creates a new `execution_id` with clean operational counters while reusing the workflow definitions.

---

## Wait for Multiple Signals (AND Logic)

By default, `event_triggers` uses OR logic—any listed signal triggers the node. To implement AND logic (wait for all signals), use a router with operational context:

### The Pattern

```yaml
example_workflow:
  TaskA:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: A_DONE

  TaskB:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: B_DONE

  WaitForBoth:
    node_type: router
    event_triggers: [A_DONE, B_DONE]
    event_emissions:
      - signal_name: BOTH_COMPLETE
        condition: "&#123;&#123; 'A_DONE' in context.__operational__.signals and 'B_DONE' in context.__operational__.signals &#125;&#125;"
      - signal_name: WAITING
        condition: "&#123;&#123; not ('A_DONE' in context.__operational__.signals and 'B_DONE' in context.__operational__.signals) &#125;&#125;"
```

### How It Works

1.  `TaskA` and `TaskB` both trigger on `START` (parallel execution).
2.  `WaitForBoth` triggers on either `A_DONE` OR `B_DONE`.
3.  Condition checks if BOTH signals are in `__operational__.signals`.
4.  First trigger: condition fails → emits `WAITING`.
5.  Second trigger: condition succeeds → emits `BOTH_COMPLETE`.

## LLM Call Limiting

Control AI costs by checking `llm_calls`:

### The Pattern

```yaml
example_workflow:
  FirstLLM:
    node_type: llm
    event_triggers: [START]
    prompt: "First task: &#123;&#123; context.task &#125;&#125;"
    output_field: firstResult
    event_emissions:
      - signal_name: FIRST_DONE

  CheckLLMCount:
    node_type: router
    event_triggers: [FIRST_DONE]
    event_emissions:
      - signal_name: CONTINUE_LLM
        condition: "&#123;&#123; context.__operational__.llm_calls < 3 &#125;&#125;"
      - signal_name: LLM_LIMIT_REACHED
        condition: "&#123;&#123; context.__operational__.llm_calls >= 3 &#125;&#125;"

  SecondLLM:
    node_type: llm
    event_triggers: [CONTINUE_LLM]
    prompt: "Second task based on: &#123;&#123; context.firstResult &#125;&#125;"
    output_field: secondResult
    event_emissions:
      - signal_name: SECOND_DONE
```

### Use Cases

- **Budget control**: Stop after N LLM calls.
- **Rate limiting**: Prevent runaway agent loops.
- **Tiered processing**: Different paths based on usage.

## Tool Call Limiting

Monitor and limit tool usage by checking `tool_calls`:

### The Pattern

```yaml
example_workflow:
  FirstTool:
    node_type: tool
    event_triggers: [START]
    tool_name: api_call
    context_parameter_field: api_params
    output_field: firstResult
    event_emissions:
      - signal_name: FIRST_DONE

  CheckToolCount:
    node_type: router
    event_triggers: [FIRST_DONE]
    event_emissions:
      - signal_name: CONTINUE_TOOLS
        condition: "&#123;&#123; context.__operational__.tool_calls < 10 &#125;&#125;"
      - signal_name: TOOL_LIMIT_REACHED
        condition: "&#123;&#123; context.__operational__.tool_calls >= 10 &#125;&#125;"

  SecondTool:
    node_type: tool
    event_triggers: [CONTINUE_TOOLS]
    tool_name: api_call
    context_parameter_field: api_params
    output_field: secondResult
    event_emissions:
      - signal_name: SECOND_DONE
```

### Use Cases

- **Rate limiting**: Prevent excessive API calls to external services.
- **Resource protection**: Limit database or file system operations.
- **Cost control**: Track tool usage for billing or quota management.

**Note**: `tool_calls` counts both standalone tool node executions and tool calls made by agent nodes.

## Error Circuit Breaker

Implement circuit breaker pattern using `errors` count:

### The Pattern

```yaml
example_workflow:
  ProcessData:
    node_type: tool
    event_triggers: [START]
    tool_name: risky_operation
    context_parameter_field: data
    output_field: result
    event_emissions:
      - signal_name: SUCCESS

  CheckErrors:
    node_type: router
    event_triggers: [FAILURE]
    event_emissions:
      - signal_name: RETRY
        condition: "&#123;&#123; context.__operational__.errors < 3 &#125;&#125;"
      - signal_name: CIRCUIT_OPEN
        condition: "&#123;&#123; context.__operational__.errors >= 3 &#125;&#125;"

  RetryHandler:
    node_type: router
    event_triggers: [RETRY]
    event_emissions:
      - signal_name: START
```

### How It Works

1.  `ProcessData` runs a risky tool.
2.  On failure, `CheckErrors` evaluates error count.
3.  Under threshold: emit `RETRY` → triggers `START` again.
4.  Over threshold: emit `CIRCUIT_OPEN` → stop retrying.

## Loop Prevention

Prevent infinite loops by checking node execution count:

### The Pattern

```yaml
example_workflow:
  LoopingNode:
    node_type: router
    event_triggers: [START, CONTINUE]
    event_emissions:
      - signal_name: CONTINUE
        condition: "&#123;&#123; context.__operational__.nodes.get('LoopingNode', 0) < 5 &#125;&#125;"
      - signal_name: LOOP_LIMIT_REACHED
        condition: "&#123;&#123; context.__operational__.nodes.get('LoopingNode', 0) >= 5 &#125;&#125;"
```

### How It Works

1.  `LoopingNode` triggers on `START` or `CONTINUE`.
2.  Each execution increments `nodes.LoopingNode`.
3.  Condition checks if count exceeds limit.
4.  Under limit: emit `CONTINUE` (loop).
5.  Over limit: emit `LOOP_LIMIT_REACHED` (break).

## Retry Configuration

### LLM Retries

LLM nodes support `retries` for handling validation failures:

```yaml
example_workflow:
  ReliableLLM:
    node_type: llm
    event_triggers: [START]
    prompt: "Analyze: &#123;&#123; context.input &#125;&#125;"
    output_field: result
    retries: 5
    event_emissions:
      - signal_name: DONE
```

When the LLM returns invalid JSON or fails Pydantic validation, SOE automatically retries up to `retries` times (default: 3).

### LLM Failure Signal

When all retries are exhausted, the node raises an exception by default. Use `llm_failure_signal` to emit a signal instead, enabling graceful fallback:

```yaml
example_workflow:
  LLMWithFallback:
    node_type: llm
    event_triggers: [START]
    prompt: "Analyze: &#123;&#123; context.input &#125;&#125;"
    output_field: result
    retries: 3
    llm_failure_signal: LLM_FAILED
    event_emissions:
      - signal_name: DONE

  HandleLLMFailure:
    node_type: router
    event_triggers: [LLM_FAILED]
    event_emissions:
      - signal_name: USE_FALLBACK
```

This pattern enables:
- **Fallback paths**: Route to cached responses or simpler logic
- **Graceful degradation**: Continue workflow instead of crashing
- **Alerting**: Trigger notification workflows on failure

### Agent Retries

Agent nodes also support `retries`:

```yaml
example_workflow:
  ReliableAgent:
    node_type: agent
    event_triggers: [START]
    system_prompt: "You are a helpful assistant."
    user_prompt: "Help with: &#123;&#123; context.request &#125;&#125;"
    output_field: response
    available_tools: [search]
    retries: 2
    event_emissions:
      - signal_name: AGENT_DONE
```

This controls how many times the agent's internal LLM calls retry on validation failure.

### Agent Failure Signals

Agents emit `llm_failure_signal` when they exhaust all retries (terminal failure):

```yaml
example_workflow:
  RobustAgent:
    node_type: agent
    event_triggers: [START]
    prompt: "Complete the task: &#123;&#123; context.task &#125;&#125;"
    tools: [risky_operation]
    output_field: result
    retries: 3
    llm_failure_signal: AGENT_EXHAUSTED
    event_emissions:
      - signal_name: DONE

  HandleAgentExhausted:
    node_type: router
    event_triggers: [AGENT_EXHAUSTED]
    event_emissions:
      - signal_name: FALLBACK_REQUIRED
```

**Note**: Tool failures are handled via the tool registry's `failure_signal` configuration (see Tool Retries below).

### Tool Retries

For agent tools, retries are configured per-tool in the tools registry:

```python
tools = [
    {"function": risky_tool, "max_retries": 3},
    {"function": reliable_tool, "max_retries": 0},
]
```

When a tool execution fails, the agent can retry up to `max_retries` times before reporting failure to the LLM.

## Conditional Processing Based on State

Combine operational checks for smart routing:

```yaml
example_workflow:
  CheckState:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: NEEDS_LLM
        condition: "&#123;&#123; context.__operational__.llm_calls == 0 &#125;&#125;"
      - signal_name: USE_CACHED
        condition: "&#123;&#123; context.__operational__.llm_calls > 0 &#125;&#125;"

  CallLLM:
    node_type: llm
    event_triggers: [NEEDS_LLM]
    prompt: "Process: &#123;&#123; context.input &#125;&#125;"
    output_field: result
    event_emissions:
      - signal_name: COMPLETE

  UseCached:
    node_type: router
    event_triggers: [USE_CACHED]
    event_emissions:
      - signal_name: COMPLETE
```

## Operational Context Fields Reference

| Field | Type | Description |
|-------|------|-------------|
| `signals` | `List[str]` | All signals emitted during execution |
| `nodes` | `Dict[str, int]` | Execution count per node name |
| `llm_calls` | `int` | Total LLM calls (LLM + Agent nodes) |
| `tool_calls` | `int` | Total tool calls (Tool nodes + Agent tool calls) |
| `errors` | `int` | Total errors encountered |
| `main_execution_id` | `str` | Root orchestration ID (persists to children) |

## The Parent Context (`__parent__`)

Child workflows have a `__parent__` namespace in their context containing parent relationship metadata:

```python
context["__parent__"] = {
    "parent_execution_id": "parent-abc-123",  # Immediate parent's execution ID
    "main_execution_id": "root-abc-123",      # Root orchestration ID
    "signals_to_parent": ["DONE", "FAILED"],  # Signals that propagate up
    "context_updates_to_parent": ["result"],  # Keys that sync to parent
}
```

This is **read-only** and managed by SOE. It enables:
- Context updates propagating up the orchestration tree
- Signal forwarding from child to parent
- Shared conversation history across the entire tree

## Infrastructure Guardrail Patterns

These patterns use routers as guardrails to control execution flow. They check operational context or external conditions **before** allowing expensive operations to proceed.

### Execute Only Once

Prevent duplicate execution of expensive operations:

```yaml
example_workflow:
  OnceGuard:
    node_type: router
    event_triggers: [START, RETRY_REQUEST]
    event_emissions:
      - signal_name: PROCEED
        condition: "&#123;&#123; context.__operational__.nodes.get('ExpensiveOperation', 0) == 0 &#125;&#125;"
      - signal_name: ALREADY_EXECUTED
        condition: "&#123;&#123; context.__operational__.nodes.get('ExpensiveOperation', 0) > 0 &#125;&#125;"

  ExpensiveOperation:
    node_type: tool
    event_triggers: [PROCEED]
    tool_name: expensive_api_call
    context_parameter_field: api_params
    output_field: api_result
    event_emissions:
      - signal_name: OPERATION_COMPLETE

  SkipHandler:
    node_type: router
    event_triggers: [ALREADY_EXECUTED]
    event_emissions:
      - signal_name: OPERATION_COMPLETE
```

**How It Works:**
1. `OnceGuard` checks if `ExpensiveOperation` has already executed.
2. First execution: `nodes.get('ExpensiveOperation', 0) == 0` → `PROCEED`.
3. Subsequent triggers: `ALREADY_EXECUTED` → skip to handler.

**Use Cases:**
- Billing operations that must happen exactly once.
- Initialization tasks.
- Idempotent API calls.

### Health Check Guardrail

Validate external service health before proceeding:

```yaml
example_workflow:
  HealthCheckRouter:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: CHECK_SERVICE

  ServiceHealthCheck:
    node_type: tool
    event_triggers: [CHECK_SERVICE]
    tool_name: check_service_health
    output_field: health_status
    event_emissions:
      - signal_name: HEALTH_CHECKED

  HealthGuard:
    node_type: router
    event_triggers: [HEALTH_CHECKED]
    event_emissions:
      - signal_name: SERVICE_HEALTHY
        condition: "&#123;&#123; context.health_status.is_healthy == true &#125;&#125;"
      - signal_name: SERVICE_UNHEALTHY
        condition: "&#123;&#123; context.health_status.is_healthy != true &#125;&#125;"

  MainProcess:
    node_type: llm
    event_triggers: [SERVICE_HEALTHY]
    prompt: "Process with healthy service: &#123;&#123; context.request &#125;&#125;"
    output_field: result
    event_emissions:
      - signal_name: DONE

  UnhealthyFallback:
    node_type: router
    event_triggers: [SERVICE_UNHEALTHY]
    event_emissions:
      - signal_name: DONE
```

**How It Works:**
1. Router triggers health check tool.
2. Tool returns `health_status` with `is_healthy` field.
3. Second router decides: healthy → proceed, unhealthy → fallback.

**Use Cases:**
- Check database connectivity before writes.
- Validate API availability before calls.
- Verify model endpoints before inference.

### Rate Limiting

Throttle operations based on execution count:

```yaml
example_workflow:
  RateLimitGuard:
    node_type: router
    event_triggers: [REQUEST]
    event_emissions:
      - signal_name: ALLOWED
        condition: "&#123;&#123; context.__operational__.nodes.get('APICall', 0) < context.rate_limit &#125;&#125;"
      - signal_name: RATE_LIMITED
        condition: "&#123;&#123; context.__operational__.nodes.get('APICall', 0) >= context.rate_limit &#125;&#125;"

  APICall:
    node_type: tool
    event_triggers: [ALLOWED]
    tool_name: external_api
    context_parameter_field: api_params
    output_field: api_response
    event_emissions:
      - signal_name: CALL_COMPLETE

  RateLimitHandler:
    node_type: router
    event_triggers: [RATE_LIMITED]
    event_emissions:
      - signal_name: THROTTLED
```

**How It Works:**
1. Guard router checks if `APICall` count is under `rate_limit`.
2. Under limit: `ALLOWED` → execute.
3. Over limit: `RATE_LIMITED` → throttle handler.

**Use Cases:**
- API rate limiting per execution.
- Cost control for LLM calls.
- Preventing runaway loops.

### Kill Switch

Context-based execution suspension:

```yaml
example_workflow:
  KillSwitchGuard:
    node_type: router
    event_triggers: [START, CONTINUE]
    event_emissions:
      - signal_name: PROCEED
        condition: "&#123;&#123; context.kill_switch != true &#125;&#125;"
      - signal_name: SUSPENDED
        condition: "&#123;&#123; context.kill_switch == true &#125;&#125;"

  MainProcess:
    node_type: llm
    event_triggers: [PROCEED]
    prompt: "Execute step: &#123;&#123; context.current_step &#125;&#125;"
    output_field: step_result
    event_emissions:
      - signal_name: STEP_DONE

  NextStep:
    node_type: router
    event_triggers: [STEP_DONE]
    event_emissions:
      - signal_name: CONTINUE
        condition: "&#123;&#123; context.steps_remaining > 0 &#125;&#125;"
      - signal_name: ALL_COMPLETE
        condition: "&#123;&#123; context.steps_remaining <= 0 &#125;&#125;"

  SuspendHandler:
    node_type: router
    event_triggers: [SUSPENDED]
    event_emissions:
      - signal_name: AWAITING_RESUME
```

**How It Works:**
1. Guard router checks `context.kill_switch` before each step.
2. If `true`: emit `SUSPENDED`, execution stops.
3. External system can set `kill_switch` in context and send signal to resume.
4. When resumed without kill switch: execution continues.

**Use Cases:**
- Emergency stop for runaway agents.
- Pause/resume long-running workflows.
- Admin override for production systems.

### Production Guardrails (Combined Pattern)

Combine multiple guardrails for production-ready workflows:

```yaml
example_workflow:
  EntryGuard:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: CHECK_KILL_SWITCH

  KillSwitchCheck:
    node_type: router
    event_triggers: [CHECK_KILL_SWITCH]
    event_emissions:
      - signal_name: CHECK_RATE
        condition: "&#123;&#123; context.system_suspended != true &#125;&#125;"
      - signal_name: SYSTEM_SUSPENDED
        condition: "&#123;&#123; context.system_suspended == true &#125;&#125;"

  RateLimitCheck:
    node_type: router
    event_triggers: [CHECK_RATE]
    event_emissions:
      - signal_name: CHECK_HEALTH
        condition: "&#123;&#123; context.__operational__.nodes.get('CoreOperation', 0) < 100 &#125;&#125;"
      - signal_name: RATE_EXCEEDED
        condition: "&#123;&#123; context.__operational__.nodes.get('CoreOperation', 0) >= 100 &#125;&#125;"

  HealthCheck:
    node_type: tool
    event_triggers: [CHECK_HEALTH]
    tool_name: system_health_check
    output_field: system_health
    event_emissions:
      - signal_name: HEALTH_RESULT

  HealthDecision:
    node_type: router
    event_triggers: [HEALTH_RESULT]
    event_emissions:
      - signal_name: EXECUTE
        condition: "&#123;&#123; context.system_health.ready == true &#125;&#125;"
      - signal_name: SYSTEM_DEGRADED
        condition: "&#123;&#123; context.system_health.ready != true &#125;&#125;"

  CoreOperation:
    node_type: llm
    event_triggers: [EXECUTE]
    prompt: "Process: &#123;&#123; context.request &#125;&#125;"
    output_field: result
    event_emissions:
      - signal_name: DONE
```

**The Guardrail Chain:**
1. **Kill Switch Check** - Is the system suspended?
2. **Rate Limit Check** - Are we under the limit?
3. **Health Check** - Is the downstream service healthy?
4. **Execute** - Only if all checks pass.

## Infrastructure Configurations Reference

| Config | Node Types | Default | Description |
|--------|------------|---------|-------------|
| `retries` | LLM, Agent | 3 | Max validation retries for LLM response |
| `llm_failure_signal` | LLM, Agent | None | Signal to emit when all retries exhausted (instead of raising) |
| `max_retries` | Tool (in registry) | 1 | Max execution retries per tool |
| `failure_signal` | Tool (in registry) | None | Signal to emit when tool fails after all retries |

## Best Practices

### Do

- **Use operational context for control flow**: Circuit breakers, loop limits.
- **Check signals for AND logic**: `{{ 'A' in context.__operational__.signals and 'B' in context.__operational__.signals }}`.
- **Set retries appropriately**: Higher for unreliable LLMs, lower for deterministic.

### Don't

- **Write to `__operational__`**: It's managed by SOE.
- **Rely on exact node execution counts**: Implementation may vary.
- **Use operational context for business logic**: Keep it for infrastructure decisions.

## Key Points

- **`__operational__`** is a read-only namespace with runtime metadata.
- **AND logic** for signals requires a router checking `__operational__.signals`.
- **`llm_calls`** and **`errors`** enable cost control and circuit breakers.
- **`nodes`** counts enable loop prevention.
- **`retries`** config controls LLM validation retry attempts.
- **Failure signals** (`llm_failure_signal` for nodes, `failure_signal` for tools) enable graceful error handling instead of exceptions.
