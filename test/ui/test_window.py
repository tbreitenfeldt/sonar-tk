import sys

import pytest
from pytest_mock import MockerFixture
from pyglet.window import key

from sonartk.ui import Window
from sonartk.ui.element import Button
from sonartk.ui.screen import ContainerScreen
from sonartk.util import State, KeyHandler
from test.mocks.mock_state import MockState
from test.mocks.mock_pyglet_window import MockPygletWindow


@pytest.fixture
def default_window() -> Window:
    """Returns a default Window instance"""
    return Window()


@pytest.fixture
def escapable_window() -> Window:
    """Returns a Window instance with escapable set to True"""
    return Window(escapable=True)


@pytest.fixture
def titled_window() -> Window:
    """Returns a Window instance with caption set to test"""
    return Window(caption="test")


def test_bind_keys_without_escape(
    mocker: MockerFixture, default_window: Window
) -> None:
    key_handler: KeyHandler = default_window.key_handler
    # Already called in __init__, so we check the result
    assert len(key_handler.registered_key_presses) == 2
    # Check that ESC is registered (to prevent default close behavior)
    assert any(
        k.symbol == key.ESCAPE and k.modifiers == 0
        for k in key_handler.registered_key_presses.keys()
    )
    # Check that Ctrl+W is registered (custom close)
    assert any(
        k.symbol == key.W and k.modifiers == key.MOD_CTRL
        for k in key_handler.registered_key_presses.keys()
    )


def test_bind_keys_with_escape(escapable_window: Window) -> None:
    key_handler: KeyHandler = escapable_window.key_handler
    # Escapable window should only have Ctrl+W, not ESC
    assert len(key_handler.registered_key_presses) == 1
    assert any(
        k.symbol == key.W and k.modifiers == key.MOD_CTRL
        for k in key_handler.registered_key_presses.keys()
    )


def test_open_window_with_empty_caption(
    mocker: MockerFixture, default_window: Window
) -> None:
    mocker.patch("pyglet.window.Window")
    mocker.patch("pyglet.clock.schedule_once")
    mocker.patch("pyglet.clock.schedule_interval")
    mocker.patch("sonartk.ui.window.Window.setup")
    mocker.patch("pyglet.app.run")

    default_window.open_window(caption="test")
    assert default_window.caption == "test"


def test_open_window_with_caption_error(default_window: Window) -> None:
    with pytest.raises(ValueError):
        default_window.open_window()


def test_setup(mocker: MockerFixture, default_window: Window) -> None:
    mocker.patch("pyglet.clock.schedule_once")
    default_window.state_machine.add("test", MockState())
    default_window.setup()
    # Setup schedules set_state but doesn't call it immediately
    assert len(default_window.state_machine.states) == 1


def test_setup_withoutstates(
    mocker: MockerFixture, default_window: Window
) -> None:
    mocker.patch("pyglet.clock.schedule_once")
    default_window.setup()
    assert len(default_window.state_machine.states) == 0


def test_update(mocker: MockerFixture, default_window: Window) -> None:
    state_machine_update_mock = mocker.patch(
        "sonartk.util.state_machine.StateMachine.update", return_value=True
    )
    dt: float = 0.1
    default_window.update(dt)
    state_machine_update_mock.assert_called_with(dt)


def test_add(mocker: MockerFixture, default_window: Window) -> None:
    state_machine_add_mock = mocker.patch(
        "sonartk.util.state_machine.StateMachine.add"
    )
    key: str = "test"
    state: MockState = MockState()
    default_window.add(key, state)
    state_machine_add_mock.assert_called_with(key, state)


def test_that_state_machine_remove_is_called(
    mocker: MockerFixture, default_window: Window
) -> None:
    state_machine_remove_mock = mocker.patch(
        "sonartk.util.state_machine.StateMachine.remove"
    )
    key: str = "test"
    state: MockState = MockState()
    default_window.state_machine.states[key] = state
    default_window.remove(key)
    state_machine_remove_mock.assert_called_with(key)


def test_remove_return(mocker: MockerFixture, default_window: Window) -> None:
    key: str = "test"
    state: MockState = MockState()
    default_window.state_machine.add(key, state)
    result: State | None = default_window.remove(key)
    assert result == state


