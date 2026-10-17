from __future__ import annotations

from typing import Callable, Iterable, Mapping, Optional

from sonartk.map_builder import Map2d, MapTile
from sonartk.orchestration.map_interaction import (
    DEFAULT_INTERACT_KEYS,
    InteractableObject,
    MapInteractionController,
)
from sonartk.orchestration.map_sound_navigation import (
    MapSoundNavigationController,
    TerrainAudioProfile,
)
from sonartk.orchestration.paged_text_state import PagedTextState
from sonartk.orchestration.proximity_audio import (
    ProximityAudioController,
    ProximityAudioEmitter,
)
from sonartk.sound import sound_manager
from sonartk.sound.openal_lite.openal import Player
from sonartk.ui.element.grid import Grid
from sonartk.ui.screen.container_screen import ContainerScreen
from sonartk.ui.window import Window
from sonartk.util import Coordinates, Direction, speech_manager


def describe_tile_name(tile: MapTile) -> str:
    """Speak a tile by its name, with underscores read as spaces."""
    return str(tile.name).replace("_", " ")


DEFAULT_GRID_KEY = "grid"
DEFAULT_ARROW_KEY_REPEAT_SECONDS = 0.25

# Map positions are (x, y, z) with x east, y north and z up. Facing north
# with z up puts north ahead, east to the right, and heights overhead.
MAP_LISTENER_ORIENTATION: tuple[
    tuple[float, float, float], tuple[float, float, float]
] = ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


