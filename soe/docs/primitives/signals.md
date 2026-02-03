
# Appendix C: Signals Reference

This appendix covers everything about signals in SOE: how they trigger nodes, how they're emitted, and the condition evaluation rules for each node type.

All examples are tested. Run them with:

```bash
uv run pytest tests/test_cases/appendix/c_signals/ -v
```

---

## What Are Signals?

Signals are the **communication mechanism** between nodes in SOE. They:

- **Trigger** nodes via `event_triggers`
- **Route** execution flow between nodes
- **Propagate** to parent workflows in sub-orchestration

Think of signals like events in a pub/sub system. Nodes subscribe to signals they care about, and emit signals to notify other nodes.

---

## Signal Naming Best Practices

### Use Descriptive, Action-Oriented Names

```yaml
# ✅ Good - clear intent
event_emissions:
  - signal_name: ANALYSIS_COMPLETE
  - signal_name: VALIDATION_FAILED
  - signal_name: USER_VERIFIED

# ❌ Bad - vague or generic
event_emissions:
  - signal_name: DONE
  - signal_name: NEXT
  - signal_name: STEP_2
```

### Prefix Workflow-Specific Signals

When using sub-orchestration, prefix signals with the workflow name for clarity:

```yaml
# Parent workflow
signals_to_parent: [ANALYSIS_COMPLETE]  # Clear origin

# Instead of
signals_to_parent: [DONE]  # What finished? Unclear to parent
```

### Use Consistent Conventions

| Convention | Example | Use Case |
|------------|---------|----------|
| `*_COMPLETE` | `ANALYSIS_COMPLETE` | Successful completion |
| `*_FAILED` | `VALIDATION_FAILED` | Error states |
| `*_READY` | `DATA_READY` | Readiness signals |
| `*_REQUIRED` | `REVIEW_REQUIRED` | Action needed |

---

## The `event_emissions` Field

Every node type can emit signals via `event_emissions`:

```yaml
event_emissions:
  - signal_name: SUCCESS
  - signal_name: NEEDS_REVIEW
    condition: "{{ result.confidence < 0.8 }}"
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `signal_name` | `str` | Yes | The signal to emit |
| `condition` | `str` | No | Controls when the signal is emitted |

### No Signals (Terminal Node)

A node with empty or missing `event_emissions` is a **terminal node**—it executes but emits nothing:

```yaml
LogAndFinish:
  node_type: tool
  event_triggers: [COMPLETE]
  tool_name: log_result
  input_fields: [result]
  # No event_emissions = terminal node
```

Use this pattern for:
- Final logging/cleanup nodes
- Fire-and-forget operations
- Workflow endpoints

---

## Condition Types: The Three Modes

The `condition` field has **three modes** that determine when and how signals are emitted:

### Mode 1: No Condition (Unconditional)

Signals without conditions **always emit** after node execution:

```yaml
example_workflow:
  TriggerMultiple:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: PROCESSING_DONE
      - signal_name: LOG_EVENT
```

Both `PROCESSING_DONE` and `LOG_EVENT` emit every time the node runs.

> **Note**: For Router nodes, multiple unconditional signals all emit simultaneously (fan-out pattern). For LLM/Agent nodes with multiple signals, the LLM can select any/all that apply—including none.

### Mode 2: Jinja Template (Programmatic)

Conditions containing `{{ }}` are evaluated programmatically:

```yaml
example_workflow:
  AnalyzeAndRoute:
    node_type: llm
    event_triggers: [START]
    prompt: "Analyze: &#123;&#123; context.text &#125;&#125;"
    output_field: analysis
    event_emissions:
      - signal_name: HIGH_PRIORITY
        condition: "&#123;&#123; context.priority > 5 &#125;&#125;"
      - signal_name: NORMAL_PRIORITY
        condition: "&#123;&#123; context.priority <= 5 &#125;&#125;"
