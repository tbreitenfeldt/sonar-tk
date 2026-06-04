from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Optional, Protocol, cast

from pyglet.event import EventDispatcher

from sonartk.ui.element.element import Element
from sonartk.ui.ui_component import UIComponent
from sonartk.util.state import State
from sonartk.util.state_machine import StateMachine
from sonartk.util.key_handler import KeyHandler


class HasCaption(Protocol):
    @property
    def caption(self) -> str: ...

    @caption.setter
    def caption(self, value: str) -> None: ...


if TYPE_CHECKING:  # pragma: no cover
    from sonartk.ui.window import Window


class Screen(UIComponent, State, EventDispatcher):
    def __init__(self, parent: Window | Screen) -> None:
        super().__init__(parent)
        self.position: int = 0
        self.state_machine: StateMachine = StateMachine()
        self.state_machine.set_current_index(self.position)
        self.key_handler: KeyHandler = KeyHandler()
        self.bind_keys()

        # Register transition callback so nested state changes are logged
        window = self.get_window()
        if hasattr(window, "debug_mode") and window.debug_mode:
            self.state_machine.set_transition_callback(
                self._on_child_state_transition
            )

    def _on_child_state_transition(self, state_key: str) -> None:
        """Callback for logging child element state transitions."""
        window = self.get_window()
        if hasattr(window, "debug_mode") and window.debug_mode:
            is_valid, message = window.validate_handler_stack()
            if hasattr(window, "_debug_log"):
                window._debug_log(
                    f"after screen '{self.state_key}' change('{state_key}'): {message}"
                )

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
            self.activate_current_state()
            return True
        return False

    def previous_element(self) -> bool:
        """Move focus to the previous element and activate it."""
        self.dispatch_event("on_previous_element", self)
        if self.state_machine.size() > 0:
            if self.state_machine.size() > 1:
                self.position = (self.position - 1) % self.state_machine.size()
            self.activate_current_state()
            return True
        return False

    def activate_current_state(self, *args: Any, **kwargs: Any) -> None:
        """Activate the element state at the current position."""
        self.state_machine.set_current_index(self.position)
        self.state_machine.activate_current_state(*args, **kwargs)

    @abstractmethod
    def bind_keys(self) -> None:
        """Bind keyboard controls for screen-level navigation actions."""
        pass

    @property
    def caption(self) -> str:
        """Get or set the caption through the parent window."""
        parent = cast(HasCaption, self.parent)
        return parent.caption

    @caption.setter
    def caption(self, caption: str) -> None:
        """Get or set the caption through the parent window."""
        parent = cast(HasCaption, self.parent)
        parent.caption = caption

    @property
    def active_element(self) -> State:
        """Return the currently active child state."""
        return self.state_machine.current_state


Screen.register_event_type("on_next_element")
Screen.register_event_type("on_previous_element")
Screen.register_event_type("on_close")
