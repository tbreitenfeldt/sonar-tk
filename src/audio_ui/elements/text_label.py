from audio_ui.elements import Element
from audio_ui.utils import State


class TextLabel(Element[str]):
    def __init__(self, parent: State, label: str) -> None:
        super().__init__(
            parent=parent,
            label=label,
            value="",
            role="",
            use_key_handler=False,
        )

    def reset(self) -> None:
        pass

    def __repr__(self):
        return self.label
