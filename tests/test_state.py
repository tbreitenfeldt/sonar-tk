from typing import Callable

from state import State

class TestState(State):

    def __init__(self, setup_value: bool = True, update_value: bool = True, exit_value: bool = True) -> None:
        self.setup_value: bool = setup_value
        self.update_value: bool = update_value
        self.exit_value: bool = exit_value

    def setup(self, change_state: Callable[[str, any], None], setup_value: bool = None, update_value: bool = None, exit_value: bool = None) -> bool:
        self.setup_value = setup_value if setup_value is not None else self.setup_value
        self.update_value = update_value if update_value is not None else self.update_value
        self.exit_value = exit_value if exit_value is not None else self.exit_value
        return self.setup_value

    def update(self, delta_time: float) -> bool:
        return self.update_value

    def exit(self) -> bool:
        return self.exit_value
