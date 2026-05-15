"""Unit tests for the FocusableContainer protocol."""

from typing import Any, Callable, Optional

import pytest
from pytest_mock import MockerFixture

from sonartk.ui.focusable_container import FocusableContainer
from sonartk.ui.screen.container_screen import ContainerScreen
from sonartk.ui.screen.screen import Screen
from sonartk.ui.window import Window
from sonartk.util.state import State
from test.mocks.mock_state import MockState
from test.mocks.mock_pyglet_window import MockPygletWindow

# Test implementations of FocusableContainer


class ConcreteContainer:
    """Concrete implementation of FocusableContainer protocol for testing."""

    def __init__(self, active: Optional[State] = None) -> None:
        self._active = active

    @property
    def active_element(self) -> Optional[State]:
        return self._active


class NestedContainer:
    """Container that contains another container."""

    def __init__(
        self, inner_container: Optional[FocusableContainer] = None
    ) -> None:
        self._inner = inner_container

    @property
    def active_element(self) -> Optional[State]:
        if self._inner is not None:
            return self._inner.active_element
        return None


@pytest.fixture
def window(mocker: MockerFixture) -> Window:
    """Create a Window fixture."""
    window = Window()
    window.pyglet_window = mocker.MagicMock(spec=MockPygletWindow)
    window.push_window_handlers = mocker.MagicMock()  # type: ignore[method-assign]
    window.pop_window_handlers = mocker.MagicMock()  # type: ignore[method-assign]
    return window


@pytest.fixture
def test_screen(window: Window) -> Screen:
    """Create a minimal Screen for testing."""

    class TestScreen(Screen):
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

    return TestScreen(parent=window)


@pytest.fixture
def container_screen(window: Window) -> ContainerScreen:
    """Create a ContainerScreen fixture."""
    return ContainerScreen(parent=window)


# Protocol Compliance Tests


def test_concrete_container_implements_focusable_container() -> None:
    """Test that ConcreteContainer implements FocusableContainer protocol."""
    state = MockState()
    container = ConcreteContainer(active=state)

    # Check that container has the required property
    assert hasattr(container, "active_element")
    assert container.active_element is state


def test_concrete_container_with_none_active_element() -> None:
    """Test that ConcreteContainer can have None as active_element."""
    container = ConcreteContainer(active=None)
    assert container.active_element is None


def test_nested_container_implements_focusable_container() -> None:
    """Test that NestedContainer implements FocusableContainer protocol."""
    state = MockState()
    inner = ConcreteContainer(active=state)
    outer = NestedContainer(inner_container=inner)

    assert hasattr(outer, "active_element")
    assert outer.active_element is state


def test_nested_container_with_none_inner() -> None:
    """Test that NestedContainer returns None when inner is None."""
    outer = NestedContainer(inner_container=None)
    assert outer.active_element is None


# Screen Implementation Tests


def test_screen_implements_focusable_container_protocol(
    test_screen: Screen,
) -> None:
    """Test that Screen implements FocusableContainer protocol."""
    assert hasattr(test_screen, "active_element")


def test_screen_active_element_returns_current_state(
    test_screen: Screen,
) -> None:
    """Test that Screen's active_element returns the current state."""
    state = MockState()
    test_screen.state_machine.add("test_state", state)
    test_screen.state_machine.change("test_state")

    assert test_screen.active_element == state


def test_screen_active_element_changes_with_state_change(
    test_screen: Screen,
) -> None:
    """Test that Screen's active_element changes when state changes."""
    state1 = MockState()
    state2 = MockState()

    test_screen.state_machine.add("state1", state1)
    test_screen.state_machine.add("state2", state2)

    test_screen.state_machine.change("state1")
    assert test_screen.active_element == state1

    test_screen.state_machine.change("state2")
    assert test_screen.active_element == state2


# ContainerScreen Implementation Tests


def test_container_screen_implements_focusable_container_protocol(
    container_screen: ContainerScreen,
) -> None:
    """Test that ContainerScreen implements FocusableContainer protocol."""
    assert hasattr(container_screen, "active_element")


def test_container_screen_active_element_returns_current_state(
    container_screen: ContainerScreen,
) -> None:
    """Test that ContainerScreen's active_element returns the current state."""
    state = MockState()
    container_screen.state_machine.add("test_state", state)
    container_screen.state_machine.change("test_state")

    assert container_screen.active_element == state


# Protocol Behavior Tests


def test_focusable_container_protocol_allows_duck_typing() -> None:
    """Test that FocusableContainer protocol allows duck typing."""

    class DuckTypedContainer:
        """A class that doesn't explicitly declare FocusableContainer but implements it."""

        def __init__(self) -> None:
            self._element: Optional[State] = None

        @property
        def active_element(self) -> Optional[State]:
            return self._element

    # Should work with duck typing
    container = DuckTypedContainer()
    state = MockState()
    container._element = state

    assert container.active_element is state


