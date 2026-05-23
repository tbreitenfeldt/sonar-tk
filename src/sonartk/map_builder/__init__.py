from importlib import import_module
from typing import TYPE_CHECKING, Any

__all__ = ["Map2d", "MapTile", "load_2d_map"]

if TYPE_CHECKING:
    from sonartk.map_builder.map_2d import Map2d, MapTile, load_2d_map


def __getattr__(name: str) -> Any:
    if name in __all__:
        module = import_module("sonartk.map_builder.map_2d")
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
