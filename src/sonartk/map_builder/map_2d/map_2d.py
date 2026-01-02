from typing import Any, Optional, Callable, TypeAlias
from collections import deque

from sonartk.map_builder.map_2d.map_object.character import Character
from sonartk.map_builder.map_2d.parser.map_parser import MapParser
from sonartk.map_builder.map_2d.map_tile import MapTile
from sonartk.map_builder.map_2d.map_object import MapObject
from sonartk.util import Coordinates


class Map2d:
    def __init__(self, name: str, character: Character) -> None:
        self.name: str = name
        self.character: Character = character
        self.tile_map: list[MapTile] = []
        self.height: int = 0
        self.width: int = 0
        self.characters: dict[Coordinates, Character] = {}
        self.objects: dict[Coordinates, MapObject] = {}
        self.add_character(character.coordinates, character)

    def add_row(self, row: list[MapTile]) -> None:
        if self.tile_map and self.width != len(row):
            raise IndexError(
                f"The width of the new row must match the width of the map.  Row Width: {len(row)} - Map Width: {len(self.tile_map)}"
            )
        if not self.tile_map:
            self.width = len(row)

        self.height += 1
        self.tile_map[:0] = row

    def get_tile(self, coordinates: Coordinates) -> MapTile:
        x, y = coordinates
        if x >= self.width or x < 0:
            raise IndexError(
                f"x value is out of bounds. x cannot be less than0 or greater than map width.  x: {x} - map width: {self.width}"
            )
        if y >= self.height or y < 0:
            raise IndexError(
                f"y value is out of bounds. y cannot be less than 0 or greater than map height.  y: {y} - map height: {self.height}"
            )

        return self.tile_map[y * self.width + x]

    def add_character(
        self, coordinates: Coordinates, character: Character
    ) -> None:
        self.characters[coordinates] = character

    def change_character_coordinates(
        self,
        current_coordinates: Coordinates,
        new_coordinates: Coordinates,
        character: Character,
    ) -> None:
        if current_coordinates not in self.characters:
            raise LookupError(
                f"The coordinates {current_coordinates} are not found in the characters list {self.characters}"  # noqa: E713
            )

        del self.characters[current_coordinates]
        self.characters[new_coordinates] = character

    def add_map_object(
        self, coordinates: Coordinates, map_object: MapObject
    ) -> None:
        self.objects[coordinates] = map_object

    def change_map_object_coordinates(
        self,
        current_coordinates: Coordinates,
        new_coordinates: Coordinates,
        map_object: MapObject,
    ) -> None:
        if current_coordinates not in self.objects:
            raise LookupError(
                f"The coordinates {current_coordinates} are not found in the objects list {self.objects}"  # noqa: E713
            )

        del self.objects[current_coordinates]
        self.objects[new_coordinates] = map_object

    def check_radius(
        self,
        starting_coordinates: Coordinates,
        action: Callable[
            [
                Coordinates,
                Optional[MapTile],
                Optional[Character],
                Optional[MapObject],
            ],
            None,
        ],
        tile_names: list[str] = [],
    ) -> None:
        x, y = starting_coordinates
        for i in range(1, self.character.radius):
            self.check_coordinates_for_object(
                (x, y + i), action, tile_names
            )  # north
            self.check_coordinates_for_object(
                (x + i, y + i), action, tile_names
            )  # northeast
            self.check_coordinates_for_object(
                (x + i, y), action, tile_names
            )  # east
            self.check_coordinates_for_object(
                (x + i, y - i), action, tile_names
            )  # southeast
            self.check_coordinates_for_object(
                (x, y - i), action, tile_names
            )  # south
            self.check_coordinates_for_object(
                (x - i, y - i), action, tile_names
            )  # southwest
            self.check_coordinates_for_object(
                (x - i, y), action, tile_names
            )  # west
            self.check_coordinates_for_object(
                (x - i, y + i), action, tile_names
            )  # northwest

    def check_coordinates_for_object(
        self,
        coordinates: Coordinates,
        action: Callable[
            [
                Coordinates,
                Optional[MapTile],
                Optional[Character],
                Optional[MapObject],
            ],
            None,
        ],
        tile_names: list[str] = [],
    ) -> None:
        if self.is_coordinates_in_range(coordinates):
            map_object: Optional[MapObject] = (
                self.objects[coordinates]
                if coordinates in self.objects
                else None
            )
            character: Optional[Character] = (
                self.characters[coordinates]
                if coordinates in self.characters
                else None
            )
            tile: Optional[MapTile] = (
                self.get_tile(coordinates)
                if tile_names and self.get_tile(coordinates).name in tile_names
                else None
            )
            action(coordinates, tile, character, map_object)

    def find_path(
        self, start: Coordinates, end: Coordinates
    ) -> list[Coordinates]:
        queue: deque = deque()
        visited: dict[Coordinates, None] = {}
        queue.append((start, []))  # startpoint, and empty path

        while len(queue) > 0:
            node: Coordinates
            path: list[Coordinates]
            node, path = queue.pop()
            path.append(node)
            visited[node] = None

            if node == end:
                return path

            for item in self.get_adjacent_passable_coordinates(node):
                if item not in visited:
                    queue.append((item, path[:]))

        return []  # no path found

    def get_adjacent_passable_coordinates(
        self, coordinates: Coordinates
    ) -> list[Coordinates]:
        x, y = coordinates
        adjacent_coordinates: list[tuple[int, int]] = []
        # north
        if self.is_tile_passable((x, y + 1)):
            adjacent_coordinates.append((x, y + 1))
        # east
        if self.is_tile_passable((x + 1, y)):
            adjacent_coordinates.append((x + 1, y))
        # south
        if self.is_tile_passable((x, y - 1)):
            adjacent_coordinates.append((x, y - 1))
        # west
        if self.is_tile_passable((x - 1, y)):
            adjacent_coordinates.append((x - 1, y))

        return adjacent_coordinates

    def is_tile_passable(self, coordinates: Coordinates) -> bool:
        if self.is_coordinates_in_range(coordinates):
            tile: MapTile = self.get_tile(coordinates)
            return tile.is_passable and (
                not tile.is_one_way or (tile.is_one_way and tile.is_jumpable)
            )

        return False

    def is_coordinates_in_range(self, coordinates: Coordinates) -> bool:
        return (
            coordinates[0] >= 0
            and coordinates[0] < self.width
            and coordinates[1] >= 0
            and coordinates[1] < self.height
        )
