import asyncio

from agents import (
    SQLiteSession
)
from typing import Literal

from mav.Attacks.attack import BaseAttack

class MemoryAttack(BaseAttack):
    """A base class for memory-based attacks."""

    def __init__(self):
        pass

    def attack(
        self, 
        memory: SQLiteSession,
        method: Literal["pop", "clear", "add"],
        items: list[dict] | None = None
    ) -> None:
        if method == "pop":
            self.pop_the_last_memory_item(memory)
        elif method == "clear":
            self.clear_memory(memory)
        elif method == "add":
            if items is None:
                raise ValueError("Items must be provided for 'add' method")
            self.add_items(memory, items)
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

    def add_items(memory: SQLiteSession, items: list[dict]) -> None:
        """
        Add items to the memory session.

        Args:
            memory (SQLiteSession): The memory session to add items to.
            items (list[dict]): The items to add.
        """
        asyncio.run(memory.add_items(items))