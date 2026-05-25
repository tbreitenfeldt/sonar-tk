import sys
from pathlib import Path
from typing import Callable
from pyglet.window import key

EXAMPLE_DIR = Path(__file__).resolve().parent
PROJECT_SRC = EXAMPLE_DIR.parents[1] / "src"
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
    MapSoundNavigationController,
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

TILE_REFERENCE: dict[str, MapTile] = {
    "0": MapTile("path"),
    "1": MapTile("wall", is_passable=False),
}

SOUND_MAP = {
    "path": str(EXAMPLE_DIR / "step_dirt.wav"),
    "wall": str(EXAMPLE_DIR / "wall.wav"),
}
INTRO_SOUND = str(EXAMPLE_DIR / "intro.wav")
MUSIC_SOUND = str(EXAMPLE_DIR / "music.wav")
COIN_SOUND = str(EXAMPLE_DIR / "coin.wav")
PICKUP_SOUND = str(EXAMPLE_DIR / "pickup.wav")
REWARD_SOUND = str(EXAMPLE_DIR / "reward.wav")
MAP_SFX_VOLUME = 1.0
MUSIC_TO_SFX_VOLUME_RATIO = 0.14
MUSIC_FADE_DURATION_SECONDS = 1.5
MUSIC_FADE_STEP_SECONDS = 0.05
MUSIC_VOLUME_STEP = 0.1
SFX_VOLUME_STEP = 0.1
COIN_COUNT = 3


class Coin(MapObject):
    pass


def main() -> None:
    start_coordinates = (1, 9)
    character: Character = Character(
        "Test Character", start_coordinates, Direction.DOWN
    )
    (
        map_navigation_player,
        coin_player,
        pickup_player,
        reward_player,
        intro_player,
    ) = allocate_players()
    sound_manager.set_sfx_volume(
        MAP_SFX_VOLUME,
        players=[
            map_navigation_player,
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
    map_navigation = MapSoundNavigationController(
        map2d=builder.map2d,
        sound_map=SOUND_MAP,
        player=map_navigation_player,
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

    register_game_states(
        window,
        intro_player,
        reset_game,
        start_music_after_intro,
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


def allocate_players() -> tuple[Player, Player, Player, Player, Player]:
    return (
        sound_manager.player_pool.get_player(),
        sound_manager.player_pool.get_player(),
        sound_manager.player_pool.get_player(),
        sound_manager.player_pool.get_player(),
        sound_manager.player_pool.get_player(),
    )


def register_game_states(
    window: Window,
    intro_player: Player,
    reset_game: Callable[[], None],
    start_music_after_intro: Callable[[], None],
) -> None:
    intro_state = SceneAudioState(
        window=window,
        scene_sound=INTRO_SOUND,
        scene_player=intro_player,
        next_state_key="main",
        continue_keys=[key.ENTER],
        on_continue=start_music_after_intro,
    )
    won_state = MessageActionState(
        window=window,
        message="You collected all the coins and won the game. Press Enter to restart.",
        continue_keys=[key.ENTER],
        next_state_key="intro",
        on_continue=reset_game,
    )
    window.add("intro", intro_state)
    window.add("won", won_state)
    window.set_start_state("intro")


if __name__ == "__main__":
    main()
