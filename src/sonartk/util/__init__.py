from enum import Enum
from typing import TypeAlias

from sonartk.util.asset_loader import AssetLoader, sound_pool_loader
from sonartk.util.catalog import AssetCatalog, resolve_name
from sonartk.util.key_handler import Callback, Key, KeyHandler
from sonartk.util.state import State
from sonartk.util.state_machine import EmptyState, StateMachine
from sonartk.util.text_history import TextHistory

Coordinates: TypeAlias = tuple[int, int]


class Direction(Enum):
    UP = 1
    DIAGONAL_UPPER_RIGHT = 2
    RIGHT = 3
    DIAGONAL_LOWER_RIGHT = 4
    DOWN = 5
    DIAGONAL_LOWER_LEFT = 6
    LEFT = 7
    DIAGONAL_UPPER_LEFT = 8


__all__ = [
    "Callback",
    "AssetCatalog",
    "AssetLoader",
    "Coordinates",
    "Direction",
    "EmptyState",
    "Key",
    "KeyHandler",
    "State",
    "StateMachine",
    "TextHistory",
    "resolve_name",
    "sound_pool_loader",
    "speech_manager",
]
