import sonartk
import sonartk.map_builder
import sonartk.orchestration
import sonartk.sound
import sonartk.ui
import pytest
from sonartk.orchestration.game_builder import (
    BuiltMapGridGame,
    MapGridGameBuilder,
)
from sonartk.orchestration.map_sound_navigation import (
    MapSoundNavigationController,
)
from sonartk.orchestration.map_object_collection import (
    MapObjectCollectionSession,
)
from sonartk.orchestration.message_action_state import MessageActionState
from sonartk.orchestration.scene_audio_state import SceneAudioState
from sonartk.orchestration.audio_controls import bind_volume_hotkeys
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
        "bind_volume_hotkeys",
        "BuiltMapGridGame",
        "MapObjectCollectionSession",
        "MessageActionState",
        "MapGridGameBuilder",
        "MapSoundNavigationController",
        "SceneAudioState",
    ]
    assert sonartk.orchestration.bind_volume_hotkeys is bind_volume_hotkeys
    assert sonartk.orchestration.BuiltMapGridGame is BuiltMapGridGame
    assert (
        sonartk.orchestration.MapObjectCollectionSession
        is MapObjectCollectionSession
    )
    assert sonartk.orchestration.MessageActionState is MessageActionState
    assert sonartk.orchestration.MapGridGameBuilder is MapGridGameBuilder
    assert (
        sonartk.orchestration.MapSoundNavigationController
        is MapSoundNavigationController
    )
    assert sonartk.orchestration.SceneAudioState is SceneAudioState


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


def test_lazy_package_exports_raise_attribute_error_for_unknown_names() -> (
    None
):
    with pytest.raises(AttributeError, match="has no attribute"):
        _ = sonartk.map_builder.not_real_export

    with pytest.raises(AttributeError, match="has no attribute"):
        _ = sonartk.orchestration.not_real_export

    with pytest.raises(AttributeError, match="has no attribute"):
        _ = sonartk.sound.not_real_export


def test_sound_package_lazy_export_loads_sound_manager_module() -> None:
    assert (
        sonartk.sound.sound_manager.__name__ == "sonartk.sound.sound_manager"
    )
