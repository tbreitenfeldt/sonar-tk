from __future__ import annotations

from typing import Mapping, Optional

from sonartk.map_builder.map_2d.map_object.character import Character
from sonartk.map_builder.map_2d.map_tile import MapTile
from sonartk.orchestration.map_section_gate import (
    MapSectionGate,
    MapSectionTiles,
)
from sonartk.util import Direction


class _FakeMapService:
    def __init__(self) -> None:
        self.character_index: dict[tuple[int, int], Character] = {}
        self.applied_tiles: dict[tuple[int, int], MapTile] = {}
        self.removed_characters: list[Character] = []

    def set_tiles(self, updates: Mapping[tuple[int, int], MapTile]) -> None:
        self.applied_tiles = dict(updates)

    def register_character(self, character: Character) -> Optional[Character]:
        self.character_index[character.coordinates] = character
        return None

    def remove_character(self, character: Character) -> None:
        del self.character_index[character.coordinates]
        self.removed_characters.append(character)


def test_map_section_gate_open_applies_open_tiles_and_registers_character() -> (
    None
):
    map_service = _FakeMapService()
    monster = Character("Monster", (3, 3), Direction.LEFT)

    gate = MapSectionGate(
        map_service,
        MapSectionTiles(
            open_tiles={(1, 1): MapTile("path", is_passable=True)},
            closed_tiles={(1, 1): MapTile("wall", is_passable=False)},
        ),
        section_character=monster,
    )

    gate.open()

    assert gate.is_open is True
    assert map_service.applied_tiles[(1, 1)].name == "path"
    assert map_service.character_index[(3, 3)] is monster


def test_map_section_gate_close_applies_closed_tiles_and_removes_character() -> (
    None
):
    map_service = _FakeMapService()
    monster = Character("Monster", (3, 3), Direction.LEFT)

    gate = MapSectionGate(
        map_service,
        MapSectionTiles(
            open_tiles={(1, 1): MapTile("path", is_passable=True)},
            closed_tiles={(1, 1): MapTile("wall", is_passable=False)},
        ),
        section_character=monster,
    )

    gate.open()
    gate.close()

    assert gate.is_open is False
    assert map_service.applied_tiles[(1, 1)].name == "wall"
    assert monster in map_service.removed_characters
