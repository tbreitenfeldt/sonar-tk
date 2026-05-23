from importlib import import_module
from typing import TYPE_CHECKING, Any

__all__ = [
    "Window",
    "MapGridGameBuilder",
    "BuiltMapGridGame",
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
    from sonartk.ui.window import Window


def __getattr__(name: str) -> Any:
    if name == "Window":
        from sonartk.ui.window import Window

        return Window
    if name in {
        "MapGridGameBuilder",
        "BuiltMapGridGame",
        "MapSoundNavigationController",
    }:
        orchestration = import_module("sonartk.orchestration")
        return getattr(orchestration, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
