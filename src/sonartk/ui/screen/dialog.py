from __future__ import annotations

from typing import cast

import pyglet.clock
from pyglet.window import key

from sonartk.ui.element.element import Element
from sonartk.ui.screen.container_screen import ContainerScreen
from sonartk.ui.screen.screen import Screen
from sonartk.util.state_machine import EmptyState


class Dialog(ContainerScreen):
    def __init__(self, parent: Screen) -> None:
        super().__init__(parent)
        self.original_caption: str = ""
        self.original_state_key: str = ""

    def open_dialog(self, caption: str) -> None:
        """Attach this dialog to the parent and switch focus into it."""
        parent = cast(Screen, self.parent)
        self.original_state_key = parent.state_machine.current_state.state_key
        count: int = parent.state_machine.size() + 1
        parent.add(f"dialog-{caption}-{count}", self)
        self.original_caption = self.caption
        self.caption = caption + " Dialog"
        # Delay focus shift so dialog-caption speech is less likely to interrupt
        # the first focused element label inside the dialog.
        pyglet.clock.schedule_once(
            lambda dt: parent.state_machine.change(self.state_key), 0.3
        )

    # override
    def bind_keys(self) -> None:
        """Bind dialog-specific keys, including escape-to-close behavior."""
        super().bind_keys()
        self.key_handler.add_key_press(self.close, key.ESCAPE)

    # override
    def reset(self) -> None:
        """Reset all dialog child elements to their default values."""
        for state in self.state_machine.states.values():
            element: Element = cast(Element, state)
            element.reset()

    # override
    def close(self) -> bool:
        # Call Screen.close() directly, NOT ContainerScreen.close()
        # to avoid closing the parent screen
        """Close the dialog, restore caption, and return focus to the prior state."""
        from sonartk.ui.screen.screen import Screen

        Screen.close(self)
        self.position = 0
        self.reset()
        self.caption = self.original_caption
        # Delay parent refocus so restored parent caption/title speech is less
        # likely to interrupt the focused element label in the parent.
        pyglet.clock.schedule_once(lambda db: self._reset_states(), 0.3)
        return True

    def _reset_states(self) -> None:
        parent = cast(Screen, self.parent)
        parent.remove(self.state_key)
        self.state_machine.current_state = EmptyState()
        self.exit()
        parent.state_machine.change(self.original_state_key, False)