```

SOE evaluates `context.priority > 5` and emits the matching signal. No LLM involvement.

### Mode 3: Plain Text (Semantic/LLM Selection)

Plain text conditions trigger LLM signal selection:

```yaml
example_workflow:
  SentimentRouter:
    node_type: llm
    event_triggers: [START]
    prompt: "Analyze the sentiment of this message: &#123;&#123; context.message &#125;&#125;"
    output_field: sentiment_analysis
    event_emissions:
      - signal_name: POSITIVE_SENTIMENT
        condition: "The message expresses happiness, satisfaction, or positive emotions"
      - signal_name: NEGATIVE_SENTIMENT
        condition: "The message expresses anger, frustration, or negative emotions"
      - signal_name: NEUTRAL_SENTIMENT
        condition: "The message is factual, neutral, or emotionally ambiguous"
```

SOE asks the LLM: "Based on your analysis, which signal should be emitted?" The LLM chooses based on semantic understanding.

---

## How SOE Decides: The Decision Tree

The behavior depends on the node type:

### Router Node

```

┌─────────────────────────────────────────────────────────────┐
│                  Router Signal Emission                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  For EACH signal in event_emissions:                         │
│     └─ No condition? → Emit                                  │
│     └─ Jinja condition? → Evaluate, emit if truthy           │
│                                                              │
│  → Multiple signals can emit (fan-out pattern)               │
│                                                              │
└─────────────────────────────────────────────────────────────┘

```

### LLM/Agent Node

```

┌─────────────────────────────────────────────────────────────┐
│               LLM/Agent Signal Emission                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Any condition contains {{ }}?                            │
│     └─ YES → Evaluate ALL conditions programmatically        │
│              Emit signals where condition is truthy          │
│     └─ NO → Continue to step 2                               │
│                                                              │
│  2. Count signals                                            │
│     └─ Zero signals? → Nothing emitted                       │
│     └─ Single signal? → Emit unconditionally                 │
│     └─ Multiple signals?                                     │
│         └─ LLM selects ANY/ALL that apply                    │
│            (uses conditions as semantic descriptions)        │
│            (can select none, one, or multiple)               │
│                                                              │
└─────────────────────────────────────────────────────────────┘

```

### Critical Rule: Jinja Takes Over

If **any** condition contains `{{ }}`, ALL conditions are evaluated programmatically. The LLM never selects signals when Jinja is present.

---

## Signal Behavior by Node Type

### Router Node

**Purpose**: Conditional branching based on context.

**Condition Context**: `context` only.

**Evaluation**: Always programmatic (Jinja). Plain text conditions are not LLM-selected.

```yaml
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: HAS_DATA
        condition: "&#123;&#123; context.data is defined and context.data &#125;&#125;"
      - signal_name: NO_DATA
        condition: "&#123;&#123; context.data is not defined or not context.data &#125;&#125;"

  ProcessData:
    node_type: router
    event_triggers: [HAS_DATA]
    event_emissions:
      - signal_name: DONE

  HandleMissing:
    node_type: router
    event_triggers: [NO_DATA]
    event_emissions:
      - signal_name: DONE
```

**Key Point**: Router conditions must use Jinja. Plain text won't work as expected.

---

### LLM Node

**Purpose**: Single LLM call with optional signal selection.

**Condition Context**: `context` only (LLM output stored in `output_field`).

**Evaluation**: Jinja → programmatic. Plain text → LLM selection.

**Jinja Example** (SOE evaluates):

```yaml
example_workflow:
  AnalyzeAndRoute:
    node_type: llm
    event_triggers: [START]
    prompt: "Analyze: &#123;&#123; context.text &#125;&#125;"
    output_field: analysis
    event_emissions:
      - signal_name: HIGH_PRIORITY
        condition: "&#123;&#123; context.priority > 5 &#125;&#125;"
      - signal_name: NORMAL_PRIORITY
        condition: "&#123;&#123; context.priority <= 5 &#125;&#125;"
```

**Plain Text Example** (LLM selects):

```yaml
example_workflow:
  SentimentRouter:
    node_type: llm
    event_triggers: [START]
    prompt: "Analyze the sentiment of this message: &#123;&#123; context.message &#125;&#125;"
    output_field: sentiment_analysis
    event_emissions:
      - signal_name: POSITIVE_SENTIMENT
        condition: "The message expresses happiness, satisfaction, or positive emotions"
      - signal_name: NEGATIVE_SENTIMENT
        condition: "The message expresses anger, frustration, or negative emotions"
      - signal_name: NEUTRAL_SENTIMENT
        condition: "The message is factual, neutral, or emotionally ambiguous"
