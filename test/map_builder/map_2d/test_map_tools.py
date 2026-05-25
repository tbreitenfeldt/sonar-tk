import pytest

from sonartk.map_builder.map_2d.map_tools import mark_adjacent_tiles


def test_mark_adjacent_tiles_marks_cardinal_neighbors_only() -> None:
    grid = [
        ["0", "0", "0"],
        ["0", "2", "0"],
        ["0", "0", "0"],
    ]

    updated = mark_adjacent_tiles(
        grid,
        source_values={"2"},
        replacement_value="3",
        replaceable_values={"0"},
        include_diagonals=False,
    )

    assert updated == [
        ["0", "3", "0"],
        ["3", "2", "3"],
        ["0", "3", "0"],
    ]


def test_mark_adjacent_tiles_can_include_diagonals() -> None:
    grid = [
        ["0", "0", "0"],
        ["0", "2", "0"],
        ["0", "0", "0"],
    ]

    updated = mark_adjacent_tiles(
        grid,
        source_values={"2"},
        replacement_value="3",
        replaceable_values={"0"},
        include_diagonals=True,
    )

    assert updated == [
        ["3", "3", "3"],
        ["3", "2", "3"],
        ["3", "3", "3"],
    ]


def test_mark_adjacent_tiles_requires_rectangular_grid() -> None:
    with pytest.raises(ValueError, match="rectangular"):
        mark_adjacent_tiles(
            [["0", "0"], ["0"]],
            source_values={"2"},
            replacement_value="3",
            replaceable_values={"0"},
        )
