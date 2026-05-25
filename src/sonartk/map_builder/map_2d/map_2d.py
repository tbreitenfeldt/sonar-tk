from types import MappingProxyType
from typing import Literal, Mapping, Optional

from sonartk.map_builder.map_2d.map_object.character import Character
from sonartk.map_builder.map_2d.map_tile import MapTile
from sonartk.map_builder.map_2d.map_object import MapObject
from sonartk.map_builder.map_2d.map_queries import Map2dQueries
from sonartk.util import Coordinates

CharacterCollisionPolicy = Literal["error", "replace"]
ObjectCollisionPolicy = Literal["error", "replace"]


class Map2d:
    def __init__(
        self,
        name: str,
        character: Character,
        *,
        character_collision_policy: CharacterCollisionPolicy = "error",
        object_collision_policy: ObjectCollisionPolicy = "error",
    ) -> None:
        self.name: str = name
        self.character: Character = character
        self.tile_map: list[MapTile] = []
        self.height: int = 0
        self.width: int = 0
        self.character_collision_policy = character_collision_policy
        self.object_collision_policy = object_collision_policy
        self._character_index: dict[Coordinates, Character] = {}
        self._object_index: dict[Coordinates, MapObject] = {}
        self._character_index_view: Mapping[Coordinates, Character] = (
            MappingProxyType(self._character_index)
        )
        self._object_index_view: Mapping[Coordinates, MapObject] = (
            MappingProxyType(self._object_index)
        )
        self.queries: Map2dQueries = Map2dQueries(self)
        self.register_character(character)

    @property
    def character_index(self) -> Mapping[Coordinates, Character]:
        """Read-only coordinate index for registered characters."""
        return self._character_index_view

    @property
    def object_index(self) -> Mapping[Coordinates, MapObject]:
        """Read-only coordinate index for registered map objects."""
        return self._object_index_view

    def add_row(self, row: list[MapTile]) -> None:
        """Insert a map row and update map dimensions.

        New rows are prepended so ``y=0`` points at the most recently inserted
        row, matching the current map coordinate convention.
        """
        if self.tile_map and self.width != len(row):
            raise IndexError(
                f"The width of the new row must match the width of the map.  Row Width: {len(row)} - Map Width: {self.width}"
            )
        if not self.tile_map:
            self.width = len(row)

        self.height += 1
        self.tile_map[:0] = row

    def get_tile(self, coordinates: Coordinates) -> MapTile:
        """Return the tile at coordinates, raising on out-of-range access."""
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

    def set_tile(self, coordinates: Coordinates, tile: MapTile) -> None:
        """Replace the tile at coordinates, raising on out-of-range access."""
        x, y = coordinates
        if x >= self.width or x < 0:
            raise IndexError(
                f"x value is out of bounds. x cannot be less than0 or greater than map width.  x: {x} - map width: {self.width}"
            )
        if y >= self.height or y < 0:
            raise IndexError(
                f"y value is out of bounds. y cannot be less than 0 or greater than map height.  y: {y} - map height: {self.height}"
            )

        self.tile_map[y * self.width + x] = tile

    def set_tiles(self, updates: Mapping[Coordinates, MapTile]) -> None:
        """Apply multiple tile replacements as a single convenience operation."""
        for coordinates, tile in updates.items():
            self.set_tile(coordinates, tile)

    def register_character(self, character: Character) -> Optional[Character]:
        """Register a character and return any displaced occupant at that coordinate."""
        self._validate_coordinate_for_registration(character.coordinates)
        displaced = self._ensure_character_slot_available(
            character.coordinates, character
        )
        self._character_index[character.coordinates] = character
        return displaced

    def move_character(
        self, character: Character, new_coordinates: Coordinates
    ) -> Optional[Character]:
        """Move a character and return any displaced occupant at destination."""
        self._validate_coordinate_for_registration(new_coordinates)
        current_coordinates = character.coordinates
        if self._character_index.get(current_coordinates) is not character:
            raise LookupError(
                f"The character {character.name} is not registered at coordinates {current_coordinates}."
            )

        displaced = self._ensure_character_slot_available(
            new_coordinates, character
        )

        del self._character_index[current_coordinates]
        character.coordinates = new_coordinates
        self._character_index[new_coordinates] = character
        return displaced

    def remove_character(self, character: Character) -> None:
        """Remove a registered character from the coordinate index."""
        current_coordinates = character.coordinates
        if self._character_index.get(current_coordinates) is not character:
            raise LookupError(
                f"The character {character.name} is not registered at coordinates {current_coordinates}."
            )

        del self._character_index[current_coordinates]

    def register_map_object(
        self, map_object: MapObject
    ) -> Optional[MapObject]:
        """Register a map object and return any displaced occupant at that coordinate."""
        self._validate_coordinate_for_registration(map_object.coordinates)
        displaced = self._ensure_object_slot_available(
            map_object.coordinates, map_object
        )
        self._object_index[map_object.coordinates] = map_object
        return displaced

    def move_map_object(
        self, map_object: MapObject, new_coordinates: Coordinates
    ) -> Optional[MapObject]:
        """Move a map object and return any displaced occupant at destination."""
        self._validate_coordinate_for_registration(new_coordinates)
        current_coordinates = map_object.coordinates
        if self._object_index.get(current_coordinates) is not map_object:
            raise LookupError(
                f"The map object {map_object.name} is not registered at coordinates {current_coordinates}."
            )

        displaced = self._ensure_object_slot_available(
            new_coordinates, map_object
        )

        del self._object_index[current_coordinates]
        map_object.coordinates = new_coordinates
        self._object_index[new_coordinates] = map_object
        return displaced

    def remove_map_object(self, map_object: MapObject) -> None:
        """Remove a registered map object from the coordinate index."""
        current_coordinates = map_object.coordinates
        if self._object_index.get(current_coordinates) is not map_object:
            raise LookupError(
                f"The map object {map_object.name} is not registered at coordinates {current_coordinates}."
            )

        del self._object_index[current_coordinates]

    def find_map_object_coordinates(
        self, map_object: MapObject
    ) -> Optional[Coordinates]:
        """Return coordinates for a registered map object by identity."""
        for coordinates, registered_object in self._object_index.items():
            if registered_object is map_object:
                return coordinates

        return None

    def is_map_object_registered(self, map_object: MapObject) -> bool:
        """Return whether a map object is currently registered by identity."""
        return self.find_map_object_coordinates(map_object) is not None

    def get_map_object_at(
        self, coordinates: Coordinates
    ) -> Optional[MapObject]:
        """Return the registered map object at coordinates, if present."""
        return self._object_index.get(coordinates)

    def remove_map_object_at(
        self, coordinates: Coordinates
    ) -> Optional[MapObject]:
        """Remove and return the map object at coordinates, if present."""
        removed = self._object_index.get(coordinates)
        if removed is None:
            return None

        del self._object_index[coordinates]
        return removed

    def _ensure_character_slot_available(
        self, coordinates: Coordinates, character: Character
    ) -> Optional[Character]:
        existing = self._character_index.get(coordinates)
        if existing is None or existing is character:
            return None

        if self.character_collision_policy == "replace":
            del self._character_index[coordinates]
            return existing

        raise ValueError(
            f"Character coordinate collision at {coordinates} for '{character.name}'."
        )

    def _validate_coordinate_for_registration(
        self, coordinates: Coordinates
    ) -> None:
        """Validate coordinates when map dimensions are known.

        Map entities are constructed before rows are loaded in many flows, so
        bounds checks are deferred until width/height are available.
        """
        if self.width == 0 or self.height == 0:
            return

        x, y = coordinates
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            raise ValueError(
                "Coordinates out of map bounds: "
                f"{coordinates} for map size ({self.width}, {self.height})."
            )

    def _ensure_object_slot_available(
        self, coordinates: Coordinates, map_object: MapObject
    ) -> Optional[MapObject]:
        existing = self._object_index.get(coordinates)
        if existing is None or existing is map_object:
            return None

        if self.object_collision_policy == "replace":
            del self._object_index[coordinates]
            return existing

        raise ValueError(
            f"Map object coordinate collision at {coordinates} for '{map_object.name}'."
        )
