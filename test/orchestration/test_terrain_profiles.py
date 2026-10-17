import json
from pathlib import Path

import pytest

from sonartk.orchestration import (
    TerrainProfileError,
    load_terrain_profiles,
    terrain_profiles_from_dict,
    terrain_tile_factory,
)


def test_profiles_default_to_passable_and_silent() -> None:
    profiles = terrain_profiles_from_dict({"grass": {}})

    assert profiles["grass"].is_passable
    assert profiles["grass"].movement_sound_file is None
    assert profiles["grass"].ambient_sound is None
    assert profiles["grass"].climb_pitch == 1.0
    assert profiles["grass"].descend_pitch == 1.0


def test_slope_pitches_are_read() -> None:
    profiles = terrain_profiles_from_dict(
        {"path": {"climb_pitch": 1.08, "descend_pitch": 1}}
    )

    assert profiles["path"].climb_pitch == 1.08
    assert profiles["path"].descend_pitch == 1.0


@pytest.mark.parametrize("bad", [0, -1, "high", True, None])
def test_bad_slope_pitches_are_rejected(bad: object) -> None:
    with pytest.raises(TerrainProfileError, match="climb_pitch"):
        terrain_profiles_from_dict({"path": {"climb_pitch": bad}})


def test_sounds_go_through_the_resolver() -> None:
    profiles = terrain_profiles_from_dict(
        {
            "sea": {
                "passable": False,
                "movement_sound": "wall",
                "ambient": {
                    "sound": "ocean",
                    "max_distance_tiles": 40,
                    "channel": "ambience",
                },
            }
        },
        resolve_sound=lambda name: f"/audio/{name}.wav",
    )

    sea = profiles["sea"]
    assert not sea.is_passable
    assert sea.movement_sound_file == "/audio/wall.wav"
    assert sea.ambient_sound is not None
    assert sea.ambient_sound.sound_file == "/audio/ocean.wav"
    assert sea.ambient_sound.max_distance_tiles == 40
    assert sea.ambient_sound.channel == "ambience"


def test_loads_from_a_json_file(tmp_path: Path) -> None:
    path = tmp_path / "terrain.json"
    path.write_text(json.dumps({"sand": {"movement_sound": "sand.wav"}}))

    assert load_terrain_profiles(path)["sand"].movement_sound_file == (
        "sand.wav"
    )


def test_file_must_hold_an_object(tmp_path: Path) -> None:
    path = tmp_path / "terrain.json"
    path.write_text("[]")

    with pytest.raises(TerrainProfileError, match="expected an object"):
        load_terrain_profiles(path)


@pytest.mark.parametrize(
    "data, message",
    [
        ({"a": 3}, "must be an object"),
        ({"a": {"loud": True}}, "unknown options"),
        ({"a": {"ambient": {"max_distance_tiles": 3}}}, "needs a 'sound'"),
        ({"a": {"ambient": "x"}}, "needs a 'sound'"),
        ({"a": {"ambient": {"sound": "s", "echo": 1}}}, "unknown options"),
    ],
)
def test_malformed_entries_are_rejected(
    data: dict[str, object], message: str
) -> None:
    with pytest.raises(TerrainProfileError, match=message):
        terrain_profiles_from_dict(data)


def test_tile_factory_takes_passability_from_profiles() -> None:
    profiles = terrain_profiles_from_dict(
        {"sand": {}, "rock": {"passable": False}}
    )
    make = terrain_tile_factory(profiles)

    assert make("sand").is_passable
    assert not make("rock").is_passable
    assert make("rock").name == "rock"
