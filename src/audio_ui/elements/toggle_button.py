from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, List

from pyglet.window import key

from audio_ui.elements.element import Element
from audio_ui.utils import speech_manager

if TYPE_CHECKING:
    from audio_ui.screens.screen import Screen


class ToggleButton(Element[str]):
    def __init__(
        self,
        parent: Screen,
        label: str = "",
        position: int = 0,
        items: List[str] = [],
    ) -> None:
        super().__init__(parent=parent, label=label, value="", role="toggle")
        self.items: List[str] = items
        self.position: int = position
        self.default_position: int = position
        self._bind_keys()

    def _bind_keys(self) -> None:
        self.key_handler.add_key_press(self.next, key.RETURN)
        self.key_handler.add_key_press(self.next, key.SPACE)

    # override
    def setup(  # type: ignore[override]
        self,
        change_state: Callable[[str, Any], None],
        interrupt_speech: bool = True,
    ) -> bool:
        super().setup(change_state, interrupt_speech)
        speech_manager.output(
            self.items[self.position], interrupt=False, log_message=False
        )
        return True

    def next(self) -> bool:
        self.position = (self.position + 1) % len(self.items)
        self.value = self.items[self.position]
        speech_manager.output(self.value, interrupt=True, log_message=False)
        self.dispatch_event("on_change", self)
        return True

    def add(self, item: str) -> None:
        self.items.append(item)

    # override
    def reset(self) -> None:
        self.position = self.default_position


ToggleButton.register_event_type("on_change")
