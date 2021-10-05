from typing import Callable, List
import time
import sys
import os

path = os.getcwd()

if os.path.basename(path) == "examples":
    path = os.path.dirname(path)

sys.path.append(path)

from pyglet.window import key
from pyglet.event import EVENT_HANDLED, EVENT_UNHANDLED

from audio_ui.window import Window
from audio_ui.screens import ContainerScreen
from audio_ui.screens import Dialog
from audio_ui.utils import Key
from audio_ui.utils import speech_manager
from audio_ui.elements import *

class ExampleWindow:

    def __init__(self) -> None:
        self.main_window: Window = Window()
        self.container: ContainerScreen = ContainerScreen(self.main_window)
        self.menu_bar: MenuBar = self.create_menu_bar(self.container)
        self.dialog = self.create_dialog(self.container)
        self.dialog2 = self.create_dialog2(self.dialog)

        self.container.add("button1", Button(self.container, title="Open Dialog 1"))
        self.container.add("checkbox", Checkbox(self.container, title="Update"))
        self.container.add("menu", Menu(self.container, title="Main", items=[{"start": "Start"}, {"options": "Options"}]))
        self.container.add("menu2", Menu(self.container, title="Options", has_border=True, reset_position_on_focus=False, items=[{"option1": "Option 1"}, {"option2": "Option 2"}, {"option3": "Option 3"}, {"option4": "Option 4"}]))
        self.container.add("text_box", TextBox(self.container, title="Age", allowed_chars="0123456789"))
        self.container.add("toggle_button", ToggleButton(self.container, title="Update", items=["On", "Off"]))

        self.container.key_handler.add_key_release(self.menu_bar.open_menu_bar, key=key.LALT)
        self.container.key_handler.add_key_release(self.menu_bar.open_menu_bar, key=key.RALT)
        self.container.key_handler.add_key_press(lambda: self.menu_bar.open_menu("file_menu"), key.F, [key.MOD_ALT])
        self.container.key_handler.add_key_press(lambda: self.menu_bar.open_menu("edit_menu"), key.E, [key.MOD_ALT])
        self.container.key_handler.add_key_press(lambda: self.menu_bar.open_menu("help_menu"), key.H, [key.MOD_ALT])
        self.container.key_handler.add_key_press(self.next_speech_history, key.PAGEDOWN, [key.MOD_CTRL])
        self.container.key_handler.add_key_press(self.previous_speech_history, key.PAGEUP, [key.MOD_CTRL])

        self.main_window.add("container", self.container)
        self.main_window.open_window(caption="TestWindow")

    def create_dialog(self, container: ContainerScreen) -> Dialog:
        dialog = Dialog(container)
        dialog.add("hello_world", Button(dialog, "hello world"))
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
        file_menu: Menu = Menu(parent=menu_bar, title="File", items=[{"open": "Open"}, {"save": "Save"}, {"exit": "Exit"}])
        menu_bar.add_menu("file_menu", file_menu)
        edit_menu: Menu = Menu(parent=menu_bar, title="Edit", items=[{"copy": "Copy"}, {"cut": "Cut"}, {"paste": "Paste"}])
        menu_bar.add_menu("edit_menu", edit_menu)
        help_menu: Menu = Menu(parent=menu_bar, title="Help", items=[{"get_help": "Get Help"}, {"about": "About..."}])
        menu_bar.add_menu("help_menu", help_menu)
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

ExampleWindow()