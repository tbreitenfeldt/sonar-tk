from importlib import import_module
from typing import TYPE_CHECKING, Any

__all__ = [
    "BuiltMapGridGame",
    "MapGridGameBuilder",
    "MapSoundNavigationController",
]

if TYPE_CHECKING:
    from sonartk.orchestration.game_builder import (
        BuiltMapGridGame,
        MapGridGameBuilder,
    )
    from sonartk.orchestration.map_sound_navigation import (
        MapSoundNavigationController,
    )


def __getattr__(name: str) -> Any:
    if name in {"BuiltMapGridGame", "MapGridGameBuilder"}:
        module = import_module("sonartk.orchestration.game_builder")
        return getattr(module, name)
    if name == "MapSoundNavigationController":
        module = import_module("sonartk.orchestration.map_sound_navigation")
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
