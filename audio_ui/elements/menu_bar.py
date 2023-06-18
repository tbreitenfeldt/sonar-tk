from __future__ import annotations
from typing import Dict, Callable, List, Union

from pyglet.event import EVENT_HANDLED, EVENT_UNHANDLED
from pyglet.window import key

from audio_ui.elements import Menu
from audio_ui.state import State
from audio_ui.state_machine import EmptyState, StateMachine
from audio_ui.elements import Element
from audio_ui.utils import Key
from audio_ui.utils import speech_manager

class MenuBarItem(Element[str]):

    def __init__(self, parent: MenuBar, menu: Menu) -> None:
        super().__init__(parent=parent, label=menu.label, value="", role="submenu", use_key_handler=False)
        self.menu: Menu = menu
        self.is_expanded: bool = False

    def setup(self, change_state: Callable[[str, any], None], interrupt_speech=False) -> bool:
        if self.is_expanded:
            self.menu.setup(change_state)
        else:
            super().setup(change_state)

        return True

    def exit(self):
        if self.is_expanded:
            self.menu.exit()

        return super().exit()

    def reset(self) -> None:
        self.is_expanded = False


class MenuBar(Element[MenuBarItem]):

    def __init__(self, parent: State) -> None:
        super().__init__(parent, label="Menu", role="bar", value=None)
        self.is_open: bool = False
        self.is_expanded: bool = False
        self.position: int  = 0
        self.state_machine: StateMachine = StateMachine()
        self.bind_keys()

    def bind_keys(self) -> None:
        self.key_handler.add_key_press(self.open_menu, key.UP)
        self.key_handler.add_key_press(self.open_menu, key.DOWN)
        self.key_handler.add_key_press(self.next_menu, key.RIGHT)
        self.key_handler.add_key_press(self.previous_menu, key.LEFT)
        self.key_handler.add_key_press(self.close, key.ESCAPE)

    def setup(self, change_state: Callable[[str, any], None]) -> bool:
        super().setup(change_state)
        state_key: str =  list(self.state_machine.states)[self.position]
        self.state_machine.current_state = self.state_machine.states[state_key]
        self.state_machine.current_state.setup(change_state, interrupt_speech=False)
        return True

    def exit(self) -> bool:
        if self.is_open:
            self.is_open = False
            self.state_machine.current_state.exit() 
            super().exit()
            self.collapse_menus()
            self.position = 0
            self.parent.state_machine.current_state = EmptyState()
            self.parent.set_state(interrupt_speech=False)

        return True

    def reset(self) -> None:
        self.is_open = False
        self.collapse_menus()
        self.position = 0

    def open_menu_bar(self) -> bool:
        if not self.is_open:
            self.is_open = True
            self.parent.state_machine.current_state.exit()
            self.parent.state_machine.current_state = self
            self.setup(self.parent.state_machine.change)
            return EVENT_HANDLED

        return EVENT_UNHANDLED

    def open_menu(self, key: str=None) -> bool:
        # if key is None, use the current position
        if key is not None:
            index: int = list(self.state_machine.states.keys()).index(key)
            self.position = index

        if not self.is_open:
            self.is_open = True
            self.expand_menus()
            self.parent.state_machine.current_state.exit()
            self.parent.state_machine.current_state = self
            self.setup(self.parent.state_machine.change)
        else:
            self.expand_menus()
            state_key: str =  list(self.state_machine.states)[self.position]
            self.state_machine.current_state = self.state_machine.states[state_key]
            self.state_machine.current_state.setup(self.change_state)

        return EVENT_HANDLED

    def expand_menus(self) -> None:
        if not self.is_expanded:
            self.dispatch_event("on_expanded", self)
            self.is_expanded = True
            for menu in self.state_machine.states.values():
                menu.is_expanded = True

    def collapse_menus(self) -> None:
        if self.is_expanded:
            self.dispatch_event("on_collapsed", self)
            self.is_expanded = False
            for menu in self.state_machine.states.values():
                menu.is_expanded = False

    def next_menu(self) -> bool:
        self.dispatch_event("on_next_menu", self)
        self.position = (self.position + 1) % self.state_machine.size()
        self.set_state()
        return EVENT_HANDLED

    def previous_menu(self) -> bool:
        self.dispatch_event("on_previous_menu", self)
        self.position = (self.position - 1) % self.state_machine.size()
        self.set_state()
        return EVENT_HANDLED

    def add_menu(self, key: str, menu: Menu) -> MenuBarItem:
        item: MenuBarItem = MenuBarItem(self, menu)
        self.state_machine.add(key, item)
        return item

    def close(self) -> None:
        if self.is_expanded:
            # Manually set the new state since the menues should be collapsed between when current_state.exit() is called and when the new state .setup() is called
            self.state_machine.current_state.exit()
            self.collapse_menus()
            state_key: str =  list(self.state_machine.states)[self.position]
            self.state_machine.current_state = self.state_machine.states[state_key]
            self.state_machine.current_state.setup(self.change_state)
        else:
            self.is_open = False
            self.position = 0
            super().exit()
            self.parent.state_machine.current_state = EmptyState()
            self.parent.set_state(interrupt_speech=False)

    def set_state(self, interrupt_speech: bool = True) -> None:
        state_key: str =  list(self.state_machine.states)[self.position]
        self.state_machine.change(state_key, interrupt_speech)

MenuBar.register_event_type("on_expanded")
MenuBar.register_event_type("on_collapsed")
MenuBar.register_event_type("on_next_menu")
MenuBar.register_event_type("on_previous_menu")
