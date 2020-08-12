import pyglet

from utils import speech_manager
from ui.windows import Window
from ui.windows import ContainerTab
from ui.windows import Dialog
from ui.elements import Button
from ui.elements import Checkbox
from ui.elements import ToggleButton
from ui.elements import Menu
from ui.elements import TextBox

class Main:

    def __init__(self) -> None:
        self.window: Window = Window()
        tab: Tab = ContainerTab(parent=self.window, title="MTG Audio")
        self.main_tab = tab
        menu: Menu = Menu(parent=tab, title="Main", callback=self.handle_menu_selection)
        menu.add(key="start_game", item="Start Game")
        menu.add(key="online", item="Online")
        menu.add(key="options", item="Options")
        menu.add("my_text_box", TextBox(parent=menu, title="Name:", disable_up_down_keys=True))
        menu.add(key="exit", item="Exit")

        tab.add_element("dialog_button", Button(parent=tab, title="Open Dialog", callback=self.open_dialog))
        tab.add_element("tab_button", Button(parent=tab, title="Open Tab", callback=self.open_new_tab))
        tab.add_element("window_button", Button(parent=tab, title="Open Window", callback=self.open_new_window))
        tab.add_element("text_box", TextBox(parent=tab, title="Test"))
        tab.add_element("menu", menu)
        tab.add_element("checkbox", Checkbox(parent=tab, title="Hello World"))
        self.window.add_tab("parent_tab", tab)
        self.window.open_window()

    def handle_menu_selection(self, change_state, item_key: str) -> None:
        if item_key == "exit":
            speech_manager.output("closing", interrupt=True, log_message=False)
            pyglet.clock.schedule_once(lambda dt: self.window.close(), 0.5)

    def open_new_tab(self, change_state, value) -> None:
        print("Window value before new tab")
        print(self.window.is_tab_open)
        tab: Tab = ContainerTab(parent=self.window, title="New Tab Game", escapable=True)
        print("tab value after new tab")
        print(tab.is_tab_open)
        tab.add_element("button", Button(parent=tab, title="test"))
        tab.add_element("toggle_button", ToggleButton(parent=tab, title="Gender", items=["Male", "Female"]))
        self.window.add_tab("new_tab", tab)
        self.window.open_tab()

    def open_new_window(self, change_state, value) -> None:
        self.new_window: Window = Window(escapable=True)
        print(f"new_window: {self.new_window.is_tab_open}")
        tab: Tab = ContainerTab(parent=self.new_window, title="New Tab Game", escapable=True)
        tab.add_element("button", Button(parent=tab, title="test"))
        tab.add_element("toggle_button", ToggleButton(parent=tab, title="Gender", items=["Male", "Female"]))
        self.new_window.add_tab("new_tab", tab)
        self.new_window.open_window()

    def open_dialog(self, change_state, value) -> None:
        self.dialog: Dialog = Dialog(parent=self.main_tab,title="Test")
        self.dialog.add_element("toggle_button", ToggleButton(parent=self.dialog, title="Color", items=["Red", "Green", "Orange", "Yellow"]))
        self.dialog.add_element("button", Button(parent=self.dialog, title="Open Nested Dialog", callback=self.open_nested_dialog))
        self.main_tab.push_child_window(self.dialog)

    def open_nested_dialog(self, change_state, value) -> None:
        dialog: Dialog = Dialog(parent=self.dialog,title="Nested Test")
        dialog.add_element("checkbox", Checkbox(parent=dialog, title="Accept"))
        dialog.add_element("button", Button(parent=dialog, title="Cancel"))
        self.dialog.push_child_window(dialog)


if __name__ == "__main__":
    game: Main = Main()