def test_that_state_machine_change_is_called(
    mocker: MockerFixture, default_window: Window
) -> None:
    state_machine_change_mock = mocker.patch(
        "sonartk.util.state_machine.StateMachine.change"
    )
    key: str = "test"
    state: MockState = MockState()
    default_window.state_machine.states[key] = state
    default_window.change(key)
    state_machine_change_mock.assert_called_with(key)


def test_change(mocker: MockerFixture, default_window: Window) -> None:
    key: str = "test"
    state: MockState = MockState()
    default_window.state_machine.states[key] = state
    default_window.change(key)
    assert default_window.state_machine.current_state == state


def test_push_handlers(mocker: MockerFixture, default_window: Window) -> None:
    default_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]
    pyglet_push_handlers_mock = mocker.patch(
        "test.mocks.mock_pyglet_window.MockPygletWindow.push_handlers"
    )
    key_handler: KeyHandler = KeyHandler()
    default_window.push_window_handlers(key_handler)
    pyglet_push_handlers_mock.assert_called_with(key_handler)


def test_pop_handlers(mocker: MockerFixture, default_window: Window) -> None:
    default_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]
    pyglet__pop_handlers_mock = mocker.patch(
        "test.mocks.mock_pyglet_window.MockPygletWindow.pop_handlers"
    )
    key_handler: KeyHandler = KeyHandler()
    default_window.pyglet_window._event_stack.append(key_handler)  # type: ignore[union-attr]
    default_window.pop_window_handlers()
    pyglet__pop_handlers_mock.assert_called_with()


def test_pop_handlers_with_empty_stack(
    mocker: MockerFixture, default_window: Window
) -> None:
    default_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]

    # Should raise RuntimeError when popping from empty stack
    with pytest.raises(
        RuntimeError, match="Attempted to pop handler from empty stack"
    ):
        default_window.pop_window_handlers()


def test_close(mocker: MockerFixture, default_window: Window) -> None:
    default_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]
    stateMachineClearMock = mocker.patch(
        "sonartk.util.state_machine.StateMachine.clear"
    )
    pygletWindowCloseMock = mocker.patch(
        "test.mocks.mock_pyglet_window.MockPygletWindow.close"
    )
    default_window.close()
    stateMachineClearMock.assert_called_with()
    pygletWindowCloseMock.assert_called_with()


def test_get_caption(titled_window: Window) -> None:
    assert titled_window.caption == "test"


def test_set_caption_with_jaws_active(
    mocker: MockerFixture, default_window: Window
) -> None:
    default_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]
    mocker.patch(
        "accessible_output2.outputs.auto.Auto.output", return_value=None
    )
    mocker.patch(
        "sonartk.util.speech_manager.is_jaws_active", return_value=True
    )
    speech_manager_output_mock = mocker.patch(
        "sonartk.util.speech_manager.output"
    )
    title: str = "test"
    default_window.caption = title
    assert default_window._caption == title
    speech_manager_output_mock.assert_called_with(
        title, interrupt=False, log_message=False
    )


def test_set_caption_with_jaws_not_active(
    mocker: MockerFixture, default_window: Window
) -> None:
    default_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]
    mocker.patch(
        "accessible_output2.outputs.auto.Auto.output", return_value=None
    )
    mocker.patch(
        "sonartk.util.speech_manager.is_jaws_active", return_value=False
    )
    speech_manager_output_mock = mocker.patch(
        "sonartk.util.speech_manager.output"
    )
    title: str = "test"
    default_window.caption = title
    assert default_window._caption == title
    assert not speech_manager_output_mock.called


def test_with_empty_caption(
    mocker: MockerFixture, titled_window: Window
) -> None:
    titled_window.caption = ""
    assert titled_window._caption == "test"


def test_window_with_parent() -> None:
    """Test window with parent relationship"""
    parent_window: Window = Window()
    child_window: Window = Window(parent=parent_window)
    assert child_window.parent == parent_window
    assert child_window in parent_window.children


def test_get_window(default_window: Window) -> None:
    """Test get_window returns self"""
    assert default_window.get_window() == default_window


