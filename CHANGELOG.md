# Changelog

## [Unreleased]

### Fixed

* **Looping ambience lost after an output-device change**: loops that the dying device reported as stopped were skipped during recovery. Any loop that was never removed is now restored.
* **Unplugging or plugging in headphones mid-game**: output-device monitoring now starts automatically when `Window.open_window` runs (`monitor_audio_device=False` opts out, and an earlier `start_output_device_watch` call keeps its own settings). After a device change every `Player`, including ones created directly by game code, is rebuilt in place, so objects a game already holds keep working and looping sounds resume with no recovery callback or role rebinding. `sound_manager.ensure_output_device_watch()` and `Player.rebind()` / `PlayerPool.adopt_active_player()` support this.
* **All audio skipping, and pops, while walking past looping sounds**: `batch_updates` used `alcSuspendContext`, which in OpenAL Soft stops the mixer, so every step briefly paused all audio and produced pops. It now uses `AL_SOFT_deferred_updates` (`alDeferUpdatesSOFT` / `alProcessUpdatesSOFT`), which still applies the listener and source changes together but keeps the mixer running. Deferring still popped with several looping sources in practice, so it is off by default; `sound_manager.set_defer_updates(True)` turns it on, and otherwise each step's changes are applied one by one.
* **Occasional one-sided pop while walking**: `MapSoundNavigationController` moved the listener and then each source in separate calls, so the mixer could render a block with every source one tile off, heard as a crackle in the ear opposite the movement. Each step is now applied as a single batched update.
* **Ambience loop drifting with the player**: `ChannelLoop` loops sat at the spot where they started, so every step changed their distance and gain, heard as faint crackle. They are now relative to the listener.
* **Pop as a nearby object is passed**: an object's looping sound jumped to its new position after each step, so a source passed at a tile's distance swung 90 degrees or more around the listener in one step, heard as a pop. The new `proximity_glide_seconds` option (on `MapScreenController`, `MapPlaySession` and `glide_seconds` on `ProximityAudioController`, default 0) glides each playing sound from where it was heard relative to the listener to its new place. It also applies to the tile ambient (`MapSoundNavigationController(glide_seconds=...)`), where the nearest ambient tile, such as the ocean along a shore, changes as you walk.
* **Listener orientation lost after a device change**: recovery rebuilt the listener with the default orientation. The `at` and `up` vectors are now restored along with the position.

### Changed

* **Map sessions orient the listener**: `MapPlaySession.start_audio` now faces the listener north with z up (`MAP_LISTENER_ORIENTATION`), matching map coordinates (x east, y north, z up). Heights such as `FlyoverController` flyers now sound overhead instead of behind, and north sounds ahead instead of above. Pass `listener_orientation=None` to keep the previous behaviour.
* **PagedTextState** now also advances on Space by default (previously only Enter).

### Added

