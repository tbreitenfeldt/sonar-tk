from __future__ import annotations

from typing import Callable, Optional, Protocol, cast

from sonartk.map_builder.map_2d import Map2d, MapTile
from sonartk.sound import sound_manager
from sonartk.sound.openal_lite.openal import Player
from sonartk.ui.element.grid import Grid
from sonartk.util import Coordinates, Direction

SoundPosition = tuple[int, int, int]
SoundPathMap = dict[str, str]


class _ListenerLike(Protocol):
    position: SoundPosition


class _SoundServiceLike(Protocol):
    listener: _ListenerLike

    def play_sound(
        self,
        sound_file: str,
        position: SoundPosition,
        player: Player,
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
    ) -> None:
        self.map2d = map2d
        self.sound_map = sound_map
        self.player = player
        self.sound_service = sound_service or cast(
            _SoundServiceLike,
            sound_manager,
        )
        self.position_resolver = position_resolver or self._default_position

    def on_navigation(self, grid: Grid[MapTile], direction: Direction) -> bool:
        """Play movement/wall sounds and update map state.

        Returns True when the event should be handled (blocked movement), and
        False when grid navigation should continue.
        """
        is_handled = False

        try:
            self.map2d.character.directional_orientation = direction
            new_coordinates, tile = grid.get_next_cell(direction)
            if tile is None:
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
                is_handled = False
            else:
                self.play_wall_sound(grid, direction)
                is_handled = True
        except KeyError:
            pass

        return is_handled

    def on_border(self, grid: Grid[MapTile], direction: Direction) -> bool:
        """Play a border collision sound.

        Returns True if a wall sound mapping exists and was played.
        """
        return self.play_wall_sound(grid, direction)

    def play_wall_sound(
        self, grid: Grid[MapTile], direction: Direction
    ) -> bool:
        """Play the wall collision sound from the next tile position."""
        try:
            sound_file = self.sound_map["wall"]
            next_coordinates, _ = grid.get_next_cell(direction)
            self.sound_service.play_sound(
                sound_file,
                position=self.position_resolver(next_coordinates),
                player=self.player,
            )
            return True
        except KeyError:
            return False

    @staticmethod
    def _default_position(coordinates: Coordinates) -> SoundPosition:
        return (coordinates[0], coordinates[1], 0)
