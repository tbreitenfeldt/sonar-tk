from typing import Any, Callable, Dict, Optional

from .state import State

TransitionCallback = Callable[[str], None]


class EmptyState(State):
    # override
    def setup(
        self,
        change_state: Callable[[str, Any], None],
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """Perform no-op setup for the empty placeholder state."""
        return True

    # override
    def update(self, delta_time: float) -> bool:
        """Perform no-op update for the empty placeholder state."""
        return True

    # override
    def exit(self) -> bool:
        """Perform no-op exit for the empty placeholder state."""
        return True


class StateMachine:
    def __init__(self) -> None:
        self.states: Dict[str, State] = {}
        self.current_state: State = EmptyState()
        self.keys: list[str] = []
        self._pending_state: Optional[State] = None
        self._transition_callback: Optional[TransitionCallback] = None

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
        self._pending_state = None

    def size(self) -> int:
        """Return the number of registered states."""
        return len(self.states)

    def is_empty(self) -> bool:
        """Return whether no states are currently registered."""
        return self.size() == 0

    def contains(self, key: str) -> bool:
        """Check if a state with the given key exists in the machine."""
        return key in self.states

    def set_transition_callback(
        self, callback: Optional[TransitionCallback]
    ) -> None:
        """Register a callback to be called after each successful state transition."""
        self._transition_callback = callback

    def get_debug_state(self) -> State:
        """Return the effective active state, including in-progress transitions."""
        if self._pending_state is not None:
            return self._pending_state
        return self.current_state

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
            self._pending_state = next_state
            try:
                if next_state.setup(self.change, *args, **kwargs):
                    self.current_state = next_state
                    if self._transition_callback:
                        self._transition_callback(key)
            finally:
                self._pending_state = None

    def setup(self, *args: Any, **kwargs: Any) -> bool:
        """Run setup on the current active state."""
        return self.current_state.setup(self.change, *args, **kwargs)

    def update(self, delta_time: float) -> bool:
        """Run one update tick on the current active state."""
        return self.current_state.update(delta_time)

    def exit(self) -> bool:
        """Run exit on the current active state."""
        return self.current_state.exit()