* **Door beacons**: `MapScreenController(door_beacon=ObjectSound(...))` loops a positional sound at every exit that has its own sound (a door), so doors can be found by ear and told apart from ordinary exits, which keep using `exit_sound`.
* **Elevation and ramps**: `MapDocument.elevations` takes `ElevationArea(area, z, rises_toward=None)` entries (flat at `z`, or a ramp whose lowest edge is `z` and rises one per tile toward `north`/`south`/`east`/`west`; later areas win). `Map2d.elevation_at` / `set_elevations` expose heights, and `Map2d.steep_steps()` lists passable neighbours more than `MAX_STEP_HEIGHT` apart so games can validate maps. `MapSoundNavigationController` puts the listener and footsteps at the tile's height, blocks steps that are too steep, and plays footsteps at the terrain profile's new `climb_pitch` / `descend_pitch`. `play_sound` gained `pitch`, and `MapPlaySession.speak_location` announces a non-zero height.
* **Facing and interaction**: the player now turns to face an arrow key even when the move is blocked by a wall or the map border (`MapSoundNavigationController.on_border` sets `directional_orientation`). `MapInteractionController` takes `facing`, and `MapPlaySession` passes the character's orientation, so an object can only be examined when the player faces one of its tiles, up to `interact_reach_tiles` away in that direction.
* **Fixed**: a `ContainerScreen` re-entered after leaving (for example returning from a description) exited its already-exited child again, popping an extra key handler and eventually crashing with "Attempted to pop handler from empty stack".
* **Flyover pop while walking**: the flyer followed the listener only on its own timer, so for up to a frame after each step it sat a tile off and then jumped, heard as a crackle on one side. `FlyoverController.follow_listener()` moves it with the step, and the timer update is now batched too.
* **Flyovers on demand**: `FlyoverController.fly_now()` sends a flyover immediately, for testing.
* **Per-exit sounds**: `DocumentExit.sound` (and `MapExit.sound`) is a one-shot played when the player takes that exit, resolved through `resolve_sound` like object sounds, e.g. a door. Exits with their own sound do not give off the controller's looping `exit_sound` chime.
* **Object categories**: object types accept a `category` label, carried onto `MapObjectSpec.category`, so games can group objects (for example buildings) without hard-coding names.
* **Reloading maps while the game runs**: `MapScreenController.replace_definition(key, definition)` (and `MapSwitcher.register(..., replace=True)`) swap a registered map's definition, so a game can reload a map file and re-enter it without restarting. Entering the map you are already on now works (it rebuilds the screen), which also gives games a teleport.
* **Map object types**: `load_object_types(path, resolve_sound)` / `object_types_from_dict` define reusable `ObjectType`s (`footprint` offsets for any shape, `passable`, `collision_sound`, per-side `side_sounds`, a `loop` sound, `description`, `movable`). Map objects reference one with `"type"`; `MapDefinition.from_document(object_types=...)` resolves them, and `load_map` stamps blocking footprints onto the map as `object:<name>` tiles. A large object's loop plays as one source from the footprint tile nearest the player (`ProximityAudioEmitter.footprint`) and can be examined from any of its tiles (`InteractableObject.footprint`). `MapSoundNavigationController` accepts `blocked_side_sounds` for direction-specific collision sounds. `DocumentObject` gained `type`.
* **Terrain profiles from JSON**: `load_terrain_profiles(path, resolve_sound)` and `terrain_profiles_from_dict` build `TerrainAudioProfile`s from data (`passable`, `movement_sound`, `ambient`), resolving sound names through any callable such as `AssetCatalog.require`. `terrain_tile_factory(profiles)` makes the matching tile factory. Malformed entries raise `TerrainProfileError`.
* **MapScreenController music and ambience**: new `play_music`, `stop_music`, `play_ambience` and `stop_ambience` callbacks play each map's `music` and `ambience` values on entry and stop them on leave, so games no longer repeat that in `on_enter` / `on_leave`.
* **AssetCatalog and AssetLoader**: `AssetCatalog.from_directory` indexes an asset folder by logical key (`maps/beach/music`), with `require`, `get`, `many`, `keys_under` and `paths_under`. `AssetLoader` keeps memory bounded in large games: `pin` loads files for good, and `set_active(now, soon)` loads the current scene's files, loads likely-next files one per frame, and unloads the rest. `sound_pool_loader()` binds it to the shared sound pool.
* **`SoundManager.batch_updates()` / `sound_manager.batch_updates()`**: a re-entrant context manager that defers listener and source changes and commits them together, so the mixer never renders a half-moved scene.
* **`FlyoverController` / `FlyoverConfig`**: random flyovers, such as birds passing above the player. After a random interval a looping sound travels along a random heading at a set height above the listener, making one or more random calls on the way, then it waits again. Interval, duration, height, headings and call count are all configurable.
* **`name_keys`** on `MapScreenController` and `MapPlaySession`: keys that speak the current map's name.
* **`MapDocument.name`**: an optional map name. `MapScreenController` speaks it on every map entry (`announce_map_name=False` turns that off).
* **`MapDefinition` / `load_map` / `MapScreenController`**: a generic data-driven map layer. `MapDefinition.from_document` turns a `MapDocument` into objects, exits, music and ambience (resolvers bind names to your own enums), `load_map` builds it, and `MapScreenController` registers many maps, switches between them through exits, and builds a `MapPlaySession` per map, leaving only music and ambience hooks to the game.
* **Blended ambient tiles**: `blend_ambient=True` on `MapSoundNavigationController` (and `MapPlaySession`) plays each distinct ambient sound from its own nearest tile at once. `stop_ambient_sound()` releases every ambient player.
* **`ProximityAudioEmitter.start_offset`**: starts a looping emitter part-way into its sound so neighbouring emitters of the same sound do not sit in phase and blend into one source.
* **Exit sounds**: `MapScreenController(exit_sound=ObjectSound(...))` loops a positional sound from the middle of each group of adjacent exit tiles so players can find exits by ear.
* **Locate key**: `MapPlaySession(locate_keys=...)` speaks the current tile and coordinates.
* **Stereo positional warning**: `SoundManager.play_sound` logs once per sound when a stereo file is given a position, since OpenAL does not pan stereo buffers. `LoadSound` now exposes `channels`.
* **Map documents**: `MapDocument` is a versioned, validated JSON map format (north-first rows of single-character terrain codes, a legend, start, objects with sounds, exits, music, ambience). Use `load_map_document`/`save_map_document`, `build_map2d_from_document`, and `MapExitRegistry.from_document`. `MapCanvas` and `jagged_edge` draw maps and organic boundaries in code. See the Map Documents guide.
* **`ignore_unused_profiles`** on `MapSoundNavigationController.from_terrain_audio_profiles`: skip profiles for terrain absent from the map so one shared terrain table can serve every map.
* **Per-tile blocked sounds**: `MapSoundNavigationController` now plays a blocked tile's own mapped sound when it has one (for example an object that makes its own collision sound). Blocked tiles without one, and the map border, still play the shared wall sound.
* **`MapPlaySession`**: builds the screen, grid, terrain footsteps and ambient tiles, positional object sounds, and examinable objects for a `Map2d`, with `start_audio`/`stop_audio`. Games keep only their music, ambience and exit logic.
* **`MapInteractionController` / `InteractableObject`**: Enter/Space (configurable) on a map grid pages through the description of the nearest object within reach, then returns to the map.
* **`ChannelVolume` / `VolumeHotkeys` / `bind_level_hotkeys`**: stepped per-channel volume levels with a ceiling and spoken hotkeys that work on every screen.
* **`ChannelLoop`** (`sonartk.sound.channel_loop`): one looping sound on a channel whose per-loop gain survives channel volume changes.
* **`ProximityAudioController.from_emitters`, `update_at`, `stop_all`**, and defaults on `ProximityAudioEmitter` (gentle `rolloff`, linear fade) so most emitters need only a path, position and range.
* **`resolve_name`** (`sonartk.util`) binds names in data files to game enums, and **`MapDocument.require_terrain`** checks a document's legend against the game's terrain.
* **`apply_channel_volume`** on `SoundManager` (and module level): set a player's volume to a per-sound base volume scaled by its channel, so a per-loop gain survives channel volume changes.: Orchestration state that speaks long text one page at a time. Enter advances to the next page and, after the last page, transitions to an optional next state. Re-read (Up/Down) and copy (Ctrl+C) shortcuts are configurable, and `on_page_change`, `on_complete`, `on_reread`, and `on_copy` events allow games to play sounds as the player progresses.
* **PagedTextState**: Orchestration state that speaks long text one page at a time. Enter advances to the next page and, after the last page, transitions to an optional next state. Re-read (Up/Down) and copy (Ctrl+C) shortcuts are configurable, and `on_page_change`, `on_complete`, `on_reread`, and `on_copy` events allow games to play sounds as the player progresses.
* **Ambience channel**: `SoundManager` now has a dedicated `"ambience"` playback channel, so environmental loops get their own volume control without borrowing another channel.

