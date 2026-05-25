from typing import Any, Callable
from unittest.mock import MagicMock

import pyglet.clock
import pytest
from pyglet.window import key
from pytest_mock import MockerFixture

from sonartk.ui.element.element import Element
from sonartk.ui.screen.dialog import Dialog
from sonartk.ui.screen.screen import Screen
from sonartk.ui.window import Window
from sonartk.util.state_machine import EmptyState, StateMachine
from test.mocks.mock_pyglet_window import MockPygletWindow


class MockElement(Element[str]):
    """Mock element for testing."""

    def __init__(self, parent: Any, label: str = "Test") -> None:
        super().__init__(
            parent, label, "button", "test_value", use_key_handler=False
        )
        self.reset_called: bool = False

    def bind_keys(self) -> None:
        pass

    def reset(self) -> None:
        self.reset_called = True


class _FakeScreen(Screen):
    """Test screen class for testing Dialog."""

    def __init__(self, parent: Window) -> None:
        super().__init__(parent)

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


@pytest.fixture
def window(mocker: MockerFixture) -> Window:
    """Create a Window fixture."""
    window = Window()
    window.pyglet_window = mocker.MagicMock(spec=MockPygletWindow)
    window.handler_stack = []  # type: ignore[attr-defined]
    window.push_window_handlers = mocker.MagicMock()  # type: ignore[method-assign]
    window.pop_window_handlers = mocker.MagicMock()  # type: ignore[method-assign]
    return window


@pytest.fixture
def parent_screen(window: Window) -> _FakeScreen:
    """Create a parent screen fixture."""
    return _FakeScreen(window)


@pytest.fixture
def dialog(parent_screen: _FakeScreen) -> Dialog:
    """Create a Dialog fixture."""
    return Dialog(parent_screen)


# Initialization Tests


def test_init_sets_parent(parent_screen: _FakeScreen, dialog: Dialog) -> None:
    """Test that __init__ sets parent correctly."""
    assert dialog.parent == parent_screen


def test_init_creates_empty_original_caption(dialog: Dialog) -> None:
    """Test that __init__ creates empty original_caption."""
    assert dialog.original_caption == ""


def test_init_creates_empty_original_state_key(dialog: Dialog) -> None:
    """Test that __init__ creates empty original_state_key."""
    assert dialog.original_state_key == ""


def test_init_inherits_from_container_screen(dialog: Dialog) -> None:
    """Test that Dialog inherits from ContainerScreen."""
    from sonartk.ui.screen.container_screen import ContainerScreen

    assert isinstance(dialog, ContainerScreen)


def test_init_creates_state_machine(dialog: Dialog) -> None:
    """Test that __init__ creates a state_machine."""
    assert isinstance(dialog.state_machine, StateMachine)


# open_dialog Tests


def test_open_dialog_saves_original_state_key(
    mocker: MockerFixture, parent_screen: _FakeScreen, dialog: Dialog
) -> None:
    """Test that open_dialog saves the original state key."""
    parent_screen.state_key = "original_state"
    parent_screen.state_machine.current_state.state_key = "original_state"
    mocker.patch.object(pyglet.clock, "schedule_once")

    dialog.open_dialog("Test")

    assert dialog.original_state_key == "original_state"


def test_open_dialog_adds_to_parent_state_machine(
    mocker: MockerFixture, parent_screen: _FakeScreen, dialog: Dialog
) -> None:
    """Test that open_dialog adds dialog to parent state machine."""
    parent_screen.state_machine.current_state.state_key = "original_state"
    mock_add = mocker.patch.object(parent_screen, "add")
    mocker.patch.object(pyglet.clock, "schedule_once")

    dialog.open_dialog("Test")

    # Should call parent.add with dialog-{caption}-{count} key
    assert mock_add.call_count == 1
    call_args = mock_add.call_args[0]
    assert call_args[0].startswith("dialog-Test-")
    assert call_args[1] == dialog


def test_open_dialog_saves_original_caption(
    mocker: MockerFixture, parent_screen: _FakeScreen, dialog: Dialog
) -> None:
    """Test that open_dialog saves the original caption."""
    dialog.caption = "Original Caption"
    parent_screen.state_machine.current_state.state_key = "original_state"
    mocker.patch.object(pyglet.clock, "schedule_once")

    dialog.open_dialog("Test")

    assert dialog.original_caption == "Original Caption"


