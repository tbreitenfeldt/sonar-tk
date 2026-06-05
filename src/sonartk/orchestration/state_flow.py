from __future__ import annotations

from typing import Mapping, Protocol

from sonartk.util.state import State


class _WindowStateRegistry(Protocol):
    def add(self, key: str, state: State) -> None: ...

    def set_start_state(self, key: str) -> None: ...


class WindowStateFlow:
    """Fluent helper for registering keyed states on a window."""

    def __init__(self, window: _WindowStateRegistry) -> None:
        self.window = window

    def add(self, key: str, state: State) -> WindowStateFlow:
        """Register a state under a key."""
        self.window.add(key, state)
        return self

    def add_many(self, states_by_key: Mapping[str, State]) -> WindowStateFlow:
        """Register multiple keyed states."""
        for key, state in states_by_key.items():
            self.window.add(key, state)
        return self

    def start_at(self, key: str) -> WindowStateFlow:
        """Configure the start state key."""
        self.window.set_start_state(key)
        return self
