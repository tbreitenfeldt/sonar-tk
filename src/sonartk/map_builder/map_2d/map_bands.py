from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sonartk.map_builder.map_2d.map_2d import Map2d
from sonartk.map_builder.map_2d.map_object.character import Character
from sonartk.map_builder.map_2d.map_tile import MapTile


@dataclass(frozen=True)
class MapBand:
    """A horizontal strip of identical tiles spanning the full map width.

    Attributes:
        tile: Tile used for every cell in the band.
        rows: Number of map rows (north-south thickness) in the band.
    """

    tile: MapTile
    rows: int


def build_banded_map(
    name: str,
    *,
    width: int,
    bands: Sequence[MapBand],
    character: Character,
) -> Map2d:
    """Build a map from horizontal bands listed from north to south.

    Useful for coastlines, rivers, and other terrain that changes by
    distance along the north-south axis. The first band ends up at the
    highest ``y`` values (north, since ``Direction.UP`` increases ``y``).
    Every cell in a band shares the same ``MapTile`` instance.

    Args:
        name: Map name.
        width: Number of tiles from west to east.
        bands: Bands ordered from north to south.
        character: Character registered on the map.

    Raises:
        ValueError: If width is not positive, no bands are given, or a band
            has a non-positive row count.
    """
    if width <= 0:
        raise ValueError(f"width must be greater than 0, got {width}.")
    if not bands:
        raise ValueError("At least one band is required.")

    map2d = Map2d(name, character)
    for band in bands:
        if band.rows <= 0:
            raise ValueError(
                f"Band rows must be greater than 0, got {band.rows}."
            )
        for _ in range(band.rows):
            map2d.add_row([band.tile] * width)

    return map2d
