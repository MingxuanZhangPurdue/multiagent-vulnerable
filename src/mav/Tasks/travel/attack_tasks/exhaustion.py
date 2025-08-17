from typing import ClassVar
from mav.Tasks.base_tasks import BaseAttackTask, TaskDifficulty
from typing import ClassVar
from mav.Tasks.base_tasks import BaseAttackTask, TaskDifficulty
from mav.Tasks.Travel.task_suite import TravelEnvironment
from mav.Tasks.Travel.task_suite import Travel_task_suite as task_suite
from mav.items import FunctionCall

TravelExhaustionTask = BaseAttackTask[TravelEnvironment]

task_suite.register_task_type('exhaustion', 'ExhaustionTask')

@task_suite.register_user_task('exhaustion')
class ExhaustionTask0(TravelExhaustionTask):
    """
    
    """
    

@task_suite.register_user_task('exhaustion')
class ExhaustionTask1(TravelExhaustionTask):
    """
    
    """


@task_suite.register_user_task('exhaustion')
class ExhaustionTask2(TravelExhaustionTask):
    """
    
    """
    _
    

@task_suite.register_user_task('exhaustion')
class ExhaustionTask3(TravelExhaustionTask):
    """
    
    """
    