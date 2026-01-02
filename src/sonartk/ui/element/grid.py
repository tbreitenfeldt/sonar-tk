from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Optional,
    Self,
    Type,
    TypeAlias,
    TypeVar,
)

from pyglet.window import key

from sonartk.ui.element.element import Element
from sonartk.util import Coordinates, Direction, KeyHandler, speech_manager
from sonartk.util.key_handler import Key

if TYPE_CHECKING:
    from sonartk.ui.screen.screen import Screen


@dataclass
class Cell:
    value: str = ""


T = TypeVar("T")


class Grid(Element[str], Generic[T]):
    def __init__(
        self,
        parent: Element | Screen,
        label: str,
        height: int,
        width: int,
        cells: list[T] = [],
        cell_class: type = Cell,
        property_name: str = "value",
        speak_coordinates_on_change: bool = True,
        speak_value_on_change: bool = True,
        arrow_key_repeat_interval: float = 0.25,
    ) -> None:
        super().__init__(parent=parent, label=label, role="Grid", value=None)

        if height < 0:
            raise ValueError("rows cannot be less than 0")
        if width < 0:
            raise ValueError("columns cannot be less than 0")

        self.height: int = height
        self.width: int = width
        self.cells: list[T] = cells
        self.cell_class: Type[T] = cell_class
        self.property_name: str = property_name
        self.speak_coordinates_on_change: bool = speak_coordinates_on_change
        self.speak_value_on_change: bool = speak_value_on_change
        self._arrow_key_repeat_interval: float = arrow_key_repeat_interval
        self.x: int = 0
        self.y: int = 0

        if not cells:
            self.cells = [self.cell_class() for c in range(width * height)]

        self.push_handlers(on_navigation=self.on_navigation)
        self._bind_keys()

    def _bind_keys(self) -> None:
        self.key_handler.add_key_press(
            self.navigate_up,
            key.UP,
            key_repeat_interval=self.arrow_key_repeat_interval,
        )
        self.key_handler.add_key_press(
            self.navigate_down,
            key.DOWN,
            key_repeat_interval=self.arrow_key_repeat_interval,
        )
        self.key_handler.add_key_press(
            self.navigate_left,
            key.LEFT,
            key_repeat_interval=self.arrow_key_repeat_interval,
        )
        self.key_handler.add_key_press(
            self.navigate_right,
            key.RIGHT,
            key_repeat_interval=self.arrow_key_repeat_interval,
        )

    def navigate_up(self) -> bool:
        if (self.y + 1) < self.height:
            self.dispatch_event("on_navigation", self, Direction.UP)
        else:
            self.dispatch_event("on_border", self, Direction.UP)

        return True

    def navigate_down(self) -> bool:
        if (self.y - 1) >= 0:
            self.dispatch_event("on_navigation", self, Direction.DOWN)
        else:
            self.dispatch_event("on_border", self, Direction.DOWN)

        return True

    def navigate_left(self) -> bool:
        if (self.x - 1) >= 0:
            self.dispatch_event("on_navigation", self, Direction.LEFT)
        else:
            self.dispatch_event("on_border", self, Direction.LEFT)

        return True

    def navigate_right(self) -> bool:
        if (self.x + 1) < self.width:
            self.dispatch_event("on_navigation", self, Direction.RIGHT)
        else:
            self.dispatch_event("on_border", self, Direction.RIGHT)

        return True

    def on_navigation(self, grid: Self, direction: Direction) -> bool:
        if direction == Direction.UP:
            self.y += 1
        elif direction == Direction.DOWN:
            self.y -= 1
        elif direction == Direction.LEFT:
            self.x -= 1
        elif direction == Direction.RIGHT:
            self.x += 1

        msg: str = ""
        if self.speak_value_on_change:
            msg += f"{self.value} "
        if self.speak_coordinates_on_change:
            msg += f"({self.x}, {self.y})"
        if msg:
            speech_manager.output(msg)

        return True

    def get_cell(self, coordinates: Coordinates) -> T:
        x, y = coordinates
        if (x < self.width and x >= 0) and (y < self.height and y >= 0):
            return self.cells[y * self.width + x]

        return None

    def get_next_cell(self, direction: Direction) -> tuple[Coordinates, T]:
        coordinates: Coordinates = (0, 0)
        if direction == Direction.UP:
            coordinates = (self.x, self.y + 1)
            return (coordinates, self.get_cell(coordinates))
        elif direction == Direction.DOWN:
            coordinates = (self.x, self.y - 1)
            return (coordinates, self.get_cell(coordinates))
        elif direction == Direction.LEFT:
            coordinates = (self.x - 1, self.y)
            return (coordinates, self.get_cell(coordinates))
        elif direction == Direction.RIGHT:
            coordinates = (self.x + 1, self.y)
            return (coordinates, self.get_cell(coordinates))

        raise ValueError("Invalid Direction for get_next_cell")

    def add_row(self, row: list[T] = []) -> None:
        new_row: list[T] = row
        if row:
            if len(row) != self.width:
                raise ValueError(
                    "Length of pcell list must be equal to the existing grid width"
                )
        else:
            new_row = [self.cellClass() for c in range(self.width)]

        self.cells.extend(new_row)
        self.height = len(self.cells)

    # override
    def setup(  # type: ignore[override]
        self,
        change_state: Callable[[str, Any], None],
        interrupt_speech: bool = False,
    ) -> bool:
        super().setup(change_state, interrupt_speech)
        self.dispatch_event("on_change", self)
        return True

    # override
    def reset(self) -> None:
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.cells = []

    @property
    def arrow_key_repeat_interval(self) -> float:
        return self._arrow_key_repeat_interval

    @arrow_key_repeat_interval.setter
    def arrow_key_repeat_interval(
        self, arrow_key_repeat_interval: float
    ) -> None:
        self._arrow_key_repeat_interval = arrow_key_repeat_interval
        self.key_handler.update_repeat_interval_for_key(
            key=Key(key.UP), key_repeat_interval=arrow_key_repeat_interval
        )
        self.key_handler.update_repeat_interval_for_key(
            key=Key(key.DOWN), key_repeat_interval=arrow_key_repeat_interval
        )
        self.key_handler.update_repeat_interval_for_key(
            key=Key(key.LEFT), key_repeat_interval=arrow_key_repeat_interval
        )
        self.key_handler.update_repeat_interval_for_key(
            key=Key(key.RIGHT), key_repeat_interval=arrow_key_repeat_interval
        )

    @property
    def current_cell(self) -> T:
        return self.cells[self.y * self.width + self.x]

    @property
    def current_coordinates(self) -> tuple[int, int]:
        return (self.x, self.y)

    @current_coordinates.setter
    def current_coordinates(self, coordinates: tuple[int, int]) -> None:
        x, y = coordinates
        if x >= self.width or x < 0:
            raise ValueError(f"x is out of bounds. x: {x} (0 - {self.width})")
        if y >= self.height or y < 0:
            raise ValueError("y is out of bounds. y: {y} (0 - {self.height})")

        self.x = x
        self.y = y

    # override
    @property
    def value(self) -> Optional[str]:
        return str(getattr(self.current_cell, self.property_name))

    # override
    @value.setter
    def value(self, value: str) -> None:
        setattr(self.current_cell, self.class_property, value)


Grid.register_event_type("on_border")
Grid.register_event_type("on_navigation")
