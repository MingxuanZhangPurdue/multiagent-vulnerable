
from mav.Tasks.slack.task_suite import slack_task_suite
from mav.Tasks.slack.user_tasks import SlackUserTask  # noqa: F401 - Register tasks

__all__ = ["slack_task_suite"]
