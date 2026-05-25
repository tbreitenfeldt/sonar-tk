from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Optional, Protocol, cast

from sonartk.map_builder.map_2d import Map2d, MapTile
from sonartk.sound import sound_manager
from sonartk.sound.openal_lite.openal import Player
from sonartk.ui.element.grid import Grid
from sonartk.util import Coordinates, Direction

SoundPosition = tuple[int, int, int]
SoundPathMap = dict[str, str]


@dataclass(frozen=True)
class AmbientTileSoundConfig:
    """Ambient sound behavior for a tile type.

    Attributes:
        sound_file: Audio file played while this tile is the nearest emitter.
        max_distance_tiles: Maximum Manhattan tile distance for audibility.
        volume: Base playback volume before channel scaling.
        rolloff: OpenAL rolloff factor for distance attenuation.
        loop: Whether ambient playback loops continuously.
        min_volume_at_max_distance: Relative gain at max_distance_tiles.
        distance_curve_exponent: Curve shaping for distance gain. Higher values
            increase contrast between near and far volumes.
    """

    sound_file: str
    max_distance_tiles: int = 3
    volume: float = 1.0
    rolloff: float = 0.3
    loop: bool = True
    min_volume_at_max_distance: float = 0.12
    distance_curve_exponent: float = 2.0


AmbientSoundMap = dict[str, AmbientTileSoundConfig]


@dataclass(frozen=True)
class TerrainAudioProfile:
    """Unified terrain movement and ambient audio configuration.

    Attributes:
        is_passable: Whether this terrain type is walkable.
        movement_sound_file: Movement sound for passable tiles.
        ambient_sound: Optional ambient config for this terrain.
        include_in_sound_map_when_blocked: When True, blocked terrain still
            contributes to sound_map (useful for explicit blocked cues).
    """

    is_passable: bool = True
    movement_sound_file: Optional[str] = None
    ambient_sound: Optional[AmbientTileSoundConfig] = None
    include_in_sound_map_when_blocked: bool = False


TerrainAudioProfileMap = dict[str, TerrainAudioProfile]


class _ListenerLike(Protocol):
    position: SoundPosition


class _SoundServiceLike(Protocol):
    listener: _ListenerLike

    def play_sound(
        self,
        sound_file: str,
        position: SoundPosition,
        player: Player,
        volume: float = 1.0,
        rolloff: float = 0.01,
        loop: bool = False,
    ) -> None: ...


