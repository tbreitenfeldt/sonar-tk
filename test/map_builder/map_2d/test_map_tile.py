from sonartk.map_builder.map_2d.map_tile import MapTile
from sonartk.util import Direction


def test_map_tile_init_defaults() -> None:
    tile = MapTile("grass")

    assert tile.name == "grass"
    assert tile.is_passable is True
    assert tile.allowed_entry_directions is None
    assert tile.required_capabilities == frozenset()


def test_map_tile_init_custom_flags() -> None:
    tile = MapTile(
        "wall",
        is_passable=False,
        allowed_entry_directions=frozenset({Direction.LEFT}),
        required_capabilities=frozenset({"flight"}),
    )

    assert tile.name == "wall"
    assert tile.is_passable is False
    assert tile.allowed_entry_directions == frozenset({Direction.LEFT})
    assert tile.required_capabilities == frozenset({"flight"})


def test_map_tile_interact_is_no_op() -> None:
    tile = MapTile("grass")

    tile.interact()


def test_map_tile_str_contains_all_fields() -> None:
    tile = MapTile(
        "ledge",
        is_passable=True,
        allowed_entry_directions=frozenset({Direction.LEFT, Direction.UP}),
    )

    value = str(tile)

    assert "name: ledge" in value
    assert "is_passable: True" in value
    assert "allowed_entry_directions:" in value
    assert "LEFT" in value
    assert "UP" in value
    assert "required_capabilities:" in value
