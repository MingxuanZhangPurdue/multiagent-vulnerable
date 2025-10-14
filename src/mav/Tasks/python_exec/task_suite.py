from mav.Tasks.task_suite import TaskSuite
from mav.Tasks.python_exec.environment import PythonExecEnvironment

tools = []

python_exec_task_suite = TaskSuite[PythonExecEnvironment](
    tools=tools,
    name="python_exec",
    environment_type=PythonExecEnvironment,
)