class MapSoundNavigationController:
    """Handle map navigation and border sounds for grid-based maps.

    The controller is intentionally injectable so callers can swap sound services,
    position mapping, or handler wiring strategy without changing core behavior.
    """

    def __init__(
        self,
        map2d: Map2d,
        sound_map: SoundPathMap,
        player: Player,
        sound_service: Optional[_SoundServiceLike] = None,
        position_resolver: Optional[
            Callable[[Coordinates], SoundPosition]
        ] = None,
        on_move_success: Optional[
            Callable[[Coordinates, MapTile], None]
        ] = None,
        on_move_blocked: Optional[Callable[[Direction], None]] = None,
        ambient_sound_map: Optional[AmbientSoundMap] = None,
        ambient_player: Optional[Player] = None,
        blocked_tile_sound_name: str = "wall",
        validate_sound_map: bool = False,
    ) -> None:
        self.map2d = map2d
        self.sound_map = sound_map
        self.player = player
        self.sound_service = sound_service or cast(
            _SoundServiceLike,
            sound_manager,
        )
        self.position_resolver = position_resolver or self._default_position
        self.on_move_success = on_move_success
        self.on_move_blocked = on_move_blocked
        self.ambient_sound_map = ambient_sound_map or {}
        self.ambient_player = ambient_player
        self.blocked_tile_sound_name = blocked_tile_sound_name

        for tile_name, config in self.ambient_sound_map.items():
            if config.max_distance_tiles < 0:
                raise ValueError(
                    f"Ambient config for tile '{tile_name}' must use max_distance_tiles >= 0."
                )
            if not (0.0 <= config.min_volume_at_max_distance <= 1.0):
                raise ValueError(
                    f"Ambient config for tile '{tile_name}' must use min_volume_at_max_distance within [0.0, 1.0]."
                )
            if config.distance_curve_exponent <= 0:
                raise ValueError(
                    f"Ambient config for tile '{tile_name}' must use distance_curve_exponent > 0."
                )

        if validate_sound_map:
            self.validate_sound_map_for_map()

    @classmethod
    def from_terrain_audio_profiles(
        cls,
        *,
        map2d: Map2d,
        terrain_audio_profiles: Mapping[str, TerrainAudioProfile],
        player: Player,
        sound_service: Optional[_SoundServiceLike] = None,
        position_resolver: Optional[
            Callable[[Coordinates], SoundPosition]
        ] = None,
        on_move_success: Optional[
            Callable[[Coordinates, MapTile], None]
        ] = None,
        on_move_blocked: Optional[Callable[[Direction], None]] = None,
        ambient_player: Optional[Player] = None,
        blocked_tile_sound_name: str = "wall",
        validate_sound_map: bool = True,
    ) -> "MapSoundNavigationController":
        sound_map, ambient_sound_map = cls.build_audio_maps_from_profiles(
            terrain_audio_profiles
        )
        return cls(
            map2d=map2d,
            sound_map=sound_map,
            player=player,
            sound_service=sound_service,
            position_resolver=position_resolver,
            on_move_success=on_move_success,
            on_move_blocked=on_move_blocked,
            ambient_sound_map=ambient_sound_map,
            ambient_player=ambient_player,
            blocked_tile_sound_name=blocked_tile_sound_name,
            validate_sound_map=validate_sound_map,
        )

    @staticmethod
    def build_audio_maps_from_profiles(
        terrain_audio_profiles: Mapping[str, TerrainAudioProfile],
    ) -> tuple[SoundPathMap, AmbientSoundMap]:
        sound_map: SoundPathMap = {}
        ambient_sound_map: AmbientSoundMap = {}

        for tile_name, profile in terrain_audio_profiles.items():
            if profile.movement_sound_file is not None:
                sound_map[tile_name] = profile.movement_sound_file
            if profile.ambient_sound is not None:
                ambient_sound_map[tile_name] = profile.ambient_sound

        return sound_map, ambient_sound_map

    @staticmethod
    def build_tile_reference_from_profiles(
        value_to_terrain_name: Mapping[str, str],
        terrain_audio_profiles: Mapping[str, TerrainAudioProfile],
    ) -> dict[str, MapTile]:
        tile_reference: dict[str, MapTile] = {}
        for map_value, terrain_name in value_to_terrain_name.items():
            profile = terrain_audio_profiles[terrain_name]
            tile_reference[map_value] = MapTile(
                terrain_name,
                is_passable=profile.is_passable,
            )
        return tile_reference

    def validate_sound_map_for_map(self) -> None:
        """Validate that all passable map tile names have movement sounds."""
        passable_names = {
            tile.name for tile in self.map2d.tile_map if tile.is_passable
        }
        missing_passable = sorted(
            name for name in passable_names if name not in self.sound_map
        )
        if missing_passable:
            raise ValueError(
                "Missing movement sounds for passable tiles: "
                + ", ".join(missing_passable)
            )

        if self.blocked_tile_sound_name not in self.sound_map:
            raise ValueError(
                "Missing required blocked collision sound mapping for key "
                f"'{self.blocked_tile_sound_name}'."
            )

        map_tile_names = {tile.name for tile in self.map2d.tile_map}
        unknown_ambient_keys = sorted(
            name
            for name in self.ambient_sound_map.keys()
            if name not in map_tile_names
        )
        if unknown_ambient_keys:
            raise ValueError(
                "Ambient sound configured for tile names not present in map: "
                + ", ".join(unknown_ambient_keys)
            )

    def on_navigation(self, grid: Grid[MapTile], direction: Direction) -> bool:
        """Play movement/collision sounds and update map state.

        Returns True when the event should be handled (blocked movement), and
        False when grid navigation should continue.
        """
        is_handled = False

        try:
            self.map2d.character.directional_orientation = direction
            new_coordinates, tile = grid.get_next_cell(direction)
            if tile is None:
                if self.on_move_blocked is not None:
                    self.on_move_blocked(direction)
                return True

            new_position = self.position_resolver(new_coordinates)
            sound_file = self.sound_map[tile.name]

            if tile.is_passable:
                # Replacement policy may return a displaced character; navigation
                # intentionally ignores that value and only advances the active
                # player character.
                _ = self.map2d.move_character(
                    self.map2d.character, new_coordinates
                )
                self.sound_service.listener.position = new_position
                self.sound_service.play_sound(
                    sound_file,
                    position=new_position,
                    player=self.player,
                )
                self.update_ambient_sound(new_coordinates)
                if self.on_move_success is not None:
                    self.on_move_success(new_coordinates, tile)
                is_handled = False
            else:
                self.play_blocked_sound(grid, direction)
                if self.on_move_blocked is not None:
                    self.on_move_blocked(direction)
                is_handled = True
        except KeyError:
            pass

        return is_handled

    def on_border(self, grid: Grid[MapTile], direction: Direction) -> bool:
        """Play a border collision sound.

        Returns True if a blocked collision mapping exists and was played.
        """
        return self.play_blocked_sound(grid, direction)

    def play_blocked_sound(
        self, grid: Grid[MapTile], direction: Direction
    ) -> bool:
        """Play a blocked collision sound from the next tile position."""
        try:
            sound_file = self.sound_map[self.blocked_tile_sound_name]
            next_coordinates, _ = grid.get_next_cell(direction)
            self.sound_service.play_sound(
                sound_file,
                position=self.position_resolver(next_coordinates),
                player=self.player,
            )
            return True
        except KeyError:
            return False

    def play_wall_sound(
        self, grid: Grid[MapTile], direction: Direction
    ) -> bool:
        """Backward-compatible alias for blocked collision sound playback."""
        return self.play_blocked_sound(grid, direction)

    def update_ambient_sound(
        self, coordinates: Optional[Coordinates] = None
    ) -> bool:
        """Update continuous ambient playback for nearby configured tiles.

        Returns True when an ambient sound is active after the update.
        """
        if self.ambient_player is None or not self.ambient_sound_map:
            return False

        origin = coordinates or self.map2d.character.coordinates
        nearest = self._find_nearest_ambient_emitter(origin)
        if nearest is None:
            self.ambient_player.stop()
            self.ambient_player.remove()
            return False

        emitter_coordinates, config, distance = nearest
        self.sound_service.play_sound(
            config.sound_file,
            position=self.position_resolver(emitter_coordinates),
            player=self.ambient_player,
            volume=self._effective_ambient_volume(distance, config),
            rolloff=config.rolloff,
            loop=config.loop,
        )
        return True

    def _find_nearest_ambient_emitter(
        self, origin: Coordinates
    ) -> Optional[tuple[Coordinates, AmbientTileSoundConfig, int]]:
        best: Optional[tuple[Coordinates, AmbientTileSoundConfig, int]] = None

        for y in range(self.map2d.height):
            for x in range(self.map2d.width):
                coordinates = cast(Coordinates, (x, y))
                tile = self.map2d.get_tile(coordinates)
                config = self.ambient_sound_map.get(tile.name)
                if config is None:
                    continue

                distance = abs(origin[0] - x) + abs(origin[1] - y)
                if distance > config.max_distance_tiles:
                    continue

                if best is None or distance < best[2]:
                    best = (coordinates, config, distance)

        if best is None:
            return None

        return best

    @staticmethod
    def _effective_ambient_volume(
        distance_tiles: int,
        config: AmbientTileSoundConfig,
    ) -> float:
        if config.max_distance_tiles <= 0:
            return config.volume

        progress = min(distance_tiles / config.max_distance_tiles, 1.0)
        curve_value = float((1.0 - progress) ** config.distance_curve_exponent)
        relative_gain = (
            config.min_volume_at_max_distance
            + (1.0 - config.min_volume_at_max_distance) * curve_value
        )
        return config.volume * relative_gain

    @staticmethod
    def _default_position(coordinates: Coordinates) -> SoundPosition:
        return (coordinates[0], coordinates[1], 0)
