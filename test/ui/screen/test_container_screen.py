from typing import Any, Callable

import pytest
from pytest_mock import MockerFixture
from pyglet.window import key

from sonartk.ui.screen.container_screen import ContainerScreen
from sonartk.ui.screen.screen import Screen
from sonartk.ui.window import Window
from sonartk.util.key_handler import KeyHandler
from sonartk.util.state_machine import StateMachine
from test.mocks.mock_state import MockState


@pytest.fixture
def window(mocker: MockerFixture) -> Window:
    """Returns a Window instance for testing."""
    win = Window(caption="Test Window")
    # Mock pyglet_window to avoid AttributeError
    win.pyglet_window = mocker.MagicMock()  # type: ignore[attr-defined]
    return win


@pytest.fixture
def parent_screen(window: Window) -> Screen:
    """Returns a parent Screen for testing."""

    class TestScreen(Screen):
        def bind_keys(self) -> None:
            pass

        def setup(
            self,
            change_state: Callable[[str, Any], None],
            *args: Any,
            **kwargs: Any,
        ) -> bool:
            return True

        def update(self, delta_time: float) -> bool:
            return True

        def exit(self) -> bool:
            return True

    return TestScreen(parent=window)


@pytest.fixture
def container_screen(window: Window) -> ContainerScreen:
    """Returns a ContainerScreen instance with a Window parent."""
    return ContainerScreen(parent=window)


@pytest.fixture
def nested_container_screen(parent_screen: Screen) -> ContainerScreen:
    """Returns a ContainerScreen with a Screen parent."""
    return ContainerScreen(parent=parent_screen)


def test_container_screen_initialization_with_window_parent(
    window: Window, container_screen: ContainerScreen
) -> None:
    """Test ContainerScreen initialization with a Window parent."""
    assert container_screen.parent is window
    assert container_screen.position == 0
    assert isinstance(container_screen.state_machine, StateMachine)
    assert isinstance(container_screen.key_handler, KeyHandler)


def test_container_screen_initialization_with_screen_parent(
    parent_screen: Screen, nested_container_screen: ContainerScreen
) -> None:
    """Test ContainerScreen initialization with a Screen parent."""
    assert nested_container_screen.parent is parent_screen
    assert nested_container_screen.position == 0
    assert isinstance(nested_container_screen.state_machine, StateMachine)
    assert isinstance(nested_container_screen.key_handler, KeyHandler)


def test_container_screen_is_screen(container_screen: ContainerScreen) -> None:
    """Test that ContainerScreen is a Screen."""
    assert isinstance(container_screen, Screen)


def test_bind_keys_registers_tab_key(
    container_screen: ContainerScreen,
) -> None:
    """Test that bind_keys registers TAB for next_element."""
    key_handler = container_screen.key_handler

    # Check that TAB is registered
    assert any(
        k.symbol == key.TAB and k.modifiers == 0
        for k in key_handler.registered_key_presses.keys()
    )


def test_bind_keys_registers_shift_tab_key(
    container_screen: ContainerScreen,
) -> None:
    """Test that bind_keys registers SHIFT+TAB for previous_element."""
    key_handler = container_screen.key_handler

    # Check that SHIFT+TAB is registered
    assert any(
        k.symbol == key.TAB and k.modifiers == key.MOD_SHIFT
        for k in key_handler.registered_key_presses.keys()
    )


def test_bind_keys_total_key_bindings(
    container_screen: ContainerScreen,
) -> None:
    """Test that bind_keys registers exactly 2 keys."""
    assert len(container_screen.key_handler.registered_key_presses) == 2


def test_setup_pushes_key_handler(
    mocker: MockerFixture, container_screen: ContainerScreen
) -> None:
    """Test that setup pushes key_handler to window."""
    mock_push = mocker.patch.object(
        container_screen.get_window(), "push_window_handlers"
    )
    mock_change_state = mocker.MagicMock()

    container_screen.setup(mock_change_state)

    mock_push.assert_called_once_with(container_screen.key_handler)


def test_setup_calls_set_state(
    mocker: MockerFixture, container_screen: ContainerScreen
) -> None:
    """Test that setup calls set_state with interrupt_speech=False."""
    mock_set_state = mocker.patch.object(container_screen, "set_state")
    mock_change_state = mocker.MagicMock()

    container_screen.setup(mock_change_state)

    mock_set_state.assert_called_once_with(interrupt_speech=False)


