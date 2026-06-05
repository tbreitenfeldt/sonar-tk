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
    "MessageActionState",
    "MapGridGameBuilder",
    "MapSoundNavigationController",
    "SceneAudioState",
]

if TYPE_CHECKING:
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


def __getattr__(name: str) -> Any:
    if name == "bind_volume_hotkeys":
        module = import_module("sonartk.orchestration.audio_controls")
        return getattr(module, name)
    if name == "MapObjectCollectionSession":
        module = import_module("sonartk.orchestration.map_object_collection")
        return getattr(module, name)
    if name in {"BuiltMapGridGame", "MapGridGameBuilder"}:
        module = import_module("sonartk.orchestration.game_builder")
        return getattr(module, name)
    if name == "MessageActionState":
        module = import_module("sonartk.orchestration.message_action_state")
        return getattr(module, name)
    if name in {
        "MapSoundNavigationController",
        "AmbientTileSoundConfig",
        "TerrainAudioProfile",
    }:
        module = import_module("sonartk.orchestration.map_sound_navigation")
        return getattr(module, name)
    if name == "IntroGameAudioLifecycle":
        module = import_module("sonartk.orchestration.audio_lifecycle")
        return getattr(module, name)
    if name == "SceneAudioState":
        module = import_module("sonartk.orchestration.scene_audio_state")
        return getattr(module, name)
    if name == "InputGate":
        module = import_module("sonartk.orchestration.input_gate")
        return getattr(module, name)
    if name in {"ProximityAudioController", "ProximityAudioEmitter"}:
        module = import_module("sonartk.orchestration.proximity_audio")
        return getattr(module, name)
    if name == "recover_players_by_role":
        module = import_module("sonartk.orchestration.player_roles")
        return getattr(module, name)
    if name == "WindowStateFlow":
        module = import_module("sonartk.orchestration.state_flow")
        return getattr(module, name)
    if name in {"MapSectionGate", "MapSectionTiles"}:
        module = import_module("sonartk.orchestration.map_section_gate")
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
