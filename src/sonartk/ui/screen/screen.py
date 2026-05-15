from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Optional, Protocol

from pyglet.event import EventDispatcher

from sonartk.ui.element.element import Element
from sonartk.ui.ui_component import UIComponent
from sonartk.util.state import State
from sonartk.util.state_machine import StateMachine
from sonartk.util.key_handler import KeyHandler

if TYPE_CHECKING:  # pragma: no cover
    from sonartk.ui.window import Window

    class HasCaption(Protocol):
        @property
        def caption(self) -> str: ...

        @caption.setter
        def caption(self, value: str) -> None: ...


class Screen(UIComponent, State, EventDispatcher):
    def __init__(self, parent: Window | Screen) -> None:
        self.parent: HasCaption = parent  # type: ignore[assignment]
        self.position: int = 0
        self.state_machine: StateMachine = StateMachine()
        self.key_handler: KeyHandler = KeyHandler()
        self.bind_keys()

    def close(self) -> bool:
        """Emit the close event for this screen."""
        self.dispatch_event("on_close", self)
        return True

    def add(self, key: str, element: Element | Screen) -> None:
        """Register an element or nested screen in this screen state machine."""
        self.state_machine.add(key, element)

    def remove(self, key: str) -> Optional[State]:
        """Remove and return an element state by key when present."""
        return self.state_machine.remove(key)

    def next_element(self) -> bool:
        """Move focus to the next element and activate it."""
        self.dispatch_event("on_next_element", self)
        if self.state_machine.size() > 0:
            if self.state_machine.size() > 1:
                self.position = (self.position + 1) % self.state_machine.size()
            self.set_state()
            return True
        return False

    def previous_element(self) -> bool:
        """Move focus to the previous element and activate it."""
        self.dispatch_event("on_previous_element", self)
        if self.state_machine.size() > 0:
            if self.state_machine.size() > 1:
                self.position = (self.position - 1) % self.state_machine.size()
            self.set_state()
            return True
        return False

    def set_state(self, interrupt_speech: bool = True) -> None:
        """Activate the element state at the current position."""
        if not self.state_machine.is_empty():
            state_key: str = self.state_machine.keys[self.position]
            self.state_machine.change(state_key, interrupt_speech)

    @abstractmethod
    def bind_keys(self) -> None:
        """Bind keyboard controls for screen-level navigation actions."""
        pass

    @property
    def caption(self) -> str:
        """Get or set the caption through the parent window."""
        return self.parent.caption

    @caption.setter
    def caption(self, caption: str) -> None:
        """Get or set the caption through the parent window."""
        self.parent.caption = caption

    @property
    def active_element(self) -> State:
        """Return the currently active child state."""
        return self.state_machine.current_state


Screen.register_event_type("on_next_element")
Screen.register_event_type("on_previous_element")
Screen.register_event_type("on_close")
