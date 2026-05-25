from sonartk.map_builder.map_2d.map_object import MapObject


class SampleMapObject(MapObject):
    def __init__(
        self, name: str, coordinates: tuple[int, int], score: int
    ) -> None:
        super().__init__(name, coordinates)
        self.score = score


def test_map_object_init_sets_name_and_coordinates() -> None:
    obj = MapObject("chest", (2, 3))

    assert obj.name == "chest"
    assert obj.coordinates == (2, 3)


def test_map_object_interact_is_no_op() -> None:
    obj = MapObject("switch", (1, 1))

    obj.interact()


def test_map_object_subclass_can_extend_domain_fields() -> None:
    artifact = SampleMapObject("artifact", (2, 3), score=5)

    assert artifact.name == "artifact"
    assert artifact.coordinates == (2, 3)
    assert artifact.score == 5
