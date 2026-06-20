from __future__ import annotations

from typing import Any, Callable, TypeVar

import pyglet.clock

from sonartk.ui.element import Button, Menu
from sonartk.ui.element.element import Element
from sonartk.ui.screen.dialog import Dialog
from sonartk.ui.screen.screen import Screen
from sonartk.util import speech_manager

T = TypeVar("T")


def open_alert_dialog(
    parent: Screen,
    title: str,
    message: str,
    on_close: Callable[[], None] | None = None,
    ok_label: str = "OK",
) -> Dialog:
    """Open a simple alert dialog with one confirmation button."""
    dialog = Dialog(parent)
    resolved = {"value": False}
    ok_button = Button(dialog, ok_label)

    def _resolve(_element: object | None = None) -> None:
        if resolved["value"]:
            return

        resolved["value"] = True
        dialog.close()
        if on_close is not None:
            on_close()

    def _on_dialog_close(_dialog: Dialog) -> None:
        if not resolved["value"] and on_close is not None:
            on_close()

    speech_manager.output(message, interrupt=True)
    ok_button.push_handlers(on_submit=_resolve)
    dialog.push_handlers(on_close=_on_dialog_close)

    dialog.add("ok", ok_button)
    dialog.open_dialog(title)
    return dialog


def open_confirmation_dialog(
    parent: Screen,
    title: str,
    message: str,
    options: list[tuple[str, T]],
    on_decision: Callable[[T | None], None],
    cancel_label: str | None = "Cancel",
) -> Dialog:
    """Open a dialog that resolves to one of several option values."""
    if len(options) == 0:
        raise ValueError("Confirmation dialog requires at least one option")

    dialog = Dialog(parent)
    resolved = {"value": False}

    def _resolve(choice: T | None) -> None:
        if resolved["value"]:
            return

        resolved["value"] = True
        dialog.close()
        on_decision(choice)

    def _on_dialog_close(_dialog: Dialog) -> None:
        if not resolved["value"]:
            on_decision(None)

    speech_manager.output(message, interrupt=True)

    for index, (label, value) in enumerate(options):
        button = Button(dialog, label)
        button.push_handlers(on_submit=lambda _b, v=value: _resolve(v))
        dialog.add(f"option-{index}", button)

    if cancel_label is not None:
        cancel_button = Button(dialog, cancel_label)
        cancel_button.push_handlers(on_submit=lambda _b: _resolve(None))
        dialog.add("cancel", cancel_button)

    dialog.push_handlers(on_close=_on_dialog_close)
    dialog.open_dialog(title)
    return dialog


def open_menu_selection_dialog(
    parent: Screen,
    title: str,
    label: str,
    values: list[str],
    on_selection: Callable[[int | None], None],
    callback_delay_seconds: float = 0.35,
) -> Dialog | None:
    """Open a menu-based selection dialog and resolve to selected index."""
    if len(values) == 0:
        on_selection(None)
        return None

    dialog = Dialog(parent)
    submitted = {"value": False}
    menu_items: list[dict[str, Element[Any] | str]] = [
        {str(index): value} for index, value in enumerate(values)
    ]
    selection_menu = Menu(
        dialog,
        label=label,
        items=menu_items,
        has_border=True,
        is_first_letter_navigation=True,
    )
    select_button = Button(dialog, "Select")
    cancel_button = Button(dialog, "Cancel")

    def _close_with_choice(choice: int | None) -> None:
        submitted["value"] = True
        dialog.close()
        pyglet.clock.schedule_once(
            lambda _dt: on_selection(choice),
            callback_delay_seconds,
        )

    def _submit_from_menu(_element: object | None = None) -> None:
        raw_value = selection_menu.value
        if raw_value is None:
            _close_with_choice(None)
            return

        _close_with_choice(int(raw_value))

    def _cancel(_element: object | None = None) -> None:
        _close_with_choice(None)

    def _on_dialog_close(_dialog: Dialog) -> None:
        if not submitted["value"]:
            on_selection(None)

    selection_menu.push_handlers(on_submit=_submit_from_menu)
    select_button.push_handlers(on_submit=_submit_from_menu)
    cancel_button.push_handlers(on_submit=_cancel)
    dialog.push_handlers(on_close=_on_dialog_close)

    dialog.add("menu", selection_menu)
    dialog.add("select", select_button)
    dialog.add("cancel", cancel_button)
    dialog.open_dialog(title)
    return dialog
