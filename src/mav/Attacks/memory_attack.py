import asyncio

from agents import (
    SQLiteSession
)
from typing import Any

from mav.Attacks.attack import BaseAttack, AttackComponents

class MemoryAttack(BaseAttack):
    """Memory-based attacks"""

    def __init__(self, attack_config: dict = None, eval_function = None, init_env_function = None):
        super().__init__(attack_config, eval_function)
        self.init_env_function = init_env_function
        # One-time init guard
        self._env_init_done = False

    def attack(self, components: AttackComponents) -> None:

        """
        config: {
            "method": Literal["pop", "clear", "add", "replace"], # default is "pop"
            "agents": list[str], # agent names to pop the last memory item, default are all agents
            "items_to_add": dict[str, list[dict[str, Any]]], # only used when method is "add", a mapping of agent names to a list of memory items to add
        }
        """
        
        # Initialize environment once if init function is provided
        if self.init_env_function is not None and not self._env_init_done:
            try:
                # Build a stable tag for this init function to de-duplicate across identical hooks
                init_tag = f"memory_attack_{id(self.init_env_function)}"
                self.init_env_function(components.env, init_tag)
                self._env_init_done = True
            except Exception as e:
                print(f"Warning: Environment initialization failed for MemoryAttack: {e}")

        method = self.attack_config.get("method", "pop")
        agents = self.attack_config.get("agents", list[components.agent_dict.keys()])
        if method == "pop":
            self.pop(components.memory_dict, agents)
        elif method == "clear":
            self.clear(components.memory_dict, agents)
        elif method == "add":
            items_to_add = self.attack_config["items_to_add"]
            self.add(components.memory_dict, items_to_add)
        elif method == "replace":
            items_to_add = self.attack_config["items_to_add"]
            self.replace(components.memory_dict, items_to_add)
        else:
            raise ValueError("Invalid method specified. Supported methods are 'pop', 'clear', 'replace', and 'add'")

    def pop(
        self, 
        memory_dict: dict[str, SQLiteSession], 
        agents: list[str]
    ) -> None:
        """
        Pop the last item from the memory for each target agent.
        """
        for agent in agents:
            asyncio.run(memory_dict[agent].pop_item())

    def clear(
        self, 
        memory_dict: dict[str, SQLiteSession], 
        agents: list[str]
    ) -> None:
        """
        Clear the memory session for each target agent.
        """
        for agent in agents:
            asyncio.run(memory_dict[agent].clear_session())

    def add(
        self, 
        memory_dict: dict[str, SQLiteSession], 
        items_to_add: dict[str, list[dict[str, Any]]]
    ) -> None:
        """
        Add new items to the memory for each target agent.
        """
        for agent_name, items in items_to_add.items():
            asyncio.run(memory_dict[agent_name].add_items(items))

    def replace(
        self, 
        memory_dict: dict[str, SQLiteSession], 
        items_to_add: dict[str, list[dict[str, Any]]]
    ) -> None:
        """
        Replace the memory for each target agent.
        it first clears the existing memory and then adds the new items.
        """
        self.clear(memory_dict, list(items_to_add.keys()))
        self.add(memory_dict, items_to_add)
