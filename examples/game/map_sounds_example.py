import sys
from pathlib import Path
from typing import Callable
from pyglet.window import key

EXAMPLE_DIR = Path(__file__).resolve().parent
PROJECT_SRC = EXAMPLE_DIR.parents[1] / "src"
AUDIO_DIR = EXAMPLE_DIR / "audio"
SFX_DIR = AUDIO_DIR / "sfx"
MUSIC_DIR = AUDIO_DIR / "music"
sys.path.insert(0, str(PROJECT_SRC))

from sonartk.orchestration.game_builder import MapGridGameBuilder  # noqa: E402
from sonartk.map_builder.map_2d import MapTile  # noqa: E402
from sonartk.map_builder.map_2d.parser.csv_parser import (  # noqa: E402
    CSVParser,
)
from sonartk.map_builder.map_2d.map_object.character import (  # noqa: E402
    Character,
)
from sonartk.map_builder.map_2d.map_object import MapObject  # noqa: E402
from sonartk.orchestration.map_sound_navigation import (  # noqa: E402
    AmbientTileSoundConfig,
    MapSoundNavigationController,
    TerrainAudioProfile,
)
from sonartk.orchestration.audio_lifecycle import (  # noqa: E402
    IntroGameAudioLifecycle,
)
from sonartk.orchestration.scene_audio_state import (  # noqa: E402
    SceneAudioState,
)
from sonartk.orchestration.message_action_state import (  # noqa: E402
    MessageActionState,
)
from sonartk.orchestration.audio_controls import (  # noqa: E402
    bind_volume_hotkeys,
)
from sonartk.orchestration.map_object_collection import (  # noqa: E402
    MapObjectCollectionSession,
)
from sonartk.ui.element.grid import Grid  # noqa: E402
from sonartk.ui.window import Window  # noqa: E402
from sonartk.util import Direction, speech_manager  # noqa: E402
from sonartk.sound import sound_manager  # noqa: E402
from sonartk.sound.openal_lite.openal import Player  # noqa: E402

INTRO_SOUND = str(SFX_DIR / "intro.wav")
MUSIC_SOUND = str(MUSIC_DIR / "music.wav")
COIN_SOUND = str(SFX_DIR / "coin.wav")
PICKUP_SOUND = str(SFX_DIR / "pickup.wav")
REWARD_SOUND = str(SFX_DIR / "reward.wav")
RIVER_AMBIENT_SOUND = str(SFX_DIR / "river.wav")
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


class Coin(MapObject):
    pass


def preload_audio_assets() -> None:
    required_sound_paths = {
        *SOUND_MAP.values(),
        INTRO_SOUND,
        MUSIC_SOUND,
        COIN_SOUND,
        PICKUP_SOUND,
        REWARD_SOUND,
        RIVER_AMBIENT_SOUND,
    }
    sound_manager.preload_sounds(required_sound_paths)


