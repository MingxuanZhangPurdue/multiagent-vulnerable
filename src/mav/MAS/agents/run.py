import litellm
import asyncio
import json
import time
import inspect

from typing import Any, Callable, get_type_hints
from litellm.types.utils import ModelResponse, ChatCompletionMessageToolCall

from .agent import Agent
from .session import BaseSession, InMemorySession
from .items import RunResult

from mav.Tasks.base_environment import TaskEnvironment
from mav.MAS.attack_hook import AttackHook

def update_usage(
    total_usage: dict[str, Any],
    new_usage: dict[str, Any]
) -> dict[str, Any]:
    for key, value in new_usage.items():
        if key in total_usage:
            if isinstance(value, dict) and isinstance(total_usage.get(key), dict):
                update_usage(total_usage[key], value)
            elif isinstance(value, (int, float)) and isinstance(total_usage.get(key), (int, float)):
                total_usage[key] += value
            else:
                # For non-numeric, non-dict types or type mismatches, overwrite.
                total_usage[key] = value
        else:
            total_usage[key] = value
    return total_usage

def _accepts_task_environment(func: Callable) -> bool:
    """Check if the function's first parameter is typed as TaskEnvironment or subclass."""
    try:
        # Get function signature and type hints
        sig = inspect.signature(func)
        params = list(sig.parameters.values())
        
        # Check if there's at least one parameter
        if not params:
            return False
        
        first_param = params[0]
        
        # Only check positional parameters
        if first_param.kind not in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            return False
        
        # Get type hints
        type_hints = get_type_hints(func)
        param_type = type_hints.get(first_param.name)
        
        # Check if the type is TaskEnvironment or a subclass
        if param_type and inspect.isclass(param_type):
            return issubclass(param_type, TaskEnvironment)
        
        return False
    except Exception:
        return False

async def invoke_functions_from_response(
    tool_calls: list[ChatCompletionMessageToolCall],
    tool_mapping: dict[str, Callable],
    context: TaskEnvironment | None = None
) -> list[dict[str, Any]]:
    """
    Invoke tool functions concurrently, with optional context injection.
    
    If context is provided and a tool's first parameter is typed as TaskEnvironment
    (or subclass), the context will be injected as the first positional argument.
    """
    
    async def _invoke(tool_call: ChatCompletionMessageToolCall) -> dict[str, Any]:
        # Parse tool call
        tool_name = tool_call.function.name
        arguments = tool_call.function.arguments or "{}"
        tool_arguments = json.loads(arguments)
        tool = tool_mapping[tool_name]
        
        # Determine if we should inject context
        inject_context = context is not None and _accepts_task_environment(tool)
        positional_args = (context,) if inject_context else ()
        
        # Execute the tool (async or sync)
        if inspect.iscoroutinefunction(tool):
            result = await tool(*positional_args, **tool_arguments)
        else:
            result = await asyncio.to_thread(tool, *positional_args, **tool_arguments)
        
        # Return formatted response
        return {
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": tool_name,
            "content": result,
        }
    
    # Execute all tool calls concurrently
    return await asyncio.gather(*(_invoke(tool_call) for tool_call in tool_calls))


class Runner:

    @staticmethod
    async def run(
        agent: Agent,
        input: str | list[dict[str, Any]] | dict[str, Any],
        context: TaskEnvironment | None = None,
        session: BaseSession | None = None,
        hooks: list[AttackHook] | None = None,
        max_turns: int = 10,
    ) -> RunResult:
        
        turn = 0

        responses: list[dict[str, Any]] = []

        all_tool_calls: list[dict[str, Any]] = []

        final_output = None

        if session is None:
            # Create a temporary in-memory session for this run if none is provided
            session = InMemorySession(session_id="runner_temp_session")

        run_start_time = time.monotonic()

        usage = {}

        if isinstance(input, str):
            await session.add_items([{"role": "user", "content": input}])
        elif isinstance(input, list):
            await session.add_items(input)
        elif isinstance(input, dict):
            await session.add_items([input])
        else:
            raise TypeError(f"Input must be a string, a dict, or a list, but got {type(input)}")
        
        while turn < max_turns:

            system_prompt = await agent.get_system_prompt(run_context=context)

            model_response: ModelResponse = await litellm.acompletion(
                model = agent.model,
                messages = [
                    {"role": "system", "content": system_prompt},
                    *await session.get_items(),
                ],
                tools = agent.tools,
                **agent.model_settings
            )

            responses.append(model_response.to_dict())

            await session.add_items([model_response.choices[0].message.to_dict()])

            tool_calls = model_response.choices[0].message.tool_calls

            if model_response.usage is not None:
                usage = update_usage(usage, model_response.usage.to_dict())

            if not tool_calls:
                break

            for tool_call in tool_calls:
                all_tool_calls.append({
                    "tool_name": tool_call.function.name,
                    "tool_arguments": tool_call.function.arguments,
                    "tool_call_id": tool_call.id,
                })

            intermediate_messages = await invoke_functions_from_response(
                tool_calls=tool_calls,  
                tool_mapping=agent.tool_mapping,
                context=context,
            )

            await session.add_items(intermediate_messages)

        final_output = responses[-1]["choices"][0]["message"]["content"]

        return RunResult(
            final_output=final_output,
            raw_responses=responses,
            time_duration=time.monotonic() - run_start_time,
            usage=usage,
            input_items=await session.get_copy_of_items(),
            tool_calls=all_tool_calls
        )
