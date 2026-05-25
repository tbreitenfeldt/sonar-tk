from typing import Any, Callable

import pytest
from pytest_mock import MockerFixture

from sonartk.ui.element.element import Element
from sonartk.ui.element.text_label import TextLabel
from sonartk.ui.screen.screen import Screen
from sonartk.ui.ui_component import UIComponent
from sonartk.ui.window import Window
from sonartk.util import speech_manager
from test.mocks.mock_pyglet_window import MockPygletWindow


class _FakeScreen(Screen):
    """Minimal Screen subclass for testing TextLabel."""

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
def text_label(parent: _FakeScreen) -> TextLabel:
    """Create a TextLabel fixture."""
    return TextLabel(parent, "Section Header")


# Initialization Tests


def test_init_sets_parent(parent: _FakeScreen, text_label: TextLabel) -> None:
    """Test that __init__ sets parent correctly."""
    assert text_label.parent == parent


def test_init_sets_label(parent: _FakeScreen) -> None:
    """Test that __init__ sets label correctly."""
    label = TextLabel(parent, "My Label")
    assert label.label == "My Label"


def test_init_sets_value_to_empty_string(parent: _FakeScreen) -> None:
    """Test that __init__ sets value to empty string."""
    label = TextLabel(parent, "Label")
    assert label.value == ""


def test_init_sets_role_to_empty_string(parent: _FakeScreen) -> None:
    """Test that __init__ sets role to empty string."""
    label = TextLabel(parent, "Label")
    assert label.role == ""


def test_init_sets_use_key_handler_false(parent: _FakeScreen) -> None:
    """Test that __init__ sets use_key_handler to False."""
    label = TextLabel(parent, "Label")
    assert label.use_key_handler is False


def test_init_does_not_create_key_handler(parent: _FakeScreen) -> None:
    """Test that __init__ does not create a KeyHandler."""
    label = TextLabel(parent, "Label")
    assert not hasattr(label, "key_handler")


def test_init_empty_label(parent: _FakeScreen) -> None:
    """Test that __init__ accepts an empty string as label."""
    label = TextLabel(parent, "")
    assert label.label == ""


def test_init_long_label(parent: _FakeScreen) -> None:
    """Test that __init__ accepts a long label string."""
    long_label = "A" * 500
    label = TextLabel(parent, long_label)
    assert label.label == long_label


# bind_keys Tests


def test_bind_keys_is_no_op(parent: _FakeScreen) -> None:
    """Test that bind_keys does nothing (no key bindings for TextLabel)."""
    label = TextLabel(parent, "Label")
    # Should not raise and should not have a key_handler
    label.bind_keys()
    assert not hasattr(label, "key_handler")


def test_bind_keys_returns_none(parent: _FakeScreen) -> None:
    """Test that bind_keys returns None."""
    label = TextLabel(parent, "Label")
    result = label.bind_keys()
    assert result is None


# reset Tests


def test_reset_is_no_op(parent: _FakeScreen) -> None:
    """Test that reset does nothing."""
    label = TextLabel(parent, "Label")
    label.value = "something"  # type: ignore[assignment]
    label.reset()
    # Value should be unchanged since reset is a no-op
    assert label.value == "something"


def test_reset_returns_none(parent: _FakeScreen) -> None:
    """Test that reset returns None."""
    label = TextLabel(parent, "Label")
    result = label.reset()
    assert result is None


# __repr__ Tests


def test_repr_returns_label(parent: _FakeScreen) -> None:
    """Test that __repr__ returns the label string."""
    label = TextLabel(parent, "Section Header")
    assert repr(label) == "Section Header"


def test_repr_returns_empty_string_when_label_empty(
    parent: _FakeScreen,
) -> None:
    """Test that __repr__ returns empty string when label is empty."""
    label = TextLabel(parent, "")
    assert repr(label) == ""


def test_repr_matches_label_after_change(parent: _FakeScreen) -> None:
    """Test that __repr__ reflects the current label value."""
    label = TextLabel(parent, "Original")
    label.label = "Changed"
    assert repr(label) == "Changed"


# name property Tests


def test_name_returns_label_with_empty_role(parent: _FakeScreen) -> None:
    """Test that name property returns label followed by empty role."""
    label = TextLabel(parent, "Info")
    # role is "", so name is "Info "
    assert label.name == "Info "


def test_name_with_empty_label(parent: _FakeScreen) -> None:
    """Test that name property returns empty string with empty role when label is empty."""
    label = TextLabel(parent, "")
    assert label.name == " "


# value property Tests


def test_value_is_empty_string_by_default(parent: _FakeScreen) -> None:
    """Test that value is an empty string after initialization."""
    label = TextLabel(parent, "Label")
    assert label.value == ""


def test_value_setter_updates_value(parent: _FakeScreen) -> None:
    """Test that the value setter updates the value correctly."""
    label = TextLabel(parent, "Label")
    label.value = "new value"  # type: ignore[assignment]
    assert label.value == "new value"


# setup Tests


