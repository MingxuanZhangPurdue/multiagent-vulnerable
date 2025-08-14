from typing import ClassVar
from mav.Tasks.base_tasks import BaseAttackTask, TaskDifficulty
from mav.Tasks.task_suite import SlackEnvironment
from mav.Tasks.slack.task_suite import slack_task_suite as task_suite
from mav.items import FunctionCall

SlackExhaustionTask = BaseAttackTask[SlackEnvironment]

@task_suite.register_exhaustion_task
class ExhaustionTask0(SlackExhaustionTask):
    """
   
    """
    

@task_suite.register_exhaustion_task
class ExhaustionTask1(SlackExhaustionTask):
    """
    
    """


@task_suite.register_exhaustion_task
class ExhaustionTask2(SlackExhaustionTask):
    """
    
    """
    

@task_suite.register_exhaustion_task
class ExhaustionTask3(SlackExhaustionTask):
    """
    
    """