from typing import Callable, Deque
from abc import abstractmethod
from collections import deque
import time

import pyglet
from pyglet.window import key
from pyglet.event import EVENT_HANDLED

from state import State 
from state_machine import StateMachine
from utils import audio_manager
from utils import speech_manager
from utils import KeyHandler

class Tab(State):

    def __init__(self, parent: any, title: str = "", escapable: bool = False, music: str = "") -> None:
        self.parent: any = parent
        self._title: str = title
        self.escapable: bool = escapable
        self.child_window_state_machine: StateMachine = StateMachine()
        self.state_machine: StateMachine = StateMachine()
        self.music: str = music
        self.main_tab: bool = False
        self.change_state: Callable[[str, any], None] = None
        self.key_handler: KeyHandler = KeyHandler()

        if escapable:
            self.key_handler.add_key_press(self.close, key.ESCAPE)

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, title) -> None:
        self._title = title
        self.parent.set_caption(title)

    @property
    def is_tab_open(self) -> bool:
        return self.parent.is_tab_open

    @is_tab_open.setter
    def is_tab_open(self, is_tab_open) -> None:
        self.parent.is_tab_open = is_tab_open

    def setup(self, change_state: Callable[[str, any], None], interrupt_speech: bool = True) -> bool:
        self.change_state = change_state
        if self.music:
            audio_manager.load_music(self.music)
            audio_manager.play_music(loops=-1)

        self.set_caption(self._title)
        self.push_handlers(self.key_handler)
        pyglet.clock.schedule_once(lambda dt: self.show_tab(), 0.3)
        return True

    def show_tab(self) -> None:
        print("before condition")
        print(self.is_tab_open)
        if speech_manager.is_nvda_active():
            if not self.is_tab_open:
                speech_manager.output(self.title, interrupt=True, log_message=False)
                self.is_tab_open = True
                print("in condition")
                print(self.is_tab_open)
        else:
            speech_manager.output(self.title, interrupt=True, log_message=False)
            self.is_tab_open = True

    def update(self, delta_time: float) -> bool:
        if self.child_window_state_machine.size() > 0:
            return self.child_window_state_machine.update(delta_time)

    def exit(self) -> bool:
        if self.child_window_state_machine.size() > 0:
            self.child_window_state_machine.current_state.exit()

        self.pop_handlers()
        return True

    def push_child_window(self, child_window: "Tab") -> None:
        count: int = self.child_window_state_machine.size() + 1
        self.child_window_state_machine.add("child" + str(count), child_window)
        self.child_window_state_machine.change("child" + str(count))

    def pop_child_window(self) -> "Tab":
        if self.child_window_state_machine.size() > 0:
            count: int = self.child_window_state_machine.size()
            child_window: "Tab" = self.child_window_state_machine.remove("child" + str(count))
            self.setup(self.change_state)
            return child_window

        return None

    def push_handlers(self, handler: KeyHandler) -> None:
        self.parent.push_handlers(handler)

    def pop_handlers(self) -> None:
        self.parent.pop_handlers()

    def set_caption(self, caption: str) -> None:
        self.parent.set_caption(caption)

    def close(self) -> bool:
        self.parent.close_tab()
        return EVENT_HANDLED

