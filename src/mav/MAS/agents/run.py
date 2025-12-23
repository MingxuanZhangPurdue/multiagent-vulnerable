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
from .tool import FunctionToolResult
from .guardrail import (
    InputGuardrail,
    OutputGuardrail,
    InputGuardrailResult,
    OutputGuardrailResult,
    GuardrailTripwireTriggered
)

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
    """
    transform tools format from completion endpoint to responses endpoint.
    """
    if tools:
        transformed_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                transformed_tool = {
                    "name": tool["function"]["name"],
                    "type": "function",
                    "description": tool["function"]["description"],
                    "parameters": tool["function"]["parameters"],
                }
                transformed_tools.append(transformed_tool)
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

async def invoke_functions_from_responses(
    tool_calls: list[ResponseFunctionToolCall],
    tool_mapping: dict[str, Callable],
    context: TaskEnvironment | None = None
) -> list[dict[str, Any]]:
    """
    Invoke tool functions concurrently from responses endpoint, with optional context injection.
    
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

        output = None
        tool_usage = None
        if isinstance(result, str):
            output = result
        elif isinstance(result, FunctionToolResult):
            output = result.output
            tool_usage = result.usage
        else:
            raise TypeError(
                f"Tool function '{tool_name}' returned unsupported type '{type(result).__name__}'. "
                f"Expected 'str' or 'FunctionCallResult'."
            )
        
        # Return formatted response
        return {
            "call_id": tool_call.call_id,
            "type": "function_call_output",
            "output": output,
            "usage": tool_usage,
        }
    
    # Execute all tool calls concurrently
    return await asyncio.gather(*(_invoke(tool_call) for tool_call in tool_calls))


async def invoke_functions_from_completion(
    tool_calls: list[ChatCompletionMessageToolCall],
    tool_mapping: dict[str, Callable],
    context: TaskEnvironment | None = None
) -> list[dict[str, Any]]:
    """
    Invoke tool functions concurrently from completion endpoint, with optional context injection.
    
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
            
        content = None
        tool_usage = None
        if isinstance(result, str):
            content = result
        elif isinstance(result, FunctionToolResult):
            content = result.output
            tool_usage = result.usage
        else:
            raise TypeError(
                f"Tool function '{tool_name}' returned unsupported type '{type(result).__name__}'. "
                f"Expected 'str' or 'FunctionCallResult'."
            )
        
        # Return formatted response
        return {
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": tool_name,
            "content": content,
            "usage": tool_usage,
        }
    
    # Execute all tool calls concurrently
    return await asyncio.gather(*(_invoke(tool_call) for tool_call in tool_calls))

