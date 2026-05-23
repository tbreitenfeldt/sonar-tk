from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sonartk.map_builder.map_2d.map_tile import MapTile
from sonartk.orchestration.map_sound_navigation import (
    MapSoundNavigationController,
)
from sonartk.util import Coordinates, Direction


@dataclass
class _FakeCharacter:
    directional_orientation: Direction
    coordinates: Coordinates = (1, 1)


class _FakeMap2D:
    def __init__(self) -> None:
        self.character = _FakeCharacter(directional_orientation=Direction.UP)
        self.change_calls: list[tuple[Coordinates, Coordinates]] = []

    def move_character(
        self, character: _FakeCharacter, new_coordinates: Coordinates
    ) -> Optional[_FakeCharacter]:
        self.change_calls.append((character.coordinates, new_coordinates))
        character.coordinates = new_coordinates
        return None


class _FakeListener:
    def __init__(self) -> None:
        self.position: tuple[int, int, int] = (0, 0, 0)


class _FakeSoundService:
    def __init__(self) -> None:
        self.listener = _FakeListener()
        self.play_calls: list[tuple[str, tuple[int, int, int], object]] = []

    def play_sound(
        self,
        sound_file: str,
        position: tuple[int, int, int],
        player: object,
    ) -> None:
        self.play_calls.append((sound_file, position, player))


class _FakeGrid:
    def __init__(
        self,
        current_coordinates: Coordinates,
        next_coordinates: Coordinates,
        next_tile: Optional[MapTile],
    ) -> None:
        self.current_coordinates = current_coordinates
        self._next_coordinates = next_coordinates
        self._next_tile = next_tile

    def get_next_cell(
        self, direction: Direction
    ) -> tuple[Coordinates, Optional[MapTile]]:
        return self._next_coordinates, self._next_tile


def test_on_navigation_moves_and_plays_sound_for_passable_tile() -> None:
    map2d = _FakeMap2D()
    sound_service = _FakeSoundService()
    player = object()
    grid = _FakeGrid(
        current_coordinates=(1, 1),
        next_coordinates=(1, 2),
        next_tile=MapTile("path", is_passable=True),
    )

    controller = MapSoundNavigationController(
        map2d=map2d,  # type: ignore[arg-type]
        sound_map={"path": "step.wav", "wall": "wall.wav"},
        player=player,  # type: ignore[arg-type]
        sound_service=sound_service,  # type: ignore[arg-type]
    )

    is_handled = controller.on_navigation(grid, Direction.DOWN)  # type: ignore[arg-type]

    assert is_handled is False
    assert map2d.character.directional_orientation is Direction.DOWN
    assert map2d.change_calls == [((1, 1), (1, 2))]
    assert sound_service.listener.position == (1, 2, 0)
    assert sound_service.play_calls == [("step.wav", (1, 2, 0), player)]


def test_on_navigation_blocks_and_plays_wall_sound_for_impassable_tile() -> (
    None
):
    map2d = _FakeMap2D()
    sound_service = _FakeSoundService()
    player = object()
    grid = _FakeGrid(
        current_coordinates=(2, 2),
        next_coordinates=(2, 3),
        next_tile=MapTile("wall", is_passable=False),
    )

    controller = MapSoundNavigationController(
        map2d=map2d,  # type: ignore[arg-type]
        sound_map={"path": "step.wav", "wall": "wall.wav"},
        player=player,  # type: ignore[arg-type]
        sound_service=sound_service,  # type: ignore[arg-type]
    )

    is_handled = controller.on_navigation(grid, Direction.RIGHT)  # type: ignore[arg-type]

    assert is_handled is True
    assert map2d.change_calls == []
    assert sound_service.play_calls == [("wall.wav", (2, 3, 0), player)]


def test_on_navigation_handles_none_tile_as_border() -> None:
    map2d = _FakeMap2D()
    sound_service = _FakeSoundService()
    player = object()
    grid = _FakeGrid(
        current_coordinates=(0, 0),
        next_coordinates=(0, 0),
        next_tile=None,
    )

    controller = MapSoundNavigationController(
        map2d=map2d,  # type: ignore[arg-type]
        sound_map={"path": "step.wav", "wall": "wall.wav"},
        player=player,  # type: ignore[arg-type]
        sound_service=sound_service,  # type: ignore[arg-type]
    )

    is_handled = controller.on_navigation(grid, Direction.LEFT)  # type: ignore[arg-type]

    assert is_handled is True
    assert map2d.change_calls == []
    assert sound_service.play_calls == []


def test_on_border_returns_false_when_wall_sound_is_missing() -> None:
    map2d = _FakeMap2D()
    sound_service = _FakeSoundService()
    player = object()
    grid = _FakeGrid(
        current_coordinates=(4, 4),
        next_coordinates=(4, 5),
        next_tile=MapTile("wall", is_passable=False),
    )

    controller = MapSoundNavigationController(
        map2d=map2d,  # type: ignore[arg-type]
        sound_map={"path": "step.wav"},
        player=player,  # type: ignore[arg-type]
        sound_service=sound_service,  # type: ignore[arg-type]
    )

    is_handled = controller.on_border(grid, Direction.DOWN)  # type: ignore[arg-type]

    assert is_handled is False
    assert sound_service.play_calls == []


def test_custom_position_resolver_is_used_for_sound_position() -> None:
    map2d = _FakeMap2D()
    sound_service = _FakeSoundService()
    player = object()
    grid = _FakeGrid(
        current_coordinates=(1, 1),
        next_coordinates=(2, 1),
        next_tile=MapTile("path", is_passable=True),
    )

    controller = MapSoundNavigationController(
        map2d=map2d,  # type: ignore[arg-type]
        sound_map={"path": "step.wav", "wall": "wall.wav"},
        player=player,  # type: ignore[arg-type]
        sound_service=sound_service,  # type: ignore[arg-type]
        position_resolver=lambda c: (c[0] * 10, c[1] * 10, -1),
    )

    controller.on_navigation(grid, Direction.RIGHT)  # type: ignore[arg-type]

    assert sound_service.listener.position == (20, 10, -1)
    assert sound_service.play_calls == [("step.wav", (20, 10, -1), player)]
