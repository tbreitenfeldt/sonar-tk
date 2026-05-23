from pathlib import Path
import json
import pytest

from sonartk.map_builder.map_2d.map_2d import Map2d
from sonartk.map_builder.map_2d.map_queries import PathfindingState
from sonartk.map_builder.map_2d.map_tile import MapTile
from sonartk.map_builder.map_2d.map_object import MapObject
from sonartk.map_builder.map_2d.map_object.character import Character
from sonartk.util import Direction


def make_map() -> Map2d:
    character = Character("hero", (1, 1), Direction.UP, radius=3)
    map2d = Map2d("arena", character)
    map2d.add_row([MapTile("a"), MapTile("b"), MapTile("c")])
    map2d.add_row([MapTile("d"), MapTile("e"), MapTile("f")])
    map2d.add_row([MapTile("g"), MapTile("h"), MapTile("i")])
    return map2d


def test_map2d_init_sets_defaults_and_character_registration() -> None:
    character = Character("hero", (2, 3), Direction.LEFT)

    map2d = Map2d("world", character)

    assert map2d.name == "world"
    assert map2d.character is character
    assert map2d.width == 0
    assert map2d.height == 0
    assert map2d.queries.map2d is map2d
    assert map2d.character_index[(2, 3)] is character


def test_register_and_remove_character_use_entity_coordinates() -> None:
    map2d = make_map()
    ally = Character("ally", (0, 2), Direction.RIGHT)

    map2d.register_character(ally)

    assert map2d.character_index[(0, 2)] is ally

    map2d.remove_character(ally)

    assert (0, 2) not in map2d.character_index


def test_register_character_raises_on_coordinate_collision_by_default() -> (
    None
):
    map2d = make_map()
    intruder = Character("intruder", (1, 1), Direction.LEFT)

    with pytest.raises(ValueError, match="coordinate collision"):
        map2d.register_character(intruder)


def test_register_character_replaces_when_policy_allows() -> None:
    hero = Character("hero", (1, 1), Direction.UP)
    map2d = Map2d(
        "world",
        hero,
        character_collision_policy="replace",
    )
    replacement = Character("replacement", (1, 1), Direction.LEFT)

    displaced = map2d.register_character(replacement)

    assert displaced is hero
    assert map2d.character_index[(1, 1)] is replacement


def test_move_character_uses_registered_entity_coordinates() -> None:
    map2d = make_map()
    ally = Character("ally", (0, 0), Direction.RIGHT)
    map2d.register_character(ally)

    map2d.move_character(ally, (2, 0))

    assert ally.coordinates == (2, 0)
    assert (0, 0) not in map2d.character_index
    assert map2d.character_index[(2, 0)] is ally


def test_move_character_raises_on_coordinate_collision_by_default() -> None:
    map2d = make_map()
    ally = Character("ally", (0, 0), Direction.RIGHT)
    blocker = Character("blocker", (2, 0), Direction.LEFT)
    map2d.register_character(ally)
    map2d.register_character(blocker)

    with pytest.raises(ValueError, match="coordinate collision"):
        map2d.move_character(ally, (2, 0))


def test_move_character_replaces_when_policy_allows() -> None:
    map2d = Map2d(
        "world",
        Character("hero", (1, 1), Direction.UP),
        character_collision_policy="replace",
    )
    map2d.add_row([MapTile("x"), MapTile("y")])
    map2d.add_row([MapTile("a"), MapTile("b")])
    ally = Character("ally", (0, 0), Direction.RIGHT)
    blocker = Character("blocker", (1, 0), Direction.LEFT)
    map2d.register_character(ally)
    map2d.register_character(blocker)

    displaced = map2d.move_character(ally, (1, 0))

    assert displaced is blocker
    assert map2d.character_index[(1, 0)] is ally
    assert blocker.coordinates == (1, 0)


def test_register_move_and_remove_map_object_use_entity_coordinates() -> None:
    map2d = make_map()
    obj = MapObject("switch", (1, 2))

    map2d.register_map_object(obj)
    map2d.move_map_object(obj, (2, 2))

    assert obj.coordinates == (2, 2)
    assert (1, 2) not in map2d.object_index
    assert map2d.object_index[(2, 2)] is obj

    map2d.remove_map_object(obj)

    assert (2, 2) not in map2d.object_index


def test_register_map_object_raises_on_coordinate_collision_by_default() -> (
    None
):
    map2d = make_map()
    chest = MapObject("chest", (1, 1))
    orb = MapObject("orb", (1, 1))

    map2d.register_map_object(chest)

    with pytest.raises(ValueError, match="coordinate collision"):
        map2d.register_map_object(orb)


