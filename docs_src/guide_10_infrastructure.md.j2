# SOE Guide: Chapter 10 - Custom Infrastructure

## Introduction

SOE is **infrastructure agnostic** by design. The core orchestration engine doesn't care *where* your data lives or *how* signals are broadcast—it only requires that you provide implementations that follow the defined protocols.

This chapter covers two distinct infrastructure concerns:

1. **Persistent Infrastructure (Backends)** — Where data is stored
2. **Communication Infrastructure (Callers)** — How signals are broadcast

---

## Part 1: Persistent Infrastructure (Backends)

### What Are Backends?

Backends are the **persistence layer** of SOE. They store:

| Backend | Purpose | Example Use Cases |
|---------|---------|-------------------|
| `context` | Workflow execution state | DynamoDB, Redis, PostgreSQL |
| `workflow` | Workflow definitions | S3, local files, database |
| `telemetry` | Logs and events | Datadog, CloudWatch, Elasticsearch |
| `conversation_history` | LLM chat history | MongoDB, PostgreSQL, text files |
| `schema` | Context validation schemas | Database, config files |

### Built-in Backends

SOE ships with two backend implementations for immediate use:

#### In-Memory Backends
```python
from soe.local_backends import create_in_memory_backends

backends = create_in_memory_backends()
```
- **Use case**: Unit tests, prototyping
- **Pros**: Fast, no setup required
- **Cons**: Data lost on process exit, not distributable

#### Local File Backends
```python
from soe.local_backends import create_local_backends

backends = create_local_backends(
    context_storage_dir="./orchestration_data/contexts",
    workflow_storage_dir="./orchestration_data/workflows",
    telemetry_storage_dir="./orchestration_data/telemetry",  # Optional
    conversation_history_storage_dir="./orchestration_data/conversations",  # Optional
    schema_storage_dir="./orchestration_data/schemas",  # Optional
)
```
- **Use case**: Local development, debugging, simple deployments
- **Pros**: Persistent, human-readable (JSON files)
- **Cons**: Not distributable, no concurrent access

### The Backend Protocols

Each backend type follows a Python `Protocol` (structural typing). Here are the required interfaces:

#### ContextBackend Protocol
```python
class ContextBackend(Protocol):
    def save_context(self, id: str, context: dict) -> None: ...
    def get_context(self, id: str) -> dict: ...
```

#### WorkflowBackend Protocol
```python
class WorkflowBackend(Protocol):
    def save_workflows_registry(self, id: str, workflows: Any) -> None: ...
    def get_workflows_registry(self, id: str) -> Any: ...
    def save_current_workflow_name(self, id: str, name: str) -> None: ...
    def get_current_workflow_name(self, id: str) -> str: ...
```

#### TelemetryBackend Protocol (Optional)
```python
class TelemetryBackend(Protocol):
    def log_event(self, execution_id: str, event_type: str, **event_data) -> None: ...
```

#### ConversationHistoryBackend Protocol (Optional)
```python
class ConversationHistoryBackend(Protocol):
    def get_conversation_history(self, identity: str) -> List[Dict[str, Any]]: ...
    def append_to_conversation_history(self, identity: str, entry: Dict[str, Any]) -> None: ...
    def save_conversation_history(self, identity: str, history: List[Dict[str, Any]]) -> None: ...
    def delete_conversation_history(self, identity: str) -> None: ...
```

#### ContextSchemaBackend Protocol (Optional)
```python
class ContextSchemaBackend(Protocol):
    def save_context_schema(self, execution_id: str, schema: Dict[str, Any]) -> None: ...
    def get_context_schema(self, execution_id: str) -> Optional[Dict[str, Any]]: ...
    def get_field_schema(self, execution_id: str, field_name: str) -> Optional[Dict[str, Any]]: ...
    def delete_context_schema(self, execution_id: str) -> bool: ...
```

**Note**: Context schemas are keyed by `execution_id` (specifically `main_execution_id`), not workflow name. This allows child workflows to access the parent's schema definitions.

