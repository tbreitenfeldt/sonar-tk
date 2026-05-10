from typing import Optional

import pytest

from sonartk.map_builder.map_2d.map_2d import Map2d
from sonartk.map_builder.map_2d.map_tile import MapTile
from sonartk.map_builder.map_2d.map_object import MapObject
from sonartk.map_builder.map_2d.map_object.character import Character
from sonartk.util import Direction


def make_map() -> Map2d:
    character = Character("hero", (1, 1), Direction.UP, radius=3)
    map2d = Map2d("arena", character)
    map2d.add_row([MapTile("a"), MapTile("b"), MapTile("c")])
    map2d.add_row([MapTile("d"), MapTile("e"), MapTile("f")])
    map2d.add_row([MapTile("g"), MapTile("h"), MapTile("i")])
    return map2d


def test_map2d_init_sets_defaults_and_character_registration() -> None:
    character = Character("hero", (2, 3), Direction.LEFT)

    map2d = Map2d("world", character)

    assert map2d.name == "world"
    assert map2d.character is character
    assert map2d.width == 0
    assert map2d.height == 0
    assert map2d.characters[(2, 3)] is character


def test_add_row_sets_width_and_updates_height() -> None:
    map2d = Map2d("world", Character("hero", (0, 0), Direction.UP))

    map2d.add_row([MapTile("x"), MapTile("y")])
    map2d.add_row([MapTile("a"), MapTile("b")])

    assert map2d.width == 2
    assert map2d.height == 2


def test_add_row_rejects_inconsistent_width() -> None:
    map2d = Map2d("world", Character("hero", (0, 0), Direction.UP))
    map2d.add_row([MapTile("x"), MapTile("y")])

    with pytest.raises(IndexError):
        map2d.add_row([MapTile("too-short")])


def test_get_tile_returns_expected_tile() -> None:
    map2d = make_map()

    assert map2d.get_tile((0, 0)).name == "g"
    assert map2d.get_tile((2, 2)).name == "c"


def test_get_tile_raises_for_out_of_range_coordinates() -> None:
    map2d = make_map()

    with pytest.raises(IndexError):
        map2d.get_tile((-1, 0))
    with pytest.raises(IndexError):
        map2d.get_tile((0, -1))
    with pytest.raises(IndexError):
        map2d.get_tile((3, 0))
    with pytest.raises(IndexError):
        map2d.get_tile((0, 3))


def test_character_and_object_coordinate_changes() -> None:
    map2d = make_map()
    ally = Character("ally", (0, 0), Direction.RIGHT)
    obj = MapObject("switch", (1, 0))

    map2d.add_character((0, 0), ally)
    map2d.add_map_object((1, 0), obj)
    map2d.change_character_coordinates((0, 0), (2, 2), ally)
    map2d.change_map_object_coordinates((1, 0), (0, 2), obj)

    assert (0, 0) not in map2d.characters
    assert map2d.characters[(2, 2)] is ally
    assert (1, 0) not in map2d.objects
    assert map2d.objects[(0, 2)] is obj


def test_change_character_and_object_coordinates_raise_when_missing() -> None:
    map2d = make_map()
    character = Character("ghost", (5, 5), Direction.DOWN)
    obj = MapObject("orb", (5, 5))

    with pytest.raises(LookupError):
        map2d.change_character_coordinates((5, 5), (0, 0), character)
    with pytest.raises(LookupError):
        map2d.change_map_object_coordinates((5, 5), (0, 0), obj)


def test_check_coordinates_for_object_reports_tile_character_and_object() -> (
    None
):
    map2d = make_map()
    target_character = Character("target", (2, 1), Direction.UP)
    target_object = MapObject("chest", (2, 1))
    map2d.add_character((2, 1), target_character)
    map2d.add_map_object((2, 1), target_object)

    called: list[
        tuple[
            tuple[int, int],
            Optional[MapTile],
            Optional[Character],
            Optional[MapObject],
        ]
    ] = []

    def action(
        coordinates: tuple[int, int],
        tile: Optional[MapTile],
        character: Optional[Character],
        map_object: Optional[MapObject],
    ) -> None:
        called.append((coordinates, tile, character, map_object))

    map2d.check_coordinates_for_object((2, 1), action, tile_names=["f"])

    assert len(called) == 1
    coordinates, tile, character, map_object = called[0]
    assert coordinates == (2, 1)
    assert tile is not None and tile.name == "f"
    assert character is target_character
    assert map_object is target_object


def test_check_coordinates_for_object_ignores_out_of_range() -> None:
    map2d = make_map()
    calls: list[tuple[int, int]] = []

    def action(
        coordinates: tuple[int, int],
        tile: Optional[MapTile],
        character: Optional[Character],
        map_object: Optional[MapObject],
    ) -> None:
        _ = tile, character, map_object
        calls.append(coordinates)

    map2d.check_coordinates_for_object((-1, 1), action)

    assert calls == []


def test_check_radius_scans_surrounding_tiles() -> None:
    map2d = make_map()

    seen: list[tuple[int, int]] = []

    def action(
        coordinates: tuple[int, int],
        tile: Optional[MapTile],
        character: Optional[Character],
        map_object: Optional[MapObject],
    ) -> None:
        _ = tile, character, map_object
        seen.append(coordinates)

    map2d.check_radius((1, 1), action)

    expected = {
        (1, 2),
        (2, 2),
        (2, 1),
        (2, 0),
        (1, 0),
        (0, 0),
        (0, 1),
        (0, 2),
    }
    assert set(seen) == expected


def test_find_path_returns_empty_when_unreachable() -> None:
    map2d = make_map()
    for tile in map2d.tile_map:
        tile.is_passable = False

    path = map2d.find_path((0, 0), (2, 2))

    assert path == []


def test_find_path_returns_path_when_reachable() -> None:
    map2d = make_map()

    path = map2d.find_path((0, 0), (1, 0))

    assert path[0] == (0, 0)
    assert path[-1] == (1, 0)


def test_find_path_handles_revisits_without_requeueing() -> None:
    map2d = make_map()

    # Use an out-of-range destination so traversal explores all reachable
    # nodes and encounters already-visited neighbors in the open grid.
    path = map2d.find_path((0, 0), (5, 5))

    assert path == []


def test_get_adjacent_passable_coordinates_and_passable_rules() -> None:
    map2d = make_map()

    map2d.get_tile((1, 2)).is_passable = False
    map2d.get_tile((2, 1)).is_one_way = True
    map2d.get_tile((2, 1)).is_jumpable = False
    map2d.get_tile((0, 1)).is_one_way = True
    map2d.get_tile((0, 1)).is_jumpable = True

    adjacent = map2d.get_adjacent_passable_coordinates((1, 1))

    assert (1, 2) not in adjacent
    assert (2, 1) not in adjacent
    assert (0, 1) in adjacent
    assert (1, 0) in adjacent


def test_is_coordinates_in_range() -> None:
    map2d = make_map()

    assert map2d.is_coordinates_in_range((0, 0)) is True
    assert map2d.is_coordinates_in_range((2, 2)) is True
    assert map2d.is_coordinates_in_range((-1, 0)) is False
    assert map2d.is_coordinates_in_range((0, 3)) is False
