from typing import Dict, Callable, List, Union

from pyglet.event import EVENT_HANDLED, EVENT_UNHANDLED
from pyglet.window import key

from elements import Menu
from state import State
from state_machine import EmptyState
from elements import Element
from utils import Key

class MenuBar(Menu):

    def __init__(self, parent: State) -> None:
        super().__init__(parent, title="Menu Bar", is_side_menu=True, suppress_type=True, has_border=False)
        self.is_open: bool = False
        self.expanded: bool = False

    def bind_keys(self) -> None:
        super().bind_keys()
        self.key_handler.add_key_press(self.expand_menus, key.UP)
        self.key_handler.add_key_press(self.expand_menus, key.DOWN)
        self.key_handler.add_key_press(self.close, key.ESCAPE)

    def exit(self) -> bool:
        if self.is_open:
            self.expanded = False
            for menu in self.state_machine.states.values():
                menu.suppress_reading_first_item_onfocus = True
            self.close()

        return super().exit()

    def open_menu_bar(self) -> bool:
        if not self.is_open:
            self.is_open = True
            counter: int = len(self.state_machine.states) + 1
            state_key: str = f"menu_bar {counter}"
            self.parent.state_machine.add(state_key, self)
            self.parent.state_machine.change(state_key)
        else:
            return EVENT_UNHANDLED

        return EVENT_HANDLED

    def open_menu(self, key: str) -> bool:
        counter: int = self.state_machine.size()+ 1
        menu_bar_key: str = f"menu_bar {counter}"
        index: int = list(self.state_machine.states.keys()).index(key)
        self.position = index

        if not self.is_open:
            self.is_open = True
            self.expand_menus()
            self.parent.state_machine.add(menu_bar_key, self)
            self.reset_menu_onfocus = False
            self.parent.state_machine.change(menu_bar_key)
            self.reset_menu_onfocus = True


        self.set_state()
        return EVENT_HANDLED

    def expand_menus(self) -> bool:
        if not self.expanded:
            self.expanded = True
            for menu in self.state_machine.states.values():
                menu.suppress_reading_first_item_onfocus = False

        return EVENT_UNHANDLED

    def next_item(self) -> bool:
        result: bool = super().next_item()
        if not self.expanded:
            menu: Menu = self.state_machine.current_state
            menu.position = -1
        return result

    def previous_item(self) -> bool:
        result: bool = super().previous_item()
        if not self.expanded:
            menu: Menu = self.state_machine.current_state
            menu.position = -1
        return result

    def add_menu(
        self, title: str, key: str, items: List[Dict[str, Union[Element, str]]], shortcut: Key = None, *args, **kwards) -> Menu:
        menu: Menu = Menu(self, title=title, items=items, has_border=False, *args, **kwards, suppress_reading_first_item_onfocus=True)
        self.add(key, menu)
        return menu

    def close(self) -> None:
        if self.expanded:
            self.expanded = False
            for menu in self.state_machine.states.values():
                menu.suppress_reading_first_item_onfocus = True
            self.set_state()
        else:
            self.is_open = False
            self.parent.set_state(interrupt_speech=False)
            self.state_machine.current_state = EmptyState()
            self.parent.state_machine.remove(self.state_key)
