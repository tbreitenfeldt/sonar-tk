from enum import Enum
from typing import TypeAlias

import sonartk.util.speech_manager
from sonartk.util.key_handler import Callback, Key, KeyHandler
from sonartk.util.state import State
from sonartk.util.state_machine import EmptyState, StateMachine


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
    "Coordinates",
    "Direction",
    "EmptyState",
    "Key",
    "KeyHandler",
    "State",
    "StateMachine",
    "speech_manager",
]