```

**LLM Selection Mechanism**: SOE adds a `selected_signals` field to the response model, allowing the LLM to select any/all signals that apply. The condition text serves as the description.

---

### Agent Node

**Purpose**: ReAct loop with tool access.

**Condition Context**: `context` only.

**Evaluation**: Same as LLM node—Jinja → programmatic, plain text → LLM selection.

```yaml
example_workflow:
  TaskAgent:
    node_type: agent
    event_triggers: [START]
    prompt: "Help the user with their request: &#123;&#123; context.request &#125;&#125;"
    available_tools: [search, calculate]
    output_field: result
    event_emissions:
      - signal_name: TASK_COMPLETED
        condition: "The task was successfully completed with a satisfactory result"
      - signal_name: TASK_FAILED
        condition: "The task could not be completed due to limitations or errors"
      - signal_name: TASK_NEEDS_CLARIFICATION
        condition: "The request is ambiguous and needs more information from the user"
```

**Note**: Agent tools are selected by the LLM within the ReAct loop. Signal selection is a separate decision made after the agent loop completes.

---

### Tool Node

**Purpose**: Direct function execution.

**Condition Context**: `result` AND `context`.

**Evaluation**: Always programmatic. No LLM selection (tools don't call LLMs).

```yaml
example_workflow:
  ProcessPayment:
    node_type: tool
    event_triggers: [START]
    tool_name: process_payment
    context_parameter_field: payment_data
    output_field: payment_result
    event_emissions:
      - signal_name: PAYMENT_APPROVED
        condition: "&#123;&#123; result.status == 'approved' &#125;&#125;"
      - signal_name: PAYMENT_DECLINED
        condition: "&#123;&#123; result.status == 'declined' &#125;&#125;"
      - signal_name: PAYMENT_PENDING
        condition: "&#123;&#123; result.status == 'pending' &#125;&#125;"

  OnApproved:
    node_type: router
    event_triggers: [PAYMENT_APPROVED]
    event_emissions:
      - signal_name: DONE

  OnDeclined:
    node_type: router
    event_triggers: [PAYMENT_DECLINED]
    event_emissions:
      - signal_name: DONE

  OnPending:
    node_type: router
    event_triggers: [PAYMENT_PENDING]
    event_emissions:
      - signal_name: DONE
```

#### The `result` Keyword

Tool nodes have a special `result` variable in condition evaluation:

| Variable | Description | Example |
|----------|-------------|---------|
| `result` | The return value of the tool function | `{{ result.status }}` |
| `context` | The execution context | `{{ context.user_id }}` |

**Combining result and context**:

```yaml
example_workflow:
  CheckOrder:
    node_type: tool
    event_triggers: [START]
    tool_name: validate_order
    context_parameter_field: order
    output_field: validation
    event_emissions:
      - signal_name: VIP_LARGE_ORDER
        condition: "&#123;&#123; result.valid and context.customer.is_vip and context.order.total > 1000 &#125;&#125;"
      - signal_name: VIP_ORDER
        condition: "&#123;&#123; result.valid and context.customer.is_vip &#125;&#125;"
      - signal_name: LARGE_ORDER
        condition: "&#123;&#123; result.valid and context.order.total > 1000 &#125;&#125;"
      - signal_name: STANDARD_ORDER
        condition: "&#123;&#123; result.valid &#125;&#125;"
      - signal_name: INVALID_ORDER
        condition: "&#123;&#123; not result.valid &#125;&#125;"
```

**Why `result`?**: Tools return values that aren't stored in context until after condition evaluation. The `result` keyword provides access to the raw return value.

---

### Child Node

**Purpose**: Sub-orchestration.

**Condition Context**: `context` only.

**Evaluation**: Always programmatic.

**Note**: Child node `event_emissions` fire after the child workflow **starts**, not when it completes. Use `signals_to_parent` to get completion signals.

---

## Failure Signals

LLM, Agent, and Tool nodes can emit **failure signals** when they fail after exhausting retries. This enables graceful error handling.

### LLM Failure Signal

```yaml
example_workflow:
  RiskyLLMCall:
    node_type: llm
    event_triggers: [START]
    prompt: "Generate a complex response for: &#123;&#123; context.input &#125;&#125;"
    output_field: response
    retries: 2
    llm_failure_signal: LLM_FAILED
    event_emissions:
      - signal_name: SUCCESS

  HandleSuccess:
    node_type: router
    event_triggers: [SUCCESS]
    event_emissions:
      - signal_name: WORKFLOW_COMPLETE

  HandleFailure:
    node_type: router
    event_triggers: [LLM_FAILED]
    event_emissions:
      - signal_name: WORKFLOW_COMPLETE
