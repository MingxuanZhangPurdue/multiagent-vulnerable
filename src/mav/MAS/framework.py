import json
import inspect
from agents import (
    Agent,
    Runner, 
    SQLiteSession,
    TResponseInputItem
)

from typing import Any, Literal, get_args
from pydantic import BaseModel

from mav.MAS.terminations import BaseTermination
from mav.items import FunctionCall
from mav.Tasks.base_environment import TaskEnvironment
from mav.MAS.terminations import BaseTermination


class MultiAgentSystem:

    RunnerType = Literal["handoffs", "sequential", "planner_executor"]

    def __init__(
        self,
        agents: Agent | list[Agent],
        runner: RunnerType,
        termination_condition: list[BaseTermination] | None = None,
        max_iterations: int = 1000,
        enable_executor_memory: bool = True,
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

    async def query(
        self,
        input: str | list[TResponseInputItem],
        env: TaskEnvironment,
    ):
        
        if self.runner == "handoffs":
            return await self.run_handoffs(input, env)
        elif self.runner == "sequential":
            return await self.run_sequential(input, env)
        elif self.runner == "planner_executor":
            return await self.run_planner_executor(input, env)

    async def run_handoffs(
        self,
        input: str | list[TResponseInputItem],
        env: TaskEnvironment,
    ) -> dict[str, Any]:
        
        """
        Runs the agents in a handoff manner (if there are any)
        It will also work with a single agent.
        """
        if not isinstance(self.agents, Agent):
            raise ValueError("When using 'handoffs' runner, a single agent must be passed!")

        agent_input = input

        agent_result = await Runner.run(
            starting_agent=self.agents,
            input=agent_input,
            context=env,
        )

        final_output = agent_result.final_output

        return {
            "final_output": final_output,
            "environment": env,
        }

    async def run_sequential(
        self,
        input: str | list[TResponseInputItem],
        env: TaskEnvironment,
    ) -> dict[str, Any]:
        
        """
        Runs the agents in a sequential manner:
            - We create a separate memory for each agent to store their results.
            - It assumes the output of each agent will be used as the input for the next agent.
            - If the last agent does not produce a final output, the initial input will be used as the final output.
            - The final output will be the output of the last agent in the sequence after the termination condition is met.
            - The results of the last agent will be used to determine if the termination condition is met.
        """
        if not isinstance(self.agents, list):
            raise ValueError("When using 'sequential' runner, a list of agents must be passed!")

        agent_input = input

        for agent in self.agents:

            agent_result = await Runner.run(
                starting_agent=agent,
                input=agent_input,
                context=env,
            )
            
            # The final output from the current agent will be used as input for the next agent
            if agent_result.final_output:
                agent_input = agent_result.final_output
            else:
                # If the agent does not produce a final output, we use the initial input for the next agent
                agent_input = input

        final_output = agent_result.final_output

        return {
            "final_output": final_output,
            "environment": env,
        }
    
    async def run_planner_executor(
        self,
        input: str | list[TResponseInputItem],
        env: TaskEnvironment,
    ) -> dict[str, Any]:
        """
        Runs the agents in a planner-executor manner:
            - The first agent is assumed to be the planner, which generates a plan or output to be executed by the second agent (executor).
            - The second agent (executor) takes the output from the planner and executes it.
            - The process continues until the termination condition is met or the maximum number of iterations is reached.
            - The final output will be the output of the planner after the termination condition is met.
        """

        planner = self.agents[0]

        executor = self.agents[1]

        iteration = 0

        planner_memory = SQLiteSession(session_id="planner_memory")

        executor_memory = SQLiteSession(session_id="executor_memory") if self.enable_executor_memory else None

        planner_input = input

        executor_input = None

        while True and iteration < self.max_iterations:  # Prevent infinite loops

            iteration += 1

            planner_result = await Runner.run(
                starting_agent=planner,
                input=planner_input,
                context=env,
                session=planner_memory,
            )
            
            if self.termination_condition(iteration=iteration, results=planner_result.to_input_list()):
                break

            executor_input = self.cast_output_to_input(planner_result.final_output)

            executor_result = await Runner.run(
                executor,
                input=executor_input,
                context=env,
                session=executor_memory,
            )

            planner_input = self.cast_output_to_input(executor_result.final_output)

        return {
            "final_output": planner_result.final_output,
            "environment": env,
        }


    def cast_to_function_call(
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