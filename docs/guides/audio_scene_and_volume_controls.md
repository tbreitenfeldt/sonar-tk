# Audio Scene Flow And Volume Controls

This guide shows a reusable intro/cutscene flow and runtime volume controls using the orchestration and sound APIs.

## Intro Scene That Transitions On End Or Enter

```python
from pyglet.window import key

from sonartk.orchestration import SceneAudioState
from sonartk.sound import sound_manager

INTRO_SOUND = "intro.wav"
MUSIC_SOUND = "music.wav"
MUSIC_TO_SFX_RATIO = 0.18

# Reuse or allocate a player for the intro scene.
intro_player = sound_manager.player_pool.get_player()

intro_state = SceneAudioState(
    window=window,
    scene_sound=INTRO_SOUND,
    scene_player=intro_player,
    next_state_key="main",
    continue_keys=[key.ENTER],
    on_continue=lambda: sound_manager.play_music(
        MUSIC_SOUND,
        loop=True,
        volume=sound_manager.get_channel_volume("sfx") * MUSIC_TO_SFX_RATIO,
        fade_in_seconds=1.5,
        fade_step_seconds=0.05,
    ),
)

window.add("intro", intro_state)
window.position = window.state_machine.keys.index("intro")
```

Behavior:
- `SceneAudioState` starts `scene_sound` in `setup`.
- The state continues once the sound completes.
- Pressing `Enter` also continues early.
- `on_continue` is a good place to start looping background music.

## Runtime Hotkeys For Music And SFX

```python
from sonartk.orchestration import bind_volume_hotkeys
from sonartk.sound import sound_manager

map_sfx_player = sound_manager.player_pool.get_player()

# Optional: set starting SFX channel level for gameplay.
sound_manager.set_sfx_volume(1.0, players=[map_sfx_player])

bind_volume_hotkeys(
    window,
    sfx_player=map_sfx_player,
    music_step=0.05,
    sfx_step=0.05,
    couple_music_to_sfx_ratio=0.18,
)
```

Default bindings:
- `F7`: music up
- `F6`: music down
- `Shift+F7`: sfx up
- `Shift+F6`: sfx down

If `couple_music_to_sfx_ratio` is set, SFX changes also update music volume using `sfx * ratio`.

## Useful Sound Manager Helpers

```python
from sonartk.sound import sound_manager

# Channels are clamped to [0.0, 1.0].
sound_manager.set_channel_volume("music", 0.4)
sound_manager.set_channel_volume("sfx", 0.8)

# Fade currently playing music to target channel volume.
sound_manager.set_music_volume(0.3, fade_seconds=1.0, fade_step_seconds=0.05)

# Apply effective SFX channel volume to an existing player.
sound_manager.apply_sfx_volume(player)

# Non-blocking completion callback for one-shot sounds.
sound_manager.play_sound(
    "chime.wav",
    on_complete=lambda _: print("done"),
    completion_poll_interval_seconds=0.05,
)
```

Prefer `on_complete` for scene flow in active UI/game loops. Blocking waits are available but can freeze input if used on the main thread.
