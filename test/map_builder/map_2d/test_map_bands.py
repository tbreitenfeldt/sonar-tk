import pytest

from sonartk.map_builder.map_2d.map_bands import MapBand, build_banded_map
from sonartk.map_builder.map_2d.map_object.character import Character
from sonartk.map_builder.map_2d.map_tile import MapTile
from sonartk.util import Direction

WATER = MapTile("water", is_passable=False)
SAND = MapTile("sand", is_passable=True)


def _hero() -> Character:
    return Character("hero", (0, 0), Direction.UP)


def test_build_banded_map_sets_dimensions() -> None:
    map2d = build_banded_map(
        "beach",
        width=6,
        bands=[MapBand(WATER, 2), MapBand(SAND, 3)],
        character=_hero(),
    )

    assert map2d.name == "beach"
    assert (map2d.width, map2d.height) == (6, 5)


def test_first_band_is_north_at_highest_y() -> None:
    map2d = build_banded_map(
        "beach",
        width=4,
        bands=[MapBand(WATER, 2), MapBand(SAND, 3)],
        character=_hero(),
    )

    for x in range(4):
        assert [map2d.get_tile((x, y)).name for y in range(5)] == [
            "sand",
            "sand",
            "sand",
            "water",
            "water",
        ]


def test_bands_share_tile_instances() -> None:
    map2d = build_banded_map(
        "beach",
        width=3,
        bands=[MapBand(SAND, 2)],
        character=_hero(),
    )

    assert map2d.get_tile((0, 0)) is SAND
    assert map2d.get_tile((2, 1)) is SAND


@pytest.mark.parametrize("width", [0, -1])
def test_rejects_non_positive_width(width: int) -> None:
    with pytest.raises(ValueError, match="width"):
        build_banded_map(
            "m", width=width, bands=[MapBand(SAND, 1)], character=_hero()
        )


def test_rejects_empty_bands() -> None:
    with pytest.raises(ValueError, match="band"):
        build_banded_map("m", width=3, bands=[], character=_hero())


def test_rejects_non_positive_band_rows() -> None:
    with pytest.raises(ValueError, match="rows"):
        build_banded_map(
            "m", width=3, bands=[MapBand(SAND, 0)], character=_hero()
        )