def test_open_dialog_sets_new_caption(
    mocker: MockerFixture, parent_screen: _FakeScreen, dialog: Dialog
) -> None:
    """Test that open_dialog sets new caption."""
    parent_screen.state_machine.current_state.state_key = "original_state"
    mocker.patch.object(pyglet.clock, "schedule_once")

    dialog.open_dialog("Test")

    assert dialog.caption == "Test Dialog"


def test_open_dialog_schedules_state_change(
    mocker: MockerFixture, parent_screen: _FakeScreen, dialog: Dialog
) -> None:
    """Test that open_dialog schedules state change."""
    parent_screen.state_machine.current_state.state_key = "original_state"
    dialog.state_key = "dialog_state"
    mock_schedule = mocker.patch.object(pyglet.clock, "schedule_once")

    dialog.open_dialog("Test")

    # Should schedule change to dialog state with 0.3 second delay
    assert mock_schedule.call_count == 1
    assert mock_schedule.call_args[0][1] == 0.3


def test_open_dialog_increments_count(
    mocker: MockerFixture, parent_screen: _FakeScreen, dialog: Dialog
) -> None:
    """Test that open_dialog increments count based on parent state machine size."""
    parent_screen.state_machine.current_state.state_key = "original_state"
    parent_screen.add("state1", MagicMock())
    parent_screen.add("state2", MagicMock())
    mock_add = mocker.patch.object(parent_screen, "add")
    mocker.patch.object(pyglet.clock, "schedule_once")

    dialog.open_dialog("Test")

    # Count should be size + 1 = 2 + 1 = 3
    call_args = mock_add.call_args[0]
    assert call_args[0] == "dialog-Test-3"


# bind_keys Tests


def test_bind_keys_calls_super(mocker: MockerFixture, dialog: Dialog) -> None:
    """Test that bind_keys calls super().bind_keys()."""
    mock_super = mocker.patch(
        "sonartk.ui.screen.container_screen.ContainerScreen.bind_keys"
    )

    dialog.bind_keys()

    mock_super.assert_called_once()


def test_bind_keys_registers_escape(dialog: Dialog) -> None:
    """Test that bind_keys registers ESCAPE key."""
    key_handler = dialog.key_handler
    escape_key = None
    for k in key_handler.registered_key_presses.keys():
        if k.symbol == key.ESCAPE and k.modifiers == 0:
            escape_key = k
            break

    assert escape_key is not None, "ESCAPE key should be registered"
    callback, _ = key_handler.registered_key_presses[escape_key]
    assert callback.callback == dialog.close


def test_bind_keys_escape_callback_is_close_method(dialog: Dialog) -> None:
    """Test that ESCAPE key callback is dialog.close."""
    key_handler = dialog.key_handler
    for k, (callback, _) in key_handler.registered_key_presses.items():
        if k.symbol == key.ESCAPE and k.modifiers == 0:
            assert callback.callback == dialog.close
            return
    pytest.fail("ESCAPE key not registered")


# reset Tests


def test_reset_calls_reset_on_all_elements(dialog: Dialog) -> None:
    """Test that reset calls reset on all elements."""
    element1 = MockElement(dialog, "Element1")
    element2 = MockElement(dialog, "Element2")
    element3 = MockElement(dialog, "Element3")

    dialog.add("el1", element1)  # type: ignore[arg-type]
    dialog.add("el2", element2)  # type: ignore[arg-type]
    dialog.add("el3", element3)  # type: ignore[arg-type]

    dialog.reset()

    assert element1.reset_called
    assert element2.reset_called
    assert element3.reset_called


def test_reset_with_no_elements(dialog: Dialog) -> None:
    """Test that reset works with no elements."""
    # Should not raise an exception
    dialog.reset()


def test_reset_with_single_element(dialog: Dialog) -> None:
    """Test that reset works with single element."""
    element = MockElement(dialog, "Element")
    dialog.add("el", element)  # type: ignore[arg-type]

    dialog.reset()

    assert element.reset_called


# close Tests


