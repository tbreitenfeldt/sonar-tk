import pytest

from audio_ui import StateMachine, EmptyState, state
from audio_ui import State
from test.mocks.mock_state import MockState

@pytest.fixture
def state_machine() -> StateMachine:
    """Returns an empty StateMachine instance"""
    return StateMachine()

def test_default_state(state_machine: StateMachine):
    assert isinstance(state_machine.current_state, State)
    assert isinstance(state_machine.current_state, EmptyState)

def test_valid_value_for_add(state_machine: StateMachine):
    key: str = "test"
    test_state: MockState = MockState()
    state_machine.add(key, test_state)
    assert state_machine.states[key] == test_state
    assert state_machine.states[key].state_key == key

def test_none_state_for_add(state_machine: StateMachine):
    with pytest.raises(ValueError):
        key: str = "test"
        test_state: MockState = None
        state_machine.add(key, test_state)

def test_none_key_for_add(state_machine: StateMachine):
    with pytest.raises(ValueError):
        key: str = None
        test_state: MockState = MockState()
        state_machine.add(key, test_state)

def test_valid_value_for_remove(state_machine: StateMachine):
    key: str = "test"
    test_state: MockState = MockState()
    state_machine.states[key] = test_state
    assert state_machine.remove(key) == test_state
    assert len(state_machine.states) == 0

def test_invalid_value_for_remove(state_machine: StateMachine):
    key: str = "test"
    test_state: MockState = MockState()
    state_machine.states[key] = test_state
    
    assert state_machine.remove("abcdefg") == None
    assert len(state_machine.states) == 1

def test_clear(state_machine: StateMachine):
    state_machine.states["test1"] = MockState()
    state_machine.states["test2"] = MockState()
    state_machine.states["test3"] = MockState()
    state_machine.clear()
    assert len(state_machine.states) == 0

def test_size(state_machine: StateMachine):
    state_machine.states["test1"] = MockState()
    state_machine.states["test2"] = MockState()
    state_machine.states["test3"] = MockState()
    assert state_machine.size() == 3

def test_valid_change(state_machine: StateMachine):
    test_state1: MockState = MockState()
    state_machine.states["test1"] = test_state1
    state_machine.change("test1")
    assert state_machine.current_state ==  test_state1

def test_invalid_change(state_machine: StateMachine):
    with pytest.raises(KeyError):
        state_machine.change("abcdefg")

def test_exit_block_change(state_machine: StateMachine):
    test_state1: MockState = MockState(exit_value=False)
    test_state2: MockState = MockState()
    state_machine.states["test1"] = test_state1
    state_machine.states["test2"] = test_state2
    state_machine.current_state = test_state1
    state_machine.change("test2")
    assert state_machine.current_state == test_state1

def test_setup_block_change(state_machine: StateMachine):
    test_state1: MockState = MockState()
    test_state2: MockState = MockState(setup_value=False)
    state_machine.states["test1"] = test_state1
    state_machine.states["test2"] = test_state2
    state_machine.current_state = test_state1
    state_machine.change("test2")
    assert state_machine.current_state == test_state1

def test_successful_setup(state_machine: StateMachine):
    mock_state: MockState = MockState(setup_value=True)
    state_machine.states["test"] = mock_state
    state_machine.current_state = mock_state
    assert state_machine.setup(state_machine.change) == True

def test_block_setup(state_machine: StateMachine):
    mock_state: MockState = MockState(setup_value=False)
    state_machine.states["test"] = mock_state
    state_machine.current_state = mock_state
    assert state_machine.setup() == False

def test_successful_exit(state_machine: StateMachine):
    mock_state: MockState = MockState(exit_value=True)
    state_machine.states["test"] = mock_state
    state_machine.current_state = mock_state
    assert state_machine.exit() == True

def test_block_exit(state_machine: StateMachine):
    mock_state: MockState = MockState(exit_value=False)
    state_machine.states["test"] = mock_state
    state_machine.current_state = mock_state
    assert state_machine.exit() == False

def test_successful_update(state_machine: StateMachine):
    mock_state: MockState = MockState(update_value=True)
    state_machine.states["test"] = mock_state
    state_machine.current_state = mock_state
    assert state_machine.update(0.0) == True

def test_successful_update(state_machine: StateMachine):
    mock_state: MockState = MockState(update_value=False)
    state_machine.states["test"] = mock_state
    state_machine.current_state = mock_state
    assert state_machine.update(0.0) == False

def test_empty_state_setup(state_machine: StateMachine):
    empty_state: EmptyState = EmptyState()
    assert empty_state.setup(state_machine.change) == True

def test_empty_state_update():
    empty_state: EmptyState = EmptyState()
    assert empty_state.update(0.0) == True

def test_empty_state_exit():
    empty_state: EmptyState = EmptyState()
    assert empty_state.exit() == True
