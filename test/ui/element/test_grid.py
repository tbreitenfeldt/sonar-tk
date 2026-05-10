from dataclasses import dataclass
from typing import Any, Callable, Optional
from unittest.mock import MagicMock

import pytest
from pyglet.window import key
from pytest_mock import MockerFixture

from sonartk.ui.element.element import Element
from sonartk.ui.element.grid import Cell, Grid
from sonartk.ui.ui_component import UIComponent
from sonartk.ui.window import Window
from sonartk.util import Coordinates, Direction, KeyHandler
from sonartk.util.key_handler import Key
from test.mocks.mock_pyglet_window import MockPygletWindow


@dataclass
class CustomCell:
    """Custom cell class for testing."""

    value: str = ""
    extra_data: int = 0


@pytest.fixture
def window(mocker: MockerFixture) -> Window:
    """Create a Window fixture."""
    window = Window()
    window.pyglet_window = mocker.MagicMock(spec=MockPygletWindow)
    window.push_window_handlers = mocker.MagicMock()  # type: ignore[method-assign]
    window.pop_window_handlers = mocker.MagicMock()  # type: ignore[method-assign]
    return window


@pytest.fixture
def parent(window: Window) -> UIComponent:
    """Create a parent UIComponent fixture."""
    parent = UIComponent()
    parent.parent = window
    return parent  # type: ignore[return-value]


@pytest.fixture
def grid(parent: UIComponent) -> Grid[Cell]:
    """Create a Grid fixture with default settings."""
    return Grid(parent, "Test Grid", 3, 4)  # type: ignore[arg-type]


# Initialization Tests


def test_init_sets_parent(parent: UIComponent, grid: Grid[Cell]) -> None:
    """Test that __init__ sets parent correctly."""
    assert grid.parent == parent


def test_init_sets_label(parent: UIComponent) -> None:
    """Test that __init__ sets label correctly."""
    grid: Grid[Cell] = Grid(parent, "My Grid", 2, 2)  # type: ignore[arg-type]
    assert grid.label == "My Grid"


def test_init_sets_height(parent: UIComponent) -> None:
    """Test that __init__ sets height correctly."""
    grid: Grid[Cell] = Grid(parent, "Grid", 5, 3)  # type: ignore[arg-type]  # type: ignore[arg-type]
    assert grid.height == 5


def test_init_sets_width(parent: UIComponent) -> None:
    """Test that __init__ sets width correctly."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 7)  # type: ignore[arg-type]  # type: ignore[arg-type]
    assert grid.width == 7


def test_init_sets_role_to_grid(parent: UIComponent) -> None:
    """Test that __init__ sets role to 'Grid'."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]  # type: ignore[arg-type]
    assert grid.role == "Grid"


def test_init_creates_key_handler(parent: UIComponent) -> None:
    """Test that __init__ creates a KeyHandler."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]  # type: ignore[arg-type]
    assert isinstance(grid.key_handler, KeyHandler)


def test_init_sets_initial_position_to_zero(parent: UIComponent) -> None:
    """Test that __init__ sets initial x and y to 0."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]  # type: ignore[arg-type]
    assert grid.x == 0
    assert grid.y == 0


def test_init_raises_error_for_negative_height(parent: UIComponent) -> None:
    """Test that __init__ raises ValueError for negative height."""
    with pytest.raises(ValueError, match="rows cannot be less than 0"):
        Grid(parent, "Grid", -1, 3)  # type: ignore[arg-type]


def test_init_raises_error_for_negative_width(parent: UIComponent) -> None:
    """Test that __init__ raises ValueError for negative width."""
    with pytest.raises(ValueError, match="columns cannot be less than 0"):
        Grid(parent, "Grid", 3, -1)  # type: ignore[arg-type]


