# SOE — Signal-driven Orchestration Engine

**A protocol for orchestrating AI workflows through signals.**

---

## What SOE Is

SOE is an orchestration engine where nodes communicate through **signals** rather than direct function calls. You define workflows in YAML, and the engine handles execution.

| Approach | How It Works | Trade-off |
|----------|--------------|-----------|
| Chain-based | `Step A → B → C → D` | Simple but rigid |
| SOE Signal-based | `[SIGNAL] → all listeners respond` | Flexible, requires understanding signals |

**The C++ analogy**: Like C++ gives you control over memory and execution (compared to higher-level languages), SOE gives you control over orchestration primitives. You decide how state is stored, how LLMs are called, and how signals are broadcast. This requires more setup but means no vendor lock-in and full observability.

---

## What SOE Does

SOE orchestrates workflows through **signals**. Nodes don't call each other—they emit signals that other nodes listen for.

```yaml
example_workflow:
  ValidateInput:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: VALID
        condition: "{{ context.data is defined }}"
      - signal_name: INVALID

  ProcessData:
    node_type: llm
    event_triggers: [VALID]
    prompt: "Process this: {{ context.data }}"
    output_field: result
    event_emissions:
      - signal_name: DONE
```

**That's the entire workflow definition.** No SDK, no decorators, no base classes.

---

## Why SOE

### 1. Infrastructure-Agnostic
SOE defines **protocols**, not implementations. Swap PostgreSQL for DynamoDB. Replace OpenAI with a local LLM. Deploy to Lambda, Kubernetes, or a single Python script. Your workflow YAML stays the same.

### 2. Context-Driven with Jinja
All workflow state flows through **context**—a shared dictionary accessible via Jinja2 templates. This means:
- Conditions like `{{ context.user_validated }}` are readable and debuggable
- LLM prompts can interpolate any context field
- No hidden state—everything is inspectable

### 3. Deterministic + Agentic
Mix hard-coded logic with LLM-driven behavior in the same workflow. Router nodes are pure conditionals. Agent nodes can call tools. Use what you need.

### 4. Portable
Workflows are YAML. Run them locally, in CI, in production. Extract them, version them, share them.

### 5. Self-Evolving
Workflows can modify themselves at runtime. Built-in tools like `inject_workflow`, `inject_node_configuration`, and `add_signal` allow agents to:
- Create new workflows dynamically
- Add or modify nodes in existing workflows
- Update signal routing on the fly

This enables **meta-programming**: an AI system that can extend its own capabilities without human intervention.

---

## Installation

```bash
# With uv (recommended)
uv add soe-ai

# With pip
pip install soe-ai

# From source
git clone https://github.com/pgarcia14180/soe.git
cd soe && uv sync
```

---

## Quick Start

### 1. Provide Your LLM

SOE is LLM-agnostic. You must provide a `call_llm` function that matches this signature:

```python
def call_llm(
    messages: list[dict],           # [{"role": "user", "content": "..."}]
    response_model: type | None,    # Optional Pydantic model for structured output
) -> str | BaseModel:
    """Your LLM integration. Use OpenAI, Anthropic, local models, etc."""
    # Example with OpenAI:
    from openai import OpenAI
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
    )
    return response.choices[0].message.content
```

### 2. Run a Workflow

```python
from soe import orchestrate, create_all_nodes
from soe.local_backends import create_local_backends

# Your workflow (can also be loaded from file or database)
workflow = """
example_workflow:
  Start:
    node_type: router
    event_triggers: [START]
    event_emissions:
      - signal_name: DONE
"""

# Create backends (storage for context, workflows, etc.)
backends = create_local_backends("./data")

# Create all node handlers (pass your call_llm function)
nodes, broadcast = create_all_nodes(backends, call_llm=call_llm)

# Run the workflow
execution_id = orchestrate(
    config=workflow,
    initial_workflow_name="example_workflow",
    initial_signals=["START"],
    initial_context={"user": "alice"},
    backends=backends,
    broadcast_signals_caller=broadcast,
)
# When orchestrate() returns, the workflow is complete
```

**For product managers and less technical users**: The Quick Start above is all you need to run a workflow. The `config` parameter accepts YAML defining your workflow structure. The `initial_context` is where you pass input data (like user IDs, requests, etc.).

---

## Documentation

| Audience | Start Here |
|----------|------------|
| **Builders** (workflow authors) | [Documentation](docs/GUIDE.md) — Step-by-step chapters |
| **Engineers** (infrastructure) | [Infrastructure Guide](docs/guide_10_infrastructure.md) — Backend protocols |
| **Researchers** (advanced patterns) | [Advanced Patterns](docs/advanced_patterns/) — Swarm, hybrid, self-evolving |

---

## Node Types

| Node | Purpose |
|------|---------|
| `router` | Conditional signal emission (no LLM) |
| `llm` | Single LLM call with output |
| `agent` | Multi-turn LLM with tool access |
| `tool` | Execute Python functions |
| `child` | Spawn sub-workflows |

---

## Backend Protocols

Implement these to plug SOE into your infrastructure:

| Protocol | Purpose |
|----------|---------|
| `ContextBackend` | Workflow state storage |
| `WorkflowBackend` | Workflow definitions |
| `ContextSchemaBackend` | Output validation (optional) |
| `IdentityBackend` | LLM system prompts (optional) |
| `ConversationHistoryBackend` | Agent memory (optional) |
| `TelemetryBackend` | Observability (optional) |

**Recommendation**: Use the same database for context, workflows, identities, and context_schema—just separate tables. The backend methods handle table creation.

See [Infrastructure Guide](docs/guide_10_infrastructure.md) for PostgreSQL, DynamoDB, and Lambda examples.

---

## License

MIT
