from typing import Dict, Callable, List, Union

from pyglet.window import key
from pyglet.event import EVENT_HANDLED

from audio_ui.elements import Element
from audio_ui.elements import TextLabel
from audio_ui.state_machine import StateMachine, EmptyState
from audio_ui.state import State
from audio_ui.utils import audio_manager
from audio_ui.utils import speech_manager
from audio_ui.utils import KeyHandler

class Menu(Element[str]):

    def __init__(
        self, parent: State, title: str = "", items: List[Dict[str, Union[Element, str]]] = [], position: int = 0, has_border: bool = True, is_first_letter_navigation: bool = True, is_side_menu: bool = False,
        suppress_type: bool = False, reset_item_state_onchange: bool = False, reset_menu_onfocus: bool = True, suppress_reading_first_item_onfocus: bool = False,
        onsubmit_callback: Callable[[Callable[[str, any], None], str, any], None] = None, callback_args: List[any] = [], scroll_sound: str = "", select_sound: str = "", open_sound: str = "",
        border_sound: str = "", music: str = ""
    ) -> None:
        if suppress_type:
            super().__init__(parent=parent, title=title, value="", type="", callback=onsubmit_callback, callback_args=callback_args)
        else:
            super().__init__(parent=parent, title=title, value="", type="Menu", callback=onsubmit_callback, callback_args=callback_args)

        self.has_border: bool = has_border
        self.is_first_letter_navigation: bool = is_first_letter_navigation  
        self.is_side_menu: bool = is_side_menu
        self.reset_item_state_onchange: bool = reset_item_state_onchange
        self.reset_menu_onfocus: bool = reset_menu_onfocus
        self.suppress_reading_first_item_onfocus: bool = suppress_reading_first_item_onfocus
        self.scroll_sound: str = scroll_sound
        self.select_sound: str = select_sound
        self.open_sound: str = open_sound
        self.border_sound: str = border_sound
        self.music: str = music
        self.position: int = position
        self.default_position: int = position
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

        if self.music:
            audio_manager.load_music(self.music)
            audio_manager.play_music(loops=-1)

        self.play_open_sound()

        if self.reset_menu_onfocus:
            self.reset()

        if not isinstance(self.state_machine.current_state, EmptyState):
            if not self.suppress_reading_first_item_onfocus:
                self.state_machine.setup(interrupt_speech=False)
            else:
                self.position = -1
                if not isinstance(self.state_machine.current_state, TextLabel):
                    self.push_handlers(self.state_machine.current_state.key_handler)

        else:
            self.set_state(interrupt_speech=False)

        return True

    def update(self, delta_time: float) -> bool:
        super().update(delta_time)
        return self.state_machine.update(delta_time)

    def exit(self) -> bool:
        self.state_machine.current_state.exit()
        return super().exit()

    def next_item(self) -> bool:
        if self.state_machine.size() == 1:
            self.set_state()
        elif not self.end_of_menu and self.position + 1 >= self.state_machine.size():
            if self.has_border:
                self.end_of_menu = True
                self.position = len(self.state_machine.states) - 1
                self.play_border_sound()
            else:
                self.position = 0
                self.set_state()
                element: Element = self.state_machine.current_state
                if self.reset_item_state_onchange:
                    element.reset()

                if not self.play_border_sound():
                    self.play_scroll_sound()

        elif self.position + 1 < self.state_machine.size():
            self.end_of_menu = False
            self.position += 1
            self.set_state()
            element: Element = self.state_machine.current_state
            if self.reset_item_state_onchange:
                element.reset()
            self.play_scroll_sound()

        return EVENT_HANDLED

    def previous_item(self) -> bool:
        if len(self.state_machine.states) == 1:
            self.set_state()
        elif not self.end_of_menu and self.position - 1 < 0:
            if self.has_border:
                self.end_of_menu = True
                self.position = 0
                self.play_border_sound()
            else:
                self.position = len(self.state_machine.states) - 1
                self.set_state()
                element: Element = self.state_machine.current_state
                if self.reset_item_state_onchange:
                    element.reset()

                if not self.play_border_sound():
                    self.play_scroll_sound()

        elif self.position > 0 or (not self.end_of_menu and self.position == 0):
            self.end_of_menu = False
            self.position -= 1
            self.set_state()
            element: Element = self.state_machine.current_state
            if self.reset_item_state_onchange:
                element.reset()
            self.play_scroll_sound()

        return EVENT_HANDLED

    def navigate_to_beginning(self) -> bool:
        self.position = 0
        self.set_state()
        self.play_border_sound()
        return EVENT_HANDLED

    def navigate_to_end(self) -> bool:
        self.position = len(self.state_machine.states) - 1
        speech_manager.silence()
        self.set_state()
        self.play_border_sound()
        return EVENT_HANDLED

    def on_action(self) -> bool:
        self.play_select_sound()
        return EVENT_HANDLED

    def navigate_by_first_letter(self, character: str) -> bool:
        letters: List[str] = list(map(lambda s: s.title[0].lower(), self.state_machine.states.values()))

        try:
            self.position = letters.index(character.lower())
            self.set_state()
        except ValueError:
            pass

        return EVENT_HANDLED

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

    def play_scroll_sound(self) -> bool:
        if self.scroll_sound:
            audio_manager.play_sound(self.scroll_sound, wait_until_done=True)
            return True

        return False

    def play_select_sound(self) -> bool:
        if self.select_sound:
            audio_manager.play_sound(self.select_sound, wait_until_done=True)
            return True

        return False

    def play_open_sound(self) -> bool:
        if self.open_sound:
            audio_manager.play_sound(self.open_sound, wait_until_done=True)
            return True

        return False

    def play_border_sound(self) -> bool:
        if self.border_sound:
            audio_manager.play_sound(self.border_sound, wait_until_done=True)
            return True

        return False

    def reset(self):
        self.position = self.default_position
        self.end_of_menu = False
        state_key: str =  list(self.state_machine.states)[self.position]
        self.state_machine.current_state = self.state_machine.states[state_key]

        for item in self.state_machine.states.values():
            item.reset()
