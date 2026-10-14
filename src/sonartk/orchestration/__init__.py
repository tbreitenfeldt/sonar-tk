from importlib import import_module
from typing import TYPE_CHECKING, Any

__all__ = [
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

if TYPE_CHECKING:
    from sonartk.orchestration.volume_levels import (
        ChannelVolume,
        VolumeHotkeys,
        bind_level_hotkeys,
    )
    from sonartk.orchestration.map_interaction import (
        InteractableObject,
        MapInteractionController,
    )
    from sonartk.orchestration.map_play_session import MapPlaySession
    from sonartk.orchestration.map_definition import (
        LoadedMap,
        MapDefinition,
        MapObjectSpec,
        ObjectSound,
        load_map,
    )
    from sonartk.orchestration.flyovers import (
        FlyoverConfig,
        FlyoverController,
    )
    from sonartk.orchestration.map_screen_controller import (
        MapScreenController,
    )
    from sonartk.orchestration.map_exits import (
        MapExit,
        MapExitRegistry,
        MapSwitcher,
    )
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
    from sonartk.orchestration.scene_audio_state import SceneAudioState
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


_LAZY_MODULES = {
    "bind_volume_hotkeys": "audio_controls",
    "MapObjectCollectionSession": "map_object_collection",
    "BuiltMapGridGame": "game_builder",
    "MapGridGameBuilder": "game_builder",
    "MapExit": "map_exits",
    "MapExitRegistry": "map_exits",
    "MapSwitcher": "map_exits",
    "PagedTextState": "paged_text_state",
    "MessageActionState": "message_action_state",
    "MapSoundNavigationController": "map_sound_navigation",
    "AmbientTileSoundConfig": "map_sound_navigation",
    "TerrainAudioProfile": "map_sound_navigation",
    "IntroGameAudioLifecycle": "audio_lifecycle",
    "SceneAudioState": "scene_audio_state",
    "InputGate": "input_gate",
    "ProximityAudioController": "proximity_audio",
    "ProximityAudioEmitter": "proximity_audio",
    "recover_players_by_role": "player_roles",
    "WindowStateFlow": "state_flow",
    "MapSectionGate": "map_section_gate",
    "MapSectionTiles": "map_section_gate",
    "ChannelVolume": "volume_levels",
    "VolumeHotkeys": "volume_levels",
    "bind_level_hotkeys": "volume_levels",
    "InteractableObject": "map_interaction",
    "MapInteractionController": "map_interaction",
    "MapPlaySession": "map_play_session",
    "MapDefinition": "map_definition",
    "MapObjectSpec": "map_definition",
    "ObjectSound": "map_definition",
    "LoadedMap": "map_definition",
    "load_map": "map_definition",
    "MapScreenController": "map_screen_controller",
    "FlyoverConfig": "flyovers",
    "FlyoverController": "flyovers",
}


def __getattr__(name: str) -> Any:
    module_name = _LAZY_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(f"sonartk.orchestration.{module_name}")
    return getattr(module, name)
