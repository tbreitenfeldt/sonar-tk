from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Any,
    Callable,
    Hashable,
    Iterable,
    Mapping,
    Optional,
    Union,
)

from sonartk.map_builder import (
    DocumentObject,
    Map2d,
    MapDocument,
    MapTile,
    build_map2d_from_document,
    load_map_document,
)
from sonartk.map_builder.map_2d.map_object import MapObject
from sonartk.orchestration.map_exits import MapExit, MapExitRegistry
from sonartk.orchestration.object_types import ObjectType, object_tile_name
from sonartk.util import Coordinates, Direction

Resolver = Callable[[str], Any]


@dataclass(frozen=True)
class ObjectSound:
    """A looping sound that gets quieter with distance and ends at range."""

    sound_file: str
    max_distance_tiles: int
    volume: float = 1.0


@dataclass(frozen=True)
class MapObjectSpec:
    """An object placed on a map, optionally giving off a looping sound.

    ``footprint`` holds every tile the object covers, in map coordinates.
    A ``blocking`` object has that footprint stamped onto the map as
    impassable tiles when the map is loaded.
    """

    name: str
    coordinates: Coordinates
    sound: Optional[ObjectSound] = None
    description: tuple[str, ...] = ()
    footprint: tuple[Coordinates, ...] = ()
    blocking: bool = False
    collision_sound: Optional[str] = None
    side_sounds: Mapping[Direction, str] = field(default_factory=dict)
    movable: bool = False


@dataclass(frozen=True)
class MapDefinition:
    """Everything needed to build one map, kept free of runtime state.

    ``music`` and ``ambience`` hold whatever the resolvers given to
    ``from_document`` returned for the document's names, so a game can use
    its own enums for them.
    """

    key: Hashable
    document: MapDocument
    start: Coordinates
    objects: tuple[MapObjectSpec, ...] = ()
    exits: tuple[MapExit, ...] = ()
    music: Any = None
    ambience: Any = None
    name: Optional[str] = None

    @classmethod
    def from_document(
        cls,
        document: MapDocument,
        *,
        known_terrain: Optional[Iterable[str]] = None,
        resolve_sound: Optional[Resolver] = None,
        resolve_music: Optional[Resolver] = None,
        resolve_ambience: Optional[Resolver] = None,
        object_types: Optional[Mapping[str, ObjectType]] = None,
    ) -> MapDefinition:
        """Describe a map stored as a document.

        Args:
            document: The parsed map document.
            known_terrain: If given, every legend terrain must be in it.
            resolve_sound: Turns an object's sound name into a sound file
                path. Without it the name is used as the path.
            resolve_music: Turns the document's music name into a value to
                keep on the definition. Without it the name is kept.
            resolve_ambience: Like ``resolve_music``, for ambience.
            object_types: Types that objects with a ``type`` take their
                footprint, sounds and description from. Values given on
                the object itself take precedence.

        Raises:
            MapDocumentError: A legend entry is not in ``known_terrain``.
            ValueError: An object is malformed, has an unknown type, or its
                footprint leaves the map or overlaps something blocking.
        """
        if known_terrain is not None:
            document.require_terrain(known_terrain)
        specs = tuple(
            _object_spec(item, resolve_sound, object_types or {})
            for item in document.objects
        )
        exits = tuple(
            MapExit(
                item.coordinates,
                item.target_map,
                item.target_coordinates,
                (
                    None
                    if item.sound is None
                    else _resolve(resolve_sound, item.sound)
                ),
            )
            for item in document.exits
        )
        _check_footprints(document, specs, exits)
        return cls(
            key=document.key,
            document=document,
            start=document.start,
            objects=specs,
            exits=exits,
            name=document.name,
            music=_resolve(resolve_music, document.music),
            ambience=_resolve(resolve_ambience, document.ambience),
        )

    @classmethod
    def from_file(
        cls, path: Union[str, Path], **options: Any
    ) -> MapDefinition:
        """Load a map document file and describe it."""
        return cls.from_document(load_map_document(path), **options)


@dataclass
class LoadedMap:
    """A built map with its exits and objects, ready to be played."""

    definition: MapDefinition
    map2d: Map2d
    exits: MapExitRegistry
    objects: dict[str, MapObject]


