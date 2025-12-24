from __future__ import annotations
import json
import inspect
import logging
import traceback
import time

from mav.MAS.agents import (
    Agent,
    Runner,
    InMemorySession,
    RunResult
)

from typing import Any, Literal, get_args, Awaitable
from pydantic import BaseModel
from dataclasses import dataclass

from mav.MAS.terminations import BaseTermination
from mav.Tasks.base_environment import TaskEnvironment
from mav.MAS.attack_hook import AttackHook

from mav.MAS.agents.run import update_usage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

@dataclass
class MASRunResult:

    final_output: Any
    """The final output produced by the MAS after completing its run."""

    usage_dict: dict[str, dict[str, Any]]
    """A dictionary containing aggregated usage for each agent during the MAS run."""

    tool_calls_dict: dict[str, list[list[dict[str, Any]]]]
    """A dictionary containing tool calls made by each agent at each iteration during the MAS run."""

    input_list_dict: dict[str, list[list[dict[str, Any]]]]
    """A dictionary containing the list of input items provided to each agent at each iteration during the MAS run."""

    output_dict: dict[str, list[Any]]
    """A dictionary containing the final output of each agent runner result at each iteration during the MAS run."""

    time_duration: float
    """The total time duration taken for the MAS run."""

    errors: list[str] | None = None

    def __post_init__(self):
        if not self.errors:
            self.errors = None

async def run_orchestrator_worker(
    MAS: MultiAgentSystem,
    input: str | list[dict[str, Any]],
    context: TaskEnvironment | None = None,
    attack_hooks: list[AttackHook] | None = None,
    # runner specific parameters
    endpoint_orchestrator: Literal["completion", "responses"] | None = None,
    max_orchestrator_iterations: int = 10,
) -> MASRunResult:
    
    """
    Run agents in a orchestrator-worker manner:
        - The given agent is assumed to be the orchestrator, which delegates tasks and spawns worker agents as needed.
        - The worker agents perform the tasks assigned by the orchestrator.
        - The worker agent should be pre-registered as tools that the orchestrator can call.
        - The process continues until no tool calls are made by the orchestrator or the maximum number of iterations is reached.
        - The final output will be the output of the orchestrator after the termination condition is met.

    Args:
        MAS: The MultiAgentSystem instance containing the agents and configuration.
        input: The initial input to the orchestrator agent.
        context: The task environment in which the agents operate.
        attack_hooks: Optional list of AttackHook instances to apply attacks during execution.
        endpoint_orchestrator: The litellm endpoint type to use for the agent runner, either "completion" or "responses".
        max_orchestrator_iterations: Maximum number of iterations for the orchestrator agent.
    """
    if not isinstance(MAS.agents, Agent):
        raise ValueError("When using 'orchestrator_worker' runner, a single agent must be passed!")
    
    logger.info(f"Running orchestrator_worker MAS with input: {input} and endpoint: {endpoint_orchestrator}. Attack hooks passed: {attack_hooks is not None}")

    start_time = time.monotonic()

    usage_dict: dict[str, dict[str, Any]] = {
        MAS.agents.name: {}
    }
    
    input_list_dict: dict[str, list[list[dict[str, Any]]]] = {
        MAS.agents.name: []
    }

    tool_calls_dict: dict[str, list[list[dict[str, Any]]]] = {
        MAS.agents.name: []
    }

    output_dict: dict[str, list[Any]] = {
        MAS.agents.name: []
    }

    errors = []

    try:
        agent_result: RunResult = await Runner.run(
            agent=MAS.agents,
            input=input,
            context=context,
            max_turns=max_orchestrator_iterations,
            attack_hooks=attack_hooks,
            endpoint=endpoint_orchestrator
        )
    except Exception as e:
        error_message = f"Error during MAS orchestrator_worker run: {e} \n{traceback.format_exc()}"
        logger.error(error_message)
        errors.append(error_message)
        return MASRunResult(
            final_output=None,
            usage_dict=usage_dict,
            tool_calls_dict=tool_calls_dict,
            input_list_dict=input_list_dict,
            output_dict=output_dict,
            time_duration=time.monotonic() - start_time,
            errors=errors
        )

    usage_dict[MAS.agents.name] = update_usage(usage_dict[MAS.agents.name], agent_result.usage)

    tool_calls_dict[MAS.agents.name].append(agent_result.tool_calls)

    input_list_dict[MAS.agents.name].append(agent_result.input_items)

    output_dict[MAS.agents.name].append(agent_result.final_output)

    logger.info("orchestrator_worker MAS run completed.")

    return MASRunResult(
        final_output=agent_result.final_output,
        usage_dict=usage_dict,
        tool_calls_dict=tool_calls_dict,
        input_list_dict=input_list_dict,
        output_dict=output_dict,
        time_duration=time.monotonic() - start_time
    )

