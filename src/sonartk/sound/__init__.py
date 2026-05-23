from importlib import import_module
from typing import Any

__all__ = ["sound_manager"]


def __getattr__(name: str) -> Any:
    if name == "sound_manager":
        return import_module("sonartk.sound.sound_manager")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
