from typing import Any, Callable, Dict, List, Optional
from unittest.mock import MagicMock

import pytest
from pyglet.window import key
from pytest_mock import MockerFixture

from sonartk.ui.element.element import Element
from sonartk.ui.element.menu import Menu
from sonartk.ui.element.text_label import TextLabel
from sonartk.ui.screen.screen import Screen
from sonartk.ui.ui_component import UIComponent
from sonartk.ui.window import Window
from sonartk.util import KeyHandler
from sonartk.util.state_machine import StateMachine
from test.mocks.mock_pyglet_window import MockPygletWindow


class ConcreteElement(Element[str]):
    """Concrete implementation of Element for testing."""

    def __init__(self, parent: UIComponent, label: str) -> None:
        super().__init__(parent, label, "test_role", label, False)

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
def screen(window: Window, mocker: MockerFixture) -> Screen:
    """Create a Screen fixture."""

    class TestScreen(Screen):
        def bind_keys(self) -> None:
            pass

        def setup(
            self,
            change_state: Callable[[str, Any], None],
            *args: Any,
            **kwargs: Any,
        ) -> bool:
            self.change_state = change_state  # type: ignore[attr-defined]
            return True

        def update(self, delta_time: float) -> bool:
            return True

        def exit(self) -> bool:
            return True

    screen = TestScreen(parent=window)  # type: ignore[arg-type]
    screen.change_state = mocker.MagicMock()  # type: ignore[method-assign]
    return screen


@pytest.fixture
def menu(screen: Screen) -> Menu:
    """Create a Menu fixture with default settings."""
    return Menu(screen, "Main Menu")  # type: ignore[arg-type]


@pytest.fixture
def menu_with_items(screen: Screen) -> Menu:
    """Create a Menu fixture with items."""
    items: List[Dict[str, str]] = [
        {"option1": "Option 1"},
        {"option2": "Option 2"},
        {"option3": "Option 3"},
    ]
    return Menu(screen, "Main Menu", items=items)  # type: ignore[arg-type]


# Initialization Tests


def test_init_sets_parent(screen: Screen, menu: Menu) -> None:
    """Test that __init__ sets parent correctly."""
    assert menu.parent == screen


def test_init_sets_label(screen: Screen) -> None:
    """Test that __init__ sets label correctly."""
    menu = Menu(screen, "Settings Menu")
    assert menu.label == "Settings Menu"


def test_init_sets_empty_label_by_default(screen: Screen) -> None:
    """Test that __init__ sets empty label by default."""
    menu = Menu(screen)
    assert menu.label == ""


def test_init_sets_role_to_menu(screen: Screen) -> None:
    """Test that __init__ sets role to 'menu'."""
    menu = Menu(screen, "Menu")  # type: ignore[arg-type]
    assert menu.role == "menu"


def test_init_creates_key_handler(screen: Screen) -> None:
    """Test that __init__ creates a KeyHandler."""
    menu = Menu(screen, "Menu")  # type: ignore[arg-type]
    assert isinstance(menu.key_handler, KeyHandler)


def test_init_creates_state_machine(screen: Screen) -> None:
    """Test that __init__ creates a StateMachine."""
    menu = Menu(screen, "Menu")  # type: ignore[arg-type]
    assert isinstance(menu.state_machine, StateMachine)


def test_init_sets_position_to_zero_by_default(screen: Screen) -> None:
    """Test that __init__ sets position to 0 by default."""
    menu = Menu(screen, "Menu")  # type: ignore[arg-type]
    assert menu.position == 0


def test_init_sets_custom_position(screen: Screen) -> None:
    """Test that __init__ accepts custom position."""
    items: List[Dict[str, str]] = [{"a": "A"}, {"b": "B"}]
    menu = Menu(screen, "Menu", items=items, position=1)  # type: ignore[arg-type]
    assert menu.position == 1


def test_init_sets_default_position(screen: Screen) -> None:
    """Test that __init__ sets default_position."""
    menu = Menu(screen, "Menu", position=2)  # type: ignore[arg-type]
    assert menu.default_position == 2


def test_init_sets_has_border_false_by_default(screen: Screen) -> None:
    """Test that __init__ sets has_border to False by default."""
    menu = Menu(screen, "Menu")
    assert menu.has_border is False


def test_init_sets_has_border_true(screen: Screen) -> None:
    """Test that __init__ can set has_border to True."""
    menu = Menu(screen, "Menu", has_border=True)
    assert menu.has_border is True


def test_init_sets_is_first_letter_navigation_true_by_default(
    screen: Screen,
) -> None:
    """Test that __init__ sets is_first_letter_navigation to True by default."""
    menu = Menu(screen, "Menu")
    assert menu.is_first_letter_navigation is True


def test_init_sets_is_first_letter_navigation_false(screen: Screen) -> None:
    """Test that __init__ can set is_first_letter_navigation to False."""
    menu = Menu(screen, "Menu", is_first_letter_navigation=False)
    assert menu.is_first_letter_navigation is False


def test_init_sets_is_side_menu_false_by_default(screen: Screen) -> None:
    """Test that __init__ sets is_side_menu to False by default."""
    menu = Menu(screen, "Menu")
    assert menu.is_side_menu is False


def test_init_sets_is_side_menu_true(screen: Screen) -> None:
    """Test that __init__ can set is_side_menu to True."""
    menu = Menu(screen, "Menu", is_side_menu=True)
    assert menu.is_side_menu is True


