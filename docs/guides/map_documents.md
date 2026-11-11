# Map Documents

A `MapDocument` is a complete, serializable description of one map. It is
the format a map-builder tool can export and a game can load, so maps live in
data files instead of code.

## File format

```json
{
  "version": 1,
  "key": "beach",
  "legend": {"~": "ocean", "s": "sand"},
  "rows": [
    "~~~~~~",
    "~~~s~~",
    "ssssss"
  ],
  "start": [2, 0],
  "objects": [
    {"name": "rowboat", "at": [3, 1], "sound": "rowboat_object",
     "max_distance_tiles": 20}
  ],
  "exits": [
    {"at": [5, 0], "target_map": "cave", "target_at": [0, 4]}
  ],
  "music": "beach",
  "ambience": "wind",
  "properties": {}
}
```

* `rows` are written **north first**, like the map drawn on paper. Every row
  has the same width and uses one character per tile.
* `legend` maps each character to a terrain name.
* All coordinates are `[x, y]` as used by `Map2d`: `x` grows eastward and `y`
  grows northward, so `[0, 0]` is the south-west corner, which is the first
  character of the **last** row.
* Sounds, music and ambience are plain names. The library never interprets
  them; the game maps them to its own sound catalog.
* `properties` (map and object level) carries any extra JSON data a game needs.

## Multi-tile passages

The optional passage helpers expand a rectangular opening into regular exits
and give the opening one looping beacon. Its source follows the nearest tile
in the passage, so movement within range does not restart the loop or play
several overlapping loops. Each passage has its own sound, range and volume;
ordinary exits keep their existing beacon behavior.

Put passages in the map's `properties` (using inclusive map coordinates):

```json
{
  "passages": [
    {
      "area": [4, 0, 6, 0],
      "target_map": "forest",
      "target_at": [2, 1],
      "transition_sound": "door",
      "beacon": {"sound": "bell", "range": 25, "volume": 0.8}
    }
  ]
}
```

* `area` is `[x0, y0, x1, y1]`, with ordered, inclusive corners inside the
  source map. It can describe a single tile or a rectangle of any size.
* `target_map` is a nonempty map key; every tile leads to `target_at`.
  Choose walkable exit tiles and a valid destination landing as for any exit.
  The helpers do not check that the destination exists or is walkable.
* `beacon.sound` is a nonempty sound name, `range` is a positive integer
  measured in tiles, and `volume` is between 0 and 1 (default 1). The
  beacon's distance and position use the nearest tile by Manhattan distance.
  The sound stops outside its range and starts again when the player returns.
* `transition_sound` is optional and plays once when the passage is taken,
  separately from the looping beacon. A doorway can use a door sound here
  and a different beacon sound.

Parsing checks field shapes and values. It checks that sound names are
nonempty; checking whether they exist is the resolver's responsibility.
Expansion returns a new document and rejects overlapping passages or
conflicting ordinary exits. Re-expanding an already expanded document with
the same passages does not duplicate its exits.

Parsing and expansion are explicit, so maps using `properties.passages` for
other purposes are unaffected. Supply a resolver accepting a name and a
descriptive label, or omit it to use the names as sound paths:

```python
from sonartk.orchestration import (
    MapDefinition, MapScreenController, expand_passages,
    parse_map_passages, passage_exit_emitters,
)

def resolve_passage_sound(name, label):
    return sound_catalog.require(name, label)

passages = parse_map_passages(document, resolve_sound=resolve_passage_sound)
expanded = expand_passages(document, passages)
definition = MapDefinition.from_document(
    expanded, resolve_sound=lambda name: sound_catalog.require(name, "sound")
)

class PassageScreen(MapScreenController):
    def _exit_emitters(self, loaded):
        passages = parse_map_passages(
            loaded.definition.document, resolve_sound=resolve_passage_sound
        )
        return passage_exit_emitters(
            loaded.definition.exits, passages, super()._exit_emitters(loaded)
        )
```

Build each definition this way before registering it with `PassageScreen`.
The transition sound remains a document name during expansion:
`parse_map_passages` calls the passage resolver to validate it, and
`MapDefinition.from_document` resolves it again for playback. The beacon
path is resolved by `parse_map_passages`; reparsing on map entry resolves it
again. Resolver errors propagate to the caller.

`passage_exit_emitters` replaces the controller's `exit:<index>` emitters
with one emitter per passage, leaving unrelated emitters unchanged. It raises
`ValueError` if an exit is missing, duplicated, overlaps another passage, or
points to a different destination. For a `MapExitRegistry` used without a
screen controller, use `expand_passages` first so every tile is registered.

## Loading

```python
from sonartk.map_builder import build_map2d_from_document, load_map_document
from sonartk.orchestration import MapExitRegistry

document = load_map_document("maps/beach.json")
map2d = build_map2d_from_document(document, tile_factory=make_tile)
exits = MapExitRegistry.from_document(document)
```

`tile_factory(terrain_name)` returns the `MapTile` for a terrain and is
called once per terrain. Objects are registered on the returned map.
`MapDocumentError` (a `ValueError`) is raised for unknown version, ragged
rows, codes missing from the legend, out-of-bounds positions, duplicate
objects or exits, and a start tile that is not passable.

## Object types

Objects with a `"type"` take their shape, sounds and description from an
object type defined once in a data file (see `load_object_types`):

```json
{
  "rowboat": {
    "footprint": [[0, 0]],
    "passable": false,
    "collision_sound": "rowboat_collision",
    "side_sounds": {"north": "hull_scrape"},
    "loop": {"sound": "rowboat_object", "max_distance_tiles": 20},
    "description": ["Your rowboat."]
  }
}
```

```json
{"name": "rowboat", "type": "rowboat", "at": [128, 85]}
```

* `footprint` lists tile offsets from `at`, so objects can have any shape.
* A blocking (`passable: false`) object is stamped onto the map as
  impassable tiles named `object:<name>`; do not paint it in `rows`.
* `collision_sound` plays when the player bumps into any of its tiles.
  `side_sounds` (`north`, `south`, `east`, `west`) replace it for that side.
* `loop` is one uniform sound: it plays from the footprint tile nearest the
  player, so it sounds the same from every side.
* The object can be examined from next to any footprint tile.
* `sound`, `max_distance_tiles` and `properties.description` on the object
  itself override the type.
* Pass the types to `MapDefinition.from_document(..., object_types=...)`.
  Unknown types, footprints off the map, overlaps and footprints on exits
  are rejected.

## Drawing maps in code

`MapCanvas` uses the same coordinates and writes the rows for you.
`jagged_edge` produces wandering boundaries for organic coastlines:

```python
from sonartk.map_builder import MapCanvas, MapDocument, jagged_edge

canvas = MapCanvas(250, 100, "s")
tide = jagged_edge(250, 96, amplitude=2, seed=4)
canvas.fill_between(tide, [100] * 250, "~")

document = MapDocument(
    key="beach", legend={"~": "ocean", "s": "sand"},
    rows=canvas.to_rows(), start=(125, 50),
)
save_map_document(document, "beach.json")
```
