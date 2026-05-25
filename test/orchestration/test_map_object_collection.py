from __future__ import annotations

import random

import pytest

from sonartk.map_builder.map_2d.map_2d import Map2d
from sonartk.map_builder.map_2d.map_object.character import Character
from sonartk.map_builder.map_2d.map_object.map_object import MapObject
from sonartk.map_builder.map_2d.map_tile import MapTile
from sonartk.orchestration.map_object_collection import (
    MapObjectCollectionSession,
)
from sonartk.util import Direction


class Gem(MapObject):
    def __init__(
        self, name: str, coordinates: tuple[int, int], power: int
    ) -> None:
        super().__init__(name, coordinates)
        self.power = power


class Key(MapObject):
    def __init__(self, name: str, coordinates: tuple[int, int]) -> None:
        super().__init__(name, coordinates)


class BrokenGemFactory:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, index: int, coordinates: tuple[int, int]) -> Gem:
        self.calls += 1
        if self.calls == 2:
            raise RuntimeError("factory failed")

        return Gem(f"gem-{index}", coordinates, power=1)


def _make_map() -> Map2d:
    map2d = Map2d("arena", Character("hero", (1, 1), Direction.UP))
    map2d.add_row([MapTile("a"), MapTile("b"), MapTile("c")])
    map2d.add_row([MapTile("d"), MapTile("e"), MapTile("f")])
    map2d.add_row([MapTile("g"), MapTile("h"), MapTile("i")])
    return map2d


def test_map_object_collection_session_reset_collect_and_counts() -> None:
    map2d = _make_map()
    session = MapObjectCollectionSession[Gem](
        map2d,
        object_count=3,
        object_type=Gem,
        object_factory=lambda index, coordinates: Gem(
            f"gem-{index}",
            coordinates,
            power=10,
        ),
        excluded_coordinates={(1, 1)},
        object_label="gems",
        rng=random.Random(7),
    )

    session.reset()

    gems = [obj for obj in map2d.object_index.values() if isinstance(obj, Gem)]
    assert len(gems) == 3
    assert session.remaining_count == 3
    assert session.collected_count == 0
    assert all(gem.coordinates != (1, 1) for gem in gems)

    collected = session.collect_at(gems[0].coordinates)
    assert isinstance(collected, Gem)
    assert collected.power == 10
    assert session.remaining_count == 2
    assert session.collected_count == 1


def test_map_object_collection_session_has_object_at_and_collect_missing() -> (
    None
):
    map2d = _make_map()
    session = MapObjectCollectionSession[Gem](
        map2d,
        object_count=1,
        object_type=Gem,
        object_factory=lambda index, coordinates: Gem(
            f"gem-{index}",
            coordinates,
            power=5,
        ),
        object_label="gems",
        rng=random.Random(3),
    )
    session.reset()

    gem = next(
        obj for obj in map2d.object_index.values() if isinstance(obj, Gem)
    )

    assert session.has_object_at(gem.coordinates) is True
    assert session.collect_at((9, 9)) is None


def test_map_object_collection_session_reset_replaces_previous_spawn() -> None:
    map2d = _make_map()
    session = MapObjectCollectionSession[Gem](
        map2d,
        object_count=2,
        object_type=Gem,
        object_factory=lambda index, coordinates: Gem(
            f"gem-{index}",
            coordinates,
            power=7,
        ),
        object_label="gems",
        rng=random.Random(1),
    )

    session.reset()
    first_spawn = {
        obj.coordinates
        for obj in map2d.object_index.values()
        if isinstance(obj, Gem)
    }

    session.rng = random.Random(2)
    session.reset()
    second_spawn = {
        obj.coordinates
        for obj in map2d.object_index.values()
        if isinstance(obj, Gem)
    }

    assert len(first_spawn) == 2
    assert len(second_spawn) == 2
    assert first_spawn != second_spawn


def test_map_object_collection_session_raises_when_not_enough_passable_tiles() -> (
    None
):
    map2d = Map2d("tiny", Character("hero", (0, 0), Direction.UP))
    map2d.add_row([MapTile("wall", is_passable=False)])

    session = MapObjectCollectionSession[Gem](
        map2d,
        object_count=1,
        object_type=Gem,
        object_factory=lambda index, coordinates: Gem(
            f"gem-{index}",
            coordinates,
            power=1,
        ),
        object_label="gems",
        rng=random.Random(1),
    )

    with pytest.raises(ValueError, match="Cannot place"):
        session.reset()


def test_collect_at_does_not_remove_wrong_type_object() -> None:
    map2d = _make_map()
    key = Key("key-1", (0, 0))
    map2d.register_map_object(key)

    session = MapObjectCollectionSession[Gem](
        map2d,
        object_count=0,
        object_type=Gem,
        object_factory=lambda index, coordinates: Gem(
            f"gem-{index}",
            coordinates,
            power=1,
        ),
        object_label="gems",
        rng=random.Random(1),
    )

    assert session.collect_at((0, 0)) is None
    assert map2d.get_map_object_at((0, 0)) is key


