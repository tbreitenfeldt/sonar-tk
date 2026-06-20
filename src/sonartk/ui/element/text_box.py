from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, List, Optional

import pyperclip
from pyglet.window import key

from sonartk.ui.element.element import Element
from sonartk.util import speech_manager

if TYPE_CHECKING:
    from sonartk.ui.screen.screen import Screen


class TextBox(Element):
    def __init__(
        self,
        parent: Screen,
        label: str = "",
        default_value: str = "",
        hidden: bool = False,
        allowed_chars: str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ 1234567890!@#$%^&*()_+-=`~[]{}\\;:'\",<.>/?|",
        echo_characters: bool = True,
        echo_words: bool = True,
        disable_up_down_keys: bool = False,
        enable_input_history: bool = False,
        read_only: bool = False,
        text_box_size: int = 80,
    ) -> None:
        # Set attributes before super().__init__() since bind_keys() needs them
        self.default_value: str = default_value
        self.input: List[str] = list(default_value)
        self.hidden: bool = hidden
        self.allowed_chars: str = allowed_chars
        self.echo_characters: bool = echo_characters
        self.echo_words: bool = echo_words
        self.disable_up_down_keys: bool = disable_up_down_keys
        self.enable_input_history: bool = enable_input_history
        self.input_history: List[str] = []
        self.input_history_position: int = -1
        self._history_editing_value: str = ""
        self.read_only: bool = read_only
        self.text_box_size: int = text_box_size
        self.position: int = 0
        self.left_selection_index: int = -1
        self.right_selection_index: int = -1
        self.selecting_left: bool = False
        self.selecting_right: bool = False

        super().__init__(
            parent=parent, label=label, value=default_value, role="edit"
        )

    # override
    def bind_keys(self) -> None:
        """Bind editing, navigation, clipboard, and selection shortcuts."""
        self.key_handler.add_key_press(self.select_all, key.A, [key.MOD_CTRL])
        self.key_handler.add_key_press(
            self.move_word_selection_right,
            key.RIGHT,
            [key.MOD_CTRL, key.MOD_SHIFT],
        )
        self.key_handler.add_key_press(
            self.move_word_selection_left,
            key.LEFT,
            [key.MOD_CTRL, key.MOD_SHIFT],
        )
        self.key_handler.add_key_press(
            self.move_letter_selection_right, key.RIGHT, [key.MOD_SHIFT]
        )
        self.key_handler.add_key_press(
            self.move_letter_selection_left, key.LEFT, [key.MOD_SHIFT]
        )
        self.key_handler.add_key_press(self.submit, key.RETURN)

        if not self.disable_up_down_keys:
            self.key_handler.add_key_press(self.previous_history_value, key.UP)
            self.key_handler.add_key_press(self.next_history_value, key.DOWN)

        self.key_handler.add_text_motion(self.next_word, key.MOTION_NEXT_WORD)
        self.key_handler.add_text_motion(
            self.previous_word, key.MOTION_PREVIOUS_WORD
        )
        self.key_handler.add_text_motion(self.next_character, key.MOTION_RIGHT)
        self.key_handler.add_text_motion(
            self.previous_character, key.MOTION_LEFT
        )
        self.key_handler.add_text_motion(
            self.move_home, key.MOTION_BEGINNING_OF_LINE
        )
        self.key_handler.add_text_motion(self.move_end, key.MOTION_END_OF_LINE)
        self.key_handler.add_key_press(
            self.copy_to_clipboard, key.C, [key.MOD_CTRL]
        )

        if not self.read_only:
            self.key_handler.add_key_press(
                self.paste_from_clipboard, key.V, [key.MOD_CTRL]
            )
            self.key_handler.add_text_motion(
                self.delete_previous_character, key.MOTION_BACKSPACE
            )
            self.key_handler.add_text_motion(
                self.delete_next_character, key.MOTION_DELETE
            )
            self.key_handler.add_on_text_input(self.type_character)

    # override
    @property
    def value(self) -> Optional[str]:
        """Return the current textbox content as a string."""
        return self.get_value()

    # override
    @value.setter
    def value(self, value: str) -> None:
        """Return the current textbox content as a string."""
        self.replace_value(value)

    def replace_value(self, value: str, announce: bool = False) -> None:
        """Replace the textbox content and optionally speak the new value."""
        self._value = value
        self.input = list(value)
        self.position = len(self.input)
        self.left_selection_index = -1
        self.right_selection_index = -1
        self.selecting_left = False
        self.selecting_right = False

        if announce:
            self.output_value()

    # override
    def setup(  # type: ignore[override]
        self,
        change_state: Callable[[str, Any], None],
        interrupt_speech: bool = True,
    ) -> bool:
        """Announce current content and read-only state when focused."""
        super().setup(change_state, interrupt_speech)
        output_value: str = self.get_value()
        if output_value == "":
            output_value = "Blank"
        if self.read_only:
            output_value = "Read Only " + output_value

        speech_manager.output(output_value, interrupt=False, log_message=False)
        return True

    def delete_previous_character(self) -> bool:
        """Delete the character before the cursor or current selection."""
        output_value: str = ""
        if self.input:
            if self.is_selected():
                self.delete_selection()

                if self.position == 0:
                    speech_manager.output(
                        "blank", interrupt=True, log_message=False
                    )
                else:
                    output_value = self.input[self.position - 1]
                    if output_value == " ":
                        output_value = "space"
                    speech_manager.output(
                        output_value, interrupt=True, log_message=False
                    )

            elif self.position > 0:
                output_value = self.input[self.position - 1]

                if self.hidden:
                    output_value = "star"
                elif output_value == " ":
                    output_value = "space"
                elif output_value.isupper():
                    output_value = "Cap " + output_value

                speech_manager.output(
                    output_value, interrupt=True, log_message=False
                )
                del self.input[self.position - 1]
                self.position -= 1
        else:
            speech_manager.output("Blank", interrupt=True, log_message=False)

        return True

    def delete_next_character(self) -> bool:
        """Delete the character at or after the cursor or current selection."""
        output_value: str = ""
        if self.input:
            if self.is_selected():
                self.delete_selection()

                if self.position >= len(self.input):
                    speech_manager.output(
                        "blank", interrupt=True, log_message=False
                    )
                else:
                    output_value = self.input[self.position]
                    if output_value == " ":
                        output_value = "space"
                    speech_manager.output(
                        output_value, interrupt=True, log_message=False
                    )

            elif self.position + 1 <= len(self.input) - 1:
                output_value = self.input[self.position + 1]

                if self.hidden:
                    output_value = "star"
                elif output_value == " ":
                    output_value = "space"
                elif output_value.isupper():
                    output_value = "Cap " + output_value

                speech_manager.output(
                    output_value, interrupt=True, log_message=False
                )
                del self.input[self.position]
            elif self.position == len(self.input) - 1:
                speech_manager.output(
                    "Blank", interrupt=True, log_message=False
                )
                del self.input[self.position]
            elif self.position >= len(self.input):
                speech_manager.output(
                    "Blank", interrupt=True, log_message=False
                )
        else:
            speech_manager.output("Blank", interrupt=True, log_message=False)

        return True

    def output_value(self) -> bool:
        """Speak the full textbox value, masking characters when hidden."""
        output_value: str = self.get_value()

        if output_value == "":
            output_value = "Blank"
        elif self.hidden:
            output_value = "star" * len(self.input)

        speech_manager.output(output_value, interrupt=True, log_message=False)

        return True

    def next_word(self) -> bool:
        """Move to the next word boundary and announce the word at that position."""
        value: str = "".join(self.input)
        index: int = 0
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

            word = value[self.position : index]

            if self.hidden:
                word = "Star " * len(word)
            elif word == "":
                word = "space"
        else:
            self.position = index
            word = "blank"

        speech_manager.output(word, interrupt=True, log_message=False)

        self.clear_selection()
        return True

    def previous_word(self) -> bool:
        """Move to the previous word boundary and announce the word at that position."""
        value: str = "".join(self.input)
        index: int = 0
        word: str = ""

        if self.position > 0:
            if self.input[self.position - 1] == " ":
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

        word = value[self.position : index]
        if self.hidden:
            word = "Star " * len(word)
        elif word == "" and value[self.position] == " ":
            word = "space"

        speech_manager.output(word, interrupt=True, log_message=False)

        self.clear_selection()
        return True

    def next_character(self) -> bool:
        """Move cursor right and announce the newly focused character."""
        if (
            self.left_selection_index == 0
            and self.right_selection_index == len(self.input)
        ):
            self.position = len(self.input)
            speech_manager.output("Blank", interrupt=True, log_message=False)
        elif self.position + 1 == len(self.input):
            speech_manager.output("blank", interrupt=True, log_message=False)
            self.position += 1
        elif self.position + 1 > len(self.input):
            speech_manager.output("blank", interrupt=True, log_message=False)
        else:
            self.position += 1

            if self.hidden:
                speech_manager.output(
                    "star", interrupt=True, log_message=False
                )
            else:
                if self.input[self.position] == " ":
                    speech_manager.output(
                        "space", interrupt=True, log_message=False
                    )
                else:
                    output_value: str = self.input[self.position]
                    if output_value.isupper():
                        output_value = "Cap " + self.input[self.position]
                    speech_manager.output(
                        output_value, interrupt=True, log_message=False
                    )

        self.clear_selection()
        return True

    def previous_character(self) -> bool:
        """Move cursor left and announce the newly focused character."""
        if (
            self.left_selection_index == 0
            and self.right_selection_index == len(self.input)
        ):
            self.position = 0
            speech_manager.output(
                self.input[self.position], interrupt=True, log_message=False
            )
        elif self.position - 1 < 0:
            if self.input:
                if self.input[0] == " ":
                    speech_manager.output(
                        "space", interrupt=True, log_message=False
                    )
                else:
                    speech_manager.output(
                        self.input[0], interrupt=True, log_message=False
                    )
            else:
                speech_manager.output(
                    "blank", interrupt=True, log_message=False
                )
        else:
            self.position -= 1

            if self.hidden:
                speech_manager.output(
                    "star", interrupt=True, log_message=False
                )
            else:
                if self.input[self.position] == " ":
                    speech_manager.output(
                        "space", interrupt=True, log_message=False
                    )
                else:
                    output_value: str = self.input[self.position]
                    if output_value.isupper():
                        output_value = "Cap " + output_value
                    speech_manager.output(
                        output_value, interrupt=True, log_message=False
                    )

        self.clear_selection()
        return True

    def move_letter_selection_right(self) -> bool:
        """Extend or shrink selection one character to the right."""
        selection_text: str = "Selected"

        if self.selecting_left:
            selection_text = "Unselected"
        if self.position + 1 <= len(self.input):
            if self.hidden:
                speech_manager.output(
                    "star " + selection_text, interrupt=True, log_message=False
                )
            else:
                if self.input[self.position] == " ":
                    speech_manager.output(
                        "space " + selection_text,
                        interrupt=True,
                        log_message=False,
                    )
                else:
                    output_value: str = (
                        self.input[self.position] + " " + selection_text
                    )
                    if self.input[self.position].isupper():
                        output_value = "Cap " + self.input[self.position]
                    speech_manager.output(
                        output_value, interrupt=True, log_message=False
                    )

            previous_position: int = self.position
            self.position += 1
            self.set_right_selection(previous_position, self.position)

        return True

    def move_letter_selection_left(self) -> bool:
        """Extend or shrink selection one character to the left."""
        selection_text: str = "Selected"

        if self.selecting_right:
            selection_text = "Unselected"
        if self.position - 1 >= 0:
            previous_position: int = self.position
            self.position -= 1

            if self.hidden:
                speech_manager.output(
                    "star " + selection_text, interrupt=True, log_message=False
                )
            else:
                if self.input[self.position] == " ":
                    speech_manager.output(
                        "space " + selection_text,
                        interrupt=True,
                        log_message=False,
                    )
                else:
                    output_value: str = self.input[self.position]
                    if output_value.isupper():
                        output_value = "Cap " + output_value
                    output_value = output_value + " " + selection_text
                    speech_manager.output(
                        output_value, interrupt=True, log_message=False
                    )

            self.set_left_selection(self.position, previous_position)

        return True

    def move_word_selection_right(self) -> bool:
        """Extend or shrink selection one word to the right."""
        value: str = self.get_value()
        index: int = 0
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
            word = value[self.position : index]

            if self.hidden:
                word = "Star " * len(word)
            elif word == " " or (word == "" and value[self.position] == " "):
                word = "space"

            if index >= len(value):
                self.position = index
            else:
                self.position = index + 1
            speech_manager.output(
                word + " " + selection_text, interrupt=True, log_message=False
            )
            self.set_right_selection(previous_position, self.position)

        return True

    def move_word_selection_left(self) -> bool:
        """Extend or shrink selection one word to the left."""
        value: str = "".join(self.input)
        index: int = 0
        word: str = ""
        selection_text: str = "Selected"
        previous_position: int = self.position

        if self.selecting_right:
            selection_text = "Unselected"

        if self.position > 0:
            if self.input[self.position - 1] == " ":
                self.position -= 1

            try:
                index = value.rindex(" ", 0, self.position)
            except ValueError:
                index = 0

            word = value[index : self.position]
            self.position = index
            if self.position > 0:
                self.position += 1

            if self.hidden:
                word = "Star " * len(word)
            elif word == " " or (word == "" and value[self.position] == " "):
                word = "space"

            speech_manager.output(
                word + " " + selection_text, interrupt=True, log_message=False
            )
            self.set_left_selection(self.position, previous_position)

        return True

    def select_all(self) -> bool:
        """Select the entire textbox content and announce the selection."""
        if (
            self.input
            and self.left_selection_index != 0
            and self.right_selection_index != len(self.input)
        ):
            self.left_selection_index = 0
            self.right_selection_index = len(self.input)
            self.selecting_right = True
            self.position = len(self.input)
            speech_manager.output(
                self.get_value() + " Selected",
                interrupt=True,
                log_message=False,
            )

        return True

    def submit(self) -> bool:
        """Emit the submit event for the textbox value."""
        self._record_history_value()
        self.dispatch_event("on_submit", self)
        return True

    def previous_history_value(self) -> bool:
        """Recall the previous history value, or read current value when unavailable."""
        if not self.enable_input_history or not self.input_history:
            return self.output_value()

        if self.input_history_position == -1:
            self._history_editing_value = self.get_value()
            self.input_history_position = len(self.input_history) - 1
        elif self.input_history_position > 0:
            self.input_history_position -= 1

        recalled = self.input_history[self.input_history_position]
        self.replace_value(recalled, announce=True)
        return True

    def next_history_value(self) -> bool:
        """Recall the next history value, or read current value at the history bottom."""
        if not self.enable_input_history or not self.input_history:
            return self.output_value()

        if self.input_history_position == -1:
            return self.output_value()

        if self.input_history_position < len(self.input_history) - 1:
            self.input_history_position += 1
            recalled = self.input_history[self.input_history_position]
            self.replace_value(recalled, announce=True)
            return True

        self.input_history_position = -1
        self.replace_value(self._history_editing_value, announce=True)
        return True

    def _record_history_value(self) -> None:
        """Store submitted input in history when enabled."""
        if not self.enable_input_history:
            return

        current = self.get_value()
        if current == "":
            self.input_history_position = -1
            self._history_editing_value = ""
            return

        if not self.input_history or self.input_history[-1] != current:
            self.input_history.append(current)

        self.input_history_position = -1
        self._history_editing_value = ""

    def copy_to_clipboard(self) -> bool:
        """Copy current selection to the clipboard when a selection exists."""
        if self.is_selected():
            pyperclip.copy(
                self.get_value()[
                    self.left_selection_index : self.right_selection_index
                ]
            )
            speech_manager.output(
                "Copied selection to clipboard",
                interrupt=True,
                log_message=False,
            )

        return True

    def paste_from_clipboard(self) -> bool:
        """Insert clipboard text at the cursor when size limits allow."""
        value: str = pyperclip.paste()

        if len(value) + len(self.input) <= self.text_box_size:
            if self.is_selected():
                self.delete_selection()

            self.input[self.position : self.position] = list(value)
            self.position += len(value)
            speech_manager.output(
                "Pasted " + value, interrupt=True, log_message=False
            )

        return True

    def move_home(self) -> bool:
        """Move the cursor to the beginning and announce the first character."""
        self.position = 0
        if not self.input:
            speech_manager.output("blank", interrupt=True, log_message=False)
        elif self.hidden:
            speech_manager.output("star", interrupt=True, log_message=False)
        else:
            if self.input[self.position] == " ":
                speech_manager.output(
                    "space", interrupt=True, log_message=False
                )
            else:
                output_value = self.input[self.position]
                if output_value.isupper():
                    output_value = "Cap " + self.input[self.position]
                speech_manager.output(
                    output_value, interrupt=True, log_message=False
                )

        self.clear_selection()
        return True

    def move_end(self) -> bool:
        """Move the cursor to the end and announce blank."""
        self.position = len(self.input)
        speech_manager.output("blank", interrupt=True, log_message=False)

        self.clear_selection()
        return True

    def type_character(self, character: str) -> bool:
        """Insert an allowed character and perform speech feedback."""
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
                            start_of_word = value.rindex(
                                " ", 0, self.position - 1
                            )
                        except ValueError:
                            start_of_word = 0

                        output_value = value[start_of_word : self.position - 1]
                        if output_value == " ":
                            output_value = "space"
                    else:
                        output_value = "space"

                if character == " " or self.echo_characters:
                    if output_value.isupper():
                        speech_manager.output(
                            "Cap " + output_value,
                            interrupt=True,
                            log_message=False,
                        )
                    else:
                        speech_manager.output(
                            output_value, interrupt=True, log_message=False
                        )

            return True

        return False

    def get_value(self) -> str:
        """Return the textbox content by joining the internal character buffer."""
        return "".join(self.input)

    def is_selected(self) -> bool:
        """Return whether any text range is currently selected."""
        return (
            self.left_selection_index > -1 or self.right_selection_index > -1
        )

    def clear_selection(self) -> None:
        """Clear selection tracking and announce unselection when needed."""
        if self.left_selection_index > -1 or self.right_selection_index > -1:
            if self.left_selection_index != self.right_selection_index:
                speech_manager.output(
                    "Unselected", interrupt=False, log_message=False
                )

            self.left_selection_index = -1
            self.right_selection_index = -1
            self.selecting_left = False
            self.selecting_right = False

    def set_right_selection(
        self, previous_position: int, next_position: int
    ) -> None:
        """Update selection bounds while extending selection rightward."""
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

    def set_left_selection(
        self, previous_position: int, next_position: int
    ) -> None:
        """Update selection bounds while extending selection leftward."""
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

    def delete_selection(self) -> None:
        """Delete the currently selected character range."""
        if self.is_selected():
            counter: int = 0
            index: int = 0

            while counter < self.right_selection_index:
                if (
                    counter >= self.left_selection_index
                    and counter < self.right_selection_index
                ):
                    del self.input[index]
                    self.position = index
                else:
                    index += 1

                counter += 1

            self.clear_selection()

    # override
    def reset(self) -> None:
        """Restore default value and clear cursor and selection state."""
        self.value = self.default_value
        self.input = list(self.default_value)
        self.position = 0
        self.left_selection_index = -1
        self.right_selection_index = -1
        self.selecting_left = False
        self.selecting_right = False


TextBox.register_event_type("on_submit")
