from typing import Callable

from audio_ui import State

class MockState(State):

    def __init__(self, setup_value: bool = True, update_value: bool = True, exit_value: bool = True) -> None:
        self.setup_value: bool = setup_value
        self.update_value: bool = update_value
        self.exit_value: bool = exit_value

    def setup(self, change_state: Callable[[str, any], None], setup_value: bool = None) -> bool:
        return self.setup_value

    def update(self, delta_time: float) -> bool:
        return self.update_value

    def exit(self) -> bool:
        return self.exit_value
