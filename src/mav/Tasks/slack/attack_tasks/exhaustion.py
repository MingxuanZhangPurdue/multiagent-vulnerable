from typing import ClassVar
from mav.Tasks.base_tasks import BaseAttackTask, TaskDifficulty
from mav.Tasks.slack.task_suite import SlackEnvironment
from mav.Tasks.slack.task_suite import slack_task_suite as task_suite
from mav.items import FunctionCall

SlackExhaustionTask = BaseAttackTask[SlackEnvironment]

task_suite.register_task_type('exhaustion', 'ExhaustionTask')

# @task_suite.register_user_task('exhaustion')
# class ExhaustionTask0(SlackExhaustionTask):
#     """
   
#     """
    

# @task_suite.register_user_task('exhaustion')
# class ExhaustionTask1(SlackExhaustionTask):
#     """
    
#     """


# @task_suite.register_user_task('exhaustion')
# class ExhaustionTask2(SlackExhaustionTask):
#     """
    
#     """
    

# @task_suite.register_user_task('exhaustion')
# class ExhaustionTask3(SlackExhaustionTask):
#     """
    
#     """