from sonartk.orchestration.input_gate import InputGate


def test_input_gate_lock_unlock_reset() -> None:
    gate = InputGate()

    assert gate.is_locked is False

    gate.lock()
    assert gate.is_locked is True

    gate.unlock()
    assert gate.is_locked is False

    gate.lock()
    gate.reset()
    assert gate.is_locked is False
