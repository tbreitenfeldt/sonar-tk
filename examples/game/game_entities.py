"""Game-specific map object entities for the map sounds example."""

from sonartk.map_builder.map_2d.map_object import MapObject
from sonartk.map_builder.map_2d.map_object.character import Character


class Coin(MapObject):
    """Collectible coin entity."""


class Monster(Character):
    """Monster character entity."""
