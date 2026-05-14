import sonartk
import sonartk.orchestration
import sonartk.ui
from sonartk.orchestration.game_builder import (
    BuiltMapGridGame,
    MapGridGameBuilder,
)
from sonartk.orchestration.map_sound_navigation import (
    MapSoundNavigationController,
)
from sonartk.ui.focusable_container import FocusableContainer
from sonartk.ui.ui_component import UIComponent
from sonartk.ui.window import Window


def test_top_level_exports_are_explicit() -> None:
    assert sonartk.__all__ == [
        "Window",
        "MapGridGameBuilder",
        "BuiltMapGridGame",
        "MapSoundNavigationController",
    ]
    assert sonartk.Window is Window
    assert sonartk.MapGridGameBuilder is MapGridGameBuilder
    assert sonartk.BuiltMapGridGame is BuiltMapGridGame
    assert sonartk.MapSoundNavigationController is MapSoundNavigationController


def test_orchestration_exports_are_explicit() -> None:
    assert sonartk.orchestration.__all__ == [
        "BuiltMapGridGame",
        "MapGridGameBuilder",
        "MapSoundNavigationController",
    ]
    assert sonartk.orchestration.BuiltMapGridGame is BuiltMapGridGame
    assert sonartk.orchestration.MapGridGameBuilder is MapGridGameBuilder
    assert (
        sonartk.orchestration.MapSoundNavigationController
        is MapSoundNavigationController
    )


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