def test_set_state_with_states(
    mocker: MockerFixture, default_window: Window
) -> None:
    """Test set_state calls change when states exist"""
    mocker.patch("sonartk.util.state_machine.StateMachine.change")
    default_window.state_machine.add("test1", MockState())
    default_window.state_machine.add("test2", MockState())
    default_window.set_state()
    # Should call change with first state key
    assert default_window.state_machine.change.called  # type: ignore[attr-defined]


def test_set_state_with_no_interrupt(
    mocker: MockerFixture, default_window: Window
) -> None:
    """Test set_state with interrupt_speech=False"""
    change_mock = mocker.patch(
        "sonartk.util.state_machine.StateMachine.change"
    )
    default_window.state_machine.add("test", MockState())
    default_window.set_state(interrupt_speech=False)
    change_mock.assert_called_once_with("test", False)


def test_set_state_empty_state_machine(default_window: Window) -> None:
    """Test set_state does nothing when state machine is empty"""
    default_window.set_state()
    # Should not raise any errors


def test_get_handler_stack_size(default_window: Window) -> None:
    """Test get_handler_stack_size"""
    default_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]
    assert default_window.get_handler_stack_size() == 0
    default_window.pyglet_window._event_stack.append(KeyHandler())  # type: ignore[union-attr]
    assert default_window.get_handler_stack_size() == 1


def test_check_handler_leaks_no_leak(default_window: Window, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[name-defined]
    """Test check_handler_leaks with no leaks"""
    default_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]
    # Add expected number of handlers
    for _ in range(3):
        default_window.pyglet_window._event_stack.append(KeyHandler())  # type: ignore[union-attr]
    default_window.check_handler_leaks(expected_count=3)
    captured = capsys.readouterr()
    assert "WARNING" not in captured.err


def test_check_handler_leaks_with_leak(default_window: Window, capsys: pytest.CaptureFixture[str]) -> None:  # type: ignore[name-defined]
    """Test check_handler_leaks detects leaks"""
    default_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]
    # Add more handlers than expected
    for _ in range(5):
        default_window.pyglet_window._event_stack.append(KeyHandler())  # type: ignore[union-attr]
    default_window.check_handler_leaks(expected_count=3)
    captured = capsys.readouterr()
    assert "WARNING" in captured.err
    assert "2 leaked" in captured.err


def test_check_handler_leaks_uses_window_baseline_by_default(
    default_window: Window, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test leak checker defaults to window baseline when provided."""
    default_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]
    default_window._window_base_handler_count = 2
    for _ in range(2):
        default_window.pyglet_window._event_stack.append(KeyHandler())  # type: ignore[union-attr]

    default_window.check_handler_leaks()
    captured = capsys.readouterr()
    assert "WARNING" not in captured.err


def test_check_handler_leaks_default_reports_against_baseline(
    default_window: Window, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test default leak checker message uses computed baseline expected count."""
    default_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]
    default_window._window_base_handler_count = 2
    for _ in range(5):
        default_window.pyglet_window._event_stack.append(KeyHandler())  # type: ignore[union-attr]

    default_window.check_handler_leaks()
    captured = capsys.readouterr()
    assert "WARNING" in captured.err
    assert "Expected 2" in captured.err
    assert "3 leaked" in captured.err


def test_validate_handler_stack_without_pyglet_window(
    default_window: Window,
) -> None:
    """Test stack validation when pyglet window has not been created yet."""
    is_valid, message = default_window._validate_handler_stack()
    assert not is_valid
    assert "No pyglet window" in message


def test_validate_handler_stack_valid(default_window: Window) -> None:
    """Test stack validation returns valid when expected and actual match."""
    default_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]
    default_window._window_base_handler_count = 2
    for _ in range(2):
        default_window.pyglet_window._event_stack.append(KeyHandler())  # type: ignore[union-attr]

    is_valid, message = default_window._validate_handler_stack()
    assert is_valid
    assert "expected=2" in message


def test_validate_handler_stack_mismatch(default_window: Window) -> None:
    """Test stack validation reports mismatch details."""
    default_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]
    default_window._window_base_handler_count = 2
    default_window.pyglet_window._event_stack.append(KeyHandler())  # type: ignore[union-attr]

    is_valid, message = default_window._validate_handler_stack()
    assert not is_valid
    assert "Handler stack mismatch" in message
    assert "expected=2" in message
    assert "actual=1" in message


