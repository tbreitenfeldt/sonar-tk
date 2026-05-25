from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pytest

from sonartk.map_builder.map_2d.map_tile import MapTile
from sonartk.orchestration.map_sound_navigation import (
    AmbientTileSoundConfig,
    MapSoundNavigationController,
    TerrainAudioProfile,
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
        self.width = 3
        self.height = 3
        self._tiles_by_coordinates: dict[Coordinates, MapTile] = {
            (0, 0): MapTile("path", is_passable=True),
            (1, 0): MapTile("path", is_passable=True),
            (2, 0): MapTile("path", is_passable=True),
            (0, 1): MapTile("path", is_passable=True),
            (1, 1): MapTile("path", is_passable=True),
            (2, 1): MapTile("path", is_passable=True),
            (0, 2): MapTile("path", is_passable=True),
            (1, 2): MapTile("path", is_passable=True),
            (2, 2): MapTile("path", is_passable=True),
        }
        self.tile_map = list(self._tiles_by_coordinates.values())

    def move_character(
        self, character: _FakeCharacter, new_coordinates: Coordinates
    ) -> Optional[_FakeCharacter]:
        self.change_calls.append((character.coordinates, new_coordinates))
        character.coordinates = new_coordinates
        return None

    def get_tile(self, coordinates: Coordinates) -> MapTile:
        return self._tiles_by_coordinates[coordinates]


class _FakeListener:
    def __init__(self) -> None:
        self.position: tuple[int, int, int] = (0, 0, 0)


class _FakeSoundService:
    def __init__(self) -> None:
        self.listener = _FakeListener()
        self.play_calls: list[
            tuple[str, tuple[int, int, int], object, float, float, bool]
        ] = []

    def play_sound(
        self,
        sound_file: str,
        position: tuple[int, int, int],
        player: object,
        volume: float = 1.0,
        rolloff: float = 0.01,
        loop: bool = False,
        retrigger_if_same: bool = True,
    ) -> None:
        self.play_calls.append(
            (sound_file, position, player, volume, rolloff, loop)
        )


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
    assert sound_service.play_calls == [
        ("step.wav", (1, 2, 0), player, 1.0, 0.01, False)
    ]


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
    assert sound_service.play_calls == [
        ("wall.wav", (2, 3, 0), player, 1.0, 0.01, False)
    ]


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


def test_on_border_raises_when_wall_sound_is_missing() -> None:
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

    with pytest.raises(KeyError):
        controller.on_border(grid, Direction.DOWN)  # type: ignore[arg-type]

    assert sound_service.play_calls == []


def test_on_navigation_raises_when_tile_sound_is_missing() -> None:
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
        sound_map={"wall": "wall.wav"},
        player=player,  # type: ignore[arg-type]
        sound_service=sound_service,  # type: ignore[arg-type]
    )

    with pytest.raises(KeyError):
        controller.on_navigation(grid, Direction.RIGHT)  # type: ignore[arg-type]


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
    assert sound_service.play_calls == [
        ("step.wav", (20, 10, -1), player, 1.0, 0.01, False)
    ]


def test_on_navigation_invokes_success_callback_for_passable_move() -> None:
    map2d = _FakeMap2D()
    sound_service = _FakeSoundService()
    player = object()
    grid = _FakeGrid(
        current_coordinates=(1, 1),
        next_coordinates=(2, 1),
        next_tile=MapTile("path", is_passable=True),
    )
    success_calls: list[tuple[Coordinates, MapTile]] = []

    controller = MapSoundNavigationController(
        map2d=map2d,  # type: ignore[arg-type]
        sound_map={"path": "step.wav", "wall": "wall.wav"},
        player=player,  # type: ignore[arg-type]
        sound_service=sound_service,  # type: ignore[arg-type]
        on_move_success=lambda c, t: success_calls.append((c, t)),
    )

    is_handled = controller.on_navigation(grid, Direction.RIGHT)  # type: ignore[arg-type]

    assert is_handled is False
    assert len(success_calls) == 1
    assert success_calls[0][0] == (2, 1)
    assert success_calls[0][1].name == "path"


def test_on_navigation_invokes_blocked_callback_for_blocked_or_border() -> (
    None
):
    map2d = _FakeMap2D()
    sound_service = _FakeSoundService()
    player = object()
    blocked_calls: list[Direction] = []

    blocked_grid = _FakeGrid(
        current_coordinates=(1, 1),
        next_coordinates=(1, 2),
        next_tile=MapTile("wall", is_passable=False),
    )
    border_grid = _FakeGrid(
        current_coordinates=(0, 0),
        next_coordinates=(0, 0),
        next_tile=None,
    )

    controller = MapSoundNavigationController(
        map2d=map2d,  # type: ignore[arg-type]
        sound_map={"path": "step.wav", "wall": "wall.wav"},
        player=player,  # type: ignore[arg-type]
        sound_service=sound_service,  # type: ignore[arg-type]
        on_move_blocked=lambda d: blocked_calls.append(d),
    )

    assert controller.on_navigation(blocked_grid, Direction.UP) is True  # type: ignore[arg-type]
    assert controller.on_navigation(border_grid, Direction.LEFT) is True  # type: ignore[arg-type]
    assert blocked_calls == [Direction.UP, Direction.LEFT]


