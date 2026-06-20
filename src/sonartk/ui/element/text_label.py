from __future__ import annotations

import pyperclip
from pyglet.window import key

from sonartk.ui.ui_component import UIComponent

from sonartk.ui.element.element import Element
from sonartk.util import speech_manager


class TextLabel(Element[str]):
    def __init__(
        self,
        parent: UIComponent,
        label: str,
        enable_shortcuts: bool = True,
    ) -> None:
        super().__init__(
            parent=parent,
            label=label,
            value="",
            role="",
            use_key_handler=enable_shortcuts,
        )

    # override
    def bind_keys(self) -> None:
        """Bind reread and copy shortcuts for labels."""
        self.key_handler.add_key_press(self.reread_label, key.UP)
        self.key_handler.add_key_press(self.reread_label, key.DOWN)
        self.key_handler.add_key_press(self.copy_label, key.C, [key.MOD_CTRL])

    def reread_label(self) -> bool:
        """Speak the current label text."""
        output = self.label if self.label != "" else "Blank"
        speech_manager.output(output, interrupt=True, log_message=False)
        return True

    def copy_label(self) -> bool:
        """Copy the label text to the clipboard."""
        pyperclip.copy(self.label)
        speech_manager.output(
            "Copied label to clipboard", interrupt=True, log_message=False
        )
        return True

    # override
    def reset(self) -> None:
        """Reset."""
        pass

    # override
    def __repr__(self) -> str:
        return self.label
