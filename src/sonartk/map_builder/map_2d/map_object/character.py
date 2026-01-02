from sonartk.map_builder.map_2d.map_object import MapObject
from sonartk.util import Coordinates, Direction


class Character(MapObject):
    def __init__(
        self,
        name: str,
        coordinates: Coordinates,
        directional_orientation: Direction,
        radius: int = 5,
    ) -> None:
        super().__init__(name, coordinates)
        self.directional_orientation: Direction = directional_orientation
        self.radius: int = radius
