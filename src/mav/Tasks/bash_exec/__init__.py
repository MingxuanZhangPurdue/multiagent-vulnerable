from mav.Tasks.bash_exec.task_suite import bash_exec_task_suite
from mav.Tasks.bash_exec.user_tasks import BashExecUserTask  # noqa: F401 - Register tasks
from mav.Tasks.bash_exec import attack_tasks  # noqa: F401 - Register attack tasks from JSON

__all__ = ["bash_exec_task_suite"]

