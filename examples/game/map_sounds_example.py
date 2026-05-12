import sys
from pathlib import Path
from typing import cast

from pyglet.window import key
import pyglet.clock


EXAMPLE_DIR = Path(__file__).resolve().parent
PROJECT_SRC = EXAMPLE_DIR.parents[1] / "src"
sys.path.insert(0, str(PROJECT_SRC))

try:
    from sonartk.ui.window import Window
    from sonartk.ui.screen import ContainerScreen
    from sonartk.map_builder.map_2d import load_2d_map
    from sonartk.map_builder.map_2d import Map2d, MapTile
    from sonartk.map_builder.map_2d.parser.csv_parser import CSVParser
    from sonartk.ui.element.grid import Grid
    from sonartk.map_builder.map_2d.map_object.character import Character
    from sonartk.util import Direction
    from sonartk.sound import sound_manager
    from sonartk.sound.openal_lite.openal import Player
    from sonartk.util import Coordinates
except Exception:
    raise

tile_reference: dict[str, MapTile] = {
    "0": MapTile("path"),
    "1": MapTile("wall", is_passable=False),
}


def main() -> None:
    window: Window = Window(caption="Test 2D Game")
    container = ContainerScreen(window)
    character: Character = Character("Test Character", (1, 9), Direction.DOWN)
    map2d: Map2d = load_2d_map(
        "Test Map",
        str(EXAMPLE_DIR / "test.csv"),
        CSVParser(),
        tile_mapper,
        character,
    )
    grid: Grid = Grid(
        container,
        label="",
        height=map2d.height,
        width=map2d.width,
        cells=map2d.tile_map,
        cell_class=MapTile,
        property_name="name",
        speak_coordinates_on_change=False,
        speak_value_on_change=False,
    )
    grid.current_coordinates = map2d.character.coordinates
    sound_manager.listener.position = (*grid.current_coordinates, 0)
    map_navigation_player: Player = sound_manager.player_pool.get_player()
    grid.push_handlers(
        on_navigation=(
            lambda grid, direction: on_map_navigation(
                grid, map2d, direction, sound_map, map_navigation_player
            )
        )
    )
    grid.push_handlers(
        on_border=(
            lambda grid, direction: on_map_border(
                grid, direction, sound_map, map_navigation_player
            )
        )
    )
    # Note: current_position would be set here in actual implementation
    container.add("grid", grid)
    window.add(map2d.name, container)
    window.open_window()


def tile_mapper(map_value: str) -> MapTile:
    return tile_reference[map_value]


def on_map_navigation(
    grid: Grid,
    map2d: Map2d,
    direction: Direction,
    sound_map: dict[str, str],
    map_navigation_player: Player,
) -> bool:
    is_handled: bool = False

    try:
        map2d.character.directional_orientation = direction
        current_coordinates: Coordinates = grid.current_coordinates
        new_coordinates, tile = grid.get_next_cell(direction)
        if tile is None:
            return True

        # current_position used for future 3D sound positioning
        # current_position would be (*current_coordinates, 0)
        new_position = cast(tuple[int], (*new_coordinates, 0))
        sound_file: str = sound_map[tile.name]

        if tile.is_passable:
            map2d.change_character_coordinates(
                current_coordinates, new_coordinates, map2d.character
            )
            sound_manager.listener.position = new_position
            sound_manager.play_sound(
                sound_file, position=new_position, player=map_navigation_player
            )
            is_handled = False  # propigate the event allowing the grid position to change
        else:
            play_wall_sound(grid, direction, sound_map, map_navigation_player)
            is_handled = True  # stop event propigation to prevent grid position from changing
    except KeyError:
        pass

    return is_handled


def on_map_border(
    grid: Grid,
    direction: Direction,
    sound_map: dict[str, str],
    map_navigation_player: Player,
) -> bool:
    return play_wall_sound(grid, direction, sound_map, map_navigation_player)


def play_wall_sound(
    grid: Grid,
    direction: Direction,
    sound_map: dict[str, str],
    map_navigation_player: Player,
) -> bool:
    try:
        sound_file: str = sound_map["wall"]
        next_coordinates, _ = grid.get_next_cell(direction)
        sound_manager.play_sound(
            sound_file,
            position=cast(tuple[int], (*next_coordinates, 0)),
            player=map_navigation_player,
        )
        return True
    except KeyError:
        return False


sound_map = {
    "path": str(EXAMPLE_DIR / "step_dirt.wav"),
    "wall": str(EXAMPLE_DIR / "wall.wav"),
}


main()
