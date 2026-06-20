from __future__ import annotations

from bisect import bisect_right
from typing import TYPE_CHECKING, Any, Callable

from pyglet.window import key

from sonartk.ui.element.element import Element
from sonartk.ui.element.text_box import TextBox
from sonartk.util import speech_manager

if TYPE_CHECKING:
    from sonartk.ui.screen.screen import Screen


class MultilineTextBox(TextBox):
    """Read-only text viewer that supports line-by-line navigation."""

    def __init__(
        self,
        parent: Screen,
        label: str = "",
        default_value: str = "",
    ) -> None:
        self._preferred_column: int = 0
        self.lines: list[str] = self._split_lines(default_value)
        self._line_index: int = 0

        super().__init__(
            parent=parent,
            label=label,
            default_value=default_value,
            read_only=True,
            disable_up_down_keys=True,
        )
        self.role = "multiline text box"
        self._line_index = 0
        self.position = 0

    @property
    def line_index(self) -> int:
        """Return the currently selected line index."""
        return self._line_index

    @line_index.setter
    def line_index(self, line_index: int) -> None:
        """Set the selected line index and align caret to preferred column."""
        self.lines = self._split_lines(self.get_value())
        if self.line_count == 0:
            self._line_index = 0
            self.position = 0
            return

        clamped_index = max(0, min(line_index, self.line_count - 1))
        self._line_index = clamped_index
        self._move_to_column(self._line_index, self._preferred_column)

    # override
    def bind_keys(self) -> None:
        """Bind navigation keys for the read-only multiline viewer."""
        super().bind_keys()
        self.key_handler.add_key_press(self.previous_line, key.UP)
        self.key_handler.add_key_press(self.next_line, key.DOWN)
        self.key_handler.add_key_press(
            self.select_previous_line, key.UP, [key.MOD_SHIFT]
        )
        self.key_handler.add_key_press(
            self.select_next_line, key.DOWN, [key.MOD_SHIFT]
        )
        self.key_handler.add_key_press(self.move_home, key.HOME)
        self.key_handler.add_key_press(self.move_end, key.END)
        self.key_handler.add_key_press(
            self.go_to_start_of_text, key.HOME, [key.MOD_CTRL]
        )
        self.key_handler.add_key_press(
            self.go_to_end_of_text, key.END, [key.MOD_CTRL]
        )

    # override
    @property
    def value(self) -> str:
        """Return the full text content."""
        return self._value or ""

    # override
    @value.setter
    def value(self, value: str) -> None:
        """Replace the full text content and reset the line buffer."""
        self.replace_value(value, announce=False)

    # override
    def replace_value(self, value: str, announce: bool = False) -> None:
        """Replace text content and refresh line state."""
        super().replace_value(value, announce=False)
        self.position = 0
        self.lines = self._split_lines(value)
        self.line_index = 0
        self._preferred_column = 0

        if announce:
            self.speak_current_line()

    @property
    def line_count(self) -> int:
        """Return the number of visible lines."""
        return len(self.lines)

    @property
    def current_line(self) -> str:
        """Return the line currently selected by the cursor."""
        return self.lines[self.line_index]

    def select_line(self, line_index: int, announce: bool = True) -> bool:
        """Move to a specific line index and optionally speak it."""
        self.lines = self._split_lines(self.get_value())
        clamped_index = max(0, min(line_index, self.line_count - 1))
        if clamped_index != self.line_index:
            self.line_index = clamped_index
            self.dispatch_event("on_line_change", self)
        elif announce:
            self.dispatch_event("on_line_change", self)

        if announce:
            self.speak_current_line()

        return True

    # override
    def setup(  # type: ignore[override]
        self,
        change_state: Callable[[str, Any], None],
        interrupt_speech: bool = False,
    ) -> bool:
        """Announce the label (or role when label is empty) and the currently focused line."""
        Element.setup(self, change_state, interrupt_speech)
        if not self.label:
            speech_manager.output(
                self.role, interrupt=interrupt_speech, log_message=False
            )
        self.line_index = self._line_index_from_position()
        self._preferred_column = self._column_for_position(self.position)
        self.speak_current_line(interrupt=False)
        return True

    def speak_current_line(self, interrupt: bool = True) -> bool:
        """Speak the current line or a blank placeholder."""
        line = self.current_line
        if line.strip() == "":
            line = "Blank"

        speech_manager.output(line, interrupt=interrupt, log_message=False)
        return True

    def next_line(self) -> bool:
        """Move to the next line and announce it."""
        self.lines = self._split_lines(self.get_value())
        self.line_index = self._line_index_from_position()
        self._preferred_column = self._column_for_position(self.position)
        if self.line_index + 1 >= self.line_count:
            self.speak_current_line()
            return True

        return self.select_line(self.line_index + 1)

    def select_next_line(self) -> bool:
        """Extend selection to include the next line."""
        self.lines = self._split_lines(self.get_value())
        current_line_index = self._line_index_from_position()
        starts, ends = self._line_bounds()
        current_line_end = ends[current_line_index]

        if (
            current_line_index + 1 >= self.line_count
            and self.position >= current_line_end
        ):
            self._line_index = current_line_index
            self.speak_current_line()
            return True

        previous_position = self.position
        if self.position < current_line_end:
            next_position = current_line_end
        else:
            next_line_index = min(current_line_index + 1, self.line_count - 1)
            next_position = ends[next_line_index]

        self.position = next_position
        self._line_index = self._line_index_from_position()
        self._preferred_column = self._column_for_position(self.position)
        self.set_right_selection(previous_position, next_position)
        self._announce_selection_text(previous_position, next_position)
        return True

    def previous_line(self) -> bool:
        """Move to the previous line and announce it."""
        self.lines = self._split_lines(self.get_value())
        self.line_index = self._line_index_from_position()
        self._preferred_column = self._column_for_position(self.position)
        if self.line_index == 0:
            self.speak_current_line()
            return True

        return self.select_line(self.line_index - 1)

    def select_previous_line(self) -> bool:
        """Extend selection to include the previous line."""
        self.lines = self._split_lines(self.get_value())
        current_line_index = self._line_index_from_position()
        starts, ends = self._line_bounds()
        current_line_start = starts[current_line_index]

        if current_line_index == 0 and self.position <= current_line_start:
            self.speak_current_line()
            return True

        previous_position = self.position
        if self.position > current_line_start:
            next_position = current_line_start
        else:
            previous_line_index = max(current_line_index - 1, 0)
            next_position = starts[previous_line_index]

        self.position = next_position
        self._line_index = self._line_index_from_position()
        self._preferred_column = self._column_for_position(self.position)
        self.set_left_selection(next_position, previous_position)
        self._announce_selection_text(next_position, previous_position)
        return True

    def _announce_selection_text(
        self, start_position: int, end_position: int
    ) -> None:
        """Speak the selected text range using the same style as other selection commands."""
        start = min(start_position, end_position)
        end = max(start_position, end_position)
        selected_text = self.get_value()[start:end].replace("\n", " ").rstrip()

        if selected_text.strip() == "":
            selected_text = "Blank"

        speech_manager.output(
            f"{selected_text} Selected", interrupt=True, log_message=False
        )

    # override
    def move_word_selection_right(self) -> bool:
        """Extend or shrink selection one token to the right, treating newlines as tokens."""
        value = self.get_value()
        previous_position = self.position
        selection_text = "Selected"

        if self.selecting_left:
            selection_text = "Unselected"

        if self.position >= len(value):
            return True

        delimiters = {" ", "\n", "\r", "\t"}
        current_char = value[self.position]

        if current_char in delimiters:
            token = current_char
            next_position = self.position + 1
        else:
            index = self.position
            while index < len(value) and value[index] not in delimiters:
                index += 1
            token = value[self.position : index]
            next_position = index

        self.position = next_position
        self.set_right_selection(previous_position, self.position)
        self._speak_word_selection_token(token, selection_text)
        return True

    # override
    def move_word_selection_left(self) -> bool:
        """Extend or shrink selection one token to the left, treating newlines as tokens."""
        value = self.get_value()
        previous_position = self.position
        selection_text = "Selected"

        if self.selecting_right:
            selection_text = "Unselected"

        if self.position <= 0:
            return True

        delimiters = {" ", "\n", "\r", "\t"}
        previous_char = value[self.position - 1]

        if previous_char in delimiters:
            token = previous_char
            next_position = self.position - 1
        else:
            index = self.position
            while index > 0 and value[index - 1] not in delimiters:
                index -= 1
            token = value[index : self.position]
            next_position = index

        self.position = next_position
        self.set_left_selection(self.position, previous_position)
        self._speak_word_selection_token(token, selection_text)
        return True

    def _speak_word_selection_token(
        self, token: str, selection_text: str
    ) -> None:
        """Speak one selected token for word-selection commands."""
        output_token = token
        if self.hidden:
            output_token = "Star " * len(token)
        elif token == " " or token == "":
            output_token = "space"
        elif token in ("\n", "\r", "\r\n", "\n\r"):
            output_token = "Blank"
        elif token == "\t":
            output_token = "tab"

        speech_manager.output(
            f"{output_token} {selection_text}",
            interrupt=True,
            log_message=False,
        )

    # override
    def move_home(self) -> bool:
        """Move to the beginning of the current line and announce the character at the cursor."""
        self.lines = self._split_lines(self.get_value())
        self.line_index = self._line_index_from_position()
        starts, _ = self._line_bounds()
        self.position = starts[self.line_index]
        self._preferred_column = 0
        self.clear_selection()
        self._announce_character_at_cursor()
        return True

    # override
    def move_end(self) -> bool:
        """Move to the end of the current line and announce the character at the cursor."""
        self.lines = self._split_lines(self.get_value())
        self.line_index = self._line_index_from_position()
        _, ends = self._line_bounds()
        self.position = ends[self.line_index]
        self._preferred_column = self._column_for_position(self.position)
        self.clear_selection()
        self._announce_character_at_cursor()
        return True

    def _announce_character_at_cursor(self) -> None:
        """Announce the character at the cursor position or blank if none."""
        text = self.get_value()
        if self.position >= len(text):
            speech_manager.output("blank", interrupt=True, log_message=False)
            return

        char = text[self.position]
        if char == "\n":
            speech_manager.output("blank", interrupt=True, log_message=False)
        elif char == " ":
            speech_manager.output("space", interrupt=True, log_message=False)
        elif char.isupper():
            speech_manager.output(
                f"Cap {char}", interrupt=True, log_message=False
            )
        else:
            speech_manager.output(char, interrupt=True, log_message=False)

    def go_to_start_of_text(self) -> bool:
        """Jump to the beginning of the text and announce the first line."""
        self.position = 0
        self._preferred_column = 0
        self.lines = self._split_lines(self.get_value())
        self._line_index = self._line_index_from_position()
        self.dispatch_event("on_line_change", self)
        self.speak_current_line()
        return True

    def go_to_end_of_text(self) -> bool:
        """Jump to the end of the text and announce the last line."""
        self.position = len(self.get_value())
        self._preferred_column = self._column_for_position(self.position)
        self.lines = self._split_lines(self.get_value())
        self._line_index = self._line_index_from_position()
        self.dispatch_event("on_line_change", self)
        self.speak_current_line()
        return True

    def go_to_first_line(self) -> bool:
        """Jump to the first line and announce it."""
        self._preferred_column = self._column_for_position(self.position)
        return self.select_line(0)

    def go_to_last_line(self) -> bool:
        """Jump to the last line and announce it."""
        self._preferred_column = self._column_for_position(self.position)
        return self.select_line(self.line_count - 1)

    # override
    def reset(self) -> None:
        """Restore the default content and return to the first line."""
        super().reset()
        self.lines = self._split_lines(self.default_value)
        self.line_index = 0
        self._preferred_column = 0

    @staticmethod
    def _split_lines(value: str) -> list[str]:
        """Split text into visible lines while preserving trailing blanks."""
        if value == "":
            return [""]

        lines = value.splitlines()
        if not lines:
            return [""]

        if value.endswith(("\n", "\r")):
            lines.append("")

        return lines

    def _line_index_from_position(self) -> int:
        """Return the current line index based on caret position."""
        text = self.get_value()
        position = min(max(self.position, 0), len(text))
        starts, _ = self._line_bounds()
        line_index = bisect_right(starts, position) - 1
        return min(line_index, self.line_count - 1)

    def _column_for_position(self, position: int) -> int:
        """Return the visual column at the given caret position."""
        starts, ends = self._line_bounds()
        line_index = min(self._line_index_from_position(), len(starts) - 1)
        line_start = starts[line_index]
        line_end = ends[line_index]
        line_length = max(0, line_end - line_start)
        return min(max(position - line_start, 0), line_length)

    def _line_bounds(self) -> tuple[list[int], list[int]]:
        """Return start and end offsets (excluding newline chars) for each line."""
        text = self.get_value()
        starts: list[int] = [0]
        ends: list[int] = []

        index = 0
        while index < len(text):
            char = text[index]
            if char not in ("\r", "\n"):
                index += 1
                continue

            # Exclude line-break characters from line content and treat CRLF
            # as a single line break.
            ends.append(index)
            if (
                char == "\r"
                and index + 1 < len(text)
                and text[index + 1] == "\n"
            ):
                index += 1

            starts.append(index + 1)
            index += 1

        ends.append(len(text))
        return starts, ends

    def _move_to_column(self, line_index: int, column: int) -> None:
        """Move caret to a target line/column pair."""
        starts, ends = self._line_bounds()
        target_start = starts[line_index]
        target_end = ends[line_index]
        target_length = max(0, target_end - target_start)
        self.position = target_start + min(column, target_length)
        self.clear_selection()


MultilineTextBox.register_event_type("on_line_change")
