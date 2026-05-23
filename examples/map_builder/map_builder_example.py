import sys
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent
PROJECT_SRC = EXAMPLE_DIR.parents[1] / "src"
sys.path.insert(0, str(PROJECT_SRC))


try:
    from sonartk.map_builder.map_2d import load_2d_map  # type: ignore
    from sonartk.map_builder.map_2d import Map2d, MapTile  # type: ignore
    from sonartk.map_builder.map_2d.map_object.character import Character  # type: ignore
    from sonartk.map_builder.map_2d.parser.csv_parser import CSVParser  # type: ignore
    from sonartk.ui import Window  # type: ignore
    from sonartk.ui.element import Grid  # type: ignore
    from sonartk.util import Direction  # type: ignore
except Exception:
    raise

tile_references: dict[str, MapTile] = {
    "0": MapTile("path"),
    "1": MapTile("wall", is_passable=False),
}


def main() -> None:
    csv_parser = CSVParser()
    character = Character("player", (1, 9), Direction.DOWN)
    map2d: Map2d = load_2d_map(
        map_name="Test",
        file_name=str(EXAMPLE_DIR / "test.csv"),
        parser=csv_parser,
        mapper=tile_mapper,
        character=character,
    )
    print(map2d.queries.find_path((1, 9), (0, 0)))
    window: Window = Window(caption="Map Test")
    grid: Grid = Grid(
        window,  # type: ignore[arg-type]
        label="",
        height=map2d.height,
        width=map2d.width,
        cells=map2d.tile_map,
        cell_class=MapTile,
        property_name="name",
    )
    grid.current_coordinates = (1, 9)
    window.add("grid", grid)
    window.open_window()


def tile_mapper(value: str) -> MapTile:
    return tile_references[value]


if __name__ == "__main__":
    main()
