# Map Object Collection Sessions

This guide covers the generic collection APIs used to spawn, track, and collect map objects without introducing game-specific concepts into the library.

## Why This Exists

`MapObjectCollectionSession` is a reusable orchestration helper for object-collection loops:

- random spawn on passable, available tiles
- optional coordinate filters
- tracked remaining and collected counts
- safe object-type collection
- transactional reset behavior

## Basic Usage

```python
from sonartk.map_builder.map_2d.map_object.map_object import MapObject
from sonartk.orchestration.map_object_collection import MapObjectCollectionSession


class Gem(MapObject):
    def __init__(self, name: str, coordinates: tuple[int, int], power: int) -> None:
        super().__init__(name, coordinates)
        self.power = power


session = MapObjectCollectionSession[Gem](
    map2d,
    object_count=3,
    object_type=Gem,
    object_factory=lambda index, coordinates: Gem(
        f"gem-{index}",
        coordinates,
        power=5,
    ),
    excluded_coordinates={map2d.character.coordinates},
    object_label="gems",
)

session.reset()
```

## Collection API

```python
if session.has_object_at(player_coordinates):
    collected = session.collect_at(player_coordinates)
    if collected is not None:
        print(collected.name, session.collected_count, session.remaining_count)
```

Behavior notes:

- `collect_at` only removes objects matching `object_type`.
- If a different object type is at that coordinate, it returns `None` and leaves the map unchanged.

## Spawn Filters

Use optional filters to define spawn constraints:

- `excluded_coordinates`: direct exclusions (for example player start)
- `forbidden_coordinates`: additional blocked tiles
- `required_coordinates`: restrict candidate pool to a specific set
- `coordinate_predicate`: custom boolean rule evaluated per coordinate

```python
session = MapObjectCollectionSession[Gem](
    map2d,
    object_count=2,
    object_type=Gem,
    object_factory=lambda index, coordinates: Gem(f"gem-{index}", coordinates, 1),
    required_coordinates={(0, 0), (1, 0), (2, 0), (2, 1)},
    forbidden_coordinates={(1, 0)},
    coordinate_predicate=lambda coordinates: coordinates[0] == 2,
)
```

## Occupancy Rules

Spawn selection excludes:

- non-passable tiles
- character-occupied coordinates
- coordinates occupied by non-session map objects
- excluded and forbidden coordinates
- coordinates failing `coordinate_predicate`

If there are not enough valid coordinates, `reset` raises `ValueError`.

## Transactional Reset

`reset` is transactional:

- old session-owned objects are removed
- new objects are planned and created
- registration occurs as a batch
- on failure (factory or registration), newly registered objects are removed and the previous active set is restored

This prevents partial map/session state after errors.

## Map2d Identity Helpers

For object identity operations, `Map2d` exposes:

- `find_map_object_coordinates(map_object)`
- `is_map_object_registered(map_object)`

These helpers are useful when external systems may move objects and you need identity-based checks.

## Migration Note

The library no longer includes game-specific collectible types (such as coins). Define concrete item classes in your game code and use this generic session helper.

## Migration Example (Before and After)

### Before

```python
from sonartk.orchestration.coin_collection import CoinCollectionSession

coin_session = CoinCollectionSession(
    map2d,
    coin_count=3,
    excluded_coordinates={start_coordinates},
)

coin_session.reset()

if coin_session.has_coin_at(player_coordinates):
    collected = coin_session.collect_at(player_coordinates)
```

### After

```python
from sonartk.map_builder.map_2d.map_object.map_object import MapObject
from sonartk.orchestration.map_object_collection import MapObjectCollectionSession


class Coin(MapObject):
    def __init__(self, name: str, coordinates: tuple[int, int], value: int = 1) -> None:
        super().__init__(name, coordinates)
        self.value = value


coin_session = MapObjectCollectionSession[Coin](
    map2d,
    object_count=3,
    object_type=Coin,
    object_factory=lambda index, coordinates: Coin(
        f"coin-{index}",
        coordinates,
        value=1,
    ),
    excluded_coordinates={start_coordinates},
    object_label="coins",
)

coin_session.reset()

if coin_session.has_object_at(player_coordinates):
    collected = coin_session.collect_at(player_coordinates)
```

Key updates:

- Create your concrete item type in game code.
- Replace `coin_count` with `object_count`.
- Replace `has_coin_at` with `has_object_at`.
- Provide an `object_factory` for naming and object-specific fields.

## Common Migration Pitfalls

- `collect_at` is type-safe. If a different object type occupies the tile, it returns `None` and does not remove that object.
- Spawns are occupancy-aware. Passable tiles can still be invalid if they are occupied by a character or a non-session map object.
- If `reset` raises `ValueError` for capacity, check `required_coordinates`, `forbidden_coordinates`, and current occupancy.
- `reset` is transactional. On factory or registration failures, the previous active set is restored.
- Prefer `has_object_at` before playing item-hover sounds and `collect_at` for the actual pickup action.