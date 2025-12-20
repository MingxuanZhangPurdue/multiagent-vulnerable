import litellm
import asyncio
import json
import time
import inspect

from typing import Any, Callable, get_type_hints, Literal
from litellm.types.utils import ModelResponse, ChatCompletionMessageToolCall
from litellm.types.llms.openai import (
    ResponsesAPIResponse,
    ResponseFunctionToolCall
)

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

def transform_tool_format_from_completion_to_responses(
    tools: list[dict[str, Any]] | None
) -> list[dict[str, Any]] | None:
    if tools:
        transformed_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                transformed_tool = {
                    "name": tool["function"]["name"],
                    "type": "function",
                    "description": tool["function"].get("description", ""),
                    "parameters": tool["function"].get("parameters", {}),
                }
                transformed_tools.append(transformed_tool)
            else:
                transformed_tools.append(tool)
        return transformed_tools
    else:
        return tools

def _accepts_task_environment(func: Callable) -> bool:
    """Check if the function's first parameter is typed as TaskEnvironment or subclass."""
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

async def invoke_functions_from_response(
    tool_calls: list[ResponseFunctionToolCall],
    tool_mapping: dict[str, Callable],
    context: TaskEnvironment | None = None
) -> list[dict[str, Any]]:
    """
    Invoke tool functions concurrently, with optional context injection.
    
    If context is provided and a tool's first parameter is typed as TaskEnvironment
    (or subclass), the context will be injected as the first positional argument.
    """
    
    async def _invoke(tool_call: ResponseFunctionToolCall) -> dict[str, Any]:
        # Parse tool call
        tool_name = tool_call.name
        arguments = tool_call.arguments or "{}"
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
            "call_id": tool_call.call_id,
            "type": "function_call_output",
            "output": result,
        }
    
    # Execute all tool calls concurrently
    return await asyncio.gather(*(_invoke(tool_call) for tool_call in tool_calls))


async def invoke_functions_from_completion(
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

    @classmethod
    def support_responses_endpoint(
        cls,
        model: str
    ) -> bool:
        """Check if the model supports the responses endpoint.
        For now, only models starting with "openai/" are supported.
        """
        return model.startswith("openai/")
    
    @classmethod
    async def run(
        cls,
        agent: Agent,
        input: str | list[dict[str, Any]] | dict[str, Any],
        context: TaskEnvironment | None = None,
        session: BaseSession | None = None,
        hooks: list[AttackHook] | None = None,
        max_turns: int = 10,
        endpoint: Literal["completion", "responses"] | None = None
    ):
        
        """
        if endpoint is not specified, we route all openai models to responses endpoint, and all other models to completion endpoint by default.
        """

        if endpoint is None:
            if agent.model.startswith("openai/"):
                endpoint = "responses"
            else:
                endpoint = "completion"
        
        if endpoint == "completion":
            return await cls.run_completion(
                agent=agent,
                input=input,
                context=context,
                session=session,
                hooks=hooks,
                max_turns=max_turns,
            )

        elif endpoint == "responses":
            if not cls.support_responses_endpoint(agent.model):
                raise ValueError(f"Model {agent.model} does not support responses endpoint.")
            return await cls.run_responses(
                agent=agent,
                input=input,
                context=context,
                session=session,
                hooks=hooks,
                max_turns=max_turns,
            )
        
        else:
            raise ValueError(f"Unknown endpoint: {endpoint}, must be 'completion' or 'responses'.")

    @classmethod
    async def run_responses(
        cls,
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

            model_settings = agent.model_settings if agent.model_settings is not None else {}

            input = await session.get_items()

            model_response: ResponsesAPIResponse = await litellm.aresponses(
                model = agent.model,
                instructions=system_prompt,
                input=input,
                tools = transform_tool_format_from_completion_to_responses(agent.tools),
                **model_settings
            )

            tool_calls: list[ResponseFunctionToolCall] = []
            
            for item in model_response.output:
                responses.append(item.to_dict())
                await session.add_items([item.to_dict()])
                if item.type == "function_call":
                    tool_calls.append(item)

            if model_response.usage is not None:
                usage = update_usage(usage, model_response.usage.model_dump())

            if not tool_calls:
                break

            for tool_call in tool_calls:
                all_tool_calls.append({
                    "tool_name": tool_call.name,
                    "tool_arguments": tool_call.arguments,
                    "tool_call_id": tool_call.call_id
                })

            intermediate_messages = await invoke_functions_from_response(
                tool_calls=tool_calls,  
                tool_mapping=agent.tool_mapping,
                context=context,
            )

            await session.add_items(intermediate_messages)

            turn += 1

        final_output = None
        for item in responses[::-1]:
            if item.get("type") == "message":
                final_output = item["content"][0]["text"]
                break

        return RunResult(
            final_output=final_output,
            raw_responses=responses,
            time_duration=time.monotonic() - run_start_time,
            usage=usage,
            input_items=await session.get_copy_of_items(),
            tool_calls=all_tool_calls
        )


    @classmethod
    async def run_completion(
        cls,
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

            model_settings = agent.model_settings if agent.model_settings is not None else {}

            model_response: ModelResponse = await litellm.acompletion(
                model = agent.model,
                messages = [
                    {"role": "system", "content": system_prompt},
                    *await session.get_items(),
                ],
                tools = agent.tools,
                **model_settings
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

            intermediate_messages = await invoke_functions_from_completion(
                tool_calls=tool_calls,  
                tool_mapping=agent.tool_mapping,
                context=context,
            )

            await session.add_items(intermediate_messages)

            turn += 1

        final_output = responses[-1]["choices"][0]["message"]["content"]

        return RunResult(
            final_output=final_output,
            raw_responses=responses,
            time_duration=time.monotonic() - run_start_time,
            usage=usage,
            input_items=await session.get_copy_of_items(),
            tool_calls=all_tool_calls
        )
