from __future__ import annotations

import random
from typing import Optional, Sequence

from sonartk.util import Coordinates


def jagged_edge(
    width: int,
    base: int,
    *,
    amplitude: int,
    seed: Optional[int] = None,
    max_step: int = 1,
) -> list[int]:
    """Return one wandering ``y`` value per column, for organic boundaries.

    The edge is a bounded random walk: each column moves by at most
    ``max_step`` from the previous one and never strays more than
    ``amplitude`` from ``base``. Pass a ``seed`` for a repeatable shape.

    Args:
        width: Number of columns.
        base: Centre line of the edge.
        amplitude: Largest allowed distance from ``base``.
        seed: Optional seed for repeatable output.
        max_step: Largest change between neighbouring columns.

    Raises:
        ValueError: If width or max_step is not positive, or amplitude is
            negative.
    """
    if width <= 0:
        raise ValueError(f"width must be greater than 0, got {width}.")
    if amplitude < 0:
        raise ValueError(f"amplitude must be >= 0, got {amplitude}.")
    if max_step <= 0:
        raise ValueError(f"max_step must be greater than 0, got {max_step}.")

    rng = random.Random(seed)
    offset = 0
    edge: list[int] = []
    for _ in range(width):
        offset += rng.randint(-max_step, max_step)
        offset = max(-amplitude, min(amplitude, offset))
        edge.append(base + offset)
    return edge


class MapCanvas:
    """A grid of single-character terrain codes for drawing maps in code.

    Coordinates match ``Map2d``: ``x`` grows eastward and ``y`` grows
    northward, so ``(0, 0)`` is the south-west corner. ``to_rows`` returns
    the rows with north first, which is the layout used by map documents.
    """

    def __init__(self, width: int, height: int, fill: str) -> None:
        if width <= 0 or height <= 0:
            raise ValueError(
                f"width and height must be greater than 0, got "
                f"{width}x{height}."
            )
        self._check_code(fill)
        self.width = width
        self.height = height
        self._cells: list[list[str]] = [[fill] * width for _ in range(height)]

    @classmethod
    def from_rows(cls, rows: Sequence[str]) -> "MapCanvas":
        """Create a canvas from rows written north first."""
        if not rows or not rows[0]:
            raise ValueError("At least one non-empty row is required.")
        width = len(rows[0])
        if any(len(row) != width for row in rows):
            raise ValueError("All rows must have the same width.")
        canvas = cls(width, len(rows), rows[0][0])
        for row_index, row in enumerate(rows):
            canvas._cells[len(rows) - 1 - row_index] = list(row)
        return canvas

    def get(self, coordinates: Coordinates) -> str:
        """Return the terrain code at ``coordinates``."""
        x, y = self._checked(coordinates)
        return self._cells[y][x]

    def set(self, coordinates: Coordinates, code: str) -> None:
        """Set the terrain code at ``coordinates``."""
        self._check_code(code)
        x, y = self._checked(coordinates)
        self._cells[y][x] = code

    def fill_rect(
        self, corner_a: Coordinates, corner_b: Coordinates, code: str
    ) -> None:
        """Fill the rectangle between two corners, both inclusive."""
        self._check_code(code)
        x1, y1 = self._checked(corner_a)
        x2, y2 = self._checked(corner_b)
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for x in range(min(x1, x2), max(x1, x2) + 1):
                self._cells[y][x] = code

    def fill_between(
        self, lower: Sequence[int], upper: Sequence[int], code: str
    ) -> None:
        """Fill each column from ``lower[x]`` up to, not including, ``upper[x]``.

        Both sequences need one value per column. Values are clamped to the
        canvas, so an edge may run off the map. Pair it with ``jagged_edge``
        to draw organic bands.
        """
        self._check_code(code)
        if len(lower) != self.width or len(upper) != self.width:
            raise ValueError(
                f"lower and upper need {self.width} values, got "
                f"{len(lower)} and {len(upper)}."
            )
        for x in range(self.width):
            start = max(0, lower[x])
            stop = min(self.height, upper[x])
            for y in range(start, stop):
                self._cells[y][x] = code

    def to_rows(self) -> list[str]:
        """Return the grid as strings, north row first."""
        return ["".join(row) for row in reversed(self._cells)]

    def _checked(self, coordinates: Coordinates) -> Coordinates:
        x, y = coordinates
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise IndexError(
                f"{coordinates} is outside the {self.width}x{self.height} "
                "canvas."
            )
        return coordinates

    @staticmethod
    def _check_code(code: str) -> None:
        if len(code) != 1:
            raise ValueError(
                f"Terrain codes must be a single character, got {code!r}."
            )