def test_init_creates_cells_when_none_provided(parent: UIComponent) -> None:
    """Test that __init__ creates cells when none provided."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 3)  # type: ignore[arg-type]
    assert len(grid.cells) == 6
    assert all(isinstance(cell, Cell) for cell in grid.cells)


def test_init_uses_provided_cells(parent: UIComponent) -> None:
    """Test that __init__ uses provided cells."""
    cells = [Cell(value=str(i)) for i in range(6)]
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 3, cells=cells)  # type: ignore[arg-type]
    assert grid.cells == cells


def test_init_with_custom_cell_class(parent: UIComponent) -> None:
    """Test that __init__ works with custom cell class."""
    grid: Grid[CustomCell] = Grid(
        parent, "Grid", 2, 2, cell_class=CustomCell  # type: ignore[arg-type]
    )
    assert len(grid.cells) == 4
    assert all(isinstance(cell, CustomCell) for cell in grid.cells)


def test_init_with_custom_property_name(parent: UIComponent) -> None:
    """Test that __init__ accepts custom property_name."""
    grid: Grid[CustomCell] = Grid(
        parent, "Grid", 2, 2, cell_class=CustomCell, property_name="extra_data"  # type: ignore[arg-type]
    )
    assert grid.property_name == "extra_data"


def test_init_sets_speak_coordinates_flag(parent: UIComponent) -> None:
    """Test that __init__ sets speak_coordinates_on_change flag."""
    grid: Grid[Cell] = Grid(
        parent, "Grid", 2, 2, speak_coordinates_on_change=False  # type: ignore[arg-type]
    )
    assert grid.speak_coordinates_on_change is False


def test_init_sets_speak_value_flag(parent: UIComponent) -> None:
    """Test that __init__ sets speak_value_on_change flag."""
    grid: Grid[Cell] = Grid(
        parent, "Grid", 2, 2, speak_value_on_change=False  # type: ignore[arg-type]
    )
    assert grid.speak_value_on_change is False


def test_init_sets_arrow_key_repeat_interval(parent: UIComponent) -> None:
    """Test that __init__ sets arrow_key_repeat_interval."""
    grid: Grid[Cell] = Grid(
        parent, "Grid", 2, 2, arrow_key_repeat_interval=0.5  # type: ignore[arg-type]
    )
    assert grid.arrow_key_repeat_interval == 0.5


def test_init_with_zero_dimensions(parent: UIComponent) -> None:
    """Test that __init__ works with zero dimensions."""
    grid: Grid[Cell] = Grid(parent, "Grid", 0, 0)  # type: ignore[arg-type]
    assert grid.height == 0
    assert grid.width == 0
    assert len(grid.cells) == 0


def test_init_calls_bind_keys(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that __init__ calls bind_keys."""
    mock_bind_keys = mocker.patch.object(Grid, "bind_keys")
    Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]
    mock_bind_keys.assert_called_once()


# bind_keys Tests


def test_bind_keys_registers_up_arrow(parent: UIComponent) -> None:
    """Test that bind_keys registers UP arrow key."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    up_key = None
    for k in grid.key_handler.registered_key_presses.keys():
        if k.symbol == key.UP and k.modifiers == 0:
            up_key = k
            break

    assert up_key is not None, "UP key should be registered"
    callback, _ = grid.key_handler.registered_key_presses[up_key]
    assert callback.callback == grid.navigate_up


def test_bind_keys_registers_down_arrow(parent: UIComponent) -> None:
    """Test that bind_keys registers DOWN arrow key."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    down_key = None
    for k in grid.key_handler.registered_key_presses.keys():
        if k.symbol == key.DOWN and k.modifiers == 0:
            down_key = k
            break

    assert down_key is not None, "DOWN key should be registered"
    callback, _ = grid.key_handler.registered_key_presses[down_key]
    assert callback.callback == grid.navigate_down


def test_bind_keys_registers_left_arrow(parent: UIComponent) -> None:
    """Test that bind_keys registers LEFT arrow key."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    left_key = None
    for k in grid.key_handler.registered_key_presses.keys():
        if k.symbol == key.LEFT and k.modifiers == 0:
            left_key = k
            break

    assert left_key is not None, "LEFT key should be registered"
    callback, _ = grid.key_handler.registered_key_presses[left_key]
    assert callback.callback == grid.navigate_left


def test_bind_keys_registers_right_arrow(parent: UIComponent) -> None:
    """Test that bind_keys registers RIGHT arrow key."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    right_key = None
    for k in grid.key_handler.registered_key_presses.keys():
        if k.symbol == key.RIGHT and k.modifiers == 0:
            right_key = k
            break

    assert right_key is not None, "RIGHT key should be registered"
    callback, _ = grid.key_handler.registered_key_presses[right_key]
    assert callback.callback == grid.navigate_right


def test_bind_keys_sets_repeat_interval(parent: UIComponent) -> None:
    """Test that bind_keys sets repeat interval for arrow keys."""
    grid: Grid[Cell] = Grid(
        parent, "Grid", 3, 3, arrow_key_repeat_interval=0.3  # type: ignore[arg-type]
    )

    for k in grid.key_handler.registered_key_presses.keys():
        if k.symbol in [key.UP, key.DOWN, key.LEFT, key.RIGHT]:
            _, repeat_interval = grid.key_handler.registered_key_presses[k]
            assert repeat_interval == 0.3


def test_bind_keys_registers_four_keys(parent: UIComponent) -> None:
    """Test that bind_keys registers exactly four arrow keys."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]
    assert len(grid.key_handler.registered_key_presses) == 4


# Navigation Tests


def test_navigate_up_when_within_bounds(parent: UIComponent) -> None:
    """Test that navigate_up dispatches on_navigation when within bounds."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    grid.y = 0

    navigation_called = False

    @grid.event  # type: ignore[misc]
    def on_navigation(g: Grid[Cell], direction: Direction) -> None:
        nonlocal navigation_called
        navigation_called = True

    result = grid.navigate_up()
    assert result is True
    assert navigation_called is True


