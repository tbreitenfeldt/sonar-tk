from __future__ import annotations

from abc import abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Optional,
    Self,
    TypeVar,
)

from pyglet.event import EventDispatcher

from audio_ui.utils.state import State
from audio_ui.utils import KeyHandler, speech_manager

if TYPE_CHECKING:
    from audio_ui.screens.screen import Screen

V = TypeVar("V")


class Element(Generic[V], State, EventDispatcher):
    def __init__(
        self,
        parent: Self | Screen,
        label: str,
        role: str,
        value: Optional[V],
        use_key_handler: bool = True,
    ) -> None:
        self.parent: Self | Screen = parent
        self.label: str = label
        self.role: str = role
        self._value: Optional[V] = value
        self.use_key_handler: bool = use_key_handler

        if self.use_key_handler:
            self.key_handler: KeyHandler = KeyHandler()

    def push_window_handlers(self, handler: KeyHandler) -> None:
        self.parent.push_window_handlers(handler)

    def pop_window_handlers(self) -> None:
        self.parent.pop_window_handlers()

    # override
    def setup(  # type: ignore[override]
        self,
        change_state: Callable[[str, Any], None],
        interrupt_speech: bool = False,
    ) -> bool:
        if self.label:
            speech_manager.output(
                self.name, interrupt=interrupt_speech, log_message=False
            )

        if self.use_key_handler:
            self.push_window_handlers(self.key_handler)

        self.dispatch_event("on_focus", self)
        return True

    # override
    def update(self, delta_time: float) -> bool:
        self.dispatch_event("on_update", self, delta_time)
        return True

    # override
    def exit(self) -> bool:
        self.dispatch_event("on_lose_focus", self)
        if self.use_key_handler:
            self.pop_window_handlers()

        return True

    @abstractmethod
    def reset(self) -> None:
        pass

    @property
    def value(self) -> Optional[V]:
        return self._value

    @value.setter
    def value(self, value: V) -> None:
        self._value = value

    @property
    def name(self) -> str:
        return f"{self.label} {self.role}"


Element.register_event_type("on_focus")
Element.register_event_type("on_lose_focus")
Element.register_event_type("on_update")
