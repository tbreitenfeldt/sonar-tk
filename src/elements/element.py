from typing import TypeVar, Generic, Callable, List 
from abc import abstractmethod

from state import State
from utils import audio_manager
from utils import speech_manager
from utils import KeyHandler

T = TypeVar("T")

class Element(Generic[T], State):

    def __init__(self, parent: State, title: str, value: T, type: str, callback: Callable[[Callable[[str, any], None], T, any], None],
        callback_args: List[any], use_key_handler: bool = True
    ) -> None:
        self.parent: "Tab" = parent
        self.title: str = title
        self._value: T = value
        self.type: str = type
        self.use_key_handler: bool = use_key_handler
        self.callback: Callable[[Callable[[str, any], None], any, any], None] = callback
        self.callback_args: List[any] = callback_args
        self.change_state: Callable[[str, any], None] = None

        if self.use_key_handler:
            self.key_handler: KeyHandler = KeyHandler()

    @property
    def value(self) -> T:
        return self._value

    @value.setter
    def value(self, value) -> None:
        self._value = value

    def setup(self, change_state: Callable[[str, any], None], interrupt_speech=False) -> bool:
        self.change_state = change_state

        if self.title:
            speech_manager.output(self.title + " " + self.type, interrupt=interrupt_speech, log_message=False)

        if self.use_key_handler:
            self.push_handlers(self.key_handler)

        return True

    def update(self, delta_time: float) -> bool:
        return True

    def exit(self) -> bool:
        if self.use_key_handler:
            self.pop_handlers()

        return True

    def submit(self, * args, **kwargs) -> None:
        if self.callback:
            self.callback(self.change_state, self.value, *self.callback_args)

        return self.on_action(*args, **kwargs)

    @abstractmethod
    def on_action(self, *args, **kwargs) -> bool:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass

    def push_handlers(self, handler: KeyHandler) -> None:
        self.parent.push_handlers(handler)

    def pop_handlers(self) -> None:
        self.parent.pop_handlers()
