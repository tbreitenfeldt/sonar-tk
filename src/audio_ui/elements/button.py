from typing import Callable, List

from pyglet.window import key
from pyglet.event import EVENT_HANDLED

from audio_ui.utils import State, speech_manager
from audio_ui.elements import Element


class Button(Element[str]):
    def __init__(self, parent: State, label: str) -> None:
        super().__init__(
            parent=parent, label=label, value=label, role="button"
        )
        self._bind_keys()

    def _bind_keys(self) -> None:
        self.key_handler.add_key_press(self.submit, key.RETURN)
        self.key_handler.add_key_press(self.submit, key.SPACE)

    def submit(self) -> bool:
        self.dispatch_event("on_submit", self)
        return EVENT_HANDLED

    def reset(self) -> None:
        pass


Button.register_event_type("on_submit")
