from __future__ import annotations

import random
from typing import Callable, Generic, Optional, TypeVar

from sonartk.map_builder.map_2d import Map2d
from sonartk.map_builder.map_2d.map_object.map_object import MapObject
from sonartk.util import Coordinates

TMapObject = TypeVar("TMapObject", bound=MapObject)


class MapObjectCollectionSession(Generic[TMapObject]):
    """Manage spawned map objects for pickup/collection game loops.

    The session owns the lifecycle for objects it spawns and supports
    type-safe collection, configurable spawn filtering, and transactional
    resets.
    """

    def __init__(
        self,
        map2d: Map2d,
        *,
        object_count: int,
        object_type: type[TMapObject],
        object_factory: Callable[[int, Coordinates], TMapObject],
        excluded_coordinates: Optional[set[Coordinates]] = None,
        forbidden_coordinates: Optional[set[Coordinates]] = None,
        required_coordinates: Optional[set[Coordinates]] = None,
        coordinate_predicate: Optional[Callable[[Coordinates], bool]] = None,
        object_label: str = "objects",
        rng: Optional[random.Random] = None,
    ) -> None:
        if object_count < 0:
            raise ValueError("object_count must be greater than or equal to 0")

        self.map2d = map2d
        self.object_count = object_count
        self.object_type = object_type
        self.object_factory = object_factory
        self.excluded_coordinates = set(excluded_coordinates or set())
        self.forbidden_coordinates = set(forbidden_coordinates or set())
        self.required_coordinates = set(required_coordinates or set())
        self._validate_required_coordinates_in_bounds()
        self.coordinate_predicate = coordinate_predicate
        self.object_label = object_label
        self.rng = rng
        self._active_objects: list[TMapObject] = []

    @property
    def collected_count(self) -> int:
        """Return how many objects were collected in the current session."""
        return self.object_count - self.remaining_count

    @property
    def remaining_count(self) -> int:
        """Return how many spawned objects remain on the map."""
        return len(self._active_objects)

    def reset(self) -> None:
        """Respawn session objects using current spawn constraints.

        Reset is transactional. If object creation or registration fails,
        the previous active set is restored and no partial spawn remains.
        """
        removed_active_objects: list[TMapObject] = []
        for existing_object in self._active_objects:
            if self.map2d.is_map_object_registered(existing_object):
                self.map2d.remove_map_object(existing_object)
                removed_active_objects.append(existing_object)

        self._active_objects = []
        newly_registered_objects: list[TMapObject] = []
        try:
            spawn_coordinates = self._place_random_passable_positions(
                self.object_count,
                excluded_coordinates=self.excluded_coordinates,
            )

            staged_objects: list[TMapObject] = []
            for index, coordinates in enumerate(spawn_coordinates, start=1):
                staged_objects.append(self.object_factory(index, coordinates))

            for map_object in staged_objects:
                self.map2d.register_map_object(map_object)
                newly_registered_objects.append(map_object)
                self._active_objects.append(map_object)
        except Exception:
            for map_object in newly_registered_objects:
                if self.map2d.is_map_object_registered(map_object):
                    self.map2d.remove_map_object(map_object)

            self._active_objects = []
            for map_object in removed_active_objects:
                if not self.map2d.is_map_object_registered(map_object):
                    self.map2d.register_map_object(map_object)
                self._active_objects.append(map_object)
            raise

    def has_object_at(self, coordinates: Coordinates) -> bool:
        """Return whether a matching object exists at coordinates."""
        return isinstance(
            self.map2d.get_map_object_at(coordinates),
            self.object_type,
        )

    def collect_at(self, coordinates: Coordinates) -> Optional[TMapObject]:
        """Remove and return the matching object at coordinates, if present."""
        existing = self.map2d.get_map_object_at(coordinates)
        if not isinstance(existing, self.object_type):
            return None

        self.map2d.remove_map_object(existing)

        self._active_objects = [
            map_object
            for map_object in self._active_objects
            if map_object is not existing
        ]
        return existing

    def _place_random_passable_positions(
        self,
        count: int,
        *,
        excluded_coordinates: set[Coordinates],
    ) -> set[Coordinates]:
        """Select random coordinates that satisfy passability and filters."""
        candidate_coordinates = self.required_coordinates or {
            (x, y)
            for y in range(self.map2d.height)
            for x in range(self.map2d.width)
        }

        forbidden_coordinates = excluded_coordinates.union(
            self.forbidden_coordinates
        )

        active_object_coordinates = {
            coordinates
            for coordinates, map_object in self.map2d.object_index.items()
            if map_object not in self._active_objects
        }

        passable_coordinates = [
            (x, y)
            for x, y in candidate_coordinates
            if self.map2d.get_tile((x, y)).is_passable
            and (x, y) not in forbidden_coordinates
            and (x, y) not in active_object_coordinates
            and (x, y) not in self.map2d.character_index
            and (
                self.coordinate_predicate is None
                or self.coordinate_predicate((x, y))
            )
        ]

        if len(passable_coordinates) < count:
            raise ValueError(
                f"Cannot place {count} {self.object_label}. Only {len(passable_coordinates)} passable tiles are available."
            )

        chooser = self.rng if self.rng is not None else random
        return set(chooser.sample(passable_coordinates, k=count))

    def _validate_required_coordinates_in_bounds(self) -> None:
        """Treat required coordinates as public API input and validate eagerly."""
        if not self.required_coordinates:
            return

        invalid_coordinates = sorted(
            coordinates
            for coordinates in self.required_coordinates
            if not self.map2d.queries.is_coordinates_in_range(coordinates)
        )
        if invalid_coordinates:
            raise ValueError(
                "required_coordinates contains out-of-range coordinates: "
                + ", ".join(
                    str(coordinates) for coordinates in invalid_coordinates
                )
            )
