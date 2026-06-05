"""State registration for the map sounds example."""

from typing import Callable

from pyglet.window import key

from sonartk.orchestration.audio_lifecycle import IntroGameAudioLifecycle
from sonartk.orchestration.state_flow import WindowStateFlow
from sonartk.orchestration.message_action_state import MessageActionState
from sonartk.orchestration.scene_audio_state import SceneAudioState
from sonartk.sound.openal_lite.openal import Player
from sonartk.ui.window import Window

from game_config import INTRO_SOUND, MONSTER_SCREAM_SOUND, MONSTER_SOUND


def register_game_states(
    window: Window,
    intro_player: Player,
    monster_announce_player: Player,
    monster_scream_player: Player,
    open_monster_section: Callable[[], None],
    reset_for_intro: Callable[[], None],
    audio_lifecycle: IntroGameAudioLifecycle,
) -> tuple[
    SceneAudioState,
    MessageActionState,
    SceneAudioState,
    MessageActionState,
]:
    """Register game flow states and return created state instances."""
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
        message="You destroyed the monster and won the game. Press Enter to restart.",
        continue_keys=[key.ENTER],
        next_state_key="intro",
        on_continue=reset_for_intro,
    )
    monster_unlocked_state = MessageActionState(
        window=window,
        message="You collected all 3 coins. The monster area is now open. Press Enter to continue.",
        entry_sound=MONSTER_SOUND,
        entry_sound_player=monster_announce_player,
        continue_keys=[key.ENTER],
        next_state_key="main",
        on_continue=open_monster_section,
    )
    monster_defeated_state = SceneAudioState(
        window=window,
        scene_sound=MONSTER_SCREAM_SOUND,
        scene_player=monster_scream_player,
        next_state_key="won",
    )
    WindowStateFlow(window).add_many(
        {
            "intro": intro_state,
            "monster_unlocked": monster_unlocked_state,
            "monster_defeated": monster_defeated_state,
            "won": won_state,
        }
    ).start_at("intro")
    return (
        intro_state,
        monster_unlocked_state,
        monster_defeated_state,
        won_state,
    )
