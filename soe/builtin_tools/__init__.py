"""
Built-in tools registry
"""

from .soe_inject_workflow import create_soe_inject_workflow_tool
from .soe_inject_node import create_soe_inject_node_tool
from .soe_get_workflows import create_soe_get_workflows_tool
from .soe_get_available_tools import create_soe_get_available_tools_tool
from .soe_explore_docs import create_soe_explore_docs_tool
from .soe_remove_workflow import create_soe_remove_workflow_tool
from .soe_remove_node import create_soe_remove_node_tool
from .soe_get_context import create_soe_get_context_tool
from .soe_update_context import create_soe_update_context_tool
from .soe_copy_context import create_soe_copy_context_tool
from .soe_list_contexts import create_soe_list_contexts_tool
from .soe_add_signal import create_soe_add_signal_tool
from .soe_call_tool import create_soe_call_tool_tool
from .soe_get_identities import create_soe_get_identities_tool
from .soe_inject_identity import create_soe_inject_identity_tool
from .soe_remove_identity import create_soe_remove_identity_tool
from .soe_get_context_schema import create_soe_get_context_schema_tool
from .soe_inject_context_schema_field import create_soe_inject_context_schema_field_tool
from .soe_remove_context_schema_field import create_soe_remove_context_schema_field_tool

# Registry of all available built-in tools
BUILTIN_TOOLS = {
    "soe_inject_workflow": create_soe_inject_workflow_tool,
    "soe_inject_node": create_soe_inject_node_tool,
    "soe_get_workflows": create_soe_get_workflows_tool,
    "soe_get_available_tools": create_soe_get_available_tools_tool,
    "soe_explore_docs": create_soe_explore_docs_tool,
    "soe_remove_workflow": create_soe_remove_workflow_tool,
    "soe_remove_node": create_soe_remove_node_tool,
    "soe_get_context": create_soe_get_context_tool,
    "soe_update_context": create_soe_update_context_tool,
    "soe_copy_context": create_soe_copy_context_tool,
    "soe_list_contexts": create_soe_list_contexts_tool,
    "soe_add_signal": create_soe_add_signal_tool,
    "soe_call_tool": create_soe_call_tool_tool,
    "soe_get_identities": create_soe_get_identities_tool,
    "soe_inject_identity": create_soe_inject_identity_tool,
    "soe_remove_identity": create_soe_remove_identity_tool,
    "soe_get_context_schema": create_soe_get_context_schema_tool,
    "soe_inject_context_schema_field": create_soe_inject_context_schema_field_tool,
    "soe_remove_context_schema_field": create_soe_remove_context_schema_field_tool,
}


def get_builtin_tool_factory(tool_name: str):
    """Get factory function for built-in tool"""
    return BUILTIN_TOOLS.get(tool_name)
