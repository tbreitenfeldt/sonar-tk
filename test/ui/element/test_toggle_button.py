from typing import Any, Callable

import pytest
from pyglet.window import key
from pytest_mock import MockerFixture

from sonartk.ui.element.element import Element
from sonartk.ui.element.toggle_button import ToggleButton
from sonartk.ui.ui_component import UIComponent
from sonartk.ui.window import Window
from sonartk.util import KeyHandler, speech_manager
from sonartk.util.key_handler import Key
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
def toggle(parent: UIComponent) -> ToggleButton:
    """Create a ToggleButton fixture with three items."""
    return ToggleButton(parent, "Speed", 0, ["Slow", "Medium", "Fast"])  # type: ignore[arg-type]


# Initialization Tests


def test_init_sets_parent(parent: UIComponent, toggle: ToggleButton) -> None:
    """Test that __init__ sets parent correctly."""
    assert toggle.parent == parent


def test_init_sets_label(parent: UIComponent) -> None:
    """Test that __init__ sets label correctly."""
    tb = ToggleButton(parent, "Volume", 0, ["Low", "High"])  # type: ignore[arg-type]
    assert tb.label == "Volume"


def test_init_sets_role_to_toggle(parent: UIComponent) -> None:
    """Test that __init__ sets role to 'toggle'."""
    tb = ToggleButton(parent, "Mode", 0, ["A", "B"])  # type: ignore[arg-type]
    assert tb.role == "toggle"


def test_init_sets_value_to_empty_string(parent: UIComponent) -> None:
    """Test that __init__ sets value to empty string."""
    tb = ToggleButton(parent, "Label", 0, ["X"])  # type: ignore[arg-type]
    assert tb.value == ""


def test_init_sets_items(parent: UIComponent) -> None:
    """Test that __init__ sets items correctly."""
    items = ["Option A", "Option B", "Option C"]
    tb = ToggleButton(parent, "Label", 0, items)  # type: ignore[arg-type]
    assert tb.items == items


def test_init_sets_position(parent: UIComponent) -> None:
    """Test that __init__ sets position correctly."""
    tb = ToggleButton(parent, "Label", 2, ["A", "B", "C"])  # type: ignore[arg-type]
    assert tb.position == 2


def test_init_sets_default_position(parent: UIComponent) -> None:
    """Test that __init__ sets default_position from position arg."""
    tb = ToggleButton(parent, "Label", 1, ["A", "B", "C"])  # type: ignore[arg-type]
    assert tb.default_position == 1


def test_init_default_label_empty(parent: UIComponent) -> None:
    """Test that default label is an empty string."""
    tb = ToggleButton(parent)  # type: ignore[arg-type]
    assert tb.label == ""


def test_init_default_position_zero(parent: UIComponent) -> None:
    """Test that default position is 0."""
    tb = ToggleButton(parent, "Label", items=["A", "B"])  # type: ignore[arg-type]
    assert tb.position == 0


def test_init_default_items_empty(parent: UIComponent) -> None:
    """Test that default items list is empty."""
    tb = ToggleButton(parent, "Label")  # type: ignore[arg-type]
    assert tb.items == []


def test_init_creates_key_handler(parent: UIComponent) -> None:
    """Test that __init__ creates a KeyHandler."""
    tb = ToggleButton(parent, "Label", 0, ["A"])  # type: ignore[arg-type]
    assert isinstance(tb.key_handler, KeyHandler)


