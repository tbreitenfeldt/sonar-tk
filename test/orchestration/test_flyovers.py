"""Tests for random flyovers."""

import random
from contextlib import contextmanager
from typing import Any, Iterator, cast
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from sonartk.orchestration.flyovers import FlyoverConfig, FlyoverController


class FakeService:
    def __init__(self) -> None:
        self.listener = MagicMock()
        self.listener.position = (10, 20, 0)
        self.played: list[dict[str, Any]] = []

    def play_sound(self, sound: str, **kwargs: Any) -> MagicMock:
        player = MagicMock()
        player.playing.return_value = True
        self.played.append({"sound": sound, "player": player, **kwargs})
        return player


@pytest.fixture
def clock(mocker: MockerFixture) -> MagicMock:
    return cast(
        MagicMock, mocker.patch("sonartk.orchestration.flyovers.pyglet.clock")
    )


def _config(**kwargs: Any) -> FlyoverConfig:
    values: dict[str, Any] = {
        "moving_sound": "wings.wav",
        "call_sounds": ("gull.wav", "albatross.wav"),
        "min_duration_seconds": 4.0,
        "max_duration_seconds": 4.0,
        "path_half_length": 10.0,
        "height": 5.0,
        "headings": ((1.0, 0.0),),
        "min_calls": 1,
        "max_calls": 1,
    }
    values.update(kwargs)
    return FlyoverConfig(**values)


def _controller(
    service: FakeService, seed: int = 1, **kwargs: Any
) -> FlyoverController:
    return FlyoverController(
        _config(**kwargs), sound_service=service, rng=random.Random(seed)
    )


