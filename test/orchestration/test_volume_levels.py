from __future__ import annotations

from typing import Any

from pyglet.window import key
from pytest_mock import MockerFixture

from sonartk.orchestration.volume_levels import (
    ChannelVolume,
    VolumeHotkeys,
    bind_level_hotkeys,
)


class _FakeKeyHandler:
    def __init__(self) -> None:
        self.bindings: dict[int, Any] = {}

    def add_key_press(self, callback: Any, symbol: int) -> None:
        self.bindings[symbol] = callback


class _FakeWindow:
    def __init__(self) -> None:
        self.key_handler = _FakeKeyHandler()


def _volume(
    level: int = 7, ceiling: float = 0.6
) -> tuple[ChannelVolume, list]:
    applied: list[float] = []
    volume = ChannelVolume("Effects", ceiling, applied.append, level=level)
    return volume, applied


def test_percent_is_the_level_share() -> None:
    volume, _ = _volume(level=7)
    assert volume.percent == 70


def test_engine_volume_scales_the_ceiling() -> None:
    volume, _ = _volume(level=5, ceiling=0.6)
    assert volume.engine_volume == 0.3


def test_apply_pushes_the_engine_volume() -> None:
    volume, applied = _volume(level=10, ceiling=0.6)
    volume.apply()
    assert applied == [0.6]


def test_step_changes_the_level_and_applies_it() -> None:
    volume, applied = _volume(level=7)

    assert volume.step(1) is True

    assert volume.level == 8
    assert applied == [volume.engine_volume]


def test_step_stops_at_the_limits() -> None:
    top, top_applied = _volume(level=10)
    bottom, bottom_applied = _volume(level=0)

    assert top.step(1) is False
    assert bottom.step(-1) is False
    assert top.level == 10 and bottom.level == 0
    assert top_applied == [] and bottom_applied == []


def test_custom_step_count() -> None:
    volume = ChannelVolume("Music", 1.0, lambda v: None, level=2, steps=4)
    assert volume.percent == 50
    assert volume.engine_volume == 0.5


def _bind(mocker: MockerFixture, on_change: Any = None):  # type: ignore[no-untyped-def]
    volume, applied = _volume()
    window = _FakeWindow()
    speak = mocker.Mock()
    bind_level_hotkeys(
        window,  # type: ignore[arg-type]
        [VolumeHotkeys(volume, key.F9, key.F10, on_change=on_change)],
        speak=speak,
    )
    return volume, applied, window, speak


def test_up_and_down_keys_step_and_speak(mocker: MockerFixture) -> None:
    volume, applied, window, speak = _bind(mocker)

    assert window.key_handler.bindings[key.F10]() is True
    speak.assert_called_with("Effects volume 80 percent", interrupt=True)
    assert window.key_handler.bindings[key.F9]() is True
    window.key_handler.bindings[key.F9]()

    assert volume.level == 6
    speak.assert_called_with("Effects volume 60 percent", interrupt=True)
    assert len(applied) == 3


def test_on_change_runs_after_each_press(mocker: MockerFixture) -> None:
    on_change = mocker.Mock()
    volume, _, window, _ = _bind(mocker, on_change)

    window.key_handler.bindings[key.F10]()

    on_change.assert_called_once_with(volume)


def test_speech_defaults_to_the_speech_manager(mocker: MockerFixture) -> None:
    output = mocker.patch(
        "sonartk.orchestration.volume_levels.speech_manager.output"
    )
    volume, _ = _volume()
    window = _FakeWindow()
    bind_level_hotkeys(
        window,  # type: ignore[arg-type]
        [VolumeHotkeys(volume, key.F9, key.F10)],
    )

    window.key_handler.bindings[key.F9]()

    output.assert_called_once_with("Effects volume 60 percent", interrupt=True)
