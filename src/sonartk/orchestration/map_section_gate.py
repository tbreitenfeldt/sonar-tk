from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, Mapping, Optional, Protocol, TypeVar

from sonartk.map_builder.map_2d.map_object.character import Character
from sonartk.map_builder.map_2d.map_tile import MapTile
from sonartk.util import Coordinates

TCharacter = TypeVar("TCharacter", bound=Character)


class _MapSectionService(Protocol):
    @property
    def character_index(self) -> Mapping[Coordinates, Character]: ...

    def set_tiles(self, updates: Mapping[Coordinates, MapTile]) -> None: ...

    def register_character(
        self, character: Character
    ) -> Optional[Character]: ...

    def remove_character(self, character: Character) -> None: ...


@dataclass(frozen=True)
class MapSectionTiles:
    """Open and closed tile layouts for a map section."""

    open_tiles: Mapping[Coordinates, MapTile]
    closed_tiles: Mapping[Coordinates, MapTile]


class MapSectionGate(Generic[TCharacter]):
    """Manage open/close tile patches and optional section-character lifecycle."""

    def __init__(
        self,
        map_service: _MapSectionService,
        tiles: MapSectionTiles,
        *,
        section_character: Optional[TCharacter] = None,
        on_open: Optional[Callable[[], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
        starts_open: bool = False,
    ) -> None:
        self.map_service = map_service
        self.tiles = tiles
        self.section_character = section_character
        self.on_open = on_open
        self.on_close = on_close
        self.is_open = starts_open

    def open(self) -> None:
        """Open the section and apply open layout behavior."""
        self.map_service.set_tiles(self.tiles.open_tiles)
        self._register_character_if_needed()
        self.is_open = True
        if self.on_open is not None:
            self.on_open()

    def close(self) -> None:
        """Close the section and apply closed layout behavior."""
        self.map_service.set_tiles(self.tiles.closed_tiles)
        self._remove_character_if_registered()
        self.is_open = False
        if self.on_close is not None:
            self.on_close()

    def _register_character_if_needed(self) -> None:
        if self.section_character is None:
            return

        is_registered = any(
            registered is self.section_character
            for registered in self.map_service.character_index.values()
        )
        if not is_registered:
            self.map_service.register_character(self.section_character)

    def _remove_character_if_registered(self) -> None:
        if self.section_character is None:
            return

        is_registered = any(
            registered is self.section_character
            for registered in self.map_service.character_index.values()
        )
        if is_registered:
            self.map_service.remove_character(self.section_character)