def test_init_sets_reset_position_on_focus_true_by_default(
    screen: Screen,
) -> None:
    """Test that __init__ sets reset_position_on_focus to True by default."""
    menu = Menu(screen, "Menu")  # type: ignore[arg-type]
    assert menu.reset_position_on_focus is True


def test_init_sets_reset_position_on_focus_false(screen: Screen) -> None:
    """Test that __init__ can set reset_position_on_focus to False."""
    menu = Menu(screen, "Menu", reset_position_on_focus=False)  # type: ignore[arg-type]
    assert menu.reset_position_on_focus is False


def test_init_sets_typing_buffer_to_empty_string(screen: Screen) -> None:
    """Test that __init__ sets typing_buffer to empty string."""
    menu = Menu(screen, "Menu")  # type: ignore[arg-type]
    assert menu.typing_buffer == ""


def test_init_with_string_items(screen: Screen) -> None:
    """Test that __init__ accepts string items."""
    items: List[Dict[str, str]] = [
        {"option1": "Option 1"},
        {"option2": "Option 2"},
    ]
    menu = Menu(screen, "Menu", items=items)  # type: ignore[arg-type]
    assert menu.state_machine.size() == 2


def test_init_with_element_items(screen: Screen) -> None:
    """Test that __init__ accepts Element items."""
    elem1 = ConcreteElement(screen, "Element 1")
    elem2 = ConcreteElement(screen, "Element 2")
    items: List[Dict[str, Element]] = [
        {"elem1": elem1},
        {"elem2": elem2},
    ]
    menu = Menu(screen, "Menu", items=items)  # type: ignore[arg-type]
    assert menu.state_machine.size() == 2


def test_init_raises_error_for_empty_dict_item(screen: Screen) -> None:
    """Test that __init__ raises ValueError for empty dict item."""
    items: List[Dict[str, str]] = [{}]
    with pytest.raises(ValueError, match="Requires 1 dictionary entry"):
        Menu(screen, "Menu", items=items)  # type: ignore[arg-type]


def test_init_raises_error_for_multiple_key_dict(screen: Screen) -> None:
    """Test that __init__ raises ValueError for dict with multiple keys."""
    items: List[Dict[str, str]] = [{"a": "A", "b": "B"}]  # type: ignore[dict-item]
    with pytest.raises(ValueError, match="Requires 1 dictionary entry"):
        Menu(screen, "Menu", items=items)  # type: ignore[arg-type]


def test_init_calls_bind_keys(mocker: MockerFixture, screen: Screen) -> None:
    """Test that __init__ calls bind_keys."""
    mock_bind_keys = mocker.patch.object(Menu, "bind_keys")
    Menu(screen, "Menu")  # type: ignore[arg-type]
    mock_bind_keys.assert_called_once()


# bind_keys Tests


def test_bind_keys_registers_down_for_vertical_menu(screen: Screen) -> None:
    """Test that bind_keys registers DOWN key for vertical menu."""
    menu = Menu(screen, "Menu", is_side_menu=False)
    down_key = None
    for k in menu.key_handler.registered_key_presses.keys():
        if k.symbol == key.DOWN and k.modifiers == 0:
            down_key = k
            break

    assert down_key is not None, "DOWN key should be registered"
    callback, _ = menu.key_handler.registered_key_presses[down_key]
    assert callback.callback == menu.next_item


def test_bind_keys_registers_up_for_vertical_menu(screen: Screen) -> None:
    """Test that bind_keys registers UP key for vertical menu."""
    menu = Menu(screen, "Menu", is_side_menu=False)
    up_key = None
    for k in menu.key_handler.registered_key_presses.keys():
        if k.symbol == key.UP and k.modifiers == 0:
            up_key = k
            break

    assert up_key is not None, "UP key should be registered"
    callback, _ = menu.key_handler.registered_key_presses[up_key]
    assert callback.callback == menu.previous_item


def test_bind_keys_registers_right_for_side_menu(screen: Screen) -> None:
    """Test that bind_keys registers RIGHT key for side menu."""
    menu = Menu(screen, "Menu", is_side_menu=True)
    right_key = None
    for k in menu.key_handler.registered_key_presses.keys():
        if k.symbol == key.RIGHT and k.modifiers == 0:
            right_key = k
            break

    assert right_key is not None, "RIGHT key should be registered"
    callback, _ = menu.key_handler.registered_key_presses[right_key]
    assert callback.callback == menu.next_item


def test_bind_keys_registers_left_for_side_menu(screen: Screen) -> None:
    """Test that bind_keys registers LEFT key for side menu."""
    menu = Menu(screen, "Menu", is_side_menu=True)
    left_key = None
    for k in menu.key_handler.registered_key_presses.keys():
        if k.symbol == key.LEFT and k.modifiers == 0:
            left_key = k
            break

    assert left_key is not None, "LEFT key should be registered"
    callback, _ = menu.key_handler.registered_key_presses[left_key]
    assert callback.callback == menu.previous_item


def test_bind_keys_registers_home_key(screen: Screen) -> None:
    """Test that bind_keys registers HOME key."""
    menu = Menu(screen, "Menu")
    home_key = None
    for k in menu.key_handler.registered_key_presses.keys():
        if k.symbol == key.HOME and k.modifiers == 0:
            home_key = k
            break

    assert home_key is not None, "HOME key should be registered"
    callback, _ = menu.key_handler.registered_key_presses[home_key]
    assert callback.callback == menu.navigate_to_beginning


