from __future__ import annotations

from typing import Callable, Optional

import pytest
from pytest_mock import MockerFixture

from sonartk.sound._output_device_recovery_controller import (
    OutputDeviceRecoveryController,
)


class _HostStub:
    def __init__(self) -> None:
        self._device_watch_callback: Optional[Callable[[float], None]] = None
        self._device_watch_interval_seconds = 0.5
        self._follow_default_output = True
        self._recovery_retry_count = 1
        self._status_callback: Optional[Callable[[str], None]] = None
        self._status_delay_seconds = 5.0
        self._status_timer_callback: Optional[Callable[[float], None]] = None
        self._status_announced_for_cycle = False
        self._last_known_default_device = ""
        self._last_known_current_device = ""
        self._last_known_output_inventory_signature = ""
        self._backend_error_streak = 0
        self._disconnected_streak = 0
        self._backend_error_recovery_threshold = 2
        self._disconnect_recovery_threshold = 2
        self._min_recovery_interval_seconds = 1.0
        self._last_recovery_attempt_time_seconds = 0.0
        self._recovery_in_progress = False
        self._recovery_callbacks: list[Callable[[], None]] = []

        self._begin_recovery_calls: list[tuple[int, bool]] = []
        self._cancel_status_calls = 0
        self._debug_messages: list[str] = []
        self._monotonic = 100.0
        self.default_name = "Speakers"
        self.current_name = "Speakers"
        self.inventory = "Speakers"
        self.backend_error = False
        self.disconnected = False
        self.music_stalled = False
        self.soft_reset_success = False
        self.rebuild_success = False
        self.rebuild_impl: Optional[Callable[[], bool]] = None

    def _safe_default_output_name(self) -> str:
        return self.default_name

    def _safe_current_output_name(self) -> str:
        return self.current_name

    def _safe_output_device_inventory_signature(self) -> str:
        return self.inventory

    def _has_backend_errors(self) -> bool:
        return self.backend_error

    def _is_device_disconnected(self) -> bool:
        return self.disconnected

    def _is_music_playback_stalled(self, delta_time: float) -> bool:
        _ = delta_time
        return self.music_stalled

    def _soft_reset_output_device(self) -> bool:
        return self.soft_reset_success

    def _rebuild_audio_graph(self) -> bool:
        if self.rebuild_impl is not None:
            return self.rebuild_impl()
        return self.rebuild_success

    def _debug(self, message: str) -> None:
        self._debug_messages.append(message)

    def _monotonic_time(self) -> float:
        value = self._monotonic
        self._monotonic += 0.1
        return value

    def _begin_recovery(
        self,
        retry_count: int,
        *,
        skip_soft_reset: bool = False,
    ) -> bool:
        self._begin_recovery_calls.append((retry_count, skip_soft_reset))
        return True

    def _cancel_recovery_status_timer(self) -> None:
        self._cancel_status_calls += 1


def test_start_output_device_watch_validates_arguments() -> None:
    host = _HostStub()
    controller = OutputDeviceRecoveryController(host)

    with pytest.raises(ValueError):
        controller.start_output_device_watch(poll_interval_seconds=0)
    with pytest.raises(ValueError):
        controller.start_output_device_watch(recovery_retry_count=-1)
    with pytest.raises(ValueError):
        controller.start_output_device_watch(status_delay_seconds=-1)


def test_start_and_stop_output_device_watch_schedule_and_unschedule(
    mocker: MockerFixture,
) -> None:
    host = _HostStub()
    status = mocker.MagicMock()
    host._status_callback = status
    controller = OutputDeviceRecoveryController(host)

    schedule_interval = mocker.patch(
        "sonartk.sound._output_device_recovery_controller.pyglet.clock.schedule_interval"
    )
    unschedule = mocker.patch(
        "sonartk.sound._output_device_recovery_controller.pyglet.clock.unschedule"
    )

    controller.start_output_device_watch(
        poll_interval_seconds=0.25,
        follow_default_output=False,
        recovery_retry_count=3,
        status_callback=status,
        status_delay_seconds=2.0,
    )

    assert host._device_watch_interval_seconds == 0.25
    assert host._follow_default_output is False
    assert host._recovery_retry_count == 3
    assert host._status_delay_seconds == 2.0
    assert host._device_watch_callback is not None
    schedule_interval.assert_called_once()
    status.assert_called_with("Audio device monitoring enabled.")

    controller.stop_output_device_watch()
    assert host._device_watch_callback is None
    assert unschedule.call_count >= 1


def test_poll_output_device_health_triggers_immediate_recovery_on_default_mismatch() -> (
    None
):
    host = _HostStub()
    host.default_name = "Headphones"
    host.current_name = "Speakers"
    controller = OutputDeviceRecoveryController(host)

    controller.poll_output_device_health(0.1)

    assert host._begin_recovery_calls == [(1, False)]


