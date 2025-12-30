from __future__ import annotations

import inspect

from dataclasses import dataclass, field
from typing import Callable, cast, Awaitable, Any, Literal

from .tool import convert_to_function_tool, FunctionTool, FunctionToolCallResult
from .session import BaseSession
from .guardrail import (
    InputGuardrail,
    OutputGuardrail
)
from mav.Tasks.base_environment import TaskEnvironment

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

    tools: list[Callable | Awaitable | FunctionTool] | None = None
    """The tools to use through LiteLLM API.
    """

    model_settings: dict[str, Any] | None = None
    """Configures model-specific tuning parameters (e.g. temperature, top_p, thinking, reasoning, please refer to litellm official documentation for different models and endpoints).
    """

    tool_mapping: dict[str, Callable | Awaitable] | None = field(default=None, init=False, repr=False)
    """A mapping from tool names to their corresponding callable or awaitable functions. Will be populated if tools are provided.
    """

    input_guardrails: list[InputGuardrail] = field(default_factory=list)
    """A list of input guardrails to apply to the agent's input during its run.
    """

    output_guardrails: list[OutputGuardrail] = field(default_factory=list)
    """A list of output guardrails to apply to the agent's output during its run.
    """

    def __post_init__(self):

        if not isinstance(self.name, str):
            raise TypeError(f"Agent name must be a string, got {type(self.name).__name__}")

        if self.tools is not None and not isinstance(self.tools, list):
            raise TypeError(f"Agent tools must be a list, got {type(self.tools).__name__}")
        
        if self.tools is not None:
            if not isinstance(self.tools, list):
                raise TypeError(f"Agent tools must be a list of callable functions, awaitable functions, or FunctionTool instances, got {type(self.tools).__name__}")
            if not all(
                callable(tool) or isinstance(tool, FunctionTool) for tool in self.tools
            ):
                raise TypeError("All tools must be callable or awaitable functions.")
            
            converted_tools = []
            tool_mapping = {}
            for tool in self.tools:
                if isinstance(tool, FunctionTool):
                    converted_tools.append(
                        {
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description,
                                "parameters": tool.params_json_schema,
                            },
                        }
                    )
                    tool_mapping[tool.name] = tool.on_invoke_tool
                else:
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
        
    def as_tool(
        self,
        tool_name: str | None,
        tool_description: str | None,
        max_turns: int | None = None,
        endpoint: Literal["responses", "completion"] | None = None,
        session: BaseSession | None = None,
    ) -> FunctionTool:
        """
        An convenience method to transform this agent into a tool that accepts TaskEnvironment as context, callable by other agents.
        Note that
        Args:
            tool_name: The name of the tool. If not provided, the agent's name will be used.
            tool_description: The description of the tool, which should indicate what it does and
                when to use it.
        """

        async def run_agent(context: TaskEnvironment, input: str) -> FunctionToolCallResult:
            from mav.MAS.agents import Runner, RunResult

            resolved_max_turns = max_turns if max_turns is not None else 10

            output: RunResult = await Runner.run(
                agent=self,
                input=input,
                context=context,
                max_turns=resolved_max_turns,
                session=session,
                endpoint=endpoint,
            )

            return FunctionToolCallResult(
                output=output.final_output if output.final_output is not None else "",
                usage=output.usage,
                appendix=None,
            )
        
        return FunctionTool(
            name=tool_name if tool_name is not None else self.name,
            description=tool_description or "",
            params_json_schema={
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "The input to the agent.",
                    },
                },
                "required": ["input"],
            },
            on_invoke_tool=run_agent,
        )