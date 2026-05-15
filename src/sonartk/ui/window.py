from typing import Any, Optional, cast
import sys

import pyglet.window
from pyglet.event import EventDispatcher
from pyglet.window import key

from sonartk.ui.focusable_container import FocusableContainer
from sonartk.ui.ui_component import UIComponent
from sonartk.util.state import State
from sonartk.util.state_machine import StateMachine
from sonartk.util.key_handler import KeyHandler
from sonartk.util import speech_manager

pyglet.options.debug_gl = False
pyglet.options.shadow_window = False


class Window(UIComponent, EventDispatcher):
    def __init__(
        self,
        caption: str = "",
        escapable: bool = False,
        parent: Optional["Window"] = None,
        close_children_on_close: bool = True,
    ):
        self.escapable: bool = escapable
        self.parent = parent
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
        """Register window-level keyboard shortcuts and escape behavior."""
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
        speak_current_element_on_window_focus: bool = True,
    ) -> None:
        """Create, initialize, and start the pyglet event loop for this window."""
        if not caption and not self._caption:
            raise ValueError("No caption was set for the window")
        if caption:
            self._caption = caption

        self.pyglet_window = pyglet.window.Window(  # type: ignore[abstract]
            caption=self._caption,
            width=width,
            height=height,
            fullscreen=fullscreen,
            visible=False,
        )

        self.push_window_handlers(on_close=self.close)
        self.push_window_handlers(self.key_handler)

        if speak_current_element_on_window_focus:
            self.push_window_handlers(on_activate=self.on_window_activate)

        self.dispatch_event("on_open", self)
        pyglet.clock.schedule_interval(self.update, 0.01)
        self.setup()
        self.pyglet_window.set_visible()
        pyglet.app.run()

    def on_window_activate(self) -> bool:
        """Handle window activation - announce the currently focused element."""
        if self.is_open:
            current_state: State = self.state_machine.current_state

            # Drill down to find the deepest active element
            if hasattr(current_state, "active_element"):
                element: Optional[FocusableContainer] = cast(
                    FocusableContainer, current_state
                )

                while element is not None and hasattr(
                    element, "active_element"
                ):
                    element = getattr(element, "active_element", None)  # type: ignore[assignment]

                if element is not None and hasattr(element, "name"):
                    element_name = getattr(element, "name")
                    pyglet.clock.schedule_once(
                        lambda dt: speech_manager.output(
                            element_name, interrupt=False, log_message=False
                        ),
                        0.25,
                    )

            return True

        self.is_open = True
        return False

    def setup(self) -> None:
        """Schedule initial state activation after the window opens."""
        pyglet.clock.schedule_once(lambda dt: self.set_state(), 0.25)

    def update(self, delta_time: float) -> None:
        """Dispatch update events and advance the active state each frame."""
        self.dispatch_event("on_update", self, delta_time)
        self.state_machine.update(delta_time)

    def add(self, key: str, state: State) -> None:
        """Register a named state in this window's state machine."""
        self.state_machine.add(key, state)

    def remove(self, key: str) -> Optional[State]:
        """Remove and return a previously registered state by key."""
        return self.state_machine.remove(key)

    def change(self, key: str, *args: Any, **kwargs: Any) -> None:
        """Switch to another registered state, forwarding optional arguments."""
        self.state_machine.change(key, *args, **kwargs)

    def get_window(self) -> "Window":
        """Return this window (base case for parent chain traversal)."""
        return self

    def push_window_handlers(self, *args: Any, **kwargs: Any) -> None:
        """Push one or more event handlers onto the pyglet handler stack."""
        self.pyglet_window.push_handlers(*args, **kwargs)

    def pop_window_handlers(self) -> None:
        """
        Pop a handler from the event stack.

        Raises:
            RuntimeError: If attempting to pop from an empty stack
        """
        if len(self.pyglet_window._event_stack) == 0:
            raise RuntimeError(
                "Attempted to pop handler from empty stack! "
                "More pops than pushes detected. This usually means "
                "a state's exit() method is popping handlers it didn't push."
            )
        self.pyglet_window.pop_handlers()

    def get_handler_stack_size(self) -> int:
        """Get the current number of handlers on the event stack."""
        return len(self.pyglet_window._event_stack)

    def check_handler_leaks(self, expected_count: int = 3) -> None:
        """
        Check for handler leaks and log warnings.

        Args:
            expected_count: Number of handlers expected to be on the stack.
                Default is 3 (on_close, on_activate, window key_handler).

        Call this in development/debug mode after state transitions to
        detect states that forgot to pop their handlers.
        """
        actual = self.get_handler_stack_size()
        if actual > expected_count:
            leaked = actual - expected_count
            import sys

            print(
                f"WARNING: Possible handler leak detected! "
                f"Expected {expected_count} handlers, found {actual} "
                f"({leaked} leaked).",
                file=sys.stderr,
            )

    def close(self) -> bool:
        # Close children if configured
        """Close this window, clean up states and handlers, and optionally close child windows."""
        if self.close_children_on_close:
            for child in self.children[:]:
                if hasattr(child, "pyglet_window"):
                    child.close()

        # Remove from parent's children list
        if self.parent and hasattr(self.parent, "children") and self in self.parent.children:  # type: ignore[attr-defined]
            self.parent.children.remove(self)  # type: ignore[attr-defined]

        self.dispatch_event("on_close", self)

        # Exit states BEFORE clearing handlers so they can clean up properly
        self.state_machine.exit()
        self.state_machine.clear()

        # Pop all remaining handlers - use pyglet's pop directly since we're cleaning up
        while len(self.pyglet_window._event_stack) > 0:
            self.pyglet_window.pop_handlers()

        self.pyglet_window.close()
        del self.pyglet_window

        if "sonartk.sound.sound_manager" in sys.modules:
            sound_manager = sys.modules["sonartk.sound.sound_manager"]
            cleanup = getattr(sound_manager, "cleanup", None)
            if callable(cleanup):
                cleanup()

        return True

    def set_state(self, interrupt_speech: bool = True) -> None:
        """Activate the state at the current window position when available."""
        if not self.state_machine.is_empty():
            state_key: str = self.state_machine.keys[self.position]
            self.state_machine.change(state_key, interrupt_speech)

    @property
    def caption(self) -> str:
        """Return the current window caption."""
        return self._caption

    @caption.setter
    def caption(self, caption: str) -> None:
        """Return the current window caption."""
        if caption != "":
            self._caption = caption
            self.pyglet_window.set_caption(caption)
            if speech_manager.is_jaws_active():
                speech_manager.output(
                    self.pyglet_window.caption,
                    interrupt=False,
                    log_message=False,
                )


Window.register_event_type("on_open")
Window.register_event_type("on_update")
Window.register_event_type("on_close")
