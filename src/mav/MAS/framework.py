import json
import inspect
from agents import (
    Agent,
    Runner, 
    SQLiteSession,
    TResponseInputItem,
    ModelResponse
)

from typing import Any, Literal, get_args
from pydantic import BaseModel

from mav.MAS.terminations import BaseTermination
from mav.items import FunctionCall
from mav.Tasks.base_environment import TaskEnvironment
from mav.MAS.terminations import BaseTermination
from mav.MAS.attack_hook import execute_attacks, AttackHook
from mav.Attacks.attack import AttackComponents

class MultiAgentSystem:

    RunnerType = Literal["handoffs", "sequential", "planner_executor"]

    def __init__(
        self,
        agents: Agent | list[Agent],
        runner: RunnerType,
        termination_condition: list[BaseTermination] | None = None,
        max_iterations: int = 10,
        enable_executor_memory: bool = True,
        shared_memory: bool = False,
        use_memory: bool = True,
    ):
        if runner == "handoffs" and not isinstance(agents, Agent):
            raise ValueError("When using 'handoffs' runner, a single agent must be passed!")
        elif runner == "sequential":
            if not isinstance(agents, list) or not all(isinstance(agent, Agent) for agent in agents):
                raise ValueError("When using 'sequential' runner, a list of agents of type agents.Agent must be passed!")
            if not len(agents) >= 1:
                raise ValueError("When using 'sequential' runner, at least one agent must be passed!")
        elif runner == "planner_executor":
            if not isinstance(agents, list) or not all(isinstance(agent, Agent) for agent in agents):
                raise ValueError("When using 'planner_executor' runner, a list of agents of type agents.Agent must be passed!")
            if not len(agents) == 2:
                raise ValueError("When using 'planner_executor' runner, exactly two agents must be passed (planner and executor)!")
            if termination_condition is None:
                raise ValueError("When using 'planner_executor' runner, a termination condition must be provided!")
        elif runner not in get_args(self.RunnerType):
            raise ValueError(f"Invalid runner specified. Supported runners are {get_args(self.RunnerType)}")

        self.agents = agents
        self.runner = runner
        self.termination_condition = termination_condition

        # planner_executor specific parameters
        self.max_iterations = max_iterations
        self.enable_executor_memory = enable_executor_memory
        self.shared_memory = shared_memory
        self.use_memory = use_memory

    async def query(
        self,
        input: str | list[TResponseInputItem],
        env: TaskEnvironment,
        attack_hooks: list[AttackHook] | None = None,
    ):
        
        if self.runner == "handoffs":
            return await self.run_handoffs(input, env, attack_hooks)
        elif self.runner == "sequential":
            return await self.run_sequential(input, env, attack_hooks)
        elif self.runner == "planner_executor":
            return await self.run_planner_executor(input, env, attack_hooks)

    async def run_handoffs(
        self,
        input: str | list[TResponseInputItem],
        env: TaskEnvironment,
        attack_hooks: list[AttackHook] | None = None,
    ) -> dict[str, Any]:
        
        """
        Runs the agents in a handoff manner (if there are any)
        It will also work with a single agent.

        Memory:
        - If use_memory is True, we use a shared memory for all agents.
        - If use_memory is False, we do not use memory.
        """
        if not isinstance(self.agents, Agent):
            raise ValueError("When using 'handoffs' runner, a single agent must be passed!")
        
        usage: dict[str, list[dict[str, int]]] = {
            self.agents.name: []
        }

        tool_calls: list[dict[str, Any]] = []

        attack_components = AttackComponents(
            input=input,
            final_output=None,
            memory_dict={},
            agent_dict={self.agents.name: self.agents},
            env=env
        )

        if self.use_memory:
            memory = SQLiteSession(session_id="handoff_memory")
        else:
            memory = None

        if attack_hooks is not None:
            execute_attacks(attack_hooks=attack_hooks, event_name="on_agent_start", iteration=0, components=attack_components)

        try:
            agent_result = await Runner.run(
                starting_agent=self.agents,
                input=attack_components.input,
                context=env,
                session=memory,
            )
        except Exception as e:
            return {
                "final_output": None,
                "usage": usage,
                "function_calls": self.cast_to_function_calls(tool_calls),
                "error": str(e)
            }

        attack_components.final_output = agent_result.final_output

        if attack_hooks is not None:
            execute_attacks(attack_hooks=attack_hooks, event_name="on_agent_end", iteration=0, components=attack_components)

        usage[self.agents.name].append(self.extract_usage(agent_result.raw_responses))

        for response in agent_result.raw_responses:
            for item in response.output:
                if item.type == "function_call":
                    tool_calls.append({
                        "tool_name": item.name,
                        "tool_arguments": item.arguments
                    })

        return {
            "final_output": attack_components.final_output,
            "usage": usage,
            "function_calls": self.cast_to_function_calls(tool_calls)
        }

    async def run_sequential(
        self,
        input: str | list[TResponseInputItem],
        env: TaskEnvironment,
        attack_hooks: list[AttackHook] | None = None,
        tool_calls_to_extract: list[str] | None = None
    ) -> dict[str, Any]:
        
        """
        Runs the agents in a sequential manner:
            - We create a separate memory for each agent to store their results.
            - It assumes the output of each agent will be used as the input for the next agent.
            - If the last agent does not produce a final output, the initial input will be used as the final output.
            - The final output will be the output of the last agent in the sequence after the termination condition is met.
            - The results of the last agent will be used to determine if the termination condition is met.

        Memory:
        - If shared_memory are True, we use a shared memory for all agents.
        - If use_memory is True and shared_memory are False, we use a separate memory for each agent.
        - Otherwise, we do not use memory.
        """
        if not isinstance(self.agents, list):
            raise ValueError("When using 'sequential' runner, a list of agents must be passed!")
        
        usage: dict[str, list[dict[str, int]]] = {
            agent.name: [] for agent in self.agents
        }
        
        tool_calls: list[dict[str, Any]] = []

        attack_components = AttackComponents(
            input=input,
            final_output=None,
            memory_dict={},
            agent_dict={agent.name: agent for agent in self.agents},
            env=env
        )

        iteration = 0

        if self.shared_memory:
            memory = SQLiteSession(session_id="sequential_memory")
        elif self.use_memory:
            memory = {}
            for agent in self.agents:
                memory[agent.name] = SQLiteSession(session_id=f"sequential_memory_{agent.name}")
        else:
            memory = None

        for agent in self.agents:

            if attack_hooks is not None:
                execute_attacks(attack_hooks=attack_hooks, event_name="on_agent_start", iteration=iteration, components=attack_components)

            try:
                if self.shared_memory:
                    agent_result = await Runner.run(
                        starting_agent=agent,
                        input=attack_components.input,
                        context=env,
                        session=memory,
                    )
                elif self.use_memory:
                    agent_result = await Runner.run(
                        starting_agent=agent,
                        input=attack_components.input,
                        context=env,
                        session=memory[agent.name],
                    )
                else:
                    agent_result = await Runner.run(
                        starting_agent=agent,
                        input=attack_components.input,
                        context=env,
                    )
            except Exception as e:
                return {
                    "final_output": None,
                    "usage": usage,
                    "function_calls": self.cast_to_function_calls(tool_calls),
                    "error": str(e)
                }

            attack_components.final_output = agent_result.final_output

            if attack_hooks is not None:
                execute_attacks(attack_hooks=attack_hooks, event_name="on_agent_end", iteration=iteration, components=attack_components)

            usage[agent.name].append(self.extract_usage(agent_result.raw_responses))

            if agent.name in tool_calls_to_extract or tool_calls_to_extract is None:
                for response in agent_result.raw_responses:
                    for item in response.output:
                        if item.type == "function_call":
                            tool_calls.append({
                                "tool_name": item.name,
                                "tool_arguments": item.arguments
                            })

            # The final output from the current agent will be used as input for the next agent
            attack_components.input = agent_result.final_output

            iteration += 1

        return {
            "final_output": attack_components.final_output,
            "usage": usage,
            "function_calls": self.cast_to_function_calls(tool_calls)
        }
    
    async def run_planner_executor(
        self,
        input: str | list[TResponseInputItem],
        env: TaskEnvironment,
        attack_hooks: list[AttackHook] | None = None,
    ) -> dict[str, Any]:
        """
        Runs the agents in a planner-executor manner:
            - The first agent is assumed to be the planner, which generates a plan or output to be executed by the second agent (executor).
            - The second agent (executor) takes the output from the planner and executes it.
            - The process continues until the termination condition is met or the maximum number of iterations is reached.
            - The final output will be the output of the planner after the termination condition is met.
        
        Memory:
        - If use_memory is True, then the planner has memory.
        - If shared_memory is True, then the executor and planner has memory.
        - If enable_executor_memory is True, then the executor has memory.
        - Otherwise, we do not use memory.
        """

        usage: dict[str, list[dict[str, int]]] = {
            "planner": [
            ],
            "executor": [
            ]
        }

        planner = self.agents[0]

        executor = self.agents[1]

        iteration = 0

        planner_memory = SQLiteSession(session_id="planner_memory") if self.use_memory else None

        executor_memory = planner_memory if self.shared_memory else SQLiteSession(session_id="executor_memory") if self.enable_executor_memory else None

        executor_tool_calls: list[dict[str, Any]] = []

        attack_components = AttackComponents(
            input=input,
            final_output=None,
            memory_dict={
                "planner": planner_memory,
                "executor": executor_memory
            },
            agent_dict={
                "planner": planner,
                "executor": executor
            },
            env=env
        )

        while iteration < self.max_iterations:  # Prevent infinite loops

            if attack_hooks is not None:
                execute_attacks(attack_hooks=attack_hooks, event_name="on_planner_start", iteration=iteration, components=attack_components)

            try:
                planner_result = await Runner.run(
                    starting_agent=planner,
                    input=attack_components.input,
                    context=env,
                    session=planner_memory,
                )
            except Exception as e:
                return {
                    "final_output": None,
                    "usage": usage,
                    "function_calls": self.cast_to_function_calls(executor_tool_calls),
                    "error": str(e)
                }

            attack_components.final_output = planner_result.final_output

            if attack_hooks is not None:
                execute_attacks(attack_hooks=attack_hooks, event_name="on_planner_end", iteration=iteration, components=attack_components)

            usage["planner"].append(self.extract_usage(planner_result.raw_responses))

            if self.termination_condition(iteration=iteration, results=planner_result.to_input_list()):
                break

            attack_components.input = self.cast_output_to_input(planner_result.final_output)

            if attack_hooks is not None:
                execute_attacks(attack_hooks=attack_hooks, event_name="on_executor_start", iteration=iteration, components=attack_components)

            try:
                executor_result = await Runner.run(
                    executor,
                    input=attack_components.input,
                    context=env,
                    session=executor_memory,
                )
            except Exception as e:
                return {
                    "final_output": None,
                    "usage": usage,
                    "function_calls": self.cast_to_function_calls(executor_tool_calls),
                    "error": str(e)
                }

            attack_components.final_output = executor_result.final_output

            if attack_hooks is not None:
                execute_attacks(attack_hooks=attack_hooks, event_name="on_executor_end", iteration=iteration, components=attack_components)

            usage["executor"].append(self.extract_usage(executor_result.raw_responses))

            for response in executor_result.raw_responses:
                    for item in response.output:
                        if item.type == "function_call":
                             executor_tool_calls.append({
                                "tool_name": item.name,
                                "tool_arguments": item.arguments
                            })

            attack_components.input = self.cast_output_to_input(executor_result.final_output)

            iteration += 1

        return {
            "final_output": planner_result.final_output,
            "usage": usage,
            "function_calls": self.cast_to_function_calls(executor_tool_calls)
        }

    def extract_usage(
        self,
        raw_responses: list[ModelResponse],
    ) -> dict[str, int]:
        
        usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "requests": 0
        }
        
        for response in raw_responses:
            usage["input_tokens"] += response.usage.input_tokens
            usage["output_tokens"] += response.usage.output_tokens
            usage["total_tokens"] += response.usage.total_tokens
            usage["requests"] += response.usage.requests

        return usage

    def cast_to_function_calls(
        self,
        tool_calls: list[dict[str, Any]],
    ) -> list[FunctionCall]:
        '''
        Converts a list of tool calls to a list of FunctionCall objects.
        '''
        return [
            FunctionCall(
                function=tool_call["tool_name"],
                args = json.loads(tool_call["tool_arguments"]),
            )
            for tool_call in tool_calls
        ]
    
    def cast_output_to_input(
        self,
        output: Any,
    ):
        if isinstance(output, str):
            # If the output is a string, we use it directly as the input
            input = output
        elif inspect.isclass(output) and issubclass(output, BaseModel):
            # If the output is a Pydantic model, we use its JSON representation as the input
            input = output.model_dump_json(indent=2)
        elif output is None:
            # If the output is None, we raise an error
            raise ValueError("Planner did not produce a final output to send to the executor!")
        else:
            try:
                # If the output is some other type, we try to cast it using JSON
                input = json.dumps(
                    output,
                    indent=2,
                    ensure_ascii=False,
                )
            except Exception as e:
                # If the output cannot be cast to a string, we raise an error
                raise ValueError(f"Failed to cast the output to string using JSON: {e}")
        return input