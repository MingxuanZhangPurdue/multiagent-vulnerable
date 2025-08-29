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


def get_environment_inspection_function(suite_name):
    """
    Dynamically get the environment inspection function for a given task suite.
    This eliminates the need to manually update function names when switching agents.
    """
    # Get the task suite
    task_suite = get_suite(suite_name)

    # Mapping of known environment inspection function names by suite
    inspection_function_candidates = [
        "environment_inspection",  # banking
        "get_channels",           # slack  
        "get_current_day",        # workspace
        "get_day_calendar_events", # travel
    ]

    # Find the environment inspection function in the suite's tools
    for tool in task_suite.tools:
        if tool.__name__ in inspection_function_candidates:
            return tool

    # Fallback: return the first tool that looks like an inspection function
    for tool in task_suite.tools:
        if any(keyword in tool.__name__.lower() for keyword in ["inspect", "current", "channel", "environment"]):
            return tool

    # If nothing found, return None and let the user know
    raise ValueError(f"No environment inspection function found for suite: {suite_name}")