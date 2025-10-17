from __future__ import annotations
import inspect
from collections.abc import Awaitable
from dataclasses import dataclass
from typing import cast, Any, Callable

@dataclass
class Agent(): 

    name: str
    """The name of the agent.
    """

    instructions: str | Callable | None 
    """Instructions for the agent.
    """

    model: str
    """The model to use through LiteLLM API.
    """

    tools: list[dict[str, Any]]
    """The tools to use through LiteLLM API.
    """

    def __post_init__(self):

        if not isinstance(self.name, str):
            raise TypeError(f"Agent name must be a string, got {type(self.name).__name__}")

        if not isinstance(self.tools, list):
            raise TypeError(f"Agent tools must be a list, got {type(self.tools).__name__}")

        if (
            self.instructions is not None
            and not isinstance(self.instructions, str)
            and not callable(self.instructions)
        ):
            raise TypeError(
                f"Agent instructions must be a string, callable, or None, "
                f"got {type(self.instructions).__name__}"
            )