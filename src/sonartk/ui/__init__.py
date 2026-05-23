from importlib import import_module
from typing import TYPE_CHECKING, Any

__all__ = ["UIComponent", "FocusableContainer", "Window"]

if TYPE_CHECKING:
    from sonartk.ui.focusable_container import FocusableContainer
    from sonartk.ui.ui_component import UIComponent
    from sonartk.ui.window import Window


def __getattr__(name: str) -> Any:
    if name == "UIComponent":
        module = import_module("sonartk.ui.ui_component")
        return getattr(module, name)
    if name == "FocusableContainer":
        module = import_module("sonartk.ui.focusable_container")
        return getattr(module, name)
    if name == "Window":
        module = import_module("sonartk.ui.window")
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
