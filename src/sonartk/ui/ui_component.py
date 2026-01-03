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

    parent: Optional["UIComponent"]

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