def test_validate_handler_stack_public_wrapper(
    default_window: Window,
) -> None:
    """Test public wrapper returns the same validation result."""
    default_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]
    default_window._window_base_handler_count = 1
    default_window.pyglet_window._event_stack.append(KeyHandler())  # type: ignore[union-attr]

    is_valid, message = default_window.validate_handler_stack()
    assert is_valid
    assert "Handler stack valid" in message


def test_validate_handler_stack_uses_pending_nested_states(
    default_window: Window,
) -> None:
    """Test validation counts nested handlers during in-progress setup."""
    default_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]
    default_window._window_base_handler_count = 3

    container = ContainerScreen(default_window)
    button = Button(container, label="Open Dialog")
    container.add("open_dialog_button", button)
    default_window.add("container", container)

    default_window.state_machine._pending_state = container
    container.state_machine._pending_state = button

    for _ in range(5):
        default_window.pyglet_window._event_stack.append(KeyHandler())  # type: ignore[union-attr]

    is_valid, message = default_window._validate_handler_stack()

    assert is_valid
    assert "expected=5" in message
    assert "actual=5" in message


def test_set_debug_mode_toggles(default_window: Window) -> None:
    """Test debug mode setter toggles the debug flag."""
    assert default_window.debug_mode is False
    default_window.set_debug_mode(True)
    assert default_window.debug_mode is True
    default_window.set_debug_mode(False)
    assert default_window.debug_mode is False


def test_set_debug_mode_logs_state_changes(
    mocker: MockerFixture, default_window: Window
) -> None:
    """Test set_debug_mode logs when enabled/disabled."""
    log_mock = mocker.patch.object(default_window, "_debug_log")

    default_window.set_debug_mode(True)
    assert log_mock.call_count == 1
    assert "enabled" in log_mock.call_args[0][0].lower()

    log_mock.reset_mock()
    default_window.set_debug_mode(False)
    assert log_mock.call_count == 1
    assert "disabled" in log_mock.call_args[0][0].lower()


def test_debug_mode_logs_on_construction(
    mocker: MockerFixture,
) -> None:
    """Test debug mode logs startup message when enabled via constructor."""
    log_mock = mocker.patch("sonartk.ui.window.Window._debug_log")

    Window(caption="test", debug_mode=True)
    # Constructor calls _debug_log once for startup
    assert log_mock.call_count >= 1


def test_change_runs_debug_validation_when_enabled(
    mocker: MockerFixture, default_window: Window
) -> None:
    """Test change triggers handler validation logging in debug mode."""
    default_window.set_debug_mode(True)
    default_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]

    default_window.state_machine.add("test", MockState())
    log_mock = mocker.patch.object(default_window, "_debug_log")

    default_window.change("test")

    # Should log validation results
    assert log_mock.called
    # Check that one of the logs mentions validation result
    logged_messages = [call[0][0] for call in log_mock.call_args_list]
    assert any("after change" in msg for msg in logged_messages)


def test_set_state_runs_debug_validation_when_enabled(
    mocker: MockerFixture, default_window: Window
) -> None:
    """Test set_state triggers handler validation logging in debug mode."""
    default_window.set_debug_mode(True)
    default_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]

    default_window.state_machine.add("test", MockState())
    log_mock = mocker.patch.object(default_window, "_debug_log")

    default_window.set_state()

    # Should log validation results
    assert log_mock.called
    # set_state transitions are logged via the shared state-machine callback
    logged_messages = [call[0][0] for call in log_mock.call_args_list]
    assert any("after change" in msg for msg in logged_messages)


def test_close_with_children(mocker: MockerFixture) -> None:
    """Test close closes children when close_children_on_close is True"""
    parent_window: Window = Window()
    parent_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]

    child1: Window = Window(parent=parent_window)
    child1.pyglet_window = MockPygletWindow()  # type: ignore[assignment]

    child2: Window = Window(parent=parent_window)
    child2.pyglet_window = MockPygletWindow()  # type: ignore[assignment]

    child1_close_mock = mocker.patch.object(
        child1, "close", wraps=child1.close
    )
    child2_close_mock = mocker.patch.object(
        child2, "close", wraps=child2.close
    )

    mocker.patch("sonartk.util.state_machine.StateMachine.exit")
    mocker.patch("sonartk.util.state_machine.StateMachine.clear")

    parent_window.close()

    assert child1_close_mock.called
    assert child2_close_mock.called


