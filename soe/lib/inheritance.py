"""
Configuration and context inheritance utilities.

Handles:
- Extracting and saving config sections (workflows, identity, schema) from parsed config
- Inheriting config from existing executions
- Inheriting context from existing executions

Used for workflow initialization and chaining.
"""

import copy
from typing import Dict, Any, Optional

from ..types import Backends


def save_config_sections(
    execution_id: str,
    backends: Backends,
    identities: Optional[Dict[str, str]] = None,
    context_schema: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Save identities and context_schema to their respective backends.

    This is the shared logic for both:
    - Extracting sections from new config
    - Inheriting sections from existing execution

    Args:
        execution_id: Target execution ID
        backends: Backend services
        identities: Identity definitions to save (optional)
        context_schema: Context schema to save (optional)
    """
    if identities and backends.identity:
        backends.identity.save_identities(execution_id, identities)

    if context_schema and backends.context_schema:
        backends.context_schema.save_context_schema(execution_id, context_schema)


def extract_and_save_config_sections(
    parsed_config: Dict[str, Any],
    execution_id: str,
    backends: Backends,
) -> Dict[str, Any]:
    """
    Extract workflows, context_schema, and identities from config.

    If config has 'workflows' key, it's the combined structure:
    - Extract and save context_schema to context_schema backend
    - Extract and save identities to identity backend
    - Return just the workflows portion

    If config doesn't have 'workflows' key, it's the legacy structure
    where the entire config is the workflows registry.

    Args:
        parsed_config: Parsed config dictionary
        execution_id: Execution ID to save sections under
        backends: Backend services

    Returns:
        The workflows registry portion of the config
    """
    if "workflows" in parsed_config:
        workflows = parsed_config["workflows"]

        save_config_sections(
            execution_id=execution_id,
            backends=backends,
            identities=parsed_config.get("identities"),
            context_schema=parsed_config.get("context_schema"),
        )

        return workflows

    # Legacy structure - entire config is workflows
    return parsed_config


def inherit_config(
    source_execution_id: str,
    target_execution_id: str,
    backends: Backends,
) -> Dict[str, Any]:
    """
    Inherit configuration from source execution to target execution.

    Copies:
    - Workflows registry
    - Identities (if available)
    - Context schema (if available)

    Args:
        source_execution_id: Execution ID to inherit from
        target_execution_id: Execution ID to inherit to
        backends: Backend services

    Returns:
        The workflows registry (for validation and use)

    Raises:
        ValueError: If source execution has no workflows registry
    """
    workflows_registry = backends.workflow.get_workflows_registry(source_execution_id)
    if not workflows_registry:
        raise ValueError(
            f"Cannot inherit config from execution '{source_execution_id}': "
            "no workflows registry found"
        )

    # Copy workflows to new execution
    backends.workflow.save_workflows_registry(target_execution_id, workflows_registry)

    # Get source identities and schema
    source_identities = None
    source_schema = None

    if backends.identity:
        source_identities = backends.identity.get_identities(source_execution_id)

    if backends.context_schema:
        source_schema = backends.context_schema.get_context_schema(source_execution_id)

    # Save to target using shared logic
    save_config_sections(
        execution_id=target_execution_id,
        backends=backends,
        identities=source_identities,
        context_schema=source_schema,
    )

    return workflows_registry


def inherit_context(
    source_execution_id: str,
    backends: Backends,
) -> Dict[str, Any]:
    """
    Inherit context from source execution, resetting operational state.

    Copies all context fields except __operational__, which is reset
    for the new execution.

    Args:
        source_execution_id: Execution ID to inherit context from
        backends: Backend services

    Returns:
        Context dictionary ready for new execution (without __operational__)

    Raises:
        ValueError: If source execution has no context
    """
    source_context = backends.context.get_context(source_execution_id)
    if not source_context:
        raise ValueError(
            f"Cannot inherit context from execution '{source_execution_id}': "
            "no context found"
        )

    # Deep copy context, excluding internal fields (will be reset for new execution)
    # __operational__ - execution tracking state
    # __parent__ - parent workflow metadata (not relevant for new execution)
    inherited_context = {
        k: copy.deepcopy(v)
        for k, v in source_context.items()
        if k not in ("__operational__", "__parent__")
    }

    return inherited_context
