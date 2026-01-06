import yaml
import re
import warnings
import asyncio
import time
import traceback
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Generic, TypeVar, Callable, Any
from mav.Tasks.base_environment import TaskEnvironment
from mav.Tasks.utils.yaml_loader import ImportLoader
from mav.Tasks.base_tasks import BaseUserTask, BaseAttackTask
from mav.MAS.framework import MultiAgentSystem, MASRunResult
from mav.Tasks.items import FunctionCall

Env = TypeVar("Env", bound=TaskEnvironment)

@lru_cache
def read_suite_file(suite_name: str, file: str, suite_data_path: Path | None) -> str:
    if suite_data_path is not None:
        path = suite_data_path / file
        with path.open() as f:
            data_yaml = yaml.load(f, ImportLoader)
        return yaml.dump(data_yaml, default_flow_style=False)
    current_dir = Path(__file__).parent
    path = current_dir / suite_name / "data" / file
    with path.open() as f:
        # Load into yaml to resolve imports
        data_yaml = yaml.load(f, ImportLoader)
    # dump back to string to pass to include injections later
    return yaml.dump(data_yaml, default_flow_style=False)

class TaskSuite(Generic[Env]):
    def __init__(
        self,
        name: str,
        environment_type: type[Env],
        tools: list[Callable],
        data_path: Path | None = None,
    ):
        """Initialize a Task Suite.
        Args:
            name: The name of the task suite.
            environment_type: The type of environment used in the task suite.
            tools: A list of tool callables available to agents in the suite.
            data_path: Optional path to the suite's data files.
        """
        self.name: str = name
        self.environment_type: type[Env] = environment_type
        self.tools = tools
        self.user_tasks: dict[str, BaseUserTask[Env]] = defaultdict(dict)
        self.data_path = data_path
        self.task_types = {"user_task": "UserTask"}
    
    def load_tasks_by_type(self, type: str) -> dict[str, BaseUserTask[Env] | BaseAttackTask[Env]]:
        tasks_to_load = {}
        for task in self.user_tasks.values():
            if task.type == type:
                tasks_to_load[task.ID] = task
        return tasks_to_load

    def load_default_environment(self) -> Env:
        environment_text = read_suite_file(self.name, "environment.yaml", self.data_path)
        environment = self.environment_type.model_validate(yaml.safe_load(environment_text))
        return environment
    
    def register_task_type(self, task_type: str, task_cls: str):
        if task_type not in self.task_types:
            self.task_types[task_type] = task_cls

    @lru_cache
    def get_task_by_id(self, task_id: str) -> BaseUserTask[Env] | BaseAttackTask[Env]:
        """Get a task by its ID."""
        return self.user_tasks[task_id]
     
    def _get_task_number(self, task_cls: type[BaseUserTask], prefix: str) -> int:
        match = re.match(rf"{prefix}(\d+)", task_cls.__name__)
        if not match:
            raise ValueError(f"User tasks must be named {prefix} followed by a number, got {task_cls.__name__}")
        return int(match.group(1))

    def register_user_task(self, task_type: str = "user_task") -> type[BaseUserTask[Env]]:
        """Register a user task in the suite.

        Args:
            task: The user task class to register.
        """
        def register_task(task: type[BaseUserTask[Env]]):
            prefix = self.task_types[task_type]
            task_n = self._get_task_number(task, prefix)
            if task_type not in self.task_types:
                raise ValueError(f"Unknown task type: {task_type}")
            if task_type == "user_task":
                task_id = f"user_task_{task_n}"
            else:
                task_id = f"{task_type}_task_{task_n}"

            setattr(task, "ID", task_id)
            setattr(task, "type", task_type)
            self.user_tasks[task_id] = task()
            return task
        return register_task
    
    def _transform_MASRunResult_to_dict(self, result: MASRunResult) -> dict[str, Any]:
        """
        A temporary function to transform MASRunResult to a dictionary for attack tasks security evaluation.
        """
        function_tool_calls: list[dict[str, Any]] = [
            tool_call
            for outer_list in result.tool_calls_dict.values()
            for inner_list in outer_list
            for tool_call in inner_list
        ]

        function_calls = [
            FunctionCall(
                function=tool_call.get("name"),
                args=tool_call.get("arguments", {})
            ) for tool_call in function_tool_calls
        ]

        error = " ".join(result.errors) if result.errors else ""

        timed_out = result.appendix.get("timed_out", False) if result.appendix else False

        execution_time = result.time_duration if result.time_duration else 0.0

        return {
            "function_calls": function_calls,
            "final_output": result.final_output,
            "error": error,
            "timed_out": timed_out,
            "execution_time": execution_time,
        }
    
    async def run_task_with_pipeline(
        self,
        multi_agent_system: MultiAgentSystem,
        task: BaseUserTask[Env] | BaseAttackTask[Env],
        attack_hooks: list[Callable] | None = None,
        environment: Env | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        
        # If no environment is provided, load the default environment
        if environment is None:
            environment = self.load_default_environment()
        # Initialize the environment according to the task, some of the tasks may modify the environment before running
        if isinstance(task, BaseUserTask):
            task_environment = task.init_environment(environment)
        else:
            task_environment = environment

        # Create a copy of the environment before running the user task to then diff if needed
        pre_environment = task_environment.model_copy(deep=True)

        # Prepare the prompt from the task
        if isinstance(task, BaseUserTask) or isinstance(task, BaseAttackTask):
            prompt = task.PROMPT
        else:
            raise ValueError(f"Task {task.ID} is not a valid BaseUserTask or BaseAttackTask instance")
        
        # Record start time
        start_time = time.perf_counter()

        try:
            if timeout is not None:
                result: MASRunResult = await asyncio.wait_for(
                    multi_agent_system.query(
                        input=prompt, 
                        context=task_environment,
                        attack_hooks=attack_hooks
                    ),
                    timeout=timeout
                )
            else:
                result: MASRunResult = await multi_agent_system.query(
                    input=prompt, 
                    context=task_environment,
                    attack_hooks=attack_hooks
                )
        except asyncio.TimeoutError:
            error_message = f"Task {task.ID} timed out after {timeout} seconds"
            warnings.warn(error_message)
            result = MASRunResult(
                final_output=None,
                tool_calls_dict={},
                inpout_calls_dict={},
                output_dict={},
                usage_dict={},
                time_duration=time.perf_counter() - start_time,
                errors=[error_message],
                appendix={"timed_out": True},
            )
        except Exception as e:
            error_message = f"Task {task.ID} failed with exception: {e} \n {traceback.format_exc()}"
            warnings.warn(error_message)
            result = MASRunResult(
                final_output=None,
                tool_calls_dict={},
                inpout_calls_dict={},
                output_dict={},
                usage_dict={},
                time_duration=time.perf_counter() - start_time,
                errors=[error_message],
            )

        if result.final_output is None:
            warnings.warn(f"Model output was None for task {task.ID}")

        # Evaluate the task based on its type
        if isinstance(task, BaseAttackTask):
            results_dict = self._transform_MASRunResult_to_dict(result)
            evaluation_results: bool | dict[str, Any] = task.security(
                model_output=result.final_output,
                pre_environment=pre_environment,
                post_environment=task_environment,
                result=results_dict
            )
        elif isinstance(task, BaseUserTask):
            evaluation_results: bool | dict[str, Any] = task.utility(
                model_output=result.final_output,
                pre_environment=pre_environment,
                post_environment=task_environment,
            )

        # Return the evaluation results, if it's a boolean wrap it in a dict with the MAS run result, else merge the MAS run result into the dict
        if isinstance(evaluation_results, bool):
            return {
                "utility": evaluation_results,
                "MAS_run_result": result
            }
        else:
            evaluation_results["MAS_run_result"] = result
            return evaluation_results