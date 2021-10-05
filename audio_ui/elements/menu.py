from typing import Dict, Callable, List, Union

import pyglet
from pyglet.window import key
from pyglet.event import EVENT_HANDLED

from audio_ui.elements import Element
from audio_ui.elements import TextLabel
from audio_ui.state_machine import StateMachine, EmptyState
from audio_ui.state import State
from audio_ui.utils import speech_manager
from audio_ui.utils import KeyHandler

class Menu(Element[str]):

    def __init__(
        self, parent: State, title: str = "", items: List[Dict[str, Union[Element, str]]] = [], position: int = 0, has_border: bool = False, is_first_letter_navigation: bool = True, is_side_menu: bool = False,
        reset_position_on_focus: bool = True
    ) -> None:
        super().__init__(parent=parent, title=title, value="", type="menu")

        self.has_border: bool = has_border
        self.is_first_letter_navigation: bool = is_first_letter_navigation  
        self.is_side_menu: bool = is_side_menu
        self.reset_position_on_focus: bool = reset_position_on_focus
        self.position: int = position
        self.default_position: int = position
        self.typing_buffer: str = ""
        self.end_of_menu: bool = 0
        self.state_machine: StateMachine = StateMachine()
        self.bind_keys()

        if items:
            for item in items:
                if not item or len(item) > 1:
                    raise ValueError("Requires 1 dictionary entry.")
                else:
                    k, v = next(iter(item.items()))
                    self.add(k, v)

    def bind_keys(self) -> None:
        if self.is_side_menu:
            self.key_handler.add_key_press(self.next_item, key.RIGHT)
            self.key_handler.add_key_press(self.previous_item, key.LEFT)
        else:
            self.key_handler.add_key_press(self.next_item, key.DOWN)
            self.key_handler.add_key_press(self.previous_item, key.UP)

        self.key_handler.add_key_press(self.navigate_to_beginning, key.HOME)
        self.key_handler.add_key_press(self.navigate_to_end, key.END)
        self.key_handler.add_key_press(self.submit, key.RETURN)

        if self.is_first_letter_navigation:
            self.key_handler.add_on_text_input(self.navigate_by_first_letter)

    @property
    def value(self) -> str:
        return list(self.state_machine.states)[self.position]

    @value.setter
    def value(self, value: str) -> None:
        index: int = 0
        for key in self.state_machine.states.keys():
            if key == value: break
            index += 1

        self.position = index
        self.state_machine.change(value)

    def setup(self, change_state: Callable[[str, any], None], interrupt_speech: bool = True) -> bool:
        super().setup(change_state, interrupt_speech)

        if self.reset_position_on_focus:
            self.position = self.default_position

        self.set_state(interrupt_speech=False)
        return True

    def update(self, delta_time: float) -> bool:
        super().update(delta_time)
        return self.state_machine.update(delta_time)

    def exit(self) -> bool:
        return self.state_machine.current_state.exit() and super().exit()

    def next_item(self) -> bool:
        if not self.has_border:
            self.dispatch_event("on_change", self)
            self.position = (self.position + 1) % self.state_machine.size()
            self.set_state()
        else:
            if self.state_machine.size() == 1:
                self.dispatch_event("on_border", self)
                self.set_state()
            elif self.position + 1 < self.state_machine.size():
                self.dispatch_event("on_change", self)
                self.position += 1
                self.set_state()
            else:
                self.dispatch_event("on_border", self)

        return EVENT_HANDLED

    def previous_item(self) -> bool:
        if not self.has_border:
            self.dispatch_event("on_change", self)
            self.position = (self.position - 1) % self.state_machine.size()
            self.set_state()
        else:
            if self.state_machine.size() == 1:
                self.dispatch_event("on_border", self)
                self.set_state()
            elif self.position - 1 >= 0:
                self.dispatch_event("on_change", self)
                self.position -= 1
                self.set_state()
            else:
                self.dispatch_event("on_border", self)

        return EVENT_HANDLED

    def navigate_to_beginning(self) -> bool:
        if self.position != 0:
            self.dispatch_event("on_change", self)
            self.position = 0
            self.set_state()

        return EVENT_HANDLED

    def navigate_to_end(self) -> bool:
        if self.position != self.state_machine.size() - 1:
            self.dispatch_event("on_change", self)
            self.position = self.state_machine.size() - 1
            self.set_state()

        return EVENT_HANDLED

    def submit(self) -> bool:
        self.dispatch_event("on_submit", self)
        return EVENT_HANDLED

    def navigate_by_first_letter(self, character: str) -> bool:
        self.typing_buffer += character
        pyglet.clock.unschedule(self._navigate_by_text)
        pyglet.clock.schedule_once(self._navigate_by_text, 0.6)
        return EVENT_HANDLED

    def _navigate_by_text(self, dt: float) -> None:
        try:
            self.position = next(i for i, s in enumerate(self.state_machine.states.values()) if s.title.startswith(self.typing_buffer))
            self.set_state()
            self.typing_buffer = ""
            self.dispatch_event("on_change", self)
        except StopIteration:
            self.dispatch_event("on_letter_navigation_fail", self)

    def set_state(self, interrupt_speech: bool = True) -> None:
        state_key: str =  list(self.state_machine.states)[self.position]
        self.state_machine.change(state_key, interrupt_speech)

    def add(self, key: str, item: Union[Element, str]) -> None:
        if isinstance(item, str):
            self.state_machine.add(key, TextLabel(self, item))
        elif isinstance(item, Element):
            self.state_machine.add(key, item)
        else:
            raise ValueError("Item must be either str or Element.")

    def remove(self, key: str) -> Element:
        return self.state_machine.remove(key)

    def reset(self):
        self.position = self.default_position
        state_key: str =  list(self.state_machine.states)[self.position]
        self.state_machine.current_state = self.state_machine.states[state_key]

        for item in self.state_machine.states.values():
            item.reset()

Menu.register_event_type("on_change")
Menu.register_event_type("on_border")
Menu.register_event_type("on_submit")
Menu.register_event_type("on_letter_navigation_fail")
