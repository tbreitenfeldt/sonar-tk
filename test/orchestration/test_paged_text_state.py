from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pyglet.window import key
from pytest_mock import MockerFixture

from sonartk.orchestration.paged_text_state import (
    DEFAULT_CONTINUE_KEYS,
    DEFAULT_COPY_KEYS,
    DEFAULT_REREAD_KEYS,
    PagedTextState,
)
from sonartk.util.key_handler import Key

PAGES = ["First page.", "Second page.", "Third page."]


class _FakeWindow:
    def __init__(self) -> None:
        self.pushed: list[object] = []
        self.popped: list[object] = []

    def push_window_handlers(self, *args: object, **kwargs: object) -> None:
        self.pushed.extend(args)

    def pop_window_handlers(self, *args: object, **kwargs: object) -> None:
        self.popped.extend(args)


@pytest.fixture
def speak(mocker: MockerFixture) -> object:
    return mocker.patch(
        "sonartk.orchestration.paged_text_state.speech_manager.output"
    )


@pytest.fixture
def clipboard(mocker: MockerFixture) -> object:
    return mocker.patch(
        "sonartk.orchestration.paged_text_state.pyperclip.copy"
    )


def _make_state(**kwargs: object) -> tuple[PagedTextState, _FakeWindow]:
    window = _FakeWindow()
    state = PagedTextState(
        window=window,  # type: ignore[arg-type]
        pages=kwargs.pop("pages", PAGES),  # type: ignore[arg-type]
        **kwargs,  # type: ignore[arg-type]
    )
    return state, window


def _press(
    state: PagedTextState, symbol: int, modifiers: int = 0
) -> bool | None:
    return state.key_handler.on_key_press(symbol, modifiers)


def _start(state: PagedTextState, mocker: MockerFixture) -> MagicMock:
    change_state: MagicMock = mocker.MagicMock()
    state.setup(change_state)
    return change_state


# --- construction ---------------------------------------------------------


def test_empty_pages_raise_value_error() -> None:
    with pytest.raises(ValueError, match="at least one page"):
        _make_state(pages=[])


def test_pages_are_copied_to_a_tuple() -> None:
    pages = ["a", "b"]
    state, _ = _make_state(pages=pages)
    pages.append("c")

    assert state.pages == ("a", "b")


def test_default_shortcuts_are_registered() -> None:
    state, _ = _make_state()
    registered = state.key_handler.registered_key_presses

    for binding in (
        *DEFAULT_CONTINUE_KEYS,
        *DEFAULT_REREAD_KEYS,
        *DEFAULT_COPY_KEYS,
    ):
        expected = binding if isinstance(binding, Key) else Key(binding)
        assert expected in registered


def test_empty_shortcut_sequences_disable_shortcuts() -> None:
    state, _ = _make_state(continue_keys=[], reread_keys=[], copy_keys=[])

    assert len(state.key_handler.registered_key_presses) == 0


def test_custom_shortcuts_replace_defaults() -> None:
    ctrl_r = Key(key.R, [key.MOD_CTRL])
    state, _ = _make_state(
        continue_keys=[key.SPACE], reread_keys=[ctrl_r], copy_keys=[key.F2]
    )

    assert set(state.key_handler.registered_key_presses) == {
        Key(key.SPACE),
        ctrl_r,
        Key(key.F2),
    }


# --- lifecycle ------------------------------------------------------------


def test_setup_speaks_first_page_and_pushes_handler(
    speak: object, mocker: MockerFixture
) -> None:
    state, window = _make_state()

    assert state.setup(mocker.MagicMock()) is True

    assert window.pushed == [state.key_handler]
    speak.assert_called_once_with("First page.")  # type: ignore[attr-defined]
    assert state.page_index == 0
    assert state.current_page == "First page."


def test_setup_resets_progress_when_state_is_reentered(
    speak: object, mocker: MockerFixture
) -> None:
    state, _ = _make_state(next_state_key="game")
    _start(state, mocker)
    _press(state, key.RETURN)
    _press(state, key.RETURN)
    _press(state, key.RETURN)

    change_state = _start(state, mocker)

    assert state.page_index == 0
    _press(state, key.RETURN)
    _press(state, key.RETURN)
    _press(state, key.RETURN)
    change_state.assert_called_once_with("game", False)


def test_exit_pops_its_handler(speak: object, mocker: MockerFixture) -> None:
    state, window = _make_state()
    _start(state, mocker)

    assert state.exit() is True
    assert window.popped == [state.key_handler]


def test_update_returns_true() -> None:
    state, _ = _make_state()

    assert state.update(0.016) is True


# --- advancing ------------------------------------------------------------


