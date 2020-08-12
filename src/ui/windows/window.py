import pyglet
from pyglet.event import EVENT_UNHANDLED, EVENT_HANDLED
from pyglet.window import key
from accessible_output2.outputs.auto import Auto

from state_machine import StateMachine
from utils import KeyHandler
from utils import speech_manager
from ui.windows import Tab

pyglet.options['debug_gl'] = False

class Window:

    def __init__(self, escapable: bool = False):
        self.escapable: bool = escapable
        self.is_tab_open: bool = False
        self.tab_state_machine: StateMachine = StateMachine()
        self.position: int = 0
        self.key_handler: KeyHandler = KeyHandler()

    def open_window(self, width: int = 640, height: int = 480, resizable: bool =False, fullscreen: bool = False) -> None:
        self.screen: pyglet.window.Window = pyglet.window.Window(width, height, resizable=resizable, fullscreen=fullscreen)
        pyglet.clock.schedule_once(lambda dt: speech_manager.silence(), 0.15)
        pyglet.clock.schedule_interval(self.update, 0.01)
        self.bind_keys()
        self.push_handlers(self.key_handler)

        if len(self.tab_state_machine.states) > 0:
            self.open_tab()

        pyglet.app.run()

    def bind_keys(self) -> None:
        if not self.escapable:
            self.key_handler.add_key_press(lambda: EVENT_HANDLED, key.ESCAPE)  # Remove pyglet default behavior of closing on escape

        self.key_handler.add_key_press(self.close, key.W, [key.MOD_CTRL])
        self.key_handler.add_key_press(self.next_tab, key.TAB, [key.MOD_CTRL])
        self.key_handler.add_key_press(self.previous_tab, key.TAB, [key.MOD_CTRL, key.MOD_SHIFT])
        self.key_handler.add_key_press(self.close_tab, key.F4, [key.MOD_CTRL])

    def update(self, delta_time: float) -> None:
        self.tab_state_machine.update(delta_time)

    def open_tab(self) -> None:
        self.set_state()

    def add_tab(self, key: str, tab: Tab) -> None:
        if self.tab_state_machine.size() == 0:
            tab.main_tab = True

        self.tab_state_machine.add(key, tab)
        self.position = self.tab_state_machine.size() - 1

    def remove_tab(self, key:str) -> Tab:
        if not self.tab_state_machine.states[key].main_tab:
            removed_tab: Tab =  self.tab_state_machine.remove(key)

            if self.position == self.tab_state_machine.size():
                self.position -= 1
            self.set_state()
            return removed_tab

        return None

    def next_tab(self) -> bool:
        if self.tab_state_machine.size() > 1:
            self.position = (self.position  + 1) % self.tab_state_machine.size()
            self.set_state()
            return EVENT_HANDLED

        return EVENT_UNHANDLED

    def previous_tab(self) -> bool:
        if self.tab_state_machine.size() > 1:
            self.position = (self.position - 1) % self.tab_state_machine.size()
            self.set_state()
            return EVENT_HANDLED

        return EVENT_UNHANDLED

    def close_tab(self) -> bool:
        if self.tab_state_machine.size() > 1:
            self.remove_tab(self.tab_state_machine.current_state.state_key)
            return EVENT_HANDLED
        elif self.tab_state_machine.size() == 1 and self.tab_state_machine.current_state.escapable:
            self.close()
            return EVENT_HANDLED

        return EVENT_UNHANDLED

    def set_state(self, interrupt_speech: bool = True) -> None:
        state_key: str =  list(self.tab_state_machine.states)[self.position]
        self.tab_state_machine.change(state_key, interrupt_speech)

    def push_handlers(self, handler: KeyHandler) -> None:
        self.screen.push_handlers(handler)

    def pop_handlers(self) -> None:
        if len(self.screen._event_stack) > 1:
            self.screen.pop_handlers()

    def set_caption(self, caption: str) -> None:
        self.screen.set_caption(caption)

    def close(self) -> None:
        self.screen.close()
