from typing import Any, Optional

import pytest
from pytest_mock import MockerFixture

from sonartk.ui.element.element import Element
from sonartk.ui.ui_component import UIComponent
from sonartk.ui.window import Window
from sonartk.util import KeyHandler, speech_manager
from test.mocks.mock_pyglet_window import MockPygletWindow


class ConcreteElement(Element[str]):
    """Concrete implementation of Element for testing."""

    def __init__(
        self,
        parent: UIComponent,
        label: str = "Test Label",
        role: str = "button",
        value: Optional[str] = None,
        use_key_handler: bool = True,
    ) -> None:
        super().__init__(parent, label, role, value, use_key_handler)

    def bind_keys(self) -> None:
        """Implement abstract bind_keys method."""
        pass

    def reset(self) -> None:
        """Implement abstract reset method."""
        pass


class IntElement(Element[int]):
    """Element with int generic type for testing."""

    def __init__(
        self,
        parent: UIComponent,
        label: str = "Int Label",
        role: str = "number",
        value: Optional[int] = None,
        use_key_handler: bool = False,
    ) -> None:
        super().__init__(parent, label, role, value, use_key_handler)

    def bind_keys(self) -> None:
        pass

    def reset(self) -> None:
        pass


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
    return parent


@pytest.fixture
def element(parent: UIComponent) -> ConcreteElement:
    """Create a ConcreteElement fixture."""
    return ConcreteElement(parent, "Test", "button", "initial_value")


# Initialization Tests


def test_init_sets_parent(
    parent: UIComponent, element: ConcreteElement
) -> None:
    """Test that __init__ sets parent correctly."""
    assert element.parent == parent


def test_init_sets_label(parent: UIComponent) -> None:
    """Test that __init__ sets label correctly."""
    element = ConcreteElement(parent, "My Label", "button", None)
    assert element.label == "My Label"


def test_init_sets_role(parent: UIComponent) -> None:
    """Test that __init__ sets role correctly."""
    element = ConcreteElement(parent, "Label", "checkbox", None)
    assert element.role == "checkbox"


def test_init_sets_value(parent: UIComponent) -> None:
    """Test that __init__ sets value correctly."""
    element = ConcreteElement(parent, "Label", "button", "test_value")
    assert element.value == "test_value"


def test_init_sets_value_none(parent: UIComponent) -> None:
    """Test that __init__ can set value to None."""
    element = ConcreteElement(parent, "Label", "button", None)
    assert element.value is None


def test_init_sets_use_key_handler_true(parent: UIComponent) -> None:
    """Test that __init__ sets use_key_handler to True by default."""
    element = ConcreteElement(parent, "Label", "button", None)
    assert element.use_key_handler is True


def test_init_sets_use_key_handler_false(parent: UIComponent) -> None:
    """Test that __init__ can set use_key_handler to False."""
    element = ConcreteElement(
        parent, "Label", "button", None, use_key_handler=False
    )
    assert element.use_key_handler is False


def test_init_creates_key_handler_when_true(parent: UIComponent) -> None:
    """Test that __init__ creates KeyHandler when use_key_handler is True."""
    element = ConcreteElement(
        parent, "Label", "button", None, use_key_handler=True
    )
    assert isinstance(element.key_handler, KeyHandler)


def test_init_does_not_create_key_handler_when_false(
    parent: UIComponent,
) -> None:
    """Test that __init__ doesn't create KeyHandler when use_key_handler is False."""
    element = ConcreteElement(
        parent, "Label", "button", None, use_key_handler=False
    )
    assert not hasattr(element, "key_handler")