def test_bind_keys_registers_end_key(screen: Screen) -> None:
    """Test that bind_keys registers END key."""
    menu = Menu(screen, "Menu")
    end_key = None
    for k in menu.key_handler.registered_key_presses.keys():
        if k.symbol == key.END and k.modifiers == 0:
            end_key = k
            break

    assert end_key is not None, "END key should be registered"
    callback, _ = menu.key_handler.registered_key_presses[end_key]
    assert callback.callback == menu.navigate_to_end


def test_bind_keys_registers_return_key(screen: Screen) -> None:
    """Test that bind_keys registers RETURN key."""
    menu = Menu(screen, "Menu")
    return_key = None
    for k in menu.key_handler.registered_key_presses.keys():
        if k.symbol == key.RETURN and k.modifiers == 0:
            return_key = k
            break

    assert return_key is not None, "RETURN key should be registered"
    callback, _ = menu.key_handler.registered_key_presses[return_key]
    assert callback.callback == menu.submit


def test_bind_keys_registers_space_key(screen: Screen) -> None:
    """Test that bind_keys registers SPACE key."""
    menu = Menu(screen, "Menu")
    space_key = None
    for k in menu.key_handler.registered_key_presses.keys():
        if k.symbol == key.SPACE and k.modifiers == 0:
            space_key = k
            break

    assert space_key is not None, "SPACE key should be registered"
    callback, _ = menu.key_handler.registered_key_presses[space_key]
    assert callback.callback == menu.submit


def test_bind_keys_registers_text_input_when_first_letter_nav_enabled(
    screen: Screen,
) -> None:
    """Test that bind_keys registers text input when first letter navigation enabled."""
    menu = Menu(screen, "Menu", is_first_letter_navigation=True)  # type: ignore[arg-type]
    assert menu.key_handler.registered_text_input is not None
    assert (
        menu.key_handler.registered_text_input.callback
        == menu.navigate_by_first_letter
    )


def test_bind_keys_does_not_register_text_input_when_disabled(
    screen: Screen,
) -> None:
    """Test that bind_keys doesn't register text input when disabled."""
    menu = Menu(screen, "Menu", is_first_letter_navigation=False)  # type: ignore[arg-type]
    assert menu.key_handler.registered_text_input is None


# value Property Tests


def test_value_getter_returns_current_menu_item_key(
    menu_with_items: Menu,
) -> None:
    """Test that value getter returns current menu item key."""
    assert menu_with_items.value == "option1"


def test_value_getter_after_position_change(menu_with_items: Menu) -> None:
    """Test that value getter returns correct key after position change."""
    menu_with_items.position = 1
    assert menu_with_items.value == "option2"


def test_value_setter_changes_position(menu_with_items: Menu) -> None:
    """Test that value setter changes position."""
    menu_with_items.value = "option3"
    assert menu_with_items.position == 2


def test_value_setter_changes_state_machine_state(
    menu_with_items: Menu,
) -> None:
    """Test that value setter changes state machine state."""
    menu_with_items.value = "option2"
    assert menu_with_items.state_machine.current_state is not None
    assert menu_with_items.state_machine.current_state.label == "Option 2"  # type: ignore[attr-defined]


def test_value_setter_with_first_item(menu_with_items: Menu) -> None:
    """Test that value setter works with first item."""
    menu_with_items.position = 2
    menu_with_items.value = "option1"
    assert menu_with_items.position == 0


# add Method Tests


def test_add_string_item_creates_text_label(
    screen: Screen, menu: Menu
) -> None:
    """Test that add creates TextLabel for string items."""
    menu.add("item1", "Item 1")
    assert menu.state_machine.size() == 1
    state = menu.state_machine.states["item1"]
    assert isinstance(state, TextLabel)
    assert state.label == "Item 1"


def test_add_element_item(screen: Screen, menu: Menu) -> None:
    """Test that add accepts Element items."""
    elem = ConcreteElement(screen, "Element 1")
    menu.add("elem1", elem)
    assert menu.state_machine.size() == 1
    assert menu.state_machine.states["elem1"] == elem


def test_add_multiple_items(screen: Screen, menu: Menu) -> None:
    """Test that add can be called multiple times."""
    menu.add("item1", "Item 1")
    menu.add("item2", "Item 2")
    menu.add("item3", "Item 3")
    assert menu.state_machine.size() == 3


def test_add_raises_error_for_invalid_type(screen: Screen, menu: Menu) -> None:
    """Test that add raises ValueError for invalid item type."""
    with pytest.raises(ValueError, match="Item must be either str or Element"):
        menu.add("invalid", 123)  # type: ignore[arg-type]


# remove Method Tests


def test_remove_existing_item(menu_with_items: Menu) -> None:
    """Test that remove removes existing item."""
    initial_size = menu_with_items.state_machine.size()
    removed = menu_with_items.remove("option2")
    assert removed is not None
    assert menu_with_items.state_machine.size() == initial_size - 1


def test_remove_returns_removed_element(menu_with_items: Menu) -> None:
    """Test that remove returns the removed element."""
    removed = menu_with_items.remove("option1")
    assert removed is not None
    assert isinstance(removed, TextLabel)
    assert removed.label == "Option 1"


def test_remove_nonexistent_item_returns_none(menu_with_items: Menu) -> None:
    """Test that remove returns None for non-existent item."""
    removed = menu_with_items.remove("nonexistent")
    assert removed is None


# next_item Tests


def test_next_item_increments_position(menu_with_items: Menu) -> None:
    """Test that next_item increments position."""
    initial_position = menu_with_items.position
    menu_with_items.next_item()
    assert menu_with_items.position == initial_position + 1


