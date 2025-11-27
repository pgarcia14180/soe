
# SOE Guide: Chapter 7 - Identity

## Introduction to Identity

**Identity** enables two powerful features:

1. **Stateful LLM interactions** — Persisting conversation history across calls
2. **System prompts** — Defining roles for LLM/Agent nodes (via Identity Schema)

Without identity, each LLM call is independent. With identity, the LLM "remembers" previous exchanges—similar to Claude's Projects or custom instructions, but dynamically per-execution.

### Why Identity Matters

Traditional orchestration treats each LLM call as stateless:
- No memory of previous responses
- No context accumulation
- Each call starts fresh
- You must specify role/instructions in every prompt

Identity transforms this into **dynamic prompting**:
- Conversation history builds over time
- LLM can reference its own previous responses
- Enables multi-turn dialogues within workflows
- **Identity Schema removes the need to specify role in every prompt**

### Identity Schema in Config

Like context schema, identities are defined in your config YAML:

```yaml
workflows:
  example_workflow:
    Analyzer:
      node_type: llm
      event_triggers: [START]
      prompt: "Analyze: {{ context.input }}"
      identity: analyst  # References identity defined below
      output_field: analysis
      event_emissions:
        - signal_name: DONE

identities:
  analyst: |
    You are a senior data analyst. Be thorough and precise.
    Always cite sources when making claims.
  reviewer: |
    You are a code reviewer. Focus on correctness and maintainability.
```

When `identities` is included in config:
1. It's automatically saved to the `IdentityBackend`
2. LLM/Agent nodes with matching `identity` field receive the system prompt
3. Child workflows can access parent's identities through `main_execution_id`

**This removes the need to repeat role instructions in every prompt** — define once in identities, use everywhere.

### Key Insight

**Identity only matters when you have MULTIPLE LLM calls.**

A single LLM node with identity doesn't demonstrate anything—the power comes when a second node with the *same* identity sees the first node's conversation history.

### The Claude Skills Parallel

Think of identity like **Claude Skills** or **Custom Instructions**:

| Claude Skills | SOE Identity |
|---------------|--------------|
| Persistent per-project | Persistent per-identity |
| User configures manually | Workflow configures dynamically |
| One instruction set | Multiple identities per workflow |
| Static prompts | Dynamic context + history |

## Multi-Turn Conversations (Same Identity)

Same identity across nodes enables multi-turn dialogues:

### The Workflow

```yaml
example_workflow:
  FirstTurn:
    node_type: llm
    event_triggers: [START]
    identity: conversation_abc
    prompt: "Start a conversation about &#123;&#123; context.topic &#125;&#125;"
    output_field: firstResponse
    event_emissions:
      - signal_name: FIRST_COMPLETE

  SecondTurn:
    node_type: llm
    event_triggers: [FIRST_COMPLETE]
    identity: conversation_abc
    prompt: "Continue the conversation. User asks: &#123;&#123; context.follow_up &#125;&#125;"
    output_field: secondResponse
    event_emissions:
      - signal_name: CONVERSATION_COMPLETE
```

### How It Works

1.  `FirstTurn` executes with `identity: conversation_abc`.
2.  Prompt and response are saved to conversation history.
3.  `SecondTurn` triggers with the **same identity**.
4.  LLM receives `conversation_history` containing the first exchange.
5.  The second LLM can reference: "As I mentioned about technology..."

### What You'll See in the Prompt

```json
{
  "prompt": "Continue the conversation. User asks: Tell me more",
  "context": "...",
  "conversation_history": "[user]: Start a conversation about technology\n[assistant]: Technology is fascinating! ..."
}
```

The `conversation_history` field is automatically populated because both nodes share `identity: conversation_abc`.

## All Identities Share History (Within Execution)

Nodes with **different** identity values still share history within the same orchestration:

### The Workflow

