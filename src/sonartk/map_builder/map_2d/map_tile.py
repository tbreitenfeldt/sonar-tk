from typing import FrozenSet

from sonartk.util import Direction


class MapTile:
    def __init__(
        self,
        name: str,
        is_passable: bool = True,
        allowed_entry_directions: FrozenSet[Direction] | None = None,
        required_capabilities: FrozenSet[str] = frozenset(),
    ) -> None:
        self.name: str = name
        self.is_passable: bool = is_passable
        self.allowed_entry_directions: FrozenSet[Direction] | None = (
            allowed_entry_directions
        )
        self.required_capabilities: FrozenSet[str] = required_capabilities

    def interact(self) -> None:
        """Interact."""
        pass

    def __str__(self) -> str:
        direction_names = (
            "any"
            if self.allowed_entry_directions is None
            else sorted(
                direction.name for direction in self.allowed_entry_directions
            )
        )
        return (
            f"(name: {self.name}, is_passable: {self.is_passable}, "
            f"allowed_entry_directions: {direction_names}, "
            f"required_capabilities: {sorted(self.required_capabilities)})"
        )
