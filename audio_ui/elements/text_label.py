from audio_ui.elements import Element
from audio_ui.state import State

class TextLabel(Element[str]):

    def __init__(self, parent: State, title: str) -> None:
        super().__init__(parent=parent, title=title, value="", type="", use_key_handler=False)

    def reset(self) -> None:
        pass

    def __repr__(self):
        return self.title