def test_setup_returns_true(container_screen: ContainerScreen) -> None:
    """Test that setup returns True."""

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    result = container_screen.setup(mock_change_state)
    assert result is True


def test_setup_with_args_and_kwargs(
    container_screen: ContainerScreen,
) -> None:
    """Test that setup accepts *args and **kwargs."""

    def mock_change_state(key: str, *args: Any, **kwargs: Any) -> None:
        pass

    result = container_screen.setup(
        mock_change_state, "arg1", "arg2", kwarg1="value1", kwarg2="value2"
    )
    assert result is True


def test_set_state_with_empty_state_machine(
    container_screen: ContainerScreen,
) -> None:
    """Test set_state when state_machine is empty (should do nothing)."""
    # Should not raise any errors
    container_screen.set_state()
    container_screen.set_state(interrupt_speech=False)


def test_set_state_changes_to_current_position(
    container_screen: ContainerScreen,
) -> None:
    """Test that set_state changes to the state at current position."""
    element1 = MockState()
    element2 = MockState()
    element3 = MockState()

    container_screen.add("el1", element1)  # type: ignore[arg-type]
    container_screen.add("el2", element2)  # type: ignore[arg-type]
    container_screen.add("el3", element3)  # type: ignore[arg-type]

    container_screen.position = 1
    container_screen.set_state()

    assert container_screen.state_machine.current_state is element2


def test_set_state_with_interrupt_speech_true(
    container_screen: ContainerScreen,
) -> None:
    """Test set_state with interrupt_speech=True."""
    element = MockState()
    container_screen.add("element1", element)  # type: ignore[arg-type]

    container_screen.set_state(interrupt_speech=True)

    assert container_screen.state_machine.current_state is element


def test_set_state_with_interrupt_speech_false(
    container_screen: ContainerScreen,
) -> None:
    """Test set_state with interrupt_speech=False."""
    element = MockState()
    container_screen.add("element1", element)  # type: ignore[arg-type]

    container_screen.set_state(interrupt_speech=False)

    assert container_screen.state_machine.current_state is element


def test_set_state_calls_state_machine_change(
    mocker: MockerFixture, container_screen: ContainerScreen
) -> None:
    """Test that set_state calls state_machine.change with correct arguments."""
    element = MockState()
    container_screen.add("element1", element)  # type: ignore[arg-type]

    mock_change = mocker.patch.object(container_screen.state_machine, "change")

    container_screen.set_state(interrupt_speech=True)

    mock_change.assert_called_once_with("element1", True)


def test_update_delegates_to_state_machine(
    mocker: MockerFixture, container_screen: ContainerScreen
) -> None:
    """Test that update delegates to state_machine.update."""
    mock_update = mocker.patch.object(container_screen.state_machine, "update")
    mock_update.return_value = True

    result = container_screen.update(0.016)

    mock_update.assert_called_once_with(0.016)
    assert result is True


def test_update_returns_state_machine_result(
    container_screen: ContainerScreen,
) -> None:
    """Test that update returns the result from state_machine.update."""
    element = MockState(update_value=False)
    container_screen.add("element1", element)  # type: ignore[arg-type]
    container_screen.set_state()

    result = container_screen.update(0.016)

    assert result is False


def test_exit_calls_state_machine_exit_when_not_empty(
    mocker: MockerFixture, container_screen: ContainerScreen
) -> None:
    """Test that exit calls state_machine.exit when not empty."""
    element = MockState()
    container_screen.add("element1", element)  # type: ignore[arg-type]

    mock_exit = mocker.patch.object(container_screen.state_machine, "exit")
    mock_exit.return_value = True
    mocker.patch.object(container_screen.get_window(), "pop_window_handlers")

    container_screen.exit()

    mock_exit.assert_called_once()


def test_exit_does_not_call_state_machine_exit_when_empty(
    mocker: MockerFixture, container_screen: ContainerScreen
) -> None:
    """Test that exit does not call state_machine.exit when empty."""
    mock_exit = mocker.patch.object(container_screen.state_machine, "exit")
    mocker.patch.object(container_screen.get_window(), "pop_window_handlers")

    container_screen.exit()

    mock_exit.assert_not_called()


