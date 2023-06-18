from typing import Callable, List

from pyglet.window import key
from pyglet.event import EVENT_HANDLED

from audio_ui.state import State
from audio_ui.elements import Element
from audio_ui.utils import speech_manager

class ToggleButton(Element[str]):

    def __init__(self, parent: State, label: str = "", position: int = 0, items: List[str] = []) -> None:
        super().__init__(parent=parent, label=label, value="", role="toggle")
        self.items: List[str] = items
        self.position: int = position
        self.default_position: int = position
        self.bind_keys()

    def bind_keys(self) -> None:
        self.key_handler.add_key_press(self.next, key.RETURN)
        self.key_handler.add_key_press(self.next, key.SPACE)

    def setup(self, change_state: Callable[[str, any], None], interrupt_speech: bool = True) -> bool:
        super().setup(change_state, interrupt_speech)
        speech_manager.output(self.items[self.position], interrupt=False, log_message=False)
        return True

    def next(self) -> bool:
        self.position = (self.position + 1) % len(self.items)
        self.value = self.items[self.position]
        speech_manager.output(self.value, interrupt=True, log_message=False)
        self.dispatch_event("on_change", self)
        return EVENT_HANDLED

    def add(self, item: str) -> None:
        self.items.append(item)

    def reset(self) -> None:
        self.position = self.default_position

ToggleButton.register_event_type("on_change")
