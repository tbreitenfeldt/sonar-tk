from sonartk.map_builder.map_2d.map_object import MapObject


def test_map_object_init_sets_name_and_coordinates() -> None:
    obj = MapObject("chest", (2, 3))

    assert obj.name == "chest"
    assert obj.coordinates == (2, 3)


def test_map_object_interact_is_no_op() -> None:
    obj = MapObject("switch", (1, 1))

    obj.interact()
