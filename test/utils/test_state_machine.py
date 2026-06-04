from typing import Any, Callable

import pytest

from sonartk.util.state_machine import StateMachine, EmptyState
from sonartk.util.state import State
from test.mocks.mock_state import MockState


@pytest.fixture
def state_machine() -> StateMachine:
    """Returns an empty StateMachine instance"""
    return StateMachine()


def test_default_state(state_machine: StateMachine) -> None:
    assert isinstance(state_machine.current_state, State)
    assert isinstance(state_machine.current_state, EmptyState)


def test_valid_value_for_add(state_machine: StateMachine) -> None:
    key: str = "test"
    test_state: MockState = MockState()
    state_machine.add(key, test_state)
    assert state_machine.states[key] == test_state
    assert state_machine.states[key].state_key == key


def test_none_state_for_add(state_machine: StateMachine) -> None:
    with pytest.raises(ValueError):
        key: str = "test"
        test_state: MockState | None = None
        state_machine.add(key, test_state)  # type: ignore


def test_none_key_for_add(state_machine: StateMachine) -> None:
    with pytest.raises(ValueError):
        key: str | None = None
        test_state: MockState = MockState()
        state_machine.add(key, test_state)  # type: ignore


def test_valid_value_for_remove(state_machine: StateMachine) -> None:
    key: str = "test"
    test_state: MockState = MockState()
    state_machine.add(key, test_state)
    assert state_machine.remove(key) == test_state
    assert len(state_machine.states) == 0


def test_invalid_value_for_remove(state_machine: StateMachine) -> None:
    key: str = "test"
    test_state: MockState = MockState()
    state_machine.states[key] = test_state

    assert state_machine.remove("abcdefg") is None
    assert len(state_machine.states) == 1


def test_clear(state_machine: StateMachine) -> None:
    state_machine.states["test1"] = MockState()
    state_machine.states["test2"] = MockState()
    state_machine.states["test3"] = MockState()
    state_machine.clear()
    assert len(state_machine.states) == 0


def test_size(state_machine: StateMachine) -> None:
    state_machine.states["test1"] = MockState()
    state_machine.states["test2"] = MockState()
    state_machine.states["test3"] = MockState()
    assert state_machine.size() == 3


def test_is_empty(state_machine: StateMachine) -> None:
    """Test that is_empty correctly identifies when the state machine has no states"""
    assert state_machine.is_empty() is True
    state_machine.add("test1", MockState())
    assert state_machine.is_empty() is False
    state_machine.clear()
    assert state_machine.is_empty() is True


def test_valid_change(state_machine: StateMachine) -> None:
    test_state1: MockState = MockState()
    state_machine.states["test1"] = test_state1
    state_machine.transition_to("test1")
    assert state_machine.current_state == test_state1


def test_invalid_change(state_machine: StateMachine) -> None:
    with pytest.raises(KeyError):
        state_machine.transition_to("abcdefg")


def test_exit_block_change(state_machine: StateMachine) -> None:
    test_state1: MockState = MockState(exit_value=False)
    test_state2: MockState = MockState()
    state_machine.states["test1"] = test_state1
    state_machine.states["test2"] = test_state2
    state_machine.current_state = test_state1
    state_machine.transition_to("test2")
    assert state_machine.current_state == test_state1


def test_setup_block_change(state_machine: StateMachine) -> None:
    test_state1: MockState = MockState()
    test_state2: MockState = MockState(setup_value=False)
    state_machine.states["test1"] = test_state1
    state_machine.states["test2"] = test_state2
    state_machine.current_state = test_state1
    state_machine.transition_to("test2")
    assert state_machine.current_state == test_state1


def test_successful_setup(state_machine: StateMachine) -> None:
    mock_state: MockState = MockState(setup_value=True)
    state_machine.states["test"] = mock_state
    state_machine.current_state = mock_state
    assert state_machine.setup(state_machine.transition_to) is True