def test_init_calls_bind_keys_when_use_key_handler_true(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that __init__ calls bind_keys when use_key_handler is True."""
    mock_bind_keys = mocker.patch.object(ConcreteElement, "bind_keys")
    ConcreteElement(parent, "Label", "button", None, use_key_handler=True)
    mock_bind_keys.assert_called_once()


def test_init_does_not_call_bind_keys_when_use_key_handler_false(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that __init__ doesn't call bind_keys when use_key_handler is False."""
    mock_bind_keys = mocker.patch.object(ConcreteElement, "bind_keys")
    ConcreteElement(parent, "Label", "button", None, use_key_handler=False)
    mock_bind_keys.assert_not_called()


# Generic Type Tests


def test_generic_type_str(parent: UIComponent) -> None:
    """Test that Element works with str generic type."""
    element = ConcreteElement(parent, "Label", "button", "string_value")
    assert element.value == "string_value"


def test_generic_type_int(parent: UIComponent) -> None:
    """Test that Element works with int generic type."""
    element = IntElement(parent, "Label", "number", 42)
    assert element.value == 42


def test_generic_type_none(parent: UIComponent) -> None:
    """Test that Element works with None value."""
    element = ConcreteElement(parent, "Label", "button", None)
    assert element.value is None


# setup Tests


def test_setup_outputs_speech_when_label_exists(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that setup outputs speech when label is not empty."""
    mock_output = mocker.patch.object(speech_manager, "output")
    element = ConcreteElement(parent, "Test Label", "button", None)

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    element.setup(mock_change_state, interrupt_speech=True)

    mock_output.assert_called_once_with(
        "Test Label button", interrupt=True, log_message=False
    )


def test_setup_does_not_output_speech_when_label_empty(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that setup doesn't output speech when label is empty."""
    mock_output = mocker.patch.object(speech_manager, "output")
    element = ConcreteElement(parent, "", "button", None)

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    element.setup(mock_change_state)

    mock_output.assert_not_called()


def test_setup_uses_interrupt_speech_false_by_default(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that setup uses interrupt_speech=False by default."""
    mock_output = mocker.patch.object(speech_manager, "output")
    element = ConcreteElement(parent, "Label", "button", None)

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    element.setup(mock_change_state)

    mock_output.assert_called_once_with(
        "Label button", interrupt=False, log_message=False
    )


def test_setup_pushes_window_handlers_when_use_key_handler_true(
    mocker: MockerFixture, window: Window, parent: UIComponent
) -> None:
    """Test that setup pushes window handlers when use_key_handler is True."""
    element = ConcreteElement(
        parent, "Label", "button", None, use_key_handler=True
    )
    mock_push = mocker.patch.object(window, "push_window_handlers")

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    element.setup(mock_change_state)

    mock_push.assert_called_once_with(element.key_handler)


def test_setup_does_not_push_handlers_when_use_key_handler_false(
    mocker: MockerFixture, window: Window, parent: UIComponent
) -> None:
    """Test that setup doesn't push handlers when use_key_handler is False."""
    element = ConcreteElement(
        parent, "Label", "button", None, use_key_handler=False
    )
    mock_push = mocker.patch.object(window, "push_window_handlers")

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    element.setup(mock_change_state)

    mock_push.assert_not_called()


def test_setup_dispatches_on_focus_event(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that setup dispatches on_focus event."""
    element = ConcreteElement(
        parent, "Label", "button", None, use_key_handler=False
    )
    mock_dispatch = mocker.patch.object(element, "dispatch_event")

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    element.setup(mock_change_state)

    mock_dispatch.assert_called_once_with("on_focus", element)


def test_setup_returns_true(parent: UIComponent) -> None:
    """Test that setup returns True."""
    element = ConcreteElement(
        parent, "Label", "button", None, use_key_handler=False
    )

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    result = element.setup(mock_change_state)
    assert result is True


def test_setup_event_listener_receives_event(
    parent: UIComponent,
) -> None:
    """Test that on_focus event listener receives the event."""
    element = ConcreteElement(
        parent, "Label", "button", None, use_key_handler=False
    )
    received_element = None

    @element.event  # type: ignore[misc]
    def on_focus(elem: Element[str]) -> None:
        nonlocal received_element
        received_element = elem

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    element.setup(mock_change_state)

    assert received_element == element


# update Tests


def test_update_dispatches_on_update_event(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that update dispatches on_update event."""
    element = ConcreteElement(
        parent, "Label", "button", None, use_key_handler=False
    )
    mock_dispatch = mocker.patch.object(element, "dispatch_event")

    element.update(0.016)

    mock_dispatch.assert_called_once_with("on_update", element, 0.016)


def test_update_returns_true(parent: UIComponent) -> None:
    """Test that update returns True."""
    element = ConcreteElement(
        parent, "Label", "button", None, use_key_handler=False
    )
    result = element.update(0.016)
    assert result is True


def test_update_with_different_delta_times(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that update works with different delta_time values."""
    element = ConcreteElement(
        parent, "Label", "button", None, use_key_handler=False
    )
    mock_dispatch = mocker.patch.object(element, "dispatch_event")

    element.update(0.5)
    mock_dispatch.assert_called_with("on_update", element, 0.5)

    mock_dispatch.reset_mock()
    element.update(1.0)
    mock_dispatch.assert_called_with("on_update", element, 1.0)


def test_update_event_listener_receives_event(
    parent: UIComponent,
) -> None:
    """Test that on_update event listener receives the event."""
    element = ConcreteElement(
        parent, "Label", "button", None, use_key_handler=False
    )
    received_element = None
    received_delta = None

    @element.event  # type: ignore[misc]
    def on_update(elem: Element[str], delta_time: float) -> None:
        nonlocal received_element, received_delta
        received_element = elem
        received_delta = delta_time

    element.update(0.016)

    assert received_element == element
    assert received_delta == 0.016


# exit Tests


def test_exit_dispatches_on_lose_focus_event(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test that exit dispatches on_lose_focus event."""
    element = ConcreteElement(
        parent, "Label", "button", None, use_key_handler=False
    )
    mock_dispatch = mocker.patch.object(element, "dispatch_event")

    element.exit()

    mock_dispatch.assert_called_once_with("on_lose_focus", element)


def test_exit_pops_window_handlers_when_use_key_handler_true(
    mocker: MockerFixture, window: Window, parent: UIComponent
) -> None:
    """Test that exit pops window handlers when use_key_handler is True."""
    element = ConcreteElement(
        parent, "Label", "button", None, use_key_handler=True
    )
    mock_pop = mocker.patch.object(window, "pop_window_handlers")

    element.exit()

    mock_pop.assert_called_once()


def test_exit_does_not_pop_handlers_when_use_key_handler_false(
    mocker: MockerFixture, window: Window, parent: UIComponent
) -> None:
    """Test that exit doesn't pop handlers when use_key_handler is False."""
    element = ConcreteElement(
        parent, "Label", "button", None, use_key_handler=False
    )
    mock_pop = mocker.patch.object(window, "pop_window_handlers")

    element.exit()

    mock_pop.assert_not_called()


def test_exit_returns_true(parent: UIComponent) -> None:
    """Test that exit returns True."""
    element = ConcreteElement(
        parent, "Label", "button", None, use_key_handler=False
    )
    result = element.exit()
    assert result is True


def test_exit_event_listener_receives_event(
    parent: UIComponent,
) -> None:
    """Test that on_lose_focus event listener receives the event."""
    element = ConcreteElement(
        parent, "Label", "button", None, use_key_handler=False
    )
    received_element = None

    @element.event  # type: ignore[misc]
    def on_lose_focus(elem: Element[str]) -> None:
        nonlocal received_element
        received_element = elem

    element.exit()

    assert received_element == element


# value Property Tests


def test_value_getter_returns_value(parent: UIComponent) -> None:
    """Test that value property getter returns the value."""
    element = ConcreteElement(parent, "Label", "button", "test_value")
    assert element.value == "test_value"


def test_value_getter_returns_none(parent: UIComponent) -> None:
    """Test that value property getter can return None."""
    element = ConcreteElement(parent, "Label", "button", None)
    assert element.value is None


def test_value_setter_sets_value(parent: UIComponent) -> None:
    """Test that value property setter sets the value."""
    element = ConcreteElement(parent, "Label", "button", "initial")
    element.value = "updated"
    assert element.value == "updated"


def test_value_setter_can_set_none(parent: UIComponent) -> None:
    """Test that value property setter can set None."""
    element = ConcreteElement(parent, "Label", "button", "initial")
    element.value = None  # type: ignore[assignment]
    assert element.value is None


def test_value_setter_with_different_types(parent: UIComponent) -> None:
    """Test that value setter works with different generic types."""
    int_element = IntElement(parent, "Label", "number", 10)
    assert int_element.value == 10

    int_element.value = 42
    assert int_element.value == 42


def test_value_internal_storage(parent: UIComponent) -> None:
    """Test that value is stored in _value internally."""
    element = ConcreteElement(parent, "Label", "button", "test")
    assert element._value == "test"

    element.value = "new"
    assert element._value == "new"


# name Property Tests


def test_name_property_returns_label_and_role(parent: UIComponent) -> None:
    """Test that name property returns 'label role'."""
    element = ConcreteElement(parent, "My Label", "button", None)
    assert element.name == "My Label button"


def test_name_property_with_different_values(parent: UIComponent) -> None:
    """Test that name property works with different label/role combinations."""
    element1 = ConcreteElement(parent, "Submit", "button", None)
    assert element1.name == "Submit button"

    element2 = ConcreteElement(parent, "Accept Terms", "checkbox", None)
    assert element2.name == "Accept Terms checkbox"


def test_name_property_with_empty_label(parent: UIComponent) -> None:
    """Test that name property works with empty label."""
    element = ConcreteElement(parent, "", "button", None)
    assert element.name == " button"


# Inheritance Tests


def test_element_inherits_from_ui_component(parent: UIComponent) -> None:
    """Test that Element inherits from UIComponent."""
    element = ConcreteElement(parent, "Label", "button", None)
    assert isinstance(element, UIComponent)


def test_element_inherits_from_state(parent: UIComponent) -> None:
    """Test that Element inherits from State."""
    from sonartk.util.state import State

    element = ConcreteElement(parent, "Label", "button", None)
    assert isinstance(element, State)


def test_element_inherits_from_event_dispatcher(parent: UIComponent) -> None:
    """Test that Element inherits from EventDispatcher."""
    from pyglet.event import EventDispatcher

    element = ConcreteElement(parent, "Label", "button", None)
    assert isinstance(element, EventDispatcher)


def test_element_has_get_window_method(parent: UIComponent) -> None:
    """Test that Element has get_window method from UIComponent."""
    element = ConcreteElement(parent, "Label", "button", None)
    assert hasattr(element, "get_window")
    assert callable(element.get_window)


def test_element_get_window_returns_window(
    window: Window, parent: UIComponent
) -> None:
    """Test that get_window returns the window."""
    element = ConcreteElement(parent, "Label", "button", None)
    assert element.get_window() == window


# Event Registration Tests


def test_on_focus_event_is_registered() -> None:
    """Test that on_focus event is registered on Element class."""
    assert "on_focus" in Element.event_types


def test_on_lose_focus_event_is_registered() -> None:
    """Test that on_lose_focus event is registered on Element class."""
    assert "on_lose_focus" in Element.event_types


def test_on_update_event_is_registered() -> None:
    """Test that on_update event is registered on Element class."""
    assert "on_update" in Element.event_types


# Integration Tests


def test_full_lifecycle_with_key_handler(
    mocker: MockerFixture, window: Window, parent: UIComponent
) -> None:
    """Test complete element lifecycle with key handler."""
    element = ConcreteElement(
        parent, "Test", "button", "value", use_key_handler=True
    )

    assert element.value == "value"
    assert isinstance(element.key_handler, KeyHandler)

    mock_push = mocker.patch.object(window, "push_window_handlers")
    mock_pop = mocker.patch.object(window, "pop_window_handlers")

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    # Setup
    result = element.setup(mock_change_state)
    assert result is True
    mock_push.assert_called_once_with(element.key_handler)

    # Update
    result = element.update(0.016)
    assert result is True

    # Exit
    result = element.exit()
    assert result is True
    mock_pop.assert_called_once()


def test_full_lifecycle_without_key_handler(
    mocker: MockerFixture, parent: UIComponent
) -> None:
    """Test complete element lifecycle without key handler."""
    element = ConcreteElement(
        parent, "Test", "button", "value", use_key_handler=False
    )

    assert element.value == "value"
    assert not hasattr(element, "key_handler")

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    # Setup
    result = element.setup(mock_change_state)
    assert result is True

    # Update
    result = element.update(0.016)
    assert result is True

    # Exit
    result = element.exit()
    assert result is True


def test_multiple_event_listeners(parent: UIComponent) -> None:
    """Test that multiple event listeners can be attached."""
    element = ConcreteElement(
        parent, "Test", "button", None, use_key_handler=False
    )

    focus_count = 0
    update_count = 0
    lose_focus_count = 0

    @element.event  # type: ignore[misc]
    def on_focus(elem: Element[str]) -> None:
        nonlocal focus_count
        focus_count += 1

    @element.event  # type: ignore[misc]
    def on_update(elem: Element[str], delta_time: float) -> None:
        nonlocal update_count
        update_count += 1

    @element.event  # type: ignore[misc]
    def on_lose_focus(elem: Element[str]) -> None:
        nonlocal lose_focus_count
        lose_focus_count += 1

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    element.setup(mock_change_state)
    assert focus_count == 1

    element.update(0.016)
    element.update(0.016)
    assert update_count == 2

    element.exit()
    assert lose_focus_count == 1


def test_value_changes_during_lifecycle(parent: UIComponent) -> None:
    """Test that value can be changed during element lifecycle."""
    element = ConcreteElement(
        parent, "Test", "button", "initial", use_key_handler=False
    )

    assert element.value == "initial"

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    element.setup(mock_change_state)
    element.value = "during_setup"
    assert element.value == "during_setup"

    element.update(0.016)
    element.value = "during_update"
    assert element.value == "during_update"

    element.exit()
    element.value = "after_exit"
    assert element.value == "after_exit"


def test_element_with_complex_label_and_role(parent: UIComponent) -> None:
    """Test element with complex label and role strings."""
    element = ConcreteElement(
        parent,
        "Submit Form Button",
        "interactive button element",
        "submit_action",
    )

    assert element.label == "Submit Form Button"
    assert element.role == "interactive button element"
    assert element.name == "Submit Form Button interactive button element"