#### IdentityBackend Protocol (Optional)
```python
class IdentityBackend(Protocol):
    def save_identities(self, execution_id: str, identities: Dict[str, str]) -> None: ...
    def get_identities(self, execution_id: str) -> Optional[Dict[str, str]]: ...
    def get_identity(self, execution_id: str, identity_name: str) -> Optional[str]: ...
    def delete_identities(self, execution_id: str) -> bool: ...
```

**Note**: Identities are simple mappings of `identity_name` → `system_prompt` (string). Like context schemas, they're keyed by `main_execution_id` for child workflow access.

### Database Recommendations

For production deployments, we recommend using **the same database** for all config-related backends:

| Backend | Recommended Storage | Why |
|---------|---------------------|-----|
| `context` | Same DB, separate table | Simplifies connection management |
| `workflow` | Same DB, separate table | Allows atomic config updates |
| `context_schema` | Same DB, separate table | Related to workflows |
| `identity` | Same DB, separate table | Related to workflows |
| `conversation_history` | Same DB, separate table | Per-execution keying |
| `telemetry` | Can be separate | High volume, different access patterns |

The backend methods handle table creation. Using one database (with separate tables) is simpler to manage than multiple databases.

### Creating Custom Backends

#### Example: PostgreSQL Context Backend

```python
import psycopg2
import json
from typing import Dict, Any

class PostgresContextBackend:
    """PostgreSQL-based context storage"""

    def __init__(self, connection_string: str):
        self.conn = psycopg2.connect(connection_string)
        self._ensure_table()

    def _ensure_table(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS soe_context (
                    execution_id VARCHAR(255) PRIMARY KEY,
                    context JSONB NOT NULL,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
        self.conn.commit()

    def save_context(self, id: str, context: Dict[str, Any]) -> None:
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO soe_context (execution_id, context)
                VALUES (%s, %s)
                ON CONFLICT (execution_id)
                DO UPDATE SET context = %s, updated_at = NOW()
            """, (id, json.dumps(context), json.dumps(context)))
        self.conn.commit()

    def get_context(self, id: str) -> Dict[str, Any]:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT context FROM soe_context WHERE execution_id = %s",
                (id,)
            )
            row = cur.fetchone()
            return row[0] if row else {}

    def cleanup_all(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM soe_context")
        self.conn.commit()
```

#### Example: DynamoDB Context Backend

```python
import boto3
import json
from typing import Dict, Any

class DynamoDBContextBackend:
    """AWS DynamoDB-based context storage"""

    def __init__(self, table_name: str, region: str = "us-east-1"):
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)

    def save_context(self, id: str, context: Dict[str, Any]) -> None:
        self.table.put_item(Item={
            'execution_id': id,
            'context': json.dumps(context)
        })

    def get_context(self, id: str) -> Dict[str, Any]:
        response = self.table.get_item(Key={'execution_id': id})
        if 'Item' in response:
            return json.loads(response['Item']['context'])
        return {}

    def cleanup_all(self) -> None:
        # Scan and delete all items (use with caution in production)
        scan = self.table.scan()
        with self.table.batch_writer() as batch:
            for item in scan['Items']:
                batch.delete_item(Key={'execution_id': item['execution_id']})
```

#### Example: Datadog Telemetry Backend

```python
from datadog import initialize, statsd
from typing import Any

class DatadogTelemetryBackend:
    """Datadog-based telemetry backend"""

    def __init__(self, api_key: str, app_key: str):
        initialize(api_key=api_key, app_key=app_key)

    def log_event(self, execution_id: str, event_type: str, **event_data) -> None:
        # Send as a custom metric
        statsd.event(
            title=f"SOE: {event_type}",
            text=f"Execution: {execution_id}",
            tags=[
                f"execution_id:{execution_id}",
                f"event_type:{event_type}",
                *[f"{k}:{v}" for k, v in event_data.items()]
            ]
        )

    def cleanup_all(self) -> None:
        # Datadog events are immutable; no cleanup needed
        pass
```

### Assembling Custom Backends

Create a `Backends` container with your custom implementations:

```python
from soe.local_backends.factory import LocalBackends

# Mix and match backends based on your infrastructure
backends = LocalBackends(
    context_backend=PostgresContextBackend("postgresql://..."),
    workflow_backend=S3WorkflowBackend("my-bucket"),
    telemetry_backend=DatadogTelemetryBackend(api_key="...", app_key="..."),
    conversation_history_backend=MongoConversationBackend("mongodb://..."),
    schema_backend=None,  # Optional
)
```

