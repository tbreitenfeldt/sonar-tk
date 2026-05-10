from typing import Optional

import pytest

from sonartk.ui.ui_component import UIComponent
from sonartk.ui.window import Window


class ConcreteUIComponent(UIComponent):
    """Concrete implementation of UIComponent for testing."""

    def __init__(self, parent: Optional[UIComponent] = None) -> None:
        self.parent = parent


class NestedUIComponent(UIComponent):
    """Another concrete implementation for testing nested hierarchies."""

    def __init__(self, parent: Optional[UIComponent] = None) -> None:
        self.parent = parent


@pytest.fixture
def window() -> Window:
    """Returns a Window instance for testing."""
    return Window()


@pytest.fixture
def component_with_no_parent() -> ConcreteUIComponent:
    """Returns a UIComponent with no parent."""
    return ConcreteUIComponent(parent=None)


@pytest.fixture
def component_with_window_parent(window: Window) -> ConcreteUIComponent:
    """Returns a UIComponent with a Window as parent."""
    return ConcreteUIComponent(parent=window)


def test_ui_component_has_parent_attribute() -> None:
    """Test that UIComponent has a parent attribute."""
    component = ConcreteUIComponent()
    assert hasattr(component, "parent")


def test_ui_component_parent_is_none_by_default() -> None:
    """Test that parent is None when not provided."""
    component = ConcreteUIComponent()
    assert component.parent is None


def test_ui_component_parent_can_be_set() -> None:
    """Test that parent can be set during initialization."""
    window = Window()
    component = ConcreteUIComponent(parent=window)
    assert component.parent is window


def test_ui_component_parent_can_be_another_component() -> None:
    """Test that parent can be another UIComponent."""
    parent_component = ConcreteUIComponent()
    child_component = ConcreteUIComponent(parent=parent_component)
    assert child_component.parent is parent_component


def test_get_window_with_direct_window_parent(
    component_with_window_parent: ConcreteUIComponent, window: Window
) -> None:
    """Test get_window when parent is directly a Window."""
    result = component_with_window_parent.get_window()
    assert result is window


def test_get_window_with_nested_hierarchy() -> None:
    """Test get_window with multiple levels of nesting."""
    window = Window()
    level1 = ConcreteUIComponent(parent=window)
    level2 = NestedUIComponent(parent=level1)
    level3 = ConcreteUIComponent(parent=level2)

    assert level3.get_window() is window
    assert level2.get_window() is window
    assert level1.get_window() is window


def test_get_window_with_deeply_nested_hierarchy() -> None:
    """Test get_window with deep nesting (5 levels)."""
    window = Window()
    level1 = ConcreteUIComponent(parent=window)
    level2 = NestedUIComponent(parent=level1)
    level3 = ConcreteUIComponent(parent=level2)
    level4 = NestedUIComponent(parent=level3)
    level5 = ConcreteUIComponent(parent=level4)

    assert level5.get_window() is window


def test_get_window_raises_runtime_error_when_no_parent(
    component_with_no_parent: ConcreteUIComponent,
) -> None:
    """Test that get_window raises RuntimeError when parent is None."""
    with pytest.raises(RuntimeError) as exc_info:
        component_with_no_parent.get_window()

    assert "has no Window in parent chain" in str(exc_info.value)
    assert "ConcreteUIComponent" in str(exc_info.value)


def test_get_window_raises_runtime_error_with_non_window_parent_chain() -> (
    None
):
    """Test that get_window raises RuntimeError when no Window in chain."""
    parent = ConcreteUIComponent(parent=None)
    child = ConcreteUIComponent(parent=parent)

    with pytest.raises(RuntimeError) as exc_info:
        child.get_window()

    assert "has no Window in parent chain" in str(exc_info.value)


def test_get_window_raises_runtime_error_with_long_non_window_chain() -> None:
    """Test RuntimeError with long chain that never reaches a Window."""
    level1 = ConcreteUIComponent(parent=None)
    level2 = NestedUIComponent(parent=level1)
    level3 = ConcreteUIComponent(parent=level2)
    level4 = NestedUIComponent(parent=level3)

    with pytest.raises(RuntimeError) as exc_info:
        level4.get_window()

    assert "has no Window in parent chain" in str(exc_info.value)


def test_window_get_window_returns_self() -> None:
    """Test that Window.get_window() returns itself."""
    window = Window()
    assert window.get_window() is window


