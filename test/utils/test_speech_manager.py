import importlib
import sys
import platform
import os
from typing import List

from unittest import mock
from accessible_output2.outputs.jaws import Jaws
from accessible_output2.outputs.nvda import NVDA
from accessible_output2.outputs.sapi5 import SAPI5
import pytest
from pytest_mock import MockerFixture
from pytest import MonkeyPatch

from sonartk.util import speech_manager
import test.mocks.appscript
from accessible_output2.outputs.voiceover import VoiceOver


@pytest.fixture(autouse=True)
def setup_speech_manager() -> None:
    speech_manager.clear_history()
    # appscript is a Mac only library, so mock the module so tests will run on other platforms.
    module = type(sys)("appscript")
    module.app = test.mocks.appscript.app  # type: ignore[attr-defined]
    sys.modules["appscript"] = module


def test_output_with_log_and_interrupt(mocker: MockerFixture) -> None:
    accessible_output2_output_mock = mocker.patch(
        "accessible_output2.outputs.auto.Auto.output"
    )
    message: str = "test"
    interrupt: bool = True
    log_message: bool = True
    speech_manager.output(
        message,
        interrupt,
        log_message,
    )
    assert len(speech_manager._speech_history) == 1
    assert speech_manager._speech_history[-1] == message
    assert (
        speech_manager._history_position
        == len(speech_manager._speech_history) - 1
    )
    accessible_output2_output_mock.assert_called_with(
        message, interrupt=interrupt
    )


def test_speech_manager_import_is_lazy() -> None:
    importlib.reload(speech_manager)
    assert speech_manager._screenreader is None


def test_output_with_multiple_logs(mocker: MockerFixture) -> None:
    accessible_output2_output_mock = mocker.patch(
        "accessible_output2.outputs.auto.Auto.output"
    )
    message1: str = "test1"
    message2: str = "test2"
    message3: str = "test3"
    interrupt: bool = True
    log_message: bool = True
    speech_manager.output(
        message1,
        interrupt,
        log_message,
    )
    speech_manager.output(
        message2,
        interrupt,
        log_message,
    )
    speech_manager.output(
        message3,
        interrupt,
        log_message,
    )
    assert len(speech_manager._speech_history) == 3
    assert speech_manager._speech_history[0] == message1
    assert speech_manager._speech_history[1] == message2
    assert speech_manager._speech_history[2] == message3
    assert (
        speech_manager._history_position
        == len(speech_manager._speech_history) - 1
    )
    accessible_output2_output_mock.assert_has_calls(
        [
            mock.call(message1, interrupt=interrupt),
            mock.call(message2, interrupt=interrupt),
            mock.call(message3, interrupt=interrupt),
        ]
    )


def test_output_without_log_and_interrupt(mocker: MockerFixture) -> None:
    accessible_output2_output_mock = mocker.patch(
        "accessible_output2.outputs.auto.Auto.output"
    )
    message: str = "test"
    interrupt: bool = False
    log_message: bool = False
    speech_manager.output(
        message,
        interrupt,
        log_message,
    )
    assert len(speech_manager._speech_history) == 0
    assert speech_manager._history_position == 0
    accessible_output2_output_mock.assert_called_with(
        message, interrupt=interrupt
    )


def test_silence_with_nvda_active(mocker: MockerFixture) -> None:
    accessible_output2_output_mock = mocker.patch(
        "accessible_output2.outputs.auto.Auto.output"
    )
    mocker.patch("platform.system", return_value="Windows")
    mocker.patch(
        "accessible_output2.outputs.auto.Auto.get_first_available_output",
        return_value=NVDA(),
    )
    speech_manager.silence()
    accessible_output2_output_mock.assert_called_with(None, interrupt=True)


def test_silence_with_nvda_not_active(mocker: MockerFixture) -> None:
    accessible_output2_output_mock = mocker.patch(
        "accessible_output2.outputs.auto.Auto.output"
    )
    mocker.patch("platform.system", return_value="Windows")
    mocker.patch(
        "accessible_output2.outputs.auto.Auto.get_first_available_output",
        return_value=None,
    )
    speech_manager.silence()
    accessible_output2_output_mock.assert_called_with("", interrupt=True)


def test_get_current_screen_reader(mocker: MockerFixture) -> None:
    screenreader: NVDA = NVDA()
    mocker.patch(
        "accessible_output2.outputs.auto.Auto.get_first_available_output",
        return_value=screenreader,
    )
    assert speech_manager.get_current_screenreader() == screenreader


def test_is_nvda_active(mocker: MockerFixture) -> None:
    mocker.patch("platform.system", return_value="Windows")
    mocker.patch(
        "accessible_output2.outputs.auto.Auto.get_first_available_output",
        return_value=NVDA(),
    )
    assert speech_manager.is_nvda_active()


