import yaml
import re
import warnings
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Generic, TypeVar, Callable, List, Sequence
from mav.items import FunctionCall
from mav.Tasks.base_environment import TaskEnvironment
from mav.Tasks.utils.yaml_loader import ImportLoader
from mav.Tasks.base_tasks import BaseUserTask
from mav.MAS.pipeline import Pipeline

IT = TypeVar("IT")

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

Env = TypeVar("Env", bound=TaskEnvironment)

class TaskSuite(Generic[Env]):
    def __init__(
        self,
        name: str,
        environment_type: type[Env],
        tools: List[Callable],
        data_path: Path | None = None,
    ):
        self.name = name
        self.environment_type = environment_type
        self.tools = tools
        self.user_tasks: dict[str, BaseUserTask[Env]] = defaultdict(dict)
        self.data_path = data_path

    def load_default_environment(self) -> Env:
        environment_text = read_suite_file(self.name, "environment.yaml", self.data_path)
        environment = self.environment_type.model_validate(yaml.safe_load(environment_text))
        return environment
    
    def _get_task_number(self, task_cls: type[BaseUserTask], prefix: str) -> int:
        match = re.match(rf"{prefix}(\d+)", task_cls.__name__)
        if not match:
            raise ValueError(f"User tasks must be named {prefix} followed by a number, got {task_cls.__name__}")
        return int(match.group(1))

    def register_user_task(self, task: type[BaseUserTask[Env]]) -> type[BaseUserTask[Env]]:
        """Register a user task in the suite.

        Args:
            task: The user task class to register.
        """
        task_n = self._get_task_number(task, "UserTask")
        task_id = f"user_task_{task_n}"
        setattr(task, "ID", task_id)
        self.user_tasks[task_id] = task()
        return task
    
    async def run_task_with_pipeline(
        self,
        pipeline: Pipeline,
        user_task: BaseUserTask[Env],
        environment: Env | None = None,
    ) -> tuple[bool, bool]:
        # If no environment is provided, load the default environment
        if environment is None:
            environment = self.load_default_environment()
        # Initialize the environment according to the task
        if isinstance(user_task, BaseUserTask):
            task_environment = user_task.init_environment(environment)
        else:
            task_environment = environment

        # Create a copy of the environment before running the user task to then diff if needed
        pre_environment = task_environment.model_copy(deep=True)
        if isinstance(user_task, BaseUserTask):
            prompt = user_task.PROMPT
        else:
            prompt = user_task.GOAL
            
        try:
            results = await pipeline.query(prompt, task_environment)
        except Exception as e:
            results = {
                "final_output": None,
                "tool_calls": [],
                "environment": task_environment,
            }

        if results["final_output"] is None:
            warnings.warn(f"Model output was None for task {user_task.ID}")

        functions_stack_trace = results.get("tool_calls", [])
        utility = self._check_task_result(
            user_task,
            results["final_output"] or [],
            pre_environment,
            task_environment,  # type: ignore
            functions_stack_trace,
        )
        return utility, True
    
    def _check_user_task_utility(
        self,
        task: BaseUserTask,
        model_output: str | List[str],
        pre_environment: Env,
        task_environment: Env,
        functions_stack_trace: Sequence[FunctionCall],
    ) -> bool:
        utility_from_stack_traces = task.utility_from_traces(
            model_output, pre_environment, task_environment, functions_stack_trace
        )
        if utility_from_stack_traces is not None:
            return utility_from_stack_traces
        return task.utility(model_output, pre_environment, task_environment)

    def _check_task_result(
        self,
        task: BaseUserTask,
        model_output: str | List[str],
        pre_environment: Env,
        task_environment: Env,
        functions_stack_trace: Sequence[FunctionCall],
    ) -> bool:
        return self._check_user_task_utility(
            task,
            model_output,
            pre_environment,
            task_environment,
            functions_stack_trace,
        )