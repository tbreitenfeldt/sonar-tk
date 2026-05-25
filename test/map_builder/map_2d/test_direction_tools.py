import pytest

from sonartk.map_builder.map_2d import direction_offset, step_coordinates
from sonartk.util import Direction


def test_direction_offset_returns_expected_delta() -> None:
    assert direction_offset(Direction.UP) == (0, 1)
    assert direction_offset(Direction.RIGHT) == (1, 0)
    assert direction_offset(Direction.DOWN) == (0, -1)
    assert direction_offset(Direction.LEFT) == (-1, 0)
    assert direction_offset(Direction.DIAGONAL_UPPER_RIGHT) == (1, 1)


def test_step_coordinates_translates_origin() -> None:
    assert step_coordinates((2, 3), Direction.UP) == (2, 4)
    assert step_coordinates((2, 3), Direction.LEFT, distance=2) == (0, 3)
    assert step_coordinates((2, 3), Direction.DIAGONAL_LOWER_RIGHT) == (3, 2)


def test_step_coordinates_rejects_negative_distance() -> None:
    with pytest.raises(ValueError, match="distance"):
        step_coordinates((0, 0), Direction.UP, distance=-1)
