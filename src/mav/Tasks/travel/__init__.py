from mav.Tasks.travel.task_suite import travel_task_suite
from mav.Tasks.travel.user_tasks import TravelUserTask  # noqa: F401 - Register tasks
from mav.Tasks.utils.task_loader import load_attack_tasks
import os

load_attack_tasks(os.path.dirname(__file__), f"{__package__}.attack_tasks")

__all__ = ["travel_task_suite"]
