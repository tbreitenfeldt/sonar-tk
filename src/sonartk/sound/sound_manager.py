from typing import Any, Optional, Tuple

from sonartk.sound.openal_lite.openal import (
    Listener,
    LoadSound,
    BufferSound,
    Player,
)
from sonartk.sound.player_pool import PlayerPool
from sonartk.sound.sound_pool import SoundPool

# Important that this is initialized first before any sounds
listener: Listener = Listener()
sound_pool: SoundPool = SoundPool()
player_pool: PlayerPool = PlayerPool()
music_player: Player = Player()


def play_music(path: str, loop: bool = True) -> None:
    """Load and play background music.

    Any currently playing music is stopped and replaced.
    """
    if music_player.playing():
        music_player.stop()
        music_player.remove()

    music_player.add(LoadSound(path))
    music_player.loop = loop
    music_player.play()


def pause_music() -> None:
    """Pause the currently playing music track."""
    music_player.pause()


def resume_music() -> None:
    """Resume playback of the paused music track."""
    music_player.play()


def stop_music() -> None:
    """Stop playback of the current music track."""
    music_player.stop()


def play_sound(
    sound: str | LoadSound | BufferSound,
    player: Optional[Player] = None,
    position: Optional[Tuple[int]] = None,
    rolloff: float = 0.01,
    loop: bool = False,
    effects: list[Any] = [],
    filters: list[Any] = [],
) -> Player:
    """Play a sound effect.

    Supports optional player reuse, positional audio, effects, and filters.
    """
    if isinstance(sound, str):
        sound = sound_pool.load(sound)
    if player is None:
        player = player_pool.get_player()
    if position is None:
        position = listener.position

    if sound not in player.queue:
        player.stop()
        player.remove()
        player.add(sound)

        if effects:
            for effect in effects:
                player.add_effect(effect)
        if filters:
            for filter in filters:
                player.add_filter(filter)

        player.rolloff = rolloff
        player.position = position
        player.play()
    else:
        player.position = position
        player.play()

    return player


def cleanup() -> None:
    """Release all shared audio resources managed by the sound subsystem."""
    sound_pool.destroy()
    player_pool.destroy()
    listener.delete()
    music_player.delete()
