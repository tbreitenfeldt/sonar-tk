"""Comprehensive unit tests for the Checkbox class."""

from typing import Any

import pytest
from pyglet.window import key
from pytest_mock import MockerFixture

from sonartk.ui.element.checkbox import Checkbox
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
def checkbox(parent: UIComponent) -> Checkbox:
    """Create a Checkbox fixture."""
    return Checkbox(parent, "Accept Terms")  # type: ignore[arg-type]


# Initialization Tests


def test_init_sets_parent(parent: UIComponent, checkbox: Checkbox) -> None:
    """Test that __init__ sets parent correctly."""
    assert checkbox.parent == parent


def test_init_sets_label(parent: UIComponent) -> None:
    """Test that __init__ sets label correctly."""
    checkbox = Checkbox(parent, "Remember Me")  # type: ignore[arg-type]
    assert checkbox.label == "Remember Me"


def test_init_sets_default_value_false(parent: UIComponent) -> None:
    """Test that __init__ sets value to False by default."""
    checkbox = Checkbox(parent, "Option")  # type: ignore[arg-type]
    assert checkbox.value is False
    assert checkbox.default_value is False


def test_init_sets_value_to_true(parent: UIComponent) -> None:
    """Test that __init__ can set value to True."""
    checkbox = Checkbox(parent, "Option", True)  # type: ignore[arg-type]
    assert checkbox.value is True
    assert checkbox.default_value is True


def test_init_sets_role_to_checkbox(parent: UIComponent) -> None:
    """Test that __init__ sets role to 'checkbox'."""
    checkbox = Checkbox(parent, "Option")  # type: ignore[arg-type]
    assert checkbox.role == "checkbox"


def test_init_creates_key_handler(parent: UIComponent) -> None:
    """Test that __init__ creates a KeyHandler."""
    checkbox = Checkbox(parent, "Option")  # type: ignore[arg-type]
    assert isinstance(checkbox.key_handler, KeyHandler)