def test_close_calls_screen_close(
    mocker: MockerFixture, dialog: Dialog
) -> None:
    """Test that close calls Screen.close() not ContainerScreen.close()."""
    mock_screen_close = mocker.patch("sonartk.ui.screen.screen.Screen.close")
    mocker.patch.object(pyglet.clock, "schedule_once")
    mocker.patch.object(dialog, "exit")

    dialog.close()

    mock_screen_close.assert_called_once_with(dialog)


def test_close_resets_position(mocker: MockerFixture, dialog: Dialog) -> None:
    """Test that close resets position to 0."""
    dialog.position = 5
    mocker.patch.object(pyglet.clock, "schedule_once")
    mocker.patch.object(dialog, "exit")

    dialog.close()

    assert dialog.position == 0


def test_close_calls_reset(mocker: MockerFixture, dialog: Dialog) -> None:
    """Test that close calls reset."""
    mock_reset = mocker.patch.object(dialog, "reset")
    mocker.patch.object(pyglet.clock, "schedule_once")
    mocker.patch.object(dialog, "exit")

    dialog.close()

    mock_reset.assert_called_once()


def test_close_restores_original_caption(
    mocker: MockerFixture, dialog: Dialog
) -> None:
    """Test that close restores original caption."""
    dialog.original_caption = "Original Caption"
    dialog.caption = "Test Dialog"
    mocker.patch.object(pyglet.clock, "schedule_once")
    mocker.patch.object(dialog, "exit")

    dialog.close()

    assert dialog.caption == "Original Caption"


def test_close_schedules_reset_states(
    mocker: MockerFixture, dialog: Dialog
) -> None:
    """Test that close schedules _reset_states."""
    mock_schedule = mocker.patch.object(pyglet.clock, "schedule_once")
    mocker.patch.object(dialog, "exit")

    dialog.close()

    assert mock_schedule.call_count == 1
    # Check that _reset_states is scheduled
    assert mock_schedule.call_args[0][1] == 0.3


def test_close_returns_true(mocker: MockerFixture, dialog: Dialog) -> None:
    """Test that close returns True."""
    mocker.patch.object(pyglet.clock, "schedule_once")
    mocker.patch.object(dialog, "exit")

    result = dialog.close()

    assert result is True


# _reset_states Tests


def test_reset_states_removes_from_parent(
    mocker: MockerFixture, parent_screen: _FakeScreen, dialog: Dialog
) -> None:
    """Test that _reset_states removes dialog from parent."""
    dialog.state_key = "dialog_key"
    mock_remove = mocker.patch.object(parent_screen, "remove")
    mocker.patch.object(dialog, "exit")
    mocker.patch.object(parent_screen.state_machine, "change")

    dialog._reset_states()

    mock_remove.assert_called_once_with("dialog_key")


def test_reset_states_sets_empty_state(
    mocker: MockerFixture, parent_screen: _FakeScreen, dialog: Dialog
) -> None:
    """Test that _reset_states sets current_state to EmptyState."""
    dialog.state_key = "dialog_key"
    mocker.patch.object(parent_screen, "remove")
    mocker.patch.object(dialog, "exit")
    mocker.patch.object(parent_screen.state_machine, "change")

    dialog._reset_states()

    assert isinstance(dialog.state_machine.current_state, EmptyState)


def test_reset_states_calls_exit(
    mocker: MockerFixture, parent_screen: _FakeScreen, dialog: Dialog
) -> None:
    """Test that _reset_states calls exit."""
    dialog.state_key = "dialog_key"
    mocker.patch.object(parent_screen, "remove")
    mock_exit = mocker.patch.object(dialog, "exit")
    mocker.patch.object(parent_screen.state_machine, "change")

    dialog._reset_states()

    mock_exit.assert_called_once()


def test_reset_states_changes_parent_state(
    mocker: MockerFixture, parent_screen: _FakeScreen, dialog: Dialog
) -> None:
    """Test that _reset_states changes parent state back to original."""
    dialog.state_key = "dialog_key"
    dialog.original_state_key = "original_state"
    mocker.patch.object(parent_screen, "remove")
    mocker.patch.object(dialog, "exit")
    mock_change = mocker.patch.object(parent_screen.state_machine, "change")

    dialog._reset_states()

    mock_change.assert_called_once_with("original_state", False)