```

When the LLM fails after 2 retries (3 total attempts), `LLM_FAILED` is emitted instead of `SUCCESS`.

### Agent Failure Signal

```yaml
example_workflow:
  ComplexAgent:
    node_type: agent
    event_triggers: [START]
    prompt: "Complete this complex task: &#123;&#123; context.task &#125;&#125;"
    available_tools: [search]
    output_field: result
    retries: 1
    llm_failure_signal: AGENT_EXHAUSTED
    event_emissions:
      - signal_name: TASK_DONE

  OnSuccess:
    node_type: router
    event_triggers: [TASK_DONE]
    event_emissions:
      - signal_name: DONE

  OnFailure:
    node_type: router
    event_triggers: [AGENT_EXHAUSTED]
    event_emissions:
      - signal_name: DONE
```

### Tool Failure Signal (Registry-Based)

Unlike LLM/Agent nodes, tool failure signals are configured in the **tools registry**, not in the YAML workflow:

```yaml
example_workflow:
  CallExternalAPI:
    node_type: tool
    event_triggers: [START]
    tool_name: flaky_api
    context_parameter_field: api_params
    output_field: api_result
    event_emissions:
      - signal_name: API_SUCCESS

  OnSuccess:
    node_type: router
    event_triggers: [API_SUCCESS]
    event_emissions:
      - signal_name: DONE

  OnFailure:
    node_type: router
    event_triggers: [API_FAILED]
    event_emissions:
      - signal_name: DONE
```

The `failure_signal` is configured when creating the tools registry:

```python
tools_registry = {
    "flaky_api": {
        "function": flaky_api,
        "max_retries": 2,           # Retry up to 2 times after initial failure
        "failure_signal": "API_FAILED",  # Emit when all retries exhausted
    }
}
```

When `flaky_api` throws an exception and exhausts all retries, `API_FAILED` is emitted.

### Failure Signal Behavior

| Field | Node Type | Location | Description |
|-------|-----------|----------|-------------|
| `llm_failure_signal` | LLM, Agent | YAML workflow | Signal emitted when LLM call fails after retries |
| `retries` | LLM, Agent | YAML workflow | Number of retry attempts (default: 3) |
| `failure_signal` | Tool | Tools registry | Signal emitted when tool fails after retries |
| `max_retries` | Tool | Tools registry | Number of retry attempts (default: 1) |

**Key Points**:
- Failure signals are **only emitted** if configured
- They replace normal `event_emissions` on failure
- Use them to create error handling branches in your workflow
- Without a failure signal, failures raise exceptions
- **Tool failure signals** are in the registry because tools are Python functions with no YAML config

---

## Sub-Orchestration Signal Propagation

### The `signals_to_parent` Field

Controls which child signals propagate to the parent workflow:

```yaml
parent_workflow:
  StartAnalysis:
    node_type: child
    event_triggers: [START]
    child_workflow_name: analysis_child
    child_initial_signals: [BEGIN]
    input_fields: [data_to_analyze]
    signals_to_parent: [ANALYSIS_SUCCESS, ANALYSIS_FAILED]
    context_updates_to_parent: [analysis_result]

  OnSuccess:
    node_type: router
    event_triggers: [ANALYSIS_SUCCESS]
    event_emissions:
      - signal_name: PARENT_DONE

  OnFailure:
    node_type: router
    event_triggers: [ANALYSIS_FAILED]
    event_emissions:
      - signal_name: PARENT_DONE

analysis_child:
  Analyze:
    node_type: llm
    event_triggers: [BEGIN]
    prompt: "Analyze this data: &#123;&#123; context.data_to_analyze &#125;&#125;"
    output_field: analysis_result
    event_emissions:
      - signal_name: ANALYSIS_SUCCESS
        condition: "Analysis completed successfully"
      - signal_name: ANALYSIS_FAILED
        condition: "Analysis could not be completed"