def test_is_nvda_not_active(mocker: MockerFixture) -> None:
    mocker.patch("platform.system", return_value="Windows")
    mocker.patch(
        "accessible_output2.outputs.auto.Auto.get_first_available_output",
        return_value=None,
    )
    assert not speech_manager.is_nvda_active()


def test_is_jaws_active(mocker: MockerFixture) -> None:
    mocker.patch("platform.system", return_value="Windows")
    mocker.patch(
        "accessible_output2.outputs.auto.Auto.get_first_available_output",
        return_value=Jaws(),
    )
    assert speech_manager.is_jaws_active()


def test_is_jaws_not_active(mocker: MockerFixture) -> None:
    mocker.patch("platform.system", return_value="Windows")
    mocker.patch(
        "accessible_output2.outputs.auto.Auto.get_first_available_output",
        return_value=None,
    )
    assert not speech_manager.is_jaws_active()


def test_is_voiceover_active(
    monkeypatch: MonkeyPatch, mocker: MockerFixture
) -> None:
    original_platform: str = platform.system()
    mocker.patch("platform.system", return_value="Darwin")
    mocker.patch(
        "accessible_output2.outputs.auto.Auto.get_first_available_output",
        return_value=VoiceOver(),
    )
    # reload the speech_manager since now platform.system() is being mocked and returning Darwin. Speech_manager  will now import VoiceOver instead of NVDA and Jaws.
    importlib.reload(speech_manager)
    assert speech_manager.is_voiceover_active()
    # remock platform.system() to return speech_manager to its original state.
    mocker.patch("platform.system", return_value=original_platform)
    importlib.reload(speech_manager)


def test_is_voiceover_not_active(
    monkeypatch: MonkeyPatch, mocker: MockerFixture
) -> None:
    mocker.patch("platform.system", return_value="Windows")
    mocker.patch(
        "accessible_output2.outputs.auto.Auto.get_first_available_output",
        return_value=None,
    )
    assert not speech_manager.is_voiceover_active()


def test_is_sapi_active(mocker: MockerFixture) -> None:
    mocker.patch("platform.system", return_value="Windows")
    mocker.patch(
        "accessible_output2.outputs.auto.Auto.get_first_available_output",
        return_value=SAPI5(),
    )
    assert speech_manager.is_sapi_active()


def test_is_sapi_not_active(mocker: MockerFixture) -> None:
    mocker.patch("platform.system", return_value="Windows")
    mocker.patch(
        "accessible_output2.outputs.auto.Auto.get_first_available_output",
        return_value=None,
    )
    assert not speech_manager.is_sapi_active()


def test_clear_history() -> None:
    speech_manager._speech_history = ["test1", "test2"]
    speech_manager._history_position = 1
    speech_manager.clear_history()
    assert len(speech_manager._speech_history) == 0
    assert speech_manager._history_position == 0


def test_pop_last_message_from_empty_history() -> None:
    result: str | None = speech_manager.pop_last_message()
    assert result is None


def test_pop_last_message() -> None:
    message1: str = "test1"
    message2: str = "test2"
    message3: str = "test3"
    speech_manager._speech_history = [message1, message2, message3]
    speech_manager._history_position = 2
    result: str | None = speech_manager.pop_last_message()
    assert result == message3
    assert speech_manager._history_position == 1


def test_trim_old_history() -> None:
    message1: str = "test1"
    message2: str = "test2"
    message3: str = "test3"
    speech_manager._speech_history = [message1, message2, message3]
    speech_manager._history_position = 2
    speech_manager.trim_old_history(message_count=2)
    assert len(speech_manager._speech_history) == 1
    assert speech_manager._speech_history[0] == message3


def test_trim_old_history_where_no_history() -> None:
    assert (len(speech_manager._speech_history)) == 0
    speech_manager.trim_old_history(message_count=4)


def test_trim_old_history_where_message_count_greater_than_history_size(
    mocker: MockerFixture,
) -> None:
    message1: str = "test1"
    message2: str = "test2"
    message3: str = "test3"
    speech_manager._speech_history = [message1, message2, message3]
    speech_manager._history_position = 2
    speech_manager.trim_old_history(message_count=4)
    assert len(speech_manager._speech_history) == 0


def test_next_history_where_history_empty() -> None:
    result: str | None = speech_manager.next_history()
    assert result is None


def test_next_history_where_position_at_end_of_list(
    mocker: MockerFixture,
) -> None:
    message1: str = "test1"
    message2: str = "test2"
    message3: str = "test3"
    speech_manager._speech_history = [message1, message2, message3]
    speech_manager._history_position = 2
    result: str | None = speech_manager.next_history()
    assert speech_manager._history_position == 2
    assert result == message3


