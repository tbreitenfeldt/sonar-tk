from typing import Generic, TypeVar

import pytest

from sonartk.map_builder.map_2d import Map2d, MapTile
from sonartk.map_builder.map_2d.map_object.character import Character
from sonartk.map_builder.map_2d.parser.map_parser import MapParser
from sonartk.map_builder.map_2d.parser.stop_parsing_exception import (
    StopParsingException,
)
from sonartk.orchestration.game_builder import MapGridGameBuilder
from sonartk.ui.element.grid import Grid
from sonartk.ui.screen.container_screen import ContainerScreen
from sonartk.ui.window import Window
from sonartk.util import Direction

T = TypeVar("T")


class FakeParser(MapParser[T], Generic[T]):
    def __init__(self, rows: list[list[T]]) -> None:
        self.rows = rows
        self.index = 0
        self.closed = False

    def open(self, file_name: str) -> None:
        self.file_name = file_name

    def read(self) -> list[T]:
        if self.index >= len(self.rows):
            raise StopParsingException()

        row = self.rows[self.index]
        self.index += 1
        return row

    def close(self) -> None:
        self.closed = True


def tile_mapper(value: str) -> MapTile:
    if value == "1":
        return MapTile("wall", is_passable=False)
    return MapTile("path")


def test_build_raises_if_map_not_configured() -> None:
    builder = MapGridGameBuilder[str](caption="Test")

    with pytest.raises(ValueError, match="No map configured"):
        builder.build()


def test_build_wires_window_screen_grid_with_defaults() -> None:
    builder = MapGridGameBuilder[str](caption="Test").with_map(
        map_name="test-map",
        file_name="test.csv",
        parser=FakeParser([["0", "1"], ["1", "0"]]),
        tile_mapper=tile_mapper,
        character=Character("Hero", (1, 1), Direction.UP),
    )

    built = builder.build()

    assert isinstance(built.window, Window)
    assert isinstance(built.screen, ContainerScreen)
    assert isinstance(built.grid, Grid)
    assert isinstance(built.map2d, Map2d)
    assert built.window.state_machine.contains("main")
    assert built.screen.state_machine.contains("grid")
    assert built.grid.width == 2
    assert built.grid.height == 2
    assert built.grid.current_coordinates == (1, 1)


def test_with_loaded_map_is_supported() -> None:
    character = Character("Hero", (0, 0), Direction.DOWN)
    map2d = Map2d("loaded", character)
    map2d.add_row([MapTile("path")])

    built = (
        MapGridGameBuilder[str](caption="Test").with_loaded_map(map2d).build()
    )

    assert built.map2d is map2d
    assert built.grid.current_coordinates == (0, 0)


def test_navigation_and_border_handlers_are_attached() -> None:
    calls = {"navigation": 0, "border": 0}

    def on_navigation(grid: Grid[MapTile], direction: Direction) -> bool:
        calls["navigation"] += 1
        return False

    def on_border(grid: Grid[MapTile], direction: Direction) -> bool:
        calls["border"] += 1
        return True

    built = (
        MapGridGameBuilder[str](caption="Test")
        .with_map(
            map_name="test-map",
            file_name="test.csv",
            parser=FakeParser([["0"]]),
            tile_mapper=tile_mapper,
            character=Character("Hero", (0, 0), Direction.UP),
        )
        .on_navigation(on_navigation)
        .on_border(on_border)
        .build()
    )

    built.grid.dispatch_event("on_navigation", built.grid, Direction.UP)
    built.grid.dispatch_event("on_border", built.grid, Direction.UP)

    assert calls["navigation"] == 1
    assert calls["border"] == 1
