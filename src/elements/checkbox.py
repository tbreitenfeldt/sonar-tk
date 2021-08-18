from typing import Callable, List

from pyglet.window import key
from pyglet.event import EVENT_HANDLED

from state import State
from elements import Element
from utils import audio_manager
from utils import speech_manager

class Checkbox(Element[bool]):

    def __init__(
        self, parent: State, title: str = "", value: bool = False, callback: Callable[[Callable[[str, any], None], bool, any], None] = None, callback_args: List[any] = [],
        check_sound: str = "", uncheck_sound: str = ""
    ) -> None:
        super().__init__(parent=parent, title=title, value=value, type="Checkbox", callback=callback, callback_args=callback_args)
        self.default_value: bool = value
        self.check_sound: str = check_sound
        self.uncheck_sound: str = uncheck_sound
        self.bind_keys()

    def bind_keys(self) -> None:
        self.key_handler.add_key_press(self.submit, key.RETURN)
        self.key_handler.add_key_press(self.submit, key.SPACE)

    def setup(self, change_state: Callable[[str, any], None], interrupt_speech: str = True) -> bool:
        super().setup(change_state, interrupt_speech)
        output_value: str = "Checked" if self.value  else "Unchecked"
        speech_manager.output(output_value, interrupt=False, log_message=False)
        return True

    def on_action(self) -> bool:
        self.value = not self.value
        output_value: str = "Checked" if self.value  else "Unchecked"
        speech_manager.output(output_value, interrupt=True, log_message=False)
        self.play_toggle_sounds()
        return EVENT_HANDLED

    def play_toggle_sounds(self) -> bool:
        if self.value and self.check_sound:
            audio_manager.play(self.check_sound)
            return True
        elif not self.value and self.uncheck_sound:
            audio_manager.play(self.uncheck_sound)
            return True

        return False

    def reset(self) -> None:
        self.value = self.default_value
