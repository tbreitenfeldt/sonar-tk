from sonartk.util import Coordinates, Direction


def direction_offset(direction: Direction) -> tuple[int, int]:
    """Return the coordinate delta for a Direction value."""
    direction_to_offset: dict[Direction, tuple[int, int]] = {
        Direction.UP: (0, 1),
        Direction.DIAGONAL_UPPER_RIGHT: (1, 1),
        Direction.RIGHT: (1, 0),
        Direction.DIAGONAL_LOWER_RIGHT: (1, -1),
        Direction.DOWN: (0, -1),
        Direction.DIAGONAL_LOWER_LEFT: (-1, -1),
        Direction.LEFT: (-1, 0),
        Direction.DIAGONAL_UPPER_LEFT: (-1, 1),
    }
    return direction_to_offset[direction]


def step_coordinates(
    origin: Coordinates,
    direction: Direction,
    distance: int = 1,
) -> Coordinates:
    """Translate origin by direction and integer distance."""
    if distance < 0:
        raise ValueError("distance must be greater than or equal to 0")

    dx, dy = direction_offset(direction)
    return (origin[0] + (dx * distance), origin[1] + (dy * distance))