def test_multiple_components_share_same_window() -> None:
    """Test that multiple components can share the same parent Window."""
    window = Window()
    component1 = ConcreteUIComponent(parent=window)
    component2 = ConcreteUIComponent(parent=window)
    component3 = NestedUIComponent(parent=window)

    assert component1.get_window() is window
    assert component2.get_window() is window
    assert component3.get_window() is window


def test_get_window_with_mixed_hierarchy() -> None:
    """Test get_window with mixed component types in hierarchy."""
    window = Window()
    concrete1 = ConcreteUIComponent(parent=window)
    nested1 = NestedUIComponent(parent=concrete1)
    concrete2 = ConcreteUIComponent(parent=nested1)
    nested2 = NestedUIComponent(parent=concrete2)

    assert nested2.get_window() is window
    assert concrete2.get_window() is window
    assert nested1.get_window() is window
    assert concrete1.get_window() is window


def test_get_window_traversal_stops_at_first_window() -> None:
    """Test that get_window stops at first Window found in chain."""
    parent_window = Window()
    child_window = Window(parent=parent_window)
    component = ConcreteUIComponent(parent=child_window)

    # Should return child_window, not parent_window
    assert component.get_window() is child_window


def test_ui_component_is_abstract_base_class() -> None:
    """Test that UIComponent is an ABC."""
    from abc import ABC

    assert issubclass(UIComponent, ABC)


def test_parent_attribute_type_annotation() -> None:
    """Test that parent attribute has correct type annotation."""
    component = ConcreteUIComponent()
    # Verify parent can be None
    component.parent = None
    assert component.parent is None

    # Verify parent can be a UIComponent
    parent = ConcreteUIComponent()
    component.parent = parent
    assert component.parent is parent


def test_error_message_contains_class_name() -> None:
    """Test that RuntimeError contains the correct class name."""
    component = NestedUIComponent(parent=None)

    with pytest.raises(RuntimeError) as exc_info:
        component.get_window()

    assert "NestedUIComponent" in str(exc_info.value)


def test_get_window_with_parent_chain_terminating_at_none() -> None:
    """Test get_window when parent chain terminates at None (no Window)."""
    level1 = ConcreteUIComponent(parent=None)
    level2 = ConcreteUIComponent(parent=level1)
    level3 = ConcreteUIComponent(parent=level2)

    with pytest.raises(RuntimeError):
        level3.get_window()


def test_parent_can_be_reassigned() -> None:
    """Test that parent can be reassigned after initialization."""
    window1 = Window()
    window2 = Window()
    component = ConcreteUIComponent(parent=window1)

    assert component.get_window() is window1

    # Reassign parent
    component.parent = window2
    assert component.get_window() is window2


def test_get_window_after_parent_set_to_none() -> None:
    """Test that get_window raises error after parent is set to None."""
    window = Window()
    component = ConcreteUIComponent(parent=window)

    # Verify it works initially
    assert component.get_window() is window

    # Set parent to None
    component.parent = None

    # Should now raise error
    with pytest.raises(RuntimeError):
        component.get_window()


def test_component_with_window_grandparent() -> None:
    """Test component with Window as grandparent."""
    window = Window()
    parent = ConcreteUIComponent(parent=window)
    child = ConcreteUIComponent(parent=parent)

    assert child.get_window() is window


def test_isinstance_check_in_get_window() -> None:
    """Test that get_window correctly identifies Window instances."""
    window = Window()
    component1 = ConcreteUIComponent(parent=window)
    component2 = ConcreteUIComponent(parent=component1)

    # Both should find the window through isinstance check
    assert component1.get_window() is window
    assert component2.get_window() is window


def test_get_window_import_from_sonartk_ui_window() -> None:
    """Test that get_window correctly imports Window from sonartk.ui.window."""
    # This tests the local import in get_window method
    window = Window()
    component = ConcreteUIComponent(parent=window)

    # Should successfully import and use Window
    result = component.get_window()
    assert isinstance(result, Window)


def test_multiple_calls_to_get_window_return_same_instance() -> None:
    """Test that multiple calls to get_window return the same Window."""
    window = Window()
    component = ConcreteUIComponent(parent=window)

    result1 = component.get_window()
    result2 = component.get_window()
    result3 = component.get_window()

    assert result1 is result2
    assert result2 is result3
    assert result1 is window
