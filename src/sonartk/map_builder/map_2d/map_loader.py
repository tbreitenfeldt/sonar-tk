from typing import Any, Callable, TypeVar

from sonartk.map_builder.map_2d.map_2d import Map2d
from sonartk.map_builder.map_2d.map_object.character import Character
from sonartk.map_builder.map_2d.map_tile import MapTile
from sonartk.map_builder.map_2d.parser.map_parser import MapParser
from sonartk.map_builder.map_2d.parser.stop_parsing_exception import (
    StopParsingException,
)

T = TypeVar("T")


def load_2d_map(
    map_name: str,
    file_name: str,
    parser: MapParser[T],
    mapper: Callable[[T], MapTile],
    character: Character,
) -> Map2d:
    map2d: Map2d = Map2d(map_name, character)
    parser.open(file_name)

    while True:
        try:
            row: list[T] = parser.read()
            mapped_row: list[MapTile] = [mapper(tile) for tile in row]
            map2d.add_row(mapped_row)
        except StopParsingException:
            break

    parser.close()
    return map2d