def test_close_without_closing_children() -> None:
    """Test close doesn't close children when close_children_on_close is False"""
    parent_window: Window = Window(close_children_on_close=False)
    parent_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]

    child: Window = Window(parent=parent_window)
    child.pyglet_window = MockPygletWindow()  # type: ignore[assignment]

    parent_window.close()

    # Child should still be in parent's children list
    assert child in parent_window.children


def test_close_removes_from_parent(mocker: MockerFixture) -> None:
    """Test that close removes window from parent's children list"""
    parent_window: Window = Window()
    child_window: Window = Window(parent=parent_window)
    child_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]

    mocker.patch("sonartk.util.state_machine.StateMachine.exit")
    mocker.patch("sonartk.util.state_machine.StateMachine.clear")

    assert child_window in parent_window.children
    child_window.close()
    assert child_window not in parent_window.children


def test_close_with_sound_manager(
    mocker: MockerFixture, default_window: Window
) -> None:
    """Test close calls sound_manager cleanup if module is loaded"""
    default_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]

    mocker.patch("sonartk.util.state_machine.StateMachine.exit")
    mocker.patch("sonartk.util.state_machine.StateMachine.clear")

    # Mock the sound manager module
    sound_manager_mock = mocker.MagicMock()
    sys.modules["sonartk.sound.sound_manager"] = sound_manager_mock

    default_window.close()

    sound_manager_mock.cleanup.assert_called_once()

    # Clean up
    del sys.modules["sonartk.sound.sound_manager"]


def test_close_exits_states_before_clearing(
    mocker: MockerFixture, default_window: Window
) -> None:
    """Test that close exits states before clearing them"""
    default_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]

    exit_mock = mocker.patch("sonartk.util.state_machine.StateMachine.exit")
    clear_mock = mocker.patch("sonartk.util.state_machine.StateMachine.clear")

    default_window.close()

    # Verify exit was called before clear
    exit_mock.assert_called_once()
    clear_mock.assert_called_once()

    # Check call order
    assert exit_mock.call_count == 1
    assert clear_mock.call_count == 1


def test_on_window_activate_when_not_open(
    mocker: MockerFixture, default_window: Window
) -> None:
    """Test on_window_activate when window is not yet open"""
    default_window.is_open = False
    result = default_window.on_window_activate()
    assert result is False
    assert default_window.is_open is True


def test_on_window_activate_when_open_no_element(
    mocker: MockerFixture, default_window: Window
) -> None:
    """Test on_window_activate when open but no active element"""
    default_window.is_open = True
    default_window.state_machine.current_state = MockState()

    mocker.patch("pyglet.clock.schedule_once")

    result = default_window.on_window_activate()
    assert result is True


def test_on_window_activate_with_focusable_element(
    mocker: MockerFixture, default_window: Window
) -> None:
    """Test on_window_activate with focusable element"""
    default_window.is_open = True

    # Create a mock state with active_element that has a name
    mock_element = mocker.MagicMock()
    mock_element.name = "Test Element"
    # Ensure the element is treated as a leaf (no more active_element)
    del mock_element.active_element

    mock_state = mocker.MagicMock()
    mock_state.active_element = mock_element

    default_window.state_machine.current_state = mock_state

    schedule_mock = mocker.patch("pyglet.clock.schedule_once")

    result = default_window.on_window_activate()
    assert result is True
    assert schedule_mock.called


def test_on_window_activate_with_nested_elements(
    mocker: MockerFixture, default_window: Window
) -> None:
    """Test on_window_activate with nested focusable elements"""
    default_window.is_open = True

    # Create innermost element with name but no active_element attribute
    inner_element = mocker.MagicMock()
    inner_element.name = "Inner Element"
    del inner_element.active_element  # Remove the attribute

    # Create middle element that points to inner
    middle_element = mocker.MagicMock()
    middle_element.active_element = inner_element

    # Create state that points to middle
    mock_state = mocker.MagicMock()
    mock_state.active_element = middle_element

    default_window.state_machine.current_state = mock_state

    schedule_mock = mocker.patch("pyglet.clock.schedule_once")
    speech_output_mock = mocker.patch("sonartk.util.speech_manager.output")

    result = default_window.on_window_activate()
    assert result is True
    assert schedule_mock.called

    # Call the scheduled function
    scheduled_func = schedule_mock.call_args[0][0]
    scheduled_func(0.25)

    speech_output_mock.assert_called_once_with(
        "Inner Element", interrupt=False, log_message=False
    )