def test_init_calls_bind_keys(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that __init__ calls bind_keys."""
    mock_bind_keys = mocker.patch.object(Checkbox, "bind_keys")
    Checkbox(parent, "Option")  # type: ignore[arg-type]
    mock_bind_keys.assert_called_once()


def test_init_with_empty_label(parent: UIComponent) -> None:
    """Test that __init__ works with empty label."""
    checkbox = Checkbox(parent, "")  # type: ignore[arg-type]
    assert checkbox.label == ""
    assert checkbox.value is False


def test_init_with_false_value(parent: UIComponent) -> None:
    """Test that __init__ works with explicit False value."""
    checkbox = Checkbox(parent, "Option", False)  # type: ignore[arg-type]
    assert checkbox.value is False
    assert checkbox.default_value is False


def test_init_stores_default_value(parent: UIComponent) -> None:
    """Test that __init__ stores default_value."""
    checkbox = Checkbox(parent, "Option", True)  # type: ignore[arg-type]
    assert checkbox.default_value is True


# bind_keys Tests


def test_bind_keys_registers_return_key(parent: UIComponent) -> None:
    """Test that bind_keys registers RETURN key."""
    checkbox = Checkbox(parent, "Option")  # type: ignore[arg-type]
    return_key = None
    for k in checkbox.key_handler.registered_key_presses.keys():
        if k.symbol == key.RETURN and k.modifiers == 0:
            return_key = k
            break

    assert return_key is not None, "RETURN key should be registered"
    callback, _ = checkbox.key_handler.registered_key_presses[return_key]
    assert callback.callback == checkbox.toggle_state


def test_bind_keys_registers_space_key(parent: UIComponent) -> None:
    """Test that bind_keys registers SPACE key."""
    checkbox = Checkbox(parent, "Option")  # type: ignore[arg-type]
    space_key = None
    for k in checkbox.key_handler.registered_key_presses.keys():
        if k.symbol == key.SPACE and k.modifiers == 0:
            space_key = k
            break

    assert space_key is not None, "SPACE key should be registered"
    callback, _ = checkbox.key_handler.registered_key_presses[space_key]
    assert callback.callback == checkbox.toggle_state


def test_bind_keys_registers_two_keys(parent: UIComponent) -> None:
    """Test that bind_keys registers exactly two keys."""
    checkbox = Checkbox(parent, "Option")  # type: ignore[arg-type]
    assert len(checkbox.key_handler.registered_key_presses) == 2


# toggle_state Tests


def test_toggle_state_changes_value_from_false_to_true(
    parent: UIComponent,
) -> None:
    """Test that toggle_state changes value from False to True."""
    checkbox = Checkbox(parent, "Option", False)  # type: ignore[arg-type]
    checkbox.toggle_state()
    assert checkbox.value is True


def test_toggle_state_changes_value_from_true_to_false(
    parent: UIComponent,
) -> None:
    """Test that toggle_state changes value from True to False."""
    checkbox = Checkbox(parent, "Option", True)  # type: ignore[arg-type]
    checkbox.toggle_state()
    assert checkbox.value is False


def test_toggle_state_dispatches_on_change_event(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that toggle_state dispatches on_change event."""
    checkbox = Checkbox(parent, "Option")  # type: ignore[arg-type]
    mock_dispatch = mocker.patch.object(checkbox, "dispatch_event")

    checkbox.toggle_state()

    assert any(
        call[0][0] == "on_change" for call in mock_dispatch.call_args_list
    )


def test_toggle_state_dispatches_on_checked_when_checked(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that toggle_state dispatches on_checked when value becomes True."""
    checkbox = Checkbox(parent, "Option", False)  # type: ignore[arg-type]
    mock_dispatch = mocker.patch.object(checkbox, "dispatch_event")

    checkbox.toggle_state()

    assert any(
        call[0][0] == "on_checked" for call in mock_dispatch.call_args_list
    )


def test_toggle_state_dispatches_on_unchecked_when_unchecked(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that toggle_state dispatches on_unchecked when value becomes False."""
    checkbox = Checkbox(parent, "Option", True)  # type: ignore[arg-type]
    mock_dispatch = mocker.patch.object(checkbox, "dispatch_event")

    checkbox.toggle_state()

    assert any(
        call[0][0] == "on_unchecked" for call in mock_dispatch.call_args_list
    )


def test_toggle_state_returns_true(parent: UIComponent) -> None:
    """Test that toggle_state returns True."""
    checkbox = Checkbox(parent, "Option")  # type: ignore[arg-type]
    result = checkbox.toggle_state()
    assert result is True


def test_toggle_state_can_be_toggled_multiple_times(
    parent: UIComponent,
) -> None:
    """Test that toggle_state can be called multiple times."""
    checkbox = Checkbox(parent, "Option", False)  # type: ignore[arg-type]

    checkbox.toggle_state()
    assert checkbox.value is True

    checkbox.toggle_state()
    assert checkbox.value is False

    checkbox.toggle_state()
    assert checkbox.value is True


def test_toggle_state_event_listener_receives_checkbox(
    parent: UIComponent,
) -> None:
    """Test that on_change event listener receives the checkbox."""
    checkbox = Checkbox(parent, "Option")  # type: ignore[arg-type]
    received_checkbox = None

    @checkbox.event  # type: ignore[misc]
    def on_change(cb: Checkbox) -> None:
        nonlocal received_checkbox
        received_checkbox = cb

    checkbox.toggle_state()

    assert received_checkbox == checkbox


def test_toggle_state_outputs_speech(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that toggle_state outputs speech."""
    mock_speech = mocker.patch("sonartk.ui.element.checkbox.speech_manager")
    checkbox = Checkbox(parent, "Option", False)  # type: ignore[arg-type]

    checkbox.toggle_state()

    mock_speech.output.assert_called_with(
        "Checked", interrupt=True, log_message=False
    )


# reset Tests


def test_reset_restores_default_value_false(parent: UIComponent) -> None:
    """Test that reset restores value to default (False)."""
    checkbox = Checkbox(parent, "Option", False)  # type: ignore[arg-type]
    checkbox.toggle_state()
    assert checkbox.value is True

    checkbox.reset()
    assert checkbox.value is False


def test_reset_restores_default_value_true(parent: UIComponent) -> None:
    """Test that reset restores value to default (True)."""
    checkbox = Checkbox(parent, "Option", True)  # type: ignore[arg-type]
    checkbox.toggle_state()
    assert checkbox.value is False

    checkbox.reset()
    assert checkbox.value is True


def test_reset_does_not_change_default_value(parent: UIComponent) -> None:
    """Test that reset does not change default_value."""
    checkbox = Checkbox(parent, "Option", True)  # type: ignore[arg-type]
    original_default = checkbox.default_value

    checkbox.toggle_state()
    checkbox.reset()

    assert checkbox.default_value == original_default


def test_reset_multiple_times(parent: UIComponent) -> None:
    """Test that reset can be called multiple times."""
    checkbox = Checkbox(parent, "Option", False)  # type: ignore[arg-type]

    checkbox.toggle_state()
    checkbox.reset()
    assert checkbox.value is False

    checkbox.toggle_state()
    checkbox.reset()
    assert checkbox.value is False


# name Property Tests


def test_name_property_returns_label_role_and_state_unchecked(
    parent: UIComponent,
) -> None:
    """Test that name property returns 'label checkbox Unchecked'."""
    checkbox = Checkbox(parent, "Remember", False)  # type: ignore[arg-type]
    assert checkbox.name == "Remember checkbox Unchecked"


def test_name_property_returns_label_role_and_state_checked(
    parent: UIComponent,
) -> None:
    """Test that name property returns 'label checkbox Checked'."""
    checkbox = Checkbox(parent, "Remember", True)  # type: ignore[arg-type]
    assert checkbox.name == "Remember checkbox Checked"


def test_name_property_updates_after_toggle(parent: UIComponent) -> None:
    """Test that name property updates after toggle_state."""
    checkbox = Checkbox(parent, "Option", False)  # type: ignore[arg-type]
    assert checkbox.name == "Option checkbox Unchecked"

    checkbox.toggle_state()
    assert checkbox.name == "Option checkbox Checked"


def test_name_property_with_empty_label(parent: UIComponent) -> None:
    """Test that name property works with empty label."""
    checkbox = Checkbox(parent, "", False)  # type: ignore[arg-type]
    assert checkbox.name == " checkbox Unchecked"


# Inheritance Tests


def test_checkbox_inherits_from_element(parent: UIComponent) -> None:
    """Test that Checkbox inherits from Element."""
    checkbox = Checkbox(parent, "Option")  # type: ignore[arg-type]
    assert isinstance(checkbox, Element)


def test_checkbox_generic_type_is_bool(parent: UIComponent) -> None:
    """Test that Checkbox uses bool as generic type."""
    checkbox = Checkbox(parent, "Option")  # type: ignore[arg-type]
    assert isinstance(checkbox.value, bool)


def test_checkbox_has_element_methods(parent: UIComponent) -> None:
    """Test that Checkbox has Element methods."""
    checkbox = Checkbox(parent, "Option")  # type: ignore[arg-type]
    assert hasattr(checkbox, "setup")
    assert hasattr(checkbox, "update")
    assert hasattr(checkbox, "exit")
    assert callable(checkbox.setup)
    assert callable(checkbox.update)
    assert callable(checkbox.exit)


def test_checkbox_has_get_window_method(parent: UIComponent) -> None:
    """Test that Checkbox has get_window method."""
    checkbox = Checkbox(parent, "Option")  # type: ignore[arg-type]
    assert hasattr(checkbox, "get_window")
    assert callable(checkbox.get_window)


# Event Registration Tests


def test_on_change_event_is_registered() -> None:
    """Test that on_change event is registered on Checkbox class."""
    assert "on_change" in Checkbox.event_types


def test_on_checked_event_is_registered() -> None:
    """Test that on_checked event is registered on Checkbox class."""
    assert "on_checked" in Checkbox.event_types


def test_on_unchecked_event_is_registered() -> None:
    """Test that on_unchecked event is registered on Checkbox class."""
    assert "on_unchecked" in Checkbox.event_types


def test_checkbox_has_inherited_events() -> None:
    """Test that Checkbox has inherited events from Element."""
    assert "on_focus" in Checkbox.event_types
    assert "on_lose_focus" in Checkbox.event_types
    assert "on_update" in Checkbox.event_types


# Integration Tests


def test_checkbox_lifecycle(
    mocker: MockerFixture, window: Window, parent: UIComponent
) -> None:
    """Test complete checkbox lifecycle."""
    checkbox = Checkbox(parent, "Option", False)  # type: ignore[arg-type]

    mock_push = mocker.patch.object(window, "push_window_handlers")
    mock_pop = mocker.patch.object(window, "pop_window_handlers")

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    # Setup
    result = checkbox.setup(mock_change_state)
    assert result is True
    mock_push.assert_called_once_with(checkbox.key_handler)

    # Update
    result = checkbox.update(0.016)
    assert result is True

    # Toggle
    result = checkbox.toggle_state()
    assert result is True
    assert checkbox.value is True

    # Reset
    checkbox.reset()
    assert checkbox.value is False

    # Exit
    result = checkbox.exit()
    assert result is True
    mock_pop.assert_called_once()


def test_checkbox_multiple_event_listeners(parent: UIComponent) -> None:
    """Test that multiple event listeners work correctly."""
    checkbox = Checkbox(parent, "Option", False)  # type: ignore[arg-type]
    change_count = 0
    checked_count = 0
    unchecked_count = 0

    @checkbox.event  # type: ignore[misc]
    def on_change(cb: Checkbox) -> None:
        nonlocal change_count
        change_count += 1

    @checkbox.event  # type: ignore[misc]
    def on_checked(cb: Checkbox) -> None:
        nonlocal checked_count
        checked_count += 1

    @checkbox.event  # type: ignore[misc]
    def on_unchecked(cb: Checkbox) -> None:
        nonlocal unchecked_count
        unchecked_count += 1

    checkbox.toggle_state()
    assert change_count == 1
    assert checked_count == 1
    assert unchecked_count == 0

    checkbox.toggle_state()
    assert change_count == 2
    assert checked_count == 1
    assert unchecked_count == 1


def test_checkbox_key_press_simulation(parent: UIComponent) -> None:
    """Test simulating key press on checkbox."""
    checkbox = Checkbox(parent, "Option", False)  # type: ignore[arg-type]

    # Simulate RETURN key press
    for k, (
        callback,
        _,
    ) in checkbox.key_handler.registered_key_presses.items():
        if k.symbol == key.RETURN and k.modifiers == 0:
            callback.call()
            break

    assert checkbox.value is True


def test_checkbox_with_different_parent_types(window: Window) -> None:
    """Test checkbox with different parent types."""
    # Direct parent as UIComponent
    parent1 = UIComponent()
    parent1.parent = window
    checkbox1 = Checkbox(parent1, "Checkbox1")  # type: ignore[arg-type]
    assert checkbox1.parent == parent1

    # Nested parent
    parent2 = UIComponent()
    parent2.parent = parent1
    checkbox2 = Checkbox(parent2, "Checkbox2")  # type: ignore[arg-type]
    assert checkbox2.parent == parent2
    assert checkbox2.get_window() == window


def test_checkbox_default_value_preservation(parent: UIComponent) -> None:
    """Test that default_value is preserved throughout lifecycle."""
    checkbox = Checkbox(parent, "Option", True)  # type: ignore[arg-type]

    assert checkbox.default_value is True

    checkbox.toggle_state()
    assert checkbox.default_value is True

    checkbox.toggle_state()
    assert checkbox.default_value is True

    checkbox.reset()
    assert checkbox.default_value is True


def test_checkbox_value_type_is_bool(parent: UIComponent) -> None:
    """Test that checkbox value is always a bool."""
    checkbox = Checkbox(parent, "Option")  # type: ignore[arg-type]

    assert type(checkbox.value) is bool
    checkbox.toggle_state()
    assert type(checkbox.value) is bool
    checkbox.reset()
    assert type(checkbox.value) is bool
