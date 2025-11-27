# SOE Advanced Patterns: Hybrid Intelligence

## Introduction

The power of SOE comes from mixing **deterministic code** with **probabilistic AI**. Routers are 100% reliable. LLMs are creative. Combine them for systems that are both flexible and safe.

This is the "Centaur" model — human-like intelligence bounded by machine precision.

### Why Hybrid Intelligence Matters

Hybrid patterns are one of SOE's biggest selling points:

1. **Low-Latency User Endpoints**: Fast, deterministic routers handle user requests immediately
2. **Async AI Processing**: LLM-driven workflows run in the background for complex analysis
3. **Self-Evolving Context**: Deterministic workflows can be enhanced by AI that modifies context

This enables architectures where:
- Users get instant responses from deterministic logic
- AI enriches/improves the system asynchronously
- Complex decisions combine both in a single workflow

---

## Pattern 1: Safety Rails

Validate inputs and outputs around AI processing.

### The Workflow

```yaml
hybrid_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: INPUT_VALID
        condition: "&#123;&#123; context.user_input is defined and context.user_input | length > 0 &#125;&#125;"
      - signal_name: INPUT_INVALID
        condition: "&#123;&#123; context.user_input is not defined or context.user_input | length == 0 &#125;&#125;"

  ProcessInput:
    node_type: tool
    event_triggers: [INPUT_VALID]
    tool_name: process_input
    context_parameter_field: process_params
    output_field: processed_result
    event_emissions:
      - signal_name: PROCESSED

  ValidateOutput:
    node_type: router
    event_triggers: [PROCESSED]
    event_emissions:
      - signal_name: OUTPUT_VALID
        condition: "&#123;&#123; context.processed_result is defined and context.processed_result.valid == true &#125;&#125;"
      - signal_name: OUTPUT_INVALID
        condition: "&#123;&#123; context.processed_result is not defined or context.processed_result.valid != true &#125;&#125;"

  Complete:
    node_type: router
    event_triggers: [OUTPUT_VALID]
    event_emissions:
      - signal_name: DONE

  HandleError:
    node_type: router
    event_triggers: [INPUT_INVALID, OUTPUT_INVALID, PROCESS_FAILED]
    event_emissions:
      - signal_name: ERROR
```

### How It Works

1. **ValidateInput** (Router) — Checks input meets requirements
2. **ProcessInput** (Tool/LLM) — Does the actual work
3. **ValidateOutput** (Router) — Ensures output meets requirements
4. **HandleError** (Router) — Catches any failures

**The AI never runs with bad input. The AI output never escapes validation.**

### The Flow

```
START
  ├─ INPUT_VALID ──→ ProcessInput ──→ PROCESSED
  │                                      ├─ OUTPUT_VALID ──→ DONE
  │                                      └─ OUTPUT_INVALID ──→ ERROR
  └─ INPUT_INVALID ──→ ERROR
```

---

## Pattern 2: LLM with Safety Rails

Same pattern but with an LLM doing the processing.

### The Workflow

```yaml
safety_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: INPUT_VALID
        condition: "&#123;&#123; context.amount is defined and context.amount > 0 &#125;&#125;"
      - signal_name: INPUT_INVALID
        condition: "&#123;&#123; context.amount is not defined or context.amount <= 0 &#125;&#125;"

  GenerateResponse:
    node_type: llm
    event_triggers: [INPUT_VALID]
    prompt: |
      Generate a professional message about a transaction of $&#123;&#123; context.amount &#125;&#125;.
      Keep it brief and professional.
    output_field: generated_message
    event_emissions:
      - signal_name: MESSAGE_GENERATED

  ValidateOutput:
    node_type: router
    event_triggers: [MESSAGE_GENERATED]
    event_emissions:
      - signal_name: OUTPUT_SAFE
        condition: "&#123;&#123; context.generated_message is defined and context.generated_message | length < 500 &#125;&#125;"
      - signal_name: OUTPUT_UNSAFE
        condition: "&#123;&#123; context.generated_message is not defined or context.generated_message | length >= 500 &#125;&#125;"

  HandleInputError:
    node_type: router
    event_triggers: [INPUT_INVALID]
    event_emissions:
      - signal_name: ERROR

  Complete:
    node_type: router
    event_triggers: [OUTPUT_SAFE]
    event_emissions:
      - signal_name: DONE

  HandleOutputError:
    node_type: router
    event_triggers: [OUTPUT_UNSAFE]
    event_emissions:
      - signal_name: ERROR
```

### How It Works

1. Router validates `amount > 0` (deterministic)
2. LLM generates professional message (creative)
3. Router validates output length < 500 (deterministic)

**Enterprise use case**: Financial messages that must be professional but also compliant.

---

## Pattern 3: Retry with Validation

LLM generates output, router validates, retry if invalid.

### The Workflow

```yaml
retry_workflow:
  Start:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: ATTEMPT

  Generate:
    node_type: llm
    event_triggers: [ATTEMPT]
    prompt: "Generate a valid JSON object with fields: name, age"
    output_field: llm_output
    event_emissions:
      - signal_name: GENERATED

  Validate:
    node_type: router
    event_triggers: [GENERATED]
    event_emissions:
      - signal_name: VALID_JSON
        condition: "&#123;&#123; context.llm_output is mapping &#125;&#125;"
      - signal_name: INVALID_JSON
        condition: "&#123;&#123; context.llm_output is not mapping &#125;&#125;"

  IncrementRetry:
    node_type: router
    event_triggers: [INVALID_JSON]
    event_emissions:
      - signal_name: ATTEMPT
        condition: "&#123;&#123; context.retry_count | default(0) < 3 &#125;&#125;"
      - signal_name: MAX_RETRIES
        condition: "&#123;&#123; context.retry_count | default(0) >= 3 &#125;&#125;"

  Complete:
    node_type: router
    event_triggers: [VALID_JSON]
    event_emissions:
      - signal_name: DONE
```

### How It Works

1. LLM generates JSON
2. Router checks if output is valid mapping
3. If invalid, increment retry counter and loop back
4. If max retries exceeded, emit `MAX_RETRIES`

**Key Insight**: The retry logic is deterministic. Only the generation is probabilistic. You control the boundaries.

---

## Why Hybrid Matters

| Pure LLM | Pure Code | Hybrid (SOE) |
|----------|-----------|--------------|
| Creative but unreliable | Reliable but rigid | Creative AND reliable |
| "Hope it follows rules" | "Can't adapt" | "Enforce rules, allow creativity" |

---

## Best Practices

1. **Validate early** — Check inputs before any AI processing
2. **Validate late** — Check outputs before any downstream effects
3. **Bound retries** — Never let loops run forever
4. **Log everything** — Use telemetry backend to track decisions

---

## Related Patterns

- [Swarm Intelligence](swarm_intelligence.md) — Multiple agents coordinating
- [Self-Evolving Workflows](self_evolving_workflows.md) — Agents that modify their own workflows
