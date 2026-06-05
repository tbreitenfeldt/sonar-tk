"""Configuration and static mappings for the map sounds example game."""

from pathlib import Path

from sonartk.map_builder.map_2d import MapTile
from sonartk.orchestration.map_sound_navigation import (
    AmbientTileSoundConfig,
    MapSoundNavigationController,
    TerrainAudioProfile,
)

EXAMPLE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = EXAMPLE_DIR / "audio"
SFX_DIR = AUDIO_DIR / "sfx"
MUSIC_DIR = AUDIO_DIR / "music"

INTRO_SOUND = str(SFX_DIR / "intro.wav")
MUSIC_SOUND = str(MUSIC_DIR / "music.wav")
COIN_SOUND = str(SFX_DIR / "coin.wav")
PICKUP_SOUND = str(SFX_DIR / "pickup.wav")
REWARD_SOUND = str(SFX_DIR / "reward.wav")
RIVER_AMBIENT_SOUND = str(SFX_DIR / "river.wav")
MONSTER_SOUND = str(SFX_DIR / "monster.wav")
MONSTER_BLOCK_SOUND = str(SFX_DIR / "monster_block.wav")
SWORD_SOUND = str(SFX_DIR / "sword.wav")
MONSTER_SCREAM_SOUND = str(SFX_DIR / "monster_scream.wav")

MAP_SFX_VOLUME = 1.0
MUSIC_TO_SFX_VOLUME_RATIO = 0.14
MUSIC_FADE_DURATION_SECONDS = 1.5
MUSIC_FADE_STEP_SECONDS = 0.05
MUSIC_VOLUME_STEP = 0.1
SFX_VOLUME_STEP = 0.1
COIN_COUNT = 3

RIVER_HEARING_DISTANCE_TILES = 3
RIVER_AMBIENT_VOLUME = 0.7
RIVER_AMBIENT_ROLLOFF = 1.5
RIVER_MIN_VOLUME_AT_MAX_DISTANCE = 0.18
RIVER_DISTANCE_CURVE_EXPONENT = 2.2

MONSTER_HEARING_DISTANCE_TILES = 6
MONSTER_AMBIENT_VOLUME = 0.85
MONSTER_AMBIENT_ROLLOFF = 1.5
MONSTER_MIN_VOLUME_AT_MAX_DISTANCE = 0.18
MONSTER_DISTANCE_CURVE_EXPONENT = 2.2

OUTPUT_DEVICE_WATCH_INTERVAL_SECONDS = 0.5
RECOVERY_RETRY_COUNT = 1
RECOVERY_STATUS_DELAY_SECONDS = 5.0

PLAYER_ROLES: tuple[str, ...] = (
    "map_navigation",
    "ambient_river",
    "ambient_monster",
    "coin",
    "pickup",
    "reward",
    "intro",
    "monster_announce",
    "monster_block",
    "sword",
    "monster_scream",
)

MONSTER_GATE_TILE_COORDINATES: tuple[tuple[int, int], ...] = ((3, 12),)
MONSTER_TILE_COORDINATES: tuple[int, int] = (4, 12)

TERRAIN_AUDIO_PROFILES: dict[str, TerrainAudioProfile] = {
    "path": TerrainAudioProfile(
        is_passable=True,
        movement_sound_file=str(SFX_DIR / "step_dirt.wav"),
    ),
    "mud": TerrainAudioProfile(
        is_passable=True,
        movement_sound_file=str(SFX_DIR / "mud.wav"),
    ),
    "wall": TerrainAudioProfile(
        is_passable=False,
        movement_sound_file=str(SFX_DIR / "wall.wav"),
    ),
    "river": TerrainAudioProfile(
        is_passable=False,
        movement_sound_file=str(SFX_DIR / "wall.wav"),
        ambient_sound=AmbientTileSoundConfig(
            sound_file=RIVER_AMBIENT_SOUND,
            max_distance_tiles=RIVER_HEARING_DISTANCE_TILES,
            volume=RIVER_AMBIENT_VOLUME,
            rolloff=RIVER_AMBIENT_ROLLOFF,
            loop=True,
            min_volume_at_max_distance=RIVER_MIN_VOLUME_AT_MAX_DISTANCE,
            distance_curve_exponent=RIVER_DISTANCE_CURVE_EXPONENT,
        ),
    ),
    "monster": TerrainAudioProfile(
        is_passable=False,
        movement_sound_file=str(SFX_DIR / "wall.wav"),
    ),
}

MAP_VALUE_TO_TERRAIN_NAME: dict[str, str] = {
    "0": "path",
    "1": "wall",
    "2": "river",
    "3": "mud",
}

TILE_REFERENCE = (
    MapSoundNavigationController.build_tile_reference_from_profiles(
        MAP_VALUE_TO_TERRAIN_NAME,
        TERRAIN_AUDIO_PROFILES,
    )
)

SOUND_MAP, AMBIENT_SOUND_MAP = (
    MapSoundNavigationController.build_audio_maps_from_profiles(
        TERRAIN_AUDIO_PROFILES
    )
)


def tile_mapper(map_value: str) -> MapTile:
    """Map CSV values to terrain tile definitions."""
    return TILE_REFERENCE[map_value]