def test_setup_outputs_speech_for_label(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that setup outputs speech for the label."""
    mock_output = mocker.patch.object(speech_manager, "output")
    label = TextLabel(parent, "Section Header")

    label.setup(lambda key, *a, **kw: None)

    mock_output.assert_called_once_with(
        "Section Header ", interrupt=False, log_message=False
    )


def test_setup_does_not_output_speech_for_empty_label(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that setup does not output speech when label is empty."""
    mock_output = mocker.patch.object(speech_manager, "output")
    label = TextLabel(parent, "")

    label.setup(lambda key, *a, **kw: None)

    mock_output.assert_not_called()


def test_setup_does_not_push_window_handlers(
    mocker: MockerFixture, window: Window, parent: _FakeScreen
) -> None:
    """Test that setup does not push window handlers (use_key_handler=False)."""
    mocker.patch.object(speech_manager, "output")
    mock_push = mocker.patch.object(window, "push_window_handlers")
    label = TextLabel(parent, "Label")

    label.setup(lambda key, *a, **kw: None)

    mock_push.assert_not_called()


def test_setup_dispatches_on_focus_event(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that setup dispatches the on_focus event."""
    mocker.patch.object(speech_manager, "output")
    label = TextLabel(parent, "Label")
    mock_dispatch = mocker.patch.object(label, "dispatch_event")

    label.setup(lambda key, *a, **kw: None)

    mock_dispatch.assert_called_once_with("on_focus", label)


def test_setup_returns_true(parent: _FakeScreen) -> None:
    """Test that setup returns True."""
    label = TextLabel(parent, "Label")
    result = label.setup(lambda key, *a, **kw: None)
    assert result is True


def test_setup_with_interrupt_speech(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that setup passes interrupt_speech flag to speech output."""
    mock_output = mocker.patch.object(speech_manager, "output")
    label = TextLabel(parent, "Hello")

    label.setup(lambda key, *a, **kw: None, interrupt_speech=True)

    mock_output.assert_called_once_with(
        "Hello ", interrupt=True, log_message=False
    )


def test_setup_on_focus_listener_receives_element(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that on_focus event listener receives the TextLabel instance."""
    mocker.patch.object(speech_manager, "output")
    label = TextLabel(parent, "Label")
    received: list[TextLabel] = []

    @label.event  # type: ignore[misc]
    def on_focus(elem: Element[str]) -> None:
        received.append(elem)  # type: ignore[arg-type]

    label.setup(lambda key, *a, **kw: None)

    assert received == [label]


# exit Tests


def test_exit_dispatches_on_lose_focus_event(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that exit dispatches the on_lose_focus event."""
    label = TextLabel(parent, "Label")
    mock_dispatch = mocker.patch.object(label, "dispatch_event")

    label.exit()

    mock_dispatch.assert_called_once_with("on_lose_focus", label)


def test_exit_does_not_pop_window_handlers(
    mocker: MockerFixture, window: Window, parent: _FakeScreen
) -> None:
    """Test that exit does not pop window handlers (use_key_handler=False)."""
    mock_pop = mocker.patch.object(window, "pop_window_handlers")
    label = TextLabel(parent, "Label")

    label.exit()

    mock_pop.assert_not_called()


def test_exit_returns_true(parent: _FakeScreen) -> None:
    """Test that exit returns True."""
    label = TextLabel(parent, "Label")
    result = label.exit()
    assert result is True


def test_exit_on_lose_focus_listener_receives_element(
    parent: _FakeScreen,
) -> None:
    """Test that on_lose_focus event listener receives the TextLabel instance."""
    label = TextLabel(parent, "Label")
    received: list[TextLabel] = []

    @label.event  # type: ignore[misc]
    def on_lose_focus(elem: Element[str]) -> None:
        received.append(elem)  # type: ignore[arg-type]

    label.exit()

    assert received == [label]


# update Tests


def test_update_dispatches_on_update_event(
    mocker: MockerFixture, parent: _FakeScreen
) -> None:
    """Test that update dispatches the on_update event."""
    label = TextLabel(parent, "Label")
    mock_dispatch = mocker.patch.object(label, "dispatch_event")

    label.update(0.016)

    mock_dispatch.assert_called_once_with("on_update", label, 0.016)


def test_update_returns_true(parent: _FakeScreen) -> None:
    """Test that update returns True."""
    label = TextLabel(parent, "Label")
    result = label.update(0.016)
    assert result is True


def test_update_on_update_listener_receives_element_and_delta(
    parent: _FakeScreen,
) -> None:
    """Test that on_update listener receives both the element and delta_time."""
    label = TextLabel(parent, "Label")
    received_elem: list[TextLabel] = []
    received_delta: list[float] = []

    @label.event  # type: ignore[misc]
    def on_update(elem: Element[str], delta_time: float) -> None:
        received_elem.append(elem)  # type: ignore[arg-type]
        received_delta.append(delta_time)

    label.update(0.5)

    assert received_elem == [label]
    assert received_delta == [0.5]


# is-a / isinstance Tests


def test_text_label_is_element(parent: _FakeScreen) -> None:
    """Test that TextLabel is an instance of Element."""
    label = TextLabel(parent, "Label")
    assert isinstance(label, Element)


def test_text_label_is_ui_component(parent: _FakeScreen) -> None:
    """Test that TextLabel is an instance of UIComponent."""
    label = TextLabel(parent, "Label")
    assert isinstance(label, UIComponent)
