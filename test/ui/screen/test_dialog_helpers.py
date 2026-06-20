from typing import Any, Callable

import pyglet.clock
import pytest
from pytest_mock import MockerFixture

from sonartk.ui.element import Button, Menu
from sonartk.ui.screen.dialog_helpers import (
    open_alert_dialog,
    open_confirmation_dialog,
    open_menu_selection_dialog,
)
from sonartk.ui.screen.screen import Screen
from sonartk.ui.window import Window
from sonartk.util import speech_manager
from test.mocks.mock_pyglet_window import MockPygletWindow


class _FakeScreen(Screen):
    def __init__(self, parent: Window) -> None:
        super().__init__(parent)

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


@pytest.fixture
def window(mocker: MockerFixture) -> Window:
    window = Window()
    window.pyglet_window = mocker.MagicMock(spec=MockPygletWindow)
    window.handler_stack = []  # type: ignore[attr-defined]
    window.push_window_handlers = mocker.MagicMock()  # type: ignore[method-assign]
    window.pop_window_handlers = mocker.MagicMock()  # type: ignore[method-assign]
    return window


@pytest.fixture
def parent_screen(window: Window) -> _FakeScreen:
    return _FakeScreen(window)


def test_open_alert_dialog_speaks_message(
    mocker: MockerFixture, parent_screen: _FakeScreen
) -> None:
    mock_output = mocker.patch.object(speech_manager, "output")
    mocker.patch.object(pyglet.clock, "schedule_once")

    dialog = open_alert_dialog(parent_screen, "Alert", "Something happened")

    assert "ok" in dialog.state_machine.states
    mock_output.assert_called_once_with("Something happened", interrupt=True)


def test_open_alert_dialog_calls_on_close_once(
    mocker: MockerFixture, parent_screen: _FakeScreen
) -> None:
    mocker.patch.object(pyglet.clock, "schedule_once")
    closed: list[bool] = []

    dialog = open_alert_dialog(
        parent_screen,
        "Alert",
        "Message",
        on_close=lambda: closed.append(True),
    )
    ok_button = dialog.state_machine.states["ok"]
    assert isinstance(ok_button, Button)

    ok_button.submit()

    assert closed == [True]


def test_open_confirmation_dialog_requires_options(
    parent_screen: _FakeScreen,
) -> None:
    with pytest.raises(ValueError, match="at least one option"):
        open_confirmation_dialog(
            parent_screen,
            "Confirm",
            "Proceed?",
            [],
            lambda _choice: None,
        )


def test_open_confirmation_dialog_returns_choice(
    mocker: MockerFixture, parent_screen: _FakeScreen
) -> None:
    mocker.patch.object(pyglet.clock, "schedule_once")
    choices: list[str | None] = []

    dialog = open_confirmation_dialog(
        parent_screen,
        "Confirm",
        "Proceed?",
        [("Yes", "yes"), ("No", "no")],
        lambda choice: choices.append(choice),
    )
    yes_button = dialog.state_machine.states["option-0"]
    assert isinstance(yes_button, Button)

    yes_button.submit()

    assert choices == ["yes"]


def test_open_menu_selection_dialog_submits_selected_index(
    mocker: MockerFixture, parent_screen: _FakeScreen
) -> None:
    schedule_calls: list[float] = []

    def _immediate_schedule(
        callback: Callable[[float], None], delay: float
    ) -> None:
        schedule_calls.append(delay)
        if delay == 0.35:
            callback(0.0)

    mocker.patch.object(
        pyglet.clock, "schedule_once", side_effect=_immediate_schedule
    )
    selected: list[int | None] = []

    dialog = open_menu_selection_dialog(
        parent_screen,
        "Choose",
        "Items",
        ["A", "B"],
        lambda choice: selected.append(choice),
    )
    assert dialog is not None
    menu = dialog.state_machine.states["menu"]
    assert isinstance(menu, Menu)

    menu.value = "1"
    menu.submit()

    assert selected == [1]
    assert 0.35 in schedule_calls


def test_open_menu_selection_dialog_handles_empty_values(
    parent_screen: _FakeScreen,
) -> None:
    selected: list[int | None] = []

    dialog = open_menu_selection_dialog(
        parent_screen,
        "Choose",
        "Items",
        [],
        lambda choice: selected.append(choice),
    )

    assert dialog is None
    assert selected == [None]