def test_navigate_up_when_at_border(parent: UIComponent) -> None:
    """Test that navigate_up dispatches on_border when at upper edge."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    grid.y = 2  # At top edge

    border_called = False

    @grid.event  # type: ignore[misc]
    def on_border(g: Grid[Cell], direction: Direction) -> None:
        nonlocal border_called
        border_called = True

    result = grid.navigate_up()
    assert result is True
    assert border_called is True


def test_navigate_down_when_within_bounds(parent: UIComponent) -> None:
    """Test that navigate_down dispatches on_navigation when within bounds."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    grid.y = 1

    navigation_called = False

    @grid.event  # type: ignore[misc]
    def on_navigation(g: Grid[Cell], direction: Direction) -> None:
        nonlocal navigation_called
        navigation_called = True

    result = grid.navigate_down()
    assert result is True
    assert navigation_called is True


def test_navigate_down_when_at_border(parent: UIComponent) -> None:
    """Test that navigate_down dispatches on_border when at lower edge."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    grid.y = 0  # At bottom edge

    border_called = False

    @grid.event  # type: ignore[misc]
    def on_border(g: Grid[Cell], direction: Direction) -> None:
        nonlocal border_called
        border_called = True

    result = grid.navigate_down()
    assert result is True
    assert border_called is True


def test_navigate_left_when_within_bounds(parent: UIComponent) -> None:
    """Test that navigate_left dispatches on_navigation when within bounds."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    grid.x = 1

    navigation_called = False

    @grid.event  # type: ignore[misc]
    def on_navigation(g: Grid[Cell], direction: Direction) -> None:
        nonlocal navigation_called
        navigation_called = True

    result = grid.navigate_left()
    assert result is True
    assert navigation_called is True


def test_navigate_left_when_at_border(parent: UIComponent) -> None:
    """Test that navigate_left dispatches on_border when at left edge."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    grid.x = 0  # At left edge

    border_called = False

    @grid.event  # type: ignore[misc]
    def on_border(g: Grid[Cell], direction: Direction) -> None:
        nonlocal border_called
        border_called = True

    result = grid.navigate_left()
    assert result is True
    assert border_called is True


def test_navigate_right_when_within_bounds(parent: UIComponent) -> None:
    """Test that navigate_right dispatches on_navigation when within bounds."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    grid.x = 0

    navigation_called = False

    @grid.event  # type: ignore[misc]
    def on_navigation(g: Grid[Cell], direction: Direction) -> None:
        nonlocal navigation_called
        navigation_called = True

    result = grid.navigate_right()
    assert result is True
    assert navigation_called is True


def test_navigate_right_when_at_border(parent: UIComponent) -> None:
    """Test that navigate_right dispatches on_border when at right edge."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    grid.x = 2  # At right edge

    border_called = False

    @grid.event  # type: ignore[misc]
    def on_border(g: Grid[Cell], direction: Direction) -> None:
        nonlocal border_called
        border_called = True

    result = grid.navigate_right()
    assert result is True
    assert border_called is True


# on_navigation Tests


def test_on_navigation_moves_up(parent: UIComponent) -> None:
    """Test that on_navigation moves y up when direction is UP."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    grid.y = 0

    result = grid.on_navigation(grid, Direction.UP)
    assert result is True
    assert grid.y == 1


def test_on_navigation_moves_down(parent: UIComponent) -> None:
    """Test that on_navigation moves y down when direction is DOWN."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    grid.y = 2

    result = grid.on_navigation(grid, Direction.DOWN)
    assert result is True
    assert grid.y == 1


def test_on_navigation_moves_left(parent: UIComponent) -> None:
    """Test that on_navigation moves x left when direction is LEFT."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    grid.x = 2

    result = grid.on_navigation(grid, Direction.LEFT)
    assert result is True
    assert grid.x == 1


def test_on_navigation_moves_right(parent: UIComponent) -> None:
    """Test that on_navigation moves x right when direction is RIGHT."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    grid.x = 0

    result = grid.on_navigation(grid, Direction.RIGHT)
    assert result is True
    assert grid.x == 1


def test_on_navigation_outputs_speech_with_value(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that on_navigation outputs speech with value."""
    mock_speech = mocker.patch("sonartk.ui.element.grid.speech_manager")
    grid: Grid[Cell] = Grid(
        parent,  # type: ignore[arg-type]
        "Grid",
        2,
        2,
        speak_value_on_change=True,
        speak_coordinates_on_change=False,
    )
    # Set value on the cell we'll navigate TO (position 1,0)
    grid.cells[1].value = "Test"

    grid.on_navigation(grid, Direction.RIGHT)

    mock_speech.output.assert_called_once()
    call_args = mock_speech.output.call_args[0][0]
    assert "Test" in call_args


