import sys
from typing import Callable, List, Union

import pyglet
import pytest
from pytest_mock import MockerFixture

from audio_ui import Window
from audio_ui import State
from audio_ui.utils import KeyHandler, Key
from audio_ui.utils import speech_manager

class MockState(State):

    def __init__(self, setup_value: bool = True, update_value: bool = True, exit_value: bool = True) -> None:
        self.setup_value: bool = setup_value
        self.update_value: bool = update_value
        self.exit_value: bool = exit_value

    def setup(self, change_state: Callable[[str, any], None], setup_value: bool = None) -> bool:
        return self.setup_value

    def update(self, delta_time: float) -> bool:
        return self.update_value

    def exit(self) -> bool:
        return self.exit_value


class MockPygletWindow:

    def __init__(self) -> None:
        self.caption: str = ""
        self._event_stack: List[any] = []

    def push_handlers(self, key_handler: KeyHandler) -> None:
        self._event_stack.append(key_handler)

    def pop_handlers(self) -> None:
        self._event_stack.pop(0)

    def set_caption(self, caption: str) -> None:
        self.caption = caption

    def close(self) -> None:
        pass


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

def test_bind_keys_without_escape(mocker: MockerFixture, default_window: Window):
    mocker.patch("audio_ui.window.Window.close", return_value=True)
    key_handler: KeyHandler = default_window.key_handler
    key_handler_add_key_press_mock = mocker.patch("audio_ui.utils.key_handler.KeyHandler.add_key_press")
    default_window.bind_keys()
    assert len(key_handler.registered_key_presses) == 3
    assert key_handler_add_key_press_mock.call_args_list[0][0][0]() == True
    assert key_handler_add_key_press_mock.call_args_list[1][0][0]() == True
    assert key_handler_add_key_press_mock.call_args_list[2][0][0]() == True

def test_bind_keys_with_escape(escapable_window: Window):
    key_handler: KeyHandler = escapable_window.key_handler
    assert len(key_handler.registered_key_presses) == 2

def test_open_window_with_empty_caption(mocker: MockerFixture, default_window: Window):
    speech_manager_silence_mock = mocker.patch("audio_ui.utils.speech_manager.silence")
    pyglet_schedule_once_mocker = mocker.patch("pyglet.clock.schedule_once")
    pyglet_schedule_interval_mock = mocker.patch("pyglet.clock.schedule_interval")
    window_setup_mock = mocker.patch("audio_ui.window.Window.setup")
    window_update_mock = mocker.patch("audio_ui.window.Window.update")
    mocker.patch("pyglet.app.run")
    default_window.open_window(caption="test")
    assert default_window.caption == "test"
    dt: float = 0.01

    # Test accessible_output2 silence calls used for silencing the screen reader so the title is not spoken automaticly.
    pyglet_schedule_once_mocker.call_args_list[0][0][0](dt)
    speech_manager_silence_mock.assert_called_with()
    pyglet_schedule_once_mocker.call_args_list[1][0][0](dt)
    speech_manager_silence_mock.assert_called_with()
    pyglet_schedule_once_mocker.call_args_list[2][0][0](dt)
    speech_manager_silence_mock.assert_called_with()
    pyglet_schedule_once_mocker.call_args_list[3][0][0](dt)
    speech_manager_silence_mock.assert_called_with()

    # test setup call
    pyglet_schedule_once_mocker.call_args_list[4][0][0](dt)
    window_setup_mock.assert_called_with()

    # test update call
    pyglet_schedule_interval_mock.call_args_list[0][0][0](dt)
    window_update_mock.assert_called_with(dt)

    assert len(default_window.pyglet_window._event_stack) == 1

def test_open_window_with_caption_error(default_window: Window):
    with pytest.raises(ValueError):
        default_window.open_window()

def test_setup(mocker: MockerFixture, default_window: Window):
    mocker.patch("accessible_output2.outputs.auto.Auto.output")
    starting_state: State = default_window.state_machine.current_state
    default_window.state_machine.add("test", MockState())
    default_window.setup()
    assert len(speech_manager.get_speech_history()) == 0
    assert len(default_window.state_machine.states) == 1
    assert starting_state.state_key != default_window.state_machine.current_state.state_key

def test_setup_withoutstates(mocker: MockerFixture, default_window: Window):
    mocker.patch("accessible_output2.outputs.auto.Auto.output", return_value=None)
    default_window.setup()
    assert len(speech_manager.get_speech_history()) == 0
    assert len(default_window.state_machine.states) == 0

