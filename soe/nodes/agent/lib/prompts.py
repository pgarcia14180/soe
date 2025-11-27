"""
Agent node prompt building utilities

Provides state-specific instructions for the agent's router stage.
"""


def get_state_instructions(execution_state: str) -> str:
    """
    Get state-specific instructions for the router stage.

    The router decides between 'call_tool' and 'finish' actions.
    Instructions vary based on what happened in previous iterations.
    """

    base_decision = "Decide the next action: 'call_tool' to use a tool, or 'finish' if task is complete."

    if execution_state == "initial":
        return f"""{base_decision}

INITIAL EXECUTION:
1. Analyze the task and available context
2. Determine if you need additional information from tools
3. If tools are needed, choose 'call_tool' and specify which tool
4. If you have enough information to complete the task, choose 'finish'

IMPORTANT: Only call tools that are NECESSARY. Be selective."""

    elif execution_state == "tool_response":
        return f"""{base_decision}

TOOL RESPONSE RECEIVED:
Your previous tool call was successful. Review the results in conversation history.

NEXT STEPS:
1. Analyze if the tool response provides what you need
2. If more information is needed, call another tool
3. If task can now be completed, choose 'finish'

Do NOT re-call tools that already succeeded."""

    elif execution_state == "tool_error":
        return f"""{base_decision}

TOOL ERROR OCCURRED:
Your previous tool call failed. Review the error in conversation history.

RECOVERY:
1. Understand what went wrong
2. Fix parameters and retry the failed tool, OR
3. Try a different approach with another tool
4. If task can be completed despite the error, choose 'finish'"""

    elif execution_state == "retry":
        return f"""{base_decision}

RETRY NEEDED:
A system error occurred (e.g., invalid tool name). Review the error.

RECOVERY:
1. Check that tool names match available tools exactly
2. Use a valid tool name and try again
3. If no tools are needed, choose 'finish'"""

    return base_decision