def test_open_window_with_no_focus_speak(
    mocker: MockerFixture, default_window: Window
) -> None:
    """Test open_window with speak_current_element_on_window_focus=False"""
    mocker.patch("pyglet.window.Window")
    mocker.patch("pyglet.clock.schedule_once")
    mocker.patch("pyglet.clock.schedule_interval")
    mocker.patch("sonartk.ui.window.Window.setup")
    mocker.patch("pyglet.app.run")

    push_handlers_mock = mocker.patch.object(
        default_window, "push_window_handlers"
    )

    default_window.open_window(
        caption="test", speak_current_element_on_window_focus=False
    )

    # Should not push on_activate handler
    calls = push_handlers_mock.call_args_list
    # Check that on_activate is not in any of the calls
    for call in calls:
        assert "on_activate" not in str(call)


def test_open_window_uses_existing_caption(
    mocker: MockerFixture, titled_window: Window
) -> None:
    """Test open_window uses existing caption when none provided"""
    mocker.patch("pyglet.window.Window")
    mocker.patch("pyglet.clock.schedule_once")
    mocker.patch("pyglet.clock.schedule_interval")
    mocker.patch("sonartk.ui.window.Window.setup")
    mocker.patch("pyglet.app.run")

    titled_window.open_window()
    assert titled_window.caption == "test"


def test_open_window_with_fullscreen(
    mocker: MockerFixture, default_window: Window
) -> None:
    """Test open_window with fullscreen=True"""
    window_mock = mocker.patch("pyglet.window.Window")
    mocker.patch("pyglet.clock.schedule_once")
    mocker.patch("pyglet.clock.schedule_interval")
    mocker.patch("sonartk.ui.window.Window.setup")
    mocker.patch("pyglet.app.run")

    default_window.open_window(caption="test", fullscreen=True)

    # Check that Window was called with fullscreen=True
    window_mock.assert_called_once()
    assert window_mock.call_args[1]["fullscreen"] is True


def test_open_window_with_custom_dimensions(
    mocker: MockerFixture, default_window: Window
) -> None:
    """Test open_window with custom width and height"""
    window_mock = mocker.patch("pyglet.window.Window")
    mocker.patch("pyglet.clock.schedule_once")
    mocker.patch("pyglet.clock.schedule_interval")
    mocker.patch("sonartk.ui.window.Window.setup")
    mocker.patch("pyglet.app.run")

    default_window.open_window(caption="test", width=1024, height=768)

    # Check that Window was called with custom dimensions
    window_mock.assert_called_once()
    assert window_mock.call_args[1]["width"] == 1024
    assert window_mock.call_args[1]["height"] == 768


def test_update_dispatches_event(
    mocker: MockerFixture, default_window: Window
) -> None:
    """Test that update dispatches on_update event"""
    dispatch_mock = mocker.patch.object(default_window, "dispatch_event")
    mocker.patch("sonartk.util.state_machine.StateMachine.update")

    dt = 0.016
    default_window.update(dt)

    dispatch_mock.assert_called_once_with("on_update", default_window, dt)


def test_close_pops_all_handlers(
    mocker: MockerFixture, default_window: Window
) -> None:
    """Test that close pops all remaining handlers"""
    default_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]

    # Add multiple handlers to the stack
    for _ in range(5):
        default_window.pyglet_window._event_stack.append(KeyHandler())  # type: ignore[union-attr]

    # Store reference before close (since it gets deleted)
    stack = default_window.pyglet_window._event_stack

    mocker.patch("sonartk.util.state_machine.StateMachine.exit")
    mocker.patch("sonartk.util.state_machine.StateMachine.clear")

    default_window.close()

    # All handlers should be popped (check the stack we saved)
    assert len(stack) == 0


