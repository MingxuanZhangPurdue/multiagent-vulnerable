from typing import Any

def FunctionCall(function: str, args: dict[str, Any]) -> dict[str, Any]:
    """Create a function call dict with name and tool_arguments."""
    return {
        "tool_name": function,
        "tool_arguments": args,
    }