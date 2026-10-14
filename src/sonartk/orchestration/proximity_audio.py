from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Optional, Protocol, cast

from sonartk.sound import sound_manager
from sonartk.sound.openal_lite.openal import Player
from sonartk.util import Coordinates

SoundPosition = tuple[int, int, int]


@dataclass(frozen=True)
class ProximityAudioEmitter:
    """Distance-based emitter configuration for positional audio.

    ``distance_curve_exponent`` already fades the sound with distance, and
    the sound service applies ``rolloff`` on top of it, so keep ``rolloff``
    small (the default) unless you want the fade to be steeper.

    ``start_offset`` (0.0 to 1.0) is how far into the sound a looping
    emitter begins. Give neighbouring emitters of the same sound different
    offsets, otherwise their identical loops stay in phase and blend into
    what sounds like a single source.
    """

    sound_path: str
    source_coordinates: Coordinates
    max_distance_tiles: int
    base_volume: float = 1.0
    min_volume_at_max_distance: float = 0.0
    distance_curve_exponent: float = 1.0
    rolloff: float = 0.05
    loop: bool = True
    channel: Optional[str] = None
    start_offset: float = 0.0


class _SoundServiceLike(Protocol):
    def play_sound(
        self,
        sound: str,
        player: Optional[Player] = None,
        position: Optional[SoundPosition] = None,
        volume: float = 1.0,
        rolloff: float = 0.01,
        loop: bool = False,
        retrigger_if_same: bool = True,
        channel: str = "sfx",
    ) -> Player: ...


class ProximityAudioController:
    """Manage one or more proximity-based emitters with shared behavior."""

    def __init__(
        self,
        *,
        emitters: Mapping[str, ProximityAudioEmitter],
        players: Mapping[str, Player],
        position_resolver: Callable[[Coordinates], SoundPosition],
        sound_service: Optional[_SoundServiceLike] = None,
    ) -> None:
        self.emitters = dict(emitters)
        self.players = dict(players)
        self.position_resolver = position_resolver
        self.sound_service = sound_service or cast(
            _SoundServiceLike, sound_manager
        )

    @classmethod
    def from_emitters(
        cls,
        emitters: Mapping[str, ProximityAudioEmitter],
        *,
        position_resolver: Callable[[Coordinates], SoundPosition],
        sound_service: Optional[_SoundServiceLike] = None,
    ) -> ProximityAudioController:
        """Build a controller that creates one player per emitter."""
        return cls(
            emitters=emitters,
            players={key: Player() for key in emitters},
            position_resolver=position_resolver,
            sound_service=sound_service,
        )

    @staticmethod
    def effective_volume(
        *,
        distance_tiles: int,
        max_distance_tiles: int,
        base_volume: float,
        min_volume_at_max_distance: float,
        distance_curve_exponent: float,
    ) -> float:
        """Compute emitter gain at a given Manhattan tile distance."""
        if max_distance_tiles <= 0:
            return base_volume

        progress = min(distance_tiles / max_distance_tiles, 1.0)
        curve_value = float((1.0 - progress) ** distance_curve_exponent)
        relative_gain = (
            min_volume_at_max_distance
            + (1.0 - min_volume_at_max_distance) * curve_value
        )
        return base_volume * relative_gain

    def update(
        self,
        emitter_key: str,
        *,
        listener_coordinates: Coordinates,
        is_active: bool,
    ) -> bool:
        """Update one emitter and return whether it remains audible."""
        emitter = self.emitters[emitter_key]
        player = self.players[emitter_key]

        if not is_active:
            player.stop()
            player.remove()
            return False

        distance = abs(
            listener_coordinates[0] - emitter.source_coordinates[0]
        ) + abs(listener_coordinates[1] - emitter.source_coordinates[1])
        if distance > emitter.max_distance_tiles:
            player.stop()
            player.remove()
            return False

        channel_options: dict[str, str] = (
            {} if emitter.channel is None else {"channel": emitter.channel}
        )
        offset_needed = emitter.start_offset > 0 and not player.playing()
        self.sound_service.play_sound(
            emitter.sound_path,
            player=player,
            position=self.position_resolver(emitter.source_coordinates),
            volume=self.effective_volume(
                distance_tiles=distance,
                max_distance_tiles=emitter.max_distance_tiles,
                base_volume=emitter.base_volume,
                min_volume_at_max_distance=emitter.min_volume_at_max_distance,
                distance_curve_exponent=emitter.distance_curve_exponent,
            ),
            rolloff=emitter.rolloff,
            loop=emitter.loop,
            retrigger_if_same=False,
            **channel_options,
        )
        if offset_needed:
            try:
                setattr(player, "seek", emitter.start_offset)
            except IndexError:
                # Nothing was queued (the sound failed to load), so there
                # is nothing to seek into.
                pass
        return True

    def update_many(
        self,
        *,
        listener_coordinates: Coordinates,
        is_active_by_key: Mapping[str, bool],
    ) -> dict[str, bool]:
        """Update many emitters in one call and return per-emitter activity."""
        return {
            emitter_key: self.update(
                emitter_key,
                listener_coordinates=listener_coordinates,
                is_active=is_active_by_key.get(emitter_key, False),
            )
            for emitter_key in self.emitters.keys()
        }

    def update_at(self, listener_coordinates: Coordinates) -> dict[str, bool]:
        """Update every emitter as active for a listener position."""
        return self.update_many(
            listener_coordinates=listener_coordinates,
            is_active_by_key={key: True for key in self.emitters},
        )

    def stop_all(self) -> None:
        """Stop every emitter's sound and release its player."""
        for player in self.players.values():
            player.stop()
            player.remove()
