from collections import defaultdict
from mav.Tasks.banking.task_suite import banking_task_suite
from mav.Tasks.slack.task_suite import slack_task_suite
from mav.Tasks.travel.task_suite import travel_task_suite
from mav.Tasks.workspace.task_suite import workspace_task_suite
from mav.Tasks.task_suite import TaskSuite

_SUITES: defaultdict[str, TaskSuite] = defaultdict(
    lambda: None,  # Returns None for missing keys
    {
        banking_task_suite.name: banking_task_suite,
        slack_task_suite.name: slack_task_suite,
        travel_task_suite.name: travel_task_suite,
        workspace_task_suite.name: workspace_task_suite,
    }
)

def get_suites() -> dict[str, TaskSuite]:
    return _SUITES

def get_suite(suite_name: str) -> TaskSuite:
    return _SUITES[suite_name]