def test_next_item_wraps_around_when_no_border(screen: Screen) -> None:
    """Test that next_item wraps to beginning when has_border is False."""
    items: List[Dict[str, str]] = [{"a": "A"}, {"b": "B"}]
    menu = Menu(screen, "Menu", items=items, has_border=False)  # type: ignore[arg-type]
    menu.position = 1  # Last item

    menu.next_item()
    assert menu.position == 0


def test_next_item_stops_at_border_when_has_border(screen: Screen) -> None:
    """Test that next_item stops at border when has_border is True."""
    items: List[Dict[str, str]] = [{"a": "A"}, {"b": "B"}]
    menu = Menu(screen, "Menu", items=items, has_border=True)  # type: ignore[arg-type]
    menu.position = 1  # Last item

    border_called = False

    @menu.event  # type: ignore[misc]
    def on_border(m: Menu) -> None:
        nonlocal border_called
        border_called = True

    menu.next_item()
    assert menu.position == 1  # Should stay at last item
    assert border_called is True


def test_next_item_dispatches_on_change_event(menu_with_items: Menu) -> None:
    """Test that next_item dispatches on_change event."""
    change_called = False

    @menu_with_items.event  # type: ignore[misc]
    def on_change(m: Menu) -> None:
        nonlocal change_called
        change_called = True

    menu_with_items.next_item()
    assert change_called is True


def test_next_item_returns_true(menu_with_items: Menu) -> None:
    """Test that next_item returns True."""
    result = menu_with_items.next_item()
    assert result is True


def test_next_item_with_single_item_and_border(screen: Screen) -> None:
    """Test that next_item with single item and border dispatches on_border."""
    items: List[Dict[str, str]] = [{"only": "Only"}]
    menu = Menu(screen, "Menu", items=items, has_border=True)  # type: ignore[arg-type]

    border_called = False

    @menu.event  # type: ignore[misc]
    def on_border(m: Menu) -> None:
        nonlocal border_called
        border_called = True

    menu.next_item()
    assert border_called is True
    assert menu.position == 0  # Should stay at position 0


# previous_item Tests


def test_previous_item_decrements_position(menu_with_items: Menu) -> None:
    """Test that previous_item decrements position."""
    menu_with_items.position = 2
    menu_with_items.previous_item()
    assert menu_with_items.position == 1


def test_previous_item_wraps_around_when_no_border(screen: Screen) -> None:
    """Test that previous_item wraps to end when has_border is False."""
    items: List[Dict[str, str]] = [{"a": "A"}, {"b": "B"}]
    menu = Menu(screen, "Menu", items=items, has_border=False)  # type: ignore[arg-type]
    menu.position = 0  # First item

    menu.previous_item()
    assert menu.position == 1


def test_previous_item_stops_at_border_when_has_border(screen: Screen) -> None:
    """Test that previous_item stops at border when has_border is True."""
    items: List[Dict[str, str]] = [{"a": "A"}, {"b": "B"}]
    menu = Menu(screen, "Menu", items=items, has_border=True)  # type: ignore[arg-type]
    menu.position = 0  # First item

    border_called = False

    @menu.event  # type: ignore[misc]
    def on_border(m: Menu) -> None:
        nonlocal border_called
        border_called = True

    menu.previous_item()
    assert menu.position == 0  # Should stay at first item
    assert border_called is True


def test_previous_item_dispatches_on_change_event(
    menu_with_items: Menu,
) -> None:
    """Test that previous_item dispatches on_change event."""
    menu_with_items.position = 1
    change_called = False

    @menu_with_items.event  # type: ignore[misc]
    def on_change(m: Menu) -> None:
        nonlocal change_called
        change_called = True

    menu_with_items.previous_item()
    assert change_called is True


def test_previous_item_returns_true(menu_with_items: Menu) -> None:
    """Test that previous_item returns True."""
    menu_with_items.position = 1
    result = menu_with_items.previous_item()
    assert result is True


# navigate_to_beginning Tests


def test_navigate_to_beginning_sets_position_to_zero(
    menu_with_items: Menu,
) -> None:
    """Test that navigate_to_beginning sets position to 0."""
    menu_with_items.position = 2
    menu_with_items.navigate_to_beginning()
    assert menu_with_items.position == 0


def test_navigate_to_beginning_dispatches_on_change(
    menu_with_items: Menu,
) -> None:
    """Test that navigate_to_beginning dispatches on_change event."""
    menu_with_items.position = 1
    change_called = False

    @menu_with_items.event  # type: ignore[misc]
    def on_change(m: Menu) -> None:
        nonlocal change_called
        change_called = True

    menu_with_items.navigate_to_beginning()
    assert change_called is True


def test_navigate_to_beginning_does_not_dispatch_when_already_at_start(
    menu_with_items: Menu,
) -> None:
    """Test that navigate_to_beginning doesn't dispatch event when already at start."""
    menu_with_items.position = 0
    change_called = False

    @menu_with_items.event  # type: ignore[misc]
    def on_change(m: Menu) -> None:
        nonlocal change_called
        change_called = True

    menu_with_items.navigate_to_beginning()
    assert change_called is False


def test_navigate_to_beginning_returns_true(menu_with_items: Menu) -> None:
    """Test that navigate_to_beginning returns True."""
    result = menu_with_items.navigate_to_beginning()
    assert result is True


# navigate_to_end Tests


def test_navigate_to_end_sets_position_to_last(
    menu_with_items: Menu,
) -> None:
    """Test that navigate_to_end sets position to last item."""
    menu_with_items.navigate_to_end()
    assert menu_with_items.position == 2  # Last index


