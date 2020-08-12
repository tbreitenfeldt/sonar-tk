from typing import Dict, Callable, List

from pyglet.window import key
from pyglet.event import EVENT_HANDLED

from ui.elements import Element
from state_machine import StateMachine, EmptyState
from utils import audio_manager
from utils import speech_manager
from utils import KeyHandler

class BasicMenuItem(Element[str]):

    def __init__(self, parent: "Tab", title: str) -> None:
        super().__init__(parent=parent, title=title, value="", type="", callback=None, callback_args=None, use_key_handler=False)

    def on_action(self) -> bool:
        return True

    def __repr__(self):
        return self.title


class Menu(Element[str]):

    def __init__(
        self, parent: "Tab", title: str = "", is_border: bool = True, is_first_letter_navigation: bool = True, is_side_menu: bool = False,
        callback: Callable[[Callable[[str, any], None], str, any], None] = None, callback_args: List[any] = [], scroll_sound: str = "", select_sound: str = "", open_sound: str = "",
        border_sound: str = "", music: str = ""
    ) -> None:
        super().__init__(parent=parent, title=title, value="", type="Menu", callback=callback, callback_args=callback_args)
        self.is_border: bool = is_border
        self.is_first_letter_navigation: bool = is_first_letter_navigation  
        self.is_side_menu: bool = is_side_menu
        self.scroll_sound: str = scroll_sound
        self.select_sound: str = select_sound
        self.open_sound: str = open_sound
        self.border_sound: str = border_sound
        self.music: str = music
        self.position: int = 0
        self.end_of_menu: bool = 0
        self.state_machine: StateMachine = StateMachine()
        self.bind_keys()

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
        self.state_machine.change(value)

    def setup(self, change_state: Callable[[str, any], None], interrupt_speech: bool = True) -> bool:
        super().setup(change_state, interrupt_speech)

        if self.music:
            audio_manager.load_music(self.music)
            audio_manager.play_music(loops=-1)

        self.play_open_sound()

        if not isinstance(self.state_machine.current_state, EmptyState):
            self.state_machine.setup(interrupt_speech=False)
        else:
            self.set_state(interrupt_speech=False)

        return True

    def update(self, delta_time: float) -> bool:
        super().update(delta_time)
        return self.state_machine.update(delta_time)

    def exit(self) -> bool:
        self.state_machine.current_state.exit()
        self.pop_handlers()
        return True

    def next_item(self) -> bool:
        if self.state_machine.size() == 1:
            self.set_state()
        elif not self.end_of_menu and self.position + 1 >= self.state_machine.size():
            if self.is_border:
                self.end_of_menu = True
                self.position = len(self.state_machine.states) - 1
                self.play_border_sound()
            else:
                self.position = 0
                self.set_state()

                if not self.play_border_sound():
                    self.play_scroll_sound()

        elif self.position + 1 < self.state_machine.size():
            self.end_of_menu = False
            self.position += 1
            self.set_state()
            self.play_scroll_sound()

        return EVENT_HANDLED

    def previous_item(self) -> bool:
        if len(self.state_machine.states) == 1:
            self.set_state()
        elif not self.end_of_menu and self.position - 1 < 0:
            if self.is_border:
                self.end_of_menu = True
                self.position = 0
                self.play_border_sound()
            else:
                self.position = len(self.state_machine.states) - 1
                self.set_state()

                if not self.play_border_sound():
                    self.play_scroll_sound()

        elif self.position > 0:
            self.end_of_menu = False
            self.position -= 1
            self.set_state()
            self.play_scroll_sound()
        elif not self.end_of_menu and self.position == 0:
            self.end_of_menu = False
            self.position -= 1
            self.set_state()
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

    def add(self, key: str, item: any) -> None:
        if isinstance(item, str):
            self.state_machine.add(key, BasicMenuItem(self, item))
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
