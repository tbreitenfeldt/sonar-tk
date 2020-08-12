from typing import Callable

from pyglet.event import EVENT_HANDLED

from ui.windows import ContainerTab
from utils import speech_manager

class Dialog(ContainerTab):

    def __init__(self, parent: "Tab", title: str = "", music: str = "") -> None:
        super().__init__(parent=parent, title=title, escapable=True, music=music)
        self.title += " Dialog"

    def close(self) -> bool:
        self.parent.pop_child_window()
        return EVENT_HANDLED