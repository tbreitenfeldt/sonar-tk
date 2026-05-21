from typing import Any, Optional, Tuple

from sonartk.sound.openal_lite.openal import (
    Listener,
    LoadSound,
    BufferSound,
    Player,
)
from sonartk.sound.player_pool import PlayerPool
from sonartk.sound.sound_pool import SoundPool


class SoundManager:
    """Manage shared audio resources and playback operations."""

    def __init__(
        self,
        *,
        listener: Optional[Listener] = None,
        sound_pool: Optional[SoundPool] = None,
        player_pool: Optional[PlayerPool] = None,
        music_player: Optional[Player] = None,
    ) -> None:
        # Important that listener is initialized before any sounds.
        self.listener: Listener = listener or Listener()
        self.sound_pool: SoundPool = sound_pool or SoundPool()
        self.player_pool: PlayerPool = player_pool or PlayerPool()
        self.music_player: Player = music_player or Player()

    def play_music(self, path: str, loop: bool = True) -> None:
        """Load and play background music.

        Any currently playing music is stopped and replaced.
        """
        if self.music_player.playing():
            self.music_player.stop()
            self.music_player.remove()

        self.music_player.add(self.sound_pool.load(path))
        self.music_player.loop = loop
        self.music_player.play()

    def pause_music(self) -> None:
        """Pause the currently playing music track."""
        self.music_player.pause()

    def resume_music(self) -> None:
        """Resume playback of the paused music track."""
        self.music_player.play()

    def stop_music(self) -> None:
        """Stop playback of the current music track."""
        self.music_player.stop()

    def play_sound(
        self,
        sound: str | LoadSound | BufferSound,
        player: Optional[Player] = None,
        position: Optional[Tuple[int]] = None,
        rolloff: float = 0.01,
        loop: bool = False,
        effects: Optional[list[Any]] = None,
        filters: Optional[list[Any]] = None,
    ) -> Player:
        """Play a sound effect.

        Supports optional player reuse, positional audio, effects, and filters.
        """
        if effects is None:
            effects = []
        if filters is None:
            filters = []

        if isinstance(sound, str):
            sound = self.sound_pool.load(sound)
        if player is None:
            player = self.player_pool.get_player()
        if position is None:
            position = self.listener.position

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

    def cleanup(self) -> None:
        """Release all shared audio resources managed by the sound subsystem."""
        self.sound_pool.destroy()
        self.player_pool.destroy()
        self.listener.delete()
        self.music_player.delete()


_default_manager = SoundManager()

# Backward-compatible module-level shared resources.
listener: Listener = _default_manager.listener
sound_pool: SoundPool = _default_manager.sound_pool
player_pool: PlayerPool = _default_manager.player_pool
music_player: Player = _default_manager.music_player


def _sync_default_manager_from_module() -> None:
    """Keep the default manager aligned with module-level globals."""
    _default_manager.listener = listener
    _default_manager.sound_pool = sound_pool
    _default_manager.player_pool = player_pool
    _default_manager.music_player = music_player


def play_music(path: str, loop: bool = True) -> None:
    """Load and play background music."""
    _sync_default_manager_from_module()
    _default_manager.play_music(path, loop=loop)


def pause_music() -> None:
    """Pause the currently playing music track."""
    _sync_default_manager_from_module()
    _default_manager.pause_music()


def resume_music() -> None:
    """Resume playback of the paused music track."""
    _sync_default_manager_from_module()
    _default_manager.resume_music()


def stop_music() -> None:
    """Stop playback of the current music track."""
    _sync_default_manager_from_module()
    _default_manager.stop_music()


def play_sound(
    sound: str | LoadSound | BufferSound,
    player: Optional[Player] = None,
    position: Optional[Tuple[int]] = None,
    rolloff: float = 0.01,
    loop: bool = False,
    effects: Optional[list[Any]] = None,
    filters: Optional[list[Any]] = None,
) -> Player:
    """Play a sound effect."""
    _sync_default_manager_from_module()
    return _default_manager.play_sound(
        sound=sound,
        player=player,
        position=position,
        rolloff=rolloff,
        loop=loop,
        effects=effects,
        filters=filters,
    )


def cleanup() -> None:
    """Release all shared audio resources managed by the sound subsystem."""
    _sync_default_manager_from_module()
    _default_manager.cleanup()
