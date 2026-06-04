# Sonar TK

Sonar TK is a Python library for creating audio-first games and accessible,
screen-reader-oriented interactive applications.

The project is organized into focused packages:

- ui: windowing, focus, screens, and interactive UI elements.
- map_builder: 2D map loading, tiles, map objects, and parsers.
- sound: sound playback and OpenAL integration helpers.
- util: speech, key handling, shared state/state machine primitives, and
  core utility types.
- orchestration: optional higher-level coordination helpers for composing
	ui + map_builder + sound into game flows.

For common game composition, Sonar TK also provides a top-level builder API.

If you only need core primitives (for example, UI-only or UI+sound projects),
you can ignore `orchestration` entirely.

## Installation

Install from PyPI:

```bash
pip install sonartk
```

## Supported Python Versions

Sonar TK currently requires Python 3.13 or newer.

## Top-Level API

The top-level package exposes high-level entry points:

```python
from sonartk import (
    Window,
    MapGridGameBuilder,
    BuiltMapGridGame,
    MapSoundNavigationController,
)
```

- Window: primary application window.
- MapGridGameBuilder: composition helper for map + grid game wiring.
- BuiltMapGridGame: typed return object from the builder.
- MapSoundNavigationController: reusable map navigation + sound integration helper.

## Package-Level APIs

Use package imports when you want lower-level control:

```python
from sonartk.ui import Window
from sonartk.map_builder import Map2d, MapTile, load_2d_map
from sonartk.orchestration import (
    MapGridGameBuilder,
    MapSoundNavigationController,
)
from sonartk.sound import sound_manager
from sonartk.util import Direction, Coordinates, KeyHandler
```

UI remains focused on UI primitives. Cross-domain composition helpers belong at
top level (for example, MapGridGameBuilder).

The explicit orchestration package path is also supported:

```python
from sonartk.orchestration import MapGridGameBuilder
from sonartk.orchestration import MapSoundNavigationController
```

## Public API Reference

The following exports are the intended stable import surface:

- sonartk: Window, MapGridGameBuilder, BuiltMapGridGame, MapSoundNavigationController
- sonartk.ui: UIComponent, FocusableContainer, Window
- sonartk.map_builder: Map2d, MapTile, load_2d_map
- sonartk.map_builder.map_2d: Map2d, Map2dQueries, MapQueryResult, PathfindingResult, PathfindingState, MapTile, load_2d_map
- sonartk.map_builder.map_2d.map_object: MapObject, Character
- sonartk.map_builder.map_2d.parser: MapParser, CSVParser, JSONParser
- sonartk.orchestration: AmbientTileSoundConfig, IntroGameAudioLifecycle, TerrainAudioProfile, BuiltMapGridGame, MapGridGameBuilder, MapSoundNavigationController
- sonartk.sound: sound_manager
- sonartk.util: Callback, Coordinates, Direction, EmptyState, Key,
  KeyHandler, State, StateMachine, speech_manager

## Audio Preloading APIs

When using the sound package, you can preload assets at startup to reduce
runtime latency and fail early on missing/invalid files.

- `sound_manager.preload_sounds(paths)`: preload through the shared default
    sound manager.
- `sound_manager.allocate_players_by_role(role_names)`: allocate named players
    for gameplay roles without positional tuple wiring.
- `SoundPool.load_many(paths)`: lower-level preload API when managing your own
    `SoundPool` instance.

## New Orchestration Audio APIs

- `TerrainAudioProfile`: unify passability + movement + ambient terrain audio.
- `MapSoundNavigationController.from_terrain_audio_profiles(...)`: build
    movement + ambient controller directly from terrain profiles.
- `MapSoundNavigationController.validate_sound_map_for_map()`: fail fast on
    missing movement/collision mappings.
- `IntroGameAudioLifecycle`: reusable intro-to-game audio transition helper.

## Map Terrain Utility

- `sonartk.map_builder.map_2d.map_tools.mark_adjacent_tiles(...)`: generic
    terrain post-processing helper (for example, mark mud banks around rivers).

If you need symbols outside this list, import from the concrete module path
and treat those imports as lower-level/internal APIs.

