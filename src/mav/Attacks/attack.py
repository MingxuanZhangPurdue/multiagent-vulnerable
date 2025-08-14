from abc import ABC, abstractmethod
from typing import Any
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

    def __init__(self, attack_config: dict[str, Any] = None):
        self.attack_config = attack_config

    @abstractmethod
    async def attack(self, components: AttackComponents):
        pass