class MapPlaySession:
    """Everything needed to walk one map: screen, grid, sounds, objects.

    Builds a screen holding a silent coordinate grid over ``map2d``, wires
    it to terrain footsteps and ambient tiles, positional object sounds, and
    examinable objects. The session does not touch the window's state list
    or any music, so the game decides when to ``window.add`` the
    ``screen`` and when to call ``start_audio`` and ``stop_audio``.

    Args:
        window: Window the screen belongs to.
        map2d: The map to play.
        screen_key: State key the game registers the screen under; also the
            state descriptions return to.
        terrain_audio_profiles: Terrain name to footstep, collision and
            ambient configuration. Profiles for terrain the map does not use
            are ignored, so one table serves every map.
        object_emitters: Looping positional sounds by object name.
        interactables: Objects the player can examine.
        on_move_success: Called after each successful step, once object
            sounds are updated, as ``(coordinates, tile)``.
        on_page_change: Called when an object description advances.
        interact_keys: Keys that examine objects.
        interact_reach_tiles: How far away objects can be examined.
        grid_key: Key of the grid inside the screen.
        arrow_key_repeat_interval: Seconds between repeats of a held arrow.
        blend_ambient: Play each distinct ambient sound from its nearest
            tile at once, instead of only the nearest ambient tile.
        blocked_side_sounds: Tile name to ``{Direction: sound}``, played
            instead of the tile's usual collision sound when hit while
            travelling that direction.
        locate_keys: Keys that speak the current tile and coordinates.
        describe_tile: Turns a tile into the text spoken for it.
        name_keys: Keys that speak the map's name.
        map_name: The name spoken by ``name_keys``.
        listener_orientation: ``(at, up)`` vectors the listener takes when
            audio starts. The default faces north with z up, so heights
            such as flyovers sound overhead. Pass ``None`` to leave the
            listener as it is.
    """

    def __init__(
        self,
        *,
        window: Window,
        map2d: Map2d,
        screen_key: str,
        terrain_audio_profiles: Mapping[str, TerrainAudioProfile],
        object_emitters: Optional[Mapping[str, ProximityAudioEmitter]] = None,
        interactables: Iterable[InteractableObject] = (),
        on_move_success: Optional[
            Callable[[Coordinates, MapTile], None]
        ] = None,
        on_page_change: Optional[Callable[[PagedTextState, int], None]] = None,
        interact_keys: tuple[int, ...] = DEFAULT_INTERACT_KEYS,
        interact_reach_tiles: int = 1,
        grid_key: str = DEFAULT_GRID_KEY,
        arrow_key_repeat_interval: float = DEFAULT_ARROW_KEY_REPEAT_SECONDS,
        blend_ambient: bool = False,
        blocked_side_sounds: Optional[
            Mapping[str, Mapping[Direction, str]]
        ] = None,
        locate_keys: tuple[int, ...] = (),
        describe_tile: Callable[[MapTile], str] = describe_tile_name,
        name_keys: tuple[int, ...] = (),
        map_name: Optional[str] = None,
        listener_orientation: Optional[
            tuple[tuple[float, float, float], tuple[float, float, float]]
        ] = MAP_LISTENER_ORIENTATION,
    ) -> None:
        self.window = window
        self.listener_orientation = listener_orientation
        self.map2d = map2d
        self.screen_key = screen_key
        self.on_move_success = on_move_success
        self.describe_tile = describe_tile
        self.map_name = map_name
        self.screen = ContainerScreen(window)
        self.grid: Grid[MapTile] = Grid(
            self.screen,
            label="",
            height=map2d.height,
            width=map2d.width,
            cells=map2d.tile_map,
            cell_class=MapTile,
            property_name="name",
            speak_coordinates_on_change=False,
            speak_value_on_change=False,
            arrow_key_repeat_interval=arrow_key_repeat_interval,
        )
        self.grid.current_coordinates = map2d.character.coordinates

        self.navigation = (
            MapSoundNavigationController.from_terrain_audio_profiles(
                map2d=map2d,
                terrain_audio_profiles=terrain_audio_profiles,
                ignore_unused_profiles=True,
                blend_ambient=blend_ambient,
                blocked_side_sounds=blocked_side_sounds,
                player=Player(),
                ambient_player=Player(),
                on_move_success=self._handle_move_success,
            )
        )
        self.grid.push_handlers(
            on_navigation=self.navigation.on_navigation,
            on_border=self.navigation.on_border,
        )
        self.screen.add(grid_key, self.grid)

        self.interaction = MapInteractionController(
            window=window,
            grid=self.grid,
            return_state_key=screen_key,
            objects=interactables,
            keys=interact_keys,
            reach_tiles=interact_reach_tiles,
            on_page_change=on_page_change,
        )
        for binding in locate_keys:
            self.grid.key_handler.add_key_press(self.speak_location, binding)
        for binding in name_keys:
            self.grid.key_handler.add_key_press(self.speak_map_name, binding)
        self.objects = ProximityAudioController.from_emitters(
            object_emitters or {},
            position_resolver=self.navigation.position_resolver,
        )

    def speak_location(self) -> bool:
        """Speak the tile under the player and its coordinates."""
        x, y = self.grid.current_coordinates
        tile = self.map2d.get_tile((x, y))
        height = self.map2d.elevation_at((x, y))
        spoken = f"{self.describe_tile(tile)}, x {x}, y {y}"
        if height != 0:
            spoken += f", height {height}"
        speech_manager.output(spoken, interrupt=True)
        return True

    def speak_map_name(self) -> bool:
        """Speak the name of the map, when it has one."""
        if self.map_name:
            speech_manager.output(self.map_name, interrupt=True)
        return True

    def start_audio(self) -> None:
        """Place the listener at the player and start nearby sounds."""
        start = self.map2d.character.coordinates
        if self.listener_orientation is not None:
            at, up = self.listener_orientation
            sound_manager.listener.at_orientation = at
            sound_manager.listener.up_orientation = up
        sound_manager.listener.position = self.navigation.position_resolver(
            start
        )
        self.navigation.update_ambient_sound(start)
        self.objects.update_at(start)

    def release(self) -> None:
        """Stop sounds and remove this session's screen and states."""
        self.stop_audio()
        self.interaction.release()
        self.window.remove(self.screen_key)

    def stop_audio(self) -> None:
        """Silence and release the object and ambient tile players."""
        self.objects.stop_all()
        self.navigation.stop_ambient_sound()

    def _handle_move_success(
        self, coordinates: Coordinates, tile: MapTile
    ) -> None:
        self.objects.update_at(coordinates)
        if self.on_move_success is not None:
            self.on_move_success(coordinates, tile)