def test_exit_pops_window_handlers(
    mocker: MockerFixture, container_screen: ContainerScreen
) -> None:
    """Test that exit pops window handlers."""
    mock_pop = mocker.patch.object(
        container_screen.get_window(), "pop_window_handlers"
    )

    container_screen.exit()

    mock_pop.assert_called_once()


def test_exit_returns_true(
    mocker: MockerFixture, container_screen: ContainerScreen
) -> None:
    """Test that exit returns True."""
    mocker.patch.object(container_screen.get_window(), "pop_window_handlers")
    result = container_screen.exit()
    assert result is True


def test_exit_pops_handlers_even_with_empty_state_machine(
    mocker: MockerFixture, container_screen: ContainerScreen
) -> None:
    """Test that exit pops handlers even when state_machine is empty."""
    mock_pop = mocker.patch.object(
        container_screen.get_window(), "pop_window_handlers"
    )

    # State machine is empty
    assert container_screen.state_machine.is_empty()

    container_screen.exit()

    # Should still pop handlers
    mock_pop.assert_called_once()


def test_close_calls_parent_close(
    mocker: MockerFixture, container_screen: ContainerScreen
) -> None:
    """Test that close calls parent.close()."""
    mock_parent_close = mocker.patch.object(container_screen.parent, "close")

    container_screen.close()

    mock_parent_close.assert_called_once()


def test_close_calls_super_close(
    mocker: MockerFixture, container_screen: ContainerScreen
) -> None:
    """Test that close calls super().close()."""
    mock_super_close = mocker.patch.object(Screen, "close")

    container_screen.close()

    mock_super_close.assert_called_once()


def test_close_returns_true(container_screen: ContainerScreen) -> None:
    """Test that close returns True."""
    result = container_screen.close()
    assert result is True


def test_close_with_screen_parent(
    mocker: MockerFixture, nested_container_screen: ContainerScreen
) -> None:
    """Test close with a Screen parent."""
    mock_parent_close = mocker.patch.object(
        nested_container_screen.parent, "close"
    )

    nested_container_screen.close()

    mock_parent_close.assert_called_once()


def test_bind_keys_tab_calls_next_element(
    container_screen: ContainerScreen,
) -> None:
    """Test that TAB key is registered to call next_element."""
    key_handler = container_screen.key_handler
    tab_key = None
    for k in key_handler.registered_key_presses.keys():
        if k.symbol == key.TAB and k.modifiers == 0:
            tab_key = k
            break

    assert tab_key is not None, "TAB key should be registered"
    callback, _ = key_handler.registered_key_presses[tab_key]
    assert callback.callback == container_screen.next_element


def test_bind_keys_shift_tab_calls_previous_element(
    container_screen: ContainerScreen,
) -> None:
    """Test that SHIFT+TAB key is registered to call previous_element."""
    key_handler = container_screen.key_handler
    shift_tab_key = None
    for k in key_handler.registered_key_presses.keys():
        if k.symbol == key.TAB and k.modifiers == key.MOD_SHIFT:
            shift_tab_key = k
            break

    assert shift_tab_key is not None, "SHIFT+TAB key should be registered"
    callback, _ = key_handler.registered_key_presses[shift_tab_key]
    assert callback.callback == container_screen.previous_element


def test_get_window_returns_window(
    window: Window, container_screen: ContainerScreen
) -> None:
    """Test that get_window returns the root Window."""
    assert container_screen.get_window() is window


def test_get_window_with_nested_container(
    window: Window, nested_container_screen: ContainerScreen
) -> None:
    """Test get_window with nested ContainerScreen."""
    assert nested_container_screen.get_window() is window


def test_setup_integration_with_state_machine(
    container_screen: ContainerScreen,
) -> None:
    """Test setup integration with elements in state_machine."""
    element1 = MockState()
    element2 = MockState()

    container_screen.add("el1", element1)  # type: ignore[arg-type]
    container_screen.add("el2", element2)  # type: ignore[arg-type]

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    result = container_screen.setup(mock_change_state)

    assert result is True
    # set_state should have been called, making el1 active
    assert container_screen.state_machine.current_state is element1


