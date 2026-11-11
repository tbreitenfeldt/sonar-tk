"""Reusable multi-tile map passages and their proximity beacons."""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite
from typing import Any, Callable, Iterable, Mapping

from sonartk.map_builder import DocumentExit, MapDocument, MapDocumentError
from sonartk.orchestration.map_definition import ObjectSound
from sonartk.orchestration.map_exits import MapExit
from sonartk.orchestration.proximity_audio import ProximityAudioEmitter
from sonartk.util import Coordinates

SoundResolver = Callable[[str, str], str]


@dataclass(frozen=True)
class MapPassage:
    """Exit tiles sharing a destination and one nearest-tile beacon.

    ``transition_sound`` is the document's sound name, not a resolved path.
    ``beacon`` contains the resolved path used for the looping sound.
    """

    tiles: tuple[Coordinates, ...]
    target_map: str
    target_at: Coordinates
    beacon: ObjectSound
    transition_sound: str | None = None

    def __post_init__(self) -> None:
        if not self.tiles:
            raise ValueError("A map passage must contain at least one tile.")

    def exits(self) -> tuple[DocumentExit, ...]:
        """Create a document exit for each passage tile."""
        return tuple(
            DocumentExit(
                tile, self.target_map, self.target_at, self.transition_sound
            )
            for tile in self.tiles
        )

    def emitter(self) -> ProximityAudioEmitter:
        """Create one loop positioned at the nearest tile in the passage."""
        return ProximityAudioEmitter(
            sound_path=self.beacon.sound_file,
            source_coordinates=self.tiles[0],
            max_distance_tiles=self.beacon.max_distance_tiles,
            base_volume=self.beacon.volume,
            footprint=self.tiles,
        )


def _coordinates(value: Any, label: str, length: int) -> tuple[int, ...]:
    if (
        not isinstance(value, (list, tuple))
        or len(value) != length
        or any(type(number) is not int for number in value)
    ):
        raise MapDocumentError(f"Passage {label} needs {length} integers.")
    return tuple(value)


def _sound(name: Any, label: str, resolve_sound: SoundResolver | None) -> str:
    if not isinstance(name, str) or not name:
        raise MapDocumentError(f"Passage {label} must be a sound name.")
    return name if resolve_sound is None else resolve_sound(name, label)


def parse_map_passages(
    document: MapDocument, *, resolve_sound: SoundResolver | None = None
) -> tuple[MapPassage, ...]:
    """Parse ``properties.passages``; optionally resolve sound names.

    ``resolve_sound`` receives the name and a descriptive label. The optional
    transition sound is resolved for validation, but kept as a name for
    conversion by ``MapDefinition.from_document``.
    """
    data = document.properties.get("passages", [])
    if not isinstance(data, list):
        raise MapDocumentError("Map passages must be a list.")
    passages = []
    for item in data:
        if not isinstance(item, dict):
            raise MapDocumentError("Each passage must be an object.")
        x0, y0, x1, y1 = _coordinates(item.get("area"), "area", 4)
        if x0 > x1 or y0 > y1:
            raise MapDocumentError("Passage area corners must be ordered.")
        if not document.contains((x0, y0)) or not document.contains((x1, y1)):
            raise MapDocumentError("Passage area must be inside the map.")
        target_map = item.get("target_map")
        if not isinstance(target_map, str) or not target_map:
            raise MapDocumentError(
                "Passage target_map must be non-empty text."
            )
        target_x, target_y = _coordinates(
            item.get("target_at"), "target_at", 2
        )
        beacon = item.get("beacon")
        if not isinstance(beacon, dict):
            raise MapDocumentError("Passage beacon must be an object.")
        sound = _sound(beacon.get("sound"), "beacon sound", resolve_sound)
        distance = beacon.get("range")
        if type(distance) is not int or distance <= 0:
            raise MapDocumentError(
                "Passage beacon range must be a positive integer."
            )
        volume = beacon.get("volume", 1.0)
        if (
            isinstance(volume, bool)
            or not isinstance(volume, (int, float))
            or not isfinite(volume)
            or not 0 <= volume <= 1
        ):
            raise MapDocumentError(
                "Passage beacon volume must be between 0 and 1."
            )
        transition = item.get("transition_sound")
        if transition is not None:
            _sound(transition, "transition sound", resolve_sound)
        passages.append(
            MapPassage(
                tiles=tuple(
                    (x, y)
                    for y in range(y0, y1 + 1)
                    for x in range(x0, x1 + 1)
                ),
                target_map=target_map,
                target_at=(target_x, target_y),
                beacon=ObjectSound(sound, distance, float(volume)),
                transition_sound=transition,
            )
        )
    return tuple(passages)


def expand_passages(
    document: MapDocument, passages: Iterable[MapPassage]
) -> MapDocument:
    """Add passage tiles as regular exits, rejecting conflicts and overlaps."""
    exits = list(document.exits)
    existing = {item.coordinates: item for item in exits}
    claimed: set[Coordinates] = set()
    for passage in passages:
        for item in passage.exits():
            if item.coordinates in claimed:
                raise MapDocumentError(
                    f"Overlapping passages at {item.coordinates}."
                )
            claimed.add(item.coordinates)
            prior = existing.get(item.coordinates)
            if prior is not None and prior != item:
                raise MapDocumentError(
                    f"Passage conflicts with exit at {item.coordinates}."
                )
            if prior is None:
                exits.append(item)
                existing[item.coordinates] = item
    return replace(document, exits=tuple(exits))


def passage_exit_emitters(
    exits: Iterable[MapExit],
    passages: Iterable[MapPassage],
    emitters: Mapping[str, ProximityAudioEmitter],
) -> dict[str, ProximityAudioEmitter]:
    """Replace per-exit emitters with one footprint emitter per passage.

    ``emitters`` uses the ``exit:<index>`` keys of MapScreenController.
    Exits outside passages and other entries are left unchanged.
    """
    result = dict(emitters)
    indices: dict[Coordinates, tuple[int, MapExit]] = {}
    for index, item in enumerate(exits):
        if item.coordinates in indices:
            raise ValueError(f"Duplicate exit at {item.coordinates}.")
        indices[item.coordinates] = (index, item)
    claimed: set[Coordinates] = set()
    for passage in passages:
        for tile in passage.tiles:
            if tile not in indices:
                raise ValueError(
                    f"No exit registered for passage tile {tile}."
                )
            if tile in claimed:
                raise ValueError(f"Overlapping passages at {tile}.")
            index, item = indices[tile]
            if (
                item.target_map != passage.target_map
                or item.target_coordinates != passage.target_at
            ):
                raise ValueError(f"Exit conflicts with passage at {tile}.")
            claimed.add(tile)
            result.pop(f"exit:{index}", None)
        first_index, _ = indices[passage.tiles[0]]
        result[f"exit:{first_index}"] = passage.emitter()
    return result
