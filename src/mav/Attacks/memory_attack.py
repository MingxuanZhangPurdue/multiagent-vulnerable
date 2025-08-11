import asyncio

from agents import (
    SQLiteSession
)
from typing import Literal

from mav.Attacks.attack import BaseAttack, AttackComponents

class MemoryAttack(BaseAttack):
    """A base class for memory-based attacks."""

    def __init__(self, method: Literal["pop", "clear", "add"]):
        self.method = method

    def attack(
        self,
        components: AttackComponents,
    ) -> None:
        memory = components.memory
        if self.method == "pop":
            self.pop_the_last_memory_item(memory)
        elif self.method == "clear":
            self.clear_memory(memory)
        else:
            raise ValueError("Invalid method specified. Supported methods are 'pop', 'clear', and 'add'")

    def pop_the_last_memory_item(memory: SQLiteSession) -> None:
        """
        Pop the last item from the memory.

        Args:
            memory (SQLiteSession): The memory session to pop an item from.
        """
        asyncio.run(memory.pop_item())

    def clear_memory(memory: SQLiteSession) -> None:
        """
        Clear the memory session.       
        Args:
            memory (SQLiteSession): The memory session to clear.
        """
        asyncio.run(memory.clear_session())