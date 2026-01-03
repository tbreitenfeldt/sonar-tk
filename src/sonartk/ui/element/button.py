from __future__ import annotations

from typing import TYPE_CHECKING, Callable, List

from pyglet.window import key

from sonartk.ui.element.element import Element
from sonartk.util import speech_manager

if TYPE_CHECKING:
    from sonartk.ui.screen.screen import Screen


class Button(Element[str]):
    def __init__(self, parent: Element | Screen, label: str) -> None:
        super().__init__(
            parent=parent, label=label, value=label, role="button"
        )

    # override
    def bind_keys(self) -> None:
        self.key_handler.add_key_press(self.submit, key.RETURN)
        self.key_handler.add_key_press(self.submit, key.SPACE)

    def submit(self) -> bool:
        self.dispatch_event("on_submit", self)
        return True

    # override
    def reset(self) -> None:
        pass


Button.register_event_type("on_submit")
