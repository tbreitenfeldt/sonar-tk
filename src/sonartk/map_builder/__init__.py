from importlib import import_module
from typing import TYPE_CHECKING, Any

__all__ = [
    "Map2d",
    "MapBand",
    "MapTile",
    "build_banded_map",
    "load_2d_map",
    "DocumentExit",
    "DocumentObject",
    "MAP_DOCUMENT_VERSION",
    "MapCanvas",
    "MapDocument",
    "MapDocumentError",
    "build_map2d_from_document",
    "jagged_edge",
    "load_map_document",
    "save_map_document",
]

if TYPE_CHECKING:
    from sonartk.map_builder.map_2d import (
        Map2d,
        MapBand,
        MapTile,
        build_banded_map,
        load_2d_map,
        DocumentExit,
        DocumentObject,
        MAP_DOCUMENT_VERSION,
        MapCanvas,
        MapDocument,
        MapDocumentError,
        build_map2d_from_document,
        jagged_edge,
        load_map_document,
        save_map_document,
    )


def __getattr__(name: str) -> Any:
    if name in __all__:
        module = import_module("sonartk.map_builder.map_2d")
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