def test_navigate_to_end_dispatches_on_change(menu_with_items: Menu) -> None:
    """Test that navigate_to_end dispatches on_change event."""
    change_called = False

    @menu_with_items.event  # type: ignore[misc]
    def on_change(m: Menu) -> None:
        nonlocal change_called
        change_called = True

    menu_with_items.navigate_to_end()
    assert change_called is True


def test_navigate_to_end_does_not_dispatch_when_already_at_end(
    menu_with_items: Menu,
) -> None:
    """Test that navigate_to_end doesn't dispatch event when already at end."""
    menu_with_items.position = 2
    change_called = False

    @menu_with_items.event  # type: ignore[misc]
    def on_change(m: Menu) -> None:
        nonlocal change_called
        change_called = True

    menu_with_items.navigate_to_end()
    assert change_called is False


def test_navigate_to_end_returns_true(menu_with_items: Menu) -> None:
    """Test that navigate_to_end returns True."""
    result = menu_with_items.navigate_to_end()
    assert result is True


# submit Tests


def test_submit_dispatches_on_submit_event(menu_with_items: Menu) -> None:
    """Test that submit dispatches on_submit event."""
    submit_called = False

    @menu_with_items.event  # type: ignore[misc]
    def on_submit(m: Menu) -> None:
        nonlocal submit_called
        submit_called = True

    menu_with_items.submit()
    assert submit_called is True


def test_submit_returns_true(menu_with_items: Menu) -> None:
    """Test that submit returns True."""
    result = menu_with_items.submit()
    assert result is True


def test_submit_event_receives_menu_instance(menu_with_items: Menu) -> None:
    """Test that on_submit event receives menu instance."""
    received_menu = None

    @menu_with_items.event  # type: ignore[misc]
    def on_submit(m: Menu) -> None:
        nonlocal received_menu
        received_menu = m

    menu_with_items.submit()
    assert received_menu == menu_with_items


# navigate_by_first_letter Tests


def test_navigate_by_first_letter_appends_to_typing_buffer(
    menu_with_items: Menu,
) -> None:
    """Test that navigate_by_first_letter appends to typing buffer."""
    menu_with_items.navigate_by_first_letter("O")
    assert menu_with_items.typing_buffer == "O"


def test_navigate_by_first_letter_appends_multiple_characters(
    menu_with_items: Menu,
) -> None:
    """Test that navigate_by_first_letter appends multiple characters."""
    menu_with_items.navigate_by_first_letter("O")
    menu_with_items.navigate_by_first_letter("p")
    assert menu_with_items.typing_buffer == "Op"


def test_navigate_by_first_letter_returns_true(
    menu_with_items: Menu,
) -> None:
    """Test that navigate_by_first_letter returns True."""
    result = menu_with_items.navigate_by_first_letter("A")
    assert result is True


# set_state Tests


def test_set_state_changes_current_state(menu_with_items: Menu) -> None:
    """Test that set_state changes current state."""
    menu_with_items.position = 1
    menu_with_items.set_state()
    assert menu_with_items.state_machine.current_state is not None
    assert menu_with_items.state_machine.current_state.label == "Option 2"  # type: ignore[attr-defined]  # type: ignore[attr-defined]


def test_set_state_with_different_positions(menu_with_items: Menu) -> None:
    """Test that set_state works with different positions."""
    for i in range(3):
        menu_with_items.position = i
        menu_with_items.set_state()
        assert menu_with_items.state_machine.current_state is not None
        assert (
            menu_with_items.state_machine.current_state.label  # type: ignore[attr-defined]
            == f"Option {i + 1}"
        )


# setup Tests


def test_setup_calls_super_setup(
    mocker: MockerFixture, screen: Screen
) -> None:
    """Test that setup calls super().setup()."""
    # Create menu first, then patch to avoid patching during __init__
    items: List[Dict[str, str]] = [{"a": "A"}]
    menu = Menu(screen, "Menu", items=items)  # type: ignore[arg-type]

    mock_super_setup = mocker.patch.object(Element, "setup", return_value=True)

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    menu.setup(mock_change_state)

    # Verify super().setup was called (it will be called multiple times - once for menu, once for each item)
    assert mock_super_setup.called
    # Check that at least one call was with the expected arguments
    assert any(
        call[0][0] == mock_change_state and call[0][1] is True
        for call in mock_super_setup.call_args_list
    )


def test_setup_resets_position_when_reset_position_on_focus_true(
    screen: Screen,
) -> None:
    """Test that setup resets position when reset_position_on_focus is True."""
    items: List[Dict[str, str]] = [{"a": "A"}, {"b": "B"}]
    menu = Menu(  # type: ignore[arg-type]
        screen, "Menu", items=items, position=0, reset_position_on_focus=True  # type: ignore[arg-type]
    )
    menu.position = 1  # Change position

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    menu.setup(mock_change_state)
    assert menu.position == 0  # Should reset to default_position


def test_setup_does_not_reset_position_when_reset_position_on_focus_false(
    screen: Screen,
) -> None:
    """Test that setup doesn't reset position when reset_position_on_focus is False."""
    items: List[Dict[str, str]] = [{"a": "A"}, {"b": "B"}]
    menu = Menu(  # type: ignore[arg-type]
        screen, "Menu", items=items, position=0, reset_position_on_focus=False  # type: ignore[arg-type]
    )
    menu.position = 1  # Change position

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    menu.setup(mock_change_state)
    assert menu.position == 1  # Should not reset


