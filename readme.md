# Sonar TK

Sonar TK is a Python library for creating audio-first games and accessible,
screen-reader-oriented interactive applications.

The project is organized into focused packages:

- ui: windowing, focus, screens, and interactive UI elements.
- map_builder: 2D map loading, tiles, map objects, and parsers.
- sound: sound playback and OpenAL integration helpers.
- util: speech, key handling, shared state/state machine primitives, and
  core utility types.

For common game composition, Sonar TK also provides a top-level builder API.

## Installation

Install from PyPI:

	pip install sonartk

## Supported Python Versions

Sonar TK currently requires Python 3.13 or newer.

## Top-Level API

The top-level package exposes high-level entry points:

	from sonartk import Window, MapGridGameBuilder, BuiltMapGridGame

- Window: primary application window.
- MapGridGameBuilder: composition helper for map + grid game wiring.
- BuiltMapGridGame: typed return object from the builder.

## Package-Level APIs

Use package imports when you want lower-level control:

	from sonartk.ui import Window
	from sonartk.map_builder import Map2d, MapTile, load_2d_map
	from sonartk.sound import sound_manager
	from sonartk.util import Direction, Coordinates, KeyHandler

UI remains focused on UI primitives. Cross-domain composition helpers belong at
top level (for example, MapGridGameBuilder).

## Public API Reference

The following exports are the intended stable import surface:

- sonartk: Window, MapGridGameBuilder, BuiltMapGridGame
- sonartk.ui: UIComponent, FocusableContainer, Window
- sonartk.map_builder: Map2d, MapTile, load_2d_map
- sonartk.map_builder.map_2d: Map2d, MapTile, load_2d_map
- sonartk.map_builder.map_2d.map_object: MapObject, Character
- sonartk.map_builder.map_2d.parser: MapParser, CSVParser, JSONParser
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

	pip install -r requirements.txt

## Running Tests

Run the test suite with pytest:

	pytest

Run coverage locally:

	pytest --cov=src --cov-report=term-missing
