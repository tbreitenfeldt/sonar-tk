from typing import Any, Callable
from unittest.mock import MagicMock

import pytest

from sonartk.util import AssetLoader, asset_loader, sound_pool_loader


class Clock:
    """Stands in for pyglet.clock, running scheduled calls on demand."""

    def __init__(self) -> None:
        self.scheduled: list[Callable[[float], None]] = []

    def schedule_once(
        self, func: Callable[[float], None], delay: float
    ) -> None:
        self.scheduled.append(func)

    def unschedule(self, func: Callable[[float], None]) -> None:
        self.scheduled = [f for f in self.scheduled if f != func]

    def tick(self) -> None:
        calls, self.scheduled = self.scheduled, []
        for func in calls:
            func(0.0)


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> Clock:
    fake = Clock()
    monkeypatch.setattr(asset_loader.pyglet, "clock", fake)
    return fake


@pytest.fixture
def loaded() -> list[str]:
    return []


@pytest.fixture
def loader(clock: Clock, loaded: list[str]) -> AssetLoader:
    return AssetLoader(loaded.append, loaded.remove)


def test_pinned_paths_load_and_are_never_unloaded(
    loader: AssetLoader, loaded: list[str]
) -> None:
    loader.pin(["ui"])
    loader.set_active(["a"])
    loader.set_active([])

    assert loaded == ["ui"]
    assert loader.resident == {"ui"}


def test_active_paths_load_immediately(
    loader: AssetLoader, loaded: list[str]
) -> None:
    loader.set_active(["a", "b"])

    assert loaded == ["a", "b"]


def test_paths_no_longer_wanted_are_unloaded(
    loader: AssetLoader, loaded: list[str]
) -> None:
    loader.set_active(["a", "b"])
    loader.set_active(["b", "c"])

    assert sorted(loaded) == ["b", "c"]


def test_already_loaded_paths_are_not_reloaded(
    loader: AssetLoader, loaded: list[str]
) -> None:
    loader.set_active(["a"])
    loader.set_active(["a"])

    assert loaded == ["a"]


def test_soon_paths_load_one_per_frame(
    loader: AssetLoader, clock: Clock, loaded: list[str]
) -> None:
    loader.set_active(["a"], soon=["b", "c", "a"])

    assert loaded == ["a"]
    assert loader.pending == ("b", "c")
    clock.tick()
    assert loaded == ["a", "b"]
    clock.tick()
    assert loaded == ["a", "b", "c"]
    assert loader.pending == ()
    assert clock.scheduled == []


def test_new_scene_cancels_queued_loads(
    loader: AssetLoader, clock: Clock, loaded: list[str]
) -> None:
    loader.set_active([], soon=["b", "c"])
    loader.set_active(["d"])
    clock.tick()

    assert loaded == ["d"]


def test_soon_paths_that_are_pinned_or_loaded_are_skipped(
    loader: AssetLoader, clock: Clock, loaded: list[str]
) -> None:
    loader.pin(["ui"])
    loader.set_active(["a"], soon=["ui", "a"])

    assert loader.pending == ()
    assert clock.scheduled == []


def test_finish_pending_loads_everything_queued(
    loader: AssetLoader, loaded: list[str]
) -> None:
    loader.set_active([], soon=["b", "c"])
    loader.finish_pending()

    assert loaded == ["b", "c"]


def test_load_next_with_nothing_queued_does_nothing(
    loader: AssetLoader, loaded: list[str]
) -> None:
    loader._load_next(0.0)

    assert loaded == []


def test_sound_pool_loader_uses_the_shared_pool(
    monkeypatch: pytest.MonkeyPatch, clock: Clock
) -> None:
    from sonartk.sound import sound_manager

    pool: Any = MagicMock()
    monkeypatch.setattr(sound_manager, "sound_pool", pool)
    loader = sound_pool_loader()

    loader.set_active(["a"])
    loader.set_active([])

    pool.load.assert_called_once_with("a")
    pool.unload.assert_called_once_with("a")