def test_exit_integration_with_state_machine(
    mocker: MockerFixture,
    container_screen: ContainerScreen,
) -> None:
    """Test exit integration with elements in state_machine."""
    element = MockState()
    container_screen.add("element1", element)  # type: ignore[arg-type]
    container_screen.set_state()

    mocker.patch.object(container_screen.get_window(), "pop_window_handlers")
    result = container_screen.exit()

    assert result is True


def test_update_with_multiple_elements(
    container_screen: ContainerScreen,
) -> None:
    """Test update with multiple elements in state_machine."""
    element1 = MockState(update_value=True)
    element2 = MockState(update_value=False)

    container_screen.add("el1", element1)  # type: ignore[arg-type]
    container_screen.add("el2", element2)  # type: ignore[arg-type]

    container_screen.set_state()  # Activates el1
    result = container_screen.update(0.016)
    assert result is True

    container_screen.position = 1
    container_screen.set_state()  # Activates el2
    result = container_screen.update(0.016)
    assert result is False


def test_container_screen_inherits_screen_methods(
    container_screen: ContainerScreen,
) -> None:
    """Test that ContainerScreen inherits Screen methods."""
    assert hasattr(container_screen, "next_element")
    assert hasattr(container_screen, "previous_element")
    assert hasattr(container_screen, "add")
    assert hasattr(container_screen, "remove")


def test_caption_property_delegates_to_parent(
    window: Window, container_screen: ContainerScreen
) -> None:
    """Test that caption property delegates to parent."""
    window.caption = "Test Caption"
    assert container_screen.caption == "Test Caption"


def test_caption_setter_delegates_to_parent(
    window: Window, container_screen: ContainerScreen
) -> None:
    """Test that caption setter delegates to parent."""
    container_screen.caption = "New Caption"
    assert window.caption == "New Caption"


def test_state_machine_is_inherited_from_screen(
    container_screen: ContainerScreen,
) -> None:
    """Test that state_machine is inherited from Screen."""
    assert isinstance(container_screen.state_machine, StateMachine)
    assert container_screen.state_machine.is_empty()


def test_position_is_inherited_from_screen(
    container_screen: ContainerScreen,
) -> None:
    """Test that position is inherited from Screen."""
    assert container_screen.position == 0
    container_screen.position = 5
    assert container_screen.position == 5


def test_setup_with_empty_state_machine(
    container_screen: ContainerScreen,
) -> None:
    """Test setup when state_machine is empty."""

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    result = container_screen.setup(mock_change_state)
    assert result is True


def test_exit_order_of_operations(
    mocker: MockerFixture, container_screen: ContainerScreen
) -> None:
    """Test that exit calls state_machine.exit before popping handlers."""
    call_order = []

    def mock_state_exit() -> bool:
        call_order.append("state_exit")
        return True

    def mock_pop() -> None:
        call_order.append("pop_handlers")

    element = MockState()
    container_screen.add("element1", element)  # type: ignore[arg-type]

    mocker.patch.object(
        container_screen.state_machine, "exit", side_effect=mock_state_exit
    )
    mocker.patch.object(
        container_screen.get_window(),
        "pop_window_handlers",
        side_effect=mock_pop,
    )

    container_screen.exit()

    assert call_order == ["state_exit", "pop_handlers"]


def test_close_order_of_operations(
    mocker: MockerFixture, container_screen: ContainerScreen
) -> None:
    """Test that close calls super().close() before parent.close()."""
    call_order = []

    def mock_super_close() -> bool:
        call_order.append("super_close")
        return True

    def mock_parent_close() -> bool:
        call_order.append("parent_close")
        return True

    mocker.patch.object(Screen, "close", side_effect=mock_super_close)
    mocker.patch.object(
        container_screen.parent, "close", side_effect=mock_parent_close
    )

    container_screen.close()

    assert call_order == ["super_close", "parent_close"]


def test_multiple_container_screens_share_window(window: Window) -> None:
    """Test that multiple ContainerScreens can share the same Window."""
    cs1 = ContainerScreen(parent=window)
    cs2 = ContainerScreen(parent=window)
    cs3 = ContainerScreen(parent=window)

    assert cs1.get_window() is window
    assert cs2.get_window() is window
    assert cs3.get_window() is window
