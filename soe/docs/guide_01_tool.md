
# SOE Guide: Chapter 1 - Tool Nodes

## Introduction to Tool Nodes

The **Tool Node** executes a Python function directly. It's the most concrete node type in SOE—it does real work: calling APIs, processing data, interacting with databases.

We start with Tool nodes because they represent **actual execution**. While other nodes route signals or generate text, Tool nodes are where your workflow touches the real world.

### When to Use Tool Nodes

- **External Operations**: Sending emails, processing payments, database queries
- **API Calls**: HTTP requests, third-party service integrations
- **Data Transformations**: Calculations, file processing, format conversions
- **Deterministic Logic**: When you need code, not AI

## Your First Tool Node

Let's send an email using a tool node.

### The Workflow

```yaml
example_workflow:
  SendEmail:
    node_type: tool
    event_triggers: [START]
    tool_name: send_email
    context_parameter_field: email_data
    output_field: email_result
    event_emissions:
      - signal_name: EMAIL_SENT
```

### How It Works

1.  **`tool_name`**: The key in your `tools_registry` dict.
2.  **`context_parameter_field`**: The context field containing the tool's kwargs (a dict).
3.  **`output_field`**: Where to store the result in context.
4.  **`event_emissions`**: Signals to emit after execution (conditions evaluate `result`).

## Passing Parameters to Tools

There are two ways to pass parameters to a tool: **inline parameters** (hardcoded in YAML) or **context parameters** (dynamic from context).

### Option 1: Inline Parameters (Static)

Use `parameters` to specify tool arguments directly in the workflow YAML:

```yaml
example_workflow:
  ReadToolDocs:
    node_type: tool
    event_triggers: [START]
    tool_name: soe_explore_docs
    parameters:
      path: "soe/docs/guide_01_tool.md"
      action: "read"
    output_field: tool_documentation
    event_emissions:
      - signal_name: DOCS_READY
```

**Jinja templates work in parameters:**

```yaml
example_workflow:
  FetchUserData:
    node_type: tool
    event_triggers: [START]
    tool_name: fetch_data
    parameters:
      user_id: "&#123;&#123; context.current_user_id &#125;&#125;"
      include_history: true
    output_field: user_data
    event_emissions:
      - signal_name: DATA_FETCHED
```

### Option 2: Context Parameters (Dynamic)

Use `context_parameter_field` when the parameters come from another node's output or initial context:

```yaml
example_workflow:
  SendEmail:
    node_type: tool
    event_triggers: [START]
    tool_name: send_email
    context_parameter_field: email_data
    output_field: email_result
```

### Understanding context_parameter_field

The `context_parameter_field` specifies which context field contains the parameters to pass to your tool. This field must contain a dictionary that will be unpacked as keyword arguments.

**Where does this data come from?**

1. **Initial context**: You can pass it when starting the workflow:
   ```python
   orchestrate(
       config=workflow,
       initial_context={"email_data": {"to": "user@example.com", "subject": "Hello"}}
   )
   ```

2. **LLM output**: An LLM node can generate structured parameters:
   ```yaml
   ExtractEmailParams:
     node_type: llm
     prompt: "Extract email parameters from: {{ context.user_request }}"
     output_field: email_data  # LLM returns {"to": "...", "subject": "...", "body": "..."}

   SendEmail:
     node_type: tool
     tool_name: send_email
     context_parameter_field: email_data  # Uses LLM output as tool input
   ```

3. **Another tool's output**: Chain tools together:
   ```yaml
   PrepareData:
     node_type: tool
     tool_name: prepare_email_data
     output_field: email_data

   SendEmail:
     node_type: tool
     tool_name: send_email
     context_parameter_field: email_data  # Uses previous tool's output
   ```

**Tip**: Use [Context Schema](guide_06_schema.md) to validate that LLM output has the correct structure before passing to tools.

### The Tools Registry

Tools are registered as plain Python functions:

```python
def send_email(to: str, subject: str, body: str) -> dict:
    # Your email sending logic
    return {"status": "sent", "to": to}

tools_registry = {
    "send_email": send_email,
}
```

## Event Emissions with Conditions

Tool nodes use `event_emissions` with optional Jinja conditions. Signals without conditions are always emitted on success. Signals with conditions can reference:

- **`result`**: The tool's return value
- **`context`**: The full workflow context

### Conditional Signal Example

```yaml
example_workflow:
  ProcessPayment:
    node_type: tool
    event_triggers: [START]
    tool_name: process_payment
    context_parameter_field: payment_data
    output_field: payment_result
    event_emissions:
      - signal_name: PAYMENT_SUCCESS
        condition: "&#123;&#123; result.status == 'approved' &#125;&#125;"
      - signal_name: PAYMENT_DECLINED
        condition: "&#123;&#123; result.status == 'declined' &#125;&#125;"
      - signal_name: PAYMENT_PENDING
        condition: "&#123;&#123; result.status == 'pending' &#125;&#125;"
```

### How It Works

1.  Tool executes and stores result in `output_field`.
2.  Each `event_emissions` condition is evaluated against both `result` and `context`.
3.  Signals with matching conditions (or no condition) are emitted.

**Note:** `event_emissions` are only evaluated on successful execution. For failure handling, use `failure_signal` in the registry.

### Combining Result and Context

Conditions can use both the tool's output and existing context values:

```yaml
example_workflow:
  ProcessPayment:
    node_type: tool
    event_triggers: [START]
    tool_name: process_payment
    context_parameter_field: payment_data
    output_field: payment_result
    event_emissions:
      - signal_name: PAYMENT_SUCCESS
        condition: "&#123;&#123; result.status == 'approved' &#125;&#125;"
      - signal_name: VIP_PAYMENT_SUCCESS
        condition: "&#123;&#123; result.status == 'approved' and context.customer.is_vip &#125;&#125;"
      - signal_name: LARGE_PAYMENT_SUCCESS
        condition: "&#123;&#123; result.status == 'approved' and context.payment_data.amount > 1000 &#125;&#125;"
```

This is useful when you need to:
- Combine tool output with customer data (VIP handling)
- Check result against thresholds from context
- Route based on both tool success and workflow state

## Extended Tool Registry

For more control over tool behavior, use the extended format:

```python
tools_registry = {
    # Simple format (default: max_retries=1)
    "send_email": send_email,

    # Extended format with configuration
    "process_payment": {
        "function": process_payment,
        "max_retries": 3,  # Retry up to 3 times on failure
        "failure_signal": "PAYMENT_FAILED",  # Emit when all retries exhausted
    },
}
```

**Extended registry fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `function` | Callable | (required) | The Python function to execute |
| `max_retries` | int | 1 | Number of retries after initial failure |
| `failure_signal` | str | None | Signal to emit when all retries exhausted |
| `process_accumulated` | bool | False | Pass full history list (advanced) |

> **Note:** The `process_accumulated` option is an advanced feature for aggregation patterns. It allows a tool to receive the entire history of a context field instead of just the last value. See [Fan-Out, Fan-In & Aggregations](advanced_patterns/guide_fanout_and_aggregations.md) for details.

### Success vs Failure Flow

```
Tool executes
    │
    ├── Success → evaluate event_emissions → emit matching signals
    │
    └── Exception → retry up to max_retries
                        │
                        └── All retries failed → emit failure_signal (if defined)
```

**When to use extended format:**

- **Flaky operations**: Set `max_retries` higher for network calls or external APIs
- **Critical failures**: Use `failure_signal` to handle unrecoverable errors

## Next Steps

Now that you can execute real operations, let's add intelligence with [LLM Nodes](guide_02_llm.md) →
