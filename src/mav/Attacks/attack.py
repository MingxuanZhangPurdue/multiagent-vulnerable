from abc import ABC, abstractmethod
from typing import Any, Callable
from agents import Agent
from dataclasses import dataclass, field
from agents import FunctionTool
from litellm import BaseModel, Field
from mav.Tasks.base_environment import TaskEnvironment
from agents import Session
@dataclass(slots=True)
class AttackComponents:
    input: Any
    env: TaskEnvironment
    agent_dict: dict[str, Agent] = field(default_factory=dict)
    memory_dict: dict[str, Session] = field(default_factory=dict)

class BaseAttack(ABC):

    def __init__(self, attack_config: dict[str, Any] = None):
        self.attack_config = attack_config

    @abstractmethod
    async def attack(self, components: AttackComponents):
        pass