def test_reset_states_changes_with_interrupt_false(
    mocker: MockerFixture, parent_screen: _FakeScreen, dialog: Dialog
) -> None:
    """Test that _reset_states changes state with interrupt_speech=False."""
    dialog.state_key = "dialog_key"
    dialog.original_state_key = "original_state"
    mocker.patch.object(parent_screen, "remove")
    mocker.patch.object(dialog, "exit")
    mock_change = mocker.patch.object(parent_screen.state_machine, "change")

    dialog._reset_states()

    # Second argument should be False
    assert mock_change.call_args[0][1] is False


# Integration Tests


def test_full_dialog_lifecycle(
    mocker: MockerFixture, parent_screen: _FakeScreen, dialog: Dialog
) -> None:
    """Test complete dialog lifecycle: open -> close."""
    parent_screen.state_machine.current_state.state_key = "original_state"
    dialog.caption = "Original"
    element = MockElement(dialog, "Element")
    dialog.add("el", element)  # type: ignore[arg-type]

    mocker.patch.object(pyglet.clock, "schedule_once")
    mocker.patch.object(parent_screen, "add")
    mocker.patch.object(parent_screen, "remove")
    mocker.patch.object(dialog, "exit")

    # Open dialog
    dialog.open_dialog("Test")
    assert dialog.caption == "Test Dialog"
    assert dialog.original_caption == "Original"

    # Close dialog
    dialog.close()
    assert dialog.caption == "Original"
    assert dialog.position == 0
    assert element.reset_called


def test_dialog_with_multiple_elements(
    mocker: MockerFixture, dialog: Dialog
) -> None:
    """Test dialog with multiple elements."""
    element1 = MockElement(dialog, "Element1")
    element2 = MockElement(dialog, "Element2")
    element3 = MockElement(dialog, "Element3")

    dialog.add("el1", element1)  # type: ignore[arg-type]
    dialog.add("el2", element2)  # type: ignore[arg-type]
    dialog.add("el3", element3)  # type: ignore[arg-type]

    mocker.patch.object(pyglet.clock, "schedule_once")
    mocker.patch.object(dialog, "exit")

    dialog.close()

    assert element1.reset_called
    assert element2.reset_called
    assert element3.reset_called


def test_dialog_inherits_container_screen_methods(dialog: Dialog) -> None:
    """Test that Dialog has ContainerScreen methods."""
    assert hasattr(dialog, "next_element")
    assert hasattr(dialog, "previous_element")
    assert hasattr(dialog, "setup")
    assert hasattr(dialog, "update")


def test_dialog_key_handler_has_tab_keys(dialog: Dialog) -> None:
    """Test that Dialog inherits TAB navigation from ContainerScreen."""
    key_handler = dialog.key_handler
    tab_found = False
    shift_tab_found = False

    for k in key_handler.registered_key_presses.keys():
        if k.symbol == key.TAB and k.modifiers == 0:
            tab_found = True
        if k.symbol == key.TAB and k.modifiers == key.MOD_SHIFT:
            shift_tab_found = True

    assert tab_found, "TAB key should be registered from ContainerScreen"
    assert (
        shift_tab_found
    ), "SHIFT+TAB should be registered from ContainerScreen"


def test_open_dialog_multiple_times(
    mocker: MockerFixture, parent_screen: _FakeScreen
) -> None:
    """Test opening multiple dialogs increments count correctly."""
    parent_screen.state_machine.current_state.state_key = "original_state"
    mock_add = mocker.patch.object(parent_screen, "add")
    mocker.patch.object(pyglet.clock, "schedule_once")

    dialog1 = Dialog(parent_screen)
    dialog1.open_dialog("First")

    dialog2 = Dialog(parent_screen)
    dialog2.open_dialog("Second")

    # Verify both dialogs were added with incrementing counts
    assert mock_add.call_count == 2


def test_close_without_exit_mocked(
    mocker: MockerFixture, parent_screen: _FakeScreen, dialog: Dialog
) -> None:
    """Test close doesn't fail when exit is mocked."""
    mocker.patch.object(dialog.get_window(), "pop_window_handlers")
    mocker.patch.object(pyglet.clock, "schedule_once")

    result = dialog.close()

    assert result is True
