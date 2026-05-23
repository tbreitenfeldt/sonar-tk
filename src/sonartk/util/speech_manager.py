"""
This module was created to manage speech actions and properties in a singalton fassion.
Implementing a true singalton class in python is challenging and often not very readable, so module level variables are used with the name mangling convention
to enforce they are not to be imported from the outside world.
"""

import os
import platform
import shutil
import sys
import types
from typing import List, Optional, cast

# For accessible_output2, to handle cases when occasionally error is thrown due to genpy temp folder not getting removed.
try:
    genpy_path = os.path.join(os.environ["temp"], "gen_py")
    if getattr(sys, "frozen", True) and os.path.isdir(genpy_path):
        shutil.rmtree(genpy_path)
except (OSError, KeyError):
    pass

from accessible_output2.outputs.auto import Auto
from accessible_output2.outputs.base import Output

if platform.system() == "Windows":
    from accessible_output2.outputs.jaws import Jaws
    from accessible_output2.outputs.nvda import NVDA
    from accessible_output2.outputs.sapi5 import SAPI5
elif platform.system() == "Darwin":
    from accessible_output2.outputs.voiceover import VoiceOver

global _speech_history
global _history_position
global _screenreader

_speech_history = []
_history_position = 0
_screenreader = None


class _NullScreenreader:
    def output(self, *args: object, **kwargs: object) -> None:
        return None

    def get_first_available_output(self) -> "_NullScreenreader":
        return self


class _AppscriptStubObject:
    def __call__(
        self, *args: object, **kwargs: object
    ) -> "_AppscriptStubObject":
        return self

    def __getattr__(self, name: str) -> "_AppscriptStubObject":
        return self


def _ensure_appscript_stub() -> None:
    if platform.system() == "Darwin":
        return
    if "appscript" in sys.modules:
        return

    module = types.ModuleType("appscript")
    module.app = lambda *args, **kwargs: _AppscriptStubObject()  # type: ignore[attr-defined]
    sys.modules["appscript"] = module


def _get_screenreader() -> Output:
    global _screenreader

    if _screenreader is None:
        _ensure_appscript_stub()
        try:
            _screenreader = Auto()
        except Exception:
            _screenreader = cast(Output, _NullScreenreader())

    return _screenreader


def output(
    message: str, interrupt: bool = False, log_message: bool = True
) -> None:
    """Send a message to the active screen reader and optionally store it in history."""
    global _screenreader
    global _speech_history

    if log_message:
        _speech_history.append(message)
        navigate_to_end_of_history()

    _get_screenreader().output(message, interrupt=interrupt)


def silence() -> None:
    """Stop current speech output on the active screen reader."""
    global _screenreader

    if platform.system() == "Windows" and isinstance(
        _get_screenreader().get_first_available_output(), NVDA
    ):
        _get_screenreader().output(None, interrupt=True)
    else:
        _get_screenreader().output("", interrupt=True)


def get_current_screenreader() -> Output:
    """Return the currently selected accessible_output2 output instance."""
    global _screenreader
    return _get_screenreader().get_first_available_output()


def is_nvda_active() -> bool:
    """Return whether NVDA is the active screen reader output."""
    return platform.system() == "Windows" and isinstance(
        get_current_screenreader(), NVDA
    )


def is_jaws_active() -> bool:
    """Return whether JAWS is the active screen reader output."""
    return platform.system() == "Windows" and isinstance(
        get_current_screenreader(), Jaws
    )


def is_voiceover_active() -> bool:
    """Return whether VoiceOver is the active screen reader output."""
    return platform.system() == "Darwin" and isinstance(
        get_current_screenreader(), VoiceOver
    )


def is_sapi_active() -> bool:
    """Return whether SAPI5 is the active screen reader output."""
    return platform.system() == "Windows" and isinstance(
        get_current_screenreader(), SAPI5
    )


def clear_history() -> None:
    """Clear all stored speech history and reset history navigation position."""
    global _speech_history
    global _history_position
    _speech_history.clear()
    _speech_history = []
    _history_position = 0


def pop_last_message() -> Optional[str]:
    """Remove and return the most recent history message, if available."""
    global _speech_history
    global _history_position

    if len(_speech_history) == 0:
        return None

    _history_position = len(_speech_history) - 2
    return _speech_history.pop()


def trim_old_history(message_count: int) -> None:
    """Remove the oldest history entries up to the requested count."""
    global _speech_history
    global _history_position

    if len(_speech_history) > 0:
        if message_count > len(_speech_history):
            message_count = len(_speech_history)

        for i in range(message_count):
            del _speech_history[0]


def next_history() -> Optional[str]:
    """Move forward in speech history and return the current message."""
    global _speech_history
    global _history_position

    if len(_speech_history) == 0:
        return None
    if _history_position + 1 >= len(_speech_history):
        _history_position = len(_speech_history) - 1
    else:
        _history_position += 1

    return _speech_history[_history_position]


def previous_history() -> Optional[str]:
    """Move backward in speech history and return the current message."""
    global _speech_history
    global _history_position

    if len(_speech_history) == 0:
        return None
    if _history_position - 1 < 0:
        _history_position = 0
    else:
        _history_position -= 1

    return _speech_history[_history_position]


def navigate_to_end_of_history() -> Optional[str]:
    """Jump to the newest history message and return it."""
    global _speech_history
    global _history_position

    if len(_speech_history) == 0:
        return None

    _history_position = len(_speech_history) - 1
    return _speech_history[_history_position]


def navigate_to_beginning_of_history() -> Optional[str]:
    """Jump to the oldest history message and return it."""
    global _speech_history
    global _history_position

    if len(_speech_history) == 0:
        return None

    _history_position = 0
    return _speech_history[_history_position]


def get_speech_history() -> List[str]:
    """Return the in-memory speech history list."""
    global _speech_history
    return _speech_history
