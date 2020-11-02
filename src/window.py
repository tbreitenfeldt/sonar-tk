import pyglet
from pyglet.event import EVENT_UNHANDLED, EVENT_HANDLED
from pyglet.window import key
from accessible_output2.outputs.auto import Auto

from state_machine import StateMachine
from state import State
from utils import KeyHandler
from utils import speech_manager

pyglet.options['debug_gl'] = False

class Window:

    def __init__(self, escapable: bool = False):
        self.escapable: bool = escapable
        self.state_machine: StateMachine = StateMachine()
        self.position: int = 0
        self.key_handler: KeyHandler = KeyHandler()
        self._caption: str = ""
        self.pyglet_window: pyglet.window.Window = None
        self.bind_keys()

    def bind_keys(self) -> None:
        if not self.escapable:
            self.key_handler.add_key_press(lambda: EVENT_HANDLED, key.ESCAPE)  # Remove pyglet default behavior of closing on escape

        self.key_handler.add_key_press(self.close_window, key.W, [key.MOD_CTRL])
        self.key_handler.add_key_press(self.close_window, key.F4, [key.MOD_CTRL])

    def open_window(self, caption: str, width: int = 640, height: int = 480, resizable: bool =False, fullscreen: bool = False) -> None:
        self.pyglet_window = pyglet.window.Window(width, height, resizable=resizable, fullscreen=fullscreen, caption=caption)
        self._caption = caption
        pyglet.clock.schedule_once(lambda dt: speech_manager.silence(), 0.1)
        pyglet.clock.schedule_once(lambda dt: self.run_speech_introduction(), 0.18)
        pyglet.clock.schedule_interval(self.update, 0.01)
        self.push_handlers(self.key_handler)
        pyglet.app.run()

    def run_speech_introduction(self) -> None:
        speech_manager.output(self._caption, interrupt=True, log_message=False)
        first_state_key: str = next(iter(self.state_machine.states))
        self.state_machine.change(first_state_key)


    def update(self, delta_time: float) -> None:
        self.state_machine.update(delta_time)

    def add(self, key: str, state: State) -> None:
        self.state_machine.add(key, state)

    def remove(self, key: str) -> State:
        return self.state_machine.remove(key)

    def change(self, key: str, *args: any, **kwargs: any) -> None:
        self.state_machine.change(key, *args, **kwargs)

    def push_handlers(self, handler: KeyHandler) -> None:
        self.pyglet_window.push_handlers(handler)

    def pop_handlers(self) -> None:
        if len(self.pyglet_window._event_stack) > 1:
            self.pyglet_window.pop_handlers()

    def close_window(self) -> None:
        self.state_machine.clear()
        self.pyglet_window.close()

    @property
    def caption(self) -> str:
        return self._caption

    @caption.setter
    def caption(self, caption: str) -> None:
        speech_manager.output(self._caption, interrupt=True, log_message=False)
        self._caption = caption
        self.pyglet_window.set_caption(caption)
