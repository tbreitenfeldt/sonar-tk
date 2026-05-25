from copy import deepcopy
from typing import Iterable


def mark_adjacent_tiles(
    grid: list[list[str]],
    *,
    source_values: Iterable[str],
    replacement_value: str,
    replaceable_values: Iterable[str],
    include_diagonals: bool = False,
) -> list[list[str]]:
    """Return a new grid with neighbors of source tiles replaced.

    This utility is useful for terrain post-processing, such as converting
    passable tiles adjacent to hazard tiles into alternate terrain.
    """
    source_set = set(source_values)
    replaceable_set = set(replaceable_values)
    if not grid:
        return []

    result = deepcopy(grid)
    row_count = len(grid)
    col_count = len(grid[0])
    if any(len(row) != col_count for row in grid):
        raise ValueError("Grid must be rectangular.")

    if include_diagonals:
        directions = [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
        ]
    else:
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for y in range(row_count):
        for x in range(col_count):
            if grid[y][x] not in source_set:
                continue

            for dx, dy in directions:
                nx = x + dx
                ny = y + dy
                if nx < 0 or ny < 0 or nx >= col_count or ny >= row_count:
                    continue
                if grid[ny][nx] in replaceable_set:
                    result[ny][nx] = replacement_value

    return result