def test_move_map_object_replaces_when_policy_allows() -> None:
    map2d = Map2d(
        "world",
        Character("hero", (1, 1), Direction.UP),
        object_collision_policy="replace",
    )
    map2d.add_row([MapTile("x"), MapTile("y")])
    map2d.add_row([MapTile("a"), MapTile("b")])
    chest = MapObject("chest", (0, 0))
    orb = MapObject("orb", (1, 0))
    map2d.register_map_object(chest)
    map2d.register_map_object(orb)

    displaced = map2d.move_map_object(chest, (1, 0))

    assert displaced is orb
    assert map2d.object_index[(1, 0)] is chest
    assert orb.coordinates == (1, 0)


def test_add_row_sets_width_and_updates_height() -> None:
    map2d = Map2d("world", Character("hero", (0, 0), Direction.UP))

    map2d.add_row([MapTile("x"), MapTile("y")])
    map2d.add_row([MapTile("a"), MapTile("b")])

    assert map2d.width == 2
    assert map2d.height == 2


def test_add_row_prepends_new_rows_at_y_zero() -> None:
    map2d = Map2d("world", Character("hero", (0, 0), Direction.UP))

    map2d.add_row([MapTile("old-left"), MapTile("old-right")])
    map2d.add_row([MapTile("new-left"), MapTile("new-right")])

    assert map2d.get_tile((0, 0)).name == "new-left"
    assert map2d.get_tile((1, 0)).name == "new-right"
    assert map2d.get_tile((0, 1)).name == "old-left"
    assert map2d.get_tile((1, 1)).name == "old-right"


def test_add_row_rejects_inconsistent_width() -> None:
    map2d = Map2d("world", Character("hero", (0, 0), Direction.UP))
    map2d.add_row([MapTile("x"), MapTile("y")])

    with pytest.raises(IndexError, match="Map Width: 2"):
        map2d.add_row([MapTile("too-short")])


def test_get_tile_returns_expected_tile() -> None:
    map2d = make_map()

    assert map2d.get_tile((0, 0)).name == "g"
    assert map2d.get_tile((2, 2)).name == "c"


def test_get_tile_raises_for_out_of_range_coordinates() -> None:
    map2d = make_map()

    with pytest.raises(IndexError):
        map2d.get_tile((-1, 0))
    with pytest.raises(IndexError):
        map2d.get_tile((0, -1))
    with pytest.raises(IndexError):
        map2d.get_tile((3, 0))
    with pytest.raises(IndexError):
        map2d.get_tile((0, 3))


def test_character_and_object_coordinate_changes() -> None:
    map2d = make_map()
    ally = Character("ally", (0, 0), Direction.RIGHT)
    obj = MapObject("switch", (1, 0))

    map2d.register_character(ally)
    map2d.register_map_object(obj)
    map2d.move_character(ally, (2, 2))
    map2d.move_map_object(obj, (0, 2))

    assert (0, 0) not in map2d.character_index
    assert map2d.character_index[(2, 2)] is ally
    assert ally.coordinates == (2, 2)
    assert (1, 0) not in map2d.object_index
    assert map2d.object_index[(0, 2)] is obj
    assert obj.coordinates == (0, 2)


def test_change_character_and_object_coordinates_raise_when_missing() -> None:
    map2d = make_map()
    character = Character("ghost", (5, 5), Direction.DOWN)
    obj = MapObject("orb", (5, 5))

    with pytest.raises(LookupError):
        map2d.move_character(character, (0, 0))
    with pytest.raises(LookupError):
        map2d.move_map_object(obj, (0, 0))


def test_get_coordinate_hit_reports_tile_character_and_object() -> None:
    map2d = make_map()
    target_character = Character("target", (2, 1), Direction.UP)
    target_object = MapObject("chest", (2, 1))
    map2d.register_character(target_character)
    map2d.register_map_object(target_object)

    hit = map2d.queries.get_coordinate_hit((2, 1), tile_names=["f"])

    assert hit is not None
    assert hit.coordinates == (2, 1)
    assert hit.tile is not None and hit.tile.name == "f"
    assert hit.character is target_character
    assert hit.map_object is target_object


def test_get_coordinate_hit_returns_none_out_of_range() -> None:
    map2d = make_map()
    hit = map2d.queries.get_coordinate_hit((-1, 1))

    assert hit is None


def test_get_coordinate_hit_returns_none_when_tile_filter_misses() -> None:
    map2d = make_map()

    hit = map2d.queries.get_coordinate_hit((2, 1), tile_names=["not-f"])

    assert hit is None


