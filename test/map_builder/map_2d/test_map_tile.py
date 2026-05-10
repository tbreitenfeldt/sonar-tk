from sonartk.map_builder.map_2d.map_tile import MapTile


def test_map_tile_init_defaults() -> None:
    tile = MapTile("grass")

    assert tile.name == "grass"
    assert tile.is_passable is True
    assert tile.is_one_way is False
    assert tile.is_jumpable is False


def test_map_tile_init_custom_flags() -> None:
    tile = MapTile("wall", is_passable=False, is_one_way=True)

    assert tile.name == "wall"
    assert tile.is_passable is False
    assert tile.is_one_way is True


def test_map_tile_interact_is_no_op() -> None:
    tile = MapTile("grass")

    tile.interact()


def test_map_tile_str_contains_all_fields() -> None:
    tile = MapTile("ledge", is_passable=True, is_one_way=True)
    tile.is_jumpable = True

    value = str(tile)

    assert "name: ledge" in value
    assert "is_passable: True" in value
    assert "is_one_way: True" in value
    assert "is_jumpable: True" in value
