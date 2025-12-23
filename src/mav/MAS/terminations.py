from abc import ABC, abstractmethod
from typing import Any
from mav.Tasks.base_environment import TaskEnvironment

class BaseTermination(ABC):
    @abstractmethod
    def __call__(self, 
        iteration: int | None = None, 
        input_items_dict: dict[str, list[list[dict[str, Any]]]] | None = None,
        tool_calls_dict: dict[str, list[list[dict[str, Any]]]] | None = None,
        output_dict: dict[str, list[Any]] | None = None,
        env: TaskEnvironment | None = None
    ) -> bool:
        """Check if the termination condition is met.
        Returns:
            bool: True if the termination condition is met, False otherwise.
        """
        pass

class AndTermination(BaseTermination):
    """Termination condition that is met when all provided conditions are met.
    """
    def __init__(self, *conditions: BaseTermination):
        if not conditions:
            raise ValueError("At least one condition must be provided")
        self.conditions = conditions

    def __call__(self, 
        iteration: int | None = None, 
        input_items_dict: dict[str, list[list[dict[str, Any]]]] | None = None,
        tool_calls_dict: dict[str, list[list[dict[str, Any]]]] | None = None,
        output_dict: dict[str, list[Any]] | None = None,
        env: TaskEnvironment | None = None
    ) -> bool:
        return all(condition(iteration, input_items_dict, tool_calls_dict, output_dict, env) for condition in self.conditions)

class OrTermination(BaseTermination):
    """Termination condition that is met when at least one of the provided conditions is met.
    """
    def __init__(self, *conditions: BaseTermination):
        if not conditions:
            raise ValueError("At least one condition must be provided")
        self.conditions = conditions

    def __call__(self, 
        iteration: int | None = None, 
        input_items_dict: dict[str, list[list[dict[str, Any]]]] | None = None,
        tool_calls_dict: dict[str, list[list[dict[str, Any]]]] | None = None,
        output_dict: dict[str, list[Any]] | None = None,
        env: TaskEnvironment | None = None
    ) -> bool:
        return any(condition(iteration, input_items_dict, tool_calls_dict, output_dict, env) for condition in self.conditions)

class MaxIterationsTermination(BaseTermination):
    """Termination condition that is met when the maximum number of iterations is reached.
    """
    def __init__(self, max_iterations: int):
        if max_iterations < 1:
            raise ValueError("max_iterations must be positive")
        self.max_iterations = max_iterations

    def __call__(self, 
        iteration: int | None = None, 
        input_items_dict: dict[str, list[list[dict[str, Any]]]] | None = None,
        tool_calls_dict: dict[str, list[list[dict[str, Any]]]] | None = None,
        output_dict: dict[str, list[Any]] | None = None,
        env: TaskEnvironment | None = None
    ) -> bool:
        if iteration is None:
            raise ValueError("iteration must be provided for MaxIterationsTermination check")
        return iteration >= self.max_iterations
    
class PlannerExecutorMessageTerminiation(BaseTermination):
    """
    A termination condition based on specific messages in the planner-executor framework. It will terminate if a specified message is found in the latest output of the planner agent.
    """
    def __init__(self, termination_message: str):
        self.termination_message = termination_message
    
    def __call__(self, 
        iteration: int | None = None, 
        input_items_dict: dict[str, list[list[dict[str, Any]]]] | None = None,
        tool_calls_dict: dict[str, list[list[dict[str, Any]]]] | None = None,
        output_dict: dict[str, list[Any]] | None = None,
        env: TaskEnvironment | None = None
    ) -> bool:
        
        if output_dict is None or "planner" not in output_dict:
            raise ValueError("Output dictionary must contain 'planner' outputs for PlannerExecutorMessageTermination")
        
        latest_output = output_dict["planner"][-1]
        if isinstance(latest_output, str) and self.termination_message in latest_output:
            return True
        return False
    
# class WebAgentTermination(BaseTermination):
#     """
#     A specialized termination condition for web agents.
#     """
#     def __init__(self, termination_message: str):
#         self.termination_message = termination_message
    
#     def __call__(self, 
#         iteration: int | None = None, 
#         results: List[Dict[str, Any]] | None = None, 
#         env: TaskEnvironment | None = None
#     ) -> bool:
        
#         if env is None:
#             raise ValueError("A valid TaskEnvironment must be provided for WebAgentTermination")
        
#         if env.trajectory[-1]["action_type"] == ActionTypes.STOP:
#             return True
#         return False