```

Only `ANALYSIS_SUCCESS` and `ANALYSIS_FAILED` reach the parent. Other child signals stay internal.

### Best Practices for Sub-Orchestration Signals

#### 1. Use Specific, Workflow-Prefixed Names

```yaml
# ✅ Good - parent knows exactly what completed
signals_to_parent: [ANALYZER_COMPLETE, ANALYZER_FAILED]

# ❌ Bad - ambiguous in parent context
signals_to_parent: [DONE, ERROR]
```

#### 2. Keep Internal Signals Internal

Don't propagate signals that only matter within the child.

#### 3. Consider the Parent's Perspective

The parent workflow should receive signals that are actionable.

---

## The `context_updates_to_parent` Field

Controls which context keys are synced to the parent:

```yaml
SpawnAnalyzer:
  node_type: child
  context_updates_to_parent: [analysis_result, confidence_score]
```

When the child updates these keys, they're automatically copied to the parent's context.

---

## LLM Signal Selection: Under the Hood

When the LLM selects signals, SOE:

1. **Builds a response model** with a `selected_signals` field (list):
   ```python
   class Response(BaseModel):
       response: str
       selected_signals: List[Literal["POSITIVE", "NEGATIVE", "NEUTRAL"]] = []
   ```

2. **Provides descriptions** from the `condition` field:
   ```
   Select ALL signals that apply (can be none, one, or multiple):
   - POSITIVE: The message expresses positive sentiment
   - NEGATIVE: The message expresses negative sentiment
   - NEUTRAL: The message is neutral
   ```

3. **Extracts the selection** and emits all selected signals (can be empty).

This is why plain-text conditions are called "semantic"—the LLM understands the descriptions and selects all that apply.

---

## Common Patterns

### Exclusive Routing

Only one path taken based on mutually exclusive conditions:

```yaml
example_workflow:
  RouteByType:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: TYPE_A
        condition: "&#123;&#123; context.type == 'a' &#125;&#125;"
      - signal_name: TYPE_B
        condition: "&#123;&#123; context.type == 'b' &#125;&#125;"
      - signal_name: TYPE_DEFAULT
        condition: "&#123;&#123; context.type not in ['a', 'b'] &#125;&#125;"

  HandleA:
    node_type: router
    event_triggers: [TYPE_A]
    event_emissions:
      - signal_name: DONE

  HandleB:
    node_type: router
    event_triggers: [TYPE_B]
    event_emissions:
      - signal_name: DONE

  HandleDefault:
    node_type: router
    event_triggers: [TYPE_DEFAULT]
    event_emissions:
      - signal_name: DONE
```

### Fan-Out (Multiple Signals)

Multiple signals can emit simultaneously, triggering parallel processing:

```yaml
example_workflow:
  TriggerMultiple:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: NOTIFY_USER
        condition: "&#123;&#123; context.notify_user &#125;&#125;"
      - signal_name: LOG_EVENT
        condition: "&#123;&#123; context.log_enabled &#125;&#125;"
      - signal_name: UPDATE_METRICS

  NotifyUser:
    node_type: router
    event_triggers: [NOTIFY_USER]
    event_emissions:
      - signal_name: NOTIFICATION_SENT

  LogEvent:
    node_type: router
    event_triggers: [LOG_EVENT]
    event_emissions:
      - signal_name: EVENT_LOGGED

  UpdateMetrics:
    node_type: router
    event_triggers: [UPDATE_METRICS]
    event_emissions:
      - signal_name: METRICS_UPDATED