* **Channel for ambient/proximity sounds**: `AmbientTileSoundConfig` and `ProximityAudioEmitter` accept an optional `channel` that is forwarded to `play_sound`.

* **Banded maps**: `MapBand` and `build_banded_map` build maps from horizontal terrain strips listed north to south (coastlines, rivers, etc.).

* **Map exits and switching**: `MapExit`, `MapExitRegistry`, and `MapSwitcher` let a game register map loaders, follow exits between maps (replacing the active map in memory), and react through `on_map_leave` / `on_map_enter` events.

* **Map.tile_revision / refresh_ambient_emitters()**: `Map2d` counts tile changes, and `MapSoundNavigationController` uses it to keep a cached list of ambient emitters instead of scanning every tile on every step.

## [0.2] - 2026-06-19

This release adds major UI improvements including multiline text viewing, dialog helpers, text input history, and improved menu navigation with immediate first-letter feedback.

### Changed

* **PagedTextState** now also advances on Space by default (previously only Enter).

### Added

* **MultilineTextBox**: Read-only text viewer with line-by-line navigation. Supports Up/Down for line navigation, Shift+Up/Down for selection, Home/End for line bounds, and Ctrl+Home/Ctrl+End for document boundaries. Full keyboard selection and copy-to-clipboard support inherited from TextBox.
* **Dialog helpers**: Three convenience functions (`open_alert_dialog`, `open_confirmation_dialog`, `open_menu_selection_dialog`) for common modal dialog patterns without manual Button/Menu wiring.
* **TextBox input history**: New `enable_input_history` flag enables Up/Down recall of previously submitted values. History is deduplicated, excludes blank entries, and preserves the user's unsaved draft when navigating.
* **TextHistory**: Standalone bounded most-recent-first history dataclass for managing command/input history outside of TextBox.
* **TextLabel keyboard shortcuts**: TextLabel now supports Up/Down to re-read the label and Ctrl+C to copy to clipboard. Disabled by default when used inside a Menu to preserve menu navigation control.
* **Improved menu first-letter navigation**: Now responds immediately on first character press instead of waiting for timeout. Repeated same-character jumps cycle through matching items, and additional characters refine the prefix search from the top.
* **speech_manager.output() None handling**: Output now gracefully accepts None and returns early without side effects, simplifying caller code.