```yaml
example_workflow:
  FirstTurn:
    node_type: llm
    event_triggers: [START]
    identity: session_A
    prompt: "Start a conversation about &#123;&#123; context.topic &#125;&#125;"
    output_field: firstResponse
    event_emissions:
      - signal_name: FIRST_COMPLETE

  SecondTurn:
    node_type: llm
    event_triggers: [FIRST_COMPLETE]
    identity: session_B
    prompt: "Continue the conversation. User asks: &#123;&#123; context.follow_up &#125;&#125;"
    output_field: secondResponse
    event_emissions:
      - signal_name: CONVERSATION_COMPLETE
```

### What Actually Happens

1.  `FirstTurn` has identity `session_A` → history enabled, keyed by `main_execution_id`.
2.  `SecondTurn` has identity `session_B` → history enabled, same `main_execution_id`.
3.  **Both share the same conversation history** because they use the same execution.
4.  The identity VALUE (`session_A` vs `session_B`) doesn't matter—only its presence.

**Key insight**: Identity isolation happens at the **orchestration boundary**, not within a workflow.

## No Identity = No History

Without identity, each call is completely stateless:

### The Workflow

```yaml
example_workflow:
  FirstTurn:
    node_type: llm
    event_triggers: [START]
    prompt: "Start a conversation about &#123;&#123; context.topic &#125;&#125;"
    output_field: firstResponse
    event_emissions:
      - signal_name: FIRST_COMPLETE

  SecondTurn:
    node_type: llm
    event_triggers: [FIRST_COMPLETE]
    prompt: "Continue the conversation. User asks: &#123;&#123; context.follow_up &#125;&#125;"
    output_field: secondResponse
    event_emissions:
      - signal_name: CONVERSATION_COMPLETE
```

### What Happens

1.  `FirstTurn` executes, but nothing is saved (no identity).
2.  `SecondTurn` executes with **empty history**.
3.  Neither node knows about the other.
4.  Pure function-like, stateless behavior.

Use this for independent LLM calls that don't need context.

## How Identity Actually Works

**Important**: Identity is a **boolean flag**, not a key.

- **Identity present (any truthy value)**: Conversation history is enabled
- **Identity absent or empty**: No conversation history

### The Reality

Conversation history is keyed by `main_execution_id`, NOT the identity value:

```python
# All these share the SAME history within one orchestration:
identity: conversation_abc    # History keyed by main_execution_id
identity: session_A           # Same history - same main_execution_id
identity: user_123            # Same history - same main_execution_id

# Only this is different:
# (no identity)               # No history at all
```

This means **all LLM/Agent nodes with any identity share conversation history within an execution tree**. The identity value itself doesn't isolate conversations—it just enables the feature.

### When You Need Isolation

If you need truly isolated conversation histories, you must use **separate orchestration calls**:

```python
# Execution 1 - has its own main_execution_id
execution_1 = orchestrate(
    initial_context={"user_id": "alice"},
    ...
)

# Execution 2 - different main_execution_id, different history
execution_2 = orchestrate(
    initial_context={"user_id": "bob"},
    ...
)
```

Each `orchestrate()` call creates a new `main_execution_id`, giving isolated histories.

## History Accumulates Over Turns

With three or more nodes using the same identity, history grows:

### The Workflow

```yaml
example_workflow:
  Turn1:
    node_type: llm
    event_triggers: [START]
    identity: long_conversation
    prompt: "User says: &#123;&#123; context.msg1 &#125;&#125;"
    output_field: response1
    event_emissions:
      - signal_name: TURN1_DONE

  Turn2:
    node_type: llm
    event_triggers: [TURN1_DONE]
    identity: long_conversation
    prompt: "User says: &#123;&#123; context.msg2 &#125;&#125;"
    output_field: response2
    event_emissions:
      - signal_name: TURN2_DONE

  Turn3:
    node_type: llm
    event_triggers: [TURN2_DONE]
    identity: long_conversation
    prompt: "User says: &#123;&#123; context.msg3 &#125;&#125;"
    output_field: response3
    event_emissions:
      - signal_name: TURN3_DONE
```

### Accumulation Pattern

| Turn | Sees History From |
|------|------------------|
| Turn1 | (empty) |
| Turn2 | Turn1 |
| Turn3 | Turn1 + Turn2 |

