from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional, Union

from sonartk.map_builder.map_2d.map_2d import Map2d
from sonartk.map_builder.map_2d.map_object import MapObject
from sonartk.map_builder.map_2d.map_object.character import Character
from sonartk.map_builder.map_2d.map_tile import MapTile
from sonartk.util import Coordinates, Direction

MAP_DOCUMENT_VERSION = 1


class MapDocumentError(ValueError):
    """Raised when a map document is malformed or inconsistent."""


@dataclass(frozen=True)
class DocumentObject:
    """An object placed on a map.

    Attributes:
        name: Unique name of the object within the map.
        coordinates: Tile the object stands on.
        sound: Optional game-defined sound id. The library never interprets
            it; the game maps ids to its own sound catalog.
        max_distance_tiles: Range of the sound, when one is set.
        properties: Free-form JSON-compatible data for the game.
        type: Optional object type name. The library never interprets it;
            ``MapDefinition`` looks it up among the game's object types.
    """

    name: str
    coordinates: Coordinates
    sound: Optional[str] = None
    max_distance_tiles: Optional[int] = None
    properties: dict[str, Any] = field(default_factory=dict)
    type: Optional[str] = None


@dataclass(frozen=True)
class DocumentExit:
    """A tile that leads to another map."""

    coordinates: Coordinates
    target_map: str
    target_coordinates: Coordinates
    sound: Optional[str] = None


RISE_DIRECTIONS = ("north", "south", "east", "west")


@dataclass(frozen=True)
class ElevationArea:
    """A rectangle of tiles above or below the map's base level of 0.

    Without ``rises_toward`` every tile in the area is at height ``z``. With
    it the area is a ramp: the edge farthest from that direction is at
    ``z`` and each tile closer to it is one higher. A flat landing at the top
    of a ramp is therefore the ramp's last height, so a 4 tile ramp from
    ground level uses ``z=1`` and is followed by a landing at ``z=4``.

    Attributes:
        area: ``(x0, y0, x1, y1)``, both corners included.
        z: Height of the flat area, or of the ramp's lowest tiles.
        rises_toward: ``north``, ``south``, ``east`` or ``west`` for a ramp.
    """

    area: tuple[int, int, int, int]
    z: int
    rises_toward: Optional[str] = None

    def height_at(self, coordinates: Coordinates) -> Optional[int]:
        """Return the height at ``coordinates``, or None outside the area."""
        x0, y0, x1, y1 = self.area
        x, y = coordinates
        if not (x0 <= x <= x1 and y0 <= y <= y1):
            return None
        if self.rises_toward == "north":
            return self.z + (y - y0)
        if self.rises_toward == "south":
            return self.z + (y1 - y)
        if self.rises_toward == "east":
            return self.z + (x - x0)
        if self.rises_toward == "west":
            return self.z + (x1 - x)
        return self.z

    def tiles(self) -> dict[Coordinates, int]:
        """Return the height of every tile in the area."""
        x0, y0, x1, y1 = self.area
        result: dict[Coordinates, int] = {}
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                height = self.height_at((x, y))
                assert height is not None
                result[(x, y)] = height
        return result