async def run_planner_executor(
        MAS: MultiAgentSystem,
        input: str | list[dict[str, Any]],
        context: TaskEnvironment | None = None,
        attack_hooks: list[AttackHook] | None = None,
        # runner specific parameters
        endpoint_planner: Literal["completion", "responses"] | None = None,
        endpoint_executor: Literal["completion", "responses"] | None = None,
        max_iterations: int = 5,
        max_planner_iterations: int = 10,
        max_executor_iterations: int = 10,
        enable_planner_memory: bool = True,
        enable_executor_memory: bool = False,
        shared_memory: bool = False,
        termination_condition: BaseTermination | None = None,
    ) -> MASRunResult:
        """
        Runs the agents in a planner-executor manner:
            - The first agent is assumed to be the planner, which generates a plan or output to be executed by the second agent (executor).
            - The second agent (executor) takes the output from the planner and executes it.
            - The process continues until the termination condition is met or the maximum number of iterations (max_iterations) is reached.
            - The final output will be the output of the planner after the termination condition is met.
        Session memory configuration:
        - If enable_planner_memory is True, then the planner has session memory. This should be set to True if max_iterations > 1, otherwise the planner will not remember any previous iterations.
        - If enable_executor_memory is True, then the executor has session memory.
        - If shared_memory is True, then both planner and executor share the same session memory. When this is set to True, both enable_planner_memory and enable_executor_memory must be True, otherwise it will not have any effect.
        - Otherwise, we do not use memory.

        Args:
            MAS: The MultiAgentSystem instance containing the agents and configuration.
            input: The initial input to the planner agent.
            context: The task environment in which the agents operate.
            attack_hooks: Optional list of AttackHook instances to apply attacks during execution.
            endpoint_planner: The litellm endpoint type to use for the planner agent runner, either "completion" or "responses".
            endpoint_executor: The litellm endpoint type to use for the executor agent runner, either "completion" or "responses".
            max_iterations: Maximum number of planner-executor iterations.
            max_planner_iterations: Maximum number of iterations for the planner agent per turn.
            max_executor_iterations: Maximum number of iterations for the executor agent per turn.
            enable_planner_memory: Whether to enable session memory for the planner agent.
            enable_executor_memory: Whether to enable session memory for the executor agent.
            shared_memory: Whether to use shared session memory between planner and executor agents.
            termination_condition: An optional termination condition to determine when to stop the planner-executor loop.
        """
        if not isinstance(MAS.agents, list) or not all(isinstance(agent, Agent) for agent in MAS.agents):
            raise ValueError("When using 'planner_executor' runner, a list of agents of type mav.MAS.agents.Agent must be passed!")
        if not len(MAS.agents) == 2:
            raise ValueError("When using 'planner_executor' runner, exactly two agents must be passed (planner and executor) and in that order!")
        
        start_time = time.monotonic()
        
        logger.info(f"Running planner-executor MAS with input: {input} and endpoint_planner: {endpoint_planner}, endpoint_executor: {endpoint_executor}. Attack hooks passed: {attack_hooks is not None}")

        usage_dict: dict[str, dict[str, int]] = {
            "planner": {},
            "executor": {}
        }

        tool_calls_dict: dict[str, list[list[dict[str, Any]]]] = {
            "planner": [],
            "executor": []
        }

        input_list_dict: dict[str, list[list[dict[str, Any]]]] = {
            "planner": [],
            "executor": []
        }

        output_dict: dict[str, list[Any]] = {
            "planner": [],
            "executor": []
        }

        errors = []

        # Assuming the first agent is the planner and the second is the executor
        planner = MAS.agents[0]
        executor = MAS.agents[1]

        # Initialize the iteration counter
        iteration = 0

        # Session memory configuration
        if enable_planner_memory:
            planner_memory = InMemorySession(session_id="planner_memory")
        else:
            planner_memory = None
            if max_iterations > 1:
                logger.warning("Max iterations > 1 but enable_planner_memory is False. The planner will not remember any previous iterations. Are you sure this is intended?")

        if enable_executor_memory:
            executor_memory = InMemorySession(session_id="executor_memory")
        else:
            executor_memory = None

        if shared_memory:
            shared_session = InMemorySession(session_id="shared_memory")
            planner_memory = shared_session
            executor_memory = shared_session

        planner_input = input

        executor_input = None

        MAS_final_output = None

        while iteration < max_iterations:
            
            # Planner turn
            try:
                planner_result: RunResult = await Runner.run(
                    agent=planner,
                    input=planner_input,
                    context=context,
                    attack_hooks=attack_hooks,
                    session=planner_memory,
                    max_turns=max_planner_iterations,
                    endpoint=endpoint_planner
                )
            except Exception as e:
                error_message = f"Error during MAS planner_executor run at iteration {iteration} for the planner: {e} \n{traceback.format_exc()}"
                logger.error(error_message)
                errors.append(error_message)
                break
            
            # Update usage, tool calls, output, and input items for planner
            usage_dict["planner"] = update_usage(usage_dict["planner"], planner_result.usage)
            tool_calls_dict["planner"].append(planner_result.tool_calls)
            input_list_dict["planner"].append(planner_result.input_items)
            output_dict["planner"].append(planner_result.final_output)
            
            MAS_final_output = planner_result.final_output

            if termination_condition and termination_condition(iteration=iteration, input_items_dict=planner_result.input_items, output_dict=output_dict, env=context):
                break
            
            # Executor turn

            try:
                executor_input = MAS._agent_output_to_agent_input(planner_result.final_output)
            except Exception as e:
                error_message = f"Error casting planner output to executor input at iteration {iteration}: {e} \n{traceback.format_exc()}"
                logger.error(error_message)
                errors.append(error_message)
                break
            
            try:
                executor_result: RunResult = await Runner.run(
                    agent=executor,
                    input=executor_input,
                    context=context,
                    session=executor_memory,
                    max_turns=max_executor_iterations,
                    endpoint=endpoint_executor,
                )
            except Exception as e:
                error_message = f"Error during MAS planner_executor run at iteration {iteration} for executor: {e} \n{traceback.format_exc()}"
                logger.error(error_message)
                errors.append(error_message)
                break
            
            # Update usage, tool calls, and input items for executor
            usage_dict["executor"] = update_usage(usage_dict["executor"], executor_result.usage)
            tool_calls_dict["executor"].append(executor_result.tool_calls)
            input_list_dict["executor"].append(executor_result.input_items)
            output_dict["executor"].append(executor_result.final_output)

            try:
                planner_input = MAS._agent_output_to_agent_input(executor_result.final_output)
            except Exception as e:
                error_message = f"Error casting executor output to planner input at iteration {iteration}: {e} \n{traceback.format_exc()}"
                logger.error(error_message)
                errors.append(error_message)
                break

            iteration += 1

        logger.info("planner_executor MAS run completed.")

        return MASRunResult(
            final_output=MAS_final_output,
            usage_dict=usage_dict,
            tool_calls_dict=tool_calls_dict,
            input_list_dict=input_list_dict,
            output_dict=output_dict,
            time_duration=time.monotonic() - start_time,
            errors=errors
        )

