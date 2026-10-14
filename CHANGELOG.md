# Changelog

## [Unreleased]

### Fixed

* **Looping ambience lost after an output-device change**: loops that the dying device reported as stopped were skipped during recovery. Any loop that was never removed is now restored.
* **Unplugging or plugging in headphones mid-game**: output-device monitoring now starts automatically when `Window.open_window` runs (`monitor_audio_device=False` opts out, and an earlier `start_output_device_watch` call keeps its own settings). After a device change every `Player`, including ones created directly by game code, is rebuilt in place, so objects a game already holds keep working and looping sounds resume with no recovery callback or role rebinding. `sound_manager.ensure_output_device_watch()` and `Player.rebind()` / `PlayerPool.adopt_active_player()` support this.
* **Occasional one-sided pop while walking**: `MapSoundNavigationController` moved the listener and then each source in separate calls, so the mixer could render a block with every source one tile off, heard as a crackle in the ear opposite the movement. Each step is now applied as a single batched update.

### Changed

* **PagedTextState** now also advances on Space by default (previously only Enter).

### Added

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


