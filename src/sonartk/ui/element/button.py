from __future__ import annotations

from typing import TYPE_CHECKING

from pyglet.window import key

from sonartk.ui.element.element import Element

if TYPE_CHECKING:
    from sonartk.ui.screen.screen import Screen


class Button(Element[str]):
    def __init__(self, parent: Element | Screen, label: str) -> None:
        super().__init__(
            parent=parent, label=label, value=label, role="button"
        )

    # override
    def bind_keys(self) -> None:
        """Bind keys."""
        self.key_handler.add_key_press(self.submit, key.RETURN)
        self.key_handler.add_key_press(self.submit, key.SPACE)

    def submit(self) -> bool:
        """Submit."""
        self.dispatch_event("on_submit", self)
        return True

    # override
    def reset(self) -> None:
        """Reset."""
        pass


Button.register_event_type("on_submit")
