from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

import pyglet
from pyglet.window import key

from audio_ui.screens.screen import Screen

if TYPE_CHECKING:
    from audio_ui.window import Window


class ContainerScreen(Screen):
    def __init__(self, parent: Window) -> None:
        super().__init__(parent)

    # Override
    def bind_keys(self) -> None:
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
    def close(self) -> bool:
        super().close()
        self.parent.close()
        return True
