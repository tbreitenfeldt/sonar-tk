from dataclasses import dataclass, field
from typing import (
    Any,
    AbstractSet,
    Callable,
    ClassVar,
    Iterator,
    Literal,
    Optional,
    TYPE_CHECKING,
    cast,
)
from heapq import heappop, heappush
import math
import json

from sonartk.map_builder.map_2d.map_object.character import Character
from sonartk.map_builder.map_2d.map_tile import MapTile
from sonartk.map_builder.map_2d.map_object import MapObject
from sonartk.util import Coordinates, Direction

if TYPE_CHECKING:
    from sonartk.map_builder.map_2d.map_2d import Map2d


@dataclass(frozen=True)
class MapQueryResult:
    """Typed result for a coordinate-level spatial query."""

    coordinates: Coordinates
    tile: Optional[MapTile]
    character: Optional[Character]
    map_object: Optional[MapObject]


@dataclass(frozen=True)
class PathfindingState:
    """Optional runtime rules that affect pathfinding passability."""

    blocked_coordinates: AbstractSet[Coordinates] = field(
        default_factory=frozenset
    )
    block_characters: bool = False
    block_map_objects: bool = False
    allow_end_occupied: bool = True
    allow_start_blocked: bool = True
    allow_diagonal_movement: bool = False
    allow_corner_cutting: bool = False
    tile_cost_by_name: dict[str, float] = field(default_factory=dict)
    tile_cost_resolver: Callable[[MapTile, Coordinates], float] | None = None
    dynamic_cost_layers: tuple[
        Callable[[MapTile, Coordinates], float], ...
    ] = ()
    actor_capabilities: frozenset[str] = frozenset()
    turn_penalty: float = 0.0
    blocker_proximity_cost: float = 0.0
    tie_breaker: Literal["fifo", "lower-heuristic", "lower-cost"] = "fifo"
    max_expanded_nodes: int | None = None
    max_total_cost: float | None = None
    smoothing_mode: Literal["none", "collinear"] = "none"
    enable_result_cache: bool = False
    cache_namespace: str = "default"
    map_state_token: str | int | None = None

    _PROFILE_REGISTRY: ClassVar[dict[str, "PathfindingState"]] = {}
    _SERIALIZED_PROFILE_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {
            "blocked_coordinates",
            "block_characters",
            "block_map_objects",
            "allow_end_occupied",
            "allow_start_blocked",
            "allow_diagonal_movement",
            "allow_corner_cutting",
            "tile_cost_by_name",
            "actor_capabilities",
            "turn_penalty",
            "blocker_proximity_cost",
            "tie_breaker",
            "max_expanded_nodes",
            "max_total_cost",
            "smoothing_mode",
            "enable_result_cache",
            "cache_namespace",
            "map_state_token",
        }
    )

    def with_overrides(self, **overrides: object) -> "PathfindingState":
        """Return a copy of this state with selected fields overridden."""
        state_fields = {
            "blocked_coordinates",
            "block_characters",
            "block_map_objects",
            "allow_end_occupied",
            "allow_start_blocked",
            "allow_diagonal_movement",
            "allow_corner_cutting",
            "tile_cost_by_name",
            "tile_cost_resolver",
            "dynamic_cost_layers",
            "actor_capabilities",
            "turn_penalty",
            "blocker_proximity_cost",
            "tie_breaker",
            "max_expanded_nodes",
            "max_total_cost",
            "smoothing_mode",
            "enable_result_cache",
            "cache_namespace",
            "map_state_token",
        }
        unknown = [key for key in overrides if key not in state_fields]
        if unknown:
            joined = ", ".join(sorted(unknown))
            raise ValueError(f"Unknown PathfindingState fields: {joined}")
        return PathfindingState(**{**self.__dict__, **overrides})

    @classmethod
    def register_profile(
        cls,
        name: str,
        state: "PathfindingState",
        *,
        overwrite: bool = False,
    ) -> None:
        """Register a named custom profile for reuse across pathfinding calls."""
        profile_name = name.strip()
        if profile_name == "":
            raise ValueError("Profile name cannot be blank.")
        if profile_name in cls._PROFILE_REGISTRY and not overwrite:
            raise ValueError(
                f"Pathfinding profile '{profile_name}' is already registered. Pass overwrite=True to replace it."
            )
        cls._PROFILE_REGISTRY[profile_name] = state

    @classmethod
    def from_profile(cls, name: str) -> "PathfindingState":
        """Return a previously registered custom profile by name."""
        profile_name = name.strip()
        try:
            return cls._PROFILE_REGISTRY[profile_name]
        except KeyError as exc:
            raise KeyError(
                f"Unknown pathfinding profile: {profile_name}"
            ) from exc

    @classmethod
    def unregister_profile(cls, name: str) -> None:
        """Remove a named custom profile if it exists."""
        cls._PROFILE_REGISTRY.pop(name.strip(), None)

    @classmethod
    def list_profiles(cls) -> tuple[str, ...]:
        """Return all registered custom profile names sorted alphabetically."""
        return tuple(sorted(cls._PROFILE_REGISTRY.keys()))

    @classmethod
    def export_profiles(cls) -> dict[str, dict[str, object]]:
        """Export registered profiles as JSON-safe dictionaries."""
        exported: dict[str, dict[str, object]] = {}
        for name, state in cls._PROFILE_REGISTRY.items():
            exported[name] = state.to_profile_dict()
        return exported

    @classmethod
    def import_profiles(
        cls,
        profiles: dict[str, dict[str, object]],
        *,
        overwrite: bool = False,
        strict: bool = True,
    ) -> None:
        """Import profile dictionaries produced by export_profiles."""
        for name, payload in profiles.items():
            state = cls.from_profile_dict(payload, strict=strict)
            cls.register_profile(name, state, overwrite=overwrite)

    @classmethod
    def save_profiles(
        cls,
        file_path: str,
        *,
        pretty: bool = True,
        sort_keys: bool = True,
    ) -> None:
        """Write registered profiles to a JSON file."""
        with open(file_path, "w", encoding="utf-8") as handle:
            json.dump(
                cls.export_profiles(),
                handle,
                indent=2 if pretty else None,
                sort_keys=sort_keys,
                separators=None if pretty else (",", ":"),
            )

    @classmethod
    def load_profiles(
        cls,
        file_path: str,
        *,
        overwrite: bool = False,
        strict: bool = True,
    ) -> None:
        """Load and register profiles from a JSON file."""
        with open(file_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            raise ValueError("Profile file must contain a JSON object.")
        cls.import_profiles(payload, overwrite=overwrite, strict=strict)

    def to_profile_dict(self) -> dict[str, object]:
        """Serialize this state to a JSON-safe dictionary.

        Callable fields are intentionally unsupported for persistence.
        """
        if self.tile_cost_resolver is not None:
            raise ValueError(
                "Cannot serialize PathfindingState with tile_cost_resolver; use tile_cost_by_name for persisted profiles."
            )
        if len(self.dynamic_cost_layers) > 0:
            raise ValueError(
                "Cannot serialize PathfindingState with dynamic_cost_layers; use fixed costs for persisted profiles."
            )

        return {
            "blocked_coordinates": [
                list(item) for item in self.blocked_coordinates
            ],
            "block_characters": self.block_characters,
            "block_map_objects": self.block_map_objects,
            "allow_end_occupied": self.allow_end_occupied,
            "allow_start_blocked": self.allow_start_blocked,
            "allow_diagonal_movement": self.allow_diagonal_movement,
            "allow_corner_cutting": self.allow_corner_cutting,
            "tile_cost_by_name": dict(self.tile_cost_by_name),
            "actor_capabilities": sorted(self.actor_capabilities),
            "turn_penalty": self.turn_penalty,
            "blocker_proximity_cost": self.blocker_proximity_cost,
            "tie_breaker": self.tie_breaker,
            "max_expanded_nodes": self.max_expanded_nodes,
            "max_total_cost": self.max_total_cost,
            "smoothing_mode": self.smoothing_mode,
            "enable_result_cache": self.enable_result_cache,
            "cache_namespace": self.cache_namespace,
            "map_state_token": self.map_state_token,
        }

    @classmethod
    def from_profile_dict(
        cls,
        payload: dict[str, object],
        *,
        strict: bool = True,
    ) -> "PathfindingState":
        """Deserialize a profile dictionary into PathfindingState."""
        if strict:
            cls._validate_serialized_profile_payload(payload)

        blocked_raw = cast(
            list[list[int]] | tuple[tuple[int, int], ...],
            payload.get("blocked_coordinates", []),
        )
        blocked_coordinates = frozenset(
            (int(item[0]), int(item[1])) for item in blocked_raw
        )
        actor_capabilities_raw = cast(
            list[object] | tuple[object, ...],
            payload.get("actor_capabilities", []),
        )
        actor_capabilities = frozenset(
            str(item) for item in actor_capabilities_raw
        )
        tile_cost_by_name_raw = cast(
            dict[str, float | int],
            payload.get("tile_cost_by_name", {}),
        )
        tile_cost_by_name = {
            str(key): float(value)
            for key, value in tile_cost_by_name_raw.items()
        }
        tie_breaker_raw = str(payload.get("tie_breaker", "fifo"))
        tie_breaker: Literal["fifo", "lower-heuristic", "lower-cost"] = "fifo"
        if tie_breaker_raw in {"fifo", "lower-heuristic", "lower-cost"}:
            tie_breaker = cast(
                Literal["fifo", "lower-heuristic", "lower-cost"],
                tie_breaker_raw,
            )

        smoothing_mode_raw = str(payload.get("smoothing_mode", "none"))
        smoothing_mode: Literal["none", "collinear"] = "none"
        if smoothing_mode_raw in {"none", "collinear"}:
            smoothing_mode = cast(
                Literal["none", "collinear"], smoothing_mode_raw
            )

        max_expanded_nodes_raw = payload.get("max_expanded_nodes")
        max_expanded_nodes = (
            int(cast(int, max_expanded_nodes_raw))
            if max_expanded_nodes_raw is not None
            else None
        )
        max_total_cost_raw = payload.get("max_total_cost")
        max_total_cost = (
            float(cast(float | int, max_total_cost_raw))
            if max_total_cost_raw is not None
            else None
        )
        map_state_token = cast(
            str | int | None, payload.get("map_state_token")
        )

        return cls(
            blocked_coordinates=blocked_coordinates,
            block_characters=bool(payload.get("block_characters", False)),
            block_map_objects=bool(payload.get("block_map_objects", False)),
            allow_end_occupied=bool(payload.get("allow_end_occupied", True)),
            allow_start_blocked=bool(payload.get("allow_start_blocked", True)),
            allow_diagonal_movement=bool(
                payload.get("allow_diagonal_movement", False)
            ),
            allow_corner_cutting=bool(
                payload.get("allow_corner_cutting", False)
            ),
            tile_cost_by_name=tile_cost_by_name,
            actor_capabilities=actor_capabilities,
            turn_penalty=float(
                cast(float | int, payload.get("turn_penalty", 0.0))
            ),
            blocker_proximity_cost=float(
                cast(float | int, payload.get("blocker_proximity_cost", 0.0))
            ),
            tie_breaker=tie_breaker,
            max_expanded_nodes=max_expanded_nodes,
            max_total_cost=max_total_cost,
            smoothing_mode=smoothing_mode,
            enable_result_cache=bool(
                payload.get("enable_result_cache", False)
            ),
            cache_namespace=str(payload.get("cache_namespace", "default")),
            map_state_token=map_state_token,
        )

    @classmethod
    def _validate_serialized_profile_payload(
        cls,
        payload: dict[str, object],
    ) -> None:
        unknown_keys = set(payload.keys()) - cls._SERIALIZED_PROFILE_FIELDS
        if unknown_keys:
            joined = ", ".join(sorted(unknown_keys))
            raise ValueError(f"Unknown profile fields: {joined}")

        cls._validate_profile_bool_fields(payload)
        cls._validate_profile_scalar_fields(payload)
        cls._validate_profile_numeric_fields(payload)
        cls._validate_profile_enum_fields(payload)
        cls._validate_profile_collection_fields(payload)

    @classmethod
    def _validate_profile_bool_fields(
        cls,
        payload: dict[str, object],
    ) -> None:

        bool_fields = {
            "block_characters",
            "block_map_objects",
            "allow_end_occupied",
            "allow_start_blocked",
            "allow_diagonal_movement",
            "allow_corner_cutting",
            "enable_result_cache",
        }
        for field_name in bool_fields:
            if field_name in payload and not isinstance(
                payload[field_name], bool
            ):
                raise ValueError(f"Field '{field_name}' must be a boolean.")

    @classmethod
    def _validate_profile_scalar_fields(
        cls,
        payload: dict[str, object],
    ) -> None:

        if "cache_namespace" in payload and not isinstance(
            payload["cache_namespace"], str
        ):
            raise ValueError("Field 'cache_namespace' must be a string.")

        if (
            "map_state_token" in payload
            and payload["map_state_token"] is not None
        ):
            if not isinstance(
                payload["map_state_token"], (str, int)
            ) or isinstance(payload["map_state_token"], bool):
                raise ValueError(
                    "Field 'map_state_token' must be a string, integer, or null."
                )

    @classmethod
    def _validate_profile_numeric_fields(
        cls,
        payload: dict[str, object],
    ) -> None:

        numeric_fields = {
            "turn_penalty",
            "blocker_proximity_cost",
            "max_total_cost",
        }
        for field_name in numeric_fields:
            if field_name in payload and payload[field_name] is not None:
                value = payload[field_name]
                if not isinstance(value, (int, float)) or isinstance(
                    value, bool
                ):
                    raise ValueError(f"Field '{field_name}' must be a number.")
                if not math.isfinite(float(value)):
                    raise ValueError(f"Field '{field_name}' must be finite.")
                if (
                    field_name == "blocker_proximity_cost"
                    and float(value) < 0.0
                ):
                    raise ValueError(
                        "Field 'blocker_proximity_cost' must be non-negative."
                    )

        if (
            "max_expanded_nodes" in payload
            and payload["max_expanded_nodes"] is not None
        ):
            value = payload["max_expanded_nodes"]
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError(
                    "Field 'max_expanded_nodes' must be an integer."
                )
            if value < 0:
                raise ValueError(
                    "Field 'max_expanded_nodes' must be non-negative."
                )

        if (
            "max_total_cost" in payload
            and payload["max_total_cost"] is not None
        ):
            max_total_cost = float(
                cast(float | int, payload["max_total_cost"])
            )
            if max_total_cost < 0.0:
                raise ValueError(
                    "Field 'max_total_cost' must be non-negative."
                )

    @classmethod
    def _validate_profile_enum_fields(
        cls,
        payload: dict[str, object],
    ) -> None:

        if "tie_breaker" in payload:
            tie_breaker = payload["tie_breaker"]
            valid_ties = {"fifo", "lower-heuristic", "lower-cost"}
            if (
                not isinstance(tie_breaker, str)
                or tie_breaker not in valid_ties
            ):
                joined = ", ".join(sorted(valid_ties))
                raise ValueError(
                    f"Field 'tie_breaker' must be one of: {joined}."
                )

        if "smoothing_mode" in payload:
            smoothing_mode = payload["smoothing_mode"]
            valid_smoothing = {"none", "collinear"}
            if (
                not isinstance(smoothing_mode, str)
                or smoothing_mode not in valid_smoothing
            ):
                joined = ", ".join(sorted(valid_smoothing))
                raise ValueError(
                    f"Field 'smoothing_mode' must be one of: {joined}."
                )

    @classmethod
    def _validate_profile_collection_fields(
        cls,
        payload: dict[str, object],
    ) -> None:

        if "actor_capabilities" in payload:
            value = payload["actor_capabilities"]
            if not isinstance(value, (list, tuple, set, frozenset)):
                raise ValueError(
                    "Field 'actor_capabilities' must be a list of strings."
                )
            if not all(isinstance(item, str) for item in value):
                raise ValueError(
                    "Field 'actor_capabilities' must contain only strings."
                )

        if "tile_cost_by_name" in payload:
            value = payload["tile_cost_by_name"]
            if not isinstance(value, dict):
                raise ValueError(
                    "Field 'tile_cost_by_name' must be a dictionary."
                )
            for key, cost in value.items():
                if not isinstance(key, str):
                    raise ValueError(
                        "Field 'tile_cost_by_name' keys must be strings."
                    )
                if not isinstance(cost, (int, float)) or isinstance(
                    cost, bool
                ):
                    raise ValueError(
                        "Field 'tile_cost_by_name' values must be numbers."
                    )
                if not math.isfinite(float(cost)):
                    raise ValueError(
                        "Field 'tile_cost_by_name' values must be finite numbers."
                    )
                if float(cost) < 0.0:
                    raise ValueError(
                        "Field 'tile_cost_by_name' values must be non-negative."
                    )

        if "blocked_coordinates" in payload:
            value = payload["blocked_coordinates"]
            if not isinstance(value, (list, tuple, set, frozenset)):
                raise ValueError(
                    "Field 'blocked_coordinates' must be an iterable of coordinate pairs."
                )
            for item in value:
                if not isinstance(item, (list, tuple)) or len(item) != 2:
                    raise ValueError(
                        "Field 'blocked_coordinates' must contain [x, y] coordinate pairs."
                    )
                x_value, y_value = item
                if (
                    not isinstance(x_value, int)
                    or isinstance(x_value, bool)
                    or not isinstance(y_value, int)
                    or isinstance(y_value, bool)
                ):
                    raise ValueError(
                        "Field 'blocked_coordinates' values must be integers."
                    )

    @classmethod
    def for_player(
        cls,
        tier: Literal["relaxed", "standard", "strict"] = "standard",
    ) -> "PathfindingState":
        """Profile for player-style movement with selectable strictness tier."""
        presets: dict[str, dict[str, object]] = {
            "relaxed": {
                "allow_diagonal_movement": True,
                "allow_corner_cutting": True,
                "tie_breaker": "fifo",
                "smoothing_mode": "collinear",
            },
            "standard": {
                "allow_diagonal_movement": False,
                "allow_corner_cutting": False,
                "tie_breaker": "lower-heuristic",
                "smoothing_mode": "collinear",
            },
            "strict": {
                "allow_diagonal_movement": False,
                "allow_corner_cutting": False,
                "allow_start_blocked": False,
                "blocker_proximity_cost": 0.25,
                "tie_breaker": "lower-cost",
                "smoothing_mode": "none",
            },
        }
        return cls(
            actor_capabilities=frozenset({"walk"}),
            **cast(dict[str, Any], presets[tier]),
        )

    @classmethod
    def for_flying_enemy(
        cls,
        tier: Literal["relaxed", "standard", "strict"] = "standard",
    ) -> "PathfindingState":
        """Profile for flying enemies with selectable strictness tier."""
        presets: dict[str, dict[str, object]] = {
            "relaxed": {
                "allow_diagonal_movement": True,
                "allow_corner_cutting": True,
                "turn_penalty": 0.0,
                "tie_breaker": "fifo",
                "smoothing_mode": "collinear",
            },
            "standard": {
                "allow_diagonal_movement": True,
                "allow_corner_cutting": True,
                "tie_breaker": "lower-heuristic",
                "smoothing_mode": "collinear",
            },
            "strict": {
                "allow_diagonal_movement": True,
                "allow_corner_cutting": False,
                "turn_penalty": 0.35,
                "blocker_proximity_cost": 0.15,
                "tie_breaker": "lower-cost",
                "smoothing_mode": "none",
            },
        }
        return cls(
            actor_capabilities=frozenset({"walk", "flight"}),
            **cast(dict[str, Any], presets[tier]),
        )

    @classmethod
    def for_heavy_unit(
        cls,
        tier: Literal["relaxed", "standard", "strict"] = "standard",
    ) -> "PathfindingState":
        """Profile for heavy units with selectable strictness tier."""
        presets: dict[str, dict[str, object]] = {
            "relaxed": {
                "allow_diagonal_movement": False,
                "allow_corner_cutting": False,
                "turn_penalty": 0.2,
                "blocker_proximity_cost": 0.1,
                "tie_breaker": "lower-heuristic",
                "smoothing_mode": "none",
            },
            "standard": {
                "allow_diagonal_movement": False,
                "allow_corner_cutting": False,
                "turn_penalty": 0.5,
                "blocker_proximity_cost": 0.25,
                "tie_breaker": "lower-cost",
                "smoothing_mode": "none",
            },
            "strict": {
                "allow_diagonal_movement": False,
                "allow_corner_cutting": False,
                "allow_start_blocked": False,
                "turn_penalty": 0.8,
                "blocker_proximity_cost": 0.4,
                "tie_breaker": "lower-cost",
                "max_expanded_nodes": 1500,
                "smoothing_mode": "none",
            },
        }
        return cls(
            actor_capabilities=frozenset({"walk", "heavy"}),
            **cast(dict[str, Any], presets[tier]),
        )


@dataclass(frozen=True)
class PathfindingResult:
    """Structured result metadata for a pathfinding search."""

    found: bool
    path: list[Coordinates]
    total_cost: float | None
    visited_nodes: int
    expanded_nodes: int
    reason: Literal[
        "found",
        "start-out-of-range",
        "end-out-of-range",
        "end-not-passable",
        "start-not-passable",
        "unreachable",
        "search-budget-exhausted",
        "cost-budget-exhausted",
    ]
    from_cache: bool = False


class Map2dQueries:
    """Spatial query and pathfinding operations for a Map2d instance."""

    def __init__(self, map2d: "Map2d") -> None:
        self.map2d = map2d
        self._path_cache: dict[tuple[object, ...], PathfindingResult] = {}
        self._cache_epoch: int = 0

    def invalidate_path_cache(self) -> None:
        """Invalidate all cached pathfinding results."""
        self._cache_epoch += 1
        self._path_cache.clear()

    def iter_radius_hits(
        self,
        starting_coordinates: Coordinates,
        tile_names: Optional[list[str]] = None,
    ) -> Iterator[MapQueryResult]:
        """Yield query hits around a starting point for distances 1..radius-1."""
        x, y = starting_coordinates
        for i in range(1, self.map2d.character.radius):
            # north
            hit = self.get_coordinate_hit((x, y + i), tile_names)
            if hit is not None:
                yield hit
            # northeast
            hit = self.get_coordinate_hit((x + i, y + i), tile_names)
            if hit is not None:
                yield hit
            # east
            hit = self.get_coordinate_hit((x + i, y), tile_names)
            if hit is not None:
                yield hit
            # southeast
            hit = self.get_coordinate_hit((x + i, y - i), tile_names)
            if hit is not None:
                yield hit
            # south
            hit = self.get_coordinate_hit((x, y - i), tile_names)
            if hit is not None:
                yield hit
            # southwest
            hit = self.get_coordinate_hit((x - i, y - i), tile_names)
            if hit is not None:
                yield hit
            # west
            hit = self.get_coordinate_hit((x - i, y), tile_names)
            if hit is not None:
                yield hit
            # northwest
            hit = self.get_coordinate_hit((x - i, y + i), tile_names)
            if hit is not None:
                yield hit

    def get_coordinate_hit(
        self,
        coordinates: Coordinates,
        tile_names: Optional[list[str]] = None,
    ) -> Optional[MapQueryResult]:
        """Return a typed query hit for coordinates, or None if out-of-range."""
        resolved_tile_names: list[str] = tile_names or []
        if not self.is_coordinates_in_range(coordinates):
            return None

        map_object: Optional[MapObject] = (
            self.map2d.object_index[coordinates]
            if coordinates in self.map2d.object_index
            else None
        )
        character: Optional[Character] = (
            self.map2d.character_index[coordinates]
            if coordinates in self.map2d.character_index
            else None
        )
        tile: Optional[MapTile] = None
        if resolved_tile_names:
            resolved_tile: MapTile = self.map2d.get_tile(coordinates)
            if resolved_tile.name in resolved_tile_names:
                tile = resolved_tile

            # When tile filters are supplied, skip empty hits that do not
            # match any requested tile and have no character/object occupants.
            if tile is None and character is None and map_object is None:
                return None

        return MapQueryResult(
            coordinates=coordinates,
            tile=tile,
            character=character,
            map_object=map_object,
        )

    def find_path(
        self,
        start: Coordinates,
        end: Coordinates,
        state: Optional[PathfindingState] = None,
    ) -> list[Coordinates]:
        """Find and return the lowest-cost passable coordinate path between points."""
        return self.find_path_result(start, end, state=state).path

    def find_path_result(
        self,
        start: Coordinates,
        end: Coordinates,
        state: Optional[PathfindingState] = None,
    ) -> PathfindingResult:
        """Find a path and return path + diagnostic metadata."""
        self._validate_state(state)
        cache_key: tuple[object, ...] | None = self._make_cache_key(
            start, end, state
        )
        if cache_key is not None and cache_key in self._path_cache:
            cached = self._path_cache[cache_key]
            return PathfindingResult(
                found=cached.found,
                path=list(cached.path),
                total_cost=cached.total_cost,
                visited_nodes=cached.visited_nodes,
                expanded_nodes=cached.expanded_nodes,
                reason=cached.reason,
                from_cache=True,
            )

        if not self.is_coordinates_in_range(start):
            result = PathfindingResult(
                found=False,
                path=[],
                total_cost=None,
                visited_nodes=0,
                expanded_nodes=0,
                reason="start-out-of-range",
            )
            self._store_cached_result(cache_key, result)
            return result
        if not self.is_coordinates_in_range(end):
            result = PathfindingResult(
                found=False,
                path=[],
                total_cost=None,
                visited_nodes=0,
                expanded_nodes=0,
                reason="end-out-of-range",
            )
            self._store_cached_result(cache_key, result)
            return result
        if start == end:
            result = PathfindingResult(
                found=True,
                path=[start],
                total_cost=0.0,
                visited_nodes=1,
                expanded_nodes=0,
                reason="found",
            )
            self._store_cached_result(cache_key, result)
            return result

        if not self.is_tile_passable(end, state=state, end=end):
            result = PathfindingResult(
                found=False,
                path=[],
                total_cost=None,
                visited_nodes=0,
                expanded_nodes=0,
                reason="end-not-passable",
            )
            self._store_cached_result(cache_key, result)
            return result
        if (
            state is not None
            and not state.allow_start_blocked
            and not self.is_tile_passable(start, state=state, end=end)
        ):
            result = PathfindingResult(
                found=False,
                path=[],
                total_cost=None,
                visited_nodes=0,
                expanded_nodes=0,
                reason="start-not-passable",
            )
            self._store_cached_result(cache_key, result)
            return result

        open_heap: list[
            tuple[float, float, float, float, int, Coordinates]
        ] = []
        start_heuristic = self._heuristic(start, end, state)
        heappush(
            open_heap,
            self._priority_item(
                heuristic=start_heuristic,
                path_cost=0.0,
                counter=0,
                coordinates=start,
                state=state,
            ),
        )
        best_cost: dict[Coordinates, float] = {start: 0.0}
        parents: dict[Coordinates, Coordinates] = {}
        visit_counter = 1
        expanded_nodes = 0
        cost_budget_blocked = False

        while len(open_heap) > 0:
            (
                _estimated_total,
                queued_cost,
                _tie_primary,
                _tie_secondary,
                _order,
                node,
            ) = heappop(open_heap)
            current_cost = best_cost.get(node, float("inf"))
            if queued_cost > current_cost:
                continue
            expanded_nodes += 1

            if (
                state is not None
                and state.max_expanded_nodes is not None
                and expanded_nodes > state.max_expanded_nodes
            ):
                result = PathfindingResult(
                    found=False,
                    path=[],
                    total_cost=None,
                    visited_nodes=len(best_cost),
                    expanded_nodes=expanded_nodes,
                    reason="search-budget-exhausted",
                )
                self._store_cached_result(cache_key, result)
                return result

            if node == end:
                found_path = self._build_path(parents, end)
                if state is not None and state.smoothing_mode == "collinear":
                    found_path = self._smooth_collinear(found_path)
                result = PathfindingResult(
                    found=True,
                    path=found_path,
                    total_cost=current_cost,
                    visited_nodes=len(best_cost),
                    expanded_nodes=expanded_nodes,
                    reason="found",
                )
                self._store_cached_result(cache_key, result)
                return result

            for item in self.get_adjacent_passable_coordinates(
                node,
                state=state,
                end=end,
            ):
                new_cost = current_cost + self._movement_cost(
                    node, item, state, parents=parents
                )
                if (
                    state is not None
                    and state.max_total_cost is not None
                    and new_cost > state.max_total_cost
                ):
                    cost_budget_blocked = True
                    continue
                if new_cost < best_cost.get(item, float("inf")):
                    best_cost[item] = new_cost
                    parents[item] = node
                    heuristic = self._heuristic(item, end, state)
                    heappush(
                        open_heap,
                        self._priority_item(
                            heuristic=heuristic,
                            path_cost=new_cost,
                            counter=visit_counter,
                            coordinates=item,
                            state=state,
                        ),
                    )
                    visit_counter += 1

        reason: Literal["unreachable", "cost-budget-exhausted"] = (
            "cost-budget-exhausted" if cost_budget_blocked else "unreachable"
        )
        result = PathfindingResult(
            found=False,
            path=[],
            total_cost=None,
            visited_nodes=len(best_cost),
            expanded_nodes=expanded_nodes,
            reason=reason,
        )
        self._store_cached_result(cache_key, result)
        return result

    def get_adjacent_passable_coordinates(
        self,
        coordinates: Coordinates,
        state: Optional[PathfindingState] = None,
        end: Optional[Coordinates] = None,
    ) -> list[Coordinates]:
        """Return cardinally adjacent coordinates that are passable."""
        x, y = coordinates
        adjacent_coordinates: list[Coordinates] = []
        for dx, dy, direction in self._neighbor_steps(state):
            candidate: Coordinates = (x + dx, y + dy)
            if not self.is_tile_passable(
                candidate,
                state=state,
                end=end,
                from_coordinates=coordinates,
                move_direction=direction,
            ):
                continue

            if (
                abs(dx) == 1
                and abs(dy) == 1
                and state is not None
                and not state.allow_corner_cutting
            ):
                horizontal: Coordinates = (x + dx, y)
                vertical: Coordinates = (x, y + dy)
                if not self.is_tile_passable(
                    horizontal,
                    state=state,
                    end=end,
                    from_coordinates=coordinates,
                ):
                    continue
                if not self.is_tile_passable(
                    vertical,
                    state=state,
                    end=end,
                    from_coordinates=coordinates,
                ):
                    continue

            adjacent_coordinates.append(candidate)

        return adjacent_coordinates

    def is_tile_passable(
        self,
        coordinates: Coordinates,
        state: Optional[PathfindingState] = None,
        end: Optional[Coordinates] = None,
        from_coordinates: Optional[Coordinates] = None,
        move_direction: Optional[Direction] = None,
    ) -> bool:
        """Return whether a tile can currently be traversed."""
        if not self.is_coordinates_in_range(coordinates):
            return False

        tile: MapTile = self.map2d.get_tile(coordinates)
        if not tile.is_passable:
            return False

        if (
            tile.allowed_entry_directions is not None
            and from_coordinates is not None
        ):
            resolved_direction = (
                move_direction
                or self._resolve_move_direction(from_coordinates, coordinates)
            )
            if resolved_direction not in tile.allowed_entry_directions:
                return False

        if tile.required_capabilities:
            actor_capabilities = (
                state.actor_capabilities if state is not None else frozenset()
            )
            if not tile.required_capabilities.issubset(actor_capabilities):
                return False

        if state is None:
            return True

        if coordinates in state.blocked_coordinates:
            return False

        is_goal = end is not None and coordinates == end
        if (
            state.block_characters
            and coordinates in self.map2d.character_index
        ):
            if not (is_goal and state.allow_end_occupied):
                return False
        if state.block_map_objects and coordinates in self.map2d.object_index:
            if not (is_goal and state.allow_end_occupied):
                return False

        return True

    @staticmethod
    def _neighbor_steps(
        state: Optional[PathfindingState],
    ) -> tuple[tuple[int, int, Direction], ...]:
        cardinal_steps: tuple[tuple[int, int, Direction], ...] = (
            (0, 1, Direction.UP),
            (1, 0, Direction.RIGHT),
            (0, -1, Direction.DOWN),
            (-1, 0, Direction.LEFT),
        )
        if state is None or not state.allow_diagonal_movement:
            return cardinal_steps

        diagonal_steps: tuple[tuple[int, int, Direction], ...] = (
            (1, 1, Direction.DIAGONAL_UPPER_RIGHT),
            (1, -1, Direction.DIAGONAL_LOWER_RIGHT),
            (-1, -1, Direction.DIAGONAL_LOWER_LEFT),
            (-1, 1, Direction.DIAGONAL_UPPER_LEFT),
        )
        return cardinal_steps + diagonal_steps

    @staticmethod
    def _resolve_move_direction(
        from_coordinates: Coordinates, to_coordinates: Coordinates
    ) -> Direction:
        dx = to_coordinates[0] - from_coordinates[0]
        dy = to_coordinates[1] - from_coordinates[1]
        direction_map: dict[tuple[int, int], Direction] = {
            (0, 1): Direction.UP,
            (1, 1): Direction.DIAGONAL_UPPER_RIGHT,
            (1, 0): Direction.RIGHT,
            (1, -1): Direction.DIAGONAL_LOWER_RIGHT,
            (0, -1): Direction.DOWN,
            (-1, -1): Direction.DIAGONAL_LOWER_LEFT,
            (-1, 0): Direction.LEFT,
            (-1, 1): Direction.DIAGONAL_UPPER_LEFT,
        }
        if (dx, dy) not in direction_map:
            raise ValueError(
                f"Unsupported movement from {from_coordinates} to {to_coordinates}."
            )
        return direction_map[(dx, dy)]

    @staticmethod
    def _build_path(
        parents: dict[Coordinates, Coordinates], end: Coordinates
    ) -> list[Coordinates]:
        path: list[Coordinates] = [end]
        while path[-1] in parents:
            path.append(parents[path[-1]])
        path.reverse()
        return path

    def _movement_cost(
        self,
        from_coordinates: Coordinates,
        to_coordinates: Coordinates,
        state: Optional[PathfindingState],
        parents: dict[Coordinates, Coordinates],
    ) -> float:
        dx = abs(to_coordinates[0] - from_coordinates[0])
        dy = abs(to_coordinates[1] - from_coordinates[1])
        is_diagonal = dx == 1 and dy == 1
        base_cost = math.sqrt(2.0) if is_diagonal else 1.0

        tile = self.map2d.get_tile(to_coordinates)
        extra_cost = 0.0
        if state is not None:
            if tile.name in state.tile_cost_by_name:
                extra_cost = state.tile_cost_by_name[tile.name]
            if state.tile_cost_resolver is not None:
                extra_cost = state.tile_cost_resolver(tile, to_coordinates)
            for layer in state.dynamic_cost_layers:
                extra_cost += layer(tile, to_coordinates)

            if state.turn_penalty > 0 and from_coordinates in parents:
                previous = parents[from_coordinates]
                previous_direction = self._resolve_move_direction(
                    previous, from_coordinates
                )
                current_direction = self._resolve_move_direction(
                    from_coordinates, to_coordinates
                )
                if previous_direction != current_direction:
                    extra_cost += state.turn_penalty

            if state.blocker_proximity_cost > 0:
                extra_cost += (
                    state.blocker_proximity_cost
                    * self._count_blockers_adjacent(
                        to_coordinates,
                        state,
                    )
                )

        if extra_cost < 0:
            raise ValueError(
                f"Pathfinding tile costs must be non-negative. Got {extra_cost} for tile '{tile.name}' at {to_coordinates}."
            )
        return base_cost + extra_cost

    @staticmethod
    def _heuristic(
        coordinates: Coordinates,
        end: Coordinates,
        state: Optional[PathfindingState],
    ) -> float:
        dx = abs(end[0] - coordinates[0])
        dy = abs(end[1] - coordinates[1])
        if state is not None and state.allow_diagonal_movement:
            diagonal_steps = min(dx, dy)
            straight_steps = max(dx, dy) - diagonal_steps
            return math.sqrt(2.0) * diagonal_steps + straight_steps
        return float(dx + dy)

    def is_coordinates_in_range(self, coordinates: Coordinates) -> bool:
        """Return whether coordinates are within map bounds."""
        return (
            coordinates[0] >= 0
            and coordinates[0] < self.map2d.width
            and coordinates[1] >= 0
            and coordinates[1] < self.map2d.height
        )

    def _validate_state(self, state: Optional[PathfindingState]) -> None:
        if state is None:
            return
        if state.turn_penalty < 0:
            raise ValueError("turn_penalty must be non-negative.")
        if state.blocker_proximity_cost < 0:
            raise ValueError("blocker_proximity_cost must be non-negative.")
        if (
            state.max_expanded_nodes is not None
            and state.max_expanded_nodes < 1
        ):
            raise ValueError("max_expanded_nodes must be >= 1.")
        if state.max_total_cost is not None and state.max_total_cost < 0:
            raise ValueError("max_total_cost must be non-negative.")

    def _count_blockers_adjacent(
        self,
        coordinates: Coordinates,
        state: PathfindingState,
    ) -> int:
        x, y = coordinates
        neighbors = ((x, y + 1), (x + 1, y), (x, y - 1), (x - 1, y))
        blocked = 0
        for neighbor in neighbors:
            if not self.is_coordinates_in_range(neighbor):
                blocked += 1
                continue
            tile = self.map2d.get_tile(neighbor)
            if not tile.is_passable:
                blocked += 1
                continue
            if (
                state.block_characters
                and neighbor in self.map2d.character_index
            ):
                blocked += 1
                continue
            if state.block_map_objects and neighbor in self.map2d.object_index:
                blocked += 1
                continue
            if neighbor in state.blocked_coordinates:
                blocked += 1
        return blocked

    def _priority_item(
        self,
        heuristic: float,
        path_cost: float,
        counter: int,
        coordinates: Coordinates,
        state: Optional[PathfindingState],
    ) -> tuple[float, float, float, float, int, Coordinates]:
        estimated_total = path_cost + heuristic
        if state is None or state.tie_breaker == "fifo":
            tie_primary = 0.0
            tie_secondary = 0.0
        elif state.tie_breaker == "lower-heuristic":
            tie_primary = heuristic
            tie_secondary = path_cost
        else:
            tie_primary = path_cost
            tie_secondary = heuristic
        return (
            estimated_total,
            path_cost,
            tie_primary,
            tie_secondary,
            counter,
            coordinates,
        )

    @staticmethod
    def _smooth_collinear(path: list[Coordinates]) -> list[Coordinates]:
        if len(path) < 3:
            return path
        smoothed: list[Coordinates] = [path[0]]
        for index in range(1, len(path) - 1):
            prev = smoothed[-1]
            current = path[index]
            nxt = path[index + 1]
            dx1 = current[0] - prev[0]
            dy1 = current[1] - prev[1]
            dx2 = nxt[0] - current[0]
            dy2 = nxt[1] - current[1]
            if (dx1, dy1) == (dx2, dy2):
                continue
            smoothed.append(current)
        smoothed.append(path[-1])
        return smoothed

    def _make_cache_key(
        self,
        start: Coordinates,
        end: Coordinates,
        state: Optional[PathfindingState],
    ) -> tuple[object, ...] | None:
        if state is None or not state.enable_result_cache:
            return None
        return (
            self._cache_epoch,
            state.cache_namespace,
            state.map_state_token,
            start,
            end,
            state.blocked_coordinates,
            state.block_characters,
            state.block_map_objects,
            state.allow_end_occupied,
            state.allow_start_blocked,
            state.allow_diagonal_movement,
            state.allow_corner_cutting,
            tuple(sorted(state.tile_cost_by_name.items())),
            id(state.tile_cost_resolver) if state.tile_cost_resolver else None,
            tuple(id(layer) for layer in state.dynamic_cost_layers),
            state.actor_capabilities,
            state.turn_penalty,
            state.blocker_proximity_cost,
            state.tie_breaker,
            state.max_expanded_nodes,
            state.max_total_cost,
            state.smoothing_mode,
        )

    def _store_cached_result(
        self,
        cache_key: tuple[object, ...] | None,
        result: PathfindingResult,
    ) -> None:
        if cache_key is None:
            return
        self._path_cache[cache_key] = result
