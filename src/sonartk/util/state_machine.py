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
        self.current_index: int = 0
        self._start_state_key: Optional[str] = None
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
            if self._start_state_key == key:
                self._start_state_key = None
            if self.current_index >= len(self.keys):
                self.current_index = max(0, len(self.keys) - 1)
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
        self.current_index = 0
        self._start_state_key = None
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

    def set_current_index(self, index: int) -> None:
        """Set the selection index used by activate_current_state."""
        self.current_index = index

    def set_start_state_key(self, key: str) -> None:
        """Set a preferred state key used by activate_current_state."""
        if key == "":
            raise ValueError("Start state key cannot be empty")

        if not self.is_empty() and not self.contains(key):
            raise KeyError(
                f"State '{key}' not in state machine. "
                f"Available states: {list(self.states.keys())}"
            )

        self._start_state_key = key

    def clear_start_state_key(self) -> None:
        """Clear any preferred start state key."""
        self._start_state_key = None

    def activate_current_state(self, *args: Any, **kwargs: Any) -> None:
        """Activate selected state using start key first, then current index."""
        if self.is_empty():
            return

        if self._start_state_key is not None:
            if not self.contains(self._start_state_key):
                raise KeyError(
                    f"State '{self._start_state_key}' not in state machine. "
                    f"Available states: {list(self.states.keys())}"
                )
            key = self._start_state_key
        else:
            if self.current_index < 0 or self.current_index >= len(self.keys):
                raise IndexError(
                    "Current index is out of range for the current "
                    "state machine keys"
                )
            key = self.keys[self.current_index]

        self.transition_to(key, *args, **kwargs)

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

    def transition_to(self, key: str, *args: Any, **kwargs: Any) -> None:
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
                if next_state.setup(self.transition_to, *args, **kwargs):
                    self.current_state = next_state
                    if self._transition_callback:
                        self._transition_callback(key)
            finally:
                self._pending_state = None

    def setup(self, *args: Any, **kwargs: Any) -> bool:
        """Run setup on the current active state."""
        return self.current_state.setup(self.transition_to, *args, **kwargs)

    def update(self, delta_time: float) -> bool:
        """Run one update tick on the current active state."""
        return self.current_state.update(delta_time)

    def exit(self) -> bool:
        """Run exit on the current active state."""
        return self.current_state.exit()
