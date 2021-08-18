from typing import Callable

import pyglet
from pyglet.event import EVENT_HANDLED, EVENT_UNHANDLED
from pyglet.window import key

from elements import Element
from utils import KeyHandler
from state import State
from state_machine import EmptyState
from state_machine import StateMachine
from screens import Screen
from window import Window

class ContainerScreen(Screen):

    def __init__(self, parent: Window) -> None:
        super().__init__(parent)
        self.change_state: Callable[[str, any], None] = None

    def bind_keys(self) -> None:
        self.key_handler.add_key_press(self.next_element, key.TAB)
        self.key_handler.add_key_press(self.previous_element, key.TAB, [key.MOD_SHIFT])

    def setup(self, change_state: Callable[[str, any], None], *args, **kwargs) -> bool:
        self.change_state = change_state
        self.push_handlers(self.key_handler)
        self.set_state(interrupt_speech=False)
        return True

    def update(self, delta_time: float) -> bool:
        return self.state_machine.update(delta_time)

    def exit(self) -> bool:
        if self.state_machine.size() > 0:
            self.state_machine.exit()

        self.pop_handlers()
        return EVENT_HANDLED

    def close(self) -> None:
        self.parent.close()
