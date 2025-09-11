
from mav.Tasks.slack.task_suite import slack_task_suite
from mav.Tasks.slack.user_tasks import SlackUserTask  # noqa: F401 - Register tasks
from mav.Tasks.utils.task_loader import load_attack_tasks
import os

load_attack_tasks(os.path.dirname(__file__), f"{__package__}.attack_tasks")

__all__ = ["slack_task_suite"]
