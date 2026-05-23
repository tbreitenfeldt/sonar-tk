import sonartk.map_builder
import sonartk.map_builder.map_2d
import sonartk.map_builder.map_2d.map_object
import sonartk.map_builder.map_2d.parser

from sonartk.map_builder.map_2d import Map2d, MapTile, load_2d_map
from sonartk.map_builder.map_2d import (
    Map2dQueries,
    MapQueryResult,
    PathfindingResult,
    PathfindingState,
)
from sonartk.map_builder.map_2d.map_object import Character, MapObject
from sonartk.map_builder.map_2d.parser import CSVParser, JSONParser, MapParser


def test_map_builder_package_exports() -> None:
    assert sonartk.map_builder.__all__ == ["Map2d", "MapTile", "load_2d_map"]
    assert sonartk.map_builder.Map2d is Map2d
    assert sonartk.map_builder.MapTile is MapTile
    assert sonartk.map_builder.load_2d_map is load_2d_map


def test_map_2d_package_exports() -> None:
    assert sonartk.map_builder.map_2d.__all__ == [
        "Map2d",
        "Map2dQueries",
        "MapQueryResult",
        "PathfindingResult",
        "PathfindingState",
        "MapTile",
        "load_2d_map",
    ]
    assert Map2d is not None
    assert Map2dQueries is not None
    assert MapQueryResult is not None
    assert PathfindingResult is not None
    assert PathfindingState is not None
    assert MapTile is not None
    assert load_2d_map is not None


def test_map_object_package_exports() -> None:
    assert sonartk.map_builder.map_2d.map_object.__all__ == [
        "MapObject",
        "Character",
    ]
    assert MapObject is not None
    assert Character is not None


def test_parser_package_exports() -> None:
    assert sonartk.map_builder.map_2d.parser.__all__ == [
        "MapParser",
        "CSVParser",
        "JSONParser",
    ]
    assert MapParser is not None
    assert CSVParser is not None
    assert JSONParser is not None
