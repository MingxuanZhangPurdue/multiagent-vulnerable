from mav.Tasks.task_suite import TaskSuite
from mav.Tasks.bash_exec.environment import BashExecEnvironment

tools = []

bash_exec_task_suite = TaskSuite[BashExecEnvironment](
    tools=tools,
    name="bash_exec",
    environment_type=BashExecEnvironment,
)

