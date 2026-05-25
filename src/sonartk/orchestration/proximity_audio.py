from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Optional, Protocol, cast

from sonartk.sound import sound_manager
from sonartk.sound.openal_lite.openal import Player
from sonartk.util import Coordinates

SoundPosition = tuple[int, int, int]


@dataclass(frozen=True)
class ProximityAudioEmitter:
    """Distance-based emitter configuration for positional audio."""

    sound_path: str
    source_coordinates: Coordinates
    max_distance_tiles: int
    base_volume: float
    min_volume_at_max_distance: float
    distance_curve_exponent: float
    rolloff: float
    loop: bool = True


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
        )
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
