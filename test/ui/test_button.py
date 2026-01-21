"""Comprehensive unit tests for the Button class."""

from typing import Any, Callable

import pytest
from pyglet.window import key
from pytest_mock import MockerFixture

from sonartk.ui.element.button import Button
from sonartk.ui.element.element import Element
from sonartk.ui.ui_component import UIComponent
from sonartk.ui.window import Window
from sonartk.util import KeyHandler
from test.mocks.mock_pyglet_window import MockPygletWindow


@pytest.fixture
def window(mocker: MockerFixture) -> Window:
    """Create a Window fixture."""
    window = Window()
    window.pyglet_window = mocker.MagicMock(spec=MockPygletWindow)
    window.push_window_handlers = mocker.MagicMock()  # type: ignore[method-assign]
    window.pop_window_handlers = mocker.MagicMock()  # type: ignore[method-assign]
    return window


@pytest.fixture
def parent(window: Window) -> UIComponent:
    """Create a parent UIComponent fixture."""
    parent = UIComponent()
    parent.parent = window
    return parent  # type: ignore[return-value]


@pytest.fixture
def button(parent: UIComponent) -> Button:
    """Create a Button fixture."""
    return Button(parent, "Submit")  # type: ignore[arg-type]


# Initialization Tests


def test_init_sets_parent(parent: UIComponent, button: Button) -> None:
    """Test that __init__ sets parent correctly."""
    assert button.parent == parent


def test_init_sets_label(parent: UIComponent) -> None:
    """Test that __init__ sets label correctly."""
    button = Button(parent, "Click Me")  # type: ignore[arg-type]
    assert button.label == "Click Me"


def test_init_sets_value_to_label(parent: UIComponent) -> None:
    """Test that __init__ sets value to the same as label."""
    button = Button(parent, "Submit Form")  # type: ignore[arg-type]
    assert button.value == "Submit Form"


def test_init_sets_role_to_button(parent: UIComponent) -> None:
    """Test that __init__ sets role to 'button'."""
    button = Button(parent, "Click")  # type: ignore[arg-type]
    assert button.role == "button"


def test_init_creates_key_handler(parent: UIComponent) -> None:
    """Test that __init__ creates a KeyHandler."""
    button = Button(parent, "Click")  # type: ignore[arg-type]
    assert isinstance(button.key_handler, KeyHandler)


