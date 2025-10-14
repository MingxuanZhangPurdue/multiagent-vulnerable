from mav.Tasks.base_tasks import BaseUserTask
from mav.Tasks.bash_exec.environment import BashExecEnvironment
from mav.items import FunctionCall
from mav.Tasks.bash_exec.task_suite import bash_exec_task_suite as task_suite

BashExecUserTask = BaseUserTask[BashExecEnvironment]

