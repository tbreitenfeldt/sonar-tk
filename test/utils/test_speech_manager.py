import importlib
import sys
import platform

from unittest import mock
from accessible_output2.outputs.jaws import Jaws
from accessible_output2.outputs.nvda import NVDA
import pytest
from pytest_mock import MockerFixture
from pytest import MonkeyPatch

from audio_ui.utils import speech_manager
from accessible_output2.outputs.voiceover import VoiceOver
import test.mocks.appscript

# appscript is a Mac only library, so mock the module so tests will run on other platforms.
module = type(sys)("appscript")
module.app = test.mocks.appscript.app
sys.modules["appscript"] = module

@pytest.fixture(autouse=True)
def setup_speech_manager() -> speech_manager:
    speech_manager.clear_history()
    return speech_manager

def test_output_with_log_and_interrupt(mocker: MockerFixture):
    accessible_output2_output_mock = mocker.patch("accessible_output2.outputs.auto.Auto.output")
    message: str = "test"
    interrupt: bool = True
    log_message: bool = True
    speech_manager.output(message, interrupt, log_message,)
    assert len(speech_manager._speech_history) == 1
    assert speech_manager._speech_history[-1] == message
    assert speech_manager._history_position == len(speech_manager._speech_history) - 1
    accessible_output2_output_mock.assert_called_with(message, interrupt=interrupt)

def test_output_with_multiple_logs(mocker: MockerFixture):
    accessible_output2_output_mock = mocker.patch("accessible_output2.outputs.auto.Auto.output")
    message1: str = "test1"
    message2: str = "test2"
    message3: str = "test3"
    interrupt: bool = True
    log_message: bool = True
    speech_manager.output(message1, interrupt, log_message,)
    speech_manager.output(message2, interrupt, log_message,)
    speech_manager.output(message3, interrupt, log_message,)
    assert len(speech_manager._speech_history) == 3
    assert speech_manager._speech_history[0] == message1
    assert speech_manager._speech_history[1] == message2
    assert speech_manager._speech_history[2] == message3
    assert speech_manager._history_position == len(speech_manager._speech_history) - 1
    accessible_output2_output_mock.assert_has_calls([mock.call(message1, interrupt=interrupt), mock.call(message2, interrupt=interrupt), mock.call(message3, interrupt=interrupt)])

def test_output_without_log_and_interrupt(mocker: MockerFixture):
    accessible_output2_output_mock = mocker.patch("accessible_output2.outputs.auto.Auto.output")
    message: str = "test"
    interrupt: bool = False
    log_message: bool = False
    speech_manager.output(message, interrupt, log_message,)
    assert len(speech_manager._speech_history) == 0
    assert speech_manager._history_position == 0
    accessible_output2_output_mock.assert_called_with(message, interrupt=interrupt)

def test_silence_with_nvda_active(mocker: MockerFixture):
    accessible_output2_output_mock = mocker.patch("accessible_output2.outputs.auto.Auto.output")
    mocker.patch("platform.system", return_value="Windows")
    mocker.patch("accessible_output2.outputs.auto.Auto.get_first_available_output", return_value=NVDA())
    speech_manager.silence()
    accessible_output2_output_mock.assert_called_with(None, interrupt=True)

def test_silence_with_nvda_not_active(mocker: MockerFixture):
    accessible_output2_output_mock = mocker.patch("accessible_output2.outputs.auto.Auto.output")
    mocker.patch("platform.system", return_value="Windows")
    mocker.patch("accessible_output2.outputs.auto.Auto.get_first_available_output", return_value=None)
    speech_manager.silence()
    accessible_output2_output_mock.assert_called_with("", interrupt=True)

def test_get_current_screen_reader(mocker: MockerFixture):
    screenreader: NVDA = NVDA()
    mocker.patch("accessible_output2.outputs.auto.Auto.get_first_available_output", return_value=screenreader)
    assert speech_manager.get_current_screenreader() == screenreader

def test_is_nvda_active(mocker: MockerFixture):
    mocker.patch("platform.system", return_value="Windows")
    mocker.patch("accessible_output2.outputs.auto.Auto.get_first_available_output", return_value=NVDA())
    assert speech_manager.is_nvda_active()

def test_is_nvda_not_active(mocker: MockerFixture):
    mocker.patch("platform.system", return_value="Windows")
    mocker.patch("accessible_output2.outputs.auto.Auto.get_first_available_output", return_value=None)
    assert not speech_manager.is_nvda_active()

def test_is_jaws_active(mocker: MockerFixture):
    mocker.patch("platform.system", return_value="Windows")
    mocker.patch("accessible_output2.outputs.auto.Auto.get_first_available_output", return_value=Jaws())
    assert speech_manager.is_jaws_active()

def test_is_jaws_not_active(mocker: MockerFixture):
    mocker.patch("platform.system", return_value="Windows")
    mocker.patch("accessible_output2.outputs.auto.Auto.get_first_available_output", return_value=None)
    assert not speech_manager.is_jaws_active()

def test_is_voiceover_active(monkeypatch: MonkeyPatch, mocker: MockerFixture):
    original_platform: str = platform.system()
    mocker.patch("platform.system", return_value="Darwin")
    mocker.patch("accessible_output2.outputs.auto.Auto.get_first_available_output", return_value=VoiceOver())
    # reload the speech_manager since now platform.system() is being mocked and returning Darwin. Speech_manager  will now import VoiceOver instead of NVDA and Jaws.
    importlib.reload(speech_manager)
    assert speech_manager.is_voiceover_active()
    # remock platform.system() to return speech_manager to its original state.
    mocker.patch("platform.system", return_value=original_platform)
    importlib.reload(speech_manager)

def test_is_voiceover_not_active(monkeypatch: MonkeyPatch, mocker: MockerFixture):
    mocker.patch("platform.system", return_value="Windows")
    mocker.patch("accessible_output2.outputs.auto.Auto.get_first_available_output", return_value=None)
    assert not speech_manager.is_voiceover_active()
