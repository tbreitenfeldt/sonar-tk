from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, Optional, TypeVar

from sonartk.map_builder.map_2d import Map2d, MapTile, load_2d_map
from sonartk.map_builder.map_2d.map_object.character import Character
from sonartk.map_builder.map_2d.parser.map_parser import MapParser
from sonartk.ui.element.grid import Grid
from sonartk.ui.screen.container_screen import ContainerScreen
from sonartk.ui.window import Window
from sonartk.util import Direction

T = TypeVar("T")

GridEventHandler = Callable[[Grid[MapTile], Direction], bool | None]


@dataclass(frozen=True)
class BuiltMapGridGame:
    """Represents a fully wired map + grid game composition.

    Attributes:
        window: Top-level application window.
        screen: Container screen that hosts the grid.
        map2d: Loaded game map with character state.
        grid: Grid view over map tiles.
    """

    window: Window
    screen: ContainerScreen
    map2d: Map2d
    grid: Grid[MapTile]


class MapGridGameBuilder(Generic[T]):
    """Builds a map-driven grid game with minimal setup boilerplate.

    This builder is additive and optional. It composes existing APIs
    (`Window`, `ContainerScreen`, `Grid`, and `load_2d_map`) and still
    returns underlying objects for advanced customization.
    """

    def __init__(
        self,
        caption: str,
        screen_key: str = "main",
        grid_key: str = "grid",
    ) -> None:
        self.window: Window = Window(caption=caption)
        self.screen: ContainerScreen = ContainerScreen(self.window)
        self.screen_key: str = screen_key
        self.grid_key: str = grid_key
        self.grid_label: str = ""
        self.speak_coordinates_on_change: bool = False
        self.speak_value_on_change: bool = False
        self.arrow_key_repeat_interval: float = 0.25
        self._map2d: Optional[Map2d] = None
        self._navigation_handlers: list[GridEventHandler] = []
        self._border_handlers: list[GridEventHandler] = []

    def with_map(
        self,
        map_name: str,
        file_name: str,
        parser: MapParser[T],
        tile_mapper: Callable[[T], MapTile],
        character: Character,
    ) -> "MapGridGameBuilder[T]":
        """Load and attach map data for the grid game."""
        self._map2d = load_2d_map(
            map_name,
            file_name,
            parser,
            tile_mapper,
            character,
        )
        return self

    def with_loaded_map(self, map2d: Map2d) -> "MapGridGameBuilder[T]":
        """Attach an already-loaded map instance."""
        self._map2d = map2d
        return self

    @property
    def map2d(self) -> Map2d:
        """Get the configured map.

        Raises:
            ValueError: If no map has been configured yet.
        """
        if self._map2d is None:
            raise ValueError("No map configured. Call with_map() first.")

        return self._map2d

    def with_grid_options(
        self,
        label: str = "",
        speak_coordinates_on_change: bool = False,
        speak_value_on_change: bool = False,
        arrow_key_repeat_interval: float = 0.25,
    ) -> "MapGridGameBuilder[T]":
        """Customize grid behavior without manual grid construction."""
        self.grid_label = label
        self.speak_coordinates_on_change = speak_coordinates_on_change
        self.speak_value_on_change = speak_value_on_change
        self.arrow_key_repeat_interval = arrow_key_repeat_interval
        return self

    def on_navigation(
        self, handler: GridEventHandler
    ) -> "MapGridGameBuilder[T]":
        """Register an `on_navigation` handler for the built grid."""
        self._navigation_handlers.append(handler)
        return self

    def on_border(self, handler: GridEventHandler) -> "MapGridGameBuilder[T]":
        """Register an `on_border` handler for the built grid."""
        self._border_handlers.append(handler)
        return self

    def build(self) -> BuiltMapGridGame:
        """Create and wire all components.

        Raises:
            ValueError: If no map has been provided.
            RuntimeError: If builder keys already exist in target state machines.
        """
        if self._map2d is None:
            raise ValueError("No map configured. Call with_map() first.")

        if self.window.state_machine.contains(self.screen_key):
            raise RuntimeError(
                f"Window already contains a state with key '{self.screen_key}'."
            )
        if self.screen.state_machine.contains(self.grid_key):
            raise RuntimeError(
                f"Screen already contains a state with key '{self.grid_key}'."
            )

        grid = Grid(
            self.screen,
            label=self.grid_label,
            height=self._map2d.height,
            width=self._map2d.width,
            cells=self._map2d.tile_map,
            cell_class=MapTile,
            property_name="name",
            speak_coordinates_on_change=self.speak_coordinates_on_change,
            speak_value_on_change=self.speak_value_on_change,
            arrow_key_repeat_interval=self.arrow_key_repeat_interval,
        )
        grid.current_coordinates = self._map2d.character.coordinates

        for handler in self._navigation_handlers:
            grid.push_handlers(on_navigation=handler)
        for handler in self._border_handlers:
            grid.push_handlers(on_border=handler)

        self.screen.add(self.grid_key, grid)
        self.window.add(self.screen_key, self.screen)

        return BuiltMapGridGame(
            window=self.window,
            screen=self.screen,
            map2d=self._map2d,
            grid=grid,
        )
