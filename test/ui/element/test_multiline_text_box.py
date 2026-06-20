from typing import Any, Callable

import pytest
from pyglet.window import key
from pytest_mock import MockerFixture

from sonartk.ui.element.multiline_text_box import MultilineTextBox
from sonartk.ui.screen.screen import Screen
from sonartk.ui.window import Window
from sonartk.util import KeyHandler, speech_manager
from test.mocks.mock_pyglet_window import MockPygletWindow


class _FakeScreen(Screen):
    """Test screen class for testing MultilineTextBox."""

    def __init__(self, parent: Window) -> None:
        super().__init__(parent)

    def bind_keys(self) -> None:
        pass

    def setup(
        self,
        change_state: Callable[[str, Any], None],
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        return True

    def update(self, delta_time: float) -> bool:
        return True

    def exit(self) -> bool:
        return True


@pytest.fixture
def window(mocker: MockerFixture) -> Window:
    """Create a Window fixture."""
    window = Window()
    window.pyglet_window = mocker.MagicMock(spec=MockPygletWindow)
    window.push_window_handlers = mocker.MagicMock()  # type: ignore[method-assign]
    window.pop_window_handlers = mocker.MagicMock()  # type: ignore[method-assign]
    return window


@pytest.fixture
def parent(window: Window) -> _FakeScreen:
    """Create a parent TestScreen fixture."""
    return _FakeScreen(window)


@pytest.fixture
def multiline_text_box(parent: _FakeScreen) -> MultilineTextBox:
    """Create a multiline text box fixture."""
    return MultilineTextBox(
        parent,
        "Details",
        "First line\nSecond line\nThird line",
    )  # type: ignore[arg-type]


def test_init_sets_parent(
    parent: _FakeScreen, multiline_text_box: MultilineTextBox
) -> None:
    """Test that __init__ sets parent correctly."""
    assert multiline_text_box.parent == parent


def test_init_sets_label(parent: _FakeScreen) -> None:
    """Test that __init__ sets label correctly."""
    viewer = MultilineTextBox(parent, "My Label")  # type: ignore[arg-type]
    assert viewer.label == "My Label"


def test_init_sets_role_to_multiline_text_box(parent: _FakeScreen) -> None:
    """Test that __init__ sets the role for a multiline viewer."""
    viewer = MultilineTextBox(parent, "Label")  # type: ignore[arg-type]
    assert viewer.role == "multiline text box"


def test_init_sets_default_value(parent: _FakeScreen) -> None:
    """Test that __init__ stores the default value."""
    viewer = MultilineTextBox(parent, "Label", "Line 1\nLine 2")  # type: ignore[arg-type]
    assert viewer.default_value == "Line 1\nLine 2"


def test_init_sets_value_from_default(parent: _FakeScreen) -> None:
    """Test that __init__ sets value from default_value."""
    viewer = MultilineTextBox(parent, "Label", "Line 1\nLine 2")  # type: ignore[arg-type]
    assert viewer.value == "Line 1\nLine 2"


def test_init_splits_lines(parent: _FakeScreen) -> None:
    """Test that __init__ splits the content into visible lines."""
    viewer = MultilineTextBox(parent, "Label", "Line 1\nLine 2")  # type: ignore[arg-type]
    assert viewer.lines == ["Line 1", "Line 2"]


def test_init_sets_line_index_to_zero(parent: _FakeScreen) -> None:
    """Test that __init__ starts on the first line."""
    viewer = MultilineTextBox(parent, "Label", "Line 1\nLine 2")  # type: ignore[arg-type]
    assert viewer.line_index == 0


def test_init_sets_line_count(parent: _FakeScreen) -> None:
    """Test that line_count matches the number of lines."""
    viewer = MultilineTextBox(parent, "Label", "Line 1\nLine 2\nLine 3")  # type: ignore[arg-type]
    assert viewer.line_count == 3


def test_init_creates_key_handler(parent: _FakeScreen) -> None:
    """Test that __init__ creates a KeyHandler."""
    viewer = MultilineTextBox(parent, "Label")  # type: ignore[arg-type]
    assert isinstance(viewer.key_handler, KeyHandler)


def test_bind_keys_registers_navigation_keys(parent: _FakeScreen) -> None:
    """Test that bind_keys registers line navigation shortcuts."""
    viewer = MultilineTextBox(parent, "Label")  # type: ignore[arg-type]
    from sonartk.util.key_handler import Key

    assert Key(key.UP) in viewer.key_handler.registered_key_presses
    assert Key(key.DOWN) in viewer.key_handler.registered_key_presses
    assert Key(key.HOME) in viewer.key_handler.registered_key_presses
    assert Key(key.END) in viewer.key_handler.registered_key_presses
    assert (
        Key(key.HOME, [key.MOD_CTRL])
        in viewer.key_handler.registered_key_presses
    )
    assert (
        Key(key.END, [key.MOD_CTRL])
        in viewer.key_handler.registered_key_presses
    )


def test_bind_keys_keeps_character_navigation_from_text_box(
    parent: _FakeScreen,
) -> None:
    """Test that inherited left/right character navigation remains available."""
    viewer = MultilineTextBox(parent, "Label")  # type: ignore[arg-type]
    from sonartk.util.key_handler import Key

    assert Key(key.MOTION_RIGHT) in viewer.key_handler.registered_text_motions
    assert Key(key.MOTION_LEFT) in viewer.key_handler.registered_text_motions


def test_home_moves_to_beginning_of_current_line(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that Home keeps navigation within the current line and announces the character."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "abc\ndefg")  # type: ignore[arg-type]
    viewer.position = 6

    result = viewer.key_handler.on_key_press(key.HOME, 0)

    assert result is True
    assert viewer.position == 4
    assert viewer.line_index == 1
    mock_output.assert_called_with("d", interrupt=True, log_message=False)


def test_end_moves_to_end_of_current_line(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that End keeps navigation within the current line and announces the character."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "abc\ndefg")  # type: ignore[arg-type]
    viewer.position = 5

    result = viewer.key_handler.on_key_press(key.END, 0)

    assert result is True
    assert viewer.position == 8
    assert viewer.line_index == 1
    mock_output.assert_called_with("blank", interrupt=True, log_message=False)


def test_control_home_moves_to_beginning_of_text(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that Control+Home jumps to the first line and announces it."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "Line 1\nLine 2\nLine 3")  # type: ignore[arg-type]
    viewer.line_index = 2

    result = viewer.key_handler.on_key_press(key.HOME, key.MOD_CTRL)

    assert result is True
    assert viewer.line_index == 0
    assert viewer.position == 0
    mock_output.assert_called_with("Line 1", interrupt=True, log_message=False)


def test_control_end_moves_to_end_of_text(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that Control+End jumps to the last line and announces it."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "Line 1\nLine 2\nLine 3")  # type: ignore[arg-type]

    result = viewer.key_handler.on_key_press(key.END, key.MOD_CTRL)

    assert result is True
    assert viewer.line_index == 2
    assert viewer.position == len(viewer.value)
    mock_output.assert_called_with("Line 3", interrupt=True, log_message=False)


def test_control_home_on_empty_text_announces_blank(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that Control+Home on empty text announces Blank."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "")  # type: ignore[arg-type]

    result = viewer.key_handler.on_key_press(key.HOME, key.MOD_CTRL)

    assert result is True
    mock_output.assert_called_with("Blank", interrupt=True, log_message=False)


def test_control_end_on_empty_text_announces_blank(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that Control+End on empty text announces Blank."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "")  # type: ignore[arg-type]

    result = viewer.key_handler.on_key_press(key.END, key.MOD_CTRL)

    assert result is True
    mock_output.assert_called_with("Blank", interrupt=True, log_message=False)


def test_bind_keys_does_not_register_text_input(parent: _FakeScreen) -> None:
    """Test that the viewer does not accept text input."""
    viewer = MultilineTextBox(parent, "Label")  # type: ignore[arg-type]
    assert viewer.key_handler.registered_text_input is None


def test_copy_selection_works_like_text_box(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that selection and copy behaviors are inherited from TextBox."""
    mock_copy = mocker.patch("pyperclip.copy")
    mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "abc")  # type: ignore[arg-type]

    viewer.move_letter_selection_right()
    viewer.copy_to_clipboard()

    mock_copy.assert_called_once_with("a")


def test_value_setter_updates_lines_and_clamps_index(
    parent: _FakeScreen,
) -> None:
    """Test that value updates the line buffer and keeps the cursor valid."""
    viewer = MultilineTextBox(parent, "Label", "Line 1\nLine 2")  # type: ignore[arg-type]
    viewer.line_index = 1

    viewer.value = "One line"

    assert viewer.lines == ["One line"]
    assert viewer.line_index == 0


def test_current_line_returns_active_line(parent: _FakeScreen) -> None:
    """Test that current_line reflects the selected line."""
    viewer = MultilineTextBox(parent, "Label", "Line 1\nLine 2")  # type: ignore[arg-type]
    viewer.line_index = 1
    assert viewer.current_line == "Line 2"


def test_select_line_dispatches_change_event(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that select_line emits the change event when the line changes."""
    viewer = MultilineTextBox(parent, "Label", "Line 1\nLine 2")  # type: ignore[arg-type]
    mock_dispatch = mocker.patch.object(viewer, "dispatch_event")

    viewer.select_line(1, announce=False)

    mock_dispatch.assert_called_once_with("on_line_change", viewer)


def test_setup_outputs_label_and_current_line(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that setup speaks the label and the current line."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Details", "Line 1\nLine 2")  # type: ignore[arg-type]

    viewer.setup(lambda key, *a, **kw: None)

    assert mock_output.call_count == 2
    mock_output.assert_any_call(
        "Details multiline text box", interrupt=False, log_message=False
    )
    mock_output.assert_any_call("Line 1", interrupt=False, log_message=False)


def test_setup_announces_role_when_label_is_empty(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that setup speaks the role when no label is provided."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "", "Line 1\nLine 2")  # type: ignore[arg-type]

    viewer.setup(lambda key, *a, **kw: None)

    assert mock_output.call_count == 2
    mock_output.assert_any_call(
        "multiline text box", interrupt=False, log_message=False
    )
    mock_output.assert_any_call("Line 1", interrupt=False, log_message=False)


def test_speak_current_line_outputs_blank_for_empty_line(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that blank lines are announced as Blank."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "")  # type: ignore[arg-type]

    result = viewer.speak_current_line()

    assert result is True
    mock_output.assert_called_once_with(
        "Blank", interrupt=True, log_message=False
    )


def test_speak_current_line_preserves_leading_spaces(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that non-blank lines are spoken without trimming indentation."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "  Indented")  # type: ignore[arg-type]

    result = viewer.speak_current_line()

    assert result is True
    mock_output.assert_called_once_with(
        "  Indented", interrupt=True, log_message=False
    )


def test_next_line_advances_and_announces(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that next_line advances to the next line."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "Line 1\nLine 2")  # type: ignore[arg-type]

    result = viewer.next_line()

    assert result is True
    assert viewer.line_index == 1
    mock_output.assert_called_with("Line 2", interrupt=True, log_message=False)


def test_next_line_at_end_announces_boundary(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that next_line speaks the last line at the boundary."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "Line 1")  # type: ignore[arg-type]

    result = viewer.next_line()

    assert result is True
    assert viewer.line_index == 0
    mock_output.assert_called_with("Line 1", interrupt=True, log_message=False)


def test_previous_line_moves_back_and_announces(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that previous_line moves back to the prior line."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "Line 1\nLine 2")  # type: ignore[arg-type]
    viewer.line_index = 1

    result = viewer.previous_line()

    assert result is True
    assert viewer.line_index == 0
    mock_output.assert_called_with("Line 1", interrupt=True, log_message=False)


def test_previous_line_at_start_announces_boundary(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that previous_line speaks the first line at the boundary."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "Line 1")  # type: ignore[arg-type]

    result = viewer.previous_line()

    assert result is True
    mock_output.assert_called_with("Line 1", interrupt=True, log_message=False)


def test_go_to_first_line_moves_to_top(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that go_to_first_line moves to the first line."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "Line 1\nLine 2")  # type: ignore[arg-type]
    viewer.line_index = 1

    result = viewer.go_to_first_line()

    assert result is True
    assert viewer.line_index == 0
    mock_output.assert_called_with("Line 1", interrupt=True, log_message=False)


def test_go_to_last_line_moves_to_bottom(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that go_to_last_line moves to the last line."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "Line 1\nLine 2\nLine 3")  # type: ignore[arg-type]

    result = viewer.go_to_last_line()

    assert result is True
    assert viewer.line_index == 2
    mock_output.assert_called_with("Line 3", interrupt=True, log_message=False)


def test_reset_restores_default_value_and_first_line(
    parent: _FakeScreen,
) -> None:
    """Test that reset restores the default content and cursor position."""
    viewer = MultilineTextBox(parent, "Label", "Line 1\nLine 2")  # type: ignore[arg-type]
    viewer.value = "Changed\nContent"
    viewer.line_index = 1

    viewer.reset()

    assert viewer.value == "Line 1\nLine 2"
    assert viewer.lines == ["Line 1", "Line 2"]
    assert viewer.line_index == 0


def test_value_setter_preserves_trailing_blank_line(
    parent: _FakeScreen,
) -> None:
    """Test that a trailing newline keeps an explicit blank line."""
    viewer = MultilineTextBox(parent, "Label")  # type: ignore[arg-type]

    viewer.value = "Line 1\n"

    assert viewer.lines == ["Line 1", ""]


def test_select_next_line_extends_selection_downward(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that Shift+Down reads the selected line text."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "abc\ndefg")  # type: ignore[arg-type]
    viewer.position = 1

    result = viewer.select_next_line()

    assert result is True
    assert viewer.is_selected()
    assert viewer.left_selection_index == 1
    assert viewer.right_selection_index == 3
    mock_output.assert_called_with(
        "bc Selected", interrupt=True, log_message=False
    )


def test_select_next_line_can_be_extended_by_word_selection(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that line selection remains adjustable with word selection commands."""
    mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "abc def\nghi jkl")  # type: ignore[arg-type]
    viewer.position = 1

    viewer.select_next_line()
    previous_right = viewer.right_selection_index
    result = viewer.move_word_selection_right()

    assert result is True
    assert viewer.is_selected()
    assert viewer.right_selection_index > previous_right


def test_select_next_line_at_end_announces_boundary(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that Shift+Down at the last line speaks the last line."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "abc\ndefg")  # type: ignore[arg-type]
    viewer.line_index = 1
    viewer.position = len(viewer.value)

    result = viewer.select_next_line()

    assert result is True
    mock_output.assert_called_with("defg", interrupt=True, log_message=False)


def test_select_previous_line_extends_selection_upward(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that Shift+Up reads the selected line text."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "abc\ndefg\nhijk")  # type: ignore[arg-type]
    viewer.position = 8

    result = viewer.select_previous_line()

    assert result is True
    assert viewer.is_selected()
    assert viewer.left_selection_index == 4
    assert viewer.right_selection_index == 8
    mock_output.assert_called_with(
        "defg Selected", interrupt=True, log_message=False
    )


def test_select_previous_line_continues_existing_selection(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that multiple Shift+Up calls extend selection further."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "abc\ndefg\nhijk")  # type: ignore[arg-type]
    viewer.position = 9

    viewer.select_previous_line()
    viewer.position = 4
    result = viewer.select_previous_line()

    assert result is True
    assert viewer.is_selected()
    assert viewer.left_selection_index == 0
    assert viewer.right_selection_index == 9
    mock_output.assert_called_with(
        "abc Selected", interrupt=True, log_message=False
    )


def test_select_previous_line_at_start_announces_boundary(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that Shift+Up at the first line speaks the first line."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "abc\ndefg")  # type: ignore[arg-type]
    viewer.position = 0

    result = viewer.select_previous_line()

    assert result is True
    mock_output.assert_called_with("abc", interrupt=True, log_message=False)


def test_move_word_selection_right_treats_newline_as_word(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that word selection to the right selects newline as its own token."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "abc\ndef")  # type: ignore[arg-type]
    viewer.position = 0

    first = viewer.move_word_selection_right()
    second = viewer.move_word_selection_right()

    assert first is True
    assert second is True
    assert viewer.position == 4
    assert viewer.left_selection_index == 0
    assert viewer.right_selection_index == 4
    assert mock_output.call_args_list[0].args[0] == "abc Selected"
    assert mock_output.call_args_list[1].args[0] == "Blank Selected"


def test_move_word_selection_left_treats_newline_as_word(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that word selection to the left selects newline as its own token."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "abc\ndef")  # type: ignore[arg-type]
    viewer.position = len(viewer.value)

    first = viewer.move_word_selection_left()
    second = viewer.move_word_selection_left()

    assert first is True
    assert second is True
    assert viewer.position == 3
    assert viewer.left_selection_index == 3
    assert viewer.right_selection_index == 7
    assert mock_output.call_args_list[0].args[0] == "def Selected"
    assert mock_output.call_args_list[1].args[0] == "Blank Selected"


def test_line_index_from_position_handles_carriage_return_only(
    parent: _FakeScreen,
) -> None:
    """Test line indexing with CR-only line separators."""
    viewer = MultilineTextBox(parent, "Label", "a\rb\rc")  # type: ignore[arg-type]

    viewer.position = 2
    assert viewer._line_index_from_position() == 1

    viewer.position = 4
    assert viewer._line_index_from_position() == 2


def test_next_line_navigates_with_carriage_return_only(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test next_line navigation with CR-only line separators."""
    mock_output = mocker.patch.object(speech_manager, "output")
    viewer = MultilineTextBox(parent, "Label", "First\rSecond\rThird")  # type: ignore[arg-type]

    result = viewer.next_line()

    assert result is True
    assert viewer.line_index == 1
    mock_output.assert_called_with("Second", interrupt=True, log_message=False)
