from __future__ import annotations

from typing import Any, Callable, cast, TYPE_CHECKING

import pyglet.clock
from pyglet.window import key

from sonartk.ui.element.element import Element
from sonartk.ui.screen.container_screen import ContainerScreen

if TYPE_CHECKING:
    from sonartk.ui.screen.screen import Screen

from sonartk.util.state_machine import EmptyState, State
from sonartk.util.key_handler import KeyHandler
from sonartk.util import speech_manager


class Dialog(ContainerScreen):
    def __init__(self, parent: Screen) -> None:
        super().__init__(parent)
        self.original_caption: str = ""
        self.original_state_key: str = ""

    def open_dialog(self, caption: str) -> None:
        self.original_state_key = (
            self.parent.state_machine.current_state.state_key  # type: ignore[attr-defined]
        )
        count: int = self.parent.state_machine.size() + 1  # type: ignore[attr-defined]
        self.parent.add(f"dialog-{caption}-{count}", self)  # type: ignore[attr-defined]
        self.original_caption = self.caption
        self.caption = caption + " Dialog"
        pyglet.clock.schedule_once(
            lambda dt: self.parent.state_machine.change(self.state_key), 0.3  # type: ignore[attr-defined]
        )

    # override
    def bind_keys(self) -> None:
        super().bind_keys()
        self.key_handler.add_key_press(self.close, key.ESCAPE)

    # override
    def reset(self) -> None:
        for state in self.state_machine.states.values():
            element: Element = cast(Element, state)
            element.reset()

    # override
    def close(self) -> bool:
        # Call Screen.close() directly, NOT ContainerScreen.close()
        # to avoid closing the parent screen
        from sonartk.ui.screen.screen import Screen

        Screen.close(self)
        self.position = 0
        self.reset()
        self.caption = self.original_caption
        pyglet.clock.schedule_once(lambda db: self._reset_states(), 0.3)
        return True

    def _reset_states(self) -> None:
        self.parent.remove(self.state_key)  # type: ignore[attr-defined]
        self.state_machine.current_state = EmptyState()
        self.exit()
        self.parent.state_machine.change(self.original_state_key, False)  # type: ignore[attr-defined]
