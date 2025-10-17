import litellm
import json

from typing import Any, Callable
from litellm.types.utils import ModelResponse

from .agent import Agent
from .session import Session

from src.mav.Tasks.base_environment import TaskEnvironment
from src.mav.MAS.attack_hook import AttackHook

async def invoke_functions_from_response(
    tool_calls: list[dict[str, Any]],
    tool_mapping: dict[str, Callable]
) -> list[dict[str, Any]]:
    intermediate_messages = []
    for tool_call in tool_calls:
        tool_name = tool_call["function"]["name"]
        tool_arguments = json.loads(tool_call["function"]["arguments"])
        tool_call_id = tool_call["id"]
        tool_call_output = tool_mapping[tool_name](**tool_arguments)
        intermediate_messages.append(
            {
                "tool_call_id": tool_call_id,
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
        max_turns: int = 20,
        hooks: list[AttackHook] | None = None,
    ):
        turn = 0

        responses: list[dict[str, Any]] = []

        final_output = None

        time_duration = 0

        while turn < max_turns:

            system_prompt = await agent.get_system_prompt(run_context=context)

            model_response: ModelResponse = await litellm.acompletion(
                model = agent.model,
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": input},
                ],
                tools = agent.tools,
                **agent.model_settings
            )

            responses.append(model_response.to_dict())

            tool_calls = model_response.choices[0].message.tool_calls

            if not tool_calls:
                break

            intermediate_messages = await invoke_functions_from_response(
                tool_calls=tool_calls,  
                tool_mapping=agent.tool_mapping
            )

        final_output = responses[-1]["choices"][0]["message"]["content"]

        return final_output
