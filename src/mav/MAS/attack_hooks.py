from typing import Callable
from agents import Agent
from mav.Tasks.base_environment import TaskEnvironment
from mav.Attacks import AttackComponents

class AttackHooks:

    def __init__(
        self,
        attacks: dict[str, list[Callable]] = {}
    ):
        self.attacks = attacks

    """
    Supported events:
    - on_run_start
    """

    async def execute_attacks(self, event_name: str, components: AttackComponents):
        attacks_to_run = self.attacks.get(event_name, [])
        for attack in attacks_to_run:
            await attack(components)