def test_update(mocker: MockerFixture, default_window: Window):
    state_machine_update_mock = mocker.patch("audio_ui.state_machine.StateMachine.update", return_value=True)
    dt: float = 0.1
    default_window.update(dt)
    state_machine_update_mock.assert_called_with(dt)

def test_add(mocker: MockerFixture, default_window: Window):
    state_machine_add_mock = mocker.patch("audio_ui.state_machine.StateMachine.add")
    key: str = "test"
    state: MockState = MockState
    default_window.add(key, state)
    state_machine_add_mock.assert_called_with(key, state)

def test_that_state_machine_remove_is_called(mocker: MockerFixture, default_window: Window):
    state_machine_remove_mock = mocker.patch("audio_ui.state_machine.StateMachine.remove")
    key: str = "test"
    state: MockState = MockState()
    default_window.state_machine.states[key] =  state
    default_window.remove(key)
    state_machine_remove_mock.assert_called_with(key)

def test_remove_return(mocker: MockerFixture, default_window: Window):
    key: str = "test"
    state: MockState = MockState()
    default_window.state_machine.states[key] =  state
    result: State = default_window.remove(key)
    assert result == state

def test_that_state_machine_change_is_called(mocker: MockerFixture, default_window: Window):
    state_machine_change_mock = mocker.patch("audio_ui.state_machine.StateMachine.change")
    key: str = "test"
    state: MockState = MockState()
    default_window.state_machine.states[key] = state
    default_window.change(key)
    state_machine_change_mock.assert_called_with(key)

def test_change(mocker: MockerFixture, default_window: Window):
    key: str = "test"
    state: MockState = MockState()
    default_window.state_machine.states[key] = state
    default_window.change(key)
    assert default_window.state_machine.current_state == state

def test_push_handlers(mocker: MockerFixture, default_window: Window):
    default_window.pyglet_window = MockPygletWindow()
    pyglet_push_handlers_mock = mocker.patch("test.test_window.MockPygletWindow.push_handlers")
    key_handler: KeyHandler = KeyHandler()
    default_window.push_handlers(key_handler)
    pyglet_push_handlers_mock.assert_called_with(key_handler)

def test_pop_handlers(mocker: MockerFixture, default_window: Window):
    default_window.pyglet_window = MockPygletWindow()    
    pyglet__pop_handlers_mock = mocker.patch("test.test_window.MockPygletWindow.pop_handlers")
    key_handler: KeyHandler = KeyHandler()
    default_window.pyglet_window._event_stack.append(key_handler)
    default_window.pop_handlers()
    pyglet__pop_handlers_mock.assert_called_with()

def test_pop_handlers_with_empty_stack(mocker: MockerFixture, default_window: Window):
    default_window.pyglet_window = MockPygletWindow()    
    pyglet__pop_handlers_mock = mocker.patch("test.test_window.MockPygletWindow.pop_handlers")
    default_window.pop_handlers()
    assert not pyglet__pop_handlers_mock.called

def test_close(mocker: MockerFixture, default_window: Window):
    default_window.pyglet_window = MockPygletWindow()
    stateMachineClearMock = mocker.patch("audio_ui.state_machine.StateMachine.clear")
    pygletWindowCloseMock = mocker.patch("test.test_window.MockPygletWindow.close")
    default_window.close()
    stateMachineClearMock.assert_called_with()
    pygletWindowCloseMock.assert_called_with()

def test_get_caption(titled_window: Window):
    assert titled_window.caption == "test"

def test_set_caption_with_jaws_active(mocker: MockerFixture, default_window: Window):
    default_window.pyglet_window = MockPygletWindow()
    mocker.patch("accessible_output2.outputs.auto.Auto.output", return_value=None)
    mocker.patch("audio_ui.utils.speech_manager.is_jaws_active", return_value=True)
    speech_manager_output_mock = mocker.patch("audio_ui.utils.speech_manager.output")
    title: str = "test"
    default_window.caption = title
    assert default_window._caption == title
    speech_manager_output_mock.assert_called_with(title, interrupt=False, log_message=False)

def test_set_caption_with_jaws_not_active(mocker: MockerFixture, default_window: Window):
    default_window.pyglet_window = MockPygletWindow()
    mocker.patch("accessible_output2.outputs.auto.Auto.output", return_value=None)
    mocker.patch("audio_ui.utils.speech_manager.is_jaws_active", return_value=False)
    speech_manager_output_mock = mocker.patch("audio_ui.utils.speech_manager.output")
    title: str = "test"
    default_window.caption = title
    assert default_window._caption == title
    assert not speech_manager_output_mock.called

def test_with_empty_caption(mocker: MockerFixture, titled_window: Window):
    titled_window.caption = ""
    assert titled_window._caption == "test"
