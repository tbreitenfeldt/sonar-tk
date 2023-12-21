import os
import sys
import time
from typing import Any, Callable, List, Optional

from pyglet.window import key

sys.path.insert(0, "../src")

try:
    from audio_ui.elements import (  # type: ignore
        Button,
        Cell,
        Checkbox,
        Element,
        Grid,
        Menu,
        MenuBar,
        TextBox,
        ToggleButton,
    )
    from audio_ui.screens import ContainerScreen, Dialog  # type: ignore
    from audio_ui.utils import Key, speech_manager  # type: ignore
    from audio_ui.window import Window  # type: ignore
except Exception:
    raise


class ExampleWindow:
    def __init__(self) -> None:
        self.main_window: Window = Window()
        self.container: ContainerScreen = ContainerScreen(self.main_window)
        self.menu_bar: MenuBar = self.create_menu_bar(self.container)
        self.save_dialog: Dialog = self.create_save_dialog(self.container)
        self.open_dialog: Dialog = self.create_open_dialog(self.save_dialog)
        self.open_dialog_button: Element = Button(
            self.container, label="Open Dialog 1"
        )
        self.checkbox: Element = Checkbox(self.container, label="Update")
        self.open_newwindow_button: Element = Button(
            self.container, label="Open a New Window"
        )
        self.grid: Grid = Grid(
            self.container, "Test", rows=10, columns=10, cell_class=Cell
        )

        self.open_dialog_button.push_handlers(
            on_submit=lambda b: self.save_dialog.open_dialog(caption="Save")
        )
        self.checkbox.push_handlers(
            on_checked=lambda c: speech_manager.output(
                "Updated Item", interrupt=False
            )
        )
        self.open_newwindow_button.push_handlers(
            on_submit=self.open_new_window
        )

        self.container.add("open_dialog_button", self.open_dialog_button)
        self.container.add("checkbox", self.checkbox)
        self.container.add("open_newwindow_button", self.open_newwindow_button)
        self.container.add(
            "menu",
            Menu(
                self.container,
                label="Main",
                items=[{"start": "Start"}, {"options": "Options"}],
            ),
        )
        self.container.add(
            "menu2",
            Menu(
                self.container,
                label="Options",
                has_border=True,
                reset_position_on_focus=False,
                items=[
                    {"option1": "Option 1"},
                    {"option2": "Option 2"},
                    {"option3": "Option 3"},
                    {"option4": "Option 4"},
                ],
            ),
        )
        self.container.add(
            "text_box",
            TextBox(self.container, label="Age", allowed_chars="0123456789"),
        )
        self.container.add(
            "toggle_button",
            ToggleButton(self.container, label="Update", items=["On", "Off"]),
        )
        self.container.add("grid", self.grid)

        self.container.key_handler.add_key_release(
            self.menu_bar.open_menu_bar, key=key.LALT
        )
        self.container.key_handler.add_key_release(
            self.menu_bar.open_menu_bar, key=key.RALT
        )
        self.container.key_handler.add_key_press(
            lambda: self.menu_bar.open_menu("file_menu"), key.F, [key.MOD_ALT]
        )
        self.container.key_handler.add_key_press(
            lambda: self.menu_bar.open_menu("edit_menu"), key.E, [key.MOD_ALT]
        )
        self.container.key_handler.add_key_press(
            lambda: self.menu_bar.open_menu("help_menu"), key.H, [key.MOD_ALT]
        )
        self.container.key_handler.add_key_press(
            self.next_speech_history, key.PAGEDOWN, [key.MOD_CTRL]
        )
        self.container.key_handler.add_key_press(
            self.previous_speech_history, key.PAGEUP, [key.MOD_CTRL]
        )

        self.main_window.add("container", self.container)
        self.main_window.open_window(caption="TestWindow")

    def create_save_dialog(self, container: ContainerScreen) -> Dialog:
        dialog = Dialog(container)
        button: Button = Button(dialog, "Open Another Dialog")
        button.push_handlers(
            on_submit=lambda b: self.open_dialog.open_dialog(caption="Open")
        )
        dialog.add("hello_world", button)
        dialog.add("checkbox", Checkbox(dialog, "test"))
        return dialog

    def create_open_dialog(self, container: Dialog) -> Dialog:
        dialog = Dialog(container)
        dialog.add("open_button", Button(dialog, "Open"))
        dialog.add("checkbox", Checkbox(dialog, "Change Name"))
        return dialog

    def create_menu_bar(self, parent: ContainerScreen) -> Menu:
        menu_bar: MenuBar = MenuBar(parent)
        file_menu: Menu = Menu(
            parent=menu_bar,
            label="File",
            items=[{"open": "Open"}, {"save": "Save"}, {"exit": "Exit"}],
        )
        menu_bar.add_menu("file_menu", file_menu)
        edit_menu: Menu = Menu(
            parent=menu_bar,
            label="Edit",
            items=[{"copy": "Copy"}, {"cut": "Cut"}, {"paste": "Paste"}],
        )
        menu_bar.add_menu("edit_menu", edit_menu)
        help_menu: Menu = Menu(
            parent=menu_bar,
            label="Help",
            items=[{"get_help": "Get Help"}, {"about": "About..."}],
        )
        menu_bar.add_menu("help_menu", help_menu)
        return menu_bar

    def onsubmit_file_menu(
        self, change_state: Callable[[str, Any], None], value: str
    ) -> None:
        if value == "open":
            speech_manager.output("Open Menu Item")
        elif value == "save":
            speech_manager.output("save Menu Item")
        elif value == "exit":
            speech_manager.output("Exiting!")
            time.sleep(1)
            self.main_window.close()

    def onsubmit_edit_menu(
        self, change_state: Callable[[str, Any], None], value: str
    ) -> None:
        if value == "copy":
            speech_manager.output("Copy Menu Item")
        elif value == "cut":
            speech_manager.output("Cut Menu Item")
        elif value == "paste":
            speech_manager.output("Paste Menu Item")

    def next_speech_history(self) -> bool:
        line: Optional[str] = speech_manager.next_history()

        if line is not None:
            speech_manager.output(line, interrupt=True, log_message=False)
            return False

        return True

    def previous_speech_history(self) -> bool:
        line: Optional[str] = speech_manager.previous_history()

        if line is not None:
            speech_manager.output(line, interrupt=True, log_message=False)
        return False

        return True

    def open_new_window(self, button: Button) -> None:
        window: Window = Window(escapable=True)
        container: ContainerScreen = ContainerScreen(window)
        container.add(
            "menu2",
            Menu(
                container,
                label="Options",
                has_border=True,
                reset_position_on_focus=False,
                items=[
                    {"option1": "Option 1"},
                    {"option2": "Option 2"},
                    {"option3": "Option 3"},
                    {"option4": "Option 4"},
                ],
            ),
        )
        container.add(
            "text_box",
            TextBox(container, label="Age", allowed_chars="0123456789"),
        )
        window.add("container", container)
        window.open_window(caption="A new window")


ExampleWindow()