def test_reset_removes_previously_tracked_object_even_if_moved() -> None:
    map2d = _make_map()
    session = MapObjectCollectionSession[Gem](
        map2d,
        object_count=1,
        object_type=Gem,
        object_factory=lambda index, coordinates: Gem(
            f"gem-{index}",
            coordinates,
            power=3,
        ),
        object_label="gems",
        rng=random.Random(4),
    )

    session.reset()
    first_gem = next(
        obj for obj in map2d.object_index.values() if isinstance(obj, Gem)
    )
    map2d.move_map_object(first_gem, (0, 0))

    session.reset()
    gems = [obj for obj in map2d.object_index.values() if isinstance(obj, Gem)]

    assert len(gems) == 1
    assert all(gem is not first_gem for gem in gems)


def test_negative_object_count_raises_value_error() -> None:
    map2d = _make_map()

    with pytest.raises(ValueError, match="object_count"):
        MapObjectCollectionSession[Gem](
            map2d,
            object_count=-1,
            object_type=Gem,
            object_factory=lambda index, coordinates: Gem(
                f"gem-{index}",
                coordinates,
                power=1,
            ),
            object_label="gems",
            rng=random.Random(1),
        )


def test_reset_avoids_preoccupied_passable_tiles() -> None:
    map2d = _make_map()
    blocker = Key("blocker", (0, 0))
    map2d.register_map_object(blocker)

    session = MapObjectCollectionSession[Gem](
        map2d,
        object_count=2,
        object_type=Gem,
        object_factory=lambda index, coordinates: Gem(
            f"gem-{index}",
            coordinates,
            power=1,
        ),
        object_label="gems",
        rng=random.Random(2),
    )

    session.reset()
    gems = [obj for obj in map2d.object_index.values() if isinstance(obj, Gem)]

    assert len(gems) == 2
    assert all(gem.coordinates != (0, 0) for gem in gems)
    assert map2d.get_map_object_at((0, 0)) is blocker


def test_reset_raises_when_occupied_tiles_reduce_capacity() -> None:
    map2d = _make_map()
    for coordinates in [
        (0, 0),
        (1, 0),
        (2, 0),
        (0, 1),
        (2, 1),
        (0, 2),
        (2, 2),
    ]:
        map2d.register_map_object(Key(f"k-{coordinates}", coordinates))

    session = MapObjectCollectionSession[Gem](
        map2d,
        object_count=2,
        object_type=Gem,
        object_factory=lambda index, coordinates: Gem(
            f"gem-{index}",
            coordinates,
            power=1,
        ),
        object_label="gems",
        rng=random.Random(1),
    )

    with pytest.raises(ValueError, match="Cannot place"):
        session.reset()


def test_required_coordinates_and_coordinate_predicate_filters() -> None:
    map2d = _make_map()
    required = {(0, 0), (1, 0), (2, 0), (2, 1)}

    session = MapObjectCollectionSession[Gem](
        map2d,
        object_count=2,
        object_type=Gem,
        object_factory=lambda index, coordinates: Gem(
            f"gem-{index}",
            coordinates,
            power=1,
        ),
        required_coordinates=required,
        forbidden_coordinates={(1, 0)},
        coordinate_predicate=lambda coordinates: coordinates[0] == 2,
        object_label="gems",
        rng=random.Random(9),
    )

    session.reset()
    gems = [obj for obj in map2d.object_index.values() if isinstance(obj, Gem)]
    gem_coordinates = {gem.coordinates for gem in gems}

    assert gem_coordinates.issubset(required)
    assert gem_coordinates == {(2, 0), (2, 1)}


def test_transactional_reset_rolls_back_on_factory_failure() -> None:
    map2d = _make_map()
    session = MapObjectCollectionSession[Gem](
        map2d,
        object_count=2,
        object_type=Gem,
        object_factory=lambda index, coordinates: Gem(
            f"gem-{index}",
            coordinates,
            power=2,
        ),
        object_label="gems",
        rng=random.Random(4),
    )
    session.reset()
    original_coordinates = {
        obj.coordinates
        for obj in map2d.object_index.values()
        if isinstance(obj, Gem)
    }

    broken_factory = BrokenGemFactory()
    session.object_factory = broken_factory

    with pytest.raises(RuntimeError, match="factory failed"):
        session.reset()

    remaining_coordinates = {
        obj.coordinates
        for obj in map2d.object_index.values()
        if isinstance(obj, Gem)
    }
    assert remaining_coordinates == original_coordinates
    assert session.remaining_count == 2
