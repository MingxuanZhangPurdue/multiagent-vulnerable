import sys
from mav.MAS.framework import MultiAgentSystem
from mav.Tasks.task_suite import TaskSuite
from typing import Sequence
from tqdm import tqdm
from mav.MAS.attack_hook import AttackHook
from mav.Tasks.base_tasks import BaseUserTask, BaseAttackTask

async def benchmark_suite(
    multi_agent_system: MultiAgentSystem,
    suite: TaskSuite,
    attack_hooks: list[AttackHook] | None = None,
    IDs: Sequence[str] | None = None,
    task_type: str = "user_task",
    timeout: float = 200
):
    suite_results: dict[str, dict] = {}

    # Load tasks of the specified type
    tasks_of_type = suite.load_tasks_by_type(task_type)

    tasks_to_run: list[BaseAttackTask] | list[BaseUserTask] = []

    # Filter tasks to run based on provided IDs, if not provided run all tasks of that type
    if IDs is not None:
        tasks_to_run = [tasks_of_type[task_id] for task_id in IDs if task_id in tasks_of_type]
    else:
        tasks_to_run = list(tasks_of_type.values())

    for task in tqdm(tasks_to_run, desc=f"Running {task_type} tasks", file=sys.stderr):
        eval_result = await suite.run_task_with_pipeline(
            multi_agent_system=multi_agent_system,
            task=task,
            attack_hooks=attack_hooks,
            timeout=timeout,
        )

        suite_results[task.ID] = eval_result

    return suite_results

