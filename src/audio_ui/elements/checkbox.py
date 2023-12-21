from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from pyglet.window import key

from audio_ui.elements.element import Element
from audio_ui.utils import speech_manager

if TYPE_CHECKING:
    from audio_ui.screens.screen import Screen


class Checkbox(Element[bool]):
    def __init__(
        self, parent: Element | Screen, label: str = "", value: bool = False
    ) -> None:
        super().__init__(
            parent=parent, label=label, value=value, role="checkbox"
        )
        self.default_value: bool = value
        self._bind_keys()

    def _bind_keys(self) -> None:
        self.key_handler.add_key_press(self.toggle_state, key.RETURN)
        self.key_handler.add_key_press(self.toggle_state, key.SPACE)

    def toggle_state(self) -> bool:
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
        self.value = self.default_value

    # override
    @property
    def name(self) -> str:
        output_value: str = "Checked" if self.value else "Unchecked"
        return f"{self.label} {self.role} {output_value}"


Checkbox.register_event_type("on_change")
Checkbox.register_event_type("on_checked")
Checkbox.register_event_type("on_unchecked")