def test_update_ambient_sound_plays_nearest_configured_tile() -> None:
    map2d = _FakeMap2D()
    map2d.character.coordinates = (1, 1)
    map2d._tiles_by_coordinates[(0, 1)] = MapTile("river", is_passable=False)
    map2d._tiles_by_coordinates[(2, 2)] = MapTile("river", is_passable=False)
    sound_service = _FakeSoundService()
    movement_player = object()
    ambient_player = object()

    controller = MapSoundNavigationController(
        map2d=map2d,  # type: ignore[arg-type]
        sound_map={"path": "step.wav", "wall": "wall.wav"},
        player=movement_player,  # type: ignore[arg-type]
        sound_service=sound_service,  # type: ignore[arg-type]
        ambient_sound_map={
            "river": AmbientTileSoundConfig(
                sound_file="river_loop.wav",
                max_distance_tiles=2,
                volume=0.6,
                rolloff=0.4,
                loop=True,
                min_volume_at_max_distance=1.0,
            )
        },
        ambient_player=ambient_player,  # type: ignore[arg-type]
    )

    is_active = controller.update_ambient_sound()

    assert is_active is True
    assert sound_service.play_calls == [
        ("river_loop.wav", (0, 1, 0), ambient_player, 0.6, 0.4, True)
    ]


def test_update_ambient_sound_stops_player_when_no_emitter_in_range() -> None:
    map2d = _FakeMap2D()
    map2d.character.coordinates = (1, 1)
    map2d._tiles_by_coordinates[(0, 0)] = MapTile("river", is_passable=False)
    sound_service = _FakeSoundService()
    movement_player = object()
    ambient_player = _FakeAmbientPlayer()

    controller = MapSoundNavigationController(
        map2d=map2d,  # type: ignore[arg-type]
        sound_map={"path": "step.wav", "wall": "wall.wav"},
        player=movement_player,  # type: ignore[arg-type]
        sound_service=sound_service,  # type: ignore[arg-type]
        ambient_sound_map={
            "river": AmbientTileSoundConfig(
                sound_file="river_loop.wav",
                max_distance_tiles=0,
            )
        },
        ambient_player=ambient_player,  # type: ignore[arg-type]
    )

    is_active = controller.update_ambient_sound()

    assert is_active is False
    assert ambient_player.stop_calls == 1
    assert ambient_player.remove_calls == 1
    assert sound_service.play_calls == []


def test_on_navigation_updates_ambient_after_successful_move() -> None:
    map2d = _FakeMap2D()
    map2d.character.coordinates = (1, 1)
    map2d._tiles_by_coordinates[(2, 1)] = MapTile("path", is_passable=True)
    map2d._tiles_by_coordinates[(2, 2)] = MapTile("river", is_passable=False)
    sound_service = _FakeSoundService()
    movement_player = object()
    ambient_player = object()
    grid = _FakeGrid(
        current_coordinates=(1, 1),
        next_coordinates=(2, 1),
        next_tile=MapTile("path", is_passable=True),
    )

    controller = MapSoundNavigationController(
        map2d=map2d,  # type: ignore[arg-type]
        sound_map={"path": "step.wav", "wall": "wall.wav"},
        player=movement_player,  # type: ignore[arg-type]
        sound_service=sound_service,  # type: ignore[arg-type]
        ambient_sound_map={
            "river": AmbientTileSoundConfig(
                sound_file="river_loop.wav",
                min_volume_at_max_distance=1.0,
            )
        },
        ambient_player=ambient_player,  # type: ignore[arg-type]
    )

    controller.on_navigation(grid, Direction.RIGHT)  # type: ignore[arg-type]

    assert sound_service.play_calls == [
        ("step.wav", (2, 1, 0), movement_player, 1.0, 0.01, False),
        ("river_loop.wav", (2, 2, 0), ambient_player, 1.0, 0.3, True),
    ]


def test_init_rejects_negative_ambient_distance() -> None:
    map2d = _FakeMap2D()
    sound_service = _FakeSoundService()
    movement_player = object()
    ambient_player = object()

    try:
        MapSoundNavigationController(
            map2d=map2d,  # type: ignore[arg-type]
            sound_map={"path": "step.wav", "wall": "wall.wav"},
            player=movement_player,  # type: ignore[arg-type]
            sound_service=sound_service,  # type: ignore[arg-type]
            ambient_sound_map={
                "river": AmbientTileSoundConfig(
                    sound_file="river_loop.wav",
                    max_distance_tiles=-1,
                )
            },
            ambient_player=ambient_player,  # type: ignore[arg-type]
        )
    except ValueError as exc:
        assert "max_distance_tiles >= 0" in str(exc)
    else:
        raise AssertionError("Expected ValueError for negative distance")