def main() -> None:
    preload_audio_assets()

    start_coordinates = (1, 2)
    character: Character = Character(
        "Test Character", start_coordinates, Direction.DOWN
    )
    players = sound_manager.allocate_players_by_role(
        [
            "map_navigation",
            "ambient_river",
            "coin",
            "pickup",
            "reward",
            "intro",
        ]
    )
    map_navigation_player = players["map_navigation"]
    ambient_river_player = players["ambient_river"]
    coin_player = players["coin"]
    pickup_player = players["pickup"]
    reward_player = players["reward"]
    intro_player = players["intro"]
    sound_manager.set_sfx_volume(
        MAP_SFX_VOLUME,
        players=[
            map_navigation_player,
            ambient_river_player,
            coin_player,
            pickup_player,
            reward_player,
        ],
    )
    builder = MapGridGameBuilder[str](caption="Test 2D Game").with_map(
        map_name="Test Map",
        file_name=str(EXAMPLE_DIR / "test.csv"),
        parser=CSVParser(),
        tile_mapper=tile_mapper,
        character=character,
    )

    def coin_factory(index: int, coordinates: tuple[int, int]) -> Coin:
        return Coin(f"coin-{index}", coordinates)

    coin_session = MapObjectCollectionSession[Coin](
        builder.map2d,
        object_count=COIN_COUNT,
        object_type=Coin,
        object_factory=coin_factory,
        excluded_coordinates={start_coordinates},
        object_label="coins",
    )
    map_navigation = MapSoundNavigationController.from_terrain_audio_profiles(
        map2d=builder.map2d,
        terrain_audio_profiles=TERRAIN_AUDIO_PROFILES,
        player=map_navigation_player,
        ambient_player=ambient_river_player,
        validate_sound_map=True,
    )

    def on_navigation_with_coins(
        grid: Grid[MapTile], direction: Direction
    ) -> bool:
        is_handled = map_navigation.on_navigation(grid, direction)
        if not is_handled:
            current_coordinates = builder.map2d.character.coordinates
            if coin_session.has_object_at(current_coordinates):
                play_spatial_sound(
                    COIN_SOUND,
                    current_coordinates,
                    coin_player,
                )

        return is_handled

    game = (
        builder.with_grid_options(
            label="",
            speak_coordinates_on_change=False,
            speak_value_on_change=False,
        )
        .on_navigation(on_navigation_with_coins)
        .on_border(map_navigation.on_border)
        .build()
    )

    grid: Grid = game.grid
    window = game.window

    def reset_game() -> None:
        coin_session.reset()

        # Keep map indices consistent by moving through Map2d; do not assign
        # character.coordinates directly during reset.
        _ = builder.map2d.move_character(
            builder.map2d.character,
            start_coordinates,
        )
        grid.current_coordinates = start_coordinates
        sound_manager.listener.position = as_listener_position(
            start_coordinates
        )

    reset_game()

    def pick_up_coin() -> bool:
        current_coordinates = builder.map2d.character.coordinates
        if coin_session.collect_at(current_coordinates) is not None:
            coins_collected = coin_session.collected_count
            coins_remaining = coin_session.remaining_count
            play_spatial_sound(
                PICKUP_SOUND,
                current_coordinates,
                pickup_player,
            )
            remaining_label = "coin" if coins_remaining == 1 else "coins"
            speech_manager.output(
                f"Picked up coin. Total coins: {coins_collected}. {coins_remaining} {remaining_label} left."
            )

            if coins_remaining == 0:
                play_spatial_sound(
                    REWARD_SOUND,
                    current_coordinates,
                    reward_player,
                )
                window.change("won")

        return True

    grid.key_handler.add_key_press(pick_up_coin, key.SPACE)

    bind_volume_hotkeys(
        window,
        sfx_player=map_navigation_player,
        music_step=MUSIC_VOLUME_STEP,
        sfx_step=SFX_VOLUME_STEP,
        couple_music_to_sfx_ratio=MUSIC_TO_SFX_VOLUME_RATIO,
    )

    def start_music_after_intro() -> None:
        sound_manager.set_music_volume(
            sound_manager.get_channel_volume("sfx") * MUSIC_TO_SFX_VOLUME_RATIO
        )
        sound_manager.play_music(
            MUSIC_SOUND,
            loop=True,
            volume=1.0,
            fade_in_seconds=MUSIC_FADE_DURATION_SECONDS,
            fade_step_seconds=MUSIC_FADE_STEP_SECONDS,
        )

    def stop_intro_audio() -> None:
        ambient_river_player.stop()
        ambient_river_player.remove()

    def start_game_ambience() -> None:
        map_navigation.update_ambient_sound(
            builder.map2d.character.coordinates
        )

    def reset_for_intro() -> None:
        audio_lifecycle.prepare_intro()
        reset_game()

    audio_lifecycle = IntroGameAudioLifecycle(
        stop_intro_audio=stop_intro_audio,
        start_game_music=start_music_after_intro,
        start_game_ambience=start_game_ambience,
    )

    register_game_states(
        window,
        intro_player,
        reset_for_intro,
        audio_lifecycle,
    )

    sound_manager.listener.position = as_listener_position(
        grid.current_coordinates
    )
    window.open_window(speak_current_element_on_window_focus=False)


def as_listener_position(coordinates: tuple[int, int]) -> tuple[int, int, int]:
    return (coordinates[0], coordinates[1], 0)


def play_spatial_sound(
    sound_path: str,
    coordinates: tuple[int, int],
    player: Player,
) -> None:
    sound_manager.play_sound(
        sound_path,
        position=as_listener_position(coordinates),
        player=player,
    )


def tile_mapper(map_value: str) -> MapTile:
    return TILE_REFERENCE[map_value]


def register_game_states(
    window: Window,
    intro_player: Player,
    reset_for_intro: Callable[[], None],
    audio_lifecycle: IntroGameAudioLifecycle,
) -> None:
    intro_state = SceneAudioState(
        window=window,
        scene_sound=INTRO_SOUND,
        scene_player=intro_player,
        next_state_key="main",
        continue_keys=[key.ENTER],
        on_continue=audio_lifecycle.start_game_audio,
    )
    won_state = MessageActionState(
        window=window,
        message="You collected all the coins and won the game. Press Enter to restart.",
        continue_keys=[key.ENTER],
        next_state_key="intro",
        on_continue=reset_for_intro,
    )
    window.add("intro", intro_state)
    window.add("won", won_state)
    window.set_start_state("intro")


if __name__ == "__main__":
    main()
