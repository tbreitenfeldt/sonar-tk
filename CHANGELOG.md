# Changelog

## [0.2] - 2026-06-19

This release adds major UI improvements including multiline text viewing, dialog helpers, text input history, and improved menu navigation with immediate first-letter feedback.

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