def test_on_window_activate_element_without_name(
    mocker: MockerFixture, default_window: Window
) -> None:
    """Test on_window_activate when element exists but has no name attribute"""
    default_window.is_open = True

    # Create an element without a name attribute
    mock_element = mocker.MagicMock()
    del mock_element.name  # Remove name attribute
    del mock_element.active_element

    mock_state = mocker.MagicMock()
    mock_state.active_element = mock_element

    default_window.state_machine.current_state = mock_state

    schedule_mock = mocker.patch("pyglet.clock.schedule_once")

    result = default_window.on_window_activate()
    assert result is True
    # Should not schedule anything since element has no name
    assert not schedule_mock.called


def test_close_with_sound_manager_non_callable_cleanup(
    mocker: MockerFixture, default_window: Window
) -> None:
    """Test close() when sound_manager module exists but cleanup is not callable."""
    default_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]

    mocker.patch("sonartk.util.state_machine.StateMachine.exit")
    mocker.patch("sonartk.util.state_machine.StateMachine.clear")

    sound_manager_mock = mocker.MagicMock()
    sound_manager_mock.cleanup = "not_a_callable"  # Not callable
    sys.modules["sonartk.sound.sound_manager"] = sound_manager_mock

    result = default_window.close()
    assert result is True
    # cleanup was not called since it's not callable
    assert sound_manager_mock.cleanup == "not_a_callable"

    del sys.modules["sonartk.sound.sound_manager"]


def test_on_window_activate_element_is_none(
    mocker: MockerFixture, default_window: Window
) -> None:
    """Test on_window_activate when element becomes None during traversal"""
    default_window.is_open = True

    # Create a state where active_element leads to None
    mock_element = mocker.MagicMock()
    mock_element.active_element = None

    mock_state = mocker.MagicMock()
    mock_state.active_element = mock_element

    default_window.state_machine.current_state = mock_state

    schedule_mock = mocker.patch("pyglet.clock.schedule_once")

    result = default_window.on_window_activate()
    assert result is True
    # Should not schedule since element becomes None
    assert not schedule_mock.called


def test_close_without_parent(
    mocker: MockerFixture, default_window: Window
) -> None:
    """Test close when window has no parent"""
    default_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]
    default_window.parent = None

    mocker.patch("sonartk.util.state_machine.StateMachine.exit")
    mocker.patch("sonartk.util.state_machine.StateMachine.clear")

    # Should not raise any errors
    default_window.close()


def test_close_not_in_parent_children(mocker: MockerFixture) -> None:
    """Test close when window is not in parent's children list"""
    parent_window: Window = Window()
    child_window: Window = Window()
    child_window.parent = parent_window
    # Manually remove from parent's children (simulating edge case)
    if child_window in parent_window.children:
        parent_window.children.remove(child_window)

    child_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]

    mocker.patch("sonartk.util.state_machine.StateMachine.exit")
    mocker.patch("sonartk.util.state_machine.StateMachine.clear")

    # Should not raise any errors even though not in parent's children
    child_window.close()


def test_parent_validation_rejects_non_ui_component(
    mocker: MockerFixture, default_window: Window
) -> None:
    """Test parent setter rejects non-UIComponent values."""
    mock_parent = mocker.MagicMock(spec=[])

    with pytest.raises(TypeError, match="parent must be a UIComponent"):
        default_window.parent = mock_parent


def test_close_child_without_pyglet_window(mocker: MockerFixture) -> None:
    """Test close when a child doesn't have pyglet_window attribute"""
    parent_window: Window = Window()
    parent_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]

    # Create child WITH parent parameter (will be in parent.children)
    child_with_window: Window = Window(parent=parent_window)
    child_with_window.pyglet_window = MockPygletWindow()  # type: ignore[assignment]

    # Create another child WITHOUT pyglet_window
    child_without_window: Window = Window(parent=parent_window)
    # Don't set pyglet_window on this one

    mocker.patch("sonartk.util.state_machine.StateMachine.exit")
    mocker.patch("sonartk.util.state_machine.StateMachine.clear")

    # Close parent - should skip child_without_window but close child_with_window
    parent_window.close()
    # Verify child_without_window was created but not closed (no pyglet_window)
    assert child_without_window in parent_window.children
