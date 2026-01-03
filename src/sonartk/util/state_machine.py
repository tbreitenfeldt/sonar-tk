from typing import Any, Callable, Dict, Optional

from .state import State


class EmptyState(State):
    # override
    def setup(
        self,
        change_state: Callable[[str, Any], None],
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        return True

    # override
    def update(self, delta_time: float) -> bool:
        return True

    # override
    def exit(self) -> bool:
        return True


class StateMachine:
    def __init__(self) -> None:
        self.states: Dict[str, State] = {}
        self.current_state: State = EmptyState()
        self.keys: list[str] = []

    def add(self, key: str, state: State) -> None:
        """Add a state to the machine. Raises ValueError if key already exists."""
        if key is None or state is None:
            raise ValueError("Neither key or state can be None")
        if key in self.states:
            raise ValueError(
                f"State with key '{key}' already exists. "
                f"Remove it first or use a different key."
            )

        self.keys.append(key)
        state.state_key = key
        self.states[key] = state

    def remove(self, key: str) -> Optional[State]:
        """
        Remove a state from the machine.

        Warning: If removing the currently active state, you must manually call
        exit() and transition to another state first to ensure proper cleanup.
        This method does not automatically exit states.
        """
        if key in self.states:
            self.keys.remove(key)
            item: State = self.states[key]
            del self.states[key]
            return item

        return None

    def clear(self) -> None:
        """
        Remove all states from the machine.

        Warning: If the current state is not EmptyState, you must manually call
        exit() on it before clearing to ensure proper cleanup. This method does
        not automatically exit states.
        """
        self.states.clear()
        self.keys.clear()
        self.current_state = EmptyState()

    def size(self) -> int:
        return len(self.states)

    def is_empty(self) -> bool:
        return self.size() == 0

    def contains(self, key: str) -> bool:
        """Check if a state with the given key exists in the machine."""
        return key in self.states

    def change(self, key: str, *args: Any, **kwargs: Any) -> None:
        """
        Transition to a new state. Both exit() and setup() can conditionally prevent transitions.

        Changing to the current state will exit and re-setup that state (full refresh).
        """
        if key not in self.states:
            raise KeyError(
                f"State '{key}' not in state machine. "
                f"Available states: {list(self.states.keys())}"
            )

        next_state: State = self.states[key]

        if self.current_state.exit():
            if next_state.setup(self.change, *args, **kwargs):
                self.current_state = next_state

    def setup(self, *args: Any, **kwargs: Any) -> bool:
        return self.current_state.setup(self.change, *args, **kwargs)

    def update(self, delta_time: float) -> bool:
        return self.current_state.update(delta_time)

    def exit(self) -> bool:
        return self.current_state.exit()
