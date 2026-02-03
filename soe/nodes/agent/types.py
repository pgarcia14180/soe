"""
Agent node models and data structures
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    """Request sent to agent - includes everything needed to build a complete prompt"""

    agent_id: str
    prompt: str
    agent_config: Dict[str, Any]
    tool_responses: Dict[str, Any] = {}


class AgentResponse(BaseModel):
    """Validated agent response with mutually exclusive types:
    - Tool response: Only tool_calls + minimal context
    - Signal response: Only emitted_signals + context (THE END)
    - Clarification response: Only needs_clarification + message
    """

    output: Any = None

    tool_calls: Dict[str, Any] = {}
    emitted_signals: List[str] = []
    needs_clarification: bool = False
    clarification_message: str = ""


class RouterInput(BaseModel):
    """Input model for the Router stage prompt."""
    instructions: str = Field(description="State-specific instructions for the router")
    task_description: str
    context: str
    available_tools: str
    conversation_history: str = ""


class RouterResponse(BaseModel):
    """Output model for the Router stage."""
    action: Literal["call_tool", "finish"]
    tool_name: Optional[str] = Field(None, description="Name of the tool to call. Required if action is 'call_tool'.")


class ParameterInput(BaseModel):
    """Input for Parameter stage prompt."""
    task_description: str
    context: str
    tool_name: str
    conversation_history: str = ""


class ResponseStageInput(BaseModel):
    """Input model for the Response stage prompt."""
    task_description: str
    context: str
    conversation_history: str = ""


class FinalResponse(BaseModel):
    """Standardized output from the Response stage."""
    output: Any
    selected_signals: List[str] = []