---

## Part 2: Communication Infrastructure (Callers)

### What Are Callers?

Callers are the **communication layer** of SOE. The most important is `broadcast_signals_caller`, which controls how signals propagate through the system.

### The Default Pattern (In-Process)

```python
from soe import broadcast_signals

def broadcast_signals_caller(id: str, signals: List[str]) -> None:
    broadcast_signals(id, signals, nodes, backends)
```

This is synchronous and in-process—perfect for testing and simple deployments.

### Distributed Callers

For production systems, you might want signals to trigger external services.

#### Example: AWS Lambda Caller

```python
import boto3
import json

def create_lambda_caller(function_name: str, region: str = "us-east-1"):
    """Create a caller that invokes AWS Lambda for signal broadcasting"""
    lambda_client = boto3.client('lambda', region_name=region)

    def broadcast_signals_caller(id: str, signals: List[str]) -> None:
        payload = {
            'execution_id': id,
            'signals': signals
        }
        lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='Event',  # Async invocation
            Payload=json.dumps(payload)
        )

    return broadcast_signals_caller
```

#### Example: HTTP Webhook Caller

```python
import requests

def create_http_caller(webhook_url: str, auth_token: str = None):
    """Create a caller that sends signals via HTTP POST"""
    headers = {'Content-Type': 'application/json'}
    if auth_token:
        headers['Authorization'] = f'Bearer {auth_token}'

    def broadcast_signals_caller(id: str, signals: List[str]) -> None:
        payload = {
            'execution_id': id,
            'signals': signals
        }
        response = requests.post(webhook_url, json=payload, headers=headers)
        response.raise_for_status()

    return broadcast_signals_caller
```

#### Example: Message Queue Caller (SQS)

```python
import boto3
import json

def create_sqs_caller(queue_url: str, region: str = "us-east-1"):
    """Create a caller that sends signals to an SQS queue"""
    sqs = boto3.client('sqs', region_name=region)

    def broadcast_signals_caller(id: str, signals: List[str]) -> None:
        message = {
            'execution_id': id,
            'signals': signals
        }
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message)
        )

    return broadcast_signals_caller
```

---

## Part 3: The LLM Caller

### SOE Doesn't Provide an LLM

Unlike some frameworks that bundle specific LLM providers, SOE is **LLM agnostic**. You provide a `call_llm` function that wraps your chosen provider.

### The CallLlm Protocol

```python
class CallLlm(Protocol):
    def __call__(self, prompt: str, config: Dict[str, Any]) -> str:
        ...
```

### Example: OpenAI Caller

```python
import openai

def create_openai_caller(api_key: str, default_model: str = "gpt-4o"):
    """Create an LLM caller for OpenAI API"""
    client = openai.OpenAI(api_key=api_key)

    def call_llm(prompt: str, config: dict) -> str:
        model = config.get("model", default_model)
        temperature = config.get("temperature", 1.0)

        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    return call_llm
```

### Example: Test Stub Caller

```python
def create_stub_caller(responses: dict = None):
    """Create a stub caller for testing"""
    responses = responses or {}

    def call_llm(prompt: str, config: dict) -> str:
        for pattern, response in responses.items():
            if pattern in prompt:
                return response
        return '{"response": "stub response"}'

    return call_llm
```

---

## Summary

| Concern | Component | Built-in Options | Custom Examples |
|---------|-----------|------------------|-----------------|
| **Persistence** | Backends | In-Memory, Local Files | PostgreSQL, DynamoDB, MongoDB |
| **Telemetry** | TelemetryBackend | In-Memory, Local Files | Datadog, CloudWatch |
| **Communication** | Callers | In-process | Lambda, HTTP, SQS |
| **LLM** | CallLlm | None (you provide) | OpenAI, Anthropic, Ollama |

The key principle: **SOE defines the protocols, you provide the implementations**.

---

## Next Steps

Now that you've mastered the infrastructure, explore the capabilities built directly into the engine:
- **[Chapter 11: Built-in Tools](guide_11_builtins.md)** — Self-evolution, documentation exploration, and runtime modification