def _fly(controller: FlyoverController, seconds: float = 4.0) -> None:
    for _ in range(int(seconds * 10)):
        controller._tick(0.1)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"min_interval_seconds": 0},
        {"min_interval_seconds": 30, "max_interval_seconds": 20},
        {"min_duration_seconds": 0},
        {"min_calls": 3, "max_calls": 1},
        {"call_sounds": ()},
        {"headings": ()},
        {"path_half_length": 0},
    ],
)
def test_config_rejects_bad_values(kwargs: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        _config(**kwargs)


def test_no_calls_need_no_call_sounds() -> None:
    assert _config(call_sounds=(), min_calls=0, max_calls=0)


def test_default_intervals_are_wide() -> None:
    config = FlyoverConfig("wings.wav", ("gull.wav",))

    assert config.min_interval_seconds >= 15
    assert config.max_interval_seconds <= 60


def test_start_schedules_a_random_wait_within_the_interval(
    clock: MagicMock,
) -> None:
    delays = set()
    for seed in range(20):
        clock.reset_mock()
        controller = _controller(
            FakeService(),
            seed,
            min_interval_seconds=15,
            max_interval_seconds=60,
        )
        controller.start()
        controller.start()
        clock.schedule_once.assert_called_once()
        delay = clock.schedule_once.call_args.args[1]
        assert 15 <= delay <= 60
        delays.add(delay)

    assert len(delays) > 1


def test_spawn_loops_the_moving_sound_above_the_start(
    clock: MagicMock,
) -> None:
    service = FakeService()
    controller = _controller(service)

    controller._spawn()

    moving = service.played[0]
    assert moving["sound"] == "wings.wav"
    assert moving["loop"] is True
    assert moving["position"] == (0.0, 20.0, 5.0)
    assert controller.flying
    clock.schedule_interval.assert_called_once()


def test_the_flyer_crosses_over_the_listener(clock: MagicMock) -> None:
    service = FakeService()
    controller = _controller(service, min_calls=0, max_calls=0)
    controller._spawn()
    player = service.played[0]["player"]

    controller._tick(2.0)
    assert player.position == (10.0, 20.0, 5.0)

    controller._tick(1.0)
    assert player.position == (15.0, 20.0, 5.0)


def test_the_flyer_stays_above_a_listener_on_high_ground(
    clock: MagicMock,
) -> None:
    service = FakeService()
    service.listener.position = (10, 20, 10)
    controller = _controller(service)
    controller.start()
    controller._spawn()
    _fly(controller, 2.0)

    assert service.played[0]["position"][2] == 15.0
    assert service.played[0]["player"].position[2] == 15.0


def test_fly_now_sends_a_flyer_at_once_and_replaces_the_current_one(
    clock: MagicMock,
) -> None:
    service = FakeService()
    controller = _controller(service)
    controller.fly_now()
    assert not controller.flying

    controller.start()
    controller.fly_now()
    first = service.played[0]["player"]
    controller.fly_now()

    assert controller.flying
    first.stop.assert_called_once()
    assert len(service.played) == 2


def test_the_flyer_follows_a_walking_listener(clock: MagicMock) -> None:
    service = FakeService()
    controller = _controller(service, min_calls=0, max_calls=0)
    controller._spawn()
    player = service.played[0]["player"]

    service.listener.position = (50, 60, 0)
    controller._tick(2.0)

    assert player.position == (50.0, 60.0, 5.0)


def test_the_flyer_moves_with_the_listener_between_ticks(
    clock: MagicMock,
) -> None:
    service = FakeService()
    controller = _controller(service, min_calls=0, max_calls=0)
    controller._spawn()
    player = service.played[0]["player"]
    controller._tick(2.0)

    service.listener.position = (11, 20, 0)
    controller.follow_listener()

    assert player.position == (11.0, 20.0, 5.0)


def test_following_the_listener_does_nothing_without_a_flyer(
    clock: MagicMock,
) -> None:
    service = FakeService()
    controller = _controller(service)

    controller.follow_listener()

    assert not service.played


def test_updates_are_batched_when_the_service_supports_it(
    clock: MagicMock,
) -> None:
    service = FakeService()
    batches: list[str] = []

    @contextmanager
    def batch_updates() -> Iterator[None]:
        batches.append("begin")
        yield
        batches.append("end")

    service.batch_updates = batch_updates  # type: ignore[attr-defined]
    controller = _controller(service, min_calls=0, max_calls=0)
    controller._spawn()

    controller._tick(0.1)
    controller.follow_listener()

    assert batches == ["begin", "end", "begin", "end"]


def test_the_flyer_passes_directly_over_a_moving_listener(
    clock: MagicMock,
) -> None:
    service = FakeService()
    controller = _controller(
        service, min_calls=0, max_calls=0, headings=((0.0, 1.0),)
    )
    controller._spawn()
    player = service.played[0]["player"]

    for step in range(20):
        service.listener.position = (10 + step, 20 + 2 * step, 0)
        controller._tick(0.1)

    assert player.position == (29.0, 58.0, 5.0)


def test_calls_play_once_each_from_the_flyer(clock: MagicMock) -> None:
    service = FakeService()
    controller = _controller(service, min_calls=2, max_calls=2)
    controller._spawn()

    _fly(controller)

    calls = [p for p in service.played if p["sound"] != "wings.wav"]
    assert len(calls) == 2
    assert all(not p.get("loop", False) for p in calls)
    assert all(p["sound"] in ("gull.wav", "albatross.wav") for p in calls)
    assert all(p["position"][2] == 5.0 for p in calls)


def test_calls_are_a_random_choice_of_sound(clock: MagicMock) -> None:
    chosen: set[str] = set()
    for seed in range(20):
        service = FakeService()
        controller = _controller(service, seed)
        controller._spawn()
        _fly(controller)
        chosen.update(p["sound"] for p in service.played[1:])

    assert chosen == {"gull.wav", "albatross.wav"}


def test_headings_are_random(clock: MagicMock) -> None:
    starts = set()
    for seed in range(30):
        service = FakeService()
        controller = _controller(
            service,
            seed,
            headings=((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0)),
        )
        controller._spawn()
        starts.add(service.played[0]["position"])

    assert len(starts) == 4


def test_the_call_count_varies_between_flyovers(clock: MagicMock) -> None:
    counts = set()
    for seed in range(20):
        service = FakeService()
        controller = _controller(service, seed, min_calls=1, max_calls=2)
        controller._spawn()
        _fly(controller)
        counts.add(len(service.played) - 1)

    assert counts == {1, 2}


def test_finishing_stops_the_wings_and_schedules_the_next(
    clock: MagicMock,
) -> None:
    service = FakeService()
    controller = _controller(service)
    controller.start()
    controller._spawn()
    clock.schedule_once.reset_mock()
    wings = service.played[0]["player"]

    controller._tick(5.0)

    wings.stop.assert_called_once()
    wings.remove.assert_called_once()
    assert not controller.flying
    clock.unschedule.assert_called_with(controller._tick)
    clock.schedule_once.assert_called_once()


def test_finished_calls_are_dropped(clock: MagicMock) -> None:
    service = FakeService()
    controller = _controller(service)
    controller._spawn()
    _fly(controller, 2.5)
    assert controller._call_players
    cast(MagicMock, controller._call_players[0].playing).return_value = False

    controller._tick(0.1)

    assert controller._call_players == []


def test_stop_silences_everything_and_does_not_reschedule(
    clock: MagicMock,
) -> None:
    service = FakeService()
    controller = _controller(service)
    controller.start()
    controller._spawn()
    _fly(controller, 2.5)
    clock.schedule_once.reset_mock()

    controller.stop()

    assert not controller.running
    assert not controller.flying
    for played in service.played:
        played["player"].stop.assert_called()
    clock.unschedule.assert_any_call(controller._spawn)
    clock.schedule_once.assert_not_called()


def test_stop_without_a_flyover_is_harmless(clock: MagicMock) -> None:
    controller = _controller(FakeService())

    controller.stop()
    controller.start()
    controller.stop()

    assert not controller.running
