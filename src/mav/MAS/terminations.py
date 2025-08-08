from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union, Optional

class BaseTermination(ABC):
    @abstractmethod
    def __call__(self, iteration: int, results: List[Dict[str, Any]] | None) -> bool:
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

    def __call__(self, iteration: int, results: List[Dict[str, Any]] | None) -> bool:
        return all(condition(iteration, results) for condition in self.conditions)

class OrTermination(BaseTermination):
    """Termination condition that is met when at least one of the provided conditions is met.
    """
    def __init__(self, *conditions: BaseTermination):
        if not conditions:
            raise ValueError("At least one condition must be provided")
        self.conditions = conditions

    def __call__(self, iteration: int, results: List[Dict[str, Any]] | None) -> bool:
        return any(condition(iteration, results) for condition in self.conditions)

class MaxIterationsTermination(BaseTermination):
    """Termination condition that is met when the maximum number of iterations is reached.
    """
    def __init__(self, max_iterations: int):
        if max_iterations < 1:
            raise ValueError("max_iterations must be positive")
        self.max_iterations = max_iterations

    def __call__(self, iteration: int, results: List[Dict[str, Any]] | None) -> bool:
        return iteration >= self.max_iterations
    
class MessageTermination(BaseTermination):
    """Termination condition that is met when a specific message is found in the final output.
    """
    def __init__(self, termination_message: str):
        self.termination_message = termination_message
    
    def __call__(self, iteration: int, results: List[Dict[str, Any]] | None) -> bool:
        if results is None or not results:
            return False
        
        final_item = results[-1]
        
        if final_item.get("role") != "assistant":
            return False
            
        content = final_item.get("content")
        if isinstance(content, str):
            return self.termination_message in content
        elif isinstance(content, list):
            return any(
                item.get("type") == "output_text" 
                and self.termination_message in item.get("text", "")
                for item in content
            )
        
        return False