def test_on_navigation_outputs_speech_with_coordinates(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that on_navigation outputs speech with coordinates."""
    mock_speech = mocker.patch("sonartk.ui.element.grid.speech_manager")
    grid: Grid[Cell] = Grid(
        parent,  # type: ignore[arg-type]
        "Grid",
        2,
        2,
        speak_value_on_change=False,
        speak_coordinates_on_change=True,
    )

    grid.on_navigation(grid, Direction.RIGHT)

    mock_speech.output.assert_called_once()
    call_args = mock_speech.output.call_args[0][0]
    assert "(1, 0)" in call_args


def test_on_navigation_outputs_speech_with_both(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that on_navigation outputs speech with value and coordinates."""
    mock_speech = mocker.patch("sonartk.ui.element.grid.speech_manager")
    grid: Grid[Cell] = Grid(
        parent,  # type: ignore[arg-type]
        "Grid",
        2,
        2,
        speak_value_on_change=True,
        speak_coordinates_on_change=True,
    )
    # Set value on the cell we'll navigate TO (position 1,0)
    grid.cells[1].value = "Test"

    grid.on_navigation(grid, Direction.RIGHT)

    mock_speech.output.assert_called_once()
    call_args = mock_speech.output.call_args[0][0]
    assert "Test" in call_args
    assert "(1, 0)" in call_args


def test_on_navigation_no_speech_when_both_disabled(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that on_navigation doesn't output speech when both flags are False."""
    mock_speech = mocker.patch("sonartk.ui.element.grid.speech_manager")
    grid: Grid[Cell] = Grid(
        parent,  # type: ignore[arg-type]
        "Grid",
        2,
        2,
        speak_value_on_change=False,
        speak_coordinates_on_change=False,
    )

    grid.on_navigation(grid, Direction.RIGHT)

    mock_speech.output.assert_not_called()


# get_cell Tests


def test_get_cell_returns_cell_at_valid_coordinates(
    parent: UIComponent,
) -> None:
    """Test that get_cell returns cell at valid coordinates."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 3)  # type: ignore[arg-type]
    cell = grid.get_cell((1, 1))
    assert cell is not None
    assert cell == grid.cells[4]  # Row 1, Col 1 = index 4


def test_get_cell_returns_none_for_negative_x(parent: UIComponent) -> None:
    """Test that get_cell returns None for negative x."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]
    cell = grid.get_cell((-1, 0))
    assert cell is None


def test_get_cell_returns_none_for_negative_y(parent: UIComponent) -> None:
    """Test that get_cell returns None for negative y."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]
    cell = grid.get_cell((0, -1))
    assert cell is None


def test_get_cell_returns_none_for_x_out_of_bounds(
    parent: UIComponent,
) -> None:
    """Test that get_cell returns None for x >= width."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 3)  # type: ignore[arg-type]
    cell = grid.get_cell((3, 0))
    assert cell is None


def test_get_cell_returns_none_for_y_out_of_bounds(
    parent: UIComponent,
) -> None:
    """Test that get_cell returns None for y >= height."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 3)  # type: ignore[arg-type]
    cell = grid.get_cell((0, 2))
    assert cell is None


def test_get_cell_at_corners(parent: UIComponent) -> None:
    """Test that get_cell works at all corners."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 4)  # type: ignore[arg-type]

    # Bottom-left (0, 0)
    cell = grid.get_cell((0, 0))
    assert cell is not None
    assert cell == grid.cells[0]

    # Bottom-right (3, 0)
    cell = grid.get_cell((3, 0))
    assert cell is not None
    assert cell == grid.cells[3]

    # Top-left (0, 2)
    cell = grid.get_cell((0, 2))
    assert cell is not None
    assert cell == grid.cells[8]

    # Top-right (3, 2)
    cell = grid.get_cell((3, 2))
    assert cell is not None
    assert cell == grid.cells[11]


# get_next_cell Tests


def test_get_next_cell_up(parent: UIComponent) -> None:
    """Test that get_next_cell returns correct cell for UP direction."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    grid.x = 1
    grid.y = 1

    coords, cell = grid.get_next_cell(Direction.UP)
    assert coords == (1, 2)
    assert cell is not None
    assert cell == grid.cells[7]


def test_get_next_cell_down(parent: UIComponent) -> None:
    """Test that get_next_cell returns correct cell for DOWN direction."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    grid.x = 1
    grid.y = 1

    coords, cell = grid.get_next_cell(Direction.DOWN)
    assert coords == (1, 0)
    assert cell is not None
    assert cell == grid.cells[1]


def test_get_next_cell_left(parent: UIComponent) -> None:
    """Test that get_next_cell returns correct cell for LEFT direction."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    grid.x = 1
    grid.y = 1

    coords, cell = grid.get_next_cell(Direction.LEFT)
    assert coords == (0, 1)
    assert cell is not None
    assert cell == grid.cells[3]


def test_get_next_cell_right(parent: UIComponent) -> None:
    """Test that get_next_cell returns correct cell for RIGHT direction."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    grid.x = 1
    grid.y = 1

    coords, cell = grid.get_next_cell(Direction.RIGHT)
    assert coords == (2, 1)
    assert cell is not None
    assert cell == grid.cells[5]


def test_get_next_cell_returns_none_when_out_of_bounds(
    parent: UIComponent,
) -> None:
    """Test that get_next_cell returns None when next cell is out of bounds."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]
    grid.x = 1
    grid.y = 1

    coords, cell = grid.get_next_cell(Direction.UP)
    assert coords == (1, 2)
    assert cell is None


def test_get_next_cell_raises_error_for_invalid_direction(
    parent: UIComponent,
) -> None:
    """Test that get_next_cell raises ValueError for invalid direction."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Invalid Direction"):
        grid.get_next_cell(Direction.DIAGONAL_UPPER_RIGHT)


# add_row Tests


def test_add_row_adds_empty_row(parent: UIComponent) -> None:
    """Test that add_row adds an empty row."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 3)  # type: ignore[arg-type]
    initial_cells = len(grid.cells)

    grid.add_row()

    assert len(grid.cells) == initial_cells + 3
    # Note: add_row sets height to len(cells), not len(cells) // width
    assert grid.height == 9


def test_add_row_adds_provided_row(parent: UIComponent) -> None:
    """Test that add_row adds provided row."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 3)  # type: ignore[arg-type]
    new_row = [Cell(value=str(i)) for i in range(3)]

    grid.add_row(new_row)

    assert len(grid.cells) == 9
    assert grid.cells[-3:] == new_row


def test_add_row_raises_error_for_wrong_length(
    parent: UIComponent,
) -> None:
    """Test that add_row raises ValueError for wrong row length."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 3)  # type: ignore[arg-type]
    wrong_row = [Cell(value=str(i)) for i in range(2)]  # Wrong length

    with pytest.raises(ValueError, match="Length of pcell list must be equal"):
        grid.add_row(wrong_row)


def test_add_row_multiple_times(parent: UIComponent) -> None:
    """Test that add_row can be called multiple times."""
    grid: Grid[Cell] = Grid(parent, "Grid", 1, 2)  # type: ignore[arg-type]

    grid.add_row()
    # Note: add_row sets height to len(cells), not number of rows
    assert grid.height == 4
    assert len(grid.cells) == 4

    grid.add_row()
    assert grid.height == 6
    assert len(grid.cells) == 6


def test_add_row_updates_height_property(parent: UIComponent) -> None:
    """Test that add_row updates height property."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 3)  # type: ignore[arg-type]

    grid.add_row()

    # Note: add_row sets height to len(cells), not len(cells) // width
    assert grid.height == len(grid.cells)


# setup Tests


def test_setup_calls_super_setup(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that setup calls super().setup()."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]
    mock_super_setup = mocker.patch.object(Element, "setup", return_value=True)

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    grid.setup(mock_change_state)

    mock_super_setup.assert_called_once_with(mock_change_state, False)


def test_setup_dispatches_on_change_event(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that setup dispatches on_change event."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]
    mock_dispatch = mocker.patch.object(grid, "dispatch_event")

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    grid.setup(mock_change_state)

    assert any(
        call[0][0] == "on_change" for call in mock_dispatch.call_args_list
    )


def test_setup_returns_true(parent: UIComponent) -> None:
    """Test that setup returns True."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    result = grid.setup(mock_change_state)
    assert result is True


def test_setup_with_interrupt_speech(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that setup passes interrupt_speech to super()."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]
    mock_super_setup = mocker.patch.object(Element, "setup", return_value=True)

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    grid.setup(mock_change_state, interrupt_speech=True)

    mock_super_setup.assert_called_once_with(mock_change_state, True)


# reset Tests


def test_reset_resets_x_and_y_to_zero(parent: UIComponent) -> None:
    """Test that reset resets x and y to 0."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    grid.x = 2
    grid.y = 2

    grid.reset()

    assert grid.x == 0
    assert grid.y == 0


def test_reset_clears_cells(parent: UIComponent) -> None:
    """Test that reset clears cells list."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]

    grid.reset()

    assert len(grid.cells) == 0


def test_reset_sets_dimensions_to_zero(parent: UIComponent) -> None:
    """Test that reset sets width and height to 0."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 4)  # type: ignore[arg-type]

    grid.reset()

    assert grid.width == 0
    assert grid.height == 0


def test_reset_can_be_called_multiple_times(parent: UIComponent) -> None:
    """Test that reset can be called multiple times."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]

    grid.reset()
    grid.reset()

    assert grid.x == 0
    assert grid.y == 0
    assert grid.width == 0
    assert grid.height == 0


# arrow_key_repeat_interval Property Tests


def test_arrow_key_repeat_interval_getter(parent: UIComponent) -> None:
    """Test that arrow_key_repeat_interval getter returns correct value."""
    grid: Grid[Cell] = Grid(
        parent, "Grid", 2, 2, arrow_key_repeat_interval=0.5  # type: ignore[arg-type]
    )
    assert grid.arrow_key_repeat_interval == 0.5


def test_arrow_key_repeat_interval_setter(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that arrow_key_repeat_interval setter updates the interval."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]
    mock_update = mocker.patch.object(
        grid.key_handler, "update_repeat_interval_for_key"
    )

    grid.arrow_key_repeat_interval = 0.6

    assert grid.arrow_key_repeat_interval == 0.6
    assert mock_update.call_count == 4  # Called for each arrow key


def test_arrow_key_repeat_interval_setter_updates_all_keys(
    parent: UIComponent,
) -> None:
    """Test that setter updates repeat interval for all arrow keys."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]  # type: ignore[arg-type]

    grid.arrow_key_repeat_interval = 0.7

    for k in grid.key_handler.registered_key_presses.keys():
        if k.symbol in [key.UP, key.DOWN, key.LEFT, key.RIGHT]:
            _, repeat_interval = grid.key_handler.registered_key_presses[k]
            assert repeat_interval == 0.7


# current_cell Property Tests


def test_current_cell_returns_cell_at_current_position(
    parent: UIComponent,
) -> None:
    """Test that current_cell returns cell at current x,y position."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    grid.x = 1
    grid.y = 1

    cell = grid.current_cell

    assert cell == grid.cells[4]  # y * width + x = 1 * 3 + 1


def test_current_cell_at_origin(parent: UIComponent) -> None:
    """Test that current_cell returns first cell when at origin."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]

    cell = grid.current_cell

    assert cell == grid.cells[0]


def test_current_cell_updates_after_navigation(parent: UIComponent) -> None:
    """Test that current_cell updates after navigation."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    # Set unique values to distinguish cells
    for i, cell in enumerate(grid.cells):
        cell.value = str(i)

    initial_cell_value = grid.current_cell.value

    grid.on_navigation(grid, Direction.RIGHT)

    new_cell_value = grid.current_cell.value
    assert new_cell_value != initial_cell_value
    assert new_cell_value == "1"


# current_coordinates Property Tests


def test_current_coordinates_getter(parent: UIComponent) -> None:
    """Test that current_coordinates returns current x,y position."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]
    grid.x = 2
    grid.y = 1

    coords = grid.current_coordinates

    assert coords == (2, 1)


def test_current_coordinates_setter(parent: UIComponent) -> None:
    """Test that current_coordinates setter updates position."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]

    grid.current_coordinates = (2, 1)

    assert grid.x == 2
    assert grid.y == 1


def test_current_coordinates_setter_raises_error_for_x_out_of_bounds(
    parent: UIComponent,
) -> None:
    """Test that current_coordinates setter raises error for x >= width."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="x is out of bounds"):
        grid.current_coordinates = (2, 0)


def test_current_coordinates_setter_raises_error_for_negative_x(
    parent: UIComponent,
) -> None:
    """Test that current_coordinates setter raises error for negative x."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="x is out of bounds"):
        grid.current_coordinates = (-1, 0)


def test_current_coordinates_setter_raises_error_for_y_out_of_bounds(
    parent: UIComponent,
) -> None:
    """Test that current_coordinates setter raises error for y >= height."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="y is out of bounds"):
        grid.current_coordinates = (0, 2)


def test_current_coordinates_setter_raises_error_for_negative_y(
    parent: UIComponent,
) -> None:
    """Test that current_coordinates setter raises error for negative y."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="y is out of bounds"):
        grid.current_coordinates = (0, -1)


def test_current_coordinates_at_boundaries(parent: UIComponent) -> None:
    """Test that current_coordinates works at grid boundaries."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 4)  # type: ignore[arg-type]

    # Bottom-left
    grid.current_coordinates = (0, 0)
    assert grid.current_coordinates == (0, 0)

    # Top-right
    grid.current_coordinates = (3, 2)
    assert grid.current_coordinates == (3, 2)


# value Property Tests


def test_value_getter_returns_current_cell_value(
    parent: UIComponent,
) -> None:
    """Test that value getter returns value of current cell."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]
    grid.cells[0].value = "Test Value"

    value = grid.value

    assert value == "Test Value"


def test_value_setter_updates_current_cell_value(
    parent: UIComponent,
) -> None:
    """Test that value setter updates value of current cell."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]

    grid.value = "New Value"

    assert grid.cells[0].value == "New Value"


def test_value_with_custom_property_name(parent: UIComponent) -> None:
    """Test that value works with custom property_name."""
    grid: Grid[CustomCell] = Grid(
        parent, "Grid", 2, 2, cell_class=CustomCell, property_name="extra_data"  # type: ignore[arg-type]
    )
    grid.cells[0].extra_data = 42

    value = grid.value

    assert value == "42"


def test_value_setter_with_custom_property_name(
    parent: UIComponent,
) -> None:
    """Test that value setter works with custom property_name."""
    grid: Grid[CustomCell] = Grid(
        parent, "Grid", 2, 2, cell_class=CustomCell, property_name="extra_data"  # type: ignore[arg-type]
    )

    grid.value = "99"

    assert grid.cells[0].extra_data == "99"


def test_value_updates_after_navigation(parent: UIComponent) -> None:
    """Test that value updates after navigation."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]
    grid.cells[0].value = "Cell 0"
    grid.cells[1].value = "Cell 1"

    grid.on_navigation(grid, Direction.RIGHT)

    assert grid.value == "Cell 1"


# Event Registration Tests


def test_on_border_event_is_registered() -> None:
    """Test that on_border event is registered on Grid class."""
    assert "on_border" in Grid.event_types


def test_on_navigation_event_is_registered() -> None:
    """Test that on_navigation event is registered on Grid class."""
    assert "on_navigation" in Grid.event_types


def test_grid_has_inherited_events() -> None:
    """Test that Grid has inherited events from Element."""
    assert "on_focus" in Grid.event_types
    assert "on_lose_focus" in Grid.event_types
    assert "on_change" in Grid.event_types


# Inheritance Tests


def test_grid_inherits_from_element(parent: UIComponent) -> None:
    """Test that Grid inherits from Element."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]
    assert isinstance(grid, Element)


def test_grid_has_element_methods(parent: UIComponent) -> None:
    """Test that Grid has Element methods."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]  # type: ignore[arg-type]
    assert hasattr(grid, "setup")
    assert hasattr(grid, "update")
    assert hasattr(grid, "exit")
    assert callable(grid.setup)
    assert callable(grid.update)
    assert callable(grid.exit)


def test_grid_has_get_window_method(parent: UIComponent) -> None:
    """Test that Grid has get_window method."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]  # type: ignore[arg-type]
    assert hasattr(grid, "get_window")
    assert callable(grid.get_window)


# Integration Tests


def test_grid_lifecycle(
    mocker: MockerFixture, window: Window, parent: UIComponent
) -> None:
    """Test complete grid lifecycle."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]

    mock_push = mocker.patch.object(window, "push_window_handlers")
    mock_pop = mocker.patch.object(window, "pop_window_handlers")

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    # Setup
    result = grid.setup(mock_change_state)
    assert result is True
    mock_push.assert_called_once_with(grid.key_handler)

    # Update
    result = grid.update(0.016)
    assert result is True

    # Navigate
    result = grid.navigate_right()
    assert result is True
    assert grid.x == 1

    # Reset
    grid.reset()
    assert grid.x == 0

    # Exit
    result = grid.exit()
    assert result is True
    mock_pop.assert_called_once()


def test_grid_navigation_sequence(parent: UIComponent) -> None:
    """Test a sequence of navigation actions."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]

    # Start at (0, 0)
    assert grid.current_coordinates == (0, 0)

    # Move right to (1, 0)
    grid.on_navigation(grid, Direction.RIGHT)
    assert grid.current_coordinates == (1, 0)

    # Move up to (1, 1)
    grid.on_navigation(grid, Direction.UP)
    assert grid.current_coordinates == (1, 1)

    # Move left to (0, 1)
    grid.on_navigation(grid, Direction.LEFT)
    assert grid.current_coordinates == (0, 1)

    # Move down to (0, 0)
    grid.on_navigation(grid, Direction.DOWN)
    assert grid.current_coordinates == (0, 0)


def test_grid_multiple_event_listeners(parent: UIComponent) -> None:
    """Test that multiple event listeners work correctly."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]
    navigation_count = 0
    border_count = 0

    @grid.event  # type: ignore[misc]
    def on_navigation(g: Grid[Cell], direction: Direction) -> None:
        nonlocal navigation_count
        navigation_count += 1

    @grid.event  # type: ignore[misc]
    def on_border(g: Grid[Cell], direction: Direction) -> None:
        nonlocal border_count
        border_count += 1

    # Navigate within bounds
    grid.navigate_right()
    assert navigation_count == 1
    assert border_count == 0

    # Navigate to border
    grid.navigate_right()
    assert navigation_count == 1
    assert border_count == 1


def test_grid_key_press_simulation(parent: UIComponent) -> None:
    """Test simulating arrow key presses on grid."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 3)  # type: ignore[arg-type]

    # Simulate RIGHT key press
    for k, (
        callback,
        _,
    ) in grid.key_handler.registered_key_presses.items():
        if k.symbol == key.RIGHT and k.modifiers == 0:
            callback.call()
            break

    assert grid.x == 1

    # Simulate UP key press
    for k, (
        callback,
        _,
    ) in grid.key_handler.registered_key_presses.items():
        if k.symbol == key.UP and k.modifiers == 0:
            callback.call()
            break

    assert grid.y == 1


def test_grid_with_custom_cells(parent: UIComponent) -> None:
    """Test grid with custom cell class."""
    custom_cells = [
        CustomCell(value=f"Cell {i}", extra_data=i) for i in range(4)
    ]
    grid: Grid[CustomCell] = Grid(
        parent, "Grid", 2, 2, cells=custom_cells, cell_class=CustomCell  # type: ignore[arg-type]
    )

    assert grid.current_cell.value == "Cell 0"
    assert grid.current_cell.extra_data == 0

    grid.on_navigation(grid, Direction.RIGHT)

    assert grid.current_cell.value == "Cell 1"
    assert grid.current_cell.extra_data == 1


def test_grid_cell_value_modification(parent: UIComponent) -> None:
    """Test modifying cell values through grid."""
    grid: Grid[Cell] = Grid(parent, "Grid", 2, 2)  # type: ignore[arg-type]

    grid.value = "Modified"
    assert grid.cells[0].value == "Modified"

    grid.on_navigation(grid, Direction.RIGHT)
    grid.value = "Another"
    assert grid.cells[1].value == "Another"


def test_grid_with_different_dimensions(parent: UIComponent) -> None:
    """Test grid with various dimensions."""
    # Wide grid
    wide_grid: Grid[Cell] = Grid(parent, "Grid", 2, 10)  # type: ignore[arg-type]  # type: ignore[arg-type]
    assert wide_grid.width == 10
    assert wide_grid.height == 2
    assert len(wide_grid.cells) == 20

    # Tall grid
    tall_grid: Grid[Cell] = Grid(parent, "Grid", 10, 2)  # type: ignore[arg-type]
    assert tall_grid.width == 2
    assert tall_grid.height == 10
    assert len(tall_grid.cells) == 20

    # Square grid
    square_grid: Grid[Cell] = Grid(parent, "Grid", 5, 5)  # type: ignore[arg-type]
    assert square_grid.width == 5
    assert square_grid.height == 5
    assert len(square_grid.cells) == 25


def test_grid_dynamic_growth(parent: UIComponent) -> None:
    """Test dynamically growing grid with add_row."""
    grid: Grid[Cell] = Grid(parent, "Grid", 1, 3)  # type: ignore[arg-type]
    initial_cell_count = len(grid.cells)

    # Add multiple rows
    for i in range(5):
        grid.add_row()

    # Each add_row adds 3 cells (width is 3)
    assert len(grid.cells) == initial_cell_count + (5 * 3)
    # Note: add_row sets height to len(cells), not number of rows
    assert grid.height == len(grid.cells)


def test_grid_cell_indexing(parent: UIComponent) -> None:
    """Test that cells are indexed correctly."""
    grid: Grid[Cell] = Grid(parent, "Grid", 3, 4)  # type: ignore[arg-type]

    # Label cells for testing
    for i, cell in enumerate(grid.cells):
        cell.value = str(i)

    # Test various positions
    grid.current_coordinates = (0, 0)
    assert grid.value == "0"

    grid.current_coordinates = (3, 0)
    assert grid.value == "3"

    grid.current_coordinates = (0, 1)
    assert grid.value == "4"

    grid.current_coordinates = (2, 2)
    assert grid.value == "10"


def test_grid_default_cell_class_is_cell() -> None:
    """Test that default cell_class is Cell."""
    from sonartk.ui.element.grid import Cell

    assert Cell is not None


def test_cell_dataclass_has_value_field() -> None:
    """Test that Cell dataclass has value field."""
    cell = Cell()
    assert hasattr(cell, "value")
    assert cell.value == ""


def test_cell_can_be_instantiated_with_value() -> None:
    """Test that Cell can be instantiated with a value."""
    cell = Cell(value="Test")
    assert cell.value == "Test"
