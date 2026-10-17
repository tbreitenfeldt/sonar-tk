from __future__ import annotations

from typing import Any, Optional

import pytest

from sonartk.map_builder.map_2d.map_document import (
    ElevationArea,
    MapDocument,
    MapDocumentError,
    build_map2d_from_document,
)
from sonartk.map_builder.map_2d.map_tile import MapTile
from sonartk.orchestration.map_sound_navigation import (
    MapSoundNavigationController,
    TerrainAudioProfile,
)
from sonartk.util import Coordinates, Direction


def tile_factory(terrain: str) -> MapTile:
    return MapTile(terrain, is_passable=terrain != "rock")


def document(**overrides: Any) -> MapDocument:
    values: dict[str, Any] = {
        "key": "bluff",
        "legend": {"s": "sand", "r": "rock"},
        "rows": ("sssssss", "sssssss", "sssssss"),
        "start": (0, 0),
    }
    values.update(overrides)
    return MapDocument(**values)


class TestElevationArea:
    def test_flat_area_has_one_height(self) -> None:
        area = ElevationArea((1, 0, 2, 1), z=4)
        assert area.height_at((1, 1)) == 4
        assert area.height_at((3, 1)) is None
        assert area.tiles() == {(1, 0): 4, (2, 0): 4, (1, 1): 4, (2, 1): 4}

    @pytest.mark.parametrize(
        "direction,low,high",
        [
            ("north", (1, 0), (1, 2)),
            ("south", (1, 2), (1, 0)),
            ("east", (0, 1), (2, 1)),
            ("west", (2, 1), (0, 1)),
        ],
    )
    def test_ramp_rises_toward_its_direction(
        self, direction: str, low: Coordinates, high: Coordinates
    ) -> None:
        area = ElevationArea((0, 0, 2, 2), z=3, rises_toward=direction)
        assert area.height_at(low) == 3
        assert area.height_at(high) == 5


class TestDocumentElevations:
    def test_height_defaults_to_zero(self) -> None:
        assert document().elevation_at((2, 2)) == 0

    def test_later_areas_override_earlier_ones(self) -> None:
        doc = document(
            elevations=(
                ElevationArea((0, 0, 3, 2), z=2),
                ElevationArea((1, 1, 2, 1), z=9),
            )
        )
        assert doc.elevation_at((0, 0)) == 2
        assert doc.elevation_at((1, 1)) == 9
        assert doc.elevation_map()[(1, 1)] == 9

    def test_level_zero_tiles_are_left_out_of_the_map(self) -> None:
        doc = document(elevations=(ElevationArea((0, 0, 1, 0), z=0),))
        assert doc.elevation_map() == {}

    def test_round_trips_through_dicts(self) -> None:
        doc = document(
            elevations=(
                ElevationArea((0, 0, 3, 0), z=1, rises_toward="east"),
                ElevationArea((4, 0, 6, 2), z=4),
            )
        )
        data = doc.to_dict()
        assert data["elevations"] == [
            {"area": [0, 0, 3, 0], "z": 1, "rises_toward": "east"},
            {"area": [4, 0, 6, 2], "z": 4},
        ]
        assert MapDocument.from_dict(data) == doc

    def test_documents_without_elevations_stay_unchanged(self) -> None:
        assert "elevations" not in document().to_dict()

    @pytest.mark.parametrize(
        "area",
        [
            ElevationArea((2, 0, 1, 0), z=1),
            ElevationArea((0, 0, 9, 0), z=1),
            ElevationArea((0, 0, 1, 0), z=1, rises_toward="up"),
            ElevationArea((0, 0, 1, 0), z=1.5),  # type: ignore[arg-type]
            ElevationArea((0, 0, 1, 0), z=True),
        ],
    )
    def test_bad_areas_are_rejected(self, area: ElevationArea) -> None:
        with pytest.raises(MapDocumentError):
            document(elevations=(area,))

    @pytest.mark.parametrize(
        "item",
        [
            {"z": 1},
            {"area": [0, 0, 1], "z": 1},
            {"area": [0, 0, 1, "a"], "z": 1},
            {"area": [0, 0, 1, 0]},
        ],
    )
    def test_malformed_elevation_data_is_rejected(
        self, item: dict[str, Any]
    ) -> None:
        data = document().to_dict()
        data["elevations"] = [item]
        with pytest.raises(MapDocumentError):
            MapDocument.from_dict(data)