### Fixed

* **Menu/TextLabel handler conflict**: When a TextLabel instance is added to a Menu via `Menu.add()`, its keyboard handlers are now automatically disabled so menu Up/Down navigation remains authoritative.
* **MultilineTextBox line indexing for mixed newlines**: Line calculation now correctly handles CR-only (`\r`), LF-only (`\n`), and CRLF (`\r\n`) line separators. Line index, cursor column tracking, and navigation stay aligned with split lines across all styles.
* **Element.exit() handler pop**: Now correctly passes the key handler to `pop_window_handlers()` for explicit stack tracking and debugging.

### Changed

* **Window.pop_window_handlers() signature**: Now accepts optional `*args, **kwargs` for API compatibility while maintaining backward compatibility.
* **TextLabel default behavior**: Keyboard shortcuts are now enabled by default via `enable_shortcuts=True` parameter.

## [0.1.1] - 2026-06-19

This release improves runtime reliability for both keyboard input and audio playback recovery. Key handling now better manages handler lifecycle and repeat behavior, reducing stuck-input edge cases during fast gameplay combinations.

Audio management is now more resilient when output devices change or recover mid-session. Recovery callbacks, device-watch controls, and replacement-player handoff support are now exposed through `sound_manager`, with coverage and checks updated to match.

### Changed

* **PagedTextState** now also advances on Space by default (previously only Enter).

### Added

* Key handling: added lifecycle/reset controls and improved repeat/release behavior for modifier-heavy input sequences.
* Sound recovery: added output-device watch controls, recovery callback registration, debug callback support, and recovered-player handoff APIs.
* Recovery behavior: improved detection and fallback flow for device changes, backend errors, disconnect/stall conditions, and rebuild/restore continuity.
* Volume orchestration: `bind_volume_hotkeys` now supports dynamic player resolvers and SFX-change callbacks.

### Changed

* State machine transition API: removed deprecated `change` alias and standardized on `transition_to` as the single transition primitive.
* UI activation API: removed deprecated `set_state` aliases from window/screen/menu layers and standardized on `activate_current_state`.
* Activation forwarding: `activate_current_state` now accepts and forwards arbitrary `*args` and `**kwargs` to state setup/activation paths.
* Internal consistency: updated call sites, examples, tests, and docs to use the canonical state machine naming and behavior.

## [0.1] - 2026-05-25

This is the initial release of this library. The code is in a usable state, although with many intended improvements in the future. This library provides screen reader only output, no graphical user interface is provided. All UI elements are abstract components that are only accessible through the keyboard via screen reader output. 

Provides 4 main packages to use for building games
* ui - provides common tools for building a user interface I.E. windows, buttons, checkboxes, texboxes, etc...
* sound - provides a wrapper for OpenAL. This package has 3d audio support, and is meant to provide friendly tools for managing audio.
* map_builder - provides tools for managing 2d maps for games. This module is design to interact with the ui package for building games. The intention is to build 3d support in the future.
* orchestration - brings together low level APIs into quick and condensed APIs for commonly used patterns.


