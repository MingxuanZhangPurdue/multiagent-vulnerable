from typing import Any

class BaseSession:
    """Custom session implementation following the Session protocol."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        # Your initialization here

    async def get_items(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Retrieve conversation history for this session."""
        # Your implementation here
        pass

    async def add_items(self, items: list[dict[str, Any]]) -> None:
        """Store new items for this session."""
        # Your implementation here
        pass

    async def pop_item(self) -> dict[str, Any] | None:
        """Remove and return the most recent item from this session."""
        # Your implementation here
        pass

    async def clear_session(self) -> None:
        """Clear all items for this session."""
        # Your implementation here
        pass

    async def get_copy_of_items(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Retrieve a copy of the conversation history for this session."""

class InMemorySession(BaseSession):
    """In-memory session implementation."""

    def __init__(self, session_id: str):
        super().__init__(session_id)
        self.items: list[dict[str, Any]] = []

    async def get_items(self, limit: int | None = None) -> list[dict[str, Any]]:
        if limit is not None and limit < len(self.items):
            return self.items[-limit:]
        return self.items

    async def add_items(self, items: list[dict[str, Any]]) -> None:
        self.items.extend(items)

    async def pop_item(self) -> dict[str, Any] | None:
        if self.items:
            return self.items.pop()
        return None

    async def clear_session(self) -> None:
        self.items = []

    async def get_copy_of_items(self, limit: int | None = None) -> list[dict[str, Any]]:
        if limit is not None and limit < len(self.items):
            return self.items[-limit:].copy()
        return self.items.copy()
        