## Map Builder Behavior Notes

- Map2d.add_row prepends rows. The latest inserted row is y=0.
- Map2d register/move methods now return displaced occupants when collision policy is set to replace:
    - Map2d.register_character(...) -> Character | None
    - Map2d.move_character(...) -> Character | None
    - Map2d.register_map_object(...) -> MapObject | None
    - Map2d.move_map_object(...) -> MapObject | None
- Map2dQueries.get_coordinate_hit(...) with tile_names returns None for in-range coordinates when:
    - no tile name matches, and
    - no character/map object occupies that coordinate.
- Map2dQueries.find_path(...) accepts optional PathfindingState for dynamic traversal rules:
    - blocked_coordinates: explicit blocked coordinates for this search.
    - block_characters: treat character-occupied coordinates as blocked.
    - block_map_objects: treat map-object-occupied coordinates as blocked.
        - actor_capabilities: capability profile used for tile capability checks.
    - allow_end_occupied: allow/disallow a blocked end coordinate.
    - allow_start_blocked: allow/disallow starting from a blocked coordinate.
    - allow_diagonal_movement: enable 8-direction path traversal.
    - allow_corner_cutting: allow/disallow diagonal corner cuts around blockers.
    - tile_cost_by_name: add non-negative movement costs by tile name.
    - tile_cost_resolver: callback for dynamic non-negative movement costs.
        - dynamic_cost_layers: stackable callbacks for additive contextual costs.
        - turn_penalty: non-negative cost applied when the route changes direction.
        - blocker_proximity_cost: non-negative cost scaled by nearby blocker count.
        - tie_breaker: equal-cost ordering policy (fifo, lower-heuristic, lower-cost).
        - max_expanded_nodes: optional hard cap for search expansion.
        - max_total_cost: optional hard cap for route total cost.
        - smoothing_mode: post-process output path (none or collinear).
        - enable_result_cache/cache_namespace/map_state_token: result-cache controls for repeated planning.
- Map2dQueries.find_path_result(...) returns metadata (found, path, total_cost,
    visited_nodes, expanded_nodes, reason, from_cache) for AI/debug tooling.
- MapTile.allowed_entry_directions can constrain which movement directions may enter a tile.
- MapTile.required_capabilities can require actor capabilities for traversal.
- PathfindingState also includes preset constructors for common movement profiles:
    - PathfindingState.for_player(tier="relaxed"|"standard"|"strict")
    - PathfindingState.for_flying_enemy(tier="relaxed"|"standard"|"strict")
    - PathfindingState.for_heavy_unit(tier="relaxed"|"standard"|"strict")

Example of handling displaced occupants in replace mode:

```python
from sonartk.map_builder import Map2d
from sonartk.map_builder.map_2d.map_object import Character
from sonartk.util import Direction

hero = Character("hero", (1, 1), Direction.UP)
map2d = Map2d(
    "arena",
    hero,
    character_collision_policy="replace",
)

ally = Character("ally", (0, 0), Direction.RIGHT)
blocker = Character("blocker", (1, 0), Direction.LEFT)
map2d.register_character(ally)
map2d.register_character(blocker)

displaced = map2d.move_character(ally, (1, 0))
if displaced is not None:
    print(f"Displaced character: {displaced.name}")
```

Example of state-aware pathfinding:

```python
from sonartk.map_builder.map_2d import PathfindingState

path = map2d.queries.find_path(
    start=(0, 0),
    end=(3, 0),
    state=PathfindingState(
        blocked_coordinates={(1, 0)},
        block_characters=True,
        block_map_objects=True,
        allow_end_occupied=False,
        allow_start_blocked=False,
        allow_diagonal_movement=True,
        allow_corner_cutting=False,
        tile_cost_by_name={"mud": 4.0},
        turn_penalty=0.25,
        max_expanded_nodes=2000,
        smoothing_mode="collinear",
    ),
)
```

Example of metadata and caching:

```python
state = PathfindingState(
    enable_result_cache=True,
    cache_namespace="enemy-ai",
    map_state_token="wave-2",
)

result = map2d.queries.find_path_result((0, 0), (4, 2), state=state)
if result.found:
    print(result.path, result.total_cost, result.from_cache)
else:
    print(result.reason)

# Invalidate when map blockers/state changes.
map2d.queries.invalidate_path_cache()
```

