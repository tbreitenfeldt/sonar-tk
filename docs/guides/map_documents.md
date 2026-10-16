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