def test_setup_calls_set_state(
    mocker: MockerFixture, menu_with_items: Menu
) -> None:
    """Test that setup calls set_state."""
    mock_set_state = mocker.patch.object(menu_with_items, "set_state")

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    menu_with_items.setup(mock_change_state)
    mock_set_state.assert_called_once_with(interrupt_speech=False)


def test_setup_returns_true(menu_with_items: Menu) -> None:
    """Test that setup returns True."""

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    result = menu_with_items.setup(mock_change_state)
    assert result is True


# update Tests


def test_update_calls_super_update(
    mocker: MockerFixture, menu_with_items: Menu
) -> None:
    """Test that update calls super().update()."""
    mock_super_update = mocker.patch.object(
        Element, "update", return_value=True
    )

    menu_with_items.update(0.016)

    mock_super_update.assert_called_once_with(0.016)


def test_update_calls_state_machine_update(
    mocker: MockerFixture, menu_with_items: Menu
) -> None:
    """Test that update calls state_machine.update()."""
    mock_sm_update = mocker.patch.object(
        menu_with_items.state_machine, "update", return_value=True
    )

    menu_with_items.update(0.016)

    mock_sm_update.assert_called_once_with(0.016)


def test_update_returns_state_machine_update_result(
    menu_with_items: Menu,
) -> None:
    """Test that update returns state_machine.update() result."""
    result = menu_with_items.update(0.016)
    # State machine update should return True for empty state
    assert isinstance(result, bool)


# exit Tests


def test_exit_calls_state_machine_current_state_exit(
    mocker: MockerFixture, menu_with_items: Menu
) -> None:
    """Test that exit calls state_machine.current_state.exit()."""
    mock_state_exit = mocker.patch.object(
        menu_with_items.state_machine.current_state, "exit", return_value=True
    )

    menu_with_items.exit()

    mock_state_exit.assert_called_once()


def test_exit_calls_super_exit(
    mocker: MockerFixture, menu_with_items: Menu
) -> None:
    """Test that exit calls super().exit()."""
    mock_super_exit = mocker.patch.object(Element, "exit", return_value=True)

    menu_with_items.exit()

    mock_super_exit.assert_called_once()


def test_exit_returns_true_when_both_succeed(menu_with_items: Menu) -> None:
    """Test that exit returns True when both exits succeed."""
    result = menu_with_items.exit()
    assert result is True


# reset Tests


def test_reset_resets_position_to_default(menu_with_items: Menu) -> None:
    """Test that reset resets position to default_position."""
    menu_with_items.position = 2
    menu_with_items.reset()
    assert menu_with_items.position == 0


def test_reset_resets_current_state(menu_with_items: Menu) -> None:
    """Test that reset resets current state."""
    menu_with_items.position = 2
    menu_with_items.set_state()
    menu_with_items.reset()
    assert menu_with_items.state_machine.current_state is not None
    assert menu_with_items.state_machine.current_state.label == "Option 1"  # type: ignore[attr-defined]  # type: ignore[attr-defined]


def test_reset_calls_reset_on_all_items(
    mocker: MockerFixture, screen: Screen
) -> None:
    """Test that reset calls reset on all menu items."""
    elem1 = ConcreteElement(screen, "Elem1")
    elem2 = ConcreteElement(screen, "Elem2")
    mock_reset1 = mocker.patch.object(elem1, "reset")
    mock_reset2 = mocker.patch.object(elem2, "reset")

    items: List[Dict[str, Element]] = [{"e1": elem1}, {"e2": elem2}]
    menu = Menu(screen, "Menu", items=items)  # type: ignore[arg-type]  # type: ignore[arg-type]

    menu.reset()

    mock_reset1.assert_called_once()
    mock_reset2.assert_called_once()


def test_reset_with_non_zero_default_position(screen: Screen) -> None:
    """Test that reset works with non-zero default_position."""
    items: List[Dict[str, str]] = [{"a": "A"}, {"b": "B"}, {"c": "C"}]
    menu = Menu(screen, "Menu", items=items, position=1)  # type: ignore[arg-type]
    menu.position = 2

    menu.reset()

    assert menu.position == 1


# active_element Property Tests


def test_active_element_returns_current_state(menu_with_items: Menu) -> None:
    """Test that active_element returns current state."""
    active = menu_with_items.active_element
    assert active is not None
    assert active == menu_with_items.state_machine.current_state


def test_active_element_changes_with_position(menu_with_items: Menu) -> None:
    """Test that active_element changes with position."""
    menu_with_items.position = 0
    menu_with_items.set_state()
    first_active = menu_with_items.active_element

    menu_with_items.position = 1
    menu_with_items.set_state()
    second_active = menu_with_items.active_element

    assert first_active != second_active


def test_active_element_returns_none_for_empty_menu(screen: Screen) -> None:
    """Test that active_element returns None for empty menu."""
    menu = Menu(screen, "Empty Menu")
    assert menu.active_element is None


# Event Registration Tests


def test_on_change_event_is_registered() -> None:
    """Test that on_change event is registered on Menu class."""
    assert "on_change" in Menu.event_types


def test_on_border_event_is_registered() -> None:
    """Test that on_border event is registered on Menu class."""
    assert "on_border" in Menu.event_types


def test_on_submit_event_is_registered() -> None:
    """Test that on_submit event is registered on Menu class."""
    assert "on_submit" in Menu.event_types


def test_on_letter_navigation_fail_event_is_registered() -> None:
    """Test that on_letter_navigation_fail event is registered on Menu class."""
    assert "on_letter_navigation_fail" in Menu.event_types


