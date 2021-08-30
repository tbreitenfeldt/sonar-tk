from typing import List

from audio_ui.utils import KeyHandler

class MockPygletWindow:

    def __init__(self) -> None:
        self.caption: str = ""
        self._event_stack: List[any] = []

    def push_handlers(self, key_handler: KeyHandler) -> None:
        self._event_stack.append(key_handler)

    def pop_handlers(self) -> None:
        self._event_stack.pop(0)

    def set_caption(self, caption: str) -> None:
        self.caption = caption

    def close(self) -> None:
        pass

