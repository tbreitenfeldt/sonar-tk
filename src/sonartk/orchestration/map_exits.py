from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, Hashable, Optional, TypeVar

from pyglet.event import EventDispatcher

from sonartk.map_builder.map_2d.map_document import MapDocument
from sonartk.util import Coordinates

TMap = TypeVar("TMap")


@dataclass(frozen=True)
class MapExit:
    """A tile that leads to another map.

    Attributes:
        coordinates: Tile on the current map that triggers the exit.
        target_map: Key of the destination map registered with a
            ``MapSwitcher``.
        target_coordinates: Where the player appears on the destination map.
    """

    coordinates: Coordinates
    target_map: Hashable
    target_coordinates: Coordinates


class MapExitRegistry:
    """Lookup of exits for one map by tile coordinates."""

    def __init__(self) -> None:
        self._exits: dict[Coordinates, MapExit] = {}

    @classmethod
    def from_document(cls, document: MapDocument) -> "MapExitRegistry":
        """Build a registry from the exits listed in a map document."""
        registry = cls()
        for item in document.exits:
            registry.add(
                MapExit(
                    item.coordinates,
                    item.target_map,
                    item.target_coordinates,
                )
            )
        return registry

    def add(self, map_exit: MapExit) -> None:
        """Register an exit, rejecting a second exit on the same tile."""
        if map_exit.coordinates in self._exits:
            raise ValueError(
                f"An exit is already registered at {map_exit.coordinates}."
            )
        self._exits[map_exit.coordinates] = map_exit

    def exit_at(self, coordinates: Coordinates) -> Optional[MapExit]:
        """Return the exit at coordinates, or None."""
        return self._exits.get(coordinates)

    def __len__(self) -> int:
        return len(self._exits)


class MapSwitcher(EventDispatcher, Generic[TMap]):
    """Keep one active map in memory and swap it for another on demand.

    Games register a loader per map key. A loader receives the spawn
    coordinates (or None for the map's default start) and returns a
    game-defined map object. The previous map is released when the swap
    completes.

    Events:
        on_map_leave(previous_key, previous_map): Fired before the swap, only
            when a map was active.
        on_map_enter(key, new_map, spawn): Fired after the new map is active.
    """

    def __init__(self) -> None:
        super().__init__()
        self._loaders: dict[Hashable, Callable[[Optional[Coordinates]], TMap]]
        self._loaders = {}
        self._current: Optional[TMap] = None
        self._current_key: Optional[Hashable] = None

    @property
    def current(self) -> Optional[TMap]:
        """The active map, or None before the first switch."""
        return self._current

    @property
    def current_key(self) -> Optional[Hashable]:
        """Key of the active map, or None before the first switch."""
        return self._current_key

    def register(
        self,
        key: Hashable,
        loader: Callable[[Optional[Coordinates]], TMap],
        *,
        replace: bool = False,
    ) -> None:
        """Register a loader for a map key.

        An existing key raises ``ValueError`` unless ``replace`` is true,
        which swaps in the new loader, such as after reloading a map file.
        """
        if key in self._loaders and not replace:
            raise ValueError(f"A map is already registered for {key!r}.")
        self._loaders[key] = loader

    def switch_to(
        self, key: Hashable, spawn: Optional[Coordinates] = None
    ) -> TMap:
        """Load and activate a map.

        The new map is loaded first, so a failing loader leaves the current
        map active and fires no events.
        """
        if key not in self._loaders:
            raise KeyError(f"No map registered for {key!r}.")

        new_map = self._loaders[key](spawn)

        if self._current_key is not None:
            self.dispatch_event(
                "on_map_leave", self._current_key, self._current
            )
        self._current = new_map
        self._current_key = key
        self.dispatch_event("on_map_enter", key, new_map, spawn)
        return new_map

    def follow_exit(self, map_exit: MapExit) -> TMap:
        """Switch to the destination described by an exit."""
        return self.switch_to(map_exit.target_map, map_exit.target_coordinates)

    def try_exit(
        self, registry: MapExitRegistry, coordinates: Coordinates
    ) -> bool:
        """Follow the exit at coordinates, if any. Returns True if switched.

        Call this from a movement-success hook with the player's new tile.
        """
        map_exit = registry.exit_at(coordinates)
        if map_exit is None:
            return False
        self.follow_exit(map_exit)
        return True

    def on_map_leave(self, key: Hashable, map_obj: Optional[TMap]) -> None:
        """Default event handler."""

    def on_map_enter(
        self, key: Hashable, map_obj: TMap, spawn: Optional[Coordinates]
    ) -> None:
        """Default event handler."""


MapSwitcher.register_event_type("on_map_leave")
MapSwitcher.register_event_type("on_map_enter")
