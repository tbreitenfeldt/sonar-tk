from typing import Callable

from pyglet import clock
from pyglet.event import EVENT_HANDLED
from pyglet.window import key

from audio_ui.screens import Screen
from audio_ui.screens import ContainerScreen
from audio_ui.utils import speech_manager
from audio_ui.utils import KeyHandler
from audio_ui.state_machine import EmptyState

class Dialog(Screen):

    def __init__(self, parent: ContainerScreen) -> None:
        super().__init__(parent)
        self.original_state_key: str = ""
        self.change_state: Callable[[str, any], None] = None

    def bind_keys(self) -> None:
        self.key_handler.add_key_press(self.close, key.ESCAPE)
        self.key_handler.add_key_press(self.next_element, key.TAB)
        self.key_handler.add_key_press(self.previous_element, key.TAB, [key.MOD_SHIFT])

    def open_dialog(self, caption: str) -> None:
        count: int = self.parent.state_machine.size() + 1
        self.parent.add(f"dialog{count}", self)
        self.original_caption = self.caption
        self.caption = caption + " Dialog"
        clock.schedule_once(lambda dt: self.parent.state_machine.change(self.state_key), 0.3)

    def setup(self, change_state: Callable[[str, any], None], *args, **kwargs) -> bool:
        self.change_state = change_state
        self.push_window_handlers(self.key_handler)
        self.set_state(interrupt_speech=False)
        return EVENT_HANDLED

    def update(self, delta_time: float) -> bool:
        return self.state_machine.update(delta_time)

    def exit(self) -> bool:
        if self.state_machine.size() > 0:
            self.state_machine.exit()

        self.pop_window_handlers()
        return EVENT_HANDLED

    def reset(self) -> None:
        for element in self.state_machine.states.values():
            element.reset()

    def close(self) -> None:
        self.position = 0
        self.reset()
        self.caption = self.original_caption
        clock.schedule_once(lambda db: self._reset_states(), 0.3)
        return EVENT_HANDLED

    def _reset_states(self) -> None:
        self.parent.set_state(interrupt_speech=False)
        self.state_machine.current_state = EmptyState()
        self.parent.remove(self.state_key)