class TestMap2dElevation:
    def test_built_map_knows_heights(self) -> None:
        doc = document(elevations=(ElevationArea((1, 0, 3, 0), 1, "east"),))
        map2d = build_map2d_from_document(doc, tile_factory)
        assert [map2d.elevation_at((x, 0)) for x in range(5)] == [
            0,
            1,
            2,
            3,
            0,
        ]

    def test_a_gentle_ramp_has_no_steep_steps(self) -> None:
        doc = document(
            rows=("sssssss",),
            elevations=(
                ElevationArea((1, 0, 3, 0), 1, "east"),
                ElevationArea((4, 0, 6, 0), 3),
            ),
        )
        assert build_map2d_from_document(doc, tile_factory).steep_steps() == []

    def test_a_sudden_rise_is_reported_once(self) -> None:
        doc = document(
            rows=("sssssss",), elevations=(ElevationArea((1, 0, 6, 0), z=2),)
        )
        map2d = build_map2d_from_document(doc, tile_factory)
        assert map2d.steep_steps() == [((0, 0), (1, 0))]

    def test_steep_steps_in_the_north_direction_are_found(self) -> None:
        doc = document(elevations=(ElevationArea((0, 1, 0, 1), z=5),))
        steps = build_map2d_from_document(doc, tile_factory).steep_steps()
        assert ((0, 0), (0, 1)) in steps
        assert ((0, 1), (0, 2)) in steps

    def test_cliffs_of_impassable_terrain_are_not_steps(self) -> None:
        doc = document(
            rows=("ssrss", "ssrss"),
            elevations=(ElevationArea((3, 0, 4, 1), z=9),),
        )
        assert build_map2d_from_document(doc, tile_factory).steep_steps() == []


class _Listener:
    position: tuple[int, int, int] = (0, 0, 0)


class _Sound:
    def __init__(self) -> None:
        self.listener = _Listener()
        self.calls: list[dict[str, Any]] = []

    def play_sound(self, sound_file: str, **kwargs: Any) -> None:
        self.calls.append({"file": sound_file, **kwargs})


class _Grid:
    def __init__(
        self,
        here: Coordinates,
        direction_target: Optional[Coordinates],
        map2d: Any,
    ) -> None:
        self.map2d = map2d
        self.target = direction_target

    def get_next_cell(
        self, direction: Direction
    ) -> tuple[Coordinates, Optional[MapTile]]:
        assert self.target is not None
        return self.target, self.map2d.get_tile(self.target)


def _controller(
    doc: MapDocument,
    start: Coordinates,
    climb: float = 1.1,
    descend: float = 0.9,
) -> tuple[MapSoundNavigationController, _Sound, Any]:
    map2d = build_map2d_from_document(doc, tile_factory, spawn=start)
    sound = _Sound()
    profiles = {
        "sand": TerrainAudioProfile(
            movement_sound_file="sand.wav",
            climb_pitch=climb,
            descend_pitch=descend,
        ),
        "rock": TerrainAudioProfile(
            is_passable=False, movement_sound_file="wall.wav"
        ),
        "wall": TerrainAudioProfile(
            is_passable=False, movement_sound_file="wall.wav"
        ),
    }
    controller = MapSoundNavigationController.from_terrain_audio_profiles(
        map2d=map2d,
        terrain_audio_profiles=profiles,
        player=object(),  # type: ignore[arg-type]
        sound_service=sound,  # type: ignore[arg-type]
    )
    return controller, sound, map2d


def _step(
    controller: MapSoundNavigationController, map2d: Any, target: Coordinates
) -> bool:
    return controller.on_navigation(
        _Grid(map2d.character.coordinates, target, map2d),  # type: ignore[arg-type]
        Direction.RIGHT,
    )


class TestNavigation:
    def doc(self) -> MapDocument:
        return document(
            elevations=(ElevationArea((1, 0, 3, 0), 1, "east"),),
        )

    def test_sounds_and_listener_follow_the_height(self) -> None:
        controller, sound, map2d = _controller(self.doc(), (0, 0))
        assert _step(controller, map2d, (1, 0)) is False
        assert sound.listener.position == (1, 0, 1)
        assert sound.calls[0]["position"] == (1, 0, 1)

    def test_climbing_raises_the_pitch(self) -> None:
        controller, sound, map2d = _controller(self.doc(), (0, 0))
        _step(controller, map2d, (1, 0))
        assert sound.calls[0]["pitch"] == 1.1

    def test_descending_lowers_the_pitch(self) -> None:
        controller, sound, map2d = _controller(self.doc(), (2, 0))
        _step(controller, map2d, (1, 0))
        assert sound.calls[0]["pitch"] == 0.9

    def test_level_steps_leave_the_pitch_alone(self) -> None:
        controller, sound, map2d = _controller(self.doc(), (4, 0))
        _step(controller, map2d, (5, 0))
        assert "pitch" not in sound.calls[0]

    def test_terrain_without_slope_pitches_leaves_it_alone(self) -> None:
        controller, sound, map2d = _controller(self.doc(), (0, 0), 1.0, 1.0)
        _step(controller, map2d, (1, 0))
        assert "pitch" not in sound.calls[0]

    def test_a_step_too_high_is_blocked(self) -> None:
        doc = document(elevations=(ElevationArea((1, 0, 6, 0), z=2),))
        blocked: list[Direction] = []
        controller, sound, map2d = _controller(doc, (0, 0))
        controller.on_move_blocked = blocked.append
        assert _step(controller, map2d, (1, 0)) is True
        assert map2d.character.coordinates == (0, 0)
        assert sound.calls[0]["file"] == "wall.wav"
        assert blocked == [Direction.RIGHT]

    def test_a_step_too_high_without_a_blocked_callback(self) -> None:
        doc = document(elevations=(ElevationArea((1, 0, 6, 0), z=2),))
        controller, _, map2d = _controller(doc, (0, 0))
        assert _step(controller, map2d, (1, 0)) is True
