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
    AmbientTileSoundConfig,
    MapSoundNavigationController,
    TerrainAudioProfile,
)
from sonartk.orchestration.audio_lifecycle import IntroGameAudioLifecycle
from sonartk.orchestration.map_object_collection import (
    MapObjectCollectionSession,
)
from sonartk.orchestration.message_action_state import MessageActionState
from sonartk.orchestration.paged_text_state import PagedTextState
from sonartk.orchestration.map_exits import (
    MapExit,
    MapExitRegistry,
    MapSwitcher,
)
from sonartk.orchestration.scene_audio_state import SceneAudioState
from sonartk.orchestration.volume_levels import (
    ChannelVolume,
    VolumeHotkeys,
    bind_level_hotkeys,
)
from sonartk.orchestration.map_interaction import (
    InteractableObject,
    MapInteractionController,
)
from sonartk.orchestration import map_definition
from sonartk.orchestration.map_play_session import MapPlaySession
from sonartk.orchestration.flyovers import FlyoverConfig, FlyoverController
from sonartk.orchestration.map_screen_controller import MapScreenController
from sonartk.orchestration.audio_controls import bind_volume_hotkeys
from sonartk.orchestration.input_gate import InputGate
from sonartk.orchestration.proximity_audio import (
    ProximityAudioController,
    ProximityAudioEmitter,
)
from sonartk.orchestration.player_roles import recover_players_by_role
from sonartk.orchestration.state_flow import WindowStateFlow
from sonartk.orchestration.map_section_gate import (
    MapSectionGate,
    MapSectionTiles,
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
        "AmbientTileSoundConfig",
        "InputGate",
        "IntroGameAudioLifecycle",
        "MapSectionGate",
        "MapSectionTiles",
        "TerrainAudioProfile",
        "ProximityAudioController",
        "ProximityAudioEmitter",
        "recover_players_by_role",
        "WindowStateFlow",
        "bind_volume_hotkeys",
        "BuiltMapGridGame",
        "MapObjectCollectionSession",
        "MapExit",
        "MapExitRegistry",
        "MapSwitcher",
        "MessageActionState",
        "PagedTextState",
        "MapGridGameBuilder",
        "MapSoundNavigationController",
        "SceneAudioState",
        "ChannelVolume",
        "VolumeHotkeys",
        "bind_level_hotkeys",
        "InteractableObject",
        "MapInteractionController",
        "MapPlaySession",
        "MapDefinition",
        "MapObjectSpec",
        "ObjectSound",
        "LoadedMap",
        "load_map",
        "MapScreenController",
        "FlyoverConfig",
        "FlyoverController",
    ]
    assert sonartk.orchestration.ChannelVolume is ChannelVolume
    assert sonartk.orchestration.VolumeHotkeys is VolumeHotkeys
    assert sonartk.orchestration.bind_level_hotkeys is bind_level_hotkeys
    assert sonartk.orchestration.InteractableObject is InteractableObject
    assert (
        sonartk.orchestration.MapInteractionController
        is MapInteractionController
    )
    assert sonartk.orchestration.MapPlaySession is MapPlaySession
    assert sonartk.orchestration.MapDefinition is map_definition.MapDefinition
    assert sonartk.orchestration.MapObjectSpec is map_definition.MapObjectSpec
    assert sonartk.orchestration.ObjectSound is map_definition.ObjectSound
    assert sonartk.orchestration.LoadedMap is map_definition.LoadedMap
    assert sonartk.orchestration.load_map is map_definition.load_map
    assert sonartk.orchestration.MapScreenController is MapScreenController
    assert sonartk.orchestration.FlyoverConfig is FlyoverConfig
    assert sonartk.orchestration.FlyoverController is FlyoverController
    assert (
        sonartk.orchestration.AmbientTileSoundConfig is AmbientTileSoundConfig
    )
    assert (
        sonartk.orchestration.IntroGameAudioLifecycle
        is IntroGameAudioLifecycle
    )
    assert sonartk.orchestration.TerrainAudioProfile is TerrainAudioProfile
    assert sonartk.orchestration.InputGate is InputGate
    assert (
        sonartk.orchestration.ProximityAudioController
        is ProximityAudioController
    )
    assert sonartk.orchestration.ProximityAudioEmitter is ProximityAudioEmitter
    assert sonartk.orchestration.MapSectionGate is MapSectionGate
    assert sonartk.orchestration.MapSectionTiles is MapSectionTiles
    assert (
        sonartk.orchestration.recover_players_by_role
        is recover_players_by_role
    )
    assert sonartk.orchestration.WindowStateFlow is WindowStateFlow
    assert sonartk.orchestration.bind_volume_hotkeys is bind_volume_hotkeys
    assert sonartk.orchestration.BuiltMapGridGame is BuiltMapGridGame
    assert (
        sonartk.orchestration.MapObjectCollectionSession
        is MapObjectCollectionSession
    )
    assert sonartk.orchestration.MessageActionState is MessageActionState
    assert sonartk.orchestration.PagedTextState is PagedTextState
    assert sonartk.orchestration.MapExit is MapExit
    assert sonartk.orchestration.MapExitRegistry is MapExitRegistry
    assert sonartk.orchestration.MapSwitcher is MapSwitcher
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
