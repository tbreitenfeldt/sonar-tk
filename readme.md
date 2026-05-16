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
- sonartk.map_builder.map_2d: Map2d, MapTile, load_2d_map
- sonartk.map_builder.map_2d.map_object: MapObject, Character
- sonartk.map_builder.map_2d.parser: MapParser, CSVParser, JSONParser
- sonartk.orchestration: BuiltMapGridGame, MapGridGameBuilder, MapSoundNavigationController
- sonartk.sound: sound_manager
- sonartk.util: Callback, Coordinates, Direction, EmptyState, Key,
  KeyHandler, State, StateMachine, speech_manager

If you need symbols outside this list, import from the concrete module path
and treat those imports as lower-level/internal APIs.

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
[Window debug] after change('menu_screen'): Handler stack valid (expected=3, actual=3)
[Window debug] after set_state('button_0'): Handler stack valid (expected=4, actual=4)
```

Or toggle it at runtime:

```python
window.set_debug_mode(True)  # Logs: Debug mode enabled - handler stack validation active
window.set_debug_mode(False) # Logs: Debug mode disabled
```

When debug mode is enabled, window automatically logs handler-stack validation
after:

- Window.change(...)
- Window.set_state(...)

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
