import litellm
import json
import time

from typing import Any, Callable
from litellm.types.utils import ModelResponse, ChatCompletionMessageToolCall

from .agent import Agent
from .session import Session
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

async def invoke_functions_from_response(
    tool_calls: list[ChatCompletionMessageToolCall],
    tool_mapping: dict[str, Callable]
) -> list[dict[str, Any]]:
    intermediate_messages = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        tool_arguments = json.loads(tool_call.function.arguments)
        tool_call_output = tool_mapping[tool_name](**tool_arguments)
        intermediate_messages.append(
            {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": tool_name,
                "content": tool_call_output,
            }
        )
    return intermediate_messages

class Runner:

    @staticmethod
    async def run(
        agent: Agent,
        input: str | list[dict[str, Any]],
        context: TaskEnvironment | None = None,
        session: Session | None = None,
        hooks: list[AttackHook] | None = None,
        max_turns: int = 20,
    ) -> RunResult:
        
        turn = 0

        responses: list[dict[str, Any]] = []

        final_output = None

        input_items: list[dict[str, Any]] = []

        run_start_time = time.monotonic()

        usage = {}

        if isinstance(input, str):
            input_items = [{"role": "user", "content": input}]
        elif isinstance(input, list):
            input_items.extend(input)
        else:
            raise TypeError(f"Input must be a string or a list, but got {type(input)}")
        
        while turn < max_turns:

            system_prompt = await agent.get_system_prompt(run_context=context)

            #print(input_items)

            model_response: ModelResponse = await litellm.acompletion(
                model = agent.model,
                messages = [
                    {"role": "system", "content": system_prompt},
                    *input_items,
                ],
                tools = agent.tools,
                **agent.model_settings
            )

            responses.append(model_response.to_dict())

            input_items.append(model_response.choices[0].message.to_dict())

            tool_calls = model_response.choices[0].message.tool_calls

            if model_response.usage is not None:
                usage = update_usage(usage, model_response.usage.to_dict())

            if not tool_calls:
                break

            #print (tool_calls)

            intermediate_messages = await invoke_functions_from_response(
                tool_calls=tool_calls,  
                tool_mapping=agent.tool_mapping
            )

            #print (intermediate_messages)

            input_items.extend(intermediate_messages)

        final_output = responses[-1]["choices"][0]["message"]["content"]

        return RunResult(
            final_output=final_output,
            raw_responses=responses,
            time_duration=time.monotonic() - run_start_time,
            usage=usage,
            input_items=input_items,
        )
