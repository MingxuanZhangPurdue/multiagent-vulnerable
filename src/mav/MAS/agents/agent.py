from __future__ import annotations

import inspect

from dataclasses import dataclass
from typing import Callable, cast, Awaitable, Any


from src.mav.MAS.agents.tool import FunctionTool


@dataclass
class Agent(): 

    name: str
    """The name of the agent.
    """

    model: str
    """The model to use through LiteLLM API.
    """

    instructions: str | Callable | None = None
    """Instructions for the agent.
    """

    tools: list[FunctionTool] | None = None
    """The tools to use through LiteLLM API.
    """

    model_settings: dict[str, Any] | None = None
    """Configures model-specific tuning parameters (e.g. temperature, top_p).
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
        
        if self.tools is not None:
            self.tool_mapping = {tool.name: tool.on_invoke_tool for tool in self.tools}
        
    async def get_system_prompt(self, run_context) -> str | None:
        if isinstance(self.instructions, str):
            return self.instructions
        elif callable(self.instructions):
            # Inspect the signature of the instructions function
            sig = inspect.signature(self.instructions)
            params = list(sig.parameters.values())

            # Enforce exactly 2 parameters
            if len(params) != 2:
                raise TypeError(
                    f"'instructions' callable must accept exactly 2 arguments (context, agent), "
                    f"but got {len(params)}: {[p.name for p in params]}"
                )

            # Call the instructions function properly
            if inspect.iscoroutinefunction(self.instructions):
                return await cast(Awaitable[str], self.instructions(run_context, self))
            else:
                return cast(str, self.instructions(run_context, self))

        elif self.instructions is not None:
            raise TypeError(
                f"Agent instructions must be a string, callable, or None, "
                f"got {type(self.instructions).__name__}"
            )

        return None
        