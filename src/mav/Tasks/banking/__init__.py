from mav.Tasks.banking.task_suite import banking_task_suite
from mav.Tasks.banking.user_tasks import BankingUserTask  # noqa: F401 - Register tasks
from mav.Tasks.banking.harmful_behavior import HarmfulBehaviorTask0 # noqa: F401 - Register tasks
from mav.Tasks.banking.privacy import PrivacyTask0 # noqa: F401 - Register tasks
from mav.Tasks.banking.exhaustion import ExhaustionTask0 # noqa: F401 - Register tasks

__all__ = ["banking_task_suite"]