```

---

## Complete Example: Order Processing

This workflow demonstrates multiple signal patterns working together:

```yaml
order_processing:
  # 1. Router with Jinja conditions (programmatic)
  ValidateOrder:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: ORDER_VALID
        condition: "&#123;&#123; context.order['line_items']|length > 0 and context.order.total > 0 &#125;&#125;"
      - signal_name: ORDER_INVALID
        condition: "&#123;&#123; context.order['line_items']|length == 0 or context.order.total <= 0 &#125;&#125;"

  # 2. Tool with result conditions
  ProcessPayment:
    node_type: tool
    event_triggers: [ORDER_VALID]
    tool_name: charge_card
    context_parameter_field: payment_info
    output_field: payment_result
    event_emissions:
      - signal_name: PAYMENT_SUCCESS
        condition: "&#123;&#123; result.charged == true &#125;&#125;"
      - signal_name: PAYMENT_FAILED
        condition: "&#123;&#123; result.charged == false &#125;&#125;"

  # 3. LLM with failure signal and unconditional emission
  GenerateConfirmation:
    node_type: llm
    event_triggers: [PAYMENT_SUCCESS]
    prompt: "Generate a friendly order confirmation for order #&#123;&#123; context.order.id &#125;&#125;"
    output_field: confirmation_message
    retries: 2
    llm_failure_signal: CONFIRMATION_FAILED
    event_emissions:
      - signal_name: ORDER_COMPLETE

  # 4. Fan-out: notify multiple systems
  NotifySystems:
    node_type: router
    event_triggers: [ORDER_COMPLETE]
    event_emissions:
      - signal_name: NOTIFY_CUSTOMER
      - signal_name: UPDATE_INVENTORY
      - signal_name: LOG_ORDER

  # Handle failures
  HandleInvalidOrder:
    node_type: router
    event_triggers: [ORDER_INVALID]
    event_emissions:
      - signal_name: WORKFLOW_ERROR

  HandlePaymentFailed:
    node_type: router
    event_triggers: [PAYMENT_FAILED]
    event_emissions:
      - signal_name: WORKFLOW_ERROR

  HandleConfirmationFailed:
    node_type: router
    event_triggers: [CONFIRMATION_FAILED]
    event_emissions:
      - signal_name: ORDER_COMPLETE
```

**Patterns demonstrated**:
1. **Jinja conditions** (Router): `ORDER_VALID` vs `ORDER_INVALID`
2. **Tool result conditions**: `PAYMENT_SUCCESS` vs `PAYMENT_FAILED`
3. **Failure signal**: `CONFIRMATION_FAILED` on LLM error
4. **Fan-out**: `NOTIFY_CUSTOMER`, `UPDATE_INVENTORY`, `LOG_ORDER` emit together

---

## Debugging Signal Issues

### Signal Not Emitting

1. **Check condition syntax**: Is the Jinja valid?
2. **Check condition logic**: Does it evaluate to truthy?
3. **Check for typos**: Signal names are case-sensitive.

### Wrong Signal Emitting

1. **Jinja vs plain text**: Did you mean LLM selection but used Jinja?
2. **Missing condition**: Signals without conditions always emit.
3. **Multiple matches**: Multiple conditions can be truthy simultaneously.

### Jinja Attribute Access Gotcha

When accessing dict keys in Jinja, be careful with keys that conflict with dict methods:

```yaml
# ❌ BAD: 'items' conflicts with dict.items() method
condition: "{{ context.order.items|length > 0 }}"

# ✅ GOOD: Use bracket notation for conflicting keys
condition: "{{ context.order['items']|length > 0 }}"

# ✅ GOOD: Rename to avoid conflicts
condition: "{{ context.order.line_items|length > 0 }}"
```

**Conflicting dict method names to avoid**: `items`, `keys`, `values`, `get`, `pop`, `update`

### Parent Not Receiving Signal

1. **Check `signals_to_parent`**: Is the signal listed?
2. **Check signal name match**: Exact string match required.
3. **Verify child emitted**: Debug the child workflow first.

---

## Summary Table

| Node Type | Condition Context | LLM Selection? | Jinja Support | Failure Signal |
|-----------|-------------------|----------------|---------------|----------------|
| Router | `context` | No | Yes | No |
| LLM | `context` | Yes (plain text) | Yes | `llm_failure_signal` |
| Agent | `context` | Yes (plain text) | Yes | `llm_failure_signal` |
| Tool | `result`, `context` | No | Yes | Registry-based |
| Child | `context` | No | Yes | No |

---

## Key Takeaways

1. **No condition** = signal always emits
2. **Jinja condition** = programmatic evaluation by SOE
3. **Plain text condition** = semantic selection by LLM (LLM/Agent nodes only)
4. **`result` keyword** = tool return value (Tool nodes only)
5. **`signals_to_parent`** = controls sub-orchestration signal propagation
6. **Failure signals** = error handling for LLM/Agent nodes
7. Use **descriptive signal names** for maintainability
8. **Jinja takes over**: If any condition has `{{ }}`, all are evaluated programmatically
