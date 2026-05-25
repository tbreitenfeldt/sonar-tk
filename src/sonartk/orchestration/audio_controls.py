from __future__ import annotations

from typing import Optional

from pyglet.window import key

from sonartk.sound import sound_manager
from sonartk.sound.openal_lite.openal import Player
from sonartk.ui.window import Window


def bind_volume_hotkeys(
    window: Window,
    *,
    sfx_player: Optional[Player] = None,
    music_step: float = 0.05,
    sfx_step: float = 0.05,
    couple_music_to_sfx_ratio: Optional[float] = None,
) -> None:
    """Bind default hotkeys for runtime music and sfx volume control.

    `F7/F6` adjusts music, while `Shift+F7/Shift+F6` adjusts sfx.
    """

    def increase_music_volume() -> bool:
        current = sound_manager.get_channel_volume("music")
        sound_manager.set_music_volume(current + music_step)
        return True

    def decrease_music_volume() -> bool:
        current = sound_manager.get_channel_volume("music")
        sound_manager.set_music_volume(current - music_step)
        return True

    def increase_sfx_volume() -> bool:
        current = sound_manager.get_channel_volume("sfx")
        updated = sound_manager.set_sfx_volume(
            current + sfx_step,
            players=[sfx_player] if sfx_player is not None else None,
        )
        if couple_music_to_sfx_ratio is not None:
            sound_manager.set_music_volume(updated * couple_music_to_sfx_ratio)
        return True

    def decrease_sfx_volume() -> bool:
        current = sound_manager.get_channel_volume("sfx")
        updated = sound_manager.set_sfx_volume(
            current - sfx_step,
            players=[sfx_player] if sfx_player is not None else None,
        )
        if couple_music_to_sfx_ratio is not None:
            sound_manager.set_music_volume(updated * couple_music_to_sfx_ratio)
        return True

    window.key_handler.add_key_press(increase_music_volume, key.F7)
    window.key_handler.add_key_press(decrease_music_volume, key.F6)
    window.key_handler.add_key_press(
        increase_sfx_volume,
        key.F7,
        [key.MOD_SHIFT],
    )
    window.key_handler.add_key_press(
        decrease_sfx_volume,
        key.F6,
        [key.MOD_SHIFT],
    )
