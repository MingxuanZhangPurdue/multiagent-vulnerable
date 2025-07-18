from mav.MAS.pipeline import Pipeline
from mav.Tasks.task_suite import TaskSuite
from typing import Sequence

async def benchmark_suite_without_injections(
    agent_pipeline: Pipeline,
    suite: TaskSuite,
    user_tasks: Sequence[str] | None = None,
):
    suite_results: dict[str, dict] = {}

    if user_tasks is not None:
        user_tasks_to_run = [suite.get_user_task_by_id(user_task_id) for user_task_id in user_tasks]
    else:
        user_tasks_to_run = suite.user_tasks.values()

    for user_task in user_tasks_to_run:
        utility, function_calls_match, results = await suite.run_task_with_pipeline(agent_pipeline, user_task)
        suite_results[user_task.ID] = {
            "utility": utility,
            "function_calls_match": function_calls_match,
            "results": results,
        }

    return suite_results