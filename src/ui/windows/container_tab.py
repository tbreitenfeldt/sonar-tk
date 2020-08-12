from typing import Callable

import pyglet
from pyglet.event import EVENT_HANDLED, EVENT_UNHANDLED
from pyglet.window import key

from ui.windows import Tab
from ui.elements import Element
from utils import KeyHandler
from state_machine import EmptyState

class ContainerTab(Tab):

    def __init__(self, parent: "Window", title: str = "", escapable: bool = False, music: str = "") -> None:
        super().__init__(parent, title, escapable, music)
        self.position = 0
        self.bind_keys()

    def bind_keys(self) -> None:
        self.key_handler.add_key_press(self.next_element, key.TAB)
        self.key_handler.add_key_press(self.previous_element, key.TAB, [key.MOD_SHIFT])

    def show_tab(self) -> None:
        super().show_tab()

        if not isinstance(self.state_machine.current_state, EmptyState):
            pyglet.clock.schedule_once(lambda dt: self.state_machine.setup(interrupt_speech=False), 0.2)
        else:
            pyglet.clock.schedule_once(lambda dt: self.set_state(interrupt_speech=False), 0.2)

    def exit(self) -> bool:
        if self.state_machine.size() > 0:
            self.state_machine.current_state.exit()

        self.pop_handlers()
        return True

    def add_element(self, key: str, element: Element) -> None:
        self.state_machine.add(key, element)

    def remove_element(self, key: str) -> Element:
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
