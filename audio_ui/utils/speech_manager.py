"""
This module was created to manage speech actions and properties in a singalton fassion.
Implementing a true singalton class in python is challenging and often not very readable, so module level variables are used with the name mangling convention
to enforce they are not to be imported from the outside world.
"""

from typing import List
import platform 

from accessible_output2.outputs.auto import Auto
from accessible_output2.outputs.base import Output

if platform.system() == "Windows":
    from accessible_output2.outputs.nvda import NVDA
    from accessible_output2.outputs.jaws import Jaws
elif platform.system() == "Darwin":
    from accessible_output2.outputs.voiceover import VoiceOver

global _speech_history
global _history_position
global _screenreader

_speech_history = []
_history_position = 0
_screenreader = Auto()

def output(message: str, interrupt: bool = False, log_message: bool = True) -> None:
    global _screenreader
    global _speech_history

    if log_message:
        _speech_history.append(message)
        navigate_to_end_of_history()

    _screenreader.speak(message, interrupt=interrupt)

def silence() -> None:
    global _screenreader

    if platform.system() == "Windows" and isinstance(_screenreader.get_first_available_output(), NVDA):
        _screenreader.speak(None, interrupt=True)
    else:
        _screenreader.speak("", interrupt=True)

def get_current_screenreader() -> Output:
    global _screenreader
    return _screenreader.get_first_available_output()

def is_nvda_active() -> bool:
    return (platform.system() == "Windows" and isinstance(get_current_screenreader(), NVDA))

def is_jaws_active() -> bool:
    return (platform.system() == "Windows" and isinstance(get_current_screenreader(), Jaws))

def is_voiceover_active() -> bool:
    return (platform.system() == "Darwin" and isinstance(get_current_screenreader(), VoiceOver))

def clear_history() -> None:
    global _speech_history
    global _history_position
    _speech_history.clear()
    _speech_history = []
    _history_position = 0

def get_last_message() -> str:
    global _speech_history
    return _speech_history.pop()

def trim_old_history(message_count: int) -> None:
    global _speech_history
    global _history_position

    if len(_speech_history) > 1:
        if message_count > len(_speech_history):
            message_count = len(_speech_history)

        for i in range(message_count):
            del _speech_history[0]

def next_history() -> str:
    global _speech_history
    global _history_position

    if len(_speech_history) == 0:
        return None
    if _history_position + 1 >= len(_speech_history):
        _history_position = len(_speech_history) - 1
    else:
        _history_position += 1

    return _speech_history[_history_position]

def previous_history() -> str:
    global _speech_history
    global _history_position

    if len(_speech_history) == 0:
        return None
    if _history_position - 1 < 0:
        _history_position = 0
    else:
        _history_position -= 1

    return _speech_history[_history_position]

def navigate_to_end_of_history() -> str:
    global _speech_history
    global _history_position

    if len(_speech_history) == 0:
        return None

    _history_position = len(_speech_history) - 1
    return _speech_history[_history_position]

def navigate_to_beginning_of_history() -> str:
    global _speech_history
    global _history_position

    if len(_speech_history) == 0:
        return None

    _history_position = 0
    return _speech_history[_history_position]