class Runner:

    @classmethod
    def support_responses_endpoint(
        cls,
        model: str
    ) -> bool:
        """Check if the model supports litellm responses endpoint.
        For now, only models starting with "openai/" are supported.
        """
        return model.startswith("openai/")
    
    @classmethod
    async def _run_input_guardrails(
        cls,
        guardrails: list[InputGuardrail],
        context: TaskEnvironment | None,
        agent: Agent,
        input: str | list[dict[str, Any]] | dict[str, Any],
    ) -> list[InputGuardrailResult]:
        """Run input guardrails sequentially before agent execution."""
        if not guardrails:
            return []
        
        results = []
        for guardrail in guardrails:
            result = await guardrail.run(context, agent, input)
            results.append(result)
            if result.output.tripwire_triggered:
                raise GuardrailTripwireTriggered(result)
        
        return results
    
    @classmethod
    async def _run_output_guardrails(
        cls,
        guardrails: list[OutputGuardrail],
        context: TaskEnvironment | None,
        agent: Agent,
        agent_output: Any,
    ) -> list[OutputGuardrailResult]:
        """Run output guardrails sequentially after agent execution."""
        if not guardrails:
            return []
        
        results = []
        for guardrail in guardrails:
            result = await guardrail.run(context, agent, agent_output)
            results.append(result)
            if result.output.tripwire_triggered:
                raise GuardrailTripwireTriggered(result)
        
        return results
    
    @classmethod
    async def run(
        cls,
        agent: Agent,
        input: str | list[dict[str, Any]] | dict[str, Any],
        context: TaskEnvironment | None = None,
        session: BaseSession | None = None,
        attack_hooks: list[AttackHook] | None = None,
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
                attack_hooks=attack_hooks,
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
                attack_hooks=attack_hooks,
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
        attack_hooks: list[AttackHook] | None = None,
        max_turns: int = 10,
    ) -> RunResult:
        
        # Run input guardrails BEFORE agent execution
        if agent.input_guardrails:
            await cls._run_input_guardrails(
                agent.input_guardrails,
                context,
                agent,
                input
            )
        
        turn = 0

        all_tool_calls: list[dict[str, Any]] = []

        final_output = None

        if session is None:
            # Create a temporary in-memory session for this run if session is not provided
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
                await session.add_items([item.to_dict()])
                if item.type == "function_call":
                    tool_calls.append(item)

            if model_response.usage is not None:
                usage = update_usage(usage, {agent.model: model_response.usage.model_dump()})

            # ReAct loop: break if no tool calls
            if not tool_calls:
                break

            for tool_call in tool_calls:
                all_tool_calls.append({
                    "tool_name": tool_call.name,
                    "tool_arguments": tool_call.arguments,
                    "tool_call_id": tool_call.call_id
                })

            intermediate_messages = await invoke_functions_from_responses(
                tool_calls=tool_calls,  
                tool_mapping=agent.tool_mapping,
                context=context,
            )

            # Update usage from tool invocations for tool calls that called llms internally
            for item in intermediate_messages:
                # if usage is not None add to total usage
                if item.get("usage"):
                    usage = update_usage(usage, item["usage"])
                # Need to remove usage from item before adding to session
                if "usage" in item:
                    item.pop("usage")

            await session.add_items(intermediate_messages)

            turn += 1

        # Extract all message outputs from the last response
        final_output = []
        for item in model_response.output:
            if item.type == "message":
                for content_part in item.content:
                    if content_part.type == "output_text":
                        final_output.append(content_part.text)

        # Join all messages or take the last one
        final_output = "\n".join(final_output) if final_output else ""

        # Run output guardrails AFTER agent execution
        if agent.output_guardrails:
            await cls._run_output_guardrails(
                agent.output_guardrails,
                context,
                agent,
                final_output
            )

        return RunResult(
            final_output=final_output,
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
        attack_hooks: list[AttackHook] | None = None,
        max_turns: int = 10,
    ) -> RunResult:
        
        # Run input guardrails BEFORE agent execution
        if agent.input_guardrails:
            await cls._run_input_guardrails(
                agent.input_guardrails,
                context,
                agent,
                input
            )
        
        turn = 0

        all_tool_calls: list[dict[str, Any]] = []

        final_output = None

        if session is None:
            # Create a temporary in-memory session for this run if session is not provided
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

            await session.add_items([model_response.choices[0].message.to_dict()])

            tool_calls = model_response.choices[0].message.tool_calls

            if model_response.usage is not None:
                usage = update_usage(usage, {agent.model:model_response.usage.to_dict()})

            # ReAct loop: break if no tool calls
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

            # Update usage from tool invocations for tool calls that called llms internally
            for item in intermediate_messages:
                # if usage is not None add to total usage
                if item.get("usage"):
                    usage = update_usage(usage, item["usage"])
                # Need to remove usage from item before adding to session
                if "usage" in item:
                    item.pop("usage")

            await session.add_items(intermediate_messages)

            turn += 1

        final_output = model_response.choices[0].message.content

        # Run output guardrails AFTER agent execution
        if agent.output_guardrails:
            await cls._run_output_guardrails(
                agent.output_guardrails,
                context,
                agent,
                final_output
            )

        return RunResult(
            final_output=final_output,
            time_duration=time.monotonic() - run_start_time,
            usage=usage,
            input_items=await session.get_copy_of_items(),
            tool_calls=all_tool_calls
        )