Example of preset profiles:

```python
player_state = PathfindingState.for_player("standard")
flying_state = PathfindingState.for_flying_enemy("relaxed")
heavy_state = PathfindingState.for_heavy_unit("strict")

player_path = map2d.queries.find_path((0, 0), (5, 2), state=player_state)
enemy_path = map2d.queries.find_path((0, 0), (5, 2), state=flying_state)
tank_path = map2d.queries.find_path((0, 0), (5, 2), state=heavy_state)
```

Example of preset + overrides:

```python
state = PathfindingState.for_player().with_overrides(
    max_expanded_nodes=500,
    allow_diagonal_movement=True,
)

path = map2d.queries.find_path((0, 0), (5, 2), state=state)
```

Example of custom profile registry:

```python
PathfindingState.register_profile(
    "scout",
    PathfindingState.for_player("relaxed").with_overrides(
        allow_diagonal_movement=True,
        turn_penalty=0.1,
    ),
)

scout_state = PathfindingState.from_profile("scout")
path = map2d.queries.find_path((0, 0), (5, 2), state=scout_state)

print(PathfindingState.list_profiles())
PathfindingState.unregister_profile("scout")
```

Example of profile persistence data:

```python
PathfindingState.register_profile("scout", PathfindingState.for_player("relaxed"))
data = PathfindingState.export_profiles()

# Save/load this JSON-safe dict with your own file I/O.
PathfindingState.import_profiles(data, overwrite=True)

# Strict mode rejects unknown profile fields.
PathfindingState.import_profiles(data, overwrite=True, strict=True)

# Strict mode also validates field types and value ranges.
# Examples rejected in strict mode:
# - negative max_total_cost or max_expanded_nodes
# - non-finite numbers (nan/inf) for numeric fields
# - negative tile_cost_by_name values
```

Example of profile JSON file helpers:

```python
PathfindingState.save_profiles("profiles.json")
PathfindingState.load_profiles("profiles.json", overwrite=True)

# Permissive mode ignores unknown fields when loading.
PathfindingState.load_profiles("profiles.json", overwrite=True, strict=False)

# strict=False only relaxes unknown-field handling.
# Invalid types and values still raise clear errors at runtime when used.

# Optional output style controls.
PathfindingState.save_profiles(
    "profiles.compact.json",
    pretty=False,
    sort_keys=False,
)
```

## Dependencies

Core runtime dependencies include:

- pyglet
- accessible_output2
- pyperclip
- ijson
- pyogg

## Source Setup

Clone the repository:

https://github.com/tbreitenfeldt/sonar-tk

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running Tests

Run the test suite with pytest:

```bash
pytest
```

Run coverage locally:

```bash
pytest --cov=src --cov-report=term-missing
```

## Window Debugging

Window includes optional runtime diagnostics for handler-stack issues.

Enable debug mode when creating the window:

```python
from sonartk import Window

window = Window(caption="My Game", debug_mode=True)
```

When debug mode is enabled, you'll see startup message and validation output on stderr:

```
[Window debug] Debug mode enabled - handler stack validation active
[Window debug] after transition_to('menu_screen'): Handler stack valid (expected=3, actual=3)
[Window debug] after transition_to('button_0'): Handler stack valid (expected=4, actual=4)
```

Or toggle it at runtime:

```python
window.set_debug_mode(True)  # Logs: Debug mode enabled - handler stack validation active
window.set_debug_mode(False) # Logs: Debug mode disabled
```

When debug mode is enabled, window automatically logs handler-stack validation
after:

- Window.transition_to(...)
- Window.activate_current_state(...)

This shows you the handler stack state (expected vs actual count) at each transition,
making it easy to spot when a state's exit() or setup() is not managing handlers
correctly.

You can run checks manually at any time:

```python
is_valid, message = window.validate_handler_stack()
if not is_valid:
    print(message)

# Optional leak check helper (defaults to window baseline handlers)
window = Window(debug_mode=True, debug_stream=debug_stream)
```
