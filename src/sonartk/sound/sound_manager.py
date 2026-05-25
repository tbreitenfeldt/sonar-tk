import time
from typing import Any, Callable, Optional

import pyglet.clock

from sonartk.sound.openal_lite.openal import (
    Listener,
    LoadSound,
    BufferSound,
    Player,
)
from sonartk.sound.player_pool import PlayerPool
from sonartk.sound.sound_pool import SoundPool

DEFAULT_CHANNEL_VOLUMES: dict[str, float] = {
    "music": 1.0,
    "sfx": 1.0,
    "ui": 1.0,
    "voice": 1.0,
}


def _clamp_volume(value: float) -> float:
    return max(0.0, min(1.0, value))


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
        self._channel_volumes: dict[str, float] = dict(DEFAULT_CHANNEL_VOLUMES)
        self._music_fade_callback: Optional[Callable[[float], None]] = None

    def play_music(
        self,
        path: str,
        loop: bool = True,
        volume: float = 1.0,
        fade_in_seconds: float = 0.0,
        fade_step_seconds: float = 0.05,
    ) -> None:
        """Load and play background music.

        Any currently playing music is stopped and replaced.
        """
        if fade_in_seconds < 0:
            raise ValueError("fade_in_seconds must be >= 0")
        if fade_in_seconds > 0 and fade_step_seconds <= 0:
            raise ValueError("fade_step_seconds must be > 0")

        if self.music_player.playing():
            self.music_player.stop()
            self.music_player.remove()

        self.music_player.add(self.sound_pool.load(path))
        self.music_player.loop = loop
        target_volume = self._effective_volume(volume, "music")

        if self._music_fade_callback is not None:
            pyglet.clock.unschedule(self._music_fade_callback)
            self._music_fade_callback = None

        if fade_in_seconds > 0:
            self.music_player.volume = 0.0
            self._schedule_music_fade(
                target_volume,
                duration_seconds=fade_in_seconds,
                step_seconds=fade_step_seconds,
            )
        else:
            self.music_player.volume = target_volume

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
        position: Optional[tuple[int, int, int]] = None,
        volume: float = 1.0,
        channel: str = "sfx",
        rolloff: float = 0.01,
        loop: bool = False,
        effects: Optional[list[Any]] = None,
        filters: Optional[list[Any]] = None,
        wait_until_finished: bool = False,
        poll_interval_seconds: float = 0.01,
        on_complete: Optional[Callable[[Player], None]] = None,
        completion_poll_interval_seconds: float = 0.01,
    ) -> Player:
        """Play a sound effect.

        Supports optional player reuse, positional audio, effects, and filters.

        If wait_until_finished is enabled, this call blocks until playback ends.
        Avoid this on the UI thread to prevent freezing input.

        If on_complete is provided, completion is detected non-blockingly via
        pyglet clock polling and callback invocation when playback stops.
        """
        if effects is None:
            effects = []
        if filters is None:
            filters = []
        if wait_until_finished and poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be > 0")
        if on_complete is not None and completion_poll_interval_seconds <= 0:
            raise ValueError("completion_poll_interval_seconds must be > 0")

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

        player.loop = loop
        player.rolloff = rolloff
        player.position = position
        player.volume = self._effective_volume(volume, channel)
        player.play()

        if wait_until_finished:
            while player.playing():
                time.sleep(poll_interval_seconds)

        if on_complete is not None:
            self._schedule_on_complete(
                player,
                on_complete,
                completion_poll_interval_seconds,
            )

        return player

    def _schedule_on_complete(
        self,
        player: Player,
        callback: Callable[[Player], None],
        poll_interval_seconds: float,
    ) -> None:
        """Run callback once when the provided player is no longer playing."""

        def poll(_: float) -> None:
            if player.playing():
                return

            pyglet.clock.unschedule(poll)
            callback(player)

        pyglet.clock.schedule_interval(poll, poll_interval_seconds)

    def get_channel_volume(self, channel: str) -> float:
        """Return the current volume scalar for a named channel."""
        return self._channel_volumes[self._validate_channel(channel)]

    def set_channel_volume(self, channel: str, volume: float) -> float:
        """Set and return the clamped volume scalar for a named channel."""
        key = self._validate_channel(channel)
        clamped = _clamp_volume(volume)
        self._channel_volumes[key] = clamped
        return clamped

    def set_music_volume(
        self,
        volume: float,
        fade_seconds: float = 0.0,
        fade_step_seconds: float = 0.05,
    ) -> float:
        """Set music channel volume and optionally fade currently playing music."""
        if fade_seconds < 0:
            raise ValueError("fade_seconds must be >= 0")
        if fade_seconds > 0 and fade_step_seconds <= 0:
            raise ValueError("fade_step_seconds must be > 0")

        target = self.set_channel_volume("music", volume)

        if self._music_fade_callback is not None:
            pyglet.clock.unschedule(self._music_fade_callback)
            self._music_fade_callback = None

        if fade_seconds > 0:
            self._schedule_music_fade(
                target,
                duration_seconds=fade_seconds,
                step_seconds=fade_step_seconds,
            )
        else:
            self.music_player.volume = target

        return target

    def set_sfx_volume(
        self,
        volume: float,
        players: Optional[list[Player]] = None,
    ) -> float:
        """Set sfx channel volume and optionally apply it to active players."""
        target = self.set_channel_volume("sfx", volume)
        if players:
            for player in players:
                self.apply_sfx_volume(player)
        return target

    def apply_sfx_volume(
        self, player: Player, base_volume: float = 1.0
    ) -> None:
        """Apply effective sfx volume to a player using an optional base volume."""
        player.volume = self._effective_volume(base_volume, "sfx")

    def _effective_volume(self, local_volume: float, channel: str) -> float:
        key = self._validate_channel(channel)
        return _clamp_volume(
            _clamp_volume(local_volume) * self._channel_volumes[key]
        )

    def _validate_channel(self, channel: str) -> str:
        if channel not in self._channel_volumes:
            raise ValueError(
                f"Unknown channel '{channel}'. Expected one of {list(self._channel_volumes.keys())}."
            )
        return channel

    def _schedule_music_fade(
        self,
        target_volume: float,
        *,
        duration_seconds: float,
        step_seconds: float,
    ) -> None:
        elapsed = 0.0
        start_volume = self.music_player.volume

        def fade_step(delta_time: float) -> None:
            nonlocal elapsed
            elapsed += delta_time
            if duration_seconds <= 0:
                progress = 1.0
            else:
                progress = min(elapsed / duration_seconds, 1.0)
            self.music_player.volume = _clamp_volume(
                start_volume + (target_volume - start_volume) * progress
            )
            if progress >= 1.0:
                pyglet.clock.unschedule(fade_step)
                if self._music_fade_callback is fade_step:
                    self._music_fade_callback = None

        self._music_fade_callback = fade_step
        pyglet.clock.schedule_interval(fade_step, step_seconds)

    def cleanup(self) -> None:
        """Release all shared audio resources managed by the sound subsystem."""
        if self._music_fade_callback is not None:
            pyglet.clock.unschedule(self._music_fade_callback)
            self._music_fade_callback = None
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


