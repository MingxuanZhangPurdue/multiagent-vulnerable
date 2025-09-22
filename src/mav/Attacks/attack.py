from abc import ABC, abstractmethod
from typing import Any, Callable
from agents import Agent
from dataclasses import dataclass, field
from mav.Tasks.base_environment import TaskEnvironment
from agents import Session

@dataclass(slots=True)
class AttackComponents:
    
    # The input of the agent right before their turn, typically should be attacked at the "on the agent run start" event
    input: str | dict[str, str]

    # The final output of the agent right after their turn, typically should be attacked at the "on the agent run end" event
    final_output: Any

    # The task environment in which the agents are operating
    env: TaskEnvironment

    # The agent instances being used in the run, you can attack instructions, models, and tools for each agent
    agent_dict: dict[str, Agent] = field(default_factory=dict)

    # The memory session for each agent, it can be None for stateless agents
    memory_dict: dict[str, Session] = field(default_factory=dict)

class BaseAttack(ABC):

    def __init__(self, attack_config: dict[str, Any] = None, eval_function: Callable = None):
        self.attack_config = attack_config
        self.eval_function = eval_function
        # self.pre_environment = None
        # self.post_environment = None

    @abstractmethod
    async def attack(self, components: AttackComponents):
        pass

    def security(self, model_output, pre_environment, post_environment, args) -> bool:
        if self.eval_function is None:
            raise ValueError("Eval function is not set")
        
        # Check if we have both environments available
        if pre_environment is not None and post_environment is not None:
            # Call eval_function with the signature that matches your task security functions:
            # eval_function(model_output, pre_environment, post_environment, result)
            return self.eval_function(model_output, pre_environment, post_environment, args)
        else:
            # Environments are required for security evaluation
            raise ValueError(f"Both pre_environment and post_environment must be provided for security evaluation. Got pre_environment={pre_environment is not None}, post_environment={post_environment is not None}")

