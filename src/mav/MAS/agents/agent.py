from __future__ import annotations

import inspect

from dataclasses import dataclass
from typing import Callable, cast, Awaitable, Any

from .tool import convert_to_function_tool

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

    tools: list[Callable | Awaitable] | None = None
    """The tools to use through LiteLLM API.
    """

    model_settings: dict[str, Any] | None = None
    """Configures model-specific tuning parameters (e.g. temperature, top_p).
    """

    tool_mapping: dict[str, Callable | Awaitable] | None = None

    def __post_init__(self):

        if not isinstance(self.name, str):
            raise TypeError(f"Agent name must be a string, got {type(self.name).__name__}")

        if self.tools is not None and not isinstance(self.tools, list):
            raise TypeError(f"Agent tools must be a list, got {type(self.tools).__name__}")
        
        if self.tools is not None:
            if not isinstance(self.tools, list):
                raise TypeError(f"Agent tools must be a list of callable or awaitable functions, got {type(self.tools).__name__}")
            if not all(
                callable(tool) or inspect.isawaitable(tool) for tool in self.tools
            ):
                raise TypeError("All tools must be callable or awaitable functions.")
            
            converted_tools = []
            tool_mapping = {}
            for tool in self.tools:
                function_tool = convert_to_function_tool(tool)
                converted_tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": function_tool.name,
                            "description": function_tool.description,
                            "parameters": function_tool.params_json_schema,
                        },
                    }
                )
                tool_mapping[function_tool.name] = function_tool.on_invoke_tool

            self.tools = converted_tools
            self.tool_mapping = tool_mapping

        if (
            self.instructions is not None
            and not isinstance(self.instructions, str)
            and not callable(self.instructions)
        ):
            raise TypeError(
                f"Agent instructions must be a string, callable, or None, "
                f"got {type(self.instructions).__name__}"
            )
        
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
        