def test_check_radius_scans_surrounding_tiles() -> None:
    map2d = make_map()
    hits = list(map2d.queries.iter_radius_hits((1, 1)))
    seen = {hit.coordinates for hit in hits}

    expected = {
        (1, 2),
        (2, 2),
        (2, 1),
        (2, 0),
        (1, 0),
        (0, 0),
        (0, 1),
        (0, 2),
    }
    assert seen == expected


def test_check_radius_with_tile_filter_only_returns_matching_hits() -> None:
    map2d = make_map()

    hits = list(map2d.queries.iter_radius_hits((1, 1), tile_names=["f"]))

    assert [hit.coordinates for hit in hits] == [(2, 1)]
    assert hits[0].tile is not None and hits[0].tile.name == "f"


def test_check_radius_with_radius_one_scans_nothing() -> None:
    character = Character("hero", (1, 1), Direction.UP, radius=1)
    map2d = Map2d("arena", character)
    map2d.add_row([MapTile("a"), MapTile("b"), MapTile("c")])
    map2d.add_row([MapTile("d"), MapTile("e"), MapTile("f")])
    map2d.add_row([MapTile("g"), MapTile("h"), MapTile("i")])

    hits = list(map2d.queries.iter_radius_hits((1, 1)))

    assert hits == []


def test_find_path_returns_empty_when_unreachable() -> None:
    map2d = make_map()
    for tile in map2d.tile_map:
        tile.is_passable = False

    path = map2d.queries.find_path((0, 0), (2, 2))

    assert path == []


def test_find_path_returns_path_when_reachable() -> None:
    map2d = make_map()

    path = map2d.queries.find_path((0, 0), (1, 0))

    assert path[0] == (0, 0)
    assert path[-1] == (1, 0)


def test_find_path_returns_shortest_path() -> None:
    map2d = make_map()

    path = map2d.queries.find_path((0, 0), (0, 1))

    assert path == [(0, 0), (0, 1)]


def test_find_path_returns_start_when_start_equals_end() -> None:
    map2d = make_map()

    path = map2d.queries.find_path((1, 1), (1, 1))

    assert path == [(1, 1)]


def test_find_path_returns_empty_for_out_of_range_start() -> None:
    map2d = make_map()

    path = map2d.queries.find_path((-1, 0), (1, 0))

    assert path == []


def test_find_path_returns_empty_for_out_of_range_end() -> None:
    map2d = make_map()

    path = map2d.queries.find_path((0, 0), (3, 0))

    assert path == []


def test_find_path_handles_revisits_without_requeueing() -> None:
    map2d = make_map()

    # Use an out-of-range destination so traversal explores all reachable
    # nodes and encounters already-visited neighbors in the open grid.
    path = map2d.queries.find_path((0, 0), (5, 5))

    assert path == []


def test_find_path_respects_blocked_coordinates_state() -> None:
    map2d = make_map()

    path = map2d.queries.find_path(
        (0, 0),
        (2, 0),
        state=PathfindingState(blocked_coordinates={(1, 0)}),
    )

    assert path != []
    assert (1, 0) not in path
    assert path[0] == (0, 0)
    assert path[-1] == (2, 0)


def test_find_path_can_block_characters_from_traversal() -> None:
    map2d = make_map()
    blocker = Character("blocker", (1, 0), Direction.LEFT)
    map2d.register_character(blocker)

    path = map2d.queries.find_path(
        (0, 0),
        (2, 0),
        state=PathfindingState(block_characters=True),
    )

    assert path != []
    assert (1, 0) not in path
    assert path[0] == (0, 0)
    assert path[-1] == (2, 0)


def test_find_path_allows_occupied_end_by_default() -> None:
    map2d = make_map()
    occupant = Character("occupant", (2, 0), Direction.LEFT)
    map2d.register_character(occupant)

    path = map2d.queries.find_path(
        (0, 0),
        (2, 0),
        state=PathfindingState(block_characters=True),
    )

    assert path[-1] == (2, 0)


def test_find_path_can_disallow_occupied_end() -> None:
    map2d = make_map()
    occupant = Character("occupant", (2, 0), Direction.LEFT)
    map2d.register_character(occupant)

    path = map2d.queries.find_path(
        (0, 0),
        (2, 0),
        state=PathfindingState(
            block_characters=True,
            allow_end_occupied=False,
        ),
    )

    assert path == []


