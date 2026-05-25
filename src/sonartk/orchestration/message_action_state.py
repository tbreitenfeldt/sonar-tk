from __future__ import annotations

from typing import Any, Callable, Optional, Sequence

from sonartk.ui.window import Window
from sonartk.util import speech_manager
from sonartk.util.key_handler import KeyHandler
from sonartk.util.state import State


class MessageActionState(State):
    """Reusable state that speaks a message and waits for action keys."""

    def __init__(
        self,
        *,
        window: Window,
        message: str,
        continue_keys: Optional[Sequence[int]] = None,
        next_state_key: Optional[str] = None,
        on_continue: Optional[Callable[[], None]] = None,
    ) -> None:
        self.window = window
        self.message = message
        self.next_state_key = next_state_key
        self.on_continue = on_continue
        self.key_handler = KeyHandler()
        self._change_state: Optional[Callable[[str, Any], None]] = None
        self._has_continued = False

        for continue_key in continue_keys or []:
            self.key_handler.add_key_press(self.continue_action, continue_key)

    def setup(
        self,
        change_state: Callable[[str, Any], None],
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        self._change_state = change_state
        self._has_continued = False
        self.window.push_window_handlers(self.key_handler)
        speech_manager.output(self.message)
        return True

    def update(self, delta_time: float) -> bool:
        return True

    def exit(self) -> bool:
        self.window.pop_window_handlers()
        return True

    def continue_action(self) -> bool:
        if self._has_continued:
            return True

        self._has_continued = True

        if self.on_continue is not None:
            self.on_continue()

        if self.next_state_key is not None and self._change_state is not None:
            self._change_state(self.next_state_key, False)

        return True