def play_music(
    path: str,
    loop: bool = True,
    volume: float = 1.0,
    fade_in_seconds: float = 0.0,
    fade_step_seconds: float = 0.05,
) -> None:
    """Load and play background music."""
    _sync_default_manager_from_module()
    _default_manager.play_music(
        path,
        loop=loop,
        volume=volume,
        fade_in_seconds=fade_in_seconds,
        fade_step_seconds=fade_step_seconds,
    )


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
    position: Optional[tuple[int, int, int]] = None,
    volume: float = 1.0,
    channel: str = "sfx",
    rolloff: float = 0.01,
    loop: bool = False,
    effects: Optional[list[Any]] = None,
    filters: Optional[list[Any]] = None,
    wait_until_finished: bool = False,
    poll_interval_seconds: float = 0.01,
    on_complete: Optional[Callable[[Player], None]] = None,
    completion_poll_interval_seconds: float = 0.01,
) -> Player:
    """Play a sound effect."""
    _sync_default_manager_from_module()
    return _default_manager.play_sound(
        sound=sound,
        player=player,
        position=position,
        volume=volume,
        channel=channel,
        rolloff=rolloff,
        loop=loop,
        effects=effects,
        filters=filters,
        wait_until_finished=wait_until_finished,
        poll_interval_seconds=poll_interval_seconds,
        on_complete=on_complete,
        completion_poll_interval_seconds=completion_poll_interval_seconds,
    )


def clamp_volume(value: float) -> float:
    """Clamp a volume scalar to the supported [0.0, 1.0] range."""
    return _clamp_volume(value)


def get_channel_volume(channel: str) -> float:
    """Return the active volume for a named channel."""
    _sync_default_manager_from_module()
    return _default_manager.get_channel_volume(channel)


def set_channel_volume(channel: str, volume: float) -> float:
    """Set a named channel volume and return the clamped result."""
    _sync_default_manager_from_module()
    return _default_manager.set_channel_volume(channel, volume)


def set_music_volume(
    volume: float,
    fade_seconds: float = 0.0,
    fade_step_seconds: float = 0.05,
) -> float:
    """Set music volume and optionally fade currently playing music."""
    _sync_default_manager_from_module()
    return _default_manager.set_music_volume(
        volume,
        fade_seconds=fade_seconds,
        fade_step_seconds=fade_step_seconds,
    )


def set_sfx_volume(
    volume: float,
    players: Optional[list[Player]] = None,
) -> float:
    """Set sfx volume and optionally apply it to supplied players."""
    _sync_default_manager_from_module()
    return _default_manager.set_sfx_volume(volume, players=players)


def apply_sfx_volume(player: Player, base_volume: float = 1.0) -> None:
    """Apply effective sfx volume to a player."""
    _sync_default_manager_from_module()
    _default_manager.apply_sfx_volume(player, base_volume=base_volume)


def cleanup() -> None:
    """Release all shared audio resources managed by the sound subsystem."""
    _sync_default_manager_from_module()
    _default_manager.cleanup()
