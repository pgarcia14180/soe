
# SOE Guide: Chapter 2 - LLM Nodes

## Introduction to LLM Nodes

The **LLM Node** is a simple way to call a language model directly. Unlike Agent nodes (which we'll cover later), LLM nodes make a single call to the model and store the response.

Think of an LLM node as a specialist: it receives context, generates a response, and passes it along.

## Your First LLM Node: Text Summarization

Let's start with a common pattern: summarizing text.

### The Workflow

```yaml
example_workflow:
  SimpleLLM:
    node_type: llm
    event_triggers: [START]
    prompt: "Summarize the following text in one sentence: &#123;&#123; context.text &#125;&#125;"
    output_field: summary
    event_emissions:
      - signal_name: SUMMARY_COMPLETE
```

### How It Works

1. **Event Trigger**: The `START` signal triggers the `SimpleLLM` node.
2. **Prompt Rendering**: The Jinja2 template `{{ context.text }}` is replaced with the actual text.
3. **LLM Call**: The rendered prompt is sent to your LLM provider.
4. **Output Storage**: The response is stored in `context.summary` (the `output_field`).
5. **Signal Emission**: `SUMMARY_COMPLETE` is emitted to continue the workflow.

### Key Concepts

- **`prompt`**: A Jinja2 template. Use `{{ context.field }}` to inject context values.
- **`output_field`**: Where the LLM response is stored in context.
- **`event_emissions`**: Signals to emit after the LLM call completes.

## Chaining LLM Nodes

LLM nodes become powerful when chained together. Each node can use the output of the previous one.

### The Workflow

```yaml
example_workflow:
  Translator:
    node_type: llm
    event_triggers: [START]
    prompt: "Translate the following to Spanish: &#123;&#123; context.text &#125;&#125;"
    output_field: spanish_text
    event_emissions:
      - signal_name: TRANSLATED

  Summarizer:
    node_type: llm
    event_triggers: [TRANSLATED]
    prompt: "Summarize this Spanish text: &#123;&#123; context.spanish_text &#125;&#125;"
    output_field: summary
    event_emissions:
      - signal_name: CHAIN_COMPLETE
```

### How It Works

1. `START` triggers `Translator`
2. Translator stores Spanish text in `context.spanish_text`
3. Translator emits `TRANSLATED`
4. `TRANSLATED` triggers `Summarizer`
5. Summarizer reads `context.spanish_text` and stores summary
6. Summarizer emits `CHAIN_COMPLETE`

This pattern is incredibly useful for:
- Multi-step processing pipelines
- Translation → Analysis workflows
- Extract → Transform → Load patterns

## LLM Signal Selection (Resolution Step)

When an LLM node has multiple signals with **conditions** (plain text, not Jinja), the LLM itself decides which signals to emit.

### The Workflow

```yaml
example_workflow:
  SentimentAnalyzer:
    node_type: llm
    event_triggers: [START]
    prompt: "Analyze the sentiment of: &#123;&#123; context.user_message &#125;&#125;"
    output_field: analysis
    event_emissions:
      - signal_name: POSITIVE
        condition: "The message expresses positive sentiment"
      - signal_name: NEGATIVE
        condition: "The message expresses negative sentiment"
      - signal_name: NEUTRAL
        condition: "The message is neutral or factual"
```

### How It Works

1. The LLM analyzes the sentiment
2. SOE sees multiple signals with plain-text conditions (no `{{ }}`)
3. SOE asks the LLM: "Select ALL signals that apply" using the conditions as descriptions
4. The LLM returns a list of matching signals (can be none, one, or multiple)

This is called the **resolution step** - it lets the LLM make routing decisions based on its understanding.

### Signal Emission Rules

The `condition` field controls how signals are emitted:

| Condition | Behavior |
|-----------|----------|
| **No condition** | Signal is always emitted |
| **Plain text** | Semantic—LLM selects any/all signals that apply based on the descriptions |
| **Jinja template (`{{ }}`)** | Programmatic—evaluated against `context`, emits if truthy |

**How SOE decides:**

1. **No conditions**: All signals emit unconditionally after node execution
2. **Has conditions**: SOE checks if they contain `{{ }}`:
   - **Yes (Jinja)**: Evaluate expression against `context`—emit if result is truthy
   - **No (plain text)**: Ask LLM to select which signals apply (multi-select)

## Testing LLM Nodes

In tests, we inject a stub function instead of calling a real LLM:

```python
def stub_llm(prompt: str, config: dict) -> str:
    return "This is a predictable response."

nodes["llm"] = create_llm_node_caller(backends, stub_llm, broadcast_signals_caller)
```

The stub knows the *contract* (prompt → response), not the implementation. This keeps tests fast and deterministic.

## Next Steps

Now that you understand LLM nodes, let's see how [Router Nodes](guide_03_router.md) connect your workflows together →
