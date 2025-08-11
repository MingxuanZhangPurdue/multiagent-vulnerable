from mav.MAS.framework import MultiAgentSystem
from mav.Tasks.banking import environment
from mav.Tasks.task_suite import TaskSuite
from typing import Sequence
from tqdm import tqdm
from mav.Attacks.attack import BaseAttack

async def benchmark_suite_without_injections(
    multi_agent_system: MultiAgentSystem,
    suite: TaskSuite,
    attacks: list[BaseAttack] | None = None,
    user_tasks: Sequence[str] | None = None,
):
    suite_results: dict[str, dict] = {}

    if user_tasks is not None:
        user_tasks_to_run = [suite.get_user_task_by_id(user_task_id) for user_task_id in user_tasks]
    else:
        user_tasks_to_run = suite.user_tasks.values()

    for user_task in tqdm(user_tasks_to_run, desc="Running User Tasks"):
        utility, results = await suite.run_task_with_pipeline(
            multi_agent_system=multi_agent_system,
            user_task=user_task,
            attacks=attacks
        )
        suite_results[user_task.ID] = {
            "utility": utility,
            "results": results,
        }

    return suite_results