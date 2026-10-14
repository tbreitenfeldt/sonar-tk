from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Hashable, Iterable, Optional, Union

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
from sonartk.util import Coordinates

Resolver = Callable[[str], Any]


@dataclass(frozen=True)
class ObjectSound:
    """A looping sound that gets quieter with distance and ends at range."""

    sound_file: str
    max_distance_tiles: int
    volume: float = 1.0


@dataclass(frozen=True)
class MapObjectSpec:
    """An object placed on a map, optionally giving off a looping sound."""

    name: str
    coordinates: Coordinates
    sound: Optional[ObjectSound] = None
    description: tuple[str, ...] = ()


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

        Raises:
            MapDocumentError: A legend entry is not in ``known_terrain``.
            ValueError: An object's description or sound is malformed.
        """
        if known_terrain is not None:
            document.require_terrain(known_terrain)
        return cls(
            key=document.key,
            document=document,
            start=document.start,
            objects=tuple(
                _object_spec(item, resolve_sound) for item in document.objects
            ),
            exits=tuple(
                MapExit(
                    item.coordinates,
                    item.target_map,
                    item.target_coordinates,
                )
                for item in document.exits
            ),
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


def _description(item: DocumentObject) -> tuple[str, ...]:
    """Read the pages spoken when the player examines the object."""
    pages = item.properties.get("description", ())
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
    item: DocumentObject, resolve_sound: Optional[Resolver]
) -> MapObjectSpec:
    description = _description(item)
    if item.sound is None:
        return MapObjectSpec(item.name, item.coordinates, None, description)
    if item.max_distance_tiles is None:
        raise ValueError(
            f"Object {item.name!r} has a sound but no max_distance_tiles."
        )
    sound_file = _resolve(resolve_sound, item.sound)
    return MapObjectSpec(
        item.name,
        item.coordinates,
        ObjectSound(sound_file, item.max_distance_tiles),
        description,
    )
