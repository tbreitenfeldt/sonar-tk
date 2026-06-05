from __future__ import annotations

from sonartk.orchestration.state_flow import WindowStateFlow
from sonartk.util.state import State


class _FakeWindow:
    def __init__(self) -> None:
        self.states: dict[str, State] = {}
        self.start_state: str | None = None

    def add(self, key: str, state: State) -> None:
        self.states[key] = state

    def set_start_state(self, key: str) -> None:
        self.start_state = key


class _FakeState(State):
    def setup(self, *args: object, **kwargs: object) -> bool:
        return True

    def update(self, delta_time: float) -> bool:
        return True

    def exit(self) -> bool:
        return True


def test_window_state_flow_add_many_and_start_at() -> None:
    window = _FakeWindow()
    intro_state = _FakeState()
    main_state = _FakeState()

    WindowStateFlow(window).add_many(
        {
            "intro": intro_state,
            "main": main_state,
        }
    ).start_at("intro")

    assert window.states == {
        "intro": intro_state,
        "main": main_state,
    }
    assert window.start_state == "intro"
