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

    def add(self, key: str, state: State) -> None:
        if key is None or state is None:
            raise ValueError("Neither key or state can be None")

        state.state_key = key
        self.states[key] = state

    def remove(self, key: str) -> Optional[State]:
        if key in self.states:
            item: State = self.states[key]
            del self.states[key]
            return item

        return None

    def clear(self) -> None:
        self.states.clear()

    def size(self) -> int:
        return len(self.states)

    def is_empty(self) -> bool:
        return self.size() == 0

    def change(self, key: str, *args: Any, **kwargs: Any) -> None:
        if self.current_state.exit():
            next_state: State = self.states[key]
            if next_state.setup(self.change, *args, **kwargs):
                self.current_state = next_state

    def setup(self, *args: Any, **kwargs: Any) -> bool:
        return self.current_state.setup(self.change, *args, **kwargs)

    def update(self, delta_time: float) -> bool:
        return self.current_state.update(delta_time)

    def exit(self) -> bool:
        return self.current_state.exit()
