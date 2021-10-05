from typing import Callable, List

from pyglet.window import key
from pyglet.event import EVENT_HANDLED

from audio_ui.state import State
from audio_ui.elements import Element
from audio_ui.utils import speech_manager

class Button(Element[str]):

    def __init__(self, parent: State, title: str) -> None:
        super().__init__(parent=parent, title=title, value=title, type="button")
        self.bind_keys()

    def bind_keys(self) -> None:
        self.key_handler.add_key_press(self.submit, key.RETURN)
        self.key_handler.add_key_press(self.submit, key.SPACE)

    def submit(self) -> bool:
        self.dispatch_event("on_submit", self)
        return EVENT_HANDLED

    def reset(self) -> None:
        pass

Button.register_event_type("on_submit")
