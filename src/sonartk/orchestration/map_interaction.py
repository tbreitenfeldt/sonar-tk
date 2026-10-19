from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Optional, Protocol, Sequence

from pyglet.window import key

from sonartk.orchestration.paged_text_state import PagedTextState
from sonartk.orchestration.state_flow import WindowStateFlow
from sonartk.ui.window import Window
from sonartk.util import Coordinates, Direction

DEFAULT_INTERACT_KEYS: tuple[int, ...] = (key.RETURN, key.ENTER, key.SPACE)


_STEP: dict[Direction, Coordinates] = {
    Direction.UP: (0, 1),
    Direction.DIAGONAL_UPPER_RIGHT: (1, 1),
    Direction.RIGHT: (1, 0),
    Direction.DIAGONAL_LOWER_RIGHT: (1, -1),
    Direction.DOWN: (0, -1),
    Direction.DIAGONAL_LOWER_LEFT: (-1, -1),
    Direction.LEFT: (-1, 0),
    Direction.DIAGONAL_UPPER_LEFT: (-1, 1),
}


class _GridLike(Protocol):
    current_coordinates: Coordinates
    key_handler: Any


@dataclass(frozen=True)
class InteractableObject:
    """An object the player can examine, and what is said about it."""

    name: str
    coordinates: Coordinates
    pages: tuple[str, ...]
    footprint: tuple[Coordinates, ...] = ()


def tile_distance(first: Coordinates, second: Coordinates) -> int:
    """Return the Chebyshev distance, so diagonal neighbors are 1 away."""
    return max(abs(first[0] - second[0]), abs(first[1] - second[1]))


class MapInteractionController:
    """Lets the player examine nearby objects from a map grid.

    Each object with a description becomes a ``PagedTextState`` registered
    on the window. Pressing an interact key on the grid transitions to the
    state of the nearest object within reach; after the last page the
    state returns to ``return_state_key``, the map. Objects without pages
    are ignored.

    Args:
        window: Window that owns the states.
        grid: Map grid; supplies the player position and key handling.
        return_state_key: State to return to after a description.
        objects: Objects that may be examined.
        keys: Keys that examine an object and also page through the text.
        reach_tiles: How far away an object can be examined.
        on_page_change: Called as ``(state, page_index)`` when a
            description advances, for example to play a paging sound.
        facing: Returns the direction the player faces. When given, an
            object can only be examined from a tile it is in line with,
            within ``reach_tiles`` in that direction. Without it any object
            within ``reach_tiles`` in any direction can be examined.
    """

    def __init__(
        self,
        *,
        window: Window,
        grid: _GridLike,
        return_state_key: str,
        objects: Iterable[InteractableObject],
        keys: Sequence[int] = DEFAULT_INTERACT_KEYS,
        reach_tiles: int = 1,
        on_page_change: Optional[Callable[[PagedTextState, int], None]] = None,
        facing: Optional[Callable[[], Optional[Direction]]] = None,
    ) -> None:
        self.facing = facing
        self.window = window
        self.grid = grid
        self.reach_tiles = reach_tiles
        self.state_keys: dict[str, str] = {}
        self._coordinates: dict[str, tuple[Coordinates, ...]] = {}

        states: dict[str, PagedTextState] = {}
        for item in objects:
            if not item.pages:
                continue
            state_key = f"{return_state_key}:describe:{item.name}"
            state = PagedTextState(
                window=window,
                pages=item.pages,
                next_state_key=return_state_key,
                continue_keys=keys,
            )
            if on_page_change is not None:
                state.push_handlers(on_page_change=on_page_change)
            states[state_key] = state
            self.state_keys[item.name] = state_key
            self._coordinates[item.name] = item.footprint or (
                item.coordinates,
            )
        if states:
            WindowStateFlow(window).add_many(states)
        for binding in keys:
            grid.key_handler.add_key_press(self.interact, binding)

    def release(self) -> None:
        """Remove the description states this controller registered."""
        for state_key in self.state_keys.values():
            self.window.remove(state_key)
        self.state_keys.clear()
        self._coordinates.clear()

    def nearest(self) -> Optional[str]:
        """Return the name of the closest object within reach, if any."""
        position = self.grid.current_coordinates
        reachable = []
        for name, tiles in self._coordinates.items():
            distance = self._distance(position, tiles)
            if distance is not None and distance <= self.reach_tiles:
                reachable.append((distance, name))
        return min(reachable)[1] if reachable else None

    def _distance(
        self, position: Coordinates, tiles: tuple[Coordinates, ...]
    ) -> Optional[int]:
        """Steps to the object, or None when the player is not facing it."""
        if self.facing is None:
            return min(tile_distance(position, tile) for tile in tiles)
        direction = self.facing()
        if direction not in _STEP:
            return None
        dx, dy = _STEP[direction]
        for steps in range(1, self.reach_tiles + 1):
            if (position[0] + dx * steps, position[1] + dy * steps) in tiles:
                return steps
        return None

    def interact(self) -> bool:
        """Describe the nearest object in reach; always handles the key."""
        name = self.nearest()
        if name is not None:
            self.window.transition_to(self.state_keys[name])
        return True