def test_init_rejects_invalid_ambient_min_volume() -> None:
    map2d = _FakeMap2D()
    sound_service = _FakeSoundService()
    movement_player = object()
    ambient_player = object()

    try:
        MapSoundNavigationController(
            map2d=map2d,  # type: ignore[arg-type]
            sound_map={"path": "step.wav", "wall": "wall.wav"},
            player=movement_player,  # type: ignore[arg-type]
            sound_service=sound_service,  # type: ignore[arg-type]
            ambient_sound_map={
                "river": AmbientTileSoundConfig(
                    sound_file="river_loop.wav",
                    min_volume_at_max_distance=1.2,
                )
            },
            ambient_player=ambient_player,  # type: ignore[arg-type]
        )
    except ValueError as exc:
        assert "min_volume_at_max_distance" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid min volume")


def test_ambient_volume_scales_by_distance() -> None:
    map2d = _FakeMap2D()
    map2d._tiles_by_coordinates[(2, 2)] = MapTile("river", is_passable=False)
    sound_service = _FakeSoundService()
    movement_player = object()
    ambient_player = object()

    controller = MapSoundNavigationController(
        map2d=map2d,  # type: ignore[arg-type]
        sound_map={"path": "step.wav", "wall": "wall.wav"},
        player=movement_player,  # type: ignore[arg-type]
        sound_service=sound_service,  # type: ignore[arg-type]
        ambient_sound_map={
            "river": AmbientTileSoundConfig(
                sound_file="river_loop.wav",
                max_distance_tiles=4,
                volume=1.0,
                min_volume_at_max_distance=0.05,
                distance_curve_exponent=3.0,
            )
        },
        ambient_player=ambient_player,  # type: ignore[arg-type]
    )

    assert controller.update_ambient_sound((2, 1)) is True
    near_volume = sound_service.play_calls[-1][3]

    assert controller.update_ambient_sound((0, 0)) is True
    far_volume = sound_service.play_calls[-1][3]

    assert near_volume > far_volume
    assert far_volume < 0.2


def test_build_audio_maps_from_profiles_returns_movement_and_ambient() -> None:
    profiles = {
        "path": TerrainAudioProfile(movement_sound_file="step.wav"),
        "river": TerrainAudioProfile(
            is_passable=False,
            movement_sound_file="wall.wav",
            ambient_sound=AmbientTileSoundConfig(sound_file="river.wav"),
        ),
    }

    sound_map, ambient_map = (
        MapSoundNavigationController.build_audio_maps_from_profiles(profiles)
    )

    assert sound_map == {"path": "step.wav", "river": "wall.wav"}
    assert ambient_map["river"].sound_file == "river.wav"


def test_build_tile_reference_from_profiles_uses_passability() -> None:
    profiles = {
        "path": TerrainAudioProfile(is_passable=True),
        "river": TerrainAudioProfile(is_passable=False),
    }

    tile_reference = (
        MapSoundNavigationController.build_tile_reference_from_profiles(
            {"0": "path", "2": "river"},
            profiles,
        )
    )

    assert tile_reference["0"].is_passable is True
    assert tile_reference["2"].is_passable is False


def test_validate_sound_map_for_map_rejects_missing_passable_tile_sound() -> (
    None
):
    map2d = _FakeMap2D()
    sound_service = _FakeSoundService()

    controller = MapSoundNavigationController(
        map2d=map2d,  # type: ignore[arg-type]
        sound_map={"wall": "wall.wav"},
        player=object(),  # type: ignore[arg-type]
        sound_service=sound_service,  # type: ignore[arg-type]
    )

    try:
        controller.validate_sound_map_for_map()
    except ValueError as exc:
        assert "Missing movement sounds for passable tiles" in str(exc)
    else:
        raise AssertionError("Expected ValueError for missing passable sound")


def test_validate_sound_map_for_map_rejects_missing_blocked_sound() -> None:
    map2d = _FakeMap2D()
    sound_service = _FakeSoundService()

    controller = MapSoundNavigationController(
        map2d=map2d,  # type: ignore[arg-type]
        sound_map={"path": "step.wav"},
        player=object(),  # type: ignore[arg-type]
        sound_service=sound_service,  # type: ignore[arg-type]
    )

    try:
        controller.validate_sound_map_for_map()
    except ValueError as exc:
        assert "Missing required blocked collision sound mapping" in str(exc)
    else:
        raise AssertionError("Expected ValueError for missing wall sound")


def test_validate_sound_map_for_map_supports_custom_blocked_sound_key() -> (
    None
):
    map2d = _FakeMap2D()
    sound_service = _FakeSoundService()

    controller = MapSoundNavigationController(
        map2d=map2d,  # type: ignore[arg-type]
        sound_map={"path": "step.wav", "blocked": "bump.wav"},
        player=object(),  # type: ignore[arg-type]
        sound_service=sound_service,  # type: ignore[arg-type]
        blocked_tile_sound_name="blocked",
    )

    controller.validate_sound_map_for_map()


class _FakeAmbientPlayer:
    def __init__(self) -> None:
        self.stop_calls = 0
        self.remove_calls = 0

    def stop(self) -> None:
        self.stop_calls += 1

    def remove(self) -> None:
        self.remove_calls += 1
