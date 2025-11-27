
# SOE Guide: Chapter 6 - Context Schema

## Introduction to Context Schema

**Context Schema** provides optional type validation for context fields. When an LLM node writes to a context field, the schema ensures the output matches the expected type (string, integer, object, etc.).

> **Note**: This was previously called just "Schema". We renamed it to "Context Schema" to distinguish it from the Identity Schema (see [Chapter 7](guide_07_identity.md)).

### Why Use Context Schema?

- **Type Safety**: Catch malformed LLM output before it breaks downstream nodes.
- **Tool Integration**: Ensure LLM output has the correct structure for tools.
- **Documentation**: Schema definitions serve as documentation for your workflow's data model.
- **Removes Prompt Boilerplate**: You don't need to specify output format in every prompt—the schema handles it.

## Defining a Schema

Schemas are defined per-workflow, mapping field names to their types:

```python
schemas = {
    "example_workflow": {
        "summary": {
            "type": "string",
            "description": "A one-sentence summary of the input text"
        }
    }
}
```

### Available Types

| Type | Python Type | Description |
|------|-------------|-------------|
| `string` | `str` | Text values |
| `integer` | `int` | Whole numbers |
| `number` | `float` | Decimal numbers |
| `boolean` | `bool` | True/False |
| `object` | `dict` | JSON objects |
| `list` | `list` | Arrays |
| `dict` | `dict` | Alias for object |

## Your First Schema

Let's validate that an LLM returns a proper string summary.

### The Workflow

```yaml
example_workflow:
  SummarizeLLM:
    node_type: llm
    event_triggers: [START]
    prompt: "Summarize the following text in one sentence: &#123;&#123; context.input_text &#125;&#125;"
    output_field: summary
    event_emissions:
      - signal_name: SUMMARY_COMPLETE
```

### The Schema Definition

```python
SCHEMA_STRING_DEFINITION = {
    "example_workflow": {
        "summary": {
            "type": "string",
            "description": "A one-sentence summary of the input text"
        }
    }
}
```

### How It Works

1.  The LLM node writes to `output_field: summary`.
2.  Schema backend checks if a schema exists for `example_workflow.summary`.
3.  If found, validates that the output is a string.
4.  Valid output → saved to context → `SUMMARY_COMPLETE` emitted.

## Integer Schema

For numeric outputs like counts or scores:

### The Workflow

```yaml
example_workflow:
  CounterLLM:
    node_type: llm
    event_triggers: [START]
    prompt: "Count the number of words in this text: &#123;&#123; context.input_text &#125;&#125;. Return only the count."
    output_field: word_count
    event_emissions:
      - signal_name: COUNT_COMPLETE
```

### The Schema

```python
SCHEMA_INTEGER_DEFINITION = {
    "example_workflow": {
        "word_count": {
            "type": "integer",
            "description": "The number of words in the input text"
        }
    }
}
```

The LLM must return `{"word_count": 42}` (an integer), not `{"word_count": "forty-two"}`.

## Object Schema

For structured data extraction:

### The Workflow

```yaml
example_workflow:
  ExtractorLLM:
    node_type: llm
    event_triggers: [START]
    prompt: "Extract the person's name and age from: &#123;&#123; context.input_text &#125;&#125;. Return as JSON with 'name' and 'age' fields."
    output_field: person_data
    event_emissions:
      - signal_name: EXTRACTION_COMPLETE
```

### The Schema

```python
SCHEMA_OBJECT_DEFINITION = {
    "example_workflow": {
        "person_data": {
            "type": "object",
            "description": "Extracted person data with name and age"
        }
    }
}
```

Object schemas accept any valid JSON object structure.

## Schema with Tool Integration

Schema shines when LLM output feeds into tool parameters. This ensures the LLM returns data in the exact format your tool expects.

### The Workflow

```yaml
example_workflow:
  ParameterExtractor:
    node_type: llm
    event_triggers: [START]
    prompt: "Extract the operation and numbers from: &#123;&#123; context.user_request &#125;&#125;. Return JSON with 'operation' (add/multiply) and 'numbers' (list of integers)."
    output_field: params
    event_emissions:
      - signal_name: PARAMS_EXTRACTED

  Calculator:
    node_type: tool
    event_triggers: [PARAMS_EXTRACTED]
    tool_name: calculate
    context_parameter_field: params
    output_field: result
    event_emissions:
      - signal_name: CALCULATED
```

### The Schema

```python
SCHEMA_TOOL_INTEGRATION_DEFINITION = {
    "example_workflow": {
        "params": {
            "type": "object",
            "description": "Extracted parameters with operation and numbers"
        },
        "result": {
            "type": "object",
            "description": "Calculation result"
        }
    }
}
```

### Data Flow

