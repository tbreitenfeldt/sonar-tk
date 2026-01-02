import sys


sys.path.insert(0, "../../src")


try:
    from sonartk.map_builder.map_2d import load_2d_map  # type: ignore
    from sonartk.map_builder.map_2d import Map2d, MapTile  # type: ignore
    from sonartk.map_builder.map_2d.parser.csv_parser import CSVParser  # type: ignore
    from sonartk.ui import Window  # type: ignore
    from sonartk.ui.element import Grid  # type: ignore
except Exception:
    raise

tile_references: dict[str, MapTile] = {
    "0": MapTile("path"),
    "1": MapTile("wall", is_passable=False),
}


def main() -> None:
    csv_parser = CSVParser()
    map2d: Map2d = load_2d_map(
        map_name="Test",
        file_name="test.csv",
        parser=csv_parser,
        mapper=tile_mapper,
    )
    print(map2d.find_path((1, 9), (0, 0)))
    window: Window = Window(caption="Map Test")
    grid: Grid = Grid(
        window,
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


main()
