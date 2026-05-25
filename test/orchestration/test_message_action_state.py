from __future__ import annotations

from pytest_mock import MockerFixture

from sonartk.orchestration.message_action_state import MessageActionState


class _FakeWindow:
    def __init__(self) -> None:
        self.pushed: list[object] = []
        self.popped_count = 0

    def push_window_handlers(self, *args: object, **kwargs: object) -> None:
        self.pushed.extend(args)

    def pop_window_handlers(self) -> None:
        self.popped_count += 1


def test_message_action_state_setup_speaks_and_pushes_handlers(
    mocker: MockerFixture,
) -> None:
    window = _FakeWindow()
    speak_mock = mocker.patch(
        "sonartk.orchestration.message_action_state.speech_manager.output"
    )

    state = MessageActionState(
        window=window,  # type: ignore[arg-type]
        message="Win!",
    )

    assert state.setup(lambda *_args, **_kwargs: None) is True
    assert len(window.pushed) == 1
    speak_mock.assert_called_once_with("Win!")


def test_message_action_state_continue_runs_hook_and_transitions_once(
    mocker: MockerFixture,
) -> None:
    window = _FakeWindow()
    on_continue = mocker.MagicMock()
    change_state = mocker.MagicMock()

    state = MessageActionState(
        window=window,  # type: ignore[arg-type]
        message="Done",
        next_state_key="intro",
        on_continue=on_continue,
    )
    state.setup(change_state)

    assert state.continue_action() is True
    assert state.continue_action() is True

    on_continue.assert_called_once()
    change_state.assert_called_once_with("intro", False)


def test_message_action_state_exit_pops_handlers() -> None:
    window = _FakeWindow()
    state = MessageActionState(
        window=window,  # type: ignore[arg-type]
        message="Done",
    )
    state.setup(lambda *_args, **_kwargs: None)

    assert state.exit() is True
    assert window.popped_count == 1


def test_message_action_state_registers_continue_keys() -> None:
    window = _FakeWindow()
    state = MessageActionState(
        window=window,  # type: ignore[arg-type]
        message="Done",
        continue_keys=[1, 2],
    )

    assert len(state.key_handler.registered_key_presses) == 2


def test_message_action_state_update_returns_true() -> None:
    window = _FakeWindow()
    state = MessageActionState(
        window=window,  # type: ignore[arg-type]
        message="Done",
    )

    assert state.update(0.016) is True
