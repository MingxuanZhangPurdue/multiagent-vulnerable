from typing import Any
from dataclasses import dataclass
@dataclass
class RunResult:

    final_output: str | Any
    """The final output produced by the agent after completing its run."""

    time_duration: float
    """The total time duration taken for the agent to complete its run."""

    usage: dict[str, dict[str, Any]]
    """A dictionary containing usage statistics during the agent's run, each key respresenting a different model used and the value being another dictionary with usage details."""

    input_items: list[dict[str, Any]]
    """The list of input items provided to its underlying model during its run."""

    tool_calls: list[dict[str, Any]] = None
    """A list of all tool calls made by the agent during its run. Extracted from input_items for easier access."""