from typing import Callable

from pyglet.window import key
from pyglet.event import EVENT_HANDLED

from audio_ui.state import State
from audio_ui.elements import Element
from audio_ui.utils import speech_manager

class Checkbox(Element[bool]):

    def __init__(self, parent: State, title: str = "", value: bool = False) -> None:
        super().__init__(parent=parent, title=title, value=value, type="checkbox")
        self.default_value: bool = value
        self.bind_keys()

    def bind_keys(self) -> None:
        self.key_handler.add_key_press(self.toggle_state, key.RETURN)
        self.key_handler.add_key_press(self.toggle_state, key.SPACE)

    def setup(self, change_state: Callable[[str, any], None], interrupt_speech: str = True) -> bool:
        super().setup(change_state, interrupt_speech)
        output_value: str = "Checked" if self.value  else "Unchecked"
        speech_manager.output(output_value, interrupt=False, log_message=False)
        return True

    def toggle_state(self) -> bool:
        self.value = not self.value
        self.dispatch_event("on_change", self)
        output_value: str = "Checked" if self.value  else "Unchecked"
        speech_manager.output(output_value, interrupt=True, log_message=False)
        return EVENT_HANDLED

    def reset(self) -> None:
        self.value = self.default_value

Checkbox.register_event_type("on_change")
