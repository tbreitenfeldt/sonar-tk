from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Union

from sonartk.util import Coordinates, Direction

SoundResolver = Callable[[str], str]

OBJECT_TILE_PREFIX = "object:"

# Moving in a direction hits the opposite side of the object.
_SIDE_TO_MOVE: dict[str, Direction] = {
    "north": Direction.DOWN,
    "south": Direction.UP,
    "east": Direction.LEFT,
    "west": Direction.RIGHT,
}
_TYPE_OPTIONS = {
    "footprint",
    "passable",
    "collision_sound",
    "side_sounds",
    "loop",
    "description",
    "movable",
}
_LOOP_OPTIONS = {"sound", "max_distance_tiles", "volume"}


class ObjectTypeError(ValueError):
    """An object type definition is malformed."""


def object_tile_name(object_name: str) -> str:
    """Return the tile name stamped on every tile an object blocks."""
    return f"{OBJECT_TILE_PREFIX}{object_name}"


@dataclass(frozen=True)
class ObjectType:
    """What every object of one kind has in common.

    Attributes:
        name: The type's name.
        footprint: Tile offsets from the object's position that it covers.
            Any shape is possible, such as an L.
        passable: Whether the player can walk over the footprint. Blocking
            objects stamp their footprint onto the map as impassable tiles.
        collision_sound: Sound played when the player bumps into the object.
            Without one the shared blocked sound plays.
        side_sounds: Collision sounds by the direction the player was moving
            when they hit the object, replacing ``collision_sound``.
        loop_sound: Looping sound the object gives off. It plays as one
            source, from the nearest footprint tile, so it sounds the same
            from any side.
        loop_max_distance_tiles: Range of the loop sound.
        loop_volume: Volume of the loop sound.
        description: Pages spoken when the player examines the object.
        movable: Whether the object may be moved. Stored for games to use.
    """

    name: str
    footprint: tuple[Coordinates, ...] = ((0, 0),)
    passable: bool = False
    collision_sound: Optional[str] = None
    side_sounds: Mapping[Direction, str] = field(default_factory=dict)
    loop_sound: Optional[str] = None
    loop_max_distance_tiles: int = 0
    loop_volume: float = 1.0
    description: tuple[str, ...] = ()
    movable: bool = False


def object_types_from_dict(
    data: Mapping[str, Any],
    resolve_sound: Optional[SoundResolver] = None,
) -> dict[str, ObjectType]:
    """Build object types from plain data.

    Each key is a type name. Each value may hold ``footprint`` (a list of
    ``[dx, dy]`` offsets, default one tile), ``passable`` (default false),
    ``collision_sound``, ``side_sounds`` (sound names by ``north``,
    ``south``, ``east`` or ``west``, the side of the object that was hit),
    ``loop`` (``sound``, ``max_distance_tiles`` and ``volume``),
    ``description`` (text or a list of pages) and ``movable``.

    Args:
        data: Type name to type data.
        resolve_sound: Turns a sound name into a file path. Without it
            names are used as paths.

    Raises:
        ObjectTypeError: An entry is malformed or an option is unknown.
    """
    resolve = resolve_sound or (lambda name: name)
    return {
        str(name): _object_type(str(name), entry, resolve)
        for name, entry in data.items()
    }


def load_object_types(
    path: Union[str, Path],
    resolve_sound: Optional[SoundResolver] = None,
) -> dict[str, ObjectType]:
    """Load object types from a JSON file.

    See ``object_types_from_dict`` for the format.
    """
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ObjectTypeError(f"{path}: expected an object of types.")
    return object_types_from_dict(data, resolve_sound)


def _object_type(name: str, entry: Any, resolve: SoundResolver) -> ObjectType:
    if not isinstance(entry, dict):
        raise ObjectTypeError(f"Object type {name!r} must be an object.")
    unknown = set(entry) - _TYPE_OPTIONS
    if unknown:
        raise ObjectTypeError(
            f"Object type {name!r} has unknown options {sorted(unknown)}."
        )
    collision = entry.get("collision_sound")
    loop = entry.get("loop")
    loop_sound: Optional[str] = None
    loop_range = 0
    loop_volume = 1.0
    if loop is not None:
        loop_sound, loop_range, loop_volume = _loop(name, loop, resolve)
    return ObjectType(
        name=name,
        footprint=_footprint(name, entry.get("footprint", [[0, 0]])),
        passable=bool(entry.get("passable", False)),
        collision_sound=None if collision is None else resolve(collision),
        side_sounds=_side_sounds(name, entry.get("side_sounds", {}), resolve),
        loop_sound=loop_sound,
        loop_max_distance_tiles=loop_range,
        loop_volume=loop_volume,
        description=_pages(name, entry.get("description", [])),
        movable=bool(entry.get("movable", False)),
    )


def _footprint(name: str, value: Any) -> tuple[Coordinates, ...]:
    if not isinstance(value, list) or not value:
        raise ObjectTypeError(
            f"Object type {name!r} footprint must be a list of [dx, dy]."
        )
    offsets: list[Coordinates] = []
    for item in value:
        if (
            not isinstance(item, (list, tuple))
            or len(item) != 2
            or not all(
                isinstance(part, int) and not isinstance(part, bool)
                for part in item
            )
        ):
            raise ObjectTypeError(
                f"Object type {name!r} footprint entry {item!r} must be "
                "two integers."
            )
        offsets.append((item[0], item[1]))
    if len(set(offsets)) != len(offsets):
        raise ObjectTypeError(
            f"Object type {name!r} footprint repeats a tile."
        )
    return tuple(offsets)


def _side_sounds(
    name: str, value: Any, resolve: SoundResolver
) -> dict[Direction, str]:
    if not isinstance(value, dict):
        raise ObjectTypeError(
            f"Object type {name!r} side_sounds must be an object."
        )
    unknown = set(value) - set(_SIDE_TO_MOVE)
    if unknown:
        raise ObjectTypeError(
            f"Object type {name!r} has unknown sides {sorted(unknown)}."
        )
    return {
        _SIDE_TO_MOVE[side]: resolve(sound) for side, sound in value.items()
    }


def _loop(
    name: str, value: Any, resolve: SoundResolver
) -> tuple[str, int, float]:
    if not isinstance(value, dict) or "sound" not in value:
        raise ObjectTypeError(f"Object type {name!r} loop needs a 'sound'.")
    unknown = set(value) - _LOOP_OPTIONS
    if unknown:
        raise ObjectTypeError(
            f"Object type {name!r} loop has unknown options "
            f"{sorted(unknown)}."
        )
    if "max_distance_tiles" not in value:
        raise ObjectTypeError(
            f"Object type {name!r} loop needs 'max_distance_tiles'."
        )
    return (
        resolve(value["sound"]),
        int(value["max_distance_tiles"]),
        float(value.get("volume", 1.0)),
    )


def _pages(name: str, value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if not isinstance(value, list) or not all(
        isinstance(page, str) for page in value
    ):
        raise ObjectTypeError(
            f"Object type {name!r} description must be text or a list of "
            "text."
        )
    return tuple(value)
