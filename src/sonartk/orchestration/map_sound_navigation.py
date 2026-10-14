from __future__ import annotations

from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional, Protocol, cast

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
        channel: Optional playback channel (for example ``"ambience"``) so
            the sound follows that channel's volume. When None, the sound
            manager's default channel is used.
    """

    sound_file: str
    max_distance_tiles: int = 3
    volume: float = 1.0
    rolloff: float = 0.3
    loop: bool = True
    min_volume_at_max_distance: float = 0.12
    distance_curve_exponent: float = 2.0
    channel: Optional[str] = None


AmbientSoundMap = dict[str, AmbientTileSoundConfig]


@dataclass(frozen=True)
class TerrainAudioProfile:
    """Unified terrain movement and ambient audio configuration.

    Attributes:
        is_passable: Whether this terrain type is walkable.
        movement_sound_file: Movement sound for passable tiles.
        ambient_sound: Optional ambient config for this terrain.
        include_in_sound_map_when_blocked: Unused; blocked terrain with a
            ``movement_sound_file`` always contributes to the sound map.
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
        retrigger_if_same: bool = True,
        channel: str = "sfx",
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
        blend_ambient: bool = False,
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
        self.blend_ambient = blend_ambient
        self._blend_players: dict[str, Player] = {}
        self.blocked_tile_sound_name = blocked_tile_sound_name
        self._ambient_emitters: Optional[
            list[tuple[Coordinates, AmbientTileSoundConfig]]
        ] = None
        self._ambient_emitters_revision: Optional[int] = None

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
        ignore_unused_profiles: bool = False,
        blend_ambient: bool = False,
    ) -> "MapSoundNavigationController":
        """Build a controller from terrain audio profiles.

        With ``ignore_unused_profiles`` the profiles may describe more
        terrain than ``map2d`` uses: profiles for tile names absent from the
        map are skipped, so one shared terrain table serves every map. The
        blocked-tile profile is always kept.

        With ``blend_ambient`` every distinct ambient sound file plays from
        its own nearest tile at once, instead of only the single nearest
        ambient tile.
        """
        if ignore_unused_profiles:
            used = {tile.name for tile in map2d.tile_map}
            used.add(blocked_tile_sound_name)
            terrain_audio_profiles = {
                name: profile
                for name, profile in terrain_audio_profiles.items()
                if name in used
            }
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
            blend_ambient=blend_ambient,
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
        self.map2d.character.directional_orientation = direction
        with self._batched():
            return self._navigate(grid, direction)

    def _batched(self) -> AbstractContextManager[Any]:
        """Group the audio changes of one step into a single update.

        Services without ``batch_updates`` simply apply them one by one.
        """
        batch = getattr(self.sound_service, "batch_updates", None)
        return batch() if batch is not None else nullcontext()

    def _navigate(self, grid: Grid[MapTile], direction: Direction) -> bool:
        new_coordinates, tile = grid.get_next_cell(direction)
        if tile is None:
            if self.on_move_blocked is not None:
                self.on_move_blocked(direction)
            return True

        new_position = self.position_resolver(new_coordinates)

        if tile.is_passable:
            sound_file = self.sound_map[tile.name]
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
            return False

        self.play_blocked_sound(grid, direction, tile.name)
        if self.on_move_blocked is not None:
            self.on_move_blocked(direction)
        return True

    def on_border(self, grid: Grid[MapTile], direction: Direction) -> bool:
        """Play a border collision sound.

        Returns True if a blocked collision mapping exists and was played.
        """
        return self.play_blocked_sound(grid, direction)

    def play_blocked_sound(
        self,
        grid: Grid[MapTile],
        direction: Direction,
        tile_name: Optional[str] = None,
    ) -> bool:
        """Play a blocked collision sound from the next tile position.

        A blocked tile plays its own mapped sound when it has one. Otherwise,
        and at the map border, the shared blocked collision sound plays.
        """
        sound_file = self.sound_map.get(
            tile_name if tile_name is not None else "",
            self.sound_map[self.blocked_tile_sound_name],
        )
        next_coordinates, _ = grid.get_next_cell(direction)
        self.sound_service.play_sound(
            sound_file,
            position=self.position_resolver(next_coordinates),
            player=self.player,
        )
        return True

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
        if self.blend_ambient:
            return self._update_blended_ambient(origin)
        nearest = self._find_nearest_ambient_emitter(origin)
        if nearest is None:
            self.ambient_player.stop()
            self.ambient_player.remove()
            return False

        emitter_coordinates, config, distance = nearest
        channel_options: dict[str, str] = (
            {} if config.channel is None else {"channel": config.channel}
        )
        self.sound_service.play_sound(
            config.sound_file,
            position=self.position_resolver(emitter_coordinates),
            player=self.ambient_player,
            volume=self._effective_ambient_volume(distance, config),
            rolloff=config.rolloff,
            loop=config.loop,
            retrigger_if_same=False,
            **channel_options,
        )
        return True

    def stop_ambient_sound(self) -> None:
        """Stop and release every ambient player, including blended ones."""
        players = [*self._blend_players.values()]
        if self.ambient_player is not None:
            players.append(self.ambient_player)
        for player in players:
            player.stop()
            player.remove()

    def _update_blended_ambient(self, origin: Coordinates) -> bool:
        self._ensure_ambient_emitters()
        nearest_by_sound: dict[
            str, tuple[Coordinates, AmbientTileSoundConfig, int]
        ] = {}
        for coordinates, config in self._ambient_emitters or []:
            distance = abs(origin[0] - coordinates[0]) + abs(
                origin[1] - coordinates[1]
            )
            if distance > config.max_distance_tiles:
                continue
            best = nearest_by_sound.get(config.sound_file)
            if best is None or distance < best[2]:
                nearest_by_sound[config.sound_file] = (
                    coordinates,
                    config,
                    distance,
                )

        for sound_file in list(self._blend_players):
            if sound_file not in nearest_by_sound:
                self._blend_players[sound_file].stop()
                self._blend_players[sound_file].remove()
        for sound_file, (coordinates, config, distance) in sorted(
            nearest_by_sound.items()
        ):
            channel_options: dict[str, str] = (
                {} if config.channel is None else {"channel": config.channel}
            )
            self.sound_service.play_sound(
                sound_file,
                position=self.position_resolver(coordinates),
                player=self._blend_player(sound_file),
                volume=self._effective_ambient_volume(distance, config),
                rolloff=config.rolloff,
                loop=config.loop,
                retrigger_if_same=False,
                **channel_options,
            )
        return bool(nearest_by_sound)

    def _blend_player(self, sound_file: str) -> Player:
        player = self._blend_players.get(sound_file)
        if player is None:
            adopt = self.ambient_player is not None and not any(
                existing is self.ambient_player
                for existing in self._blend_players.values()
            )
            player = self.ambient_player if adopt else Player()
            assert player is not None
            self._blend_players[sound_file] = player
        return player

    def refresh_ambient_emitters(self) -> None:
        """Rebuild the cached ambient emitter list from the current map.

        Called automatically when the map reports changed tiles. Call it
        manually only if tiles are changed in a way the map cannot report.
        """
        emitters: list[tuple[Coordinates, AmbientTileSoundConfig]] = []
        if self.ambient_sound_map:
            for y in range(self.map2d.height):
                for x in range(self.map2d.width):
                    coordinates = cast(Coordinates, (x, y))
                    tile = self.map2d.get_tile(coordinates)
                    config = self.ambient_sound_map.get(tile.name)
                    if config is not None:
                        emitters.append((coordinates, config))

        self._ambient_emitters = emitters
        self._ambient_emitters_revision = getattr(
            self.map2d, "tile_revision", None
        )

    def _ensure_ambient_emitters(self) -> None:
        revision = getattr(self.map2d, "tile_revision", None)
        if (
            self._ambient_emitters is None
            or revision != self._ambient_emitters_revision
        ):
            self.refresh_ambient_emitters()

    def _find_nearest_ambient_emitter(
        self, origin: Coordinates
    ) -> Optional[tuple[Coordinates, AmbientTileSoundConfig, int]]:
        self._ensure_ambient_emitters()

        best: Optional[tuple[Coordinates, AmbientTileSoundConfig, int]] = None
        for coordinates, config in self._ambient_emitters or []:
            distance = abs(origin[0] - coordinates[0]) + abs(
                origin[1] - coordinates[1]
            )
            if distance > config.max_distance_tiles:
                continue

            if best is None or distance < best[2]:
                best = (coordinates, config, distance)
                continue

            if distance != best[2]:
                continue

            best_gain = self._effective_ambient_volume(best[2], best[1])
            candidate_gain = self._effective_ambient_volume(distance, config)
            if candidate_gain > best_gain:
                best = (coordinates, config, distance)

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