def test_find_path_can_block_map_objects_from_traversal() -> None:
    map2d = make_map()
    blocker = MapObject("blocker", (1, 0))
    map2d.register_map_object(blocker)

    path = map2d.queries.find_path(
        (0, 0),
        (2, 0),
        state=PathfindingState(block_map_objects=True),
    )

    assert path != []
    assert (1, 0) not in path
    assert path[0] == (0, 0)
    assert path[-1] == (2, 0)


def test_find_path_allows_blocked_start_by_default() -> None:
    map2d = make_map()

    path = map2d.queries.find_path(
        (1, 0),
        (2, 0),
        state=PathfindingState(blocked_coordinates={(1, 0)}),
    )

    assert path == [(1, 0), (2, 0)]


def test_find_path_can_disallow_blocked_start() -> None:
    map2d = make_map()

    path = map2d.queries.find_path(
        (1, 0),
        (2, 0),
        state=PathfindingState(
            blocked_coordinates={(1, 0)},
            allow_start_blocked=False,
        ),
    )

    assert path == []


def test_find_path_prefers_lower_total_cost_over_fewer_steps() -> None:
    map2d = make_map()

    path = map2d.queries.find_path(
        (0, 0),
        (2, 0),
        state=PathfindingState(tile_cost_by_name={"h": 10.0}),
    )

    assert path != []
    assert (1, 0) not in path
    assert path[0] == (0, 0)
    assert path[-1] == (2, 0)


def test_find_path_supports_custom_tile_cost_resolver() -> None:
    map2d = make_map()

    path = map2d.queries.find_path(
        (0, 0),
        (2, 0),
        state=PathfindingState(
            tile_cost_resolver=lambda tile, _coords: (
                5.0 if tile.name == "h" else 0.0
            )
        ),
    )

    assert path != []
    assert (1, 0) not in path
    assert path[0] == (0, 0)
    assert path[-1] == (2, 0)


def test_find_path_raises_when_tile_cost_is_negative() -> None:
    map2d = make_map()

    with pytest.raises(ValueError, match="non-negative"):
        map2d.queries.find_path(
            (0, 0),
            (2, 0),
            state=PathfindingState(tile_cost_by_name={"h": -1.0}),
        )


def test_find_path_result_returns_metadata_for_success() -> None:
    map2d = make_map()

    result = map2d.queries.find_path_result((0, 0), (2, 0))

    assert result.found is True
    assert result.reason == "found"
    assert result.path[0] == (0, 0)
    assert result.path[-1] == (2, 0)
    assert result.total_cost is not None and result.total_cost > 0
    assert result.visited_nodes >= 1
    assert result.expanded_nodes >= 1


def test_find_path_result_returns_metadata_for_unreachable() -> None:
    map2d = make_map()
    for tile in map2d.tile_map:
        tile.is_passable = False

    result = map2d.queries.find_path_result((0, 0), (2, 0))

    assert result.found is False
    assert result.reason == "end-not-passable"
    assert result.path == []
    assert result.total_cost is None


def test_find_path_result_returns_reason_for_out_of_range_start() -> None:
    map2d = make_map()

    result = map2d.queries.find_path_result((-1, 0), (2, 0))

    assert result.found is False
    assert result.reason == "start-out-of-range"
    assert result.path == []


def test_find_path_result_returns_reason_for_disallowed_blocked_start() -> (
    None
):
    map2d = make_map()

    result = map2d.queries.find_path_result(
        (1, 0),
        (2, 0),
        state=PathfindingState(
            blocked_coordinates={(1, 0)},
            allow_start_blocked=False,
        ),
    )

    assert result.found is False
    assert result.reason == "start-not-passable"
    assert result.path == []


def test_find_path_respects_required_tile_capabilities() -> None:
    map2d = make_map()
    map2d.get_tile((1, 0)).required_capabilities = frozenset({"flight"})

    blocked_path = map2d.queries.find_path((0, 0), (2, 0))
    allowed_path = map2d.queries.find_path(
        (0, 0),
        (2, 0),
        state=PathfindingState(actor_capabilities=frozenset({"flight"})),
    )

    assert (1, 0) not in blocked_path
    assert (1, 0) in allowed_path


def test_find_path_result_reports_search_budget_exhaustion() -> None:
    map2d = make_map()

    result = map2d.queries.find_path_result(
        (0, 0),
        (2, 2),
        state=PathfindingState(max_expanded_nodes=1),
    )

    assert result.found is False
    assert result.reason == "search-budget-exhausted"


def test_find_path_result_reports_cost_budget_exhaustion() -> None:
    map2d = make_map()

    result = map2d.queries.find_path_result(
        (0, 0),
        (2, 2),
        state=PathfindingState(max_total_cost=1.0),
    )

    assert result.found is False
    assert result.reason == "cost-budget-exhausted"


