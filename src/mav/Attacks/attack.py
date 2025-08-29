from abc import ABC, abstractmethod
from typing import Any, Callable
from agents import Agent
from dataclasses import dataclass, field
from mav.Tasks.base_environment import TaskEnvironment
from agents import Session

@dataclass(slots=True)
class AttackComponents:
    
    # The input of the agent right before their turn, typically should be attacked at the "on the agent run start" event
    input: str

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
        self.pre_environment = None
        self.post_environment = None

    @abstractmethod
    async def attack(self, components: AttackComponents):
        pass
    
    def capture_pre_environment(self, components: AttackComponents):
        """Call this before attack to capture pre-attack environment state"""
        import copy
        self.pre_environment = copy.deepcopy(components.env)
        msg = "📸 Captured pre-attack environment state"
        print(msg)
        # Note: logger not available in base class, just print for now
    
    def capture_post_environment(self, components: AttackComponents):
        """Call this after execution to capture post-attack environment state"""
        import copy
        self.post_environment = copy.deepcopy(components.env)
        msg = "📸 Captured post-attack environment state"
        print(msg)
        # Note: logger not available in base class, just print for now

    def security(self, args) -> bool:
        if self.eval_function is None:
            raise ValueError("Eval function is not set")
        
        # Extract model_output from args (the result from benchmark_suite)
        model_output = args.get('final_output', '') if args else ''
        
        # Check if we have both environments available
        if self.pre_environment is not None and self.post_environment is not None:
            # Call eval_function with the signature that matches your task security functions:
            # eval_function(model_output, pre_environment, post_environment, result)
            return self.eval_function(model_output, self.pre_environment, self.post_environment, args)
        else:
            # Environments are required for security evaluation
            raise ValueError(f"Both pre_environment and post_environment must be provided for security evaluation. Got pre_environment={self.pre_environment is not None}, post_environment={self.post_environment is not None}")

