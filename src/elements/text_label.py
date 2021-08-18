from elements import Element
from state import State

class TextLabel(Element[str]):

    def __init__(self, parent: State, title: str) -> None:
        super().__init__(parent=parent, title=title, value="", type="", callback=None, callback_args=None, use_key_handler=False)

    def on_action(self) -> bool:
        return True

    def reset(self) -> None:
        pass

    def __repr__(self):
        return self.title