Each subsequent call sees all previous exchanges, enabling long-form conversations.

## The Skill Pattern

Combine routing with specialized identities for Claude-like skills:

### The Workflow

```yaml
example_workflow:
  SkillRouter:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: CODING_SKILL
        condition: "&#123;&#123; 'code' in context.request|lower &#125;&#125;"
      - signal_name: WRITING_SKILL
        condition: "&#123;&#123; 'write' in context.request|lower &#125;&#125;"
      - signal_name: GENERAL_SKILL
        condition: "&#123;&#123; 'code' not in context.request|lower and 'write' not in context.request|lower &#125;&#125;"

  CodingAssistant:
    node_type: llm
    event_triggers: [CODING_SKILL]
    identity: "&#123;&#123; context.user_id &#125;&#125;_coding"
    prompt: "You are a coding assistant. Help with: &#123;&#123; context.request &#125;&#125;"
    output_field: response
    event_emissions:
      - signal_name: SKILL_COMPLETE

  WritingAssistant:
    node_type: llm
    event_triggers: [WRITING_SKILL]
    identity: "&#123;&#123; context.user_id &#125;&#125;_writing"
    prompt: "You are a writing assistant. Help with: &#123;&#123; context.request &#125;&#125;"
    output_field: response
    event_emissions:
      - signal_name: SKILL_COMPLETE

  GeneralAssistant:
    node_type: llm
    event_triggers: [GENERAL_SKILL]
    identity: "&#123;&#123; context.user_id &#125;&#125;_general"
    prompt: "Help with: &#123;&#123; context.request &#125;&#125;"
    output_field: response
    event_emissions:
      - signal_name: SKILL_COMPLETE
```

### How Skills Work

1.  `SkillRouter` routes based on request content.
2.  Each skill assistant has its own identity: `{{ context.user_id }}_coding`.
3.  Coding history stays with coding assistant.
4.  Writing history stays with writing assistant.
5.  User builds separate expertise relationships per skill.

### Benefits

- **Specialized memory**: Each skill remembers its domain conversations.
- **No cross-contamination**: Coding advice doesn't leak into writing context.
- **Dynamic prompting**: Same user, different "personalities" per skill.

## Identity and Strong Models

Identity enables **dynamic prompting** patterns that leverage strong models' capabilities:

### Why Strong Models Benefit

Strong models like Claude, GPT-4, and Gemini Pro excel at:
- Maintaining context across long conversations
- Referencing previous exchanges accurately
- Building on established patterns

Identity unlocks this within stateless orchestration:

```python
# First call builds context
LLM: "You want to build a REST API. Let's start with the data model..."

# Second call (same identity) references first
LLM: "Based on the User model we designed, here's the authentication..."

# Third call builds further
LLM: "Now that auth is set up, let's add the protected endpoints..."
```

### The Dynamic Prompting Pattern

1.  **Initial context**: First call establishes baseline.
2.  **Accumulated history**: Each call adds to shared context.
3.  **Progressive refinement**: Later calls can reference and build.
4.  **No explicit state management**: History is automatic.

## Defining Identities in Config (Recommended)

The simplest approach is defining `identities` alongside your workflows. Each identity maps to a system prompt:

```yaml
workflows:
  example_workflow:
    FirstTurn:
      node_type: llm
      event_triggers: [START]
      identity: helpful_assistant
      prompt: "Start a conversation about &#123;&#123; context.topic &#125;&#125;"
      output_field: firstResponse
      event_emissions:
        - signal_name: FIRST_COMPLETE

    SecondTurn:
      node_type: llm
      event_triggers: [FIRST_COMPLETE]
      identity: helpful_assistant
      prompt: "Continue the conversation. User asks: &#123;&#123; context.follow_up &#125;&#125;"
      output_field: secondResponse
      event_emissions:
        - signal_name: CONVERSATION_COMPLETE

identities:
  helpful_assistant: "You are a friendly and knowledgeable assistant who explains topics clearly."
```

