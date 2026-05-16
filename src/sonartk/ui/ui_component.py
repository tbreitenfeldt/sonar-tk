from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from sonartk.ui.window import Window


class UIComponent(ABC):
    """
    Base class for all UI hierarchy components.

    Provides the contract for accessing the root Window from any level
    in the UI hierarchy (Window → Screen → Element → nested Elements).

    All UI components must have a parent reference (None for root Window)
    and get_window() to enable handler management and other window-level
    operations.
    """

    _parent: Optional["UIComponent"]

    def __init__(self, parent: Optional["UIComponent"] = None) -> None:
        self.parent = parent

    @property
    def parent(self) -> Optional["UIComponent"]:
        """Return this component's parent in the UI hierarchy."""
        return self._parent

    @parent.setter
    def parent(self, value: Optional["UIComponent"]) -> None:
        """
        Set this component's parent with basic hierarchy validation.

        Raises:
            TypeError: If value is not a UIComponent or None
            ValueError: If the assignment would create a circular parent chain
        """
        if value is not None and not isinstance(value, UIComponent):
            raise TypeError("parent must be a UIComponent or None")

        seen_ids: set[int] = {id(self)}
        current = value
        while current is not None:
            current_id = id(current)
            if current_id in seen_ids:
                raise ValueError(
                    "Circular parent chain detected while assigning parent"
                )
            seen_ids.add(current_id)
            current = current.parent

        self._parent = value

    def get_window(self) -> Window:
        """
        Get the root Window for this component.

        Traverses the parent chain until a Window is found.
        Window overrides this to return self.

        Returns:
            The Window at the root of the parent chain

        Raises:
            RuntimeError: If no Window is found in the parent chain
        """
        from sonartk.ui.window import Window

        current = self.parent
        while current is not None:
            if isinstance(current, Window):
                return current
            current = current.parent

        raise RuntimeError(
            f"{self.__class__.__name__} has no Window in parent chain"
        )
