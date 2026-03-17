"""
Base node class for all deerflow graph nodes.

Provides common functionality like logging, error handling, and state management.
"""

from typing import Optional, TypedDict, Any
from ..state import DeerflowState, get_settings


class NodeResult(TypedDict):
    """Result returned by node execution."""
    status: str
    message: str
    data: dict[str, Any]


class BaseNode:
    """
    Base class for all graph nodes.

    Provides common functionality like logging, error handling,
    and state management.
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.settings = get_settings()

    async def execute(self, state: DeerflowState) -> DeerflowState:
        """
        Execute the node's main logic.

        Should be implemented by subclasses. This base method handles
        common error handling and state updates.
        """
        try:
            state = await self._execute(state)
            state.completed_nodes.append(self.node_id)
        except Exception as e:
            state.add_error(self.node_id, str(e))
            raise
        finally:
            state.update_timestamp()
        return state

    async def _execute(self, state: DeerflowState) -> DeerflowState:
        """Subclass implementation of node logic."""
        raise NotImplementedError("Subclasses must implement _execute method")

    def log(self, message: str, level: str = "INFO") -> None:
        """Log a message with node identifier."""
        print(f"[{self.node_id}] {level}: {message}")

    def get_data_provider(self) -> str:
        """Get the primary data provider to use."""
        return self.settings.get_primary_data_provider()