def test_find_path_applies_dynamic_cost_layers() -> None:
    map2d = make_map()

    path = map2d.queries.find_path(
        (0, 0),
        (2, 0),
        state=PathfindingState(
            dynamic_cost_layers=(
                lambda tile, _coords: 8.0 if tile.name == "h" else 0.0,
            ),
        ),
    )

    assert path != []
    assert (1, 0) not in path


def test_find_path_smoothing_mode_collinear_reduces_turnless_nodes() -> None:
    map2d = make_map()

    result = map2d.queries.find_path_result(
        (0, 0),
        (2, 0),
        state=PathfindingState(smoothing_mode="collinear"),
    )

    assert result.found is True
    assert result.path == [(0, 0), (2, 0)]


def test_find_path_result_cache_hit_and_invalidation() -> None:
    map2d = make_map()
    state = PathfindingState(enable_result_cache=True, map_state_token="v1")

    first = map2d.queries.find_path_result((0, 0), (2, 0), state=state)
    second = map2d.queries.find_path_result((0, 0), (2, 0), state=state)

    assert first.from_cache is False
    assert second.from_cache is True

    map2d.queries.invalidate_path_cache()

    third = map2d.queries.find_path_result((0, 0), (2, 0), state=state)
    assert third.from_cache is False


def test_find_path_tie_breaker_modes_return_valid_paths() -> None:
    map2d = make_map()

    fifo_path = map2d.queries.find_path(
        (0, 0),
        (2, 2),
        state=PathfindingState(tie_breaker="fifo"),
    )
    heuristic_path = map2d.queries.find_path(
        (0, 0),
        (2, 2),
        state=PathfindingState(tie_breaker="lower-heuristic"),
    )
    cost_path = map2d.queries.find_path(
        (0, 0),
        (2, 2),
        state=PathfindingState(tie_breaker="lower-cost"),
    )

    assert fifo_path[0] == (0, 0) and fifo_path[-1] == (2, 2)
    assert heuristic_path[0] == (0, 0) and heuristic_path[-1] == (2, 2)
    assert cost_path[0] == (0, 0) and cost_path[-1] == (2, 2)


def test_pathfinding_state_for_player_profile_defaults() -> None:
    state = PathfindingState.for_player()

    assert state.actor_capabilities == frozenset({"walk"})
    assert state.allow_diagonal_movement is False
    assert state.allow_corner_cutting is False
    assert state.tie_breaker == "lower-heuristic"
    assert state.smoothing_mode == "collinear"


def test_pathfinding_state_for_player_tiers() -> None:
    relaxed = PathfindingState.for_player("relaxed")
    strict = PathfindingState.for_player("strict")

    assert relaxed.allow_diagonal_movement is True
    assert relaxed.allow_corner_cutting is True
    assert relaxed.tie_breaker == "fifo"

    assert strict.allow_diagonal_movement is False
    assert strict.allow_start_blocked is False
    assert strict.blocker_proximity_cost == 0.25
    assert strict.tie_breaker == "lower-cost"
    assert strict.smoothing_mode == "none"


def test_pathfinding_state_for_flying_enemy_profile_defaults() -> None:
    state = PathfindingState.for_flying_enemy()

    assert state.actor_capabilities == frozenset({"walk", "flight"})
    assert state.allow_diagonal_movement is True
    assert state.allow_corner_cutting is True
    assert state.tie_breaker == "lower-heuristic"
    assert state.smoothing_mode == "collinear"


def test_pathfinding_state_for_flying_enemy_tiers() -> None:
    relaxed = PathfindingState.for_flying_enemy("relaxed")
    strict = PathfindingState.for_flying_enemy("strict")

    assert relaxed.allow_diagonal_movement is True
    assert relaxed.allow_corner_cutting is True
    assert relaxed.tie_breaker == "fifo"

    assert strict.allow_diagonal_movement is True
    assert strict.allow_corner_cutting is False
    assert strict.turn_penalty == 0.35
    assert strict.blocker_proximity_cost == 0.15
    assert strict.tie_breaker == "lower-cost"
    assert strict.smoothing_mode == "none"


def test_pathfinding_state_for_heavy_unit_profile_defaults() -> None:
    state = PathfindingState.for_heavy_unit()

    assert state.actor_capabilities == frozenset({"walk", "heavy"})
    assert state.allow_diagonal_movement is False
    assert state.turn_penalty == 0.5
    assert state.blocker_proximity_cost == 0.25
    assert state.tie_breaker == "lower-cost"
    assert state.smoothing_mode == "none"


