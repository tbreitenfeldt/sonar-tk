# Audio Scene Flow And Volume Controls

This guide shows a reusable intro/cutscene flow and runtime volume controls using the orchestration and sound APIs.

## Terrain Audio Profiles And Validation

Use `TerrainAudioProfile` to keep tile passability, movement audio, and
ambient audio in one place. Build `MapSoundNavigationController` directly from
profiles and validate map coverage at startup.

```python
from sonartk.orchestration import (
    AmbientTileSoundConfig,
    MapSoundNavigationController,
    TerrainAudioProfile,
)

terrain_audio_profiles = {
    "path": TerrainAudioProfile(
        is_passable=True,
        movement_sound_file="audio/sfx/step_dirt.wav",
    ),
    "mud": TerrainAudioProfile(
        is_passable=True,
        movement_sound_file="audio/sfx/mud.wav",
    ),
    "wall": TerrainAudioProfile(
        is_passable=False,
        movement_sound_file="audio/sfx/wall.wav",
    ),
    "river": TerrainAudioProfile(
        is_passable=False,
        movement_sound_file="audio/sfx/wall.wav",
        ambient_sound=AmbientTileSoundConfig(
            sound_file="audio/sfx/river.wav",
            max_distance_tiles=3,
            volume=0.7,
            rolloff=1.5,
            min_volume_at_max_distance=0.18,
            distance_curve_exponent=2.2,
        ),
    ),
}

controller = MapSoundNavigationController.from_terrain_audio_profiles(
    map2d=map2d,
    terrain_audio_profiles=terrain_audio_profiles,
    player=movement_player,
    ambient_player=ambient_player,
    validate_sound_map=True,
)
```

Validation catches:
- Missing movement sounds for passable map tiles.
- Missing required `wall` collision mapping.
- Ambient tile names that are not present in the map.

## Intro-To-Game Audio Lifecycle

`IntroGameAudioLifecycle` provides a reusable pattern for keeping intro scenes
quiet and starting game music + ambience together on transition.

```python
from sonartk.orchestration import IntroGameAudioLifecycle


def stop_intro_audio() -> None:
    ambient_player.stop()
    ambient_player.remove()

audio_lifecycle = IntroGameAudioLifecycle(
    stop_intro_audio=stop_intro_audio,
    start_game_music=start_music,
    start_game_ambience=start_ambience,
)

# Before intro: silence long-running ambience.
audio_lifecycle.prepare_intro()

# On intro continue: start game audio layers together.
audio_lifecycle.start_game_audio()
```

## Preload Audio Assets At Startup

Preloading avoids first-play latency during gameplay and validates asset paths
up front.

```python
from sonartk.sound import sound_manager

SOUND_MAP = {
    "path": "audio/sfx/step_dirt.wav",
    "wall": "audio/sfx/wall.wav",
}
INTRO_SOUND = "audio/sfx/intro.wav"
MUSIC_SOUND = "audio/music/theme.ogg"
COIN_SOUND = "audio/sfx/coin.wav"

sound_manager.preload_sounds(
    {
        *SOUND_MAP.values(),
        INTRO_SOUND,
        MUSIC_SOUND,
        COIN_SOUND,
    }
)
```

If you are using `SoundPool` directly, call `sound_pool.load_many(paths)` for
the same behavior.

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
    # Optional static player, or use a resolver for dynamic/recovered players.
    sfx_player=map_sfx_player,
    music_step=0.05,
    sfx_step=0.05,
    couple_music_to_sfx_ratio=0.18,
)

# Dynamic player mode for games that can swap players after audio recovery.
bind_volume_hotkeys(
    window,
    sfx_player_resolver=lambda: players["map_navigation"],
    # Or provide the full set of SFX players to update in one step:
    # sfx_players_resolver=lambda: [
    #     players["map_navigation"],
    #     players["ambient_river"],
    #     players["coin"],
    # ],
    music_step=0.05,
    sfx_step=0.05,
    couple_music_to_sfx_ratio=None,
    on_sfx_volume_changed=lambda _: refresh_sfx_scaled_audio(),
)
```

Default bindings:
- `F7`: music up
- `F6`: music down
- `Shift+F7`: sfx up
- `Shift+F6`: sfx down

If `couple_music_to_sfx_ratio` is set, SFX changes also update music volume using `sfx * ratio`.

`on_sfx_volume_changed` is useful for recomputing emitter/base-volume math after runtime SFX changes.

## Lock Input During Non-Interactive Transitions

Use `InputGate` to suppress gameplay handlers while a transition state is active
(for example, while a defeat or victory sting plays).

```python
from sonartk.orchestration import InputGate

input_gate = InputGate()

def on_navigation(grid, direction):
    if input_gate.is_locked:
        return True
    return map_navigation.on_navigation(grid, direction)

def enter_transition() -> None:
    input_gate.lock()

def leave_transition() -> None:
    input_gate.unlock()
```

This pattern prevents race conditions where movement handlers can fire while
you are switching states.

## Reuse Distance-Based Ambience With ProximityAudioController

`ProximityAudioController` manages a set of named emitters and applies distance
based volume updates with one call per frame or event.

```python
from sonartk.orchestration import (
    ProximityAudioController,
    ProximityAudioEmitter,
)

monster_emitter = ProximityAudioEmitter(
    coordinates=(4, 12),
    sound_file="audio/sfx/monster.wav",
    max_distance_tiles=6,
    base_volume=0.85,
    min_volume_at_max_distance=0.18,
    distance_curve_exponent=2.2,
    rolloff=1.5,
    loop=True,
)

proximity_audio = ProximityAudioController(
    emitters={"monster": monster_emitter},
    players={"monster": ambient_player},
)

proximity_audio.update(
    "monster",
    listener_coordinates=map2d.character.coordinates,
    is_active=True,
)
```

Use `update_many(...)` when multiple emitters should be refreshed together.

## Directional Targeting And Tile Mutation Helpers

For one-step directional interactions (for example, melee attacks), use
`step_coordinates(...)` with the character's facing direction.

```python
from sonartk.map_builder.map_2d import step_coordinates

target = step_coordinates(
    map2d.character.coordinates,
    map2d.character.directional_orientation,
)
```

For dynamic world changes, use `set_tile(...)` or `set_tiles(...)`.

```python
from sonartk.map_builder.map_2d import MapTile

map2d.set_tile((4, 12), MapTile(name="path", is_passable=True))
map2d.set_tiles(
    {
        (3, 12): MapTile(name="path", is_passable=True),
        (4, 12): MapTile(name="path", is_passable=True),
    }
)
```

## Allocate Players By Role

Avoid positional tuples when multiple players are needed. Allocate named roles
through `sound_manager.allocate_players_by_role(...)`.

```python
from sonartk.sound import sound_manager

players = sound_manager.allocate_players_by_role(
    ["map_navigation", "ambient_river", "coin", "pickup", "reward", "intro"]
)

map_navigation_player = players["map_navigation"]
ambient_player = players["ambient_river"]
intro_player = players["intro"]
```

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

# Register post-recovery callback and follow default output device.
sound_manager.register_audio_recovery_callback(on_audio_recovered)
sound_manager.start_output_device_watch(
    poll_interval_seconds=0.5,
    follow_default_output=True,
    recovery_retry_count=1,
    status_callback=lambda message: speech_manager.output(message),
    status_delay_seconds=5.0,
)

# Map old players to recovered replacements inside your callback.
recovered = sound_manager.take_recovered_player(previous_player)
```

Prefer `on_complete` for scene flow in active UI/game loops. Blocking waits are available but can freeze input if used on the main thread.
