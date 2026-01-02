from typing import Any, Optional, cast
import sys

import pyglet.window
from pyglet.event import EventDispatcher
from pyglet.window import key

from sonartk.ui.screen.screen import Screen
from sonartk.util.state import State
from sonartk.util.state_machine import StateMachine
from sonartk.util.key_handler import KeyHandler
from sonartk.util import speech_manager

pyglet.options["debug_gl"] = False
pyglet.options["shadow_window"] = False


class Window(EventDispatcher):
    def __init__(
        self,
        caption: str = "",
        escapable: bool = False,
        parent: Optional["Window"] = None,
        close_children_on_close: bool = True,
    ):
        self.escapable: bool = escapable
        self.parent: Optional["Window"] = parent
        self.close_children_on_close: bool = close_children_on_close
        self.children: list["Window"] = []
        self.state_machine: StateMachine = StateMachine()
        self.position: int = 0
        self.key_handler: KeyHandler = KeyHandler()
        self._caption: str = caption
        self.is_open: bool = False

        # Register with parent if provided
        if self.parent is not None:
            self.parent.children.append(self)

        self.bind_keys()

    def bind_keys(self) -> None:
        if not self.escapable:
            # Remove pyglet default behavior of closing on escape
            self.key_handler.add_key_press(lambda: True, key.ESCAPE)

        self.key_handler.add_key_press(self.close, key.W, [key.MOD_CTRL])

    def open_window(
        self,
        caption: str = "",
        width: int = 640,
        height: int = 480,
        fullscreen: bool = False,
    ) -> None:
        if not caption and not self._caption:
            raise ValueError("No caption was set for the window")
        if caption:
            self._caption = caption

        self.pyglet_window = pyglet.window.Window(
            caption=self._caption,
            width=width,
            height=height,
            fullscreen=fullscreen,
            visible=False,
        )

        self.push_window_handlers(on_close=self.close)
        self.push_window_handlers(on_activate=self.on_window_activate)
        self.push_window_handlers(self.key_handler)

        pyglet.clock.schedule_interval(self.update, 0.01)
        self.setup()
        self.pyglet_window.set_visible()
        pyglet.app.run()

    def on_window_activate(self) -> bool:
        if self.is_open:
            if hasattr(self.state_machine.current_state, "active_element"):
                screen: Screen = cast(Screen, self.state_machine.current_state)
                element: State = screen.active_element

                while element is not None and hasattr(
                    element, "active_element"
                ):
                    element = element.active_element

                if element is not None and hasattr(element, "name"):
                    pyglet.clock.schedule_once(
                        lambda dt: speech_manager.output(
                            element.name, interrupt=False, log_message=False
                        ),
                        0.25,
                    )

            return True

        self.is_open = True
        return False

    def setup(self) -> None:
        pyglet.clock.schedule_once(lambda dt: self.set_state(), 0.25)

    def update(self, delta_time: float) -> None:
        self.dispatch_event("on_update", self, delta_time)
        self.state_machine.update(delta_time)

    def add(self, key: str, state: State) -> None:
        self.state_machine.add(key, state)

    def remove(self, key: str) -> Optional[State]:
        return self.state_machine.remove(key)

    def change(self, key: str, *args: Any, **kwargs: Any) -> None:
        self.state_machine.change(key, *args, **kwargs)

    def push_window_handlers(self, *args: Any, **kwargs: Any) -> None:
        self.pyglet_window.push_handlers(*args, **kwargs)

    def pop_window_handlers(self) -> None:
        try:
            self.pyglet_window.pop_handlers()
        except AssertionError:
            pass

    def close(self) -> bool:
        # Close children if configured
        if self.close_children_on_close:
            for child in self.children[:]:
                if hasattr(child, "pyglet_window"):
                    child.close()

        # Remove from parent's children list
        if self.parent is not None and self in self.parent.children:
            self.parent.children.remove(self)

        self.dispatch_event("on_close", self)
        while len(self.pyglet_window._event_stack) > 0:
            self.pop_window_handlers()

        self.state_machine.exit()
        self.state_machine.clear()
        self.pyglet_window.close()
        del self.pyglet_window

        if "sonartk.sound.sound_manager" in sys.modules:
            from sonartk.sound import sound_manager

            sound_manager.cleanup()

        return True

    def set_state(self, interrupt_speech: bool = True) -> None:
        if not self.state_machine.is_empty():
            state_key: str = self.state_machine.keys[self.position]
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
                speech_manager.output(
                    self.pyglet_window.caption,
                    interrupt=False,
                    log_message=False,
                )


Window.register_event_type("on_update")
Window.register_event_type("on_close")
