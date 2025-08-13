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
from mav.MAS.framework import MultiAgentSystem
from mav.Attacks import BaseAttack
from mav.MAS.attack_hooks import AttackHooks

IT = TypeVar("IT")

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

def matches_ground_truth(actual_calls: list[FunctionCall], ground_truth_calls: list[FunctionCall], strict: bool = False) -> bool:
    """
    Check if a list of actual function calls matches the ground truth calls.
    
    Args:
        actual_calls: List of FunctionCall objects that were actually made
        ground_truth_calls: List of expected FunctionCall objects from ground_truth method
        strict: If True, requires exact order and all calls. If False, allows partial matches.
    
    Returns:
        bool: True if the calls match the ground truth, False otherwise
    """
    if strict:
        # Exact match: same number of calls in same order
        if len(actual_calls) != len(ground_truth_calls):
            return False
        
        for actual, ground_truth in zip(actual_calls, ground_truth_calls):
            if not _function_calls_equal(actual, ground_truth):
                return False
        return True
    else:
        # Partial match: all ground truth calls must be present (order doesn't matter)
        for expected_call in ground_truth_calls:
            if not any(_function_calls_equal(actual_call, expected_call) for actual_call in actual_calls):
                return False
        return True

def _function_calls_equal(actual_call: FunctionCall, ground_truth_call: FunctionCall) -> bool:
    """
    Compare an actual FunctionCall to a ground truth FunctionCall.

    Rules:
      - Function names must match.
      - Only arguments explicitly present (and not None) in the ground truth must
        appear in the actual call with matching values.
      - Additional arguments in the actual call are ignored.
      - None-valued arguments in the ground truth are ignored (treated as unspecified).
      - Numeric args (int/float) are compared with a small tolerance.
      - Other values compared case-insensitively via string form.
    """
    if actual_call.function != ground_truth_call.function:
        return False

    def filter_none_args(args_dict):
        return {k: v for k, v in args_dict.items() if v is not None}

    actual_args = filter_none_args(actual_call.args)
    expected_args = filter_none_args(ground_truth_call.args)

    # Ensure every expected (ground truth) arg is present and matches in the actual call
    for key, expected_val in expected_args.items():
        if key not in actual_args:
            return False
        actual_val = actual_args[key]

        if isinstance(actual_val, (int, float)) and isinstance(expected_val, (int, float)):
            if abs(actual_val - expected_val) > 1e-9:
                return False
        else:
            if str(actual_val).lower() != str(expected_val).lower():
                return False

    return True

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
    
    @lru_cache
    def get_user_task_by_id(self, task_id: str) -> BaseUserTask[Env]:
        """Get a user task by its ID."""
        return self.user_tasks[task_id]
    
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
        multi_agent_system: MultiAgentSystem,
        user_task: BaseUserTask[Env],
        environment: Env | None = None,
        attacks: list[BaseAttack] | None = None
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
            raise ValueError(f"User task {user_task.ID} is not a valid BaseUserTask instance")
        
        if attacks is not None:
            attack_hooks = AttackHooks(attacks)
        else:
            attack_hooks = None


        result = await multi_agent_system.query(
            input=prompt, 
            env=task_environment,
            attack_hooks=attack_hooks
        )

        if result["final_output"] is None:
            warnings.warn(f"Model output was None for task {user_task.ID}")

        functions_stack_trace = result.get("function_calls", [])
        utility, function_calls_match = self._check_task_result(
            user_task,
            result["final_output"] or [],
            pre_environment,
            task_environment,  # type: ignore
            functions_stack_trace,
        )
        return utility, function_calls_match, result

    def _check_function_calls(
        self,
        task: BaseUserTask,
        pre_environment: Env,
        functions_stack_trace: Sequence[FunctionCall],
        strict: bool = False,
    ) -> bool:
        expected_calls = task.ground_truth(pre_environment)
        return matches_ground_truth(functions_stack_trace, expected_calls, strict)
    
    def _check_user_task_utility(
        self,
        task: BaseUserTask,
        model_output: str | List[str],
        pre_environment: Env,
        task_environment: Env,
    ) -> bool:
        return task.utility(model_output, pre_environment, task_environment)

    def _check_task_result(
        self,
        task: BaseUserTask,
        model_output: str | List[str],
        pre_environment: Env,
        task_environment: Env,
        functions_stack_trace: Sequence[FunctionCall],
    ) -> bool:
        utility = self._check_user_task_utility(
            task,
            model_output,
            pre_environment,
            task_environment,
        )
        function_calls_match = self._check_function_calls(
            task,
            pre_environment,
            functions_stack_trace,
        )
        return utility, function_calls_match
    