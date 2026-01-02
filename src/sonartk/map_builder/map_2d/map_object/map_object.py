from sonartk.util import Coordinates


class MapObject:
    def __init__(self, name: str, coordinates: Coordinates) -> None:
        self.name: str = name
        self.coordinates: Coordinates = coordinates

    def interact(self) -> None:
        pass