def test_pathfinding_state_for_heavy_unit_tiers() -> None:
    relaxed = PathfindingState.for_heavy_unit("relaxed")
    strict = PathfindingState.for_heavy_unit("strict")

    assert relaxed.turn_penalty == 0.2
    assert relaxed.blocker_proximity_cost == 0.1
    assert relaxed.tie_breaker == "lower-heuristic"

    assert strict.allow_start_blocked is False
    assert strict.turn_penalty == 0.8
    assert strict.blocker_proximity_cost == 0.4
    assert strict.max_expanded_nodes == 1500


def test_pathfinding_state_with_overrides_updates_selected_fields() -> None:
    base = PathfindingState.for_player()

    customized = base.with_overrides(
        max_expanded_nodes=500,
        allow_diagonal_movement=True,
    )

    assert customized is not base
    assert customized.max_expanded_nodes == 500
    assert customized.allow_diagonal_movement is True
    # unchanged defaults remain intact
    assert customized.tie_breaker == base.tie_breaker
    assert customized.smoothing_mode == base.smoothing_mode


def test_pathfinding_state_with_overrides_rejects_unknown_fields() -> None:
    base = PathfindingState.for_player()

    with pytest.raises(ValueError, match="Unknown PathfindingState fields"):
        base.with_overrides(not_a_real_field=True)


def test_pathfinding_state_profile_registry_round_trip() -> None:
    profile_name = "scout-profile"
    state = PathfindingState.for_player("relaxed")
    PathfindingState.unregister_profile(profile_name)

    PathfindingState.register_profile(profile_name, state)
    resolved = PathfindingState.from_profile(profile_name)

    assert resolved is state
    assert profile_name in PathfindingState.list_profiles()

    PathfindingState.unregister_profile(profile_name)


def test_pathfinding_state_profile_registry_requires_overwrite() -> None:
    profile_name = "tank-profile"
    first = PathfindingState.for_heavy_unit("relaxed")
    second = PathfindingState.for_heavy_unit("strict")
    PathfindingState.unregister_profile(profile_name)

    PathfindingState.register_profile(profile_name, first)
    with pytest.raises(ValueError, match="already registered"):
        PathfindingState.register_profile(profile_name, second)

    PathfindingState.register_profile(profile_name, second, overwrite=True)
    assert PathfindingState.from_profile(profile_name) is second

    PathfindingState.unregister_profile(profile_name)


def test_pathfinding_state_profile_registry_rejects_blank_name() -> None:
    with pytest.raises(ValueError, match="cannot be blank"):
        PathfindingState.register_profile("   ", PathfindingState.for_player())


def test_pathfinding_state_profile_registry_raises_for_unknown_profile() -> (
    None
):
    with pytest.raises(KeyError, match="Unknown pathfinding profile"):
        PathfindingState.from_profile("no-such-profile")


def test_pathfinding_state_profile_export_import_round_trip() -> None:
    profile_name = "persisted-scout"
    PathfindingState.unregister_profile(profile_name)

    original = PathfindingState.for_player("strict").with_overrides(
        blocked_coordinates=frozenset({(1, 2)}),
        tile_cost_by_name={"mud": 3.0},
        actor_capabilities=frozenset({"walk", "scout"}),
        max_expanded_nodes=250,
        map_state_token="zone-a",
    )
    PathfindingState.register_profile(profile_name, original)

    exported = PathfindingState.export_profiles()
    PathfindingState.unregister_profile(profile_name)
    PathfindingState.import_profiles(exported)

    restored = PathfindingState.from_profile(profile_name)
    assert restored.blocked_coordinates == frozenset({(1, 2)})
    assert restored.tile_cost_by_name == {"mud": 3.0}
    assert restored.actor_capabilities == frozenset({"walk", "scout"})
    assert restored.max_expanded_nodes == 250
    assert restored.map_state_token == "zone-a"

    PathfindingState.unregister_profile(profile_name)


def test_pathfinding_state_import_profiles_overwrite_control() -> None:
    profile_name = "persisted-heavy"
    PathfindingState.unregister_profile(profile_name)
    first = PathfindingState.for_heavy_unit("relaxed")
    second = PathfindingState.for_heavy_unit("strict")
    PathfindingState.register_profile(profile_name, first)

    payload = {
        profile_name: second.to_profile_dict(),
    }

    with pytest.raises(ValueError, match="already registered"):
        PathfindingState.import_profiles(payload)

    PathfindingState.import_profiles(payload, overwrite=True)
    assert PathfindingState.from_profile(profile_name).turn_penalty == 0.8

    PathfindingState.unregister_profile(profile_name)