def test_init_calls_bind_keys(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that __init__ calls bind_keys."""
    mock_bind = mocker.patch.object(ToggleButton, "bind_keys")
    ToggleButton(parent, "Label", 0, ["A"])  # type: ignore[arg-type]
    mock_bind.assert_called_once()


# bind_keys Tests


def test_bind_keys_registers_return_for_next(
    parent: UIComponent, toggle: ToggleButton
) -> None:
    """Test that bind_keys registers RETURN key to call next."""
    assert Key(key.RETURN) in toggle.key_handler.registered_key_presses


def test_bind_keys_registers_space_for_next(
    parent: UIComponent, toggle: ToggleButton
) -> None:
    """Test that bind_keys registers SPACE key to call next."""
    assert Key(key.SPACE) in toggle.key_handler.registered_key_presses


def test_bind_keys_return_handler_is_next(
    parent: UIComponent, toggle: ToggleButton
) -> None:
    """Test that the RETURN key handler callback is toggle.next."""
    callback, _ = toggle.key_handler.registered_key_presses[Key(key.RETURN)]
    assert callback.callback == toggle.next


def test_bind_keys_space_handler_is_next(
    parent: UIComponent, toggle: ToggleButton
) -> None:
    """Test that the SPACE key handler callback is toggle.next."""
    callback, _ = toggle.key_handler.registered_key_presses[Key(key.SPACE)]
    assert callback.callback == toggle.next


# setup Tests


def test_setup_calls_parent_setup(
    mocker: MockerFixture, parent: UIComponent, toggle: ToggleButton
) -> None:
    """Test that setup calls the parent Element.setup."""
    mock_super_setup = mocker.patch.object(Element, "setup", return_value=True)
    toggle.setup(lambda k, *a, **kw: None)
    mock_super_setup.assert_called_once()


def test_setup_outputs_current_item(
    mocker: MockerFixture, parent: UIComponent, toggle: ToggleButton
) -> None:
    """Test that setup outputs the item at the current position."""
    mocker.patch.object(Element, "setup", return_value=True)
    mock_output = mocker.patch.object(speech_manager, "output")
    toggle.setup(lambda k, *a, **kw: None)
    mock_output.assert_called_once_with(
        "Slow", interrupt=False, log_message=False
    )


def test_setup_outputs_item_at_non_zero_position(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that setup outputs the item at a non-zero starting position."""
    mocker.patch.object(Element, "setup", return_value=True)
    mock_output = mocker.patch.object(speech_manager, "output")
    tb = ToggleButton(parent, "Speed", 2, ["Slow", "Medium", "Fast"])  # type: ignore[arg-type]
    tb.setup(lambda k, *a, **kw: None)
    mock_output.assert_called_once_with(
        "Fast", interrupt=False, log_message=False
    )


def test_setup_uses_interrupt_speech_true_by_default(
    mocker: MockerFixture, parent: UIComponent, toggle: ToggleButton
) -> None:
    """Test that setup passes interrupt_speech=True by default to parent setup."""
    mock_super_setup = mocker.patch.object(Element, "setup", return_value=True)
    toggle.setup(lambda k, *a, **kw: None)
    _, kwargs = mock_super_setup.call_args
    assert kwargs.get("interrupt_speech", True) is True


def test_setup_returns_true(
    mocker: MockerFixture, parent: UIComponent, toggle: ToggleButton
) -> None:
    """Test that setup returns True."""
    mocker.patch.object(Element, "setup", return_value=True)
    mocker.patch.object(speech_manager, "output")
    result = toggle.setup(lambda k, *a, **kw: None)
    assert result is True


# next Tests


def test_next_advances_position(
    parent: UIComponent, toggle: ToggleButton
) -> None:
    """Test that next increments position by one."""
    toggle.next()
    assert toggle.position == 1


def test_next_wraps_around_to_zero(
    parent: UIComponent, toggle: ToggleButton
) -> None:
    """Test that next wraps position back to 0 after the last item."""
    toggle.position = 2
    toggle.next()
    assert toggle.position == 0


def test_next_updates_value(parent: UIComponent, toggle: ToggleButton) -> None:
    """Test that next updates value to the new item."""
    toggle.next()
    assert toggle.value == "Medium"


def test_next_updates_value_on_wrap(
    parent: UIComponent, toggle: ToggleButton
) -> None:
    """Test that next updates value correctly when wrapping."""
    toggle.position = 2
    toggle.next()
    assert toggle.value == "Slow"


def test_next_outputs_new_value(
    mocker: MockerFixture, parent: UIComponent, toggle: ToggleButton
) -> None:
    """Test that next outputs the new item via speech_manager."""
    mock_output = mocker.patch.object(speech_manager, "output")
    toggle.next()
    mock_output.assert_called_once_with(
        "Medium", interrupt=True, log_message=False
    )


def test_next_dispatches_on_change_event(
    mocker: MockerFixture, parent: UIComponent, toggle: ToggleButton
) -> None:
    """Test that next dispatches the on_change event."""
    mock_dispatch = mocker.patch.object(toggle, "dispatch_event")
    toggle.next()
    mock_dispatch.assert_called_once_with("on_change", toggle)


def test_next_returns_true(parent: UIComponent, toggle: ToggleButton) -> None:
    """Test that next returns True."""
    result = toggle.next()
    assert result is True


def test_next_multiple_times_cycles_through_all(
    parent: UIComponent, toggle: ToggleButton
) -> None:
    """Test that calling next repeatedly cycles through all items."""
    toggle.next()
    assert toggle.value == "Medium"
    toggle.next()
    assert toggle.value == "Fast"
    toggle.next()
    assert toggle.value == "Slow"


def test_next_on_change_listener_receives_element(
    parent: UIComponent, toggle: ToggleButton
) -> None:
    """Test that on_change listener receives the ToggleButton instance."""
    received: list[ToggleButton] = []

    @toggle.event  # type: ignore[misc]
    def on_change(elem: ToggleButton) -> None:
        received.append(elem)

    toggle.next()
    assert received == [toggle]


def test_next_single_item_stays_at_zero(parent: UIComponent) -> None:
    """Test that next with a single item keeps position at 0."""
    tb = ToggleButton(parent, "Label", 0, ["Only"])  # type: ignore[arg-type]
    tb.next()
    assert tb.position == 0
    assert tb.value == "Only"


# add Tests


def test_add_appends_item(parent: UIComponent, toggle: ToggleButton) -> None:
    """Test that add appends an item to the items list."""
    toggle.add("Turbo")
    assert "Turbo" in toggle.items


def test_add_increases_items_length(
    parent: UIComponent, toggle: ToggleButton
) -> None:
    """Test that add increases the length of items by one."""
    original_length = len(toggle.items)
    toggle.add("New Item")
    assert len(toggle.items) == original_length + 1


def test_add_preserves_existing_items(
    parent: UIComponent, toggle: ToggleButton
) -> None:
    """Test that add preserves existing items."""
    toggle.add("Extra")
    assert toggle.items[:3] == ["Slow", "Medium", "Fast"]


def test_add_multiple_items(parent: UIComponent, toggle: ToggleButton) -> None:
    """Test that multiple add calls append items in order."""
    toggle.add("X")
    toggle.add("Y")
    assert toggle.items[-2:] == ["X", "Y"]


def test_add_to_empty_list(parent: UIComponent) -> None:
    """Test that add works when starting from an empty items list."""
    tb = ToggleButton(parent, "Label")  # type: ignore[arg-type]
    tb.add("First")
    assert tb.items == ["First"]


def test_add_does_not_change_position(
    parent: UIComponent, toggle: ToggleButton
) -> None:
    """Test that add does not change the current position."""
    toggle.position = 1
    toggle.add("Extra")
    assert toggle.position == 1


def test_add_returns_none(parent: UIComponent, toggle: ToggleButton) -> None:
    """Test that add returns None."""
    result = toggle.add("Item")
    assert result is None


# reset Tests


def test_reset_restores_default_position_zero(
    parent: UIComponent, toggle: ToggleButton
) -> None:
    """Test that reset restores position to default_position (0)."""
    toggle.position = 2
    toggle.reset()
    assert toggle.position == 0


def test_reset_restores_non_zero_default_position(parent: UIComponent) -> None:
    """Test that reset restores to a non-zero default_position."""
    tb = ToggleButton(parent, "Label", 2, ["A", "B", "C"])  # type: ignore[arg-type]
    tb.position = 0
    tb.reset()
    assert tb.position == 2


def test_reset_does_not_change_value(
    parent: UIComponent, toggle: ToggleButton
) -> None:
    """Test that reset does not update the value property."""
    toggle.next()
    toggle.reset()
    assert toggle.value == "Medium"


def test_reset_returns_none(parent: UIComponent, toggle: ToggleButton) -> None:
    """Test that reset returns None."""
    result = toggle.reset()
    assert result is None


def test_reset_after_multiple_nexts(
    parent: UIComponent, toggle: ToggleButton
) -> None:
    """Test that reset restores position after several next() calls."""
    toggle.next()
    toggle.next()
    toggle.next()
    toggle.reset()
    assert toggle.position == 0


# is-a / isinstance Tests


def test_toggle_button_is_element(parent: UIComponent) -> None:
    """Test that ToggleButton is an instance of Element."""
    tb = ToggleButton(parent, "Label", 0, ["A"])  # type: ignore[arg-type]
    assert isinstance(tb, Element)


def test_toggle_button_is_ui_component(parent: UIComponent) -> None:
    """Test that ToggleButton is an instance of UIComponent."""
    tb = ToggleButton(parent, "Label", 0, ["A"])  # type: ignore[arg-type]
    assert isinstance(tb, UIComponent)


# name property Tests


def test_name_includes_label_and_role(
    parent: UIComponent, toggle: ToggleButton
) -> None:
    """Test that name property returns label followed by role."""
    assert toggle.name == "Speed toggle"
