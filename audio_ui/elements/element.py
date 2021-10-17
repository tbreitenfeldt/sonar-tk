from typing import TypeVar, Generic, Callable
from abc import abstractmethod

from pyglet.event import EventDispatcher

from audio_ui.state import State
from audio_ui.utils import speech_manager
from audio_ui.utils import KeyHandler

T = TypeVar("T")

class Element(Generic[T], State, EventDispatcher):

    def __init__(self, parent: State, title: str, value: T, type: str, use_key_handler: bool = True) -> None:
        self.parent: State = parent
        self.title: str = title
        self._value: T = value
        self.type: str = type
        self.use_key_handler: bool = use_key_handler
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
            self.push_window_handlers(self.key_handler)

        self.dispatch_event("on_focus", self)
        return True

    def update(self, delta_time: float) -> bool:
        self.dispatch_event("on_update", self, delta_time)
        return True

    def exit(self) -> bool:
        self.dispatch_event("on_lose_focus", self)
        if self.use_key_handler:
            self.pop_window_handlers()

        return True

    @abstractmethod
    def reset(self) -> None:
        pass

    def push_window_handlers(self, handler: KeyHandler) -> None:
        self.parent.push_window_handlers(handler)

    def pop_window_handlers(self) -> None:
        self.parent.pop_window_handlers()

Element.register_event_type("on_focus")
Element.register_event_type("on_lose_focus")
Element.register_event_type("on_update")