def test_menu_has_inherited_events() -> None:
    """Test that Menu has inherited events from Element."""
    assert "on_focus" in Menu.event_types
    assert "on_lose_focus" in Menu.event_types
    assert "on_update" in Menu.event_types


# Inheritance Tests


def test_menu_inherits_from_element(menu: Menu) -> None:
    """Test that Menu inherits from Element."""
    assert isinstance(menu, Element)


def test_menu_generic_type_is_str(screen: Screen) -> None:
    """Test that Menu uses str as generic type."""
    items: List[Dict[str, str]] = [{"test": "Test"}]
    menu = Menu(screen, "Menu", items=items)  # type: ignore[arg-type]
    assert isinstance(menu.value, str)


def test_menu_has_element_methods(menu: Menu) -> None:
    """Test that Menu has Element methods."""
    assert hasattr(menu, "setup")
    assert hasattr(menu, "update")
    assert hasattr(menu, "exit")
    assert callable(menu.setup)
    assert callable(menu.update)
    assert callable(menu.exit)


def test_menu_has_get_window_method(menu: Menu) -> None:
    """Test that Menu has get_window method."""
    assert hasattr(menu, "get_window")
    assert callable(menu.get_window)


# Integration Tests


def test_menu_lifecycle(
    mocker: MockerFixture, window: Window, screen: Screen
) -> None:
    """Test complete menu lifecycle."""
    items: List[Dict[str, str]] = [{"a": "A"}, {"b": "B"}]
    menu = Menu(screen, "Menu", items=items)  # type: ignore[arg-type]

    mock_push = mocker.patch.object(window, "push_window_handlers")
    mock_pop = mocker.patch.object(window, "pop_window_handlers")

    def mock_change_state(key: str, *args: Any) -> None:
        pass

    # Setup
    result = menu.setup(mock_change_state)
    assert result is True
    mock_push.assert_called_once_with(menu.key_handler)

    # Update
    result = menu.update(0.016)
    assert isinstance(result, bool)

    # Navigate
    result = menu.next_item()
    assert result is True
    assert menu.position == 1

    # Submit
    result = menu.submit()
    assert result is True

    # Reset
    menu.reset()
    assert menu.position == 0

    # Exit
    result = menu.exit()
    assert result is True
    mock_pop.assert_called_once()


def test_menu_navigation_sequence(menu_with_items: Menu) -> None:
    """Test a sequence of navigation actions."""
    # Start at position 0
    assert menu_with_items.position == 0

    # Move to next item
    menu_with_items.next_item()
    assert menu_with_items.position == 1

    # Move to next item again
    menu_with_items.next_item()
    assert menu_with_items.position == 2

    # Move to previous item
    menu_with_items.previous_item()
    assert menu_with_items.position == 1

    # Navigate to beginning
    menu_with_items.navigate_to_beginning()
    assert menu_with_items.position == 0

    # Navigate to end
    menu_with_items.navigate_to_end()
    assert menu_with_items.position == 2


def test_menu_multiple_event_listeners(menu_with_items: Menu) -> None:
    """Test that multiple event listeners work correctly."""
    change_count = 0
    submit_count = 0
    border_count = 0

    @menu_with_items.event  # type: ignore[misc]
    def on_change(m: Menu) -> None:
        nonlocal change_count
        change_count += 1

    @menu_with_items.event  # type: ignore[misc]
    def on_submit(m: Menu) -> None:
        nonlocal submit_count
        submit_count += 1

    @menu_with_items.event  # type: ignore[misc]
    def on_border(m: Menu) -> None:
        nonlocal border_count
        border_count += 1

    # Trigger on_change
    menu_with_items.next_item()
    assert change_count == 1

    # Trigger on_submit
    menu_with_items.submit()
    assert submit_count == 1

    # Change menu to have border and trigger on_border
    menu_with_items.has_border = True
    menu_with_items.position = 2
    menu_with_items.next_item()
    assert border_count == 1


def test_menu_key_press_simulation(screen: Screen) -> None:
    """Test simulating key presses on menu."""
    items: List[Dict[str, str]] = [{"a": "A"}, {"b": "B"}]
    menu = Menu(screen, "Menu", items=items)  # type: ignore[arg-type]

    # Simulate DOWN key press
    for k, (callback, _) in menu.key_handler.registered_key_presses.items():
        if k.symbol == key.DOWN and k.modifiers == 0:
            callback.call()
            break

    assert menu.position == 1

    # Simulate HOME key press
    for k, (callback, _) in menu.key_handler.registered_key_presses.items():
        if k.symbol == key.HOME and k.modifiers == 0:
            callback.call()
            break

    assert menu.position == 0


def test_menu_dynamic_item_management(screen: Screen) -> None:
    """Test dynamically adding and removing items."""
    menu = Menu(screen, "Menu")

    # Add items
    menu.add("item1", "Item 1")
    menu.add("item2", "Item 2")
    assert menu.state_machine.size() == 2

    # Remove item
    removed = menu.remove("item1")
    assert removed is not None
    assert menu.state_machine.size() == 1

    # Add more items
    menu.add("item3", "Item 3")
    menu.add("item4", "Item 4")
    assert menu.state_machine.size() == 3


def test_menu_with_mixed_item_types(screen: Screen) -> None:
    """Test menu with both string and Element items."""
    elem = ConcreteElement(screen, "Custom Element")
    items: List[Dict[str, Any]] = [
        {"str1": "String Item"},
        {"elem1": elem},
        {"str2": "Another String"},
    ]
    menu = Menu(screen, "Menu", items=items)

    assert menu.state_machine.size() == 3
    assert isinstance(menu.state_machine.states["str1"], TextLabel)
    assert menu.state_machine.states["elem1"] == elem
    assert isinstance(menu.state_machine.states["str2"], TextLabel)


