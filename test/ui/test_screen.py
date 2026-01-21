"""Comprehensive unit tests for the Screen module."""

from typing import Any, Callable
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from sonartk.ui.screen.screen import Screen
from sonartk.ui.window import Window
from sonartk.ui.ui_component import UIComponent
from sonartk.util.state import State
from sonartk.util.state_machine import EmptyState, StateMachine
from sonartk.util.key_handler import KeyHandler
from test.mocks.mock_state import MockState


class ConcreteScreen(Screen):
    """Concrete implementation of Screen for testing."""

    def bind_keys(self) -> None:
        """Implementation of abstract bind_keys method."""
        pass

    def setup(
        self,
        change_state: Callable[[str, Any], None],
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """Implementation of abstract setup method."""
        return True

    def update(self, delta_time: float) -> bool:
        """Implementation of abstract update method."""
        return True

    def exit(self) -> bool:
        """Implementation of abstract exit method."""
        return True


class MockElement(State, UIComponent):
    """Mock Element class for testing."""

    def __init__(self, parent: UIComponent) -> None:
        self.parent = parent
        self.setup_called = False
        self.update_called = False
        self.exit_called = False

    def setup(
        self,
        change_state: Callable[[str, Any], None],
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        self.setup_called = True
        return True

    def update(self, delta_time: float) -> bool:
        self.update_called = True
        return True

    def exit(self) -> bool:
        self.exit_called = True
        return True


@pytest.fixture
def window(mocker: MockerFixture) -> Window:
    """Returns a Window instance for testing."""
    win = Window(caption="Test Window")
    # Mock pyglet_window to avoid AttributeError
    win.pyglet_window = mocker.MagicMock()  # type: ignore[attr-defined]
    return win


@pytest.fixture
def screen(window: Window) -> ConcreteScreen:
    """Returns a ConcreteScreen instance with a Window parent."""
    return ConcreteScreen(parent=window)


@pytest.fixture
def parent_screen(window: Window) -> ConcreteScreen:
    """Returns a parent Screen for testing nested screens."""
    return ConcreteScreen(parent=window)


@pytest.fixture
def nested_screen(parent_screen: ConcreteScreen) -> ConcreteScreen:
    """Returns a nested Screen (Screen with Screen parent)."""
    return ConcreteScreen(parent=parent_screen)


def test_screen_initialization_with_window_parent(
    window: Window, screen: ConcreteScreen
) -> None:
    """Test Screen initialization with a Window parent."""
    assert screen.parent is window
    assert screen.position == 0
    assert isinstance(screen.state_machine, StateMachine)
    assert isinstance(screen.key_handler, KeyHandler)


def test_screen_initialization_with_screen_parent(
    parent_screen: ConcreteScreen, nested_screen: ConcreteScreen
) -> None:
    """Test Screen initialization with a Screen parent."""
    assert nested_screen.parent is parent_screen
    assert nested_screen.position == 0
    assert isinstance(nested_screen.state_machine, StateMachine)
    assert isinstance(nested_screen.key_handler, KeyHandler)


def test_screen_is_ui_component(screen: ConcreteScreen) -> None:
    """Test that Screen is a UIComponent."""
    assert isinstance(screen, UIComponent)


def test_screen_is_state(screen: ConcreteScreen) -> None:
    """Test that Screen is a State."""
    assert isinstance(screen, State)


def test_screen_state_machine_starts_empty(screen: ConcreteScreen) -> None:
    """Test that state_machine starts empty."""
    assert screen.state_machine.is_empty()
    assert screen.state_machine.size() == 0


def test_close_dispatches_event(
    mocker: MockerFixture, screen: ConcreteScreen
) -> None:
    """Test that close() dispatches on_close event."""
    mock_handler = mocker.MagicMock()
    screen.push_handlers(on_close=mock_handler)

    result = screen.close()

    assert result is True
    mock_handler.assert_called_once_with(screen)


def test_close_returns_true(screen: ConcreteScreen) -> None:
    """Test that close() returns True."""
    result = screen.close()
    assert result is True


def test_add_element_to_screen(screen: ConcreteScreen) -> None:
    """Test adding an element to the screen."""
    element = MockElement(parent=screen)

    screen.add("element1", element)  # type: ignore[arg-type]

    assert screen.state_machine.size() == 1
    assert screen.state_machine.contains("element1")


def test_add_screen_to_screen(parent_screen: ConcreteScreen) -> None:
    """Test adding a Screen to another Screen."""
    child_screen = ConcreteScreen(parent=parent_screen)

    parent_screen.add("child", child_screen)

    assert parent_screen.state_machine.size() == 1
    assert parent_screen.state_machine.contains("child")


def test_add_multiple_elements(screen: ConcreteScreen) -> None:
    """Test adding multiple elements to the screen."""
    element1 = MockElement(parent=screen)
    element2 = MockElement(parent=screen)
    element3 = MockElement(parent=screen)

    screen.add("el1", element1)  # type: ignore[arg-type]
    screen.add("el2", element2)  # type: ignore[arg-type]
    screen.add("el3", element3)  # type: ignore[arg-type]

    assert screen.state_machine.size() == 3
    assert screen.state_machine.contains("el1")
    assert screen.state_machine.contains("el2")
    assert screen.state_machine.contains("el3")


def test_remove_element_from_screen(screen: ConcreteScreen) -> None:
    """Test removing an element from the screen."""
    element = MockElement(parent=screen)
    screen.add("element1", element)  # type: ignore[arg-type]

    removed = screen.remove("element1")

    assert removed is element
    assert screen.state_machine.size() == 0
    assert not screen.state_machine.contains("element1")


def test_remove_nonexistent_element_returns_none(
    screen: ConcreteScreen,
) -> None:
    """Test that removing a nonexistent element returns None."""
    result = screen.remove("nonexistent")
    assert result is None


def test_remove_from_multiple_elements(screen: ConcreteScreen) -> None:
    """Test removing one element from multiple."""
    element1 = MockElement(parent=screen)
    element2 = MockElement(parent=screen)
    element3 = MockElement(parent=screen)

    screen.add("el1", element1)  # type: ignore[arg-type]
    screen.add("el2", element2)  # type: ignore[arg-type]
    screen.add("el3", element3)  # type: ignore[arg-type]

    removed = screen.remove("el2")

    assert removed is element2
    assert screen.state_machine.size() == 2
    assert screen.state_machine.contains("el1")
    assert not screen.state_machine.contains("el2")
    assert screen.state_machine.contains("el3")


def test_next_element_with_empty_state_machine(
    screen: ConcreteScreen,
) -> None:
    """Test next_element when state_machine is empty."""
    result = screen.next_element()
    assert result is False


def test_next_element_with_single_element(screen: ConcreteScreen) -> None:
    """Test next_element with only one element (position doesn't change)."""
    element = MockElement(parent=screen)
    screen.add("element1", element)  # type: ignore[arg-type]

    assert screen.position == 0
    result = screen.next_element()

    assert result is True
    assert screen.position == 0


def test_next_element_with_multiple_elements(
    mocker: MockerFixture, screen: ConcreteScreen
) -> None:
    """Test next_element with multiple elements."""
    element1 = MockElement(parent=screen)
    element2 = MockElement(parent=screen)
    element3 = MockElement(parent=screen)

    screen.add("el1", element1)  # type: ignore[arg-type]
    screen.add("el2", element2)  # type: ignore[arg-type]
    screen.add("el3", element3)  # type: ignore[arg-type]

    # Mock set_state to avoid side effects
    mocker.patch.object(screen, "set_state")

    assert screen.position == 0
    screen.next_element()
    assert screen.position == 1

    screen.next_element()
    assert screen.position == 2

    # Should wrap around to 0
    screen.next_element()
    assert screen.position == 0


def test_next_element_dispatches_event(
    mocker: MockerFixture, screen: ConcreteScreen
) -> None:
    """Test that next_element dispatches on_next_element event."""
    mock_handler = mocker.MagicMock()
    screen.push_handlers(on_next_element=mock_handler)

    element = MockElement(parent=screen)
    screen.add("element1", element)  # type: ignore[arg-type]

    screen.next_element()

    mock_handler.assert_called_once_with(screen)


def test_previous_element_with_empty_state_machine(
    screen: ConcreteScreen,
) -> None:
    """Test previous_element when state_machine is empty."""
    result = screen.previous_element()
    assert result is False


def test_previous_element_with_single_element(
    screen: ConcreteScreen,
) -> None:
    """Test previous_element with only one element (position doesn't change)."""
    element = MockElement(parent=screen)
    screen.add("element1", element)  # type: ignore[arg-type]

    assert screen.position == 0
    result = screen.previous_element()

    assert result is True
    assert screen.position == 0


def test_previous_element_with_multiple_elements(
    mocker: MockerFixture, screen: ConcreteScreen
) -> None:
    """Test previous_element with multiple elements."""
    element1 = MockElement(parent=screen)
    element2 = MockElement(parent=screen)
    element3 = MockElement(parent=screen)

    screen.add("el1", element1)  # type: ignore[arg-type]
    screen.add("el2", element2)  # type: ignore[arg-type]
    screen.add("el3", element3)  # type: ignore[arg-type]

    # Mock set_state to avoid side effects
    mocker.patch.object(screen, "set_state")

    assert screen.position == 0
    # Should wrap around to last element (2)
    screen.previous_element()
    assert screen.position == 2

    screen.previous_element()
    assert screen.position == 1

    screen.previous_element()
    assert screen.position == 0


def test_previous_element_dispatches_event(
    mocker: MockerFixture, screen: ConcreteScreen
) -> None:
    """Test that previous_element dispatches on_previous_element event."""
    mock_handler = mocker.MagicMock()
    screen.push_handlers(on_previous_element=mock_handler)

    element = MockElement(parent=screen)
    screen.add("element1", element)  # type: ignore[arg-type]

    screen.previous_element()

    mock_handler.assert_called_once_with(screen)


def test_set_state_with_empty_state_machine(screen: ConcreteScreen) -> None:
    """Test set_state when state_machine is empty (should do nothing)."""
    # Should not raise any errors
    screen.set_state()
    screen.set_state(interrupt_speech=False)


def test_set_state_changes_to_current_position(
    screen: ConcreteScreen,
) -> None:
    """Test that set_state changes to the state at current position."""
    element1 = MockState()
    element2 = MockState()
    element3 = MockState()

    screen.add("el1", element1)  # type: ignore[arg-type]
    screen.add("el2", element2)  # type: ignore[arg-type]
    screen.add("el3", element3)  # type: ignore[arg-type]

    screen.position = 1
    screen.set_state()

    assert screen.state_machine.current_state is element2


def test_set_state_with_interrupt_speech_true(
    screen: ConcreteScreen,
) -> None:
    """Test set_state with interrupt_speech=True (default)."""
    element = MockState()
    screen.add("element1", element)  # type: ignore[arg-type]

    screen.set_state(interrupt_speech=True)

    assert screen.state_machine.current_state is element


def test_set_state_with_interrupt_speech_false(
    screen: ConcreteScreen,
) -> None:
    """Test set_state with interrupt_speech=False."""
    element = MockState()
    screen.add("element1", element)  # type: ignore[arg-type]

    screen.set_state(interrupt_speech=False)

    assert screen.state_machine.current_state is element


def test_bind_keys_is_called_during_initialization(
    mocker: MockerFixture, window: Window
) -> None:
    """Test that bind_keys is called during __init__."""
    # Create a mock to track bind_keys calls
    original_bind = ConcreteScreen.bind_keys
    bind_mock = mocker.MagicMock()

    def bind_spy(self: ConcreteScreen) -> None:
        bind_mock()
        original_bind(self)

    mocker.patch.object(ConcreteScreen, "bind_keys", bind_spy)
    ConcreteScreen(parent=window)
    bind_mock.assert_called_once()


def test_bind_keys_is_abstract() -> None:
    """Test that bind_keys is an abstract method."""
    from abc import abstractmethod

    assert hasattr(Screen.bind_keys, "__isabstractmethod__")
    assert Screen.bind_keys.__isabstractmethod__ is True


def test_caption_property_gets_parent_caption(
    window: Window, screen: ConcreteScreen
) -> None:
    """Test that caption property returns parent's caption."""
    window.caption = "Test Caption"
    assert screen.caption == "Test Caption"


def test_caption_property_with_nested_screen(
    window: Window,
    parent_screen: ConcreteScreen,
    nested_screen: ConcreteScreen,
) -> None:
    """Test caption property with nested screens."""
    window.caption = "Window Caption"
    # Both screens should return the window's caption
    assert parent_screen.caption == "Window Caption"
    assert nested_screen.caption == "Window Caption"


def test_caption_setter_sets_parent_caption(
    window: Window, screen: ConcreteScreen
) -> None:
    """Test that caption setter updates parent's caption."""
    screen.caption = "New Caption"
    assert window.caption == "New Caption"


def test_caption_setter_with_nested_screen(
    window: Window,
    parent_screen: ConcreteScreen,
    nested_screen: ConcreteScreen,
) -> None:
    """Test caption setter with nested screens."""
    nested_screen.caption = "Nested Caption"
    # Should propagate to parent screen's parent (window)
    assert parent_screen.caption == "Nested Caption"
    assert window.caption == "Nested Caption"


def test_active_element_property_returns_current_state(
    screen: ConcreteScreen,
) -> None:
    """Test that active_element returns the current state."""
    element1 = MockState()
    element2 = MockState()

    screen.add("el1", element1)  # type: ignore[arg-type]
    screen.add("el2", element2)  # type: ignore[arg-type]

    # Initially should be EmptyState
    assert isinstance(screen.active_element, EmptyState)

    screen.set_state()
    assert screen.active_element is element1

    screen.position = 1
    screen.set_state()
    assert screen.active_element is element2


def test_active_element_when_empty(screen: ConcreteScreen) -> None:
    """Test active_element when state_machine is empty."""
    assert isinstance(screen.active_element, EmptyState)


def test_next_element_calls_set_state(
    mocker: MockerFixture, screen: ConcreteScreen
) -> None:
    """Test that next_element calls set_state."""
    element = MockElement(parent=screen)
    screen.add("element1", element)  # type: ignore[arg-type]

    mock_set_state = mocker.patch.object(screen, "set_state")

    screen.next_element()

    mock_set_state.assert_called_once()


def test_previous_element_calls_set_state(
    mocker: MockerFixture, screen: ConcreteScreen
) -> None:
    """Test that previous_element calls set_state."""
    element = MockElement(parent=screen)
    screen.add("element1", element)  # type: ignore[arg-type]

    mock_set_state = mocker.patch.object(screen, "set_state")

    screen.previous_element()

    mock_set_state.assert_called_once()


def test_screen_inherits_from_event_dispatcher(
    screen: ConcreteScreen,
) -> None:
    """Test that Screen inherits from EventDispatcher."""
    from pyglet.event import EventDispatcher

    assert isinstance(screen, EventDispatcher)


def test_screen_registers_event_types() -> None:
    """Test that Screen registers required event types."""
    assert "on_next_element" in Screen.event_types
    assert "on_previous_element" in Screen.event_types
    assert "on_close" in Screen.event_types


def test_get_window_returns_parent_window(
    window: Window, screen: ConcreteScreen
) -> None:
    """Test that get_window returns the parent Window."""
    assert screen.get_window() is window


def test_get_window_with_nested_screens(
    window: Window,
    parent_screen: ConcreteScreen,
    nested_screen: ConcreteScreen,
) -> None:
    """Test get_window with nested screens."""
    assert nested_screen.get_window() is window
    assert parent_screen.get_window() is window


def test_position_can_be_manually_set(screen: ConcreteScreen) -> None:
    """Test that position attribute can be set."""
    screen.position = 5
    assert screen.position == 5


def test_state_machine_attribute_is_accessible(
    screen: ConcreteScreen,
) -> None:
    """Test that state_machine attribute is accessible."""
    assert hasattr(screen, "state_machine")
    assert isinstance(screen.state_machine, StateMachine)


def test_key_handler_attribute_is_accessible(screen: ConcreteScreen) -> None:
    """Test that key_handler attribute is accessible."""
    assert hasattr(screen, "key_handler")
    assert isinstance(screen.key_handler, KeyHandler)


def test_add_uses_state_machine_add(
    mocker: MockerFixture, screen: ConcreteScreen
) -> None:
    """Test that add method delegates to state_machine.add."""
    element = MockElement(parent=screen)
    mock_add = mocker.patch.object(screen.state_machine, "add")

    screen.add("key", element)  # type: ignore[arg-type]

    mock_add.assert_called_once_with("key", element)


def test_remove_uses_state_machine_remove(
    mocker: MockerFixture, screen: ConcreteScreen
) -> None:
    """Test that remove method delegates to state_machine.remove."""
    mock_remove = mocker.patch.object(screen.state_machine, "remove")
    mock_remove.return_value = None

    screen.remove("key")

    mock_remove.assert_called_once_with("key")


def test_next_element_with_two_elements(
    mocker: MockerFixture, screen: ConcreteScreen
) -> None:
    """Test next_element behavior with exactly two elements."""
    element1 = MockElement(parent=screen)
    element2 = MockElement(parent=screen)

    screen.add("el1", element1)  # type: ignore[arg-type]
    screen.add("el2", element2)  # type: ignore[arg-type]

    mocker.patch.object(screen, "set_state")

    assert screen.position == 0
    screen.next_element()
    assert screen.position == 1

    screen.next_element()
    assert screen.position == 0


def test_previous_element_with_two_elements(
    mocker: MockerFixture, screen: ConcreteScreen
) -> None:
    """Test previous_element behavior with exactly two elements."""
    element1 = MockElement(parent=screen)
    element2 = MockElement(parent=screen)

    screen.add("el1", element1)  # type: ignore[arg-type]
    screen.add("el2", element2)  # type: ignore[arg-type]

    mocker.patch.object(screen, "set_state")

    assert screen.position == 0
    screen.previous_element()
    assert screen.position == 1

    screen.previous_element()
    assert screen.position == 0


def test_modulo_wrapping_next_element(
    mocker: MockerFixture, screen: ConcreteScreen
) -> None:
    """Test that next_element uses modulo for wrapping."""
    for i in range(5):
        screen.add(f"el{i}", MockElement(parent=screen))  # type: ignore[arg-type]

    mocker.patch.object(screen, "set_state")

    screen.position = 4
    screen.next_element()
    # 4 + 1 = 5, 5 % 5 = 0
    assert screen.position == 0


def test_modulo_wrapping_previous_element(
    mocker: MockerFixture, screen: ConcreteScreen
) -> None:
    """Test that previous_element uses modulo for wrapping."""
    for i in range(5):
        screen.add(f"el{i}", MockElement(parent=screen))  # type: ignore[arg-type]

    mocker.patch.object(screen, "set_state")

    screen.position = 0
    screen.previous_element()
    # 0 - 1 = -1, -1 % 5 = 4
    assert screen.position == 4


def test_set_state_calls_state_machine_change(
    mocker: MockerFixture, screen: ConcreteScreen
) -> None:
    """Test that set_state calls state_machine.change with correct arguments."""
    element = MockElement(parent=screen)
    screen.add("element1", element)  # type: ignore[arg-type]

    mock_change = mocker.patch.object(screen.state_machine, "change")

    screen.set_state(interrupt_speech=True)

    mock_change.assert_called_once_with("element1", True)


def test_set_state_passes_interrupt_speech_to_change(
    mocker: MockerFixture, screen: ConcreteScreen
) -> None:
    """Test that set_state passes interrupt_speech parameter correctly."""
    element = MockElement(parent=screen)
    screen.add("element1", element)  # type: ignore[arg-type]

    mock_change = mocker.patch.object(screen.state_machine, "change")

    screen.set_state(interrupt_speech=False)

    mock_change.assert_called_once_with("element1", False)


def test_parent_attribute_type(screen: ConcreteScreen) -> None:
    """Test that parent attribute exists and has correct type annotation."""
    # The parent is annotated as HasCaption but is actually a Window
    assert hasattr(screen.parent, "caption")


def test_screen_position_initialized_to_zero(
    window: Window, screen: ConcreteScreen
) -> None:
    """Test that position is initialized to 0."""
    assert screen.position == 0


def test_multiple_screens_share_same_window_parent(window: Window) -> None:
    """Test that multiple screens can share the same Window parent."""
    screen1 = ConcreteScreen(parent=window)
    screen2 = ConcreteScreen(parent=window)
    screen3 = ConcreteScreen(parent=window)

    assert screen1.parent is window
    assert screen2.parent is window
    assert screen3.parent is window