@pytest.mark.parametrize("symbol", [key.RETURN, key.ENTER, key.SPACE])
def test_default_continue_keys_advance_one_page(
    speak: object, mocker: MockerFixture, symbol: int
) -> None:
    state, _ = _make_state()
    _start(state, mocker)

    _press(state, symbol)

    assert state.page_index == 1
    assert state.current_page == "Second page."


def test_advance_speaks_new_page_with_interrupt_by_default(
    speak: object, mocker: MockerFixture
) -> None:
    state, _ = _make_state()
    _start(state, mocker)
    speak.reset_mock()  # type: ignore[attr-defined]

    _press(state, key.RETURN)

    speak.assert_called_once_with(  # type: ignore[attr-defined]
        "Second page.", interrupt=True
    )


def test_advance_can_queue_speech_instead_of_interrupting(
    speak: object, mocker: MockerFixture
) -> None:
    state, _ = _make_state(interrupt_on_advance=False)
    _start(state, mocker)
    speak.reset_mock()  # type: ignore[attr-defined]

    _press(state, key.RETURN)

    speak.assert_called_once_with(  # type: ignore[attr-defined]
        "Second page.", interrupt=False
    )


def test_non_continue_keys_do_not_advance(
    speak: object, mocker: MockerFixture
) -> None:
    state, _ = _make_state()
    _start(state, mocker)

    _press(state, key.ESCAPE)
    _press(state, key.TAB)

    assert state.page_index == 0


def test_is_last_page_tracks_progress(
    speak: object, mocker: MockerFixture
) -> None:
    state, _ = _make_state()
    _start(state, mocker)

    assert state.is_last_page is False
    _press(state, key.RETURN)
    assert state.is_last_page is False
    _press(state, key.RETURN)
    assert state.is_last_page is True


def test_single_page_is_the_last_page_immediately(
    speak: object, mocker: MockerFixture
) -> None:
    state, _ = _make_state(pages=["Only page."])
    _start(state, mocker)

    assert state.is_last_page is True


# --- finishing ------------------------------------------------------------


def test_continue_on_last_page_transitions_to_next_state(
    speak: object, mocker: MockerFixture
) -> None:
    state, _ = _make_state(next_state_key="game")
    change_state = _start(state, mocker)

    _press(state, key.RETURN)
    _press(state, key.RETURN)
    change_state.assert_not_called()
    _press(state, key.RETURN)

    change_state.assert_called_once_with("game", False)


def test_transition_happens_only_once(
    speak: object, mocker: MockerFixture
) -> None:
    state, _ = _make_state(pages=["Only"], next_state_key="game")
    change_state = _start(state, mocker)

    _press(state, key.RETURN)
    _press(state, key.RETURN)

    change_state.assert_called_once_with("game", False)


def test_last_page_is_not_respoken_when_finishing(
    speak: object, mocker: MockerFixture
) -> None:
    state, _ = _make_state(pages=["Only"], next_state_key="game")
    _start(state, mocker)
    speak.reset_mock()  # type: ignore[attr-defined]

    _press(state, key.RETURN)

    speak.assert_not_called()  # type: ignore[attr-defined]


def test_last_page_without_next_state_does_not_transition(
    speak: object, mocker: MockerFixture
) -> None:
    state, _ = _make_state(pages=["Only"])
    change_state = _start(state, mocker)

    _press(state, key.RETURN)

    change_state.assert_not_called()


def test_continue_before_setup_does_not_raise(speak: object) -> None:
    state, _ = _make_state(pages=["Only"], next_state_key="game")

    assert state.continue_action() is True


# --- reread ---------------------------------------------------------------


@pytest.mark.parametrize("symbol", [key.UP, key.DOWN])
def test_default_reread_keys_speak_current_page(
    speak: object, mocker: MockerFixture, symbol: int
) -> None:
    state, _ = _make_state()
    _start(state, mocker)
    _press(state, key.RETURN)
    speak.reset_mock()  # type: ignore[attr-defined]

    _press(state, symbol)

    speak.assert_called_once_with(  # type: ignore[attr-defined]
        "Second page.", interrupt=True, log_message=False
    )
    assert state.page_index == 1


def test_custom_reread_shortcut_with_modifier(
    speak: object, mocker: MockerFixture
) -> None:
    state, _ = _make_state(reread_keys=[Key(key.R, [key.MOD_CTRL])])
    _start(state, mocker)
    speak.reset_mock()  # type: ignore[attr-defined]

    _press(state, key.R)
    speak.assert_not_called()  # type: ignore[attr-defined]
    _press(state, key.R, key.MOD_CTRL)

    speak.assert_called_once_with(  # type: ignore[attr-defined]
        "First page.", interrupt=True, log_message=False
    )


