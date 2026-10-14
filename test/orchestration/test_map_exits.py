from typing import Optional

import pytest

from sonartk.orchestration.map_exits import (
    MapExit,
    MapExitRegistry,
    MapSwitcher,
)
from sonartk.util import Coordinates


def _build() -> tuple[MapSwitcher[str], list[tuple[object, ...]]]:
    switcher: MapSwitcher[str] = MapSwitcher()
    events: list[tuple[object, ...]] = []
    switcher.register("beach", lambda spawn: f"beach@{spawn}")
    switcher.register("hut", lambda spawn: f"hut@{spawn}")
    switcher.push_handlers(
        on_map_leave=lambda key, m: events.append(("leave", key, m)),
        on_map_enter=lambda key, m, spawn: events.append(
            ("enter", key, m, spawn)
        ),
    )
    return switcher, events


def test_initial_state_is_empty() -> None:
    switcher, _ = _build()
    assert switcher.current is None
    assert switcher.current_key is None


def test_first_switch_enters_without_leave() -> None:
    switcher, events = _build()

    result = switcher.switch_to("beach", (1, 2))

    assert result == "beach@(1, 2)"
    assert switcher.current == result
    assert switcher.current_key == "beach"
    assert events == [("enter", "beach", "beach@(1, 2)", (1, 2))]


def test_second_switch_fires_leave_then_enter() -> None:
    switcher, events = _build()
    switcher.switch_to("beach")
    events.clear()

    switcher.switch_to("hut", (0, 0))

    assert events == [
        ("leave", "beach", "beach@None"),
        ("enter", "hut", "hut@(0, 0)", (0, 0)),
    ]
    assert switcher.current_key == "hut"


def test_failing_loader_keeps_current_map() -> None:
    switcher, events = _build()

    def broken(spawn: Optional[Coordinates]) -> str:
        raise RuntimeError("boom")

    switcher.register("broken", broken)
    switcher.switch_to("beach")
    events.clear()

    with pytest.raises(RuntimeError):
        switcher.switch_to("broken")

    assert switcher.current_key == "beach"
    assert events == []


def test_unknown_key_raises() -> None:
    switcher, _ = _build()
    with pytest.raises(KeyError):
        switcher.switch_to("nowhere")


def test_duplicate_registration_raises() -> None:
    switcher, _ = _build()
    with pytest.raises(ValueError):
        switcher.register("beach", lambda spawn: "x")


def test_registry_lookup_and_duplicates() -> None:
    registry = MapExitRegistry()
    exit_a = MapExit((3, 4), "hut", (0, 1))
    registry.add(exit_a)

    assert registry.exit_at((3, 4)) is exit_a
    assert registry.exit_at((0, 0)) is None
    assert len(registry) == 1
    with pytest.raises(ValueError):
        registry.add(MapExit((3, 4), "other", (0, 0)))


def test_try_exit_switches_only_on_exit_tile() -> None:
    switcher, _ = _build()
    switcher.switch_to("beach")
    registry = MapExitRegistry()
    registry.add(MapExit((3, 4), "hut", (0, 1)))

    assert switcher.try_exit(registry, (1, 1)) is False
    assert switcher.current_key == "beach"

    assert switcher.try_exit(registry, (3, 4)) is True
    assert switcher.current_key == "hut"
    assert switcher.current == "hut@(0, 1)"
