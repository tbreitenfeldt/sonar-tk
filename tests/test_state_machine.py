import unittest

from state_machine import StateMachine, EmptyState
from state import State
from test_state import TestState

class TestStateMachine(unittest.TestCase):

    def test_default_state(self):
        state_machine: StateMachine = StateMachine()
        self.assertIsInstance(state_machine.current_state, State)
        self.assertIsInstance(state_machine.current_state, EmptyState)

    def test_valid_value_for_add(self):
        state_machine: StateMachine = StateMachine()
        key: str = "test"
        test_state: TestState = TestState()
        state_machine.add(key, test_state)
        self.assertEqual(state_machine.states[key], test_state, "Should be equal")
        self.assertEqual(state_machine.states[key].state_key, key, f"should be equal to {key}")

    def test_none_value_for_add(self):
        state_machine: StateMachine = StateMachine()
        key: str = "test"
        test_state: TestState = None
        state_machine.add(key, test_state)
        self.assertEqual(state_machine.states[key], test_state, "Should be TestState()")

    def test_valid_value_for_remove(self):
        state_machine: StateMachine = StateMachine()
        key: str = "test"
        test_state: TestState = TestState()
        state_machine.states[key] = test_state
        self.assertEqual(state_machine.remove(key), test_state, "Should be equal to TestState()")
        self.assertEqual(len(state_machine.states), 0, "Should be 0")

    def test_invalid_value_for_remove(self):
        state_machine: StateMachine = StateMachine()
        key: str = "test"
        test_state: TestState = TestState()
        state_machine.states[key] = test_state
        self.assertIsNone(state_machine.remove("abcdefg"), "Should be None")
        self.assertEquals(len(state_machine.states), 1, "Should be 1")

    def test_clear(self):
        state_machine: StateMachine = StateMachine()
        state_machine.states["test1"] = TestState()
        state_machine.states["test2"] = TestState()
        state_machine.states["test3"] = TestState()
        state_machine.clear()
        self.assertEqual(len(state_machine.states), 0, "Should be 0")

    def test_size(self):
        state_machine: StateMachine = StateMachine()
        state_machine.states["test1"] = TestState()
        state_machine.states["test2"] = TestState()
        state_machine.states["test3"] = TestState()
        self.assertEqual(state_machine.size(), 3, "Should be 3")

    def test_valid_change(self):
        state_machine: StateMachine = StateMachine()
        test_state1: TestState = TestState()
        state_machine.states["test1"] = test_state1
        state_machine.change("test1")
        self.assertEqual(state_machine.current_state, test_state1, "Should be test_state1")

    def test_invalid_change(self):
        state_machine: StateMachine = StateMachine()
        test_state1: TestState = TestState()
        state_machine.states["test1"] = test_state1
        self.assertRaises(KeyError, state_machine.change, "abcdefg")

    def test_exit_block_change(self):
        state_machine: StateMachine = StateMachine()
        test_state1: TestState = TestState(exit_value=False)
        test_state2: TestState = TestState()
        state_machine.states["test1"] = test_state1
        state_machine.states["test2"] = test_state2
        state_machine.current_state = test_state1
        state_machine.change("test2")
        self.assertEqual(state_machine.current_state, test_state1, "Should be test_state1")

    def test_setup_block_change(self):
        state_machine: StateMachine = StateMachine()
        test_state1: TestState = TestState()
        test_state2: TestState = TestState(setup_value=False)
        state_machine.states["test1"] = test_state1
        state_machine.states["test2"] = test_state2
        state_machine.current_state = test_state1
        state_machine.change("test2")
        self.assertEqual(state_machine.current_state, test_state1, "Should be test_state1")

if __name__ == "__main__":
    unittest.main()