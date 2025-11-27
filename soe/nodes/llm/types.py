"""
LLM node models and data structures
"""

from pydantic import BaseModel


class LlmNodeInput(BaseModel):
    """Input model for LLM execution."""
    prompt: str
    context: str = ""
    conversation_history: str = ""
