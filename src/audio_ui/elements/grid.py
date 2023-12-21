from __future__ import annotations

from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Optional,
    Self,
    Type,
    TypeVar,
)

from pyglet.window import key

from audio_ui.elements.element import Element
from audio_ui.utils import KeyHandler, speech_manager

if TYPE_CHECKING:
    from audio_ui.screens.screen import Screen


@dataclass
class Cell:
    value: str = ""


T = TypeVar("T", bound=Cell)


class Grid(Element[str], Generic[T]):
    def __init__(
        self,
        parent: Element | Screen,
        label: str,
        rows: int,
        columns: int,
        cell_class: Type[T],
    ) -> None:
        super().__init__(parent=parent, label=label, role="Grid", value=None)

        if rows < 0:
            raise ValueError("rows cannot be less than 0")
        if columns < 0:
            raise ValueError("columns cannot be less than 0")

        self.rows: int = rows
        self.columns: int = columns
        self.cell_class: Type[T] = cell_class
        self.x: int = 0
        self.y: int = 0
        self.cells: list[list[Cell]] = []

        self.populate()
        self.push_handlers(on_change=self.on_change)
        self._bind_keys()

    def _bind_keys(self) -> None:
        self.key_handler.add_key_press(self.navigate_up, key.UP)
        self.key_handler.add_key_press(self.navigate_down, key.DOWN)
        self.key_handler.add_key_press(self.navigate_left, key.LEFT)
        self.key_handler.add_key_press(self.navigate_right, key.RIGHT)

    def navigate_up(self) -> bool:
        if (self.y + 1) < self.columns:
            self.y += 1
            self.dispatch_event("on_navigate_up", self)
        else:
            self.dispatch_event("on_border", self)

        self.dispatch_event("on_change", self)
        return True

    def navigate_down(self) -> bool:
        if (self.y - 1) >= 0:
            self.y -= 1
            self.dispatch_event("on_navigate_down", self)
        else:
            self.dispatch_event("on_border", self)

        self.dispatch_event("on_change", self)
        return True

    def navigate_left(self) -> bool:
        if (self.x - 1) >= 0:
            self.x -= 1
            self.dispatch_event("on_navigate_left", self)
        else:
            self.dispatch_event("on_border", self)

        self.dispatch_event("on_change", self)
        return True

    def navigate_right(self) -> bool:
        if (self.x + 1) < self.rows:
            self.x += 1
            self.dispatch_event("on_navigate_right", self)
        else:
            self.dispatch_event("on_border", self)

        self.dispatch_event("on_change", self)
        return True

    def populate(self) -> None:
        self.cells = [
            [self.cell_class() for c in range(self.columns)]
            for r in range(self.rows)
        ]

    def add_row(self, index: int = 0) -> None:
        self.cells.insert(
            index, [self.cellClass() for c in range(self.columns)]
        )
        self.rows = len(self.cells)

    def add_column(self, index: int = 0) -> None:
        for row in self.cells:
            row.insert(index, self.cellClass())
        self.columns = len(self.cells[0])

    def on_change(self, grid: Self) -> bool:
        msg: str = f"{self.active.value} {self.x}, {self.y}"
        speech_manager.output(msg)
        return True

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
        for r in range(self.rows):
            self.add_row()

    @property
    def active(self) -> Cell:
        return self.cells[self.y][self.x]

    @property
    def coordinates(self) -> tuple[int, int]:
        return (self.x, self.y)

    # override
    @property
    def value(self) -> Optional[str]:
        return self.active.value

    # override
    @value.setter
    def value(self, value: str) -> None:
        self.active.value = value


Grid.register_event_type("on_navigate_up")
Grid.register_event_type("on_navigate_down")
Grid.register_event_type("on_navigate_left")
Grid.register_event_type("on_navigate_right")
Grid.register_event_type("on_border")
Grid.register_event_type("on_change")