def test_reread_still_works_after_final_page(
    speak: object, mocker: MockerFixture
) -> None:
    state, _ = _make_state(pages=["Only"], next_state_key="game")
    _start(state, mocker)
    _press(state, key.RETURN)
    speak.reset_mock()  # type: ignore[attr-defined]

    state.reread_page()

    speak.assert_called_once_with(  # type: ignore[attr-defined]
        "Only", interrupt=True, log_message=False
    )


# --- copy -----------------------------------------------------------------


def test_default_copy_shortcut_copies_current_page(
    speak: object, clipboard: object, mocker: MockerFixture
) -> None:
    state, _ = _make_state()
    _start(state, mocker)
    _press(state, key.RETURN)
    speak.reset_mock()  # type: ignore[attr-defined]

    _press(state, key.C, key.MOD_CTRL)

    clipboard.assert_called_once_with("Second page.")  # type: ignore[attr-defined]
    speak.assert_called_once_with(  # type: ignore[attr-defined]
        "Copied page to clipboard", interrupt=True, log_message=False
    )


def test_copy_requires_the_modifier(
    speak: object, clipboard: object, mocker: MockerFixture
) -> None:
    state, _ = _make_state()
    _start(state, mocker)

    _press(state, key.C)

    clipboard.assert_not_called()  # type: ignore[attr-defined]


def test_custom_copy_shortcut(
    speak: object, clipboard: object, mocker: MockerFixture
) -> None:
    state, _ = _make_state(copy_keys=[key.F2])
    _start(state, mocker)

    _press(state, key.F2)
    _press(state, key.C, key.MOD_CTRL)

    clipboard.assert_called_once_with("First page.")  # type: ignore[attr-defined]


# --- events ---------------------------------------------------------------


def test_on_page_change_fires_with_new_index_after_speaking(
    speak: object, mocker: MockerFixture
) -> None:
    state, _ = _make_state()
    calls: list[tuple[object, int, str]] = []
    state.push_handlers(
        on_page_change=lambda s, index: calls.append(
            (s, index, s.current_page)
        )
    )
    _start(state, mocker)

    _press(state, key.RETURN)
    _press(state, key.RETURN)

    assert calls == [(state, 1, "Second page."), (state, 2, "Third page.")]


def test_on_page_change_does_not_fire_for_first_page_or_finish(
    speak: object, mocker: MockerFixture
) -> None:
    state, _ = _make_state(pages=["One", "Two"], next_state_key="game")
    on_page_change = mocker.MagicMock()
    state.push_handlers(on_page_change=on_page_change)

    _start(state, mocker)
    on_page_change.assert_not_called()

    _press(state, key.RETURN)
    _press(state, key.RETURN)

    on_page_change.assert_called_once_with(state, 1)


def test_on_page_change_does_not_fire_for_reread_or_copy(
    speak: object, clipboard: object, mocker: MockerFixture
) -> None:
    state, _ = _make_state()
    on_page_change = mocker.MagicMock()
    state.push_handlers(on_page_change=on_page_change)
    _start(state, mocker)

    _press(state, key.UP)
    _press(state, key.C, key.MOD_CTRL)

    on_page_change.assert_not_called()


def test_on_complete_fires_once_before_transition(
    speak: object, mocker: MockerFixture
) -> None:
    state, _ = _make_state(pages=["Only"], next_state_key="game")
    order: list[str] = []
    state.push_handlers(on_complete=lambda s: order.append("complete"))
    change_state = mocker.MagicMock(
        side_effect=lambda *a: order.append("transition")
    )
    state.setup(change_state)

    _press(state, key.RETURN)
    _press(state, key.RETURN)

    assert order == ["complete", "transition"]


def test_on_complete_fires_without_next_state(
    speak: object, mocker: MockerFixture
) -> None:
    state, _ = _make_state(pages=["Only"])
    on_complete = mocker.MagicMock()
    state.push_handlers(on_complete=on_complete)
    _start(state, mocker)

    _press(state, key.RETURN)
    _press(state, key.RETURN)

    on_complete.assert_called_once_with(state)


def test_on_complete_does_not_fire_before_last_page(
    speak: object, mocker: MockerFixture
) -> None:
    state, _ = _make_state()
    on_complete = mocker.MagicMock()
    state.push_handlers(on_complete=on_complete)
    _start(state, mocker)

    _press(state, key.RETURN)

    on_complete.assert_not_called()


def test_on_reread_and_on_copy_fire_with_page_index(
    speak: object, clipboard: object, mocker: MockerFixture
) -> None:
    state, _ = _make_state()
    on_reread = mocker.MagicMock()
    on_copy = mocker.MagicMock()
    state.push_handlers(on_reread=on_reread, on_copy=on_copy)
    _start(state, mocker)
    _press(state, key.RETURN)

    _press(state, key.UP)
    _press(state, key.C, key.MOD_CTRL)

    on_reread.assert_called_once_with(state, 1)
    on_copy.assert_called_once_with(state, 1)
