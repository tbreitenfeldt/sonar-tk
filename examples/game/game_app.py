"""Application orchestration for the map sounds example."""

from typing import Optional

from pyglet.window import key

from sonartk.map_builder.map_2d import MapTile, step_coordinates
from sonartk.map_builder.map_2d.map_object.character import Character
from sonartk.map_builder.map_2d.parser.csv_parser import CSVParser
from sonartk.orchestration.audio_lifecycle import IntroGameAudioLifecycle
from sonartk.orchestration.audio_controls import bind_volume_hotkeys
from sonartk.orchestration.game_builder import MapGridGameBuilder
from sonartk.orchestration.input_gate import InputGate
from sonartk.orchestration.map_section_gate import (
    MapSectionGate,
    MapSectionTiles,
)
from sonartk.orchestration.map_object_collection import (
    MapObjectCollectionSession,
)
from sonartk.orchestration.map_sound_navigation import (
    MapSoundNavigationController,
)
from sonartk.orchestration.message_action_state import MessageActionState
from sonartk.orchestration.player_roles import recover_players_by_role
from sonartk.orchestration.proximity_audio import (
    ProximityAudioController,
    ProximityAudioEmitter,
)
from sonartk.orchestration.scene_audio_state import SceneAudioState
from sonartk.sound import sound_manager
from sonartk.sound.openal_lite.openal import Player
from sonartk.ui.element.grid import Grid
from sonartk.ui.window import Window
from sonartk.util import Direction, speech_manager

from audio_helpers import (
    as_listener_position,
    play_spatial_sound,
    preload_audio_assets,
)
from game_config import (
    COIN_COUNT,
    COIN_SOUND,
    EXAMPLE_DIR,
    INTRO_SOUND,
    MAP_SFX_VOLUME,
    MONSTER_AMBIENT_ROLLOFF,
    MONSTER_AMBIENT_VOLUME,
    MONSTER_BLOCK_SOUND,
    MONSTER_DISTANCE_CURVE_EXPONENT,
    MONSTER_HEARING_DISTANCE_TILES,
    MONSTER_MIN_VOLUME_AT_MAX_DISTANCE,
    MONSTER_SCREAM_SOUND,
    MONSTER_SOUND,
    MONSTER_TILE_COORDINATES,
    MONSTER_GATE_TILE_COORDINATES,
    MUSIC_FADE_DURATION_SECONDS,
    MUSIC_FADE_STEP_SECONDS,
    MUSIC_SOUND,
    MUSIC_TO_SFX_VOLUME_RATIO,
    MUSIC_VOLUME_STEP,
    OUTPUT_DEVICE_WATCH_INTERVAL_SECONDS,
    PICKUP_SOUND,
    PLAYER_ROLES,
    RECOVERY_RETRY_COUNT,
    RECOVERY_STATUS_DELAY_SECONDS,
    REWARD_SOUND,
    SFX_DIR,
    SFX_VOLUME_STEP,
    SOUND_MAP,
    SWORD_SOUND,
    TERRAIN_AUDIO_PROFILES,
    tile_mapper,
)
from game_entities import Coin, Monster
from game_states import register_game_states


