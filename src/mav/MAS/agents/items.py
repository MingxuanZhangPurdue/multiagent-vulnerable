from typing import Any
from dataclasses import dataclass
@dataclass
class RunResult:

    final_output: Any
    """The final output produced by the agent after completing its run."""

    raw_responses: list[dict[str, Any]]
    """A list of raw responses from the model for each turn taken by the agent."""

    time_duration: float
    """The total time duration taken for the agent to complete its run."""

    usage: dict[str, Any]
    """A dictionary containing usage statistics, such as token counts and costs."""

    input_items: list[dict[str, Any]]
    """The list of input items provided to its underlying model during its run."""

    tool_calls: list[dict[str, Any]] = None
    """A list of tool calls made by the agent during its run."""