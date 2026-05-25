from __future__ import annotations

from typing import Any, Callable, Optional, Protocol, Sequence

from sonartk.sound.openal_lite.openal import Player
from sonartk.ui.window import Window
from sonartk.util import speech_manager
from sonartk.util.key_handler import KeyHandler
from sonartk.util.state import State


class _MessageSoundService(Protocol):
    def play_sound(
        self,
        sound: str,
        player: Optional[Player] = None,
    ) -> Player: ...


class MessageActionState(State):
    """Reusable state that speaks a message and waits for action keys."""

    def __init__(
        self,
        *,
        window: Window,
        message: str,
        entry_sound: Optional[str] = None,
        entry_sound_player: Optional[Player] = None,
        continue_keys: Optional[Sequence[int]] = None,
        next_state_key: Optional[str] = None,
        on_continue: Optional[Callable[[], None]] = None,
        sound_service: Optional[_MessageSoundService] = None,
    ) -> None:
        from sonartk.sound import sound_manager

        self.window = window
        self.message = message
        self.entry_sound = entry_sound
        self.entry_sound_player = entry_sound_player
        self.next_state_key = next_state_key
        self.on_continue = on_continue
        self.sound_service: _MessageSoundService = (
            sound_service  # type: ignore[assignment]
            if sound_service is not None
            else sound_manager  # type: ignore[assignment]
        )
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
        if self.entry_sound is not None:
            self.sound_service.play_sound(
                self.entry_sound,
                player=self.entry_sound_player,
            )
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
