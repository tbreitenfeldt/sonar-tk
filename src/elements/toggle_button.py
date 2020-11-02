from typing import Callable, List

from pyglet.window import key
from pyglet.event import EVENT_HANDLED

from state import State
from elements import Element
from utils import audio_manager
from utils import speech_manager

class ToggleButton(Element[str]):

    def __init__(
        self, parent: State, title: str = "", position: int = 0, items: List[str] = [], callback: Callable[[Callable[[str, any], None], str, any], None] = None, callback_args: List[any] = [],
        toggle_sound: str = ""
    ) -> None:
        super().__init__(parent=parent, title=title, value="", type="Toggle", callback=callback, callback_args=callback_args)
        self.items: List[str] = items
        self.position: int = position
        self.bind_keys()

    def bind_keys(self) -> None:
        self.key_handler.add_key_press(self.submit, key.RETURN)
        self.key_handler.add_key_press(self.submit, key.SPACE)

    def setup(self, change_state: Callable[[str, any], None], interrupt_speech: bool = True) -> bool:
        super().setup(change_state, interrupt_speech)
        speech_manager.output(self.items[self.position], interrupt=False, log_message=False)
        return True

    def on_action(self) -> bool:
        self.position = (self.position + 1) % len(self.items)
        self.value = self.items[self.position]
        speech_manager.output(self.value, interrupt=True, log_message=False)
        return EVENT_HANDLED

    def add(self, item: str) -> None:
        self.items.append(item)

    def play_toggle_sound(self) -> bool:
        if self.toggle_sound:
            audio_manager.play(self.toggle_sound)
            return True

        return False
