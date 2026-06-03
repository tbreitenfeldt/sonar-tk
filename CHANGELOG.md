# Changelog

## [0.1] - 2026-05-25

This is the initial release of this library. The code is in a usable state, although with many intended improvements in the future. This library provides screen reader only output, no graphical user interface is provided. All UI elements are abstract components that are only accessible through the keyboard via screen reader output. 

Provides 4 main packages to use for building games
* ui - provides common tools for building a user interface I.E. windows, buttons, checkboxes, texboxes, etc...
* sound - provides a wrapper for OpenAL. This package has 3d audio support, and is meant to provide friendly tools for managing audio.
* map_builder - provides tools for managing 2d maps for games. This module is design to interact with the ui package for building games. The intention is to build 3d support in the future.
* orchestration - brings together low level APIs into quick and condensed APIs for commonly used patterns.

## [0.1.1] - unreleased

This release improves runtime reliability for both keyboard input and audio playback recovery. Key handling now better manages handler lifecycle and repeat behavior, reducing stuck-input edge cases during fast gameplay combinations.

Audio management is now more resilient when output devices change or recover mid-session. Recovery callbacks, device-watch controls, and replacement-player handoff support are now exposed through `sound_manager`, with coverage and checks updated to match.

* Key handling: added lifecycle/reset controls and improved repeat/release behavior for modifier-heavy input sequences.
* Sound recovery: added output-device watch controls, recovery callback registration, debug callback support, and recovered-player handoff APIs.
* Recovery behavior: improved detection and fallback flow for device changes, backend errors, disconnect/stall conditions, and rebuild/restore continuity.
* Volume orchestration: `bind_volume_hotkeys` now supports dynamic player resolvers and SFX-change callbacks.
