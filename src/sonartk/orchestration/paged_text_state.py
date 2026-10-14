from __future__ import annotations

from typing import Any, Callable, Optional, Sequence

import pyperclip
from pyglet.event import EventDispatcher
from pyglet.window import key

from sonartk.ui.window import Window
from sonartk.util import speech_manager
from sonartk.util.key_handler import Key, KeyHandler
from sonartk.util.state import State

KeyBinding = int | Key

DEFAULT_CONTINUE_KEYS: tuple[KeyBinding, ...] = (
    key.RETURN,
    key.ENTER,
    key.SPACE,
)
DEFAULT_REREAD_KEYS: tuple[KeyBinding, ...] = (key.UP, key.DOWN)
DEFAULT_COPY_KEYS: tuple[KeyBinding, ...] = (Key(key.C, [key.MOD_CTRL]),)


class PagedTextState(State, EventDispatcher):
    """Reusable state that speaks text one page at a time.

    The first page is spoken when the state becomes active. Pressing a
    continue key speaks the next page. Pressing a continue key on the last
    page finishes the state and, if ``next_state_key`` is set, transitions
    to that state. While a page is current, the player can re-read it or copy
    it to the clipboard.

    Each shortcut option takes a sequence of keys, where each entry is a key
    symbol or a ``Key`` (to include modifiers). An empty sequence disables
    that shortcut.

    Events:
        on_page_change(state, page_index): Dispatched after the player
            advances to another page, once it is current and spoken. It is not
            dispatched for the first page, since the state's own activation
            covers that.
        on_complete(state): Dispatched when a continue key is pressed on the
            last page, before any transition to ``next_state_key``.
        on_reread(state, page_index): Dispatched after the current page is
            re-read.
        on_copy(state, page_index): Dispatched after the current page is
            copied to the clipboard.
    """

    def __init__(
        self,
        *,
        window: Window,
        pages: Sequence[str],
        next_state_key: Optional[str] = None,
        continue_keys: Sequence[KeyBinding] = DEFAULT_CONTINUE_KEYS,
        reread_keys: Sequence[KeyBinding] = DEFAULT_REREAD_KEYS,
        copy_keys: Sequence[KeyBinding] = DEFAULT_COPY_KEYS,
        interrupt_on_advance: bool = True,
    ) -> None:
        super().__init__()
        if len(pages) == 0:
            raise ValueError("pages must contain at least one page.")

        self.window = window
        self.pages: tuple[str, ...] = tuple(pages)
        self.next_state_key = next_state_key
        self.interrupt_on_advance = interrupt_on_advance
        self.key_handler = KeyHandler()
        self._change_state: Optional[Callable[[str, Any], None]] = None
        self._page_index = 0
        self._is_complete = False

        self._bind(self.continue_action, continue_keys)
        self._bind(self.reread_page, reread_keys)
        self._bind(self.copy_page, copy_keys)

    @property
    def page_index(self) -> int:
        """Return the zero-based index of the current page."""
        return self._page_index

    @property
    def current_page(self) -> str:
        """Return the text of the current page."""
        return self.pages[self._page_index]

    @property
    def is_last_page(self) -> bool:
        """Return whether the current page is the last one."""
        return self._page_index == len(self.pages) - 1

    # override
    def setup(
        self,
        change_state: Callable[[str, Any], None],
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        self._change_state = change_state
        self._page_index = 0
        self._is_complete = False
        self.key_handler.activate(reset_state=True)
        self.window.push_window_handlers(self.key_handler)
        speech_manager.output(self.current_page)
        return True

    # override
    def update(self, delta_time: float) -> bool:
        return True

    # override
    def exit(self) -> bool:
        self.key_handler.deactivate(reset_state=True)
        self.window.pop_window_handlers(self.key_handler)
        return True

    def continue_action(self) -> bool:
        """Advance to the next page, or finish on the last page."""
        if self._is_complete:
            return True

        if not self.is_last_page:
            self._page_index += 1
            speech_manager.output(
                self.current_page, interrupt=self.interrupt_on_advance
            )
            self.dispatch_event("on_page_change", self, self._page_index)
            return True

        self._is_complete = True
        self.dispatch_event("on_complete", self)
        if self.next_state_key is not None and self._change_state is not None:
            self._change_state(self.next_state_key, False)

        return True

    def reread_page(self) -> bool:
        """Speak the current page again."""
        speech_manager.output(
            self.current_page, interrupt=True, log_message=False
        )
        self.dispatch_event("on_reread", self, self._page_index)
        return True

    def copy_page(self) -> bool:
        """Copy the current page text to the clipboard."""
        pyperclip.copy(self.current_page)
        speech_manager.output(
            "Copied page to clipboard", interrupt=True, log_message=False
        )
        self.dispatch_event("on_copy", self, self._page_index)
        return True

    def _bind(
        self, callback: Callable[[], bool], bindings: Sequence[KeyBinding]
    ) -> None:
        for binding in bindings:
            self.key_handler.add_key_press(callback, binding)


PagedTextState.register_event_type("on_page_change")
PagedTextState.register_event_type("on_complete")
PagedTextState.register_event_type("on_reread")
PagedTextState.register_event_type("on_copy")
