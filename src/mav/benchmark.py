from mav.MAS.framework import MultiAgentSystem
from mav.Tasks.banking import environment
from mav.Tasks.task_suite import TaskSuite
from typing import Sequence
from tqdm import tqdm
from mav.MAS.attack_hook import AttackHook

async def benchmark_suite(
    multi_agent_system: MultiAgentSystem,
    suite: TaskSuite,
    attack_hooks: list[AttackHook] | None = None,
    user_tasks: Sequence[str] | None = None,
    type: str = "user_task",
    timeout: float = 200
):
    suite_results: dict[str, dict] = {}

    if user_tasks is not None:
        user_tasks_to_run = [suite.get_user_task_by_id(user_task_id) for user_task_id in user_tasks]
    else:
        user_tasks_to_run = suite.user_tasks.values()
    
    user_tasks_to_run = [task for task in user_tasks_to_run if task.type == type]

    if type == "user_task":
        for user_task in tqdm(user_tasks_to_run, desc="Running User Tasks"):
            utility, function_calls_match, security, result, pre_environment, task_environment = await suite.run_task_with_pipeline(
                multi_agent_system=multi_agent_system,
                user_task=user_task,
                attack_hooks=attack_hooks
            )
            item = {
                "utility": utility,
                "function_calls_match": function_calls_match,
                "result": result,
                "security": security,
                "pre_environment": pre_environment,
                "post_environment": task_environment
            }

            suite_results[user_task.ID] = item
    else:
         for user_task in tqdm(user_tasks_to_run, desc="Running User Tasks"):
            utility, function_calls_match, result, pre_environment, task_environment = await suite.run_attack_task_with_pipeline(
                multi_agent_system=multi_agent_system,
                user_task=user_task,
                timeout = timeout
            )
            suite_results[user_task.ID] = {
                "utility": utility,
                "function_calls_match": function_calls_match,
                "result": result,
                "pre_environment": pre_environment,
                "post_environment": task_environment
            }

    return suite_results

