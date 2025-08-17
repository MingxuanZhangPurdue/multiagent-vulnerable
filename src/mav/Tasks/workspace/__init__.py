from mav.Tasks.workspace.task_suite import workspace_task_suite
from mav.Tasks.workspace.user_tasks import WorkspaceUserTask  # noqa: F401 - Register tasks
from mav.Tasks.utils.task_loader import load_attack_tasks
import os

load_attack_tasks(os.path.dirname(__file__), f"{__package__}.attack_tasks")

__all__ = ["workspace_task_suite"]