class MultiAgentSystem:

    ImplementedMASRunnerType = Literal["orchestrator_worker", "planner_executor"]

    def __init__(
        self,
        agents: Agent | list[Agent],
        MAS_runner: ImplementedMASRunnerType | Awaitable,
        **runner_config: Any,
    ):
        """
        MAS_runner: defines the multi-agent-system runner to use. Supported runners are:
            - "orchestrator_worker": A single agent acts as an orchestrator, delegating
                tasks to worker agents as needed. All worker agents should be pre-registered as tools for the orchestrator agent to call.
            - "planner_executor": Two agents work in tandem, where the first agent
                acts as a planner, generating plans or outputs to be executed by the
                second agent (executor).
            - Custom async function: You can provide your own multi-agent-system runner
                as an async function that takes in four required named arguments:
                MAS, input, context, attack_hooks, and any additional keyword arguments you need.
        agents: The agent(s) to be used in the multi-agent-system runner.
        **runner_config: Default runner configuration. Can be overridden in query().
            Examples:
            - For orchestrator_worker: endpoint_orchestrator, max_orchestrator_iterations
            - For planner_executor: endpoint_planner, endpoint_executor, max_iterations, 
                max_planner_iterations, max_executor_iterations, enable_planner_memory, 
                enable_executor_memory, shared_memory, termination_condition
            - For custom runners: any parameters your runner accepts
        """

        if isinstance(MAS_runner, str) and MAS_runner == "orchestrator_worker":
            self.MAS_runner = run_orchestrator_worker
        
        elif isinstance(MAS_runner, str) and MAS_runner == "planner_executor":
            self.MAS_runner = run_planner_executor
            
        elif inspect.iscoroutinefunction(MAS_runner):
            self.MAS_runner = MAS_runner
            
        else:
            raise ValueError(f"Invalid runner specified. Supported runners are {get_args(self.ImplementedMASRunnerType)} or you can provide a custom multi-agent-system runner as an async function.")

        self.agents = agents
        self.runner_config = runner_config

    async def query(
        self,
        input: str | list[dict[str, Any]],
        context: TaskEnvironment | None = None,
        attack_hooks: list[AttackHook] | None = None,
        **runner_kwargs: Any,
    ) -> MASRunResult:
        """
        Query the multi-agent system.
        
        Args:
            input: The input to the MAS.
            context: The task environment.
            attack_hooks: Optional attack hooks.
            **runner_kwargs: Runner-specific parameters that override runner_config from __init__.
                Examples: max_iterations, endpoint_planner, enable_planner_memory, etc.
        """
        # Merge: defaults from init + runtime overrides (query kwargs take precedence)
        final_runner_config = {**self.runner_config, **runner_kwargs}
        
        return await self.MAS_runner(
            MAS=self,
            input=input,
            context=context,
            attack_hooks=attack_hooks,
            **final_runner_config
        )
    
    def _agent_output_to_agent_input(
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
            raise ValueError("Output to be cast to input cannot be None.")
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
    
    def update_MAS_usage(
        self,
        current_usage: dict[str, Any],
        new_usage: dict[str, Any],
    ) -> dict[str, Any]:
        """A convenience method to update the current usage dictionary with the new usage dictionary"""
        return update_usage(current_usage, new_usage)