1.  `ParameterExtractor` LLM extracts `{"operation": "add", "numbers": [10, 20, 30]}`.
2.  Schema validates this is an object (dict).
3.  `Calculator` tool receives the validated params.
4.  Tool returns result, also validated against schema.

## Multiple Fields

A single workflow can have schemas for multiple fields:

### The Workflow

```yaml
example_workflow:
  AnalyzerLLM:
    node_type: llm
    event_triggers: [START]
    prompt: "Analyze this text: &#123;&#123; context.input_text &#125;&#125;. Extract the topic and key points."
    output_field: topic
    event_emissions:
      - signal_name: TOPIC_EXTRACTED

  SummarizerLLM:
    node_type: llm
    event_triggers: [TOPIC_EXTRACTED]
    prompt: "Given the topic '&#123;&#123; context.topic &#125;&#125;', provide a brief summary of: &#123;&#123; context.input_text &#125;&#125;"
    output_field: summary
    event_emissions:
      - signal_name: ANALYSIS_COMPLETE
```

### The Schema

```python
SCHEMA_MULTI_FIELD_DEFINITION = {
    "example_workflow": {
        "topic": {
            "type": "string",
            "description": "The main topic of the text"
        },
        "summary": {
            "type": "string",
            "description": "A brief summary based on the topic"
        }
    }
}
```

Each field is validated independently when its LLM node completes.

## Schema is Optional

Schemas are completely optional. Workflows work fine without them:

### The Workflow

```yaml
example_workflow:
  FreeLLM:
    node_type: llm
    event_triggers: [START]
    prompt: "Do whatever you want with: &#123;&#123; context.input_text &#125;&#125;"
    output_field: output
    event_emissions:
      - signal_name: DONE
```

Without schema, LLM output is saved as-is without validation. This is fine for:
- Prototyping
- Free-form text generation
- When you trust the LLM output format

## Defining Schemas in Config (Recommended)

The simplest approach is including `context_schema` directly in your config YAML:

```yaml
# Complete config with workflows and context_schema
workflows:
  example_workflow:
    Summarizer:
      node_type: llm
      event_triggers: [START]
      prompt: "Summarize: {{ context.input }}"
      output_field: summary
      event_emissions:
        - signal_name: DONE

context_schema:
  summary:
    type: string
    description: A one-sentence summary
  result:
    type: object
    description: The workflow result
```

Then pass the entire config to orchestrate:

```python
from soe import orchestrate

execution_id = orchestrate(
    config=CONFIG_YAML,  # The YAML string above
    initial_workflow_name="example_workflow",
    initial_signals=["START"],
    initial_context={"input": "test"},
    backends=backends,
    broadcast_signals_caller=broadcast_signals_caller,
)
```

When `context_schema` is included in config:
1. It's automatically extracted and saved to the `ContextSchemaBackend`
2. It's keyed by `execution_id` (specifically `main_execution_id`)
3. Child workflows can access parent's schema through the same `main_execution_id`

### Backend Requirement

For context schema to work, you need a `ContextSchemaBackend`. The local backends include one:

```python
from soe.local_backends import create_local_backends

backends = create_local_backends(
    context_storage_dir="./data/contexts",
    workflow_storage_dir="./data/workflows",
    schema_storage_dir="./data/schemas",  # Context schema storage
)
```

**Recommendation**: Use the same database for workflows, context, identities, and context_schema. The backend methods create separate tables, not separate databases. This simplifies infrastructure management.

## Saving Schemas Programmatically

You can also save schemas via the backend directly. Note that schemas are keyed by `execution_id`, not workflow name:

```python
from soe import orchestrate
from soe.local_backends import create_local_backends

backends = create_local_backends(...)

# Run orchestrate first to get the execution_id
execution_id = orchestrate(
    config=MY_WORKFLOW,
    initial_workflow_name="my_workflow",
    initial_signals=["START"],
    initial_context={"input": "test"},
    backends=backends,
    broadcast_signals_caller=broadcast_signals_caller,
)

# Retrieve schema (keyed by execution_id)
schema = backends.context_schema.get_context_schema(execution_id)

# Get schema for specific field
field_schema = backends.context_schema.get_field_schema(execution_id, "result")
```

**Important**: The preferred approach is defining `context_schema` in your config, which automatically saves it before orchestration begins.

## Key Points

- **Optional but powerful**: Use schemas when type safety matters.
- **Define in config**: Use `context_schema` section in your config for automatic setup.
- **Keyed by execution_id**: Schemas are stored by `main_execution_id`, enabling child workflow access.
- **Per-field types**: Each context field can have its own type.
- **LLM validation**: Ensures LLM output matches expected structure.
- **Tool integration**: Critical when LLM output feeds tool parameters.

## Next Steps

Now that you understand how to validate LLM output structure, let's explore [Identity](guide_07_identity.md) for persisting conversation history across LLM calls →
