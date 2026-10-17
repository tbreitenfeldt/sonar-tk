from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Union

from sonartk.map_builder import MapTile
from sonartk.orchestration.map_sound_navigation import (
    AmbientTileSoundConfig,
    TerrainAudioProfile,
)

SoundResolver = Callable[[str], str]

_AMBIENT_OPTIONS = {
    "max_distance_tiles",
    "volume",
    "rolloff",
    "loop",
    "min_volume_at_max_distance",
    "distance_curve_exponent",
    "channel",
}


_TERRAIN_OPTIONS = {
    "passable",
    "movement_sound",
    "ambient",
    "climb_pitch",
    "descend_pitch",
}


class TerrainProfileError(ValueError):
    """A terrain profile file is malformed."""


def terrain_profiles_from_dict(
    data: Mapping[str, Any],
    resolve_sound: Optional[SoundResolver] = None,
) -> dict[str, TerrainAudioProfile]:
    """Build terrain profiles from plain data.

    Each key is a terrain name. Each value may hold ``passable`` (default
    true), ``movement_sound``, ``ambient``, and ``climb_pitch`` and
    ``descend_pitch`` (pitch multipliers, default 1, for the movement sound
    when stepping up or down onto the terrain). ``ambient`` holds ``sound``
    plus any option of ``AmbientTileSoundConfig`` (``max_distance_tiles``,
    ``volume``, ``rolloff``, ``loop``, ``min_volume_at_max_distance``,
    ``distance_curve_exponent``, ``channel``).

    Args:
        data: Terrain name to profile data.
        resolve_sound: Turns a sound name from the data into a file path,
            for example through an asset catalog. Without it names are used
            as paths.

    Raises:
        TerrainProfileError: An entry is malformed or an option is unknown.
    """
    resolve = resolve_sound or (lambda name: name)
    return {
        str(name): _profile(str(name), entry, resolve)
        for name, entry in data.items()
    }


def load_terrain_profiles(
    path: Union[str, Path],
    resolve_sound: Optional[SoundResolver] = None,
) -> dict[str, TerrainAudioProfile]:
    """Load terrain profiles from a JSON file.

    See ``terrain_profiles_from_dict`` for the format.
    """
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise TerrainProfileError(f"{path}: expected an object of terrains.")
    return terrain_profiles_from_dict(data, resolve_sound)


def terrain_tile_factory(
    profiles: Mapping[str, TerrainAudioProfile],
) -> Callable[[str], MapTile]:
    """Build a tile factory whose passability comes from the profiles."""

    def make(name: str) -> MapTile:
        return MapTile(name, is_passable=profiles[name].is_passable)

    return make


def _profile(
    name: str, entry: Any, resolve: SoundResolver
) -> TerrainAudioProfile:
    if not isinstance(entry, dict):
        raise TerrainProfileError(f"Terrain {name!r} must be an object.")
    unknown = set(entry) - _TERRAIN_OPTIONS
    if unknown:
        raise TerrainProfileError(
            f"Terrain {name!r} has unknown options {sorted(unknown)}."
        )
    movement = entry.get("movement_sound")
    ambient = entry.get("ambient")
    return TerrainAudioProfile(
        is_passable=bool(entry.get("passable", True)),
        movement_sound_file=None if movement is None else resolve(movement),
        ambient_sound=(
            None if ambient is None else _ambient(name, ambient, resolve)
        ),
        climb_pitch=_pitch(name, entry, "climb_pitch"),
        descend_pitch=_pitch(name, entry, "descend_pitch"),
    )


def _pitch(name: str, entry: dict[str, Any], option: str) -> float:
    value = entry.get(option, 1.0)
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or value <= 0
    ):
        raise TerrainProfileError(
            f"Terrain {name!r} {option} must be a number above 0."
        )
    return float(value)


def _ambient(
    name: str, entry: Any, resolve: SoundResolver
) -> AmbientTileSoundConfig:
    if not isinstance(entry, dict) or "sound" not in entry:
        raise TerrainProfileError(f"Terrain {name!r} ambient needs a 'sound'.")
    options = {key: value for key, value in entry.items() if key != "sound"}
    unknown = set(options) - _AMBIENT_OPTIONS
    if unknown:
        raise TerrainProfileError(
            f"Terrain {name!r} ambient has unknown options {sorted(unknown)}."
        )
    return AmbientTileSoundConfig(
        sound_file=resolve(entry["sound"]), **options
    )