def test_init_calls_bind_keys(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that __init__ calls bind_keys."""
    mock_bind_keys = mocker.patch.object(Button, "bind_keys")
    Button(parent, "Click")  # type: ignore[arg-type]
    mock_bind_keys.assert_called_once()


def test_init_with_empty_label(parent: UIComponent) -> None:
    """Test that __init__ works with empty label."""
    button = Button(parent, "")  # type: ignore[arg-type]
    assert button.label == ""
    assert button.value == ""


def test_init_with_special_characters_label(parent: UIComponent) -> None:
    """Test that __init__ works with special characters in label."""
    button = Button(parent, "Submit & Continue!")  # type: ignore[arg-type]
    assert button.label == "Submit & Continue!"
    assert button.value == "Submit & Continue!"


# bind_keys Tests


def test_bind_keys_registers_return_key(parent: UIComponent) -> None:
    """Test that bind_keys registers RETURN key."""
    button = Button(parent, "Submit")  # type: ignore[arg-type]
    return_key = None
    for k in button.key_handler.registered_key_presses.keys():
        if k.symbol == key.RETURN and k.modifiers == 0:
            return_key = k
            break

    assert return_key is not None, "RETURN key should be registered"
    callback, _ = button.key_handler.registered_key_presses[return_key]
    assert callback.callback == button.submit


def test_bind_keys_registers_space_key(parent: UIComponent) -> None:
    """Test that bind_keys registers SPACE key."""
    button = Button(parent, "Submit")  # type: ignore[arg-type]
    space_key = None
    for k in button.key_handler.registered_key_presses.keys():
        if k.symbol == key.SPACE and k.modifiers == 0:
            space_key = k
            break

    assert space_key is not None, "SPACE key should be registered"
    callback, _ = button.key_handler.registered_key_presses[space_key]
    assert callback.callback == button.submit


def test_bind_keys_registers_two_keys(parent: UIComponent) -> None:
    """Test that bind_keys registers exactly two keys."""
    button = Button(parent, "Submit")  # type: ignore[arg-type]
    assert len(button.key_handler.registered_key_presses) == 2


# submit Tests


def test_submit_dispatches_on_submit_event(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that submit dispatches on_submit event."""
    button = Button(parent, "Submit")  # type: ignore[arg-type]
    mock_dispatch = mocker.patch.object(button, "dispatch_event")

    button.submit()

    mock_dispatch.assert_called_once_with("on_submit", button)


def test_submit_returns_true(parent: UIComponent) -> None:
    """Test that submit returns True."""
    button = Button(parent, "Submit")  # type: ignore[arg-type]
    result = button.submit()
    assert result is True


def test_submit_event_listener_receives_event(parent: UIComponent) -> None:
    """Test that on_submit event listener receives the event."""
    button = Button(parent, "Submit")  # type: ignore[arg-type]
    received_button = None

    @button.event  # type: ignore[misc]
    def on_submit(btn: Button) -> None:
        nonlocal received_button
        received_button = btn

    button.submit()

    assert received_button == button


def test_submit_can_be_called_multiple_times(parent: UIComponent) -> None:
    """Test that submit can be called multiple times."""
    button = Button(parent, "Submit")  # type: ignore[arg-type]
    submit_count = 0

    @button.event  # type: ignore[misc]
    def on_submit(btn: Button) -> None:
        nonlocal submit_count
        submit_count += 1

    button.submit()
    button.submit()
    button.submit()

    assert submit_count == 3


# reset Tests


def test_reset_does_not_raise_exception(parent: UIComponent) -> None:
    """Test that reset does not raise an exception."""
    button = Button(parent, "Submit")  # type: ignore[arg-type]
    button.reset()  # Should not raise


def test_reset_does_not_change_value(parent: UIComponent) -> None:
    """Test that reset does not change the value."""
    button = Button(parent, "Submit")  # type: ignore[arg-type]
    original_value = button.value
    button.reset()
    assert button.value == original_value


def test_reset_does_not_change_label(parent: UIComponent) -> None:
    """Test that reset does not change the label."""
    button = Button(parent, "Submit")  # type: ignore[arg-type]
    original_label = button.label
    button.reset()
    assert button.label == original_label


# Inheritance Tests


def test_button_inherits_from_element(parent: UIComponent) -> None:
    """Test that Button inherits from Element."""
    button = Button(parent, "Submit")  # type: ignore[arg-type]
    assert isinstance(button, Element)


def test_button_generic_type_is_str(parent: UIComponent) -> None:
    """Test that Button uses str as generic type."""
    button = Button(parent, "Submit")  # type: ignore[arg-type]
    assert isinstance(button.value, str)


def test_button_has_element_methods(parent: UIComponent) -> None:
    """Test that Button has Element methods."""
    button = Button(parent, "Submit")  # type: ignore[arg-type]
    assert hasattr(button, "setup")
    assert hasattr(button, "update")
    assert hasattr(button, "exit")
    assert callable(button.setup)
    assert callable(button.update)
    assert callable(button.exit)


def test_button_has_get_window_method(parent: UIComponent) -> None:
    """Test that Button has get_window method."""
    button = Button(parent, "Submit")  # type: ignore[arg-type]
    assert hasattr(button, "get_window")
    assert callable(button.get_window)


# Event Registration Tests


def test_on_submit_event_is_registered() -> None:
    """Test that on_submit event is registered on Button class."""
    assert "on_submit" in Button.event_types


def test_button_has_inherited_events() -> None:
    """Test that Button has inherited events from Element."""
    assert "on_focus" in Button.event_types
    assert "on_lose_focus" in Button.event_types
    assert "on_update" in Button.event_types


# name Property Tests


def test_name_property_returns_label_and_role(parent: UIComponent) -> None:
    """Test that name property returns 'label button'."""
    button = Button(parent, "Submit")  # type: ignore[arg-type]
    assert button.name == "Submit button"


def test_name_property_with_different_labels(parent: UIComponent) -> None:
    """Test that name property works with different labels."""
    button1 = Button(parent, "OK")  # type: ignore[arg-type]
    assert button1.name == "OK button"

    button2 = Button(parent, "Cancel")  # type: ignore[arg-type]
    assert button2.name == "Cancel button"


def test_name_property_with_empty_label(parent: UIComponent) -> None:
    """Test that name property works with empty label."""
    button = Button(parent, "")  # type: ignore[arg-type]
    assert button.name == " button"


# Integration Tests


def test_button_lifecycle(
    mocker: MockerFixture, window: Window, parent: UIComponent
) -> None:
    """Test complete button lifecycle."""
    button = Button(parent, "Submit")  # type: ignore[arg-type]

    mock_push = mocker.patch.object(window, "push_window_handlers")
    mock_pop = mocker.patch.object(window, "pop_window_handlers")

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    # Setup
    result = button.setup(mock_change_state)
    assert result is True
    mock_push.assert_called_once_with(button.key_handler)

    # Update
    result = button.update(0.016)
    assert result is True

    # Submit
    result = button.submit()
    assert result is True

    # Exit
    result = button.exit()
    assert result is True
    mock_pop.assert_called_once()


def test_button_multiple_event_listeners(parent: UIComponent) -> None:
    """Test that multiple event listeners work correctly."""
    button = Button(parent, "Submit")  # type: ignore[arg-type]
    submit_count = 0
    focus_count = 0

    @button.event  # type: ignore[misc]
    def on_submit(btn: Button) -> None:
        nonlocal submit_count
        submit_count += 1

    @button.event  # type: ignore[misc]
    def on_focus(elem: Element[str]) -> None:
        nonlocal focus_count
        focus_count += 1

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    button.setup(mock_change_state)
    assert focus_count == 1

    button.submit()
    assert submit_count == 1

    button.submit()
    assert submit_count == 2


def test_button_key_press_simulation(parent: UIComponent) -> None:
    """Test simulating key press on button."""
    button = Button(parent, "Submit")  # type: ignore[arg-type]
    submit_count = 0

    @button.event  # type: ignore[misc]
    def on_submit(btn: Button) -> None:
        nonlocal submit_count
        submit_count += 1

    # Simulate RETURN key press
    for k, (callback, _) in button.key_handler.registered_key_presses.items():
        if k.symbol == key.RETURN and k.modifiers == 0:
            callback.call()
            break

    assert submit_count == 1


def test_button_value_matches_label_throughout_lifecycle(
    parent: UIComponent,
) -> None:
    """Test that button value always matches label."""
    button = Button(parent, "Submit Form")  # type: ignore[arg-type]

    assert button.value == "Submit Form"
    assert button.label == "Submit Form"

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    button.setup(mock_change_state)
    assert button.value == "Submit Form"

    button.update(0.016)
    assert button.value == "Submit Form"

    button.reset()
    assert button.value == "Submit Form"


def test_button_with_different_parent_types(window: Window) -> None:
    """Test button with different parent types."""
    # Direct parent as UIComponent
    parent1 = UIComponent()
    parent1.parent = window
    button1 = Button(parent1, "Button1")  # type: ignore[arg-type]
    assert button1.parent == parent1

    # Nested parent
    parent2 = UIComponent()
    parent2.parent = parent1
    button2 = Button(parent2, "Button2")  # type: ignore[arg-type]
    assert button2.parent == parent2
    assert button2.get_window() == window