def test_menu_wrapping_behavior_without_border(screen: Screen) -> None:
    """Test menu wrapping behavior when has_border is False."""
    items: List[Dict[str, str]] = [{"a": "A"}, {"b": "B"}, {"c": "C"}]
    menu = Menu(screen, "Menu", items=items, has_border=False)  # type: ignore[arg-type]

    # Start at position 0
    menu.position = 0

    # Move backwards should wrap to end
    menu.previous_item()
    assert menu.position == 2

    # Move forward should wrap to beginning
    menu.next_item()
    assert menu.position == 0


def test_menu_side_menu_navigation(screen: Screen) -> None:
    """Test navigation keys for side menu."""
    items: List[Dict[str, str]] = [{"a": "A"}, {"b": "B"}]
    menu = Menu(screen, "Menu", items=items, is_side_menu=True)  # type: ignore[arg-type]

    # RIGHT should move to next
    for k, (callback, _) in menu.key_handler.registered_key_presses.items():
        if k.symbol == key.RIGHT and k.modifiers == 0:
            callback.call()
            break

    assert menu.position == 1

    # LEFT should move to previous
    for k, (callback, _) in menu.key_handler.registered_key_presses.items():
        if k.symbol == key.LEFT and k.modifiers == 0:
            callback.call()
            break

    assert menu.position == 0


def test_menu_position_preserved_across_setup_when_disabled(
    screen: Screen,
) -> None:
    """Test that position is preserved across setup when reset_position_on_focus is False."""
    items: List[Dict[str, str]] = [{"a": "A"}, {"b": "B"}, {"c": "C"}]
    menu = Menu(
        screen, "Menu", items=items, position=0, reset_position_on_focus=False  # type: ignore[arg-type]
    )

    # Change position
    menu.position = 2

    # Setup should not reset position
    def mock_change_state(key: str, *args: Any) -> None:
        pass

    menu.setup(mock_change_state)
    assert menu.position == 2


def test_menu_value_as_state_key(menu_with_items: Menu) -> None:
    """Test that value property correctly maps to state keys."""
    # Position 0 should have value "option1"
    menu_with_items.position = 0
    assert menu_with_items.value == "option1"

    # Position 1 should have value "option2"
    menu_with_items.position = 1
    assert menu_with_items.value == "option2"

    # Position 2 should have value "option3"
    menu_with_items.position = 2
    assert menu_with_items.value == "option3"


# _navigate_item with has_border=True, valid navigation (lines 133-135)


def test_navigate_item_border_menu_valid_next(screen: Screen) -> None:
    """Test _navigate_item with has_border=True moves to valid next position."""
    items: List[Dict[str, str]] = [{"a": "A"}, {"b": "B"}, {"c": "C"}]
    menu = Menu(screen, "Menu", items=items, has_border=True)  # type: ignore[arg-type]
    menu.position = 0  # Not at border

    change_called = False

    @menu.event  # type: ignore[misc]
    def on_change(m: Menu) -> None:
        nonlocal change_called
        change_called = True

    result = menu.next_item()
    assert result is True
    assert menu.position == 1
    assert change_called is True


def test_navigate_item_border_menu_valid_previous(screen: Screen) -> None:
    """Test _navigate_item with has_border=True moves to valid previous position."""
    items: List[Dict[str, str]] = [{"a": "A"}, {"b": "B"}, {"c": "C"}]
    menu = Menu(screen, "Menu", items=items, has_border=True)  # type: ignore[arg-type]
    menu.position = 2  # Not at first

    result = menu.previous_item()
    assert result is True
    assert menu.position == 1


# _navigate_by_text Tests (lines 174-184)


def test_navigate_by_text_success(menu_with_items: Menu) -> None:
    """Test _navigate_by_text navigates to matching item."""
    menu_with_items.position = 2  # Start at last item
    menu_with_items.typing_buffer = "Option 2"

    change_called = False

    @menu_with_items.event  # type: ignore[misc]
    def on_change(m: Menu) -> None:
        nonlocal change_called
        change_called = True

    menu_with_items._navigate_by_text(0.0)

    assert menu_with_items.position == 1  # "Option 2" is at index 1
    assert menu_with_items.typing_buffer == ""
    assert change_called is True


def test_navigate_by_text_failure(menu_with_items: Menu) -> None:
    """Test _navigate_by_text dispatches on_letter_navigation_fail when no match."""
    menu_with_items.typing_buffer = "XYZ"  # No item starts with "XYZ"

    fail_called = False

    @menu_with_items.event  # type: ignore[misc]
    def on_letter_navigation_fail(m: Menu) -> None:
        nonlocal fail_called
        fail_called = True

    menu_with_items._navigate_by_text(0.0)

    assert fail_called is True


# value.setter loop completion without break (branch 85->90)


def test_value_setter_loop_completes_without_match(screen: Screen) -> None:
    """Test value setter when key is not found - loop exhausts without break."""
    items: List[Dict[str, str]] = [{"a": "A"}, {"b": "B"}]
    menu = Menu(screen, "Menu", items=items)  # type: ignore[arg-type]
    # When value is not found, loop completes without break (index stays at len)
    # state_machine.change() will raise since "c" is not a valid key
    with pytest.raises(Exception):
        menu.value = "c"  # Not in menu
