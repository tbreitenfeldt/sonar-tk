from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

import pyglet
from pyglet.window import key

from sonartk.ui.screen.screen import Screen

if TYPE_CHECKING:
    from sonartk.ui.window import Window


class ContainerScreen(Screen):
    def __init__(self, parent: Window | Screen) -> None:
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
        self.get_window().push_window_handlers(self.key_handler)
        self.set_state(interrupt_speech=False)
        return True

    # override
    def set_state(self, interrupt_speech: bool = True) -> None:
        """Set the current element state."""
        if not self.state_machine.is_empty():
            state_key: str = self.state_machine.keys[self.position]
            self.state_machine.change(state_key, interrupt_speech)

    # override
    def update(self, delta_time: float) -> bool:
        return self.state_machine.update(delta_time)

    # override
    def exit(self) -> bool:
        if not self.state_machine.is_empty():
            self.state_machine.exit()

        self.get_window().pop_window_handlers()
        return True

    # override
    def close(self) -> bool:
        super().close()
        self.parent.close()  # type: ignore[attr-defined]
        return True
