from typing import Callable

import pyglet
from pyglet.event import EVENT_HANDLED, EVENT_UNHANDLED
from pyglet.window import key

from elements import Element
from utils import KeyHandler
from state import State
from state_machine import EmptyState
from state_machine import StateMachine
from window import Window

class ContainerScreen(State):

    def __init__(self, parent_window: Window) -> None:
        self.parent_window: Window = parent_window
        self.position: int = 0
        self.state_machine: StateMachine = StateMachine()
        self.change_state: Callable[[str, any], None] = None
        self.key_handler: KeyHandler = KeyHandler()
        self.bind_keys()

    def bind_keys(self) -> None:
        self.key_handler.add_key_press(self.next_element, key.TAB)
        self.key_handler.add_key_press(self.previous_element, key.TAB, [key.MOD_SHIFT])

    def setup(self, change_state: Callable[[str, any], None], *args, **kwargs) -> bool:
        self.change_state = change_state
        self.push_handlers(self.key_handler)
        self.set_state(interrupt_speech=False)
        return True

    def update(self, delta_time: float) -> bool:
        self.state_machine.update(delta_time)

    def exit(self) -> bool:
        if self.state_machine.size() > 0:
            self.state_machine.exit()

        self.pop_handlers()
        return True

    def add(self, key: str, element: Element) -> None:
        self.state_machine.add(key, element)

    def remove(self, key: str) -> Element:
        return self.state_machine.remove(key)

    def next_element(self) -> bool:
        if self.state_machine.size() > 1:
            self.position = (self.position + 1) % self.state_machine.size()
            self.set_state()
            return EVENT_HANDLED
        elif self.state_machine.size() == 1:
            self.set_state()
            return EVENT_HANDLED

        return EVENT_UNHANDLED

    def previous_element(self) -> bool:
        if self.state_machine.size() > 1:
            self.position = (self.position - 1) % self.state_machine.size()
            self.set_state()
            return EVENT_HANDLED
        elif self.state_machine.size() == 1:
            self.set_state()
            return EVENT_HANDLED

        return EVENT_UNHANDLED

    def set_state(self, interrupt_speech: bool = True) -> None:
        state_key: str =  list(self.state_machine.states)[self.position]
        self.state_machine.change(state_key, interrupt_speech)

    def push_handlers(self, handler: KeyHandler) -> None:
        self.parent_window.push_handlers(handler)

    def pop_handlers(self) -> None:
        self.parent_window.pop_handlers()

    def close_window(self) -> None:
        self.parent_window.close()