def test_activate_current_state_forwards_args_and_kwargs(
    state_machine: StateMachine,
) -> None:
    captured: dict[str, object] = {}

    class RecordingState(MockState):
        def setup(  # type: ignore[override]
            self,
            change_state: Callable[[str, Any], None],
            *args: Any,
            **kwargs: Any,
        ) -> bool:
            captured["args"] = args
            captured["kwargs"] = kwargs
            return super().setup(change_state, *args, **kwargs)

    state_machine.add("test", RecordingState())

    state_machine.activate_current_state(
        "alpha",
        "beta",
        interrupt_speech=False,
        completion_poll_interval_seconds=0.25,
    )

    assert captured["args"] == ("alpha", "beta")
    assert captured["kwargs"] == {
        "interrupt_speech": False,
        "completion_poll_interval_seconds": 0.25,
    }


def test_block_setup(state_machine: StateMachine) -> None:
    mock_state: MockState = MockState(setup_value=False)
    state_machine.states["test"] = mock_state
    state_machine.current_state = mock_state
    assert state_machine.setup() is False


def test_successful_exit(state_machine: StateMachine) -> None:
    mock_state: MockState = MockState(exit_value=True)
    state_machine.states["test"] = mock_state
    state_machine.current_state = mock_state
    assert state_machine.exit() is True


def test_block_exit(state_machine: StateMachine) -> None:
    mock_state: MockState = MockState(exit_value=False)
    state_machine.states["test"] = mock_state
    state_machine.current_state = mock_state
    assert state_machine.exit() is False


def test_successful_update(state_machine: StateMachine) -> None:
    mock_state: MockState = MockState(update_value=True)
    state_machine.states["test"] = mock_state
    state_machine.current_state = mock_state
    assert state_machine.update(0.0) is True


def test_block_update(state_machine: StateMachine) -> None:
    mock_state: MockState = MockState(update_value=False)
    state_machine.states["test"] = mock_state
    state_machine.current_state = mock_state
    assert state_machine.update(0.0) is False


def test_empty_state_setup(state_machine: StateMachine) -> None:
    empty_state: EmptyState = EmptyState()
    assert empty_state.setup(state_machine.transition_to) is True


def test_empty_state_update() -> None:
    empty_state: EmptyState = EmptyState()
    assert empty_state.update(0.0) is True


def test_empty_state_exit() -> None:
    empty_state: EmptyState = EmptyState()
    assert empty_state.exit() is True


def test_add_duplicate_key_raises_error() -> None:
    """Test that adding a state with duplicate key raises ValueError"""
    machine: StateMachine = StateMachine()
    test_state1: MockState = MockState()
    test_state2: MockState = MockState()

    machine.add("test", test_state1)

    with pytest.raises(ValueError, match="already exists"):
        machine.add("test", test_state2)


def test_contains_key_exists() -> None:
    """Test contains method returns True for existing key"""
    machine: StateMachine = StateMachine()
    test_state: MockState = MockState()
    machine.add("test", test_state)

    assert machine.contains("test")


def test_contains_key_not_exists() -> None:
    """Test contains method returns False for non-existing key"""
    machine: StateMachine = StateMachine()

    assert not machine.contains("nonexistent")


def test_change_to_nonexistent_state() -> None:
    """Test that changing to non-existent state raises KeyError"""
    machine: StateMachine = StateMachine()
    test_state: MockState = MockState()
    machine.add("test", test_state)

    with pytest.raises(KeyError, match="not in state machine"):
        machine.transition_to("nonexistent")


def test_change_to_nonexistent_state_error_message() -> None:
    """Test that the KeyError message includes available states"""
    machine: StateMachine = StateMachine()
    machine.add("state1", MockState())
    machine.add("state2", MockState())

    try:
        machine.transition_to("invalid")
        assert False, "Should have raised KeyError"
    except KeyError as e:
        error_msg = str(e)
        assert "invalid" in error_msg
        assert "not in state machine" in error_msg
        assert "Available states" in error_msg
        assert "state1" in error_msg
        assert "state2" in error_msg