When `identities` is included in config:
1. Identity definitions are automatically saved to the identity backend
2. They're keyed by `execution_id` (specifically `main_execution_id`)
3. Child workflows can access parent's identity definitions
4. The identity value in nodes (e.g., `identity: helpful_assistant`) is looked up from the definitions

### Multiple Identities

Define multiple specialized identities for different roles:

```yaml
workflows:
  example_workflow:
    SkillRouter:
      node_type: router
      event_triggers: [START]
      event_emissions:
        - signal_name: CODING_SKILL
          condition: "&#123;&#123; 'code' in context.request|lower &#125;&#125;"
        - signal_name: WRITING_SKILL
          condition: "&#123;&#123; 'write' in context.request|lower &#125;&#125;"

    CodingAssistant:
      node_type: llm
      event_triggers: [CODING_SKILL]
      identity: coding_expert
      prompt: "Help with: &#123;&#123; context.request &#125;&#125;"
      output_field: response
      event_emissions:
        - signal_name: SKILL_COMPLETE

    WritingAssistant:
      node_type: llm
      event_triggers: [WRITING_SKILL]
      identity: writing_expert
      prompt: "Help with: &#123;&#123; context.request &#125;&#125;"
      output_field: response
      event_emissions:
        - signal_name: SKILL_COMPLETE

identities:
  coding_expert: "You are an expert programmer. Provide clear, well-documented code examples."
  writing_expert: "You are a skilled writer. Focus on clarity, grammar, and style."
```

### Full Config (Workflows + Schema + Identities)

Combine all sections for complete configuration:

```yaml
workflows:
  example_workflow:
    ExtractData:
      node_type: llm
      event_triggers: [START]
      identity: data_analyst
      prompt: "Extract key information from: &#123;&#123; context.input &#125;&#125;"
      output_field: extracted_data
      event_emissions:
        - signal_name: DATA_EXTRACTED

    SummarizeData:
      node_type: llm
      event_triggers: [DATA_EXTRACTED]
      identity: data_analyst
      prompt: "Summarize the extracted data: &#123;&#123; context.extracted_data &#125;&#125;"
      output_field: summary
      event_emissions:
        - signal_name: DONE

context_schema:
  extracted_data:
    type: object
    description: Structured data extracted from input
  summary:
    type: string
    description: A concise summary of the extracted data

identities:
  data_analyst: "You are a data analyst. Be precise, structured, and thorough in your analysis."
```

## Conversation History API

Access history programmatically:

```python
from soe.local_backends import create_local_backends

backends = create_local_backends(...)

# Get conversation history (keyed by execution_id)
history = backends.conversation_history.get_conversation_history(execution_id)

# Append to history
backends.conversation_history.append_to_conversation_history(
    execution_id,
    {"role": "user", "content": "Hello"}
)

# Replace entire history
backends.conversation_history.save_conversation_history(
    execution_id,
    [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello!"}
    ]
)

# Clear history
backends.conversation_history.delete_conversation_history(execution_id)
```

## Identity Best Practices

### Do

- **Define in config**: Use `identities` section for clear, centralized definitions.
- **Use meaningful names**: `coding_expert` over `abc123`.
- **Scope appropriately**: One identity per logical conversation.
- **Clean up old histories**: Delete stale conversation data.

### Don't

- **Share identities across unrelated tasks**: Causes context confusion.
- **Use identity for short, independent tasks**: Adds unnecessary overhead.
- **Forget about history growth**: Long histories consume tokens.

## Key Points

- **Define in config**: Use `identities` section in your config for automatic setup.
- **Simple format**: `identity_name: "system prompt"` - just a string.
- **Keyed by execution_id**: Identities are stored by `main_execution_id`, enabling child workflow access.
- **History keyed by execution**: All nodes share history via `main_execution_id`.
- **Isolation at orchestration boundary**: Different `orchestrate()` calls have different histories.

## Next Steps

Now that you understand stateful interactions, let's explore [Child Workflows](guide_08_child.md) for sub-orchestration and modular composition →
