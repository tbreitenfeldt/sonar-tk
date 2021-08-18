from typing import Callable, List
import time
import sys

sys.path.append("../src")

from pyglet.window import key
from pyglet.event import EVENT_HANDLED, EVENT_UNHANDLED

from window import Window
from screens import ContainerScreen
from screens import Dialog
from utils import Key
from utils import speech_manager
from elements import *

class Test:

    def __init__(self) -> None:
        self.main_window: Window = Window()
        self.container: ContainerScreen = ContainerScreen(self.main_window)
        self.menu_bar: MenuBar = self.create_menu_bar(self.container)
        self.dialog = self.create_dialog(self.container)
        self.dialog2 = self.create_dialog2(self.dialog)

        self.container.add("button1", Button(self.container, title="Test", callback=self.open_dialog))
        self.container.add("checkbox", Checkbox(self.container, title="Update"))
        self.container.add("menu", Menu(self.container, title="Main", items=[{"start": "Start"}, {"options": "Options"}], reset_menu_onfocus=False))
        self.container.add("text_box", TextBox(self.container, title="Age", allowed_chars="0123456789"))
        self.container.add("toggle_button", ToggleButton(self.container, title="Update", items=["On", "Off"]))

        self.container.key_handler.add_key_press(lambda: self.menu_bar.open_menu("file_menu"), key.F, [key.MOD_ALT])
        self.container.key_handler.add_key_press(lambda: self.menu_bar.open_menu("edit_menu"), key.E, [key.MOD_ALT])
        self.container.key_handler.add_key_press(lambda: self.menu_bar.open_menu("help_menu"), key.H, [key.MOD_ALT])
        self.container.key_handler.add_key_release(self.menu_bar.open_menu_bar, key.LALT)
        self.container.key_handler.add_key_release(self.menu_bar.open_menu_bar, key.RALT)
        self.container.key_handler.add_key_press(self.next_speech_history, key.PAGEDOWN, [key.MOD_CTRL])
        self.container.key_handler.add_key_press(self.previous_speech_history, key.PAGEUP, [key.MOD_CTRL])

        self.main_window.add("container", self.container)
        self.main_window.open_window(caption="TestWindow")

    def create_dialog(self, container: ContainerScreen) -> Dialog:
        dialog = Dialog(container)
        dialog.add("hello_world", Button(dialog, "hello world", callback=self.open_dialog2))
        dialog.add("checkbox", Checkbox(dialog, "test"))
        return dialog

    def open_dialog(self, change_state, value) -> None:
        self.dialog.open_dialog(caption="Save")

    def create_dialog2(self, container: ContainerScreen) -> Dialog:
        dialog = Dialog(container)
        dialog.add("open_button", Button(dialog, "Open"))
        dialog.add("checkbox", Checkbox(dialog, "Change Name"))
        return dialog

    def open_dialog2(self, change_state, value) -> None:
        self.dialog2.open_dialog(caption="Open")

    def create_menu_bar(self, parent) -> Menu:
        menu_bar: MenuBar = MenuBar(parent)
        menu_bar.add_menu(title="File", key="file_menu", items=[{"open": "Open"}, {"save": "Save"}, {"exit": "Exit"}], onsubmit_callback=self.onsubmit_file_menu)
        menu_bar.add_menu(title="Edit", key="edit_menu", items=[{"copy": "Copy"}, {"cut": "Cut"}, {"paste": "Paste"}], onsubmit_callback=self.onsubmit_edit_menu)
        menu_bar.add_menu(title="Help", key="help_menu", items=[{"get_help": "Get Help"}, {"about": "About..."}])
        return menu_bar

    def onsubmit_file_menu(self, change_state: Callable[[str, any], None], value: str) -> None:
        if value == "open":
            speech_manager.output("Open Menu Item")
        elif value == "save":
            speech_manager.output("save Menu Item")
        elif value == "exit":
            speech_manager.output("Exiting!")
            time.sleep(1)
            self.main_window.close()

    def onsubmit_edit_menu(self, change_state: Callable[[str, any], None], value: str) -> None:
        if value == "copy":
            speech_manager.output("Copy Menu Item")
        elif value == "cut":
            speech_manager.output("Cut Menu Item")
        elif value == "paste":
            speech_manager.output("Paste Menu Item")

    def next_speech_history(self) -> bool:
        line: str = speech_manager.next_history()

        if line is not None:
            speech_manager.output(line, interrupt=True, log_message=False)
            return EVENT_UNHANDLED

        return EVENT_HANDLED

    def previous_speech_history(self) -> bool:
        line: str = speech_manager.previous_history()

        if line is not None:
            speech_manager.output(line, interrupt=True, log_message=False)
        return EVENT_UNHANDLED

        return EVENT_HANDLED

Test()