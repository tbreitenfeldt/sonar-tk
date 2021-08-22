from typing import List, Callable
import re

from pyglet.window import key
from pyglet.event import EVENT_HANDLED, EVENT_UNHANDLED
import pyperclip

from audio_ui.state import State
from audio_ui.elements import Element
from audio_ui.utils import audio_manager
from audio_ui.utils import speech_manager
from audio_ui.utils import KeyHandler

class TextBox(Element):

    def __init__(
        self, parent: State, title: str = "", default_value: str = "", hidden: bool = False,
        allowed_chars: str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ 1234567890!@#$%^&*()_+-=`~[]{}\;:\'\",<.>/?|",
        echo_characters: bool = True, echo_words: bool = True, disable_up_down_keys: bool = False, read_only: bool = False, text_box_size: int = 80,
        onsubmit_callback: Callable[[Callable[[str, any], None], str, any], None] = None, callback_args: List[any] = [],
        open_sound: str = "", typing_sound: str = "", border_sound: str = "", submit_sound: str = "", delete_sound: str = "", navigate_sound: str = "", music: str = "",
    ) -> None:
        super().__init__(parent=parent, title=title, value=default_value, type="Edit", callback=onsubmit_callback, callback_args=callback_args)
        self.default_value: str = default_value
        self.input: List[str] = list(default_value)
        self.hidden: bool = hidden
        self.allowed_chars: str = allowed_chars
        self.echo_characters: bool = echo_characters
        self.echo_words: bool = echo_words
        self.disable_up_down_keys: bool = disable_up_down_keys
        self.read_only: bool = read_only
        self.text_box_size: int = text_box_size
        self.open_sound: str = open_sound
        self.typing_sound: str = typing_sound
        self.border_sound: str = border_sound
        self.submit_sound: str = submit_sound
        self.delete_sound: str = delete_sound
        self.navigate_sound: str = navigate_sound
        self.music: str = music
        self.position: int = 0
        self.left_selection_index: int = -1
        self.right_selection_index: int = -1
        self.selecting_left: bool = False
        self.selecting_right: bool = False
        self.bind_keys()

    def bind_keys(self) -> None:
        self.key_handler.add_key_press(self.select_all, key.A, [key.MOD_CTRL])
        self.key_handler.add_key_press(self.move_word_selection_right, key.RIGHT, [key.MOD_CTRL, key.MOD_SHIFT])
        self.key_handler.add_key_press(self.move_word_selection_left, key.LEFT, [key.MOD_CTRL, key.MOD_SHIFT])
        self.key_handler.add_key_press(self.move_letter_selection_right, key.RIGHT, [key.MOD_SHIFT])
        self.key_handler.add_key_press(self.move_letter_selection_left, key.LEFT, [key.MOD_SHIFT])
        self.key_handler.add_key_press(self.submit, key.RETURN)

        if not self.disable_up_down_keys:
            self.key_handler.add_key_press(self.output_value, key.UP)
            self.key_handler.add_key_press(self.output_value, key.DOWN)

        self.key_handler.add_text_motion(self.next_word, key.MOTION_NEXT_WORD)
        self.key_handler.add_text_motion(self.previous_word, key.MOTION_PREVIOUS_WORD)
        self.key_handler.add_text_motion(self.next_character, key.MOTION_RIGHT)
        self.key_handler.add_text_motion(self.previous_character, key.MOTION_LEFT)
        self.key_handler.add_text_motion(self.move_home, key.MOTION_BEGINNING_OF_LINE)
        self.key_handler.add_text_motion(self.move_end, key.MOTION_END_OF_LINE)
        self.key_handler.add_key_press(self.copy_to_clipboard, key.C, [key.MOD_CTRL])

        if not self.read_only:
            self.key_handler.add_key_press(self.paste_from_clipboard, key.V, [key.MOD_CTRL])
            self.key_handler.add_text_motion(self.delete_previous_character, key.MOTION_BACKSPACE)
            self.key_handler.add_text_motion(self.delete_next_character, key.MOTION_DELETE)
            self.key_handler.add_on_text_input(self.type_character)

    @property
    def value(self) -> str:
        return self.get_value()

    @value.setter
    def value(self, value: str) -> None:
        self.input = list(value)

    def setup(self, change_state: Callable[[str, any], None], interrupt_speech: bool = True) ->bool:
        super().setup(change_state, interrupt_speech)

        if self.music:
            audio_manager.load_music(self.music)
            audio_manager.play_music(loops=-1)
        if self.open_sound != "":
            audio_manager.play_sound(self.open_sound)

        self.play_open_sound()

        output_value: str = self.get_value()
        if self.get_value() == "":
            output_value = "Blank"
        if self.read_only:
            output_value = "Read Only " + output_value

        speech_manager.output(output_value, interrupt=False, log_message=False)
        return True

    def delete_previous_character(self) -> bool:
        if self.input:
            if self.is_selected():
                self.delete_selection()

                if self.position == 0:
                    speech_manager.output("blank", interrupt=True, log_message=False)
                else:
                    output_value: str = self.input[self.position-1]
                    if output_value == " ":
                        output_value = "space"
                    speech_manager.output(output_value, interrupt=True, log_message=False)

            elif self.position > 0:
                output_value: str = self.input[self.position-1]

                if self.hidden:
                    output_value = "star"
                elif output_value == " ":
                    output_value = "space"
                elif output_value.isupper():
                    output_value = "Cap " + output_value

                speech_manager.output(output_value, interrupt=True, log_message=False)
                del self.input[self.position-1]
                self.position -= 1
                self.play_delete_sound()
        else:
            speech_manager.output("Blank", interrupt=True, log_message=False)

        return EVENT_HANDLED

    def delete_next_character(self) -> bool:
        if self.input:
            if self.is_selected():
                self.delete_selection()

                if self.position >= len(self.input):
                    speech_manager.output("blank", interrupt=True, log_message=False)
                else:
                    output_value: str = self.input[self.position]
                    if output_value == " ":
                        output_value = "space"
                    speech_manager.output(output_value, interrupt=True, log_message=False)

            elif self.position + 1 <= len(self.input) - 1:
                output_value: str = self.input[self.position+1]

                if self.hidden:
                    output_value = "star"
                elif output_value == " ":
                    output_value = "space"
                elif output_value.isupper():
                    output_value = "Cap " + output_value

                speech_manager.output(output_value, interrupt=True, log_message=False)
                del self.input[self.position]
                self.play_delete_sound()
            elif self.position == len(self.input) - 1:
                speech_manager.output("Blank", interrupt=True, log_message=False)
                del self.input[self.position]
                self.play_delete_sound()
            elif self.position >= len(self.input):
                speech_manager.output("Blank", interrupt=True, log_message=False)
        else:
            speech_manager.output("Blank", interrupt=True, log_message=False)

        return EVENT_HANDLED

    def output_value(self) -> bool:
        if not self.hidden:
            speech_manager.output(self.get_value(), interrupt=True, log_message=False)
        else:
            speech_manager.output("star" * len(self.input), interrupt=True, log_message=False)

        return EVENT_HANDLED

    def next_word(self) -> bool:
        value: str = "".join(self.input)
        index: str = 0
        word: str = ""

        try:
            index = value.index(" ", self.position, len(value))
        except ValueError:
            index = len(value)

        if index < len(value):
            self.position = index + 1
            try:
                index = value.index(" ", self.position, len(value))
            except ValueError:
                index = len(value)

            word = value[self.position:index]

            if self.hidden:
                word = "Star " * len(word)
            elif word == "":
                word = "space"
        else:
            self.position = index
            word = "blank"

        if word == " ":
            word = "space"

        speech_manager.output(word, interrupt=True, log_message=False)
        self.play_navigate_sound()

        self.clear_selection()
        return EVENT_HANDLED

    def previous_word(self) -> bool:
        value: str = "".join(self.input)
        index: str = 0
        word: str = ""

        if self.position > 0:
            if self.input[self.position-1] == " ":
                self.position -= 1

            try:
                index = value.rindex(" ", 0, self.position)
            except ValueError:
                index = 0

            self.position = index
            if self.position > 0:
                self.position += 1

        try:
            index = value.index(" ", self.position, len(value))
        except ValueError:
            index = len(value)

        word = value[self.position:index]
        if self.hidden:
            word = "Star " * len(word)
        elif word == " " or (word == "" and value[self.position] == " "):
            word = "space"

        speech_manager.output(word, interrupt=True, log_message=False)
        self.play_navigate_sound()

        self.clear_selection()
        return EVENT_HANDLED

    def next_character(self) -> bool:
        if self.left_selection_index == 0 and self.right_selection_index == len(self.input):
            self.position = len(self.input)
            speech_manager.output("Blank", interrupt=True, log_message=False)
        elif self.position + 1 == len(self.input):
            speech_manager.output("blank", interrupt=True, log_message=False)
            self.position += 1
            self.play_border_sound()
        elif self.position + 1 > len(self.input):
            speech_manager.output("blank", interrupt=True, log_message=False)
            self.play_border_sound()
        else:
            self.position += 1

            if self.hidden:
                speech_manager.output("star", interrupt=True, log_message=False)
            else:
                if self.input[self.position] == " ":
                    speech_manager.output("space", interrupt=True, log_message=False)
                else:
                    output_value: str = self.input[self.position]
                    if output_value.isupper():
                        output_value = "Cap " + self.input[self.position]
                    speech_manager.output(output_value, interrupt=True, log_message=False)

            self.play_navigate_sound()

        self.clear_selection()
        return EVENT_HANDLED

    def previous_character(self) -> bool:
        if self.left_selection_index == 0 and self.right_selection_index == len(self.input):
            self.position = 0
            speech_manager.output(self.input[self.position], interrupt=True, log_message=False)
        elif self.position - 1 < 0:
            self.play_border_sound()

            if self.input:
                if self.input[0] == " ":
                    speech_manager.output("space", interrupt=True, log_message=False)
                else:
                    speech_manager.output(self.input[0], interrupt=True, log_message=False)
            else:
                speech_manager.output("blank", interrupt=True, log_message=False)
        else:
            self.position -= 1

            self.play_navigate_sound()
            if self.hidden:
                speech_manager.output("star", interrupt=True, log_message=False)
            else:
                if self.input[self.position] == " ":
                    speech_manager.output("space", interrupt=True, log_message=False)
                else:
                    output_value: str = self.input[self.position]
                    if output_value.isupper():
                        output_value = "Cap " + output_value
                    speech_manager.output(output_value, interrupt=True, log_message=False)

            self.play_navigate_sound()

        self.clear_selection()
        return EVENT_HANDLED

    def move_letter_selection_right(self) -> bool:
        selection_text: str = "Selected"

        if self.selecting_left:
            selection_text = "Unselected"
        if self.position + 1 <= len(self.input):
            if self.hidden:
                speech_manager.output("star " + selection_text, interrupt=True, log_message=False)
            else:
                if self.input[self.position] == " ":
                    speech_manager.output("space " + selection_text, interrupt=True, log_message=False)
                else:
                    output_value: str = self.input[self.position] + " " + selection_text
                    if output_value.isupper():
                        output_value = "Cap " + self.input[self.position]
                    speech_manager.output(output_value, interrupt=True, log_message=False)

            previous_position: int = self.position
            self.position += 1
            self.set_right_selection(previous_position, self.position)

        return EVENT_HANDLED

    def move_letter_selection_left(self) -> bool:
        selection_text: str = "Selected"

        if self.selecting_right:
            selection_text = "Unselected"
        if self.position - 1 >= 0:
            previous_position: int = self.position
            self.position -= 1

            if self.hidden:
                speech_manager.output("star " + selection_text, interrupt=True, log_message=False)
            else:
                if self.input[self.position] == " ":
                    speech_manager.output("space " + selection_text, interrupt=True, log_message=False)
                else:
                    output_value: str = self.input[self.position] + " " + selection_text
                    if output_value.isupper():
                        output_value = "Cap " + output_value
                    speech_manager.output(output_value, interrupt=True, log_message=False)

            self.set_left_selection(self.position, previous_position)

        return EVENT_HANDLED

    def move_word_selection_right(self) -> bool:
        value: str = self.get_value()
        index: str = 0
        word: str = ""
        selection_text: str = "Selected"
        previous_position: int = self.position

        if self.selecting_left:
            selection_text = "Unselected"

        try:
            index = value.index(" ", self.position, len(value))
        except ValueError:
            index = len(value)

        if self.position < len(value) and index <= len(value):
            word = value[self.position:index]

            if self.hidden:
                word = "Star " * len(word)
            elif word == " " or (word == "" and value[self.position] == " "):
                word = "space"

            if index >= len(value):
                self.position = index
            else:
                self.position = index + 1
            speech_manager.output(word + " " + selection_text, interrupt=True, log_message=False)
            self.set_right_selection(previous_position, self.position)

        return EVENT_HANDLED

    def move_word_selection_left(self) -> bool:
        value: str = "".join(self.input)
        index: str = 0
        word: str = ""
        selection_text: str = "Selected"
        previous_position: int = self.position

        if self.selecting_right:
            selection_text = "Unselected"

        if self.position > 0:
            if self.input[self.position-1] == " ":
                self.position -= 1

            try:
                index = value.rindex(" ", 0, self.position)
            except ValueError:
                index = 0

            word = value[index:self.position]
            self.position = index
            if self.position > 0:
                self.position += 1

            if self.hidden:
                word = "Star " * len(word)
            elif word == " " or (word == "" and value[self.position] == " "):
                word = "space"

            speech_manager.output(word + " " + selection_text, interrupt=True, log_message=False)
            self.set_left_selection(self.position, previous_position)

        return EVENT_HANDLED

    def select_all(self) -> bool:
        if self.input and self.left_selection_index != 0 and self.right_selection_index != len(self.input):
            self.left_selection_index = 0
            self.right_selection_index = len(self.input)
            self.selecting_right = True
            self.position = len(self.input)
            speech_manager.output(self.get_value() + " Selected", interrupt=True, log_message=False)

        return EVENT_HANDLED

    def on_action(self) -> bool:
        self.play_submit_sound()
        return EVENT_HANDLED

    def copy_to_clipboard(self) -> bool:
        if self.is_selected():
            pyperclip.copy(self.get_value()[self.left_selection_index:self.right_selection_index])
            speech_manager.output("Copied selection to clipboard", interrupt=True, log_message=False)

        return EVENT_HANDLED

    def paste_from_clipboard(self) -> bool:
        value: str = pyperclip.paste()

        if len(value) + len(self.input) <= self.text_box_size:
            if self.is_selected():
                self.delete_selection()

            self.input[self.position:self.position] = list(value)
            self.position += len(value)
            speech_manager.output("Pasted " + value, interrupt=True, log_message=False)

        return EVENT_HANDLED

    def move_home(self) -> bool:
        self.position = 0
        if not self.input:
                speech_manager.output("blank", interrupt=True, log_message=False)
        elif self.hidden:
                speech_manager.output("star", interrupt=True, log_message=False)
        else:
                if self.input[self.position] == " ":
                    speech_manager.output("space", interrupt=True, log_message=False)
                else:
                    output_value = self.input[self.position]
                    if output_value.isupper():
                        output_value = "Cap " + self.input[self.position]
                    speech_manager.output(output_value, interrupt=True, log_message=False)

        self.clear_selection()
        return EVENT_HANDLED

    def move_end(self) -> bool:
        self.position = len(self.input)
        speech_manager.output("blank", interrupt=True, log_message=False)

        self.clear_selection()
        return EVENT_HANDLED

    def type_character(self, character: str) -> bool:
        if character in self.allowed_chars:
            if self.is_selected():
                self.delete_selection()
    
            if len(self.input) < self.text_box_size:
                self.input.insert(self.position, character)
                self.position += 1
    
                output_value: str = character
    
                if self.hidden:
                    output_value = "star"
                elif character == " ":
                    if self.echo_words and self.position != 1:
                        value: str = "".join(self.input)
                        start_of_word: int = -1
    
                        try:
                            start_of_word = value.rindex(" ", 0, self.position-1)
                        except ValueError:
                            start_of_word = 0
    
                        output_value = value[start_of_word:self.position - 1]
                        if output_value == " ":
                            output_value = "space"
                    else:
                        output_value = "space"
    
                if character == " " or self.echo_characters:
                    if output_value.isupper():
                        speech_manager.output("Cap " + output_value, interrupt=True, log_message=False)
                    else:
                        speech_manager.output(output_value, interrupt=True, log_message=False)
    
            self.play_typing_sound()
    
            return EVENT_HANDLED

        return EVENT_UNHANDLED

    def get_value(self) -> str:
        return "".join(self.input)

    def is_selected(self) -> bool:
        return self.left_selection_index > -1 or self.right_selection_index > -1

    def clear_selection(self) -> None:
        if self.left_selection_index > -1 or self.right_selection_index > -1:
            if self.left_selection_index != self.right_selection_index:
                speech_manager.output("Unselected", interrupt=False, log_message=False)

            self.left_selection_index = -1
            self.right_selection_index = -1
            self.selecting_left = False
            self.selecting_right = False


    def set_right_selection(self, previous_position: int, next_position: int) -> None:
            if not self.selecting_left and not self.selecting_right:
                self.selecting_right = True
                self.left_selection_index = previous_position
                self.right_selection_index = next_position
            elif self.selecting_left:
                self.left_selection_index = next_position
                if self.left_selection_index >= self.right_selection_index:
                    self.clear_selection()
            elif self.selecting_right:
                self.right_selection_index = next_position
            else:
                raise ValueError("selecting_left and selecting_right can not both be true.")

    def set_left_selection(self, previous_position: int, next_position: int) -> None:
            if not self.selecting_left and not self.selecting_right:
                self.selecting_left = True
                self.left_selection_index = previous_position
                self.right_selection_index = next_position
            elif self.selecting_left:
                self.left_selection_index = previous_position
            elif self.selecting_right:
                self.right_selection_index = previous_position
                if self.left_selection_index >= self.right_selection_index:
                    self.clear_selection()
            else:
                raise ValueError("selecting_left and selecting_right can not both be true.")

    def delete_selection(self) -> None:
        if self.is_selected():
            counter: int = 0
            index: int = 0

            while counter < self.right_selection_index:
                if counter >= self.left_selection_index and counter < self.right_selection_index:
                    del self.input[index]
                    self.position = index
                else:
                    index += 1

                counter += 1

            self.clear_selection()

    def play_open_sound(self) -> bool:
        if self.open_sound:
            audio_manager.play(self.open_sound, wait_until_done=True)
            return True

        return False

    def play_typing_sound(self) -> bool:
        if self.typing_sound:
            audio_manager.play(self.typing_sound)
            return True

        return False     

    def play_submit_sound(self) -> bool:
        if self.submit_sound:
            audio_manager.play(self.submit_sound)
            return True

        return False

    def play_border_sound(self) -> bool:
        if self.border_sound:
            audio_manager.play(self.border_sound)
            return True

        return False

    def play_delete_sound(self) -> bool:
        if self.delete_sound:
            audio_manager.play(self.delete_sound)
            return True

        return False        

    def play_navigate_sound(self) -> bool:
        if self.navigate_sound:
            audio_manager.play(self.navigate_sound)
            return True

        return False

    def reset(self) -> None:
        self.value = default_value
        self.input = list(default_value)
        self.position = 0
        self.left_selection_index = -1
        self.right_selection_index = -1
        self.selecting_left = False
        self.selecting_right = False
