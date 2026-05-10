from typing import Protocol, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from sonartk.util.state import State


class FocusableContainer(Protocol):
    """
    Protocol for UI components that contain focusable child elements.

    Components implementing this protocol maintain a reference to their
    currently active/focused child element, allowing the UI to drill down
    from Window → Screen → Element → nested Element to find the leaf
    element with focus for accessibility announcements.
    """

    @property
    def active_element(self) -> Optional["State"]:
        """
        Get the currently active/focused element within this container.

        Returns:
            The State that currently has focus within this container,
            or None if the container is empty or has no active element.
        """
        ...  # pragma: no cover
