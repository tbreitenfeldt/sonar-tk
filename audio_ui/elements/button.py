from typing import Callable, List

from pyglet.window import key
from pyglet.event import EVENT_HANDLED

from audio_ui.state import State
from audio_ui.elements import Element
from audio_ui.utils import audio_manager
from audio_ui.utils import speech_manager

class Button(Element[str]):

    def __init__(self, parent: State, title: str = "", callback: Callable[[Callable[[str, any], None], str, any], None] = None, callback_args: List[any] = [], activate_sound: str = "") -> None:
        super().__init__(parent=parent, title=title, value=title, type="Button", callback=callback, callback_args=callback_args)
        self.activate_sound: str = activate_sound
        self.bind_keys()

    def bind_keys(self) -> None:
        self.key_handler.add_key_press(self.submit, key.RETURN)
        self.key_handler.add_key_press(self.submit, key.SPACE)

    def on_action(self) -> bool:
        self.play_activate_sound()
        return EVENT_HANDLED

    def play_activate_sound(self) -> bool:
        if self.activate_sound:
            audio_manager.play(self.activate_sound)
            return True

        return False

    def reset(self) -> None:
        pass