class MapSoundsExampleGame:
    """Owns runtime state and wiring for the map sounds example."""

    def __init__(self) -> None:
        self.start_coordinates: tuple[int, int] = (1, 2)
        self.character: Character = Character(
            "Test Character",
            self.start_coordinates,
            Direction.DOWN,
        )
        self.monster_character = Monster(
            "Monster",
            MONSTER_TILE_COORDINATES,
            Direction.LEFT,
        )

        self.players: dict[str, Player] = {}
        self.map_navigation_player: Player
        self.ambient_river_player: Player
        self.ambient_monster_player: Player
        self.coin_player: Player
        self.pickup_player: Player
        self.reward_player: Player
        self.intro_player: Player
        self.monster_announce_player: Player
        self.monster_block_player: Player
        self.sword_player: Player
        self.monster_scream_player: Player

        self.builder: MapGridGameBuilder[str]
        self.map_navigation: MapSoundNavigationController
        self.coin_session: MapObjectCollectionSession[Coin]
        self.proximity_audio: ProximityAudioController
        self.monster_gate: MapSectionGate[Monster]
        self.input_gate = InputGate()

        self.window: Window
        self.grid: Grid[MapTile]
        self.audio_lifecycle: IntroGameAudioLifecycle
        self.intro_state: SceneAudioState
        self.monster_unlocked_state: MessageActionState
        self.monster_defeated_state: SceneAudioState
        self.won_state: MessageActionState

    def run(self) -> None:
        """Build and run the game."""
        self._preload_audio_assets()
        self._setup_players()
        self._build_map_and_sessions()
        self._setup_navigation_and_ambient()
        self._build_window()
        self._register_input_handlers()
        self._setup_audio_lifecycle_and_states()
        self._setup_audio_recovery_watch()
        self._open_window()

    def _preload_audio_assets(self) -> None:
        required_sound_paths = {
            *SOUND_MAP.values(),
            INTRO_SOUND,
            MUSIC_SOUND,
            COIN_SOUND,
            PICKUP_SOUND,
            REWARD_SOUND,
            MONSTER_SOUND,
            MONSTER_BLOCK_SOUND,
            SWORD_SOUND,
            MONSTER_SCREAM_SOUND,
        }
        preload_audio_assets(required_sound_paths)

    def _setup_players(self) -> None:
        self.players = sound_manager.allocate_players_by_role(PLAYER_ROLES)
        self._bind_players_from_roles(self.players)
        self._apply_sfx_levels()

    def _bind_players_from_roles(self, players: dict[str, Player]) -> None:
        self.map_navigation_player = players["map_navigation"]
        self.ambient_river_player = players["ambient_river"]
        self.ambient_monster_player = players["ambient_monster"]
        self.coin_player = players["coin"]
        self.pickup_player = players["pickup"]
        self.reward_player = players["reward"]
        self.intro_player = players["intro"]
        self.monster_announce_player = players["monster_announce"]
        self.monster_block_player = players["monster_block"]
        self.sword_player = players["sword"]
        self.monster_scream_player = players["monster_scream"]

    def _apply_sfx_levels(self) -> None:
        sound_manager.set_sfx_volume(
            MAP_SFX_VOLUME,
            players=[
                self.map_navigation_player,
                self.ambient_river_player,
                self.ambient_monster_player,
                self.coin_player,
                self.pickup_player,
                self.reward_player,
                self.monster_block_player,
                self.sword_player,
                self.monster_scream_player,
            ],
        )

    def _build_map_and_sessions(self) -> None:
        self.builder = MapGridGameBuilder[str](
            caption="Test 2D Game"
        ).with_map(
            map_name="Test Map",
            file_name=str(EXAMPLE_DIR / "test.csv"),
            parser=CSVParser(),
            tile_mapper=tile_mapper,
            character=self.character,
        )

        self.coin_session = MapObjectCollectionSession[Coin](
            self.builder.map2d,
            object_count=COIN_COUNT,
            object_type=Coin,
            object_factory=self._coin_factory,
            object_label="coins",
            excluded_coordinates={self.start_coordinates},
        )
        self.monster_gate = MapSectionGate(
            self.builder.map2d,
            MapSectionTiles(
                open_tiles={
                    **{
                        gate_coordinates: self._create_tile("path")
                        for gate_coordinates in MONSTER_GATE_TILE_COORDINATES
                    },
                    MONSTER_TILE_COORDINATES: self._create_tile("monster"),
                },
                closed_tiles={
                    **{
                        gate_coordinates: self._create_tile("wall")
                        for gate_coordinates in MONSTER_GATE_TILE_COORDINATES
                    },
                    MONSTER_TILE_COORDINATES: self._create_tile("wall"),
                },
            ),
            section_character=self.monster_character,
            on_open=self._on_monster_gate_open,
            on_close=self._on_monster_gate_close,
        )

    def _setup_navigation_and_ambient(self) -> None:
        self.map_navigation = (
            MapSoundNavigationController.from_terrain_audio_profiles(
                map2d=self.builder.map2d,
                terrain_audio_profiles=TERRAIN_AUDIO_PROFILES,
                player=self.map_navigation_player,
                position_resolver=as_listener_position,
                ambient_player=self.ambient_river_player,
                validate_sound_map=True,
            )
        )

        monster_emitter = ProximityAudioEmitter(
            sound_path=MONSTER_SOUND,
            source_coordinates=MONSTER_TILE_COORDINATES,
            max_distance_tiles=MONSTER_HEARING_DISTANCE_TILES,
            base_volume=MONSTER_AMBIENT_VOLUME,
            min_volume_at_max_distance=MONSTER_MIN_VOLUME_AT_MAX_DISTANCE,
            distance_curve_exponent=MONSTER_DISTANCE_CURVE_EXPONENT,
            rolloff=MONSTER_AMBIENT_ROLLOFF,
            loop=True,
        )
        self.proximity_audio = ProximityAudioController(
            emitters={"monster": monster_emitter},
            players={"monster": self.ambient_monster_player},
            position_resolver=as_listener_position,
        )

    def _build_window(self) -> None:
        game = (
            self.builder.with_grid_options(
                label="",
                speak_coordinates_on_change=False,
                speak_value_on_change=False,
            )
            .on_navigation(self.on_navigation_with_coins)
            .on_border(self.map_navigation.on_border)
            .build()
        )
        self.grid = game.grid
        self.window = game.window
        self.reset_game()

    def _register_input_handlers(self) -> None:
        self.grid.key_handler.add_key_press(self.pick_up_coin, key.SPACE)
        self.grid.key_handler.add_key_press(
            self.swing_sword,
            key.SPACE,
            [key.MOD_CTRL],
        )

        bind_volume_hotkeys(
            self.window,
            music_step=MUSIC_VOLUME_STEP,
            sfx_step=SFX_VOLUME_STEP,
            couple_music_to_sfx_ratio=None,
            on_sfx_volume_changed=self.refresh_sfx_scaled_audio,
        )

    def _setup_audio_lifecycle_and_states(self) -> None:
        self.audio_lifecycle = IntroGameAudioLifecycle(
            self.stop_intro_audio,
            self.start_music_after_intro,
            self.start_game_ambience,
        )

        (
            self.intro_state,
            self.monster_unlocked_state,
            self.monster_defeated_state,
            self.won_state,
        ) = register_game_states(
            self.window,
            self.intro_player,
            self.monster_announce_player,
            self.monster_scream_player,
            self.open_monster_section,
            self.reset_for_intro,
            self.audio_lifecycle,
        )

    def _setup_audio_recovery_watch(self) -> None:
        sound_manager.register_audio_recovery_callback(self.on_audio_recovered)
        sound_manager.start_output_device_watch(
            poll_interval_seconds=OUTPUT_DEVICE_WATCH_INTERVAL_SECONDS,
            follow_default_output=True,
            recovery_retry_count=RECOVERY_RETRY_COUNT,
            status_callback=self._speak_recovery_status,
            status_delay_seconds=RECOVERY_STATUS_DELAY_SECONDS,
        )

    def _open_window(self) -> None:
        sound_manager.listener.position = as_listener_position(
            self.grid.current_coordinates
        )
        self.window.open_window(speak_current_element_on_window_focus=False)

    def _speak_recovery_status(self, message: str) -> None:
        speech_manager.output(message, interrupt=False)

    def _coin_factory(self, index: int, coordinates: tuple[int, int]) -> Coin:
        return Coin(f"coin-{index}", coordinates)

    def _create_tile(self, terrain_name: str) -> MapTile:
        profile = TERRAIN_AUDIO_PROFILES[terrain_name]
        return MapTile(terrain_name, is_passable=profile.is_passable)

    def _on_monster_gate_open(self) -> None:
        self.input_gate.unlock()
        self.map_navigation.sound_map["monster"] = str(SFX_DIR / "wall.wav")
        self.update_monster_ambient_sound(
            self.builder.map2d.character.coordinates
        )

    def _on_monster_gate_close(self) -> None:
        self.map_navigation.sound_map.pop("monster", None)
        self.ambient_monster_player.stop()
        self.ambient_monster_player.remove()

    def update_monster_ambient_sound(
        self,
        coordinates: Optional[tuple[int, int]] = None,
    ) -> bool:
        return self.proximity_audio.update(
            "monster",
            listener_coordinates=coordinates
            or self.builder.map2d.character.coordinates,
            is_active=self.monster_gate.is_open,
        )

    def update_dynamic_emitters(
        self,
        coordinates: Optional[tuple[int, int]] = None,
    ) -> None:
        origin = coordinates or self.builder.map2d.character.coordinates
        self.update_monster_ambient_sound(origin)

    def refresh_sfx_scaled_audio(self, _: float) -> None:
        current_coordinates = self.builder.map2d.character.coordinates
        self.map_navigation.update_ambient_sound(current_coordinates)
        self.update_dynamic_emitters(current_coordinates)

    def on_navigation_with_coins(
        self,
        grid: Grid[MapTile],
        direction: Direction,
    ) -> bool:
        if self.input_gate.is_locked:
            return True

        self.builder.map2d.character.directional_orientation = direction
        next_coordinates, next_tile = grid.get_next_cell(direction)
        if (
            next_tile is not None
            and not next_tile.is_passable
            and next_tile.name == "monster"
        ):
            play_spatial_sound(
                MONSTER_BLOCK_SOUND,
                next_coordinates,
                self.monster_block_player,
            )
            self.update_dynamic_emitters()
            return True

        is_handled = self.map_navigation.on_navigation(grid, direction)
        self.update_dynamic_emitters()
        if not is_handled:
            current_coordinates = self.builder.map2d.character.coordinates
            if self.coin_session.has_object_at(current_coordinates):
                play_spatial_sound(
                    COIN_SOUND,
                    current_coordinates,
                    self.coin_player,
                )

        return is_handled

    def close_monster_section(self) -> None:
        self.monster_gate.close()

    def open_monster_section(self) -> None:
        self.monster_gate.open()

    def reset_game(self) -> None:
        self.coin_session.reset()
        self.close_monster_section()
        self.input_gate.reset()
        self.builder.map2d.character.directional_orientation = Direction.DOWN

        # Keep map indices consistent by moving through Map2d; do not assign
        # character.coordinates directly during reset.
        _ = self.builder.map2d.move_character(
            self.builder.map2d.character,
            self.start_coordinates,
        )
        self.grid.current_coordinates = self.start_coordinates
        sound_manager.listener.position = as_listener_position(
            self.start_coordinates
        )

    def reset_for_intro(self) -> None:
        self.audio_lifecycle.prepare_intro()
        self.reset_game()

    def swing_sword(self) -> bool:
        if self.input_gate.is_locked:
            return True

        current_coordinates = self.builder.map2d.character.coordinates
        play_spatial_sound(
            SWORD_SOUND,
            current_coordinates,
            self.sword_player,
        )

        target_coordinates = step_coordinates(
            self.builder.map2d.character.coordinates,
            self.builder.map2d.character.directional_orientation,
            distance=1,
        )
        target_hit = self.builder.map2d.queries.get_coordinate_hit(
            target_coordinates
        )
        if (
            target_hit is not None
            and target_hit.character is self.monster_character
            and self.monster_gate.is_open
        ):
            self.input_gate.lock()
            speech_manager.output("Monster hit.")
            self.close_monster_section()
            self.window.transition_to("monster_defeated")

        return True

    def pick_up_coin(self) -> bool:
        if self.input_gate.is_locked:
            return True

        current_coordinates = self.builder.map2d.character.coordinates
        if self.coin_session.collect_at(current_coordinates) is not None:
            coins_collected = self.coin_session.collected_count
            coins_remaining = self.coin_session.remaining_count
            play_spatial_sound(
                PICKUP_SOUND,
                current_coordinates,
                self.pickup_player,
            )
            remaining_label = "coin" if coins_remaining == 1 else "coins"
            speech_manager.output(
                f"Picked up coin. Total coins: {coins_collected}. {coins_remaining} {remaining_label} left."
            )

            if coins_remaining == 0:
                play_spatial_sound(
                    REWARD_SOUND,
                    current_coordinates,
                    self.reward_player,
                )
                self.window.transition_to("monster_unlocked")

        return True

    def start_music_after_intro(self) -> None:
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

    def stop_intro_audio(self) -> None:
        self.ambient_river_player.stop()
        self.ambient_river_player.remove()
        self.ambient_monster_player.stop()
        self.ambient_monster_player.remove()

    def start_game_ambience(self) -> None:
        self.map_navigation.update_ambient_sound(
            self.builder.map2d.character.coordinates
        )
        self.update_dynamic_emitters(self.builder.map2d.character.coordinates)

    def on_audio_recovered(self) -> None:
        previous_players: dict[str, Player] = {
            "map_navigation": self.map_navigation_player,
            "ambient_river": self.ambient_river_player,
            "ambient_monster": self.ambient_monster_player,
            "coin": self.coin_player,
            "pickup": self.pickup_player,
            "reward": self.reward_player,
            "intro": self.intro_player,
            "monster_announce": self.monster_announce_player,
            "monster_block": self.monster_block_player,
            "sword": self.sword_player,
            "monster_scream": self.monster_scream_player,
        }

        self.players = recover_players_by_role(
            previous_players,
            take_recovered_player=sound_manager.take_recovered_player,
            allocate_players_by_role=sound_manager.allocate_players_by_role,
        )
        self._bind_players_from_roles(self.players)
        self._apply_sfx_levels()

        self.map_navigation.player = self.map_navigation_player
        self.map_navigation.ambient_player = self.ambient_river_player
        self.proximity_audio.players["monster"] = self.ambient_monster_player

        self.intro_state.scene_player = self.intro_player
        self.monster_unlocked_state.entry_sound_player = (
            self.monster_announce_player
        )
        self.monster_defeated_state.scene_player = self.monster_scream_player

        self.map_navigation.update_ambient_sound(
            self.builder.map2d.character.coordinates
        )
        self.update_dynamic_emitters(self.builder.map2d.character.coordinates)