def test_protocol_contract_with_generic_function() -> None:
    """Test using FocusableContainer with a generic function."""

    def get_active_element(
        container: FocusableContainer,
    ) -> Optional[State]:
        """Function that uses FocusableContainer protocol."""
        return container.active_element

    state = MockState()
    container = ConcreteContainer(active=state)

    assert get_active_element(container) is state


def test_protocol_contract_with_nested_containers() -> None:
    """Test that protocol works with nested FocusableContainers."""

    def traverse_containers(
        container: FocusableContainer,
    ) -> Optional[State]:
        """Traverse nested containers to find the deepest active element."""
        element = container.active_element

        # Check if element is itself a focusable container
        if element is not None and hasattr(element, "active_element"):
            return traverse_containers(element)  # type: ignore[arg-type]

        return element

    # Create nested structure
    inner_state = MockState()
    inner_container = ConcreteContainer(active=inner_state)
    outer_container = NestedContainer(inner_container=inner_container)

    assert traverse_containers(outer_container) is inner_state


# Property Access Tests


def test_active_element_property_is_readable(
    test_screen: Screen,
) -> None:
    """Test that active_element property can be read."""
    state = MockState()
    test_screen.state_machine.add("test_state", state)
    test_screen.state_machine.change("test_state")

    # Should not raise
    _ = test_screen.active_element


def test_active_element_property_returns_state_or_none(
    test_screen: Screen,
) -> None:
    """Test that active_element returns State or None."""
    result = test_screen.active_element
    assert result is None or isinstance(result, State)


def test_protocol_with_optional_type_annotation() -> None:
    """Test that FocusableContainer works with Optional type annotation."""

    def process_container(
        container: Optional[FocusableContainer],
    ) -> Optional[State]:
        if container is None:
            return None
        return container.active_element

    container = ConcreteContainer(active=None)
    assert process_container(container) is None


def test_multiple_containers_maintain_separate_state() -> None:
    """Test that multiple containers maintain separate active elements."""
    state1 = MockState()
    state2 = MockState()

    container1 = ConcreteContainer(active=state1)
    container2 = ConcreteContainer(active=state2)

    assert container1.active_element is state1
    assert container2.active_element is state2
    assert container1.active_element is not container2.active_element


def test_container_active_element_can_be_updated(
    test_screen: Screen,
) -> None:
    """Test that container's active element changes when state changes."""
    state1 = MockState()
    state2 = MockState()

    test_screen.state_machine.add("state1", state1)
    test_screen.state_machine.add("state2", state2)
    test_screen.state_machine.change("state1")

    original_element = test_screen.active_element
    test_screen.state_machine.change("state2")
    new_element = test_screen.active_element

    assert original_element != new_element


# Integration Tests


def test_container_screen_is_focusable_container(
    container_screen: ContainerScreen,
) -> None:
    """Test that ContainerScreen can be used as FocusableContainer."""
    state = MockState()
    container_screen.state_machine.add("test_state", state)
    container_screen.state_machine.change("test_state")

    # Use as FocusableContainer
    def use_as_focusable(c: FocusableContainer) -> Optional[State]:
        return c.active_element

    result = use_as_focusable(container_screen)
    assert result is state


def test_protocol_with_isinstance_check() -> None:
    """Test behavior with runtime type checking."""

    class TypeCheckContainer:
        def __init__(self, element: Optional[State] = None) -> None:
            self._element = element

        @property
        def active_element(self) -> Optional[State]:
            return self._element

    container = TypeCheckContainer()
    state = MockState()
    container._element = state

    # Protocol uses structural subtyping, not nominal
    # So isinstance won't work with Protocol, but the interface does
    assert hasattr(container, "active_element")
    assert container.active_element is state


def test_deeply_nested_containers(test_screen: Screen) -> None:
    """Test deeply nested container structure."""

    def get_leaf_element(
        container: FocusableContainer, depth: int = 0
    ) -> Optional[State]:
        """Recursively get the deepest active element."""
        element = container.active_element

        if (
            element is not None
            and hasattr(element, "active_element")
            and depth < 10
        ):
            return get_leaf_element(element, depth + 1)  # type: ignore[arg-type]

        return element

    state1 = MockState()

    # Setup: inner state, outer container
    inner_container = ConcreteContainer(active=state1)
    outer_container = NestedContainer(inner_container=inner_container)

    assert get_leaf_element(outer_container) is state1


# Type Compatibility Tests


def test_focusable_container_protocol_in_list(
    test_screen: Screen, container_screen: ContainerScreen
) -> None:
    """Test that FocusableContainers can be used in collections."""
    containers: list[FocusableContainer] = [test_screen, container_screen]

    assert len(containers) == 2


def test_focusable_container_protocol_in_dict(
    test_screen: Screen, container_screen: ContainerScreen
) -> None:
    """Test that FocusableContainers can be used as dict values."""
    state = MockState()
    test_screen.state_machine.add("test_state", state)
    test_screen.state_machine.change("test_state")

    containers: dict[str, FocusableContainer] = {
        "screen": test_screen,
        "container": container_screen,
    }

    assert containers["screen"].active_element is state
