import sys
sys.path.append("../src")

from window import Window
from screens import ContainerScreen
from elements import *

class Test:

    def __init__(self) -> None:
        self.main_window: Window = Window()
        self.container: ContainerScreen = ContainerScreen(self.main_window)
        self.container.add("button", Button(self.container, title="Test"))
        self.container.add("checkbox", Checkbox(self.container, title="Update"))
        self.container.add("menu", Menu(self.container, title="Main", items=[{"start": "Start"}, {"options": "Options"}]))
        self.container.add("text_box", TextBox(self.container, title="Age"))
        self.container.add("toggle_button", ToggleButton(self.container, title="Update", items=["On", "Off"]))
        self.main_window.add("container", self.container)
        self.main_window.open_window(caption="Test Window")

Test()