import sys
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent
PROJECT_SRC = EXAMPLE_DIR.parents[1] / "src"
sys.path.insert(0, str(PROJECT_SRC))

try:
    from sonartk.orchestration.game_builder import MapGridGameBuilder
    from sonartk.map_builder.map_2d import MapTile
    from sonartk.map_builder.map_2d.parser.csv_parser import CSVParser
    from sonartk.map_builder.map_2d.map_object.character import Character
    from sonartk.orchestration.map_sound_navigation import (
        MapSoundNavigationController,
    )
    from sonartk.ui.element.grid import Grid
    from sonartk.util import Direction
    from sonartk.sound import sound_manager
    from sonartk.sound.openal_lite.openal import Player
except Exception:
    raise

TILE_REFERENCE: dict[str, MapTile] = {
    "0": MapTile("path"),
    "1": MapTile("wall", is_passable=False),
}

SOUND_MAP = {
    "path": str(EXAMPLE_DIR / "step_dirt.wav"),
    "wall": str(EXAMPLE_DIR / "wall.wav"),
}


def main() -> None:
    character: Character = Character("Test Character", (1, 9), Direction.DOWN)
    map_navigation_player: Player = sound_manager.player_pool.get_player()
    builder = MapGridGameBuilder[str](caption="Test 2D Game").with_map(
        map_name="Test Map",
        file_name=str(EXAMPLE_DIR / "test.csv"),
        parser=CSVParser(),
        tile_mapper=tile_mapper,
        character=character,
    )
    map_navigation = MapSoundNavigationController(
        map2d=builder.map2d,
        sound_map=SOUND_MAP,
        player=map_navigation_player,
    )

    game = (
        builder.with_grid_options(
            label="",
            speak_coordinates_on_change=False,
            speak_value_on_change=False,
        )
        .on_navigation(map_navigation.on_navigation)
        .on_border(map_navigation.on_border)
        .build()
    )

    grid: Grid = game.grid
    window = game.window

    sound_manager.listener.position = (*grid.current_coordinates, 0)
    window.open_window(speak_current_element_on_window_focus=False)


def tile_mapper(map_value: str) -> MapTile:
    return TILE_REFERENCE[map_value]


if __name__ == "__main__":
    main()
