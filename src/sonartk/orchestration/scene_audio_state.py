from __future__ import annotations

from typing import Any, Callable, Optional, Protocol, Sequence

from sonartk.sound.openal_lite.openal import Player
from sonartk.ui.window import Window
from sonartk.util.key_handler import KeyHandler
from sonartk.util.state import State


class _SceneSoundService(Protocol):
    def play_sound(
        self,
        sound: str,
        player: Optional[Player] = None,
        on_complete: Optional[Callable[[Player], None]] = None,
    ) -> Player: ...


class SceneAudioState(State):
    """Reusable scene state that gates progression on audio completion or skip input."""

    def __init__(
        self,
        *,
        window: Window,
        scene_sound: str,
        scene_player: Player,
        next_state_key: str,
        continue_keys: Optional[Sequence[int]] = None,
        stop_sound_on_continue: bool = True,
        on_continue: Optional[Callable[[], None]] = None,
        sound_service: Optional[_SceneSoundService] = None,
    ) -> None:
        from sonartk.sound import sound_manager

        self.window = window
        self.scene_sound = scene_sound
        self.scene_player = scene_player
        self.next_state_key = next_state_key
        self.stop_sound_on_continue = stop_sound_on_continue
        self.on_continue = on_continue
        self.sound_service: _SceneSoundService = (
            sound_service  # type: ignore[assignment]
            if sound_service is not None
            else sound_manager  # type: ignore[assignment]
        )
        self.key_handler = KeyHandler()
        self._change_state: Optional[Callable[..., None]] = None
        self._is_active = False
        self._has_continued = False

        for continue_key in continue_keys or []:
            self.key_handler.add_key_press(
                self.continue_to_next_state, continue_key
            )

    def setup(
        self,
        change_state: Callable[[str, Any], None],
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        self._change_state = change_state
        self._is_active = True
        self._has_continued = False
        self.key_handler.activate(reset_state=True)
        self.window.push_window_handlers(self.key_handler)
        self.sound_service.play_sound(
            self.scene_sound,
            player=self.scene_player,
            on_complete=self._on_scene_complete,
        )
        return True

    def update(self, delta_time: float) -> bool:
        return True

    def exit(self) -> bool:
        self._is_active = False
        self.key_handler.deactivate(reset_state=True)
        self.window.pop_window_handlers()
        return True

    def continue_to_next_state(self) -> bool:
        if self._has_continued or not self._is_active:
            return True

        self._has_continued = True
        if self.stop_sound_on_continue:
            self.scene_player.stop()

        if self._change_state is not None:
            self._change_state(self.next_state_key, False)

        if self.on_continue is not None:
            self.on_continue()

        return True

    def _on_scene_complete(self, _: Player) -> None:
        self.continue_to_next_state()
