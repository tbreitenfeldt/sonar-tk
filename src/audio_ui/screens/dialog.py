from __future__ import annotations

from typing import Any, Callable, cast, TYPE_CHECKING

from pyglet import clock
from pyglet.window import key

from audio_ui.elements.element import Element
from audio_ui.screens.screen import Screen
from audio_ui.utils.state_machine import EmptyState
from audio_ui.utils.key_handler import KeyHandler
from audio_ui.utils import speech_manager

if TYPE_CHECKING:
    from audio_ui.screens.container_screen import ContainerScreen


class Dialog(Screen):
    def __init__(self, parent: ContainerScreen) -> None:
        super().__init__(parent)
        self.original_caption: str = ""
        self.original_state_key: str = ""

    def open_dialog(self, caption: str) -> None:
        self.original_state_key = (
            self.parent.state_machine.current_state.state_key
        )
        count: int = self.parent.state_machine.size() + 1
        self.parent.add(f"dialog-{caption}-{count}", self)
        self.original_caption = self.caption
        self.caption = caption + " Dialog"
        clock.schedule_once(
            lambda dt: self.parent.state_machine.change(self.state_key), 0.3
        )

    # override
    def bind_keys(self) -> None:
        self.key_handler.add_key_press(self.close, key.ESCAPE)
        self.key_handler.add_key_press(self.next_element, key.TAB)
        self.key_handler.add_key_press(
            self.previous_element, key.TAB, [key.MOD_SHIFT]
        )

    # override
    def setup(
        self,
        change_state: Callable[[str, Any], None],
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        self.push_window_handlers(self.key_handler)
        self.set_state(interrupt_speech=False)
        return True

    # override
    def update(self, delta_time: float) -> bool:
        return self.state_machine.update(delta_time)

    # override
    def exit(self) -> bool:
        if not self.state_machine.is_empty():
            self.state_machine.exit()

        self.pop_window_handlers()
        return True

    # override
    def reset(self) -> None:
        for state in self.state_machine.states.values():
            element: Element = cast(Element, state)
            element.reset()

    # override
    def close(self) -> bool:
        super().close()
        self.position = 0
        self.reset()
        self.caption = self.original_caption
        clock.schedule_once(lambda db: self._reset_states(), 0.3)
        return True

    def _reset_states(self) -> None:
        self.parent.remove(self.state_key)
        self.state_machine.current_state = EmptyState()
        self.exit()
        self.parent.state_machine.change(self.original_state_key, False)
