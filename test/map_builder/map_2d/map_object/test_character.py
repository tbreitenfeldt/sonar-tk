from sonartk.map_builder.map_2d.map_object.character import Character
from sonartk.util import Direction


def test_character_init_sets_fields() -> None:
    character = Character("hero", (4, 5), Direction.RIGHT, radius=7)

    assert character.name == "hero"
    assert character.coordinates == (4, 5)
    assert character.directional_orientation is Direction.RIGHT
    assert character.radius == 7


def test_character_default_radius() -> None:
    character = Character("hero", (0, 0), Direction.UP)

    assert character.radius == 5