@dataclass(frozen=True)
class MapDocument:
    """A complete, serializable description of one map.

    Terrain is stored as ``rows`` of single-character codes, north row
    first, so the file reads like the map drawn on paper. ``legend`` maps
    each code to a terrain name. All coordinates are ``(x, y)`` as used by
    ``Map2d``: ``x`` grows eastward and ``y`` grows northward, so ``(0, 0)``
    is the south-west corner and the last character of the last row.

    Sounds, music and ambience are plain names; the game decides what they
    mean. Construction validates the document, so an existing instance is
    always consistent.

    Attributes:
        key: Identifier other maps use to refer to this one.
        legend: Terrain code to terrain name.
        rows: Terrain codes, north row first, all the same width.
        start: Default player position.
        objects: Objects on the map.
        exits: Tiles leading to other maps.
        music: Optional music name.
        ambience: Optional ambience name.
        properties: Free-form JSON-compatible data for the game.
        version: Schema version.
        name: Optional name shown or spoken to the player.
        elevations: Areas above or below the base level of 0. Where areas
            overlap the later one wins.
    """

    key: str
    legend: Mapping[str, str]
    rows: tuple[str, ...]
    start: Coordinates
    objects: tuple[DocumentObject, ...] = ()
    exits: tuple[DocumentExit, ...] = ()
    music: Optional[str] = None
    ambience: Optional[str] = None
    properties: dict[str, Any] = field(default_factory=dict)
    version: int = MAP_DOCUMENT_VERSION
    name: Optional[str] = None
    elevations: tuple[ElevationArea, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "rows", tuple(self.rows))
        object.__setattr__(self, "objects", tuple(self.objects))
        object.__setattr__(self, "exits", tuple(self.exits))
        object.__setattr__(self, "elevations", tuple(self.elevations))
        object.__setattr__(self, "legend", dict(self.legend))
        self._validate()

    @property
    def width(self) -> int:
        """Number of tiles from west to east."""
        return len(self.rows[0])

    @property
    def height(self) -> int:
        """Number of tiles from south to north."""
        return len(self.rows)

    def contains(self, coordinates: Coordinates) -> bool:
        """Return whether ``coordinates`` lie inside the map."""
        x, y = coordinates
        return 0 <= x < self.width and 0 <= y < self.height

    def code_at(self, coordinates: Coordinates) -> str:
        """Return the terrain code at ``coordinates``."""
        if not self.contains(coordinates):
            raise IndexError(f"{coordinates} is outside the map.")
        x, y = coordinates
        return self.rows[self.height - 1 - y][x]

    def terrain_at(self, coordinates: Coordinates) -> str:
        """Return the terrain name at ``coordinates``."""
        return self.legend[self.code_at(coordinates)]

    def elevation_at(self, coordinates: Coordinates) -> int:
        """Return the height at ``coordinates``; 0 outside every area."""
        for area in reversed(self.elevations):
            height = area.height_at(coordinates)
            if height is not None:
                return height
        return 0

    def elevation_map(self) -> dict[Coordinates, int]:
        """Return the height of every tile that is not at level 0."""
        heights: dict[Coordinates, int] = {}
        for area in self.elevations:
            heights.update(area.tiles())
        return {tile: z for tile, z in heights.items() if z != 0}

    def require_terrain(self, known: Iterable[str]) -> None:
        """Check that every legend terrain is one the game knows.

        Raises:
            MapDocumentError: Naming the terrain missing from ``known``.
        """
        unknown = sorted(set(self.legend.values()) - set(known))
        if unknown:
            raise MapDocumentError(
                f"Map {self.key!r} uses unknown terrain: " + ", ".join(unknown)
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible dictionary."""
        data: dict[str, Any] = {
            "version": self.version,
            "key": self.key,
            "legend": dict(self.legend),
            "rows": list(self.rows),
            "start": list(self.start),
            "objects": [_object_to_dict(item) for item in self.objects],
            "exits": [
                {
                    "at": list(item.coordinates),
                    "target_map": item.target_map,
                    "target_at": list(item.target_coordinates),
                    **({"sound": item.sound} if item.sound else {}),
                }
                for item in self.exits
            ],
            "music": self.music,
            "ambience": self.ambience,
            "properties": dict(self.properties),
        }
        if self.name is not None:
            data["name"] = self.name
        if self.elevations:
            data["elevations"] = [
                _elevation_to_dict(item) for item in self.elevations
            ]
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MapDocument":
        """Create a document from ``to_dict`` style data.

        Raises:
            MapDocumentError: If a field is missing, has the wrong shape, or
                the document is inconsistent.
        """
        if not isinstance(data, Mapping):
            raise MapDocumentError("A map document must be a JSON object.")
        version = data.get("version", MAP_DOCUMENT_VERSION)
        if version != MAP_DOCUMENT_VERSION:
            raise MapDocumentError(
                f"Unsupported map document version {version!r}; expected "
                f"{MAP_DOCUMENT_VERSION}."
            )
        try:
            return cls(
                key=_required(data, "key"),
                legend=_required(data, "legend"),
                rows=tuple(_required(data, "rows")),
                start=_coordinates(_required(data, "start"), "start"),
                objects=tuple(
                    _object_from_dict(item) for item in data.get("objects", [])
                ),
                exits=tuple(
                    _exit_from_dict(item) for item in data.get("exits", [])
                ),
                music=data.get("music"),
                ambience=data.get("ambience"),
                properties=dict(data.get("properties", {})),
                version=version,
                name=data.get("name"),
                elevations=tuple(
                    _elevation_from_dict(item)
                    for item in data.get("elevations", [])
                ),
            )
        except (TypeError, AttributeError) as error:
            raise MapDocumentError(
                f"Malformed map document: {error}"
            ) from error

    def _validate(self) -> None:
        if not isinstance(self.key, str) or not self.key:
            raise MapDocumentError("The map key must be a non-empty string.")
        if self.name is not None and not isinstance(self.name, str):
            raise MapDocumentError("The map name must be text.")
        if self.version != MAP_DOCUMENT_VERSION:
            raise MapDocumentError(
                f"Unsupported map document version {self.version!r}."
            )
        for code, terrain in self.legend.items():
            if not isinstance(code, str) or len(code) != 1:
                raise MapDocumentError(
                    f"Legend codes must be single characters, got {code!r}."
                )
            if not isinstance(terrain, str) or not terrain:
                raise MapDocumentError(
                    f"Legend code {code!r} needs a terrain name."
                )
        if not self.rows or not all(
            isinstance(row, str) and row for row in self.rows
        ):
            raise MapDocumentError("rows must be a list of non-empty strings.")
        width = len(self.rows[0])
        for index, row in enumerate(self.rows):
            if len(row) != width:
                raise MapDocumentError(
                    f"Row {index} has width {len(row)}; expected {width}."
                )
            unknown = sorted(set(row) - set(self.legend))
            if unknown:
                raise MapDocumentError(
                    f"Row {index} uses codes missing from the legend: "
                    + ", ".join(repr(code) for code in unknown)
                )
        self._require_inside(self.start, "start")
        names: set[str] = set()
        for item in self.objects:
            if item.name in names:
                raise MapDocumentError(f"Duplicate object name {item.name!r}.")
            names.add(item.name)
            self._require_inside(item.coordinates, f"object {item.name!r}")
            if item.max_distance_tiles is not None and (
                item.max_distance_tiles < 0
            ):
                raise MapDocumentError(
                    f"Object {item.name!r} needs max_distance_tiles >= 0."
                )
        exit_tiles: set[Coordinates] = set()
        for map_exit in self.exits:
            if map_exit.coordinates in exit_tiles:
                raise MapDocumentError(
                    f"Duplicate exit at {map_exit.coordinates}."
                )
            exit_tiles.add(map_exit.coordinates)
            self._require_inside(map_exit.coordinates, "exit")
        for area in self.elevations:
            self._validate_elevation(area)

    def _validate_elevation(self, item: ElevationArea) -> None:
        x0, y0, x1, y1 = item.area
        if x0 > x1 or y0 > y1:
            raise MapDocumentError(
                f"Elevation area {item.area} must run from its south-west "
                "corner to its north-east corner."
            )
        self._require_inside((x0, y0), "elevation area")
        self._require_inside((x1, y1), "elevation area")
        if not isinstance(item.z, int) or isinstance(item.z, bool):
            raise MapDocumentError(
                f"Elevation height must be a whole number, got {item.z!r}."
            )
        if item.rises_toward is not None and (
            item.rises_toward not in RISE_DIRECTIONS
        ):
            raise MapDocumentError(
                f"rises_toward must be one of {', '.join(RISE_DIRECTIONS)}; "
                f"got {item.rises_toward!r}."
            )

    def _require_inside(self, coordinates: Coordinates, label: str) -> None:
        if not self.contains(coordinates):
            raise MapDocumentError(
                f"The {label} position {coordinates} is outside the "
                f"{self.width}x{self.height} map."
            )


def load_map_document(path: Union[str, Path]) -> MapDocument:
    """Read and validate a map document from a JSON file."""
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        raise MapDocumentError(f"{path} is not valid JSON: {error}") from error
    return MapDocument.from_dict(data)


def save_map_document(
    document: MapDocument, path: Union[str, Path], *, indent: int = 2
) -> None:
    """Write a document as JSON, one terrain row per line."""
    text = json.dumps(document.to_dict(), indent=indent, ensure_ascii=False)
    with open(path, "w", encoding="utf-8", newline="\n") as file:
        file.write(text + "\n")


def build_map2d_from_document(
    document: MapDocument,
    tile_factory: Callable[[str], MapTile],
    *,
    spawn: Optional[Coordinates] = None,
    character_name: str = "player",
    orientation: Direction = Direction.DOWN,
) -> Map2d:
    """Build a ``Map2d`` from a document.

    ``tile_factory`` is called once per terrain name used by the map and
    its tile is shared by every cell of that terrain. Objects are
    registered on the map. The character starts at ``spawn`` or the
    document's start.

    Raises:
        MapDocumentError: If the spawn is outside the map or not passable.
    """
    tiles: dict[str, MapTile] = {}
    for code in sorted({char for row in document.rows for char in row}):
        terrain = document.legend[code]
        if terrain not in tiles:
            tiles[terrain] = tile_factory(terrain)

    start = spawn if spawn is not None else document.start
    if not document.contains(start):
        raise MapDocumentError(f"The start {start} is outside the map.")
    if not tiles[document.terrain_at(start)].is_passable:
        raise MapDocumentError(f"The start {start} is not passable.")

    map2d = Map2d(document.key, Character(character_name, start, orientation))
    for row in document.rows:
        map2d.add_row([tiles[document.legend[code]] for code in row])
    for item in document.objects:
        map2d.register_map_object(MapObject(item.name, item.coordinates))
    map2d.set_elevations(document.elevation_map())
    return map2d


def _required(data: Mapping[str, Any], key: str) -> Any:
    if key not in data:
        raise MapDocumentError(f"Missing required field {key!r}.")
    return data[key]


def _coordinates(value: Any, label: str) -> Coordinates:
    if (
        not isinstance(value, (list, tuple))
        or len(value) != 2
        or not all(
            isinstance(part, int) and not isinstance(part, bool)
            for part in value
        )
    ):
        raise MapDocumentError(
            f"{label} must be two integers [x, y], got {value!r}."
        )
    return (value[0], value[1])


def _object_to_dict(item: DocumentObject) -> dict[str, Any]:
    data: dict[str, Any] = {"name": item.name, "at": list(item.coordinates)}
    if item.type is not None:
        data["type"] = item.type
    if item.sound is not None:
        data["sound"] = item.sound
    if item.max_distance_tiles is not None:
        data["max_distance_tiles"] = item.max_distance_tiles
    if item.properties:
        data["properties"] = dict(item.properties)
    return data


def _object_from_dict(data: Mapping[str, Any]) -> DocumentObject:
    return DocumentObject(
        name=_required(data, "name"),
        coordinates=_coordinates(_required(data, "at"), "object position"),
        sound=data.get("sound"),
        max_distance_tiles=data.get("max_distance_tiles"),
        properties=dict(data.get("properties", {})),
        type=data.get("type"),
    )


def _elevation_to_dict(item: ElevationArea) -> dict[str, Any]:
    data: dict[str, Any] = {"area": list(item.area), "z": item.z}
    if item.rises_toward is not None:
        data["rises_toward"] = item.rises_toward
    return data


def _elevation_from_dict(data: Mapping[str, Any]) -> ElevationArea:
    area = _required(data, "area")
    if (
        not isinstance(area, (list, tuple))
        or len(area) != 4
        or not all(
            isinstance(part, int) and not isinstance(part, bool)
            for part in area
        )
    ):
        raise MapDocumentError(
            f"An elevation area must be four integers [x0, y0, x1, y1], "
            f"got {area!r}."
        )
    return ElevationArea(
        area=(area[0], area[1], area[2], area[3]),
        z=_required(data, "z"),
        rises_toward=data.get("rises_toward"),
    )


def _exit_from_dict(data: Mapping[str, Any]) -> DocumentExit:
    return DocumentExit(
        coordinates=_coordinates(_required(data, "at"), "exit position"),
        target_map=_required(data, "target_map"),
        target_coordinates=_coordinates(
            _required(data, "target_at"), "exit target"
        ),
        sound=data.get("sound"),
    )