def test_pathfinding_state_to_profile_dict_rejects_callables() -> None:
    with_resolver = PathfindingState(
        tile_cost_resolver=lambda _tile, _coords: 1.0
    )
    with pytest.raises(ValueError, match="tile_cost_resolver"):
        with_resolver.to_profile_dict()

    with_layers = PathfindingState(
        dynamic_cost_layers=(lambda _tile, _coords: 1.0,),
    )
    with pytest.raises(ValueError, match="dynamic_cost_layers"):
        with_layers.to_profile_dict()


def test_pathfinding_state_save_and_load_profiles_json(tmp_path: Path) -> None:
    profile_name = "file-scout"
    PathfindingState.unregister_profile(profile_name)
    PathfindingState.register_profile(
        profile_name,
        PathfindingState.for_player("relaxed").with_overrides(
            max_expanded_nodes=321,
            tile_cost_by_name={"mud": 2.0},
        ),
    )

    file_path = tmp_path / "profiles.json"
    PathfindingState.save_profiles(
        str(file_path),
        pretty=False,
        sort_keys=False,
    )

    PathfindingState.unregister_profile(profile_name)
    PathfindingState.load_profiles(str(file_path))

    restored = PathfindingState.from_profile(profile_name)
    assert restored.max_expanded_nodes == 321
    assert restored.tile_cost_by_name == {"mud": 2.0}

    PathfindingState.unregister_profile(profile_name)


def test_pathfinding_state_save_profiles_pretty_output(tmp_path: Path) -> None:
    profile_name = "file-pretty"
    PathfindingState.unregister_profile(profile_name)
    PathfindingState.register_profile(
        profile_name, PathfindingState.for_player()
    )

    file_path = tmp_path / "pretty_profiles.json"
    PathfindingState.save_profiles(str(file_path), pretty=True)
    pretty_content = file_path.read_text(encoding="utf-8")

    assert "\n" in pretty_content
    assert '  "' in pretty_content

    compact_path = tmp_path / "compact_profiles.json"
    PathfindingState.save_profiles(str(compact_path), pretty=False)
    compact_content = compact_path.read_text(encoding="utf-8")

    assert "\n" not in compact_content

    PathfindingState.unregister_profile(profile_name)


def test_pathfinding_state_load_profiles_rejects_non_object_json(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "bad_profiles.json"
    file_path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="JSON object"):
        PathfindingState.load_profiles(str(file_path))


def test_pathfinding_state_import_profiles_strict_rejects_unknown_fields() -> (
    None
):
    profile_name = "strict-bad"
    PathfindingState.unregister_profile(profile_name)
    payload = {
        profile_name: {
            **PathfindingState.for_player().to_profile_dict(),
            "unknown_field": True,
        }
    }

    with pytest.raises(ValueError, match="Unknown profile fields"):
        PathfindingState.import_profiles(payload, strict=True)


def test_pathfinding_state_import_profiles_permissive_ignores_unknown_fields() -> (
    None
):
    profile_name = "permissive-ok"
    PathfindingState.unregister_profile(profile_name)
    payload = {
        profile_name: {
            **PathfindingState.for_player().to_profile_dict(),
            "unknown_field": True,
        }
    }

    PathfindingState.import_profiles(payload, strict=False)
    restored = PathfindingState.from_profile(profile_name)

    assert restored.actor_capabilities == frozenset({"walk"})

    PathfindingState.unregister_profile(profile_name)


def test_pathfinding_state_load_profiles_permissive_mode(
    tmp_path: Path,
) -> None:
    profile_name = "permissive-file"
    PathfindingState.unregister_profile(profile_name)
    profile_payload = {
        profile_name: {
            **PathfindingState.for_player().to_profile_dict(),
            "unknown_field": "ignored",
        }
    }
    file_path = tmp_path / "permissive_profiles.json"
    file_path.write_text(
        json.dumps(profile_payload),
        encoding="utf-8",
    )

    PathfindingState.load_profiles(str(file_path), strict=False)
    assert PathfindingState.from_profile(
        profile_name
    ).actor_capabilities == frozenset({"walk"})

    PathfindingState.unregister_profile(profile_name)


