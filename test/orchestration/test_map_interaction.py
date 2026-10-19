from __future__ import annotations

from typing import Any

import pytest
from pyglet.window import key
from pytest_mock import MockerFixture

from sonartk.util import Direction
from sonartk.orchestration.map_interaction import (
    DEFAULT_INTERACT_KEYS,
    InteractableObject,
    MapInteractionController,
    tile_distance,
)


class _FakeKeyHandler:
    def __init__(self) -> None:
        self.bindings: list[tuple[Any, int]] = []

    def add_key_press(self, callback: Any, symbol: int) -> None:
        self.bindings.append((callback, symbol))


class _FakeGrid:
    def __init__(self, coordinates: tuple[int, int]) -> None:
        self.current_coordinates = coordinates
        self.key_handler = _FakeKeyHandler()


class _FakeWindow:
    def __init__(self) -> None:
        self.states: dict[str, object] = {}
        self.transitions: list[str] = []

    def add(self, state_key: str, state: object) -> None:
        self.states[state_key] = state

    def transition_to(self, state_key: str) -> None:
        self.transitions.append(state_key)

    def push_window_handlers(self, *args: object, **kwargs: object) -> None:
        pass

    def pop_window_handlers(self, *args: object, **kwargs: object) -> None:
        pass


BOAT = InteractableObject("boat", (10, 10), ("A boat.", "Old oars."))
SIGN = InteractableObject("sign", (11, 10), ("A sign.",))
PLAIN = InteractableObject("rock", (10, 11), ())


def _controller(
    position: tuple[int, int],
    objects: tuple[InteractableObject, ...] = (BOAT,),
    **kwargs: Any,
) -> tuple[MapInteractionController, _FakeWindow, _FakeGrid]:
    window = _FakeWindow()
    grid = _FakeGrid(position)
    controller = MapInteractionController(
        window=window,  # type: ignore[arg-type]
        grid=grid,
        return_state_key="map:beach",
        objects=objects,
        **kwargs,
    )
    return controller, window, grid


@pytest.mark.parametrize(
    "first, second, expected",
    [((0, 0), (0, 0), 0), ((0, 0), (1, 1), 1), ((2, 5), (4, 4), 2)],
)
def test_tile_distance_counts_diagonals_as_one(
    first: tuple[int, int], second: tuple[int, int], expected: int
) -> None:
    assert tile_distance(first, second) == expected


def test_registers_a_state_for_each_described_object() -> None:
    controller, window, _ = _controller((0, 0), (BOAT, SIGN, PLAIN))

    assert set(window.states) == {
        "map:beach:describe:boat",
        "map:beach:describe:sign",
    }
    assert controller.state_keys["boat"] == "map:beach:describe:boat"
    assert "rock" not in controller.state_keys


def test_description_states_return_to_the_map() -> None:
    _, window, _ = _controller((0, 0))
    state = window.states["map:beach:describe:boat"]
    assert state.next_state_key == "map:beach"  # type: ignore[attr-defined]
    assert state.pages == ("A boat.", "Old oars.")  # type: ignore[attr-defined]


def test_interact_keys_are_bound_on_the_grid() -> None:
    controller, _, grid = _controller((0, 0))
    assert [symbol for _, symbol in grid.key_handler.bindings] == list(
        DEFAULT_INTERACT_KEYS
    )
    assert all(
        callback == controller.interact
        for callback, _ in grid.key_handler.bindings
    )
    assert {key.RETURN, key.ENTER, key.SPACE} == set(DEFAULT_INTERACT_KEYS)


def test_custom_keys_replace_the_defaults() -> None:
    _, _, grid = _controller((0, 0), keys=(key.E,))
    assert [symbol for _, symbol in grid.key_handler.bindings] == [key.E]


def test_interact_describes_an_adjacent_object() -> None:
    controller, window, _ = _controller((10, 9))

    assert controller.interact() is True

    assert window.transitions == ["map:beach:describe:boat"]


def test_diagonal_neighbors_are_within_reach() -> None:
    controller, window, _ = _controller((9, 9))
    controller.interact()
    assert window.transitions == ["map:beach:describe:boat"]


def test_interact_does_nothing_out_of_reach_but_handles_the_key() -> None:
    controller, window, _ = _controller((10, 8))

    assert controller.nearest() is None
    assert controller.interact() is True
    assert window.transitions == []


def test_reach_is_configurable() -> None:
    controller, window, _ = _controller((10, 8), reach_tiles=2)
    controller.interact()
    assert window.transitions == ["map:beach:describe:boat"]


def test_the_nearest_object_wins() -> None:
    controller, window, grid = _controller((10, 10), (BOAT, SIGN))
    assert controller.nearest() == "boat"

    grid.current_coordinates = (12, 10)
    assert controller.nearest() == "sign"


def test_objects_without_pages_cannot_be_examined() -> None:
    controller, _, _ = _controller((10, 11), (PLAIN,))
    assert controller.nearest() is None


def test_no_states_are_registered_without_descriptions() -> None:
    _, window, _ = _controller((0, 0), (PLAIN,))
    assert window.states == {}


def test_on_page_change_is_forwarded(mocker: MockerFixture) -> None:
    handler = mocker.Mock()
    _, window, _ = _controller((0, 0), on_page_change=handler)
    state = window.states["map:beach:describe:boat"]

    state.dispatch_event("on_page_change", state, 1)  # type: ignore[attr-defined]

    handler.assert_called_once_with(state, 1)


def test_a_large_object_can_be_examined_from_any_footprint_tile() -> None:
    log = InteractableObject(
        "log", (10, 10), ("A log.",), ((10, 10), (11, 10), (12, 10))
    )
    controller, window, grid = _controller((13, 10), (log,))

    assert controller.nearest() == "log"

    grid.current_coordinates = (12, 11)
    assert controller.nearest() == "log"

    grid.current_coordinates = (14, 10)
    assert controller.nearest() is None


@pytest.mark.parametrize(
    "facing, position",
    [
        (Direction.UP, (10, 9)),
        (Direction.DOWN, (10, 11)),
        (Direction.RIGHT, (9, 10)),
        (Direction.LEFT, (11, 10)),
        (Direction.DIAGONAL_UPPER_RIGHT, (9, 9)),
    ],
)
def test_facing_the_object_lets_you_examine_it(
    facing: Direction, position: tuple[int, int]
) -> None:
    controller, window, _ = _controller(position, facing=lambda: facing)

    assert controller.interact() is True
    assert window.transitions == ["map:beach:describe:boat"]


def test_next_to_an_object_but_facing_away_does_nothing() -> None:
    controller, window, _ = _controller((10, 9), facing=lambda: Direction.DOWN)

    assert controller.nearest() is None
    assert controller.interact() is True
    assert window.transitions == []


def test_facing_reaches_along_the_line_up_to_the_reach() -> None:
    near, _, _ = _controller(
        (10, 8), facing=lambda: Direction.UP, reach_tiles=2
    )
    far, _, _ = _controller(
        (10, 7), facing=lambda: Direction.UP, reach_tiles=2
    )

    assert near.nearest() == "boat"
    assert far.nearest() is None


def test_facing_a_large_object_uses_any_footprint_tile() -> None:
    wide = InteractableObject(
        "cottage", (5, 5), ("A cottage.",), ((5, 5), (6, 5), (7, 5))
    )
    controller, _, _ = _controller(
        (7, 4), (wide,), facing=lambda: Direction.UP
    )

    assert controller.nearest() == "cottage"
