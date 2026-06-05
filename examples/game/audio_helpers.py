"""Audio helper functions used by the map sounds example."""

from sonartk.sound import sound_manager
from sonartk.sound.openal_lite.openal import Player


def as_listener_position(coordinates: tuple[int, int]) -> tuple[int, int, int]:
    """Map top-down grid y to OpenAL z so north/south behaves as depth."""
    return (coordinates[0], 0, coordinates[1])


def play_spatial_sound(
    sound_path: str,
    coordinates: tuple[int, int],
    player: Player,
) -> None:
    """Play a one-shot spatial sound from map coordinates."""
    sound_manager.play_sound(
        sound_path,
        position=as_listener_position(coordinates),
        player=player,
    )


def preload_audio_assets(required_sound_paths: set[str]) -> None:
    """Preload required assets to reduce first-play latency."""
    sound_manager.preload_sounds(required_sound_paths)
