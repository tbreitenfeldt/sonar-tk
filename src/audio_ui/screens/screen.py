from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Optional, Self

from pyglet.event import EventDispatcher

from audio_ui.elements.element import Element
from audio_ui.utils.state import State
from audio_ui.utils.state_machine import EmptyState, StateMachine
from audio_ui.utils.key_handler import KeyHandler

if TYPE_CHECKING:
    from audio_ui.window import Window


class Screen(State, EventDispatcher):
    def __init__(self, parent: Window | Self) -> None:
        self.parent: Window | Screen = parent
        self.position: int = 0
        self.state_machine: StateMachine = StateMachine()
        self.key_handler: KeyHandler = KeyHandler()
        self.bind_keys()

    def close(self) -> bool:
        self.dispatch_event("on_close", self)
        return True

    def add(self, key: str, element: Element) -> None:
        self.state_machine.add(key, element)

    def remove(self, key: str) -> Optional[State]:
        return self.state_machine.remove(key)

    def next_element(self) -> bool:
        self.dispatch_event("on_next_element", self)
        if self.state_machine.size() > 1:
            self.position = (self.position + 1) % self.state_machine.size()
            self.set_state()
            return True
        elif self.state_machine.size() == 1:
            self.set_state()
            return True

        return False

    def previous_element(self) -> bool:
        self.dispatch_event("on_previous_element", self)
        if self.state_machine.size() > 1:
            self.position = (self.position - 1) % self.state_machine.size()
            self.set_state()
            return True
        elif self.state_machine.size() == 1:
            self.set_state()
            return True

        return False

    def set_state(self, interrupt_speech: bool = True) -> None:
        if not self.state_machine.is_empty():
            state_key: str = list(self.state_machine.states)[self.position]
            self.state_machine.change(state_key, interrupt_speech)

    def push_window_handlers(self, handler: KeyHandler) -> None:
        self.parent.push_window_handlers(handler)

    def pop_window_handlers(self) -> None:
        self.parent.pop_window_handlers()

    @abstractmethod
    def bind_keys(self) -> None:
        pass

    @property
    def caption(self) -> str:
        return self.parent.caption

    @caption.setter
    def caption(self, caption: str) -> None:
        self.parent.caption = caption

    @property
    def active_element(self) -> State:
        return self.state_machine.current_state


Screen.register_event_type("on_next_element")
Screen.register_event_type("on_previous_element")
Screen.register_event_type("on_close")