def load_map(
    definition: MapDefinition,
    tile_factory: Callable[[str], MapTile],
    spawn: Optional[Coordinates] = None,
) -> LoadedMap:
    """Build a map, placing the player at spawn or the default start."""
    start = spawn if spawn is not None else definition.start
    map2d = build_map2d_from_document(
        definition.document, tile_factory, spawn=start
    )
    for spec in definition.objects:
        if not spec.blocking:
            continue
        if start in spec.footprint:
            raise ValueError(
                f"The start {start} is inside the object {spec.name!r}."
            )
        tile = MapTile(object_tile_name(spec.name), is_passable=False)
        for coordinates in spec.footprint:
            map2d.set_tile(coordinates, tile)
    objects = {
        spec.name: found
        for spec in definition.objects
        if (found := map2d.get_map_object_at(spec.coordinates)) is not None
    }
    exits = MapExitRegistry()
    for map_exit in definition.exits:
        exits.add(map_exit)
    return LoadedMap(definition, map2d, exits, objects)


def _resolve(resolver: Optional[Resolver], name: Optional[str]) -> Any:
    if name is None or resolver is None:
        return name
    return resolver(name)


def _description(
    item: DocumentObject, default: tuple[str, ...] = ()
) -> tuple[str, ...]:
    """Read the pages spoken when the player examines the object."""
    pages = item.properties.get("description", default)
    if isinstance(pages, str):
        pages = [pages]
    if not isinstance(pages, (list, tuple)) or not all(
        isinstance(page, str) for page in pages
    ):
        raise ValueError(
            f"Object {item.name!r} description must be text or a list of text."
        )
    return tuple(pages)


def _object_spec(
    item: DocumentObject,
    resolve_sound: Optional[Resolver],
    object_types: Mapping[str, ObjectType],
) -> MapObjectSpec:
    kind: Optional[ObjectType] = None
    if item.type is not None:
        kind = object_types.get(item.type)
        if kind is None:
            raise ValueError(
                f"Object {item.name!r} has unknown type {item.type!r}."
            )
    sound = _object_sound(item, resolve_sound, kind)
    x, y = item.coordinates
    footprint = (
        ((x, y),)
        if kind is None
        else tuple((x + dx, y + dy) for dx, dy in kind.footprint)
    )
    return MapObjectSpec(
        item.name,
        item.coordinates,
        sound,
        _description(item, () if kind is None else kind.description),
        footprint,
        blocking=kind is not None and not kind.passable,
        collision_sound=None if kind is None else kind.collision_sound,
        side_sounds={} if kind is None else dict(kind.side_sounds),
        movable=kind is not None and kind.movable,
    )


def _object_sound(
    item: DocumentObject,
    resolve_sound: Optional[Resolver],
    kind: Optional[ObjectType],
) -> Optional[ObjectSound]:
    type_range = None if kind is None else kind.loop_max_distance_tiles
    if item.sound is None:
        if kind is None or kind.loop_sound is None:
            return None
        return ObjectSound(
            kind.loop_sound,
            item.max_distance_tiles or kind.loop_max_distance_tiles,
            kind.loop_volume,
        )
    max_distance = (
        item.max_distance_tiles
        if item.max_distance_tiles is not None
        else type_range
    )
    if max_distance is None:
        raise ValueError(
            f"Object {item.name!r} has a sound but no max_distance_tiles."
        )
    return ObjectSound(_resolve(resolve_sound, item.sound), max_distance)


def _check_footprints(
    document: MapDocument,
    specs: tuple[MapObjectSpec, ...],
    exits: tuple[MapExit, ...],
) -> None:
    claimed: dict[Coordinates, str] = {}
    for spec in specs:
        for coordinates in spec.footprint:
            if not document.contains(coordinates):
                raise ValueError(
                    f"Object {spec.name!r} covers {coordinates}, outside "
                    "the map."
                )
        if not spec.blocking:
            continue
        for coordinates in spec.footprint:
            other = claimed.setdefault(coordinates, spec.name)
            if other != spec.name:
                raise ValueError(
                    f"Objects {other!r} and {spec.name!r} overlap at "
                    f"{coordinates}."
                )
            if any(coordinates == found.coordinates for found in exits):
                raise ValueError(
                    f"Object {spec.name!r} covers an exit at {coordinates}."
                )
