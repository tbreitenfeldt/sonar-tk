from __future__ import annotations

from typing import TYPE_CHECKING

from pyglet.window import key

from sonartk.ui.element.element import Element
from sonartk.util import speech_manager

if TYPE_CHECKING:
    from sonartk.ui.screen.screen import Screen


class Checkbox(Element[bool]):
    def __init__(
        self, parent: Element | Screen, label: str = "", value: bool = False
    ) -> None:
        super().__init__(
            parent=parent, label=label, value=value, role="checkbox"
        )
        self.default_value: bool = value

    # override
    def bind_keys(self) -> None:
        """Bind keys."""
        self.key_handler.add_key_press(self.toggle_state, key.RETURN)
        self.key_handler.add_key_press(self.toggle_state, key.SPACE)

    def toggle_state(self) -> bool:
        """Toggle state."""
        self.value = not self.value
        self.dispatch_event("on_change", self)

        if self.value:
            self.dispatch_event("on_checked", self)
        else:
            self.dispatch_event("on_unchecked", self)

        output_value: str = "Checked" if self.value else "Unchecked"
        speech_manager.output(output_value, interrupt=True, log_message=False)
        return True

    # override
    def reset(self) -> None:
        """Reset."""
        self.value = self.default_value

    # override
    @property
    def name(self) -> str:
        """Return the name."""
        output_value: str = "Checked" if self.value else "Unchecked"
        return f"{self.label} {self.role} {output_value}"


Checkbox.register_event_type("on_change")
Checkbox.register_event_type("on_checked")
Checkbox.register_event_type("on_unchecked")