def test_poll_output_device_health_respects_cooldown_for_non_immediate_triggers() -> (
    None
):
    host = _HostStub()
    host.backend_error = True
    host._min_recovery_interval_seconds = 5.0
    controller = OutputDeviceRecoveryController(host)

    controller.poll_output_device_health(0.1)
    controller.poll_output_device_health(0.1)
    controller.poll_output_device_health(0.1)

    assert host._begin_recovery_calls == [(1, False)]


def test_poll_output_device_health_uses_skip_soft_reset_on_inventory_change() -> (
    None
):
    host = _HostStub()
    host._last_known_default_device = "Speakers"
    host._last_known_current_device = "Speakers"
    host._last_known_output_inventory_signature = "Speakers"
    host.inventory = "Speakers|Headphones"
    controller = OutputDeviceRecoveryController(host)

    controller.poll_output_device_health(0.1)

    assert host._begin_recovery_calls == [(1, True)]


def test_start_recovery_status_timer_emits_message_when_recovery_is_active(
    mocker: MockerFixture,
) -> None:
    host = _HostStub()
    status = mocker.MagicMock()
    host._status_callback = status
    host._status_delay_seconds = 1.0
    host._recovery_in_progress = True
    controller = OutputDeviceRecoveryController(host)

    schedule_once = mocker.patch(
        "sonartk.sound._output_device_recovery_controller.pyglet.clock.schedule_once"
    )

    controller.start_recovery_status_timer()
    notify = schedule_once.call_args.args[0]
    notify(1.0)

    status.assert_called_with("Audio device changed. Recovering audio.")


def test_begin_recovery_runs_callbacks_and_cleans_timer(
    mocker: MockerFixture,
) -> None:
    host = _HostStub()
    host.soft_reset_success = True
    callback = mocker.MagicMock()
    host._recovery_callbacks = [callback]
    controller = OutputDeviceRecoveryController(host)

    assert controller.begin_recovery(2)
    callback.assert_called_once()
    assert host._cancel_status_calls == 1
    assert host._recovery_in_progress is False


def test_begin_recovery_suppresses_callback_failures_and_logs_debug(
    mocker: MockerFixture,
) -> None:
    host = _HostStub()
    host.rebuild_success = True

    def bad_callback() -> None:
        raise RuntimeError("boom")

    host._recovery_callbacks = [bad_callback]
    controller = OutputDeviceRecoveryController(host)
    mocker.patch.object(controller, "cancel_recovery_status_timer")

    assert controller.begin_recovery(0)
    assert host._debug_messages
    assert "Recovery callback failed" in host._debug_messages[-1]


def test_poll_output_device_health_ignores_when_recovery_active() -> None:
    host = _HostStub()
    host._recovery_in_progress = True
    controller = OutputDeviceRecoveryController(host)

    controller.poll_output_device_health(0.1)

    assert host._begin_recovery_calls == []


def test_start_recovery_status_timer_noop_guards(
    mocker: MockerFixture,
) -> None:
    host = _HostStub()
    controller = OutputDeviceRecoveryController(host)
    schedule_once = mocker.patch(
        "sonartk.sound._output_device_recovery_controller.pyglet.clock.schedule_once"
    )

    host._status_callback = None
    controller.start_recovery_status_timer()

    host._status_callback = mocker.MagicMock()
    host._status_delay_seconds = 0
    controller.start_recovery_status_timer()

    host._status_delay_seconds = 1
    host._status_timer_callback = lambda _: None
    controller.start_recovery_status_timer()

    schedule_once.assert_not_called()


def test_cancel_recovery_status_timer_unschedules_when_present(
    mocker: MockerFixture,
) -> None:
    host = _HostStub()
    host._status_timer_callback = lambda _: None
    controller = OutputDeviceRecoveryController(host)
    unschedule = mocker.patch(
        "sonartk.sound._output_device_recovery_controller.pyglet.clock.unschedule"
    )

    controller.cancel_recovery_status_timer()

    unschedule.assert_called_once()
    assert host._status_timer_callback is None


def test_begin_recovery_guard_when_already_running() -> None:
    host = _HostStub()
    host._recovery_in_progress = True
    controller = OutputDeviceRecoveryController(host)

    assert not controller.begin_recovery(0)


def test_begin_recovery_rebuild_retry_count() -> None:
    host = _HostStub()
    host.soft_reset_success = False
    calls = {"count": 0}

    def _rebuild_once() -> bool:
        calls["count"] += 1
        return calls["count"] >= 3

    host.rebuild_impl = _rebuild_once
    controller = OutputDeviceRecoveryController(host)

    assert controller.begin_recovery(2)
    assert calls["count"] == 3
