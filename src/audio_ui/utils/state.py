from abc import ABC, abstractmethod
from typing import Callable


class State(ABC):
    def __init__(self) -> None:
        self.state_key: str = ""

    @abstractmethod
    def setup(
        self, change_state: Callable[[str, any], None], *args, **kwargs
    ) -> bool:
        """This method is called once when the state changes to initialize the  state before the state starts running. False is returned if this state can not be entered."""

    @abstractmethod
    def update(self, delta_time: float) -> bool:
        """This gets called every frame when the state is active, used to update the innerworkings of the state. This method also returns a boolean to signify it is time to shutdown the system if False."""

    @abstractmethod
    def exit(self) -> bool:
        """This method is called once when the state changes, just before the new state is initialized, before the state switch. False is returned if this state cannot be exited."""
