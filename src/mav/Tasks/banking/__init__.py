from mav.Tasks.banking.task_suite import banking_task_suite
from mav.Tasks.banking.user_tasks import BankingUserTask  # noqa: F401 - Register tasks
from mav.Tasks.utils.task_loader import load_attack_tasks
import os

load_attack_tasks(os.path.dirname(__file__), f"{__package__}.attack_tasks")

__all__ = ["banking_task_suite"]
