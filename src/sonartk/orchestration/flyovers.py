"""Randomly timed flyovers, such as birds passing above the listener."""

from __future__ import annotations

import random
from contextlib import nullcontext
from dataclasses import dataclass
from typing import Any, ContextManager, Optional, Protocol, cast

import pyglet.clock
from sonartk.sound import sound_manager
from sonartk.sound.openal_lite.openal import Player

Position = tuple[float, float, float]

# Headings along the map plane as (x, y); height is the z axis.
COMPASS_HEADINGS: tuple[tuple[float, float], ...] = (
    (1.0, 0.0),
    (-1.0, 0.0),
    (0.0, 1.0),
    (0.0, -1.0),
)

# Share of a flyover during which calls may begin, so they can finish
# before the flyer is far away.
_CALL_WINDOW = 0.6


@dataclass(frozen=True)
class FlyoverConfig:
    """How often, how high and how fast a flyover happens, and its sounds.

    Attributes:
        moving_sound: Looped for the whole flyover, such as wing flutter.
        call_sounds: One of these is chosen at random for each call.
        min_interval_seconds: Shortest wait between flyovers.
        max_interval_seconds: Longest wait between flyovers.
        min_duration_seconds: Shortest time a flyover takes.
        max_duration_seconds: Longest time a flyover takes.
        path_half_length: Distance from the listener at which a flyover
            starts and ends.
        height: How far above the listener, on the z axis, the flyer
            passes.
        headings: ``(x, y)`` map-plane headings a flyover may take.
        min_calls: Fewest calls made during one flyover.
        max_calls: Most calls made during one flyover.
        volume: Volume of the moving sound.
        call_volume: Volume of each call.
        rolloff: Distance rolloff for every sound of the flyover.
        channel: Volume channel the sounds play on.
        update_interval_seconds: How often the position is updated.
    """

    moving_sound: str
    call_sounds: tuple[str, ...] = ()
    min_interval_seconds: float = 15.0
    max_interval_seconds: float = 60.0
    min_duration_seconds: float = 6.0
    max_duration_seconds: float = 10.0
    path_half_length: float = 30.0
    height: float = 8.0
    headings: tuple[tuple[float, float], ...] = COMPASS_HEADINGS
    min_calls: int = 1
    max_calls: int = 2
    volume: float = 1.0
    call_volume: float = 1.0
    rolloff: float = 0.01
    channel: str = "sfx"
    update_interval_seconds: float = 1 / 30

    def __post_init__(self) -> None:
        if not 0 < self.min_interval_seconds <= self.max_interval_seconds:
            raise ValueError("Flyover intervals must satisfy 0 < min <= max.")
        if not 0 < self.min_duration_seconds <= self.max_duration_seconds:
            raise ValueError("Flyover durations must satisfy 0 < min <= max.")
        if not 0 <= self.min_calls <= self.max_calls:
            raise ValueError("Flyover calls must satisfy 0 <= min <= max.")
        if self.max_calls > 0 and not self.call_sounds:
            raise ValueError("Flyover calls need at least one call sound.")
        if not self.headings:
            raise ValueError("A flyover needs at least one heading.")
        if self.path_half_length <= 0 or self.update_interval_seconds <= 0:
            raise ValueError("Path length and update interval must be > 0.")


class _SoundServiceLike(Protocol):
    listener: Any

    def play_sound(
        self,
        sound: str,
        *,
        position: Position,
        volume: float = 1.0,
        loop: bool = False,
        channel: str = "sfx",
        rolloff: float = 0.01,
    ) -> Player: ...


