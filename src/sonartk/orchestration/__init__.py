from importlib import import_module
from typing import TYPE_CHECKING, Any

__all__ = [
    "AmbientTileSoundConfig",
    "IntroGameAudioLifecycle",
    "TerrainAudioProfile",
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
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