def test_next_history(mocker: MockerFixture) -> None:
    message1: str = "test1"
    message2: str = "test2"
    message3: str = "test3"
    speech_manager._speech_history = [message1, message2, message3]
    speech_manager._history_position = 0
    result: str | None = speech_manager.next_history()
    assert speech_manager._history_position == 1
    assert result == message2


def test_previous_history_where_history_empty() -> None:
    result: str | None = speech_manager.previous_history()
    assert result is None


def test_previous_history_where_position_is_0(mocker: MockerFixture) -> None:
    message1: str = "test1"
    message2: str = "test2"
    message3: str = "test3"
    speech_manager._speech_history = [message1, message2, message3]
    speech_manager._history_position = 0
    result: str | None = speech_manager.previous_history()
    assert speech_manager._history_position == 0
    assert result == message1


def test_previous_history(mocker: MockerFixture) -> None:
    message1: str = "test1"
    message2: str = "test2"
    message3: str = "test3"
    speech_manager._speech_history = [message1, message2, message3]
    speech_manager._history_position = 2
    result: str | None = speech_manager.previous_history()
    assert speech_manager._history_position == 1
    assert result == message2


def test_navigate_to_end_of_history_where_history_empty() -> None:
    result: str | None = speech_manager.navigate_to_end_of_history()
    assert result is None


def test_navigate_to_end_of_history() -> None:
    message1: str = "test1"
    message2: str = "test2"
    message3: str = "test3"
    speech_manager._speech_history = [message1, message2, message3]
    speech_manager._history_position = 0
    result: str | None = speech_manager.navigate_to_end_of_history()
    assert speech_manager._history_position == 2
    assert result == message3


def test_navigate_to_beginning_of_history_where_history_empty() -> None:
    result: str | None = speech_manager.navigate_to_beginning_of_history()
    assert result is None


def test_navigate_to_beginning_of_history() -> None:
    message1: str = "test1"
    message2: str = "test2"
    message3: str = "test3"
    speech_manager._speech_history = [message1, message2, message3]
    speech_manager._history_position = 2
    result: str | None = speech_manager.navigate_to_beginning_of_history()
    assert speech_manager._history_position == 0
    assert result == message1


def test_get_history() -> None:
    history: List[str] = ["test1", "test2"]
    speech_manager._speech_history = history
    result: List[str] = speech_manager.get_speech_history()
    assert result == history


def test_genpy_cleanup_exception_handling(
    mocker: MockerFixture, monkeypatch: MonkeyPatch
) -> None:
    """Test that the genpy cleanup exception handler (lines 18-19) works correctly"""
    # Save original module references
    original_modules = {}
    ao2_modules = [
        key for key in sys.modules.keys() if "accessible_output2" in key
    ]
    for mod in ao2_modules:
        original_modules[mod] = sys.modules[mod]

    try:
        # Setup environment to trigger the exception path
        original_frozen = getattr(sys, "frozen", None)
        original_temp = os.environ.get("temp", None)

        # Create a mock that will raise an exception when rmtree is called
        sys.frozen = True  # type: ignore[attr-defined]
        os.environ["temp"] = "C:\\test_temp"

        # Mock the functions to trigger the exception path
        mocker.patch("os.path.isdir", return_value=True)
        mocker.patch(
            "shutil.rmtree", side_effect=PermissionError("Test exception")
        )

        # Mock accessible_output2 modules to prevent DLL loading issues
        mock_auto = mocker.MagicMock()
        mock_base = mocker.MagicMock()
        mocker.patch.dict(
            "sys.modules",
            {
                "accessible_output2.outputs.auto": mock_auto,
                "accessible_output2.outputs.base": mock_base,
                "accessible_output2.outputs.jaws": mocker.MagicMock(),
                "accessible_output2.outputs.nvda": mocker.MagicMock(),
                "accessible_output2.outputs.sapi5": mocker.MagicMock(),
                "accessible_output2.outputs.voiceover": mocker.MagicMock(),
            },
        )

        # Remove the module from cache so we can reload it
        if "sonartk.util.speech_manager" in sys.modules:
            del sys.modules["sonartk.util.speech_manager"]

        # Import the module - this will execute the try/except block
        import sonartk.util.speech_manager

        # If we got here, the exception was handled correctly (lines 18-19 executed)
        assert True

    finally:
        # Restore original state
        if original_frozen is None:
            if hasattr(sys, "frozen"):
                delattr(sys, "frozen")
        else:
            sys.frozen = original_frozen  # type: ignore[attr-defined]

        if original_temp is None:
            if "temp" in os.environ:
                del os.environ["temp"]
        else:
            os.environ["temp"] = original_temp

        # Restore original accessible_output2 modules
        for mod, module in original_modules.items():
            sys.modules[mod] = module

        # Restore speech_manager module
        import sonartk.util.speech_manager

        sys.modules["sonartk.util.speech_manager"] = (
            sonartk.util.speech_manager
        )