class FlyoverController:
    """Sends a flyer past the listener again and again, at random.

    While started it waits a random interval, then plays the moving sound
    in a loop as the flyer travels in a random heading over the listener,
    making a few calls on the way. The path is recomputed from the
    listener's current position on every update, so the flyer crosses
    right above the player even while the player walks.
    """

    def __init__(
        self,
        config: FlyoverConfig,
        *,
        sound_service: Optional[_SoundServiceLike] = None,
        rng: Optional[random.Random] = None,
    ) -> None:
        self.config = config
        self.sound_service = sound_service or cast(
            _SoundServiceLike, sound_manager
        )
        self.rng = rng or random.Random()
        self.running = False
        self.flying = False
        self._heading: tuple[float, float] = config.headings[0]
        self._elapsed = 0.0
        self._duration = 0.0
        self._pending_calls: list[tuple[float, str]] = []
        self._moving_player: Optional[Player] = None
        self._call_players: list[Player] = []

    def start(self) -> None:
        """Begin waiting for the first flyover."""
        if self.running:
            return
        self.running = True
        self._schedule_next()

    def fly_now(self) -> None:
        """Send a flyover right away, replacing any waiting or current one.

        Handy for testing. Does nothing unless the controller is running.
        """
        if not self.running:
            return
        pyglet.clock.unschedule(self._spawn)
        self._finish(stop_calls=True)
        self._spawn()

    def stop(self) -> None:
        """Cancel the next flyover and silence the current one."""
        self.running = False
        pyglet.clock.unschedule(self._spawn)
        self._finish(stop_calls=True)

    def _schedule_next(self) -> None:
        delay = self.rng.uniform(
            self.config.min_interval_seconds, self.config.max_interval_seconds
        )
        pyglet.clock.schedule_once(self._spawn, delay)

    def _spawn(self, dt: float = 0.0) -> None:
        config = self.config
        self._heading = self.rng.choice(config.headings)
        self._duration = self.rng.uniform(
            config.min_duration_seconds, config.max_duration_seconds
        )
        self._elapsed = 0.0
        count = self.rng.randint(config.min_calls, config.max_calls)
        self._pending_calls = sorted(
            (
                self.rng.uniform(0.0, self._duration * _CALL_WINDOW),
                self.rng.choice(config.call_sounds),
            )
            for _ in range(count)
        )
        self._call_players = []
        self.flying = True
        self._moving_player = self.sound_service.play_sound(
            config.moving_sound,
            position=self._position(),
            volume=config.volume,
            loop=True,
            channel=config.channel,
            rolloff=config.rolloff,
        )
        pyglet.clock.schedule_interval(
            self._tick, config.update_interval_seconds
        )

    def _position(self) -> Position:
        x, y, z = self.sound_service.listener.position
        half = self.config.path_half_length
        along = -half + 2 * half * min(self._elapsed / self._duration, 1.0)
        heading_x, heading_y = self._heading
        return (
            x + heading_x * along,
            y + heading_y * along,
            z + self.config.height,
        )

    def follow_listener(self) -> None:
        """Move the flyer to match the listener's current position.

        Call this right after the listener moves, ideally inside the same
        ``batch_updates`` block, so the flyer never lags a step behind. A
        lag of even one tile is heard as a pop on one side.
        """
        if not self.flying:
            return
        with self._batched():
            self._reposition(self._position())

    def _batched(self) -> ContextManager[Any]:
        batch = getattr(self.sound_service, "batch_updates", None)
        return batch() if batch is not None else nullcontext()

    def _reposition(self, position: Position) -> None:
        self._call_players = [p for p in self._call_players if p.playing()]
        for player in self._call_players:
            player.position = position
        if self._moving_player is not None:
            self._moving_player.position = position

    def _tick(self, dt: float) -> None:
        with self._batched():
            self._advance(dt)

    def _advance(self, dt: float) -> None:
        self._elapsed += dt
        position = self._position()
        while (
            self._pending_calls and self._pending_calls[0][0] <= self._elapsed
        ):
            _, sound = self._pending_calls.pop(0)
            self._call_players.append(
                self.sound_service.play_sound(
                    sound,
                    position=position,
                    volume=self.config.call_volume,
                    channel=self.config.channel,
                    rolloff=self.config.rolloff,
                )
            )
        self._reposition(position)
        if self._elapsed >= self._duration:
            self._finish(stop_calls=False)
            if self.running:
                self._schedule_next()

    def _finish(self, *, stop_calls: bool) -> None:
        pyglet.clock.unschedule(self._tick)
        self.flying = False
        self._pending_calls = []
        if self._moving_player is not None:
            self._moving_player.stop()
            self._moving_player.remove()
            self._moving_player = None
        if stop_calls:
            for player in self._call_players:
                player.stop()
        self._call_players = []
