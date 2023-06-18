import pyglet
from pyglet.event import EVENT_UNHANDLED, EVENT_HANDLED
from pyglet.window import key
from accessible_output2.outputs.auto import Auto

from .state_machine import StateMachine
from .state import State
from .utils import KeyHandler
from .utils import speech_manager

pyglet.options['debug_gl'] = False

class Window:

    def __init__(self, caption: str = "", escapable: bool = False):
        self.escapable: bool = escapable
        self.state_machine: StateMachine = StateMachine()
        self.position: int = 0
        self.key_handler: KeyHandler = KeyHandler()
        self._caption: str = caption
        self.pyglet_window: pyglet.window.Window = None
        self.is_open: bool = False
        self.bind_keys()

    def bind_keys(self) -> None:
        if not self.escapable:
            self.key_handler.add_key_press(lambda: EVENT_HANDLED, key.ESCAPE)  # Remove pyglet default behavior of closing on escape

        self.key_handler.add_key_press(self.close, key.W, [key.MOD_CTRL])
        self.key_handler.add_key_press(self.close, key.F4, [key.MOD_CTRL])

    def open_window(self, caption: str = "", width: int = 640, height: int = 480, resizable: bool =False, fullscreen: bool = False) -> None:
        if caption != "":
            self._caption = caption
        if self._caption == "" or self._caption is None:
            raise ValueError("No caption was set for the window")

        self.pyglet_window = pyglet.window.Window(width, height, resizable=resizable, fullscreen=fullscreen, caption=self._caption, visible=False)
        pyglet.clock.schedule_interval(self.update, 0.01)
        self.push_window_handlers(self.key_handler, on_activate=self.on_window_activate)
        self.setup()
        self.pyglet_window.set_visible()
        pyglet.app.run()

    def on_window_activate(self) -> bool:
        if self.is_open:
            if hasattr(self.state_machine.current_state, "active_element"):
                screen: Screen = self.state_machine.current_state
                element: State = screen.active_element

                while element is not None and hasattr(element, "active_element"):
                    element = element.active_element

                if element is not None and hasattr(element, "name"):
                    pyglet.clock.schedule_once(lambda dt: speech_manager.output(element.name, interrupt=False, log_message=False), 0.4)

            return EVENT_HANDLED

        self.is_open = True
        return EVENT_UNHANDLED

    def setup(self) -> None:
        def _setup() -> None:
            speech_manager.output(self._caption, interrupt=True, log_message=False)
            self.set_state()

        # Run a series of scheduled jobs to guess at when the screen reader needs to be silenced before start up. All of these calls are needed to account for operating system varients in scheduling.
        # This is to fix a small bug where NVDA attempts to read the name of the executing file and gets interrupted by the caption that is set.
        # The caption in this case wil also hopefully be silenced to duplicate JAWS behavior, so that speaking the title of the window is the responsibility of the application.
        speech_manager.silence()
        pyglet.clock.schedule_once(lambda dt: speech_manager.silence(), 0.001)
        pyglet.clock.schedule_once(lambda dt: speech_manager.silence(), 0.01)
        pyglet.clock.schedule_once(lambda dt: speech_manager.silence(), 0.05)
        pyglet.clock.schedule_once(lambda dt: speech_manager.silence(), 0.1)
        pyglet.clock.schedule_once(lambda dt: speech_manager.silence(), 0.15)
        pyglet.clock.schedule_once(lambda dt: speech_manager.silence(), 0.2)
        pyglet.clock.schedule_once(lambda dt: _setup(), 0.25)

    def update(self, delta_time: float) -> None:
        self.state_machine.update(delta_time)

    def add(self, key: str, state: State) -> None:
        self.state_machine.add(key, state)

    def remove(self, key: str) -> State:
        return self.state_machine.remove(key)

    def change(self, key: str, *args: any, **kwargs: any) -> None:
        self.state_machine.change(key, *args, **kwargs)

    def push_window_handlers(self, *args, **kwargs) -> None:
        self.pyglet_window.push_handlers(*args, **kwargs)

    def pop_window_handlers(self) -> None:
        if len(self.pyglet_window._event_stack) > 0:
            self.pyglet_window.pop_handlers()

    def close(self) -> bool:
        while len(self.pyglet_window._event_stack) > 0:
            self.pop_window_handlers()

        self.state_machine.clear()
        self.pyglet_window.close()
        del self.pyglet_window
        return EVENT_HANDLED

    def set_state(self, interrupt_speech: bool = True) -> None:
        state_key: str =  list(self.state_machine.states)[self.position]
        self.state_machine.change(state_key, interrupt_speech)

    @property
    def caption(self) -> str:
        return self._caption

    @caption.setter
    def caption(self, caption: str) -> None:
        if caption != "":
            self._caption = caption
            self.pyglet_window.set_caption(caption)
            if speech_manager.is_jaws_active():
                speech_manager.output(self.pyglet_window.caption, interrupt=False, log_message=False)
