from __future__ import annotations

from typing import TYPE_CHECKING

from audio_ui.elements.element import Element

if TYPE_CHECKING:
    from audio_ui.screens.screen import Screen


class TextLabel(Element[str]):
    def __init__(self, parent: Screen, label: str) -> None:
        super().__init__(
            parent=parent,
            label=label,
            value="",
            role="",
            use_key_handler=False,
        )

    # override
    def reset(self) -> None:
        pass

    # override
    def __repr__(self) -> str:
        return self.label
