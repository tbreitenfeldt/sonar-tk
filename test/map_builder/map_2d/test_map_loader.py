from typing import Generic, TypeVar

import pytest

from sonartk.map_builder.map_2d.map_loader import load_2d_map
from sonartk.map_builder.map_2d.map_tile import MapTile
from sonartk.map_builder.map_2d.map_object.character import Character
from sonartk.map_builder.map_2d.parser.map_parser import MapParser
from sonartk.map_builder.map_2d.parser.stop_parsing_exception import (
    StopParsingException,
)
from sonartk.util import Direction

T = TypeVar("T")


class FakeParser(MapParser[T], Generic[T]):
    def __init__(self, rows: list[list[T]]) -> None:
        self.rows = rows
        self.index = 0
        self.opened_with = ""
        self.closed = False

    def open(self, file_name: str) -> None:
        self.opened_with = file_name

    def read(self) -> list[T]:
        if self.index >= len(self.rows):
            raise StopParsingException()
        row = self.rows[self.index]
        self.index += 1
        return row

    def close(self) -> None:
        self.closed = True


def test_load_2d_map_reads_until_stop_and_closes_parser() -> None:
    parser = FakeParser[str]([["g", "w"], ["w", "g"]])
    character = Character("hero", (0, 0), Direction.UP)

    def mapper(value: str) -> MapTile:
        return (
            MapTile("wall", is_passable=False)
            if value == "w"
            else MapTile("ground")
        )

    map2d = load_2d_map("test-map", "map.csv", parser, mapper, character)

    assert parser.opened_with == "map.csv"
    assert parser.closed is True
    assert map2d.name == "test-map"
    assert map2d.width == 2
    assert map2d.height == 2
    assert map2d.get_tile((0, 0)).name == "wall"
    assert map2d.get_tile((1, 1)).name == "wall"


def test_load_2d_map_with_empty_parser_data_still_closes() -> None:
    parser = FakeParser[str]([])
    character = Character("hero", (0, 0), Direction.UP)

    map2d = load_2d_map(
        "empty",
        "empty.csv",
        parser,
        lambda _: MapTile("ground"),
        character,
    )

    assert parser.closed is True
    assert map2d.width == 0
    assert map2d.height == 0


def test_load_2d_map_closes_parser_when_mapper_raises() -> None:
    parser = FakeParser[str]([["g", "w"]])
    character = Character("hero", (0, 0), Direction.UP)

    def failing_mapper(_value: str) -> MapTile:
        raise ValueError("mapper failed")

    with pytest.raises(ValueError, match="mapper failed"):
        load_2d_map("broken", "broken.csv", parser, failing_mapper, character)

    assert parser.closed is True
