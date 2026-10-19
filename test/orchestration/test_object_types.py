from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from sonartk.orchestration.object_types import (
    ObjectTypeError,
    load_object_types,
    object_tile_name,
    object_types_from_dict,
)
from sonartk.util import Direction


def test_defaults_describe_a_single_blocking_tile() -> None:
    kinds = object_types_from_dict({"rock": {}})

    rock = kinds["rock"]
    assert rock.name == "rock"
    assert rock.footprint == ((0, 0),)
    assert rock.passable is False
    assert rock.collision_sound is None
    assert rock.side_sounds == {}
    assert rock.loop_sound is None
    assert rock.description == ()
    assert rock.movable is False
    assert rock.category is None


def test_every_option_is_read_and_sounds_are_resolved() -> None:
    kinds = object_types_from_dict(
        {
            "log": {
                "footprint": [[0, 0], [1, 0], [1, 1]],
                "passable": True,
                "collision_sound": "thud",
                "side_sounds": {"north": "n", "west": "w"},
                "loop": {
                    "sound": "creak",
                    "max_distance_tiles": 7,
                    "volume": 0.5,
                },
                "description": "A log.",
                "movable": True,
                "category": "wreck",
            }
        },
        resolve_sound=lambda name: f"audio/{name}.wav",
    )

    log = kinds["log"]
    assert log.footprint == ((0, 0), (1, 0), (1, 1))
    assert log.passable is True
    assert log.collision_sound == "audio/thud.wav"
    assert log.side_sounds == {
        Direction.DOWN: "audio/n.wav",
        Direction.RIGHT: "audio/w.wav",
    }
    assert log.loop_sound == "audio/creak.wav"
    assert log.loop_max_distance_tiles == 7
    assert log.loop_volume == 0.5
    assert log.description == ("A log.",)
    assert log.movable is True
    assert log.category == "wreck"


@pytest.mark.parametrize(
    ("side", "move"),
    [
        ("north", Direction.DOWN),
        ("south", Direction.UP),
        ("east", Direction.LEFT),
        ("west", Direction.RIGHT),
    ],
)
def test_a_side_is_hit_by_moving_toward_it(side: str, move: Direction) -> None:
    kinds = object_types_from_dict({"a": {"side_sounds": {side: "x"}}})

    assert kinds["a"].side_sounds == {move: "x"}


@pytest.mark.parametrize(
    "entry",
    [
        "text",
        {"bogus": 1},
        {"footprint": []},
        {"footprint": "x"},
        {"footprint": [[0]]},
        {"footprint": [[0, "a"]]},
        {"footprint": [[0, 0], [0, 0]]},
        {"side_sounds": []},
        {"side_sounds": {"up": "x"}},
        {"loop": {"max_distance_tiles": 3}},
        {"loop": {"sound": "x"}},
        {"loop": {"sound": "x", "max_distance_tiles": 3, "pitch": 1}},
        {"category": 4},
        {"description": 4},
        {"description": [1]},
    ],
)
def test_malformed_entries_are_rejected(entry: Any) -> None:
    with pytest.raises(ObjectTypeError):
        object_types_from_dict({"bad": entry})


def test_load_object_types_reads_a_file(tmp_path: Path) -> None:
    path = tmp_path / "objects.json"
    path.write_text(json.dumps({"rock": {"collision_sound": "thud"}}))

    assert load_object_types(path)["rock"].collision_sound == "thud"


def test_load_object_types_rejects_a_non_object(tmp_path: Path) -> None:
    path = tmp_path / "objects.json"
    path.write_text("[]")

    with pytest.raises(ObjectTypeError):
        load_object_types(path)


def test_object_tile_name_is_prefixed() -> None:
    assert object_tile_name("boat") == "object:boat"
