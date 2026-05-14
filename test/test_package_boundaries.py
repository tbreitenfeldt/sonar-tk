import sonartk
import sonartk.ui
from sonartk.game_builder import BuiltMapGridGame, MapGridGameBuilder
from sonartk.ui.focusable_container import FocusableContainer
from sonartk.ui.ui_component import UIComponent
from sonartk.ui.window import Window


def test_top_level_exports_are_explicit() -> None:
    assert sonartk.__all__ == [
        "Window",
        "MapGridGameBuilder",
        "BuiltMapGridGame",
    ]
    assert sonartk.Window is Window
    assert sonartk.MapGridGameBuilder is MapGridGameBuilder
    assert sonartk.BuiltMapGridGame is BuiltMapGridGame


def test_ui_exports_are_explicit_and_primitive_only() -> None:
    assert sonartk.ui.__all__ == [
        "UIComponent",
        "FocusableContainer",
        "Window",
    ]
    assert sonartk.ui.UIComponent is UIComponent
    assert sonartk.ui.FocusableContainer is FocusableContainer
    assert sonartk.ui.Window is Window
    assert not hasattr(sonartk.ui, "MapGridGameBuilder")
