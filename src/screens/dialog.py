from typing import Callable

from pyglet.event import EVENT_HANDLED
from pyglet.window import key

from window import Window
from screens import ContainerScreen
from utils import speech_manager

class Dialog(ContainerScreen):

    def __init__(self, parent_window: Window) -> None:
        super().__init__(parent_window)
        self.caption: str = ""
        self.original_state_key: str = parent_window.state_machine.current_state.state_key

    def bind_keys(self) -> None:
        super().bind_keys()
        self.key_handler.add_key_press(self.close_dialog, key.ESCAPE)

    def open_dialog(self, caption: str) -> None:
        self.caption = caption + " Dialog"
        self.parent_window.caption = self.caption
        count: str = self.parent_window.size() + 1
        self.parent_window.add(f"dialog{count}", self)

    def setup(self, change_state: Callable[[str, any], None], *args, **kwargs) -> bool:
        super().setup(change_state)

    def exit(self) -> bool:
        return super().exit()

    def close_dialog(self) -> bool:
        self.parent_window.caption = parent_window.caption
        self.parent_window.change(self.original_state_key)
        self.parent_window.remove(self.state_key)
        return EVENT_HANDLED