def test_pathfinding_state_strict_validation_checks_field_types() -> None:
    profile_name = "strict-types"
    PathfindingState.unregister_profile(profile_name)

    bad_bool = {
        profile_name: {
            **PathfindingState.for_player().to_profile_dict(),
            "block_characters": "yes",
        }
    }
    with pytest.raises(ValueError, match="block_characters"):
        PathfindingState.import_profiles(bad_bool, strict=True)

    bad_enum = {
        profile_name: {
            **PathfindingState.for_player().to_profile_dict(),
            "tie_breaker": "random",
        }
    }
    with pytest.raises(ValueError, match="tie_breaker"):
        PathfindingState.import_profiles(bad_enum, strict=True)

    bad_coordinates = {
        profile_name: {
            **PathfindingState.for_player().to_profile_dict(),
            "blocked_coordinates": [[1, "two"]],
        }
    }
    with pytest.raises(ValueError, match="blocked_coordinates"):
        PathfindingState.import_profiles(bad_coordinates, strict=True)

    bad_cost_map = {
        profile_name: {
            **PathfindingState.for_player().to_profile_dict(),
            "tile_cost_by_name": {"mud": "high"},
        }
    }
    with pytest.raises(ValueError, match="tile_cost_by_name"):
        PathfindingState.import_profiles(bad_cost_map, strict=True)

    bad_max_total_cost = {
        profile_name: {
            **PathfindingState.for_player().to_profile_dict(),
            "max_total_cost": -1.0,
        }
    }
    with pytest.raises(ValueError, match="max_total_cost"):
        PathfindingState.import_profiles(bad_max_total_cost, strict=True)

    bad_max_expanded_nodes = {
        profile_name: {
            **PathfindingState.for_player().to_profile_dict(),
            "max_expanded_nodes": -1,
        }
    }
    with pytest.raises(ValueError, match="max_expanded_nodes"):
        PathfindingState.import_profiles(bad_max_expanded_nodes, strict=True)

    bad_turn_penalty = {
        profile_name: {
            **PathfindingState.for_player().to_profile_dict(),
            "turn_penalty": float("inf"),
        }
    }
    with pytest.raises(ValueError, match="turn_penalty"):
        PathfindingState.import_profiles(bad_turn_penalty, strict=True)

    bad_tile_cost_non_finite = {
        profile_name: {
            **PathfindingState.for_player().to_profile_dict(),
            "tile_cost_by_name": {"mud": float("nan")},
        }
    }
    with pytest.raises(ValueError, match="tile_cost_by_name"):
        PathfindingState.import_profiles(bad_tile_cost_non_finite, strict=True)


def test_get_adjacent_passable_coordinates_and_passable_rules() -> None:
    map2d = make_map()

    map2d.get_tile((1, 2)).is_passable = False
    map2d.get_tile((2, 1)).allowed_entry_directions = frozenset(
        {Direction.LEFT}
    )
    map2d.get_tile((0, 1)).allowed_entry_directions = frozenset(
        {Direction.LEFT}
    )

    adjacent = map2d.queries.get_adjacent_passable_coordinates((1, 1))

    assert (1, 2) not in adjacent
    assert (2, 1) not in adjacent
    assert (0, 1) in adjacent
    assert (1, 0) in adjacent


def test_find_path_respects_directional_entry_rules() -> None:
    map2d = make_map()
    # Entering (1, 0) from the left uses RIGHT movement direction.
    map2d.get_tile((1, 0)).allowed_entry_directions = frozenset(
        {Direction.LEFT}
    )

    path = map2d.queries.find_path((0, 0), (2, 0))

    assert path != []
    assert (1, 0) not in path
    assert path[0] == (0, 0)
    assert path[-1] == (2, 0)


def test_find_path_supports_diagonal_movement_when_enabled() -> None:
    map2d = make_map()
    map2d.get_tile((1, 0)).is_passable = False
    map2d.get_tile((0, 1)).is_passable = False

    path = map2d.queries.find_path(
        (0, 0),
        (1, 1),
        state=PathfindingState(
            allow_diagonal_movement=True,
            allow_corner_cutting=True,
        ),
    )

    assert path == [(0, 0), (1, 1)]


def test_find_path_blocks_diagonal_corner_cutting_by_default() -> None:
    map2d = make_map()
    map2d.get_tile((1, 0)).is_passable = False
    map2d.get_tile((0, 1)).is_passable = False

    path = map2d.queries.find_path(
        (0, 0),
        (1, 1),
        state=PathfindingState(allow_diagonal_movement=True),
    )

    assert path == []


def test_is_coordinates_in_range() -> None:
    map2d = make_map()

    assert map2d.queries.is_coordinates_in_range((0, 0)) is True
    assert map2d.queries.is_coordinates_in_range((2, 2)) is True
    assert map2d.queries.is_coordinates_in_range((-1, 0)) is False
    assert map2d.queries.is_coordinates_in_range((0, 3)) is False
