from __future__ import annotations

from typing import Callable, Hashable, cast

import pyglet.clock

from sonartk.sound import sound_manager
from sonartk.sound.openal_lite.openal import Player

SoundPosition = tuple[int, int, int]
_Offset = tuple[float, float, float]

GLIDE_INTERVAL_SECONDS = 1 / 60


def _lerp(start: _Offset, end: _Offset, amount: float) -> _Offset:
    return (
        start[0] + (end[0] - start[0]) * amount,
        start[1] + (end[1] - start[1]) * amount,
        start[2] + (end[2] - start[2]) * amount,
    )


def _listener_position() -> SoundPosition:
    return cast(SoundPosition, sound_manager.listener.position)


class _Glide:
    def __init__(
        self, player: Player, start: _Offset, target: _Offset
    ) -> None:
        self.player = player
        self.start = start
        self.target = target
        self.progress = 0.0


class PositionGlider:
    """Move playing sounds smoothly to a new place after the listener steps.

    A sound that was already playing slides, in listener-relative terms,
    from where it was last heard to where it now belongs, instead of
    jumping there. A source passing close by otherwise swings around the
    listener's head in one step, which the mixer renders as a pop.

    Each sound is identified by a key of the caller's choosing. With
    ``glide_seconds`` of zero or less nothing glides.
    """

    def __init__(
        self,
        glide_seconds: float,
        listener_position: Callable[[], SoundPosition] = _listener_position,
    ) -> None:
        self.glide_seconds = glide_seconds
        self.listener_position = listener_position
        self._offsets: dict[Hashable, _Offset] = {}
        self._glides: dict[Hashable, _Glide] = {}

    @property
    def active(self) -> bool:
        """Whether any sound is still gliding."""
        return bool(self._glides)

    def begin(
        self,
        key: Hashable,
        player: Player,
        position: SoundPosition,
        was_playing: bool,
    ) -> SoundPosition:
        """Return where to place the sound now, and glide it to ``position``.

        Without gliding, or for a sound that was not already playing, this
        is ``position`` itself.
        """
        if self.glide_seconds <= 0:
            return position
        listener = self.listener_position()
        target: _Offset = (
            float(position[0] - listener[0]),
            float(position[1] - listener[1]),
            float(position[2] - listener[2]),
        )
        start = self._offsets.get(key) if was_playing else None
        if start is None or start == target:
            self._offsets[key] = target
            self._glides.pop(key, None)
            return position
        self._glides[key] = _Glide(player, start, target)
        self._offsets[key] = start
        pyglet.clock.unschedule(self._tick)
        pyglet.clock.schedule_interval(self._tick, GLIDE_INTERVAL_SECONDS)
        return cast(
            SoundPosition,
            (
                listener[0] + start[0],
                listener[1] + start[1],
                listener[2] + start[2],
            ),
        )

    def forget(self, key: Hashable) -> None:
        """Drop everything known about a sound that stopped."""
        self._offsets.pop(key, None)
        self._glides.pop(key, None)
        if not self._glides:
            pyglet.clock.unschedule(self._tick)

    def _tick(self, dt: float) -> None:
        listener = self.listener_position()
        for key in list(self._glides):
            glide = self._glides[key]
            if not glide.player.playing():
                self.forget(key)
                continue
            glide.progress = min(1.0, glide.progress + dt / self.glide_seconds)
            offset = _lerp(glide.start, glide.target, glide.progress)
            self._offsets[key] = offset
            glide.player.position = cast(
                SoundPosition,
                (
                    listener[0] + offset[0],
                    listener[1] + offset[1],
                    listener[2] + offset[2],
                ),
            )
            if glide.progress >= 1.0:
                self._glides.pop(key)
        if not self._glides:
            pyglet.clock.unschedule(self._